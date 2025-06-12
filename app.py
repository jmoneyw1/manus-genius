from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import json
import logging
import datetime
import time
import zipfile
import tempfile
import shutil
from pathlib import Path
import uuid
import subprocess
import threading
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("manus_platform.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = "/tmp/manus_uploads"
WORKSPACE_FOLDER = "/tmp/manus_workspace"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    'txt', 'py', 'js', 'html', 'css', 'json', 'xml', 'yaml', 'yml', 
    'md', 'rst', 'csv', 'sql', 'sh', 'bat', 'dockerfile', 'zip', 
    'tar', 'gz', 'java', 'cpp', 'c', 'h', 'php', 'rb', 'go', 'rs'
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(WORKSPACE_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_zip_file(zip_path, extract_to):
    """Extract ZIP file to specified directory"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Check for zip bombs and malicious files
            total_size = 0
            for file_info in zip_ref.filelist:
                total_size += file_info.file_size
                if total_size > 100 * 1024 * 1024:  # 100MB limit
                    raise ValueError("ZIP file too large when extracted")
                
                # Check for directory traversal
                if '..' in file_info.filename or file_info.filename.startswith('/'):
                    raise ValueError("Unsafe file path in ZIP")
            
            zip_ref.extractall(extract_to)
            return True
    except Exception as e:
        logger.error(f"Error extracting ZIP file: {str(e)}")
        return False

def read_file_content(file_path, max_size=1024*1024):  # 1MB limit per file
    """Read file content safely"""
    try:
        if os.path.getsize(file_path) > max_size:
            return f"[File too large: {os.path.getsize(file_path)} bytes]"
        
        # Try to read as text
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ['latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            # If all fail, return binary info
            return f"[Binary file: {os.path.getsize(file_path)} bytes]"
    
    except Exception as e:
        return f"[Error reading file: {str(e)}]"

def analyze_project_structure(workspace_path):
    """Analyze the structure of uploaded files"""
    structure = {
        "files": [],
        "directories": [],
        "total_files": 0,
        "total_size": 0,
        "file_types": {},
        "content": {}
    }
    
    try:
        for root, dirs, files in os.walk(workspace_path):
            rel_root = os.path.relpath(root, workspace_path)
            if rel_root != '.':
                structure["directories"].append(rel_root)
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, workspace_path)
                file_size = os.path.getsize(file_path)
                
                structure["files"].append({
                    "path": rel_path,
                    "size": file_size,
                    "extension": Path(file).suffix.lower()
                })
                
                structure["total_files"] += 1
                structure["total_size"] += file_size
                
                # Count file types
                ext = Path(file).suffix.lower()
                structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
                
                # Read content for text files (limit to important files)
                if (ext in ['.py', '.js', '.html', '.css', '.json', '.md', '.txt', '.yml', '.yaml'] 
                    and file_size < 100*1024):  # 100KB limit
                    structure["content"][rel_path] = read_file_content(file_path)
    
    except Exception as e:
        logger.error(f"Error analyzing project structure: {str(e)}")
    
    return structure

def simulate_ai_processing(task_description, project_structure):
    """Simulate AI processing of the task - replace with actual OpenAI API call"""
    logger.info(f"Simulating AI processing for task: {task_description}")
    
    # This is a simulation - in production, you would call OpenAI API here
    # Example: response = openai.ChatCompletion.create(...)
    
    # Analyze the task and project
    analysis = {
        "task_type": "unknown",
        "complexity": "medium",
        "estimated_time": "5-10 minutes",
        "files_analyzed": len(project_structure["files"]),
        "main_language": "unknown"
    }
    
    # Determine main language
    file_types = project_structure["file_types"]
    if '.py' in file_types:
        analysis["main_language"] = "Python"
        analysis["task_type"] = "python_development"
    elif '.js' in file_types:
        analysis["main_language"] = "JavaScript"
        analysis["task_type"] = "web_development"
    elif '.html' in file_types:
        analysis["main_language"] = "HTML/CSS"
        analysis["task_type"] = "web_development"
    
    # Generate simulated solution
    solution = {
        "analysis": analysis,
        "recommendations": [],
        "code_changes": [],
        "new_files": [],
        "explanation": ""
    }
    
    # Task-specific recommendations
    if "bug" in task_description.lower() or "fix" in task_description.lower():
        solution["recommendations"] = [
            "Review error logs and stack traces",
            "Add proper error handling",
            "Implement unit tests to prevent regression",
            "Consider code review process"
        ]
        solution["explanation"] = "I've analyzed your code for potential bug fixes. Here are the main areas that need attention."
    
    elif "optimize" in task_description.lower() or "performance" in task_description.lower():
        solution["recommendations"] = [
            "Profile code to identify bottlenecks",
            "Optimize database queries",
            "Implement caching where appropriate",
            "Consider asynchronous processing"
        ]
        solution["explanation"] = "I've identified several optimization opportunities in your codebase."
    
    elif "feature" in task_description.lower() or "add" in task_description.lower():
        solution["recommendations"] = [
            "Plan the feature architecture",
            "Update documentation",
            "Add comprehensive tests",
            "Consider backward compatibility"
        ]
        solution["explanation"] = "I've outlined a plan for implementing the requested feature."
    
    else:
        solution["recommendations"] = [
            "Code structure looks good overall",
            "Consider adding more documentation",
            "Implement automated testing",
            "Follow best practices for your language"
        ]
        solution["explanation"] = "I've reviewed your code and provided general recommendations."
    
    # Add some code examples based on language
    if analysis["main_language"] == "Python":
        solution["code_changes"] = [
            {
                "file": "main.py",
                "type": "modification",
                "description": "Add error handling and logging",
                "code": """
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def improved_function():
    try:
        # Your existing code here
        result = process_data()
        logger.info("Processing completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in processing: {str(e)}")
        raise
"""
            }
        ]
    
    elif analysis["main_language"] == "JavaScript":
        solution["code_changes"] = [
            {
                "file": "app.js",
                "type": "modification", 
                "description": "Add async/await error handling",
                "code": """
async function improvedFunction() {
    try {
        const result = await processData();
        console.log('Processing completed successfully');
        return result;
    } catch (error) {
        console.error('Error in processing:', error);
        throw error;
    }
}
"""
            }
        ]
    
    return solution

# Routes
@app.route('/')
def home():
    """Home page"""
    logger.info("Home page accessed")
    return render_template('manus_index.html')

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Upload files or ZIP for processing"""
    start_time = time.time()
    logger.info("Upload endpoint accessed")
    
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session_workspace = os.path.join(WORKSPACE_FOLDER, session_id)
        os.makedirs(session_workspace, exist_ok=True)
        
        uploaded_files = []
        
        # Handle file uploads
        if 'files' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No files uploaded"
            }), 400
        
        files = request.files.getlist('files')
        
        for file in files:
            if file.filename == '':
                continue
                
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(session_workspace, filename)
                file.save(file_path)
                
                # If it's a ZIP file, extract it
                if filename.lower().endswith('.zip'):
                    extract_dir = os.path.join(session_workspace, 'extracted')
                    os.makedirs(extract_dir, exist_ok=True)
                    
                    if extract_zip_file(file_path, extract_dir):
                        # Move extracted files to main workspace
                        for item in os.listdir(extract_dir):
                            src = os.path.join(extract_dir, item)
                            dst = os.path.join(session_workspace, item)
                            if os.path.isdir(src):
                                shutil.copytree(src, dst)
                            else:
                                shutil.copy2(src, dst)
                        
                        # Remove the ZIP and extract directory
                        os.remove(file_path)
                        shutil.rmtree(extract_dir)
                        uploaded_files.append(f"Extracted: {filename}")
                    else:
                        uploaded_files.append(f"Failed to extract: {filename}")
                else:
                    uploaded_files.append(filename)
        
        # Analyze project structure
        project_structure = analyze_project_structure(session_workspace)
        
        end_time = time.time()
        logger.info(f"Upload completed in {end_time - start_time:.2f} seconds")
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "uploaded_files": uploaded_files,
            "project_structure": {
                "total_files": project_structure["total_files"],
                "total_size": project_structure["total_size"],
                "file_types": project_structure["file_types"],
                "files": project_structure["files"][:20]  # Limit to first 20 files for display
            },
            "processing_time": round(end_time - start_time, 2)
        })
    
    except Exception as e:
        end_time = time.time()
        logger.exception(f"Error in upload endpoint after {end_time - start_time:.2f} seconds: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Upload error: {str(e)}"
        }), 500

