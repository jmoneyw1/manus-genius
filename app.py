#!/usr/bin/env python3
"""
Manus AI Platform - Production Flask Application
Optimized for production deployment with Gunicorn
"""

import os
import sys
import asyncio
import logging
from flask import Flask, request, jsonify, render_template, send_file, Response
from flask_cors import CORS
import uuid
import time
import datetime
import threading
from pathlib import Path
import tempfile
import shutil
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Import our modules
from config import Config
from file_handler import FileHandler
from openai_service import OpenAIService

# Initialize configuration and logging
Config.init_directories()
logger = Config.setup_logging()

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Initialize services
file_handler = FileHandler()
openai_service = OpenAIService()

# Global session storage (in production, use Redis or database)
active_sessions = {}
session_lock = threading.Lock()

class SessionManager:
    """Manage user sessions and cleanup"""
    
    def __init__(self):
        self.sessions = {}
        self.cleanup_thread = None
        self.start_cleanup_thread()
    
    def create_session(self) -> str:
        """Create new session"""
        session_id = str(uuid.uuid4())
        session_data = {
            'id': session_id,
            'created_at': time.time(),
            'last_activity': time.time(),
            'workspace_path': os.path.join(Config.WORKSPACE_FOLDER, session_id),
            'status': 'active'
        }
        
        with session_lock:
            self.sessions[session_id] = session_data
        
        # Create workspace directory
        os.makedirs(session_data['workspace_path'], exist_ok=True)
        
        logger.info(f"Created session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> dict:
        """Get session data"""
        with session_lock:
            session = self.sessions.get(session_id)
            if session:
                session['last_activity'] = time.time()
            return session
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = time.time()
        expired_sessions = []
        
        with session_lock:
            for session_id, session_data in self.sessions.items():
                if current_time - session_data['last_activity'] > Config.SESSION_TIMEOUT:
                    expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.remove_session(session_id)
    
    def remove_session(self, session_id: str):
        """Remove session and cleanup files"""
        with session_lock:
            session_data = self.sessions.pop(session_id, None)
        
        if session_data:
            # Clean up workspace
            workspace_path = session_data['workspace_path']
            if os.path.exists(workspace_path):
                try:
                    shutil.rmtree(workspace_path)
                    logger.info(f"Cleaned up session workspace: {session_id}")
                except Exception as e:
                    logger.error(f"Error cleaning up session {session_id}: {str(e)}")
    
    def start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                try:
                    self.cleanup_expired_sessions()
                    time.sleep(Config.CLEANUP_INTERVAL)
                except Exception as e:
                    logger.error(f"Error in cleanup thread: {str(e)}")
                    time.sleep(60)  # Wait 1 minute before retrying
        
        self.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        logger.info("Started session cleanup thread")

# Initialize session manager
session_manager = SessionManager()

# Error handlers
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    """Handle file too large error"""
    max_size_mb = Config.MAX_CONTENT_LENGTH // (1024 * 1024)
    return jsonify({
        'status': 'error',
        'message': f'File too large. Maximum size allowed: {max_size_mb}MB',
        'error_code': 'FILE_TOO_LARGE'
    }), 413

@app.errorhandler(500)
def handle_internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error occurred',
        'error_code': 'INTERNAL_ERROR'
    }), 500

@app.errorhandler(404)
def handle_not_found(e):
    """Handle not found errors"""
    return jsonify({
        'status': 'error',
        'message': 'Resource not found',
        'error_code': 'NOT_FOUND'
    }), 404

# Routes
@app.route('/')
def home():
    """Home page"""
    logger.info("Home page accessed")
    return render_template('manus_index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'version': '2.0.0',
        'sessions': len(session_manager.sessions),
        'openai_configured': bool(Config.OPENAI_API_KEY)
    })

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Enhanced file upload with support for multiple formats"""
    start_time = time.time()
    logger.info("Upload endpoint accessed")
    
    try:
        # Create new session
        session_id = session_manager.create_session()
        session_data = session_manager.get_session(session_id)
        workspace_path = session_data['workspace_path']
        
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No files uploaded',
                'error_code': 'NO_FILES'
            }), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'status': 'error',
                'message': 'No files selected',
                'error_code': 'NO_FILES_SELECTED'
            }), 400
        
        uploaded_files = []
        extracted_files = []
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
            
            if not file_handler.is_allowed_file(file.filename):
                errors.append(f"File type not supported: {file.filename}")
                continue
            
            try:
                # Secure filename
                filename = secure_filename(file.filename)
                if not filename:
                    filename = f"file_{int(time.time())}"
                
                # Save file
                file_path = os.path.join(workspace_path, filename)
                file.save(file_path)
                
                file_size = os.path.getsize(file_path)
                file_type = file_handler.get_file_type(filename)
                
                uploaded_files.append({
                    'filename': filename,
                    'original_name': file.filename,
                    'size': file_size,
                    'formatted_size': file_handler.format_file_size(file_size),
                    'type': file_type
                })
                
                # Extract archives
                if file_handler.is_archive_file(filename):
                    logger.info(f"Extracting archive: {filename}")
                    success, error_msg, files_list = file_handler.extract_archive(
                        file_path, workspace_path
                    )
                    
                    if success:
                        extracted_files.extend(files_list)
                        # Remove the archive file after extraction
                        os.remove(file_path)
                        logger.info(f"Successfully extracted {len(files_list)} files from {filename}")
                    else:
                        errors.append(f"Failed to extract {filename}: {error_msg}")
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                errors.append(f"Error processing {file.filename}: {str(e)}")
        
        # Analyze project structure
        project_structure = file_handler.analyze_project_structure(workspace_path)
        
        # Update session with project data
        with session_lock:
            session_manager.sessions[session_id].update({
                'project_structure': project_structure,
                'uploaded_files': uploaded_files,
                'extracted_files': extracted_files
            })
        
        end_time = time.time()
        logger.info(f"Upload completed in {end_time - start_time:.2f} seconds")
        
        response_data = {
            'status': 'success',
            'session_id': session_id,
            'uploaded_files': uploaded_files,
            'extracted_files': extracted_files,
            'project_structure': {
                'total_files': project_structure['total_files'],
                'total_size': project_structure['total_size'],
                'formatted_size': file_handler.format_file_size(project_structure['total_size']),
                'file_categories': project_structure['file_categories'],
                'file_types': dict(list(project_structure['file_types'].items())[:10]),  # Top 10
                'code_files_count': len(project_structure['code_files']),
                'media_files_count': len(project_structure['media_files']),
                'large_files_count': len(project_structure['large_files'])
            },
            'processing_time': round(end_time - start_time, 2)
        }
        
        if errors:
            response_data['warnings'] = errors
        
        return jsonify(response_data)
    
    except Exception as e:
        end_time = time.time()
        logger.exception(f"Error in upload endpoint after {end_time - start_time:.2f} seconds")
        return jsonify({
            'status': 'error',
            'message': f'Upload failed: {str(e)}',
            'error_code': 'UPLOAD_FAILED'
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_project():
    """Analyze project with OpenAI (async)"""
    start_time = time.time()
    logger.info("Analyze endpoint accessed")
    
    try:
        data = request.get_json()
        
        if not data or 'session_id' not in data or 'task_description' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing session_id or task_description',
                'error_code': 'MISSING_PARAMETERS'
            }), 400
        
        session_id = data['session_id']
        task_description = data['task_description']
        
        # Validate session
        session_data = session_manager.get_session(session_id)
        if not session_data:
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired session',
                'error_code': 'INVALID_SESSION'
            }), 400
        
        # Get project structure
        project_structure = session_data.get('project_structure', {})
        
        # Start async analysis
        def run_analysis():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    openai_service.analyze_code_async(task_description, project_structure)
                )
                
                # Store result in session
                with session_lock:
                    session_manager.sessions[session_id]['analysis_result'] = result
                    session_manager.sessions[session_id]['analysis_status'] = 'completed'
                
                logger.info(f"Analysis completed for session {session_id}")
                
            except Exception as e:
                logger.error(f"Error in async analysis: {str(e)}")
                with session_lock:
                    session_manager.sessions[session_id]['analysis_result'] = {
                        'error': str(e)
                    }
                    session_manager.sessions[session_id]['analysis_status'] = 'failed'
        
        # Mark analysis as started
        with session_lock:
            session_manager.sessions[session_id]['analysis_status'] = 'running'
            session_manager.sessions[session_id]['task_description'] = task_description
        
        # Start analysis in background thread
        analysis_thread = threading.Thread(target=run_analysis, daemon=True)
        analysis_thread.start()
        
        end_time = time.time()
        logger.info(f"Analysis started in {end_time - start_time:.2f} seconds")
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'message': 'Analysis started',
            'analysis_status': 'running',
            'processing_time': round(end_time - start_time, 2)
        })
    
    except Exception as e:
        end_time = time.time()
        logger.exception(f"Error in analyze endpoint after {end_time - start_time:.2f} seconds")
        return jsonify({
            'status': 'error',
            'message': f'Analysis failed to start: {str(e)}',
            'error_code': 'ANALYSIS_START_FAILED'
        }), 500

@app.route('/api/status/<session_id>')
def get_analysis_status(session_id):
    """Get analysis status"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired session',
                'error_code': 'INVALID_SESSION'
            }), 400
        
        analysis_status = session_data.get('analysis_status', 'not_started')
        
        response_data = {
            'status': 'success',
            'session_id': session_id,
            'analysis_status': analysis_status
        }
        
        if analysis_status == 'completed':
            response_data['result'] = session_data.get('analysis_result', {})
        elif analysis_status == 'failed':
            response_data['error'] = session_data.get('analysis_result', {}).get('error', 'Unknown error')
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.exception(f"Error getting analysis status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get status: {str(e)}',
            'error_code': 'STATUS_FAILED'
        }), 500