@app.route('/api/process', methods=['POST'])
def process_task():
    """Process the uploaded code with AI"""
    start_time = time.time()
    logger.info("Process endpoint accessed")
    
    try:
        data = request.get_json()
        
        if not data or 'session_id' not in data or 'task_description' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing session_id or task_description"
            }), 400
        
        session_id = data['session_id']
        task_description = data['task_description']
        
        # Validate session
        session_workspace = os.path.join(WORKSPACE_FOLDER, session_id)
        if not os.path.exists(session_workspace):
            return jsonify({
                "status": "error",
                "message": "Invalid session ID"
            }), 400
        
        logger.info(f"Processing task for session {session_id}: {task_description}")
        
        # Analyze project structure
        project_structure = analyze_project_structure(session_workspace)
        
        # Process with AI (simulated)
        solution = simulate_ai_processing(task_description, project_structure)
        
        end_time = time.time()
        logger.info(f"Processing completed in {end_time - start_time:.2f} seconds")
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "task_description": task_description,
            "solution": solution,
            "processing_time": round(end_time - start_time, 2)
        })
    
    except Exception as e:
        end_time = time.time()
        logger.exception(f"Error in process endpoint after {end_time - start_time:.2f} seconds: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Processing error: {str(e)}"
        }), 500

@app.route('/api/download/<session_id>')
def download_result(session_id):
    """Download the processed result as ZIP"""
    try:
        session_workspace = os.path.join(WORKSPACE_FOLDER, session_id)
        if not os.path.exists(session_workspace):
            return jsonify({
                "status": "error",
                "message": "Invalid session ID"
            }), 400
        
        # Create ZIP file
        zip_path = os.path.join(UPLOAD_FOLDER, f"result_{session_id}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(session_workspace):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, session_workspace)
                    zipf.write(file_path, arcname)
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f"manus_result_{session_id}.zip",
            mimetype='application/zip'
        )
    
    except Exception as e:
        logger.exception(f"Error in download endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Download error: {str(e)}"
        }), 500

@app.route('/api/sessions/<session_id>/files')
def get_session_files(session_id):
    """Get detailed file listing for a session"""
    try:
        session_workspace = os.path.join(WORKSPACE_FOLDER, session_id)
        if not os.path.exists(session_workspace):
            return jsonify({
                "status": "error",
                "message": "Invalid session ID"
            }), 400
        
        project_structure = analyze_project_structure(session_workspace)
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "project_structure": project_structure
        })
    
    except Exception as e:
        logger.exception(f"Error getting session files: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/api/sessions/<session_id>/file/<path:file_path>')
def get_file_content(session_id, file_path):
    """Get content of a specific file"""
    try:
        session_workspace = os.path.join(WORKSPACE_FOLDER, session_id)
        full_file_path = os.path.join(session_workspace, file_path)
        
        # Security check - ensure file is within workspace
        if not full_file_path.startswith(session_workspace):
            return jsonify({
                "status": "error",
                "message": "Invalid file path"
            }), 400
        
        if not os.path.exists(full_file_path):
            return jsonify({
                "status": "error",
                "message": "File not found"
            }), 404
        
        content = read_file_content(full_file_path)
        
        return jsonify({
            "status": "success",
            "file_path": file_path,
            "content": content,
            "size": os.path.getsize(full_file_path)
        })
    
    except Exception as e:
        logger.exception(f"Error getting file content: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0.0"
    })

# Cleanup old sessions (run periodically)
def cleanup_old_sessions():
    """Clean up sessions older than 1 hour"""
    try:
        current_time = time.time()
        for session_dir in os.listdir(WORKSPACE_FOLDER):
            session_path = os.path.join(WORKSPACE_FOLDER, session_dir)
            if os.path.isdir(session_path):
                # Check if directory is older than 1 hour
                if current_time - os.path.getctime(session_path) > 3600:
                    shutil.rmtree(session_path)
                    logger.info(f"Cleaned up old session: {session_dir}")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=lambda: [cleanup_old_sessions(), time.sleep(1800)])  # Run every 30 minutes
cleanup_thread.daemon = True
cleanup_thread.start()

if __name__ == '__main__':
    logger.info("Starting Manus Platform")
    app.run(debug=True, host='0.0.0.0', port=5001)