@app.route('/api/stream/<session_id>')
def stream_analysis(session_id):
    """Stream analysis results (Server-Sent Events)"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired session'
            }), 400
        
        def generate():
            try:
                # Get project structure and task
                project_structure = session_data.get('project_structure', {})
                task_description = session_data.get('task_description', '')
                
                # Stream analysis
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def stream_wrapper():
                    async for chunk in openai_service.stream_analysis(task_description, project_structure):
                        yield f"data: {chunk}\n\n"
                
                for chunk in loop.run_until_complete(stream_wrapper()):
                    yield chunk
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming: {str(e)}")
                yield f"data: Error: {str(e)}\n\n"
        
        return Response(generate(), mimetype='text/plain')
    
    except Exception as e:
        logger.exception(f"Error in stream endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Streaming failed: {str(e)}'
        }), 500

@app.route('/api/download/<session_id>')
def download_results(session_id):
    """Download session results as ZIP"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired session'
            }), 400
        
        workspace_path = session_data['workspace_path']
        if not os.path.exists(workspace_path):
            return jsonify({
                'status': 'error',
                'message': 'Session workspace not found'
            }), 404
        
        # Create ZIP file
        zip_filename = f"manus_result_{session_id}.zip"
        zip_path = os.path.join(tempfile.gettempdir(), zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(workspace_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, workspace_path)
                    zipf.write(file_path, arcname)
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
    
    except Exception as e:
        logger.exception(f"Error in download endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Download failed: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>/files')
def get_session_files(session_id):
    """Get detailed file listing for a session"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired session'
            }), 400
        
        project_structure = session_data.get('project_structure', {})
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'project_structure': project_structure
        })
    
    except Exception as e:
        logger.exception(f"Error getting session files: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get files: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>/file/<path:file_path>')
def get_file_content(session_id, file_path):
    """Get content of a specific file"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired session'
            }), 400
        
        workspace_path = session_data['workspace_path']
        full_file_path = os.path.join(workspace_path, file_path)
        
        # Security check
        if not full_file_path.startswith(workspace_path):
            return jsonify({
                'status': 'error',
                'message': 'Invalid file path'
            }), 400
        
        if not os.path.exists(full_file_path):
            return jsonify({
                'status': 'error',
                'message': 'File not found'
            }), 404
        
        content = file_handler.read_file_content(full_file_path)
        file_size = os.path.getsize(full_file_path)
        
        return jsonify({
            'status': 'success',
            'file_path': file_path,
            'content': content,
            'size': file_size,
            'formatted_size': file_handler.format_file_size(file_size),
            'type': file_handler.get_file_type(file_path)
        })
    
    except Exception as e:
        logger.exception(f"Error getting file content: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get file content: {str(e)}'
        }), 500

# Legacy endpoint for backward compatibility
@app.route('/api/process', methods=['POST'])
def process_task_legacy():
    """Legacy process endpoint - redirects to new analyze endpoint"""
    return analyze_project()

if __name__ == '__main__':
    logger.info("Starting Manus AI Platform in development mode")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
else:
    # Production mode with Gunicorn
    logger.info("Manus AI Platform initialized for production")

