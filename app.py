from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import json
import logging
import datetime
import time
import zipfile
import shutil
from pathlib import Path
import uuid
import openai
from werkzeug.utils import secure_filename
import threading

# Configuration
UPLOAD_FOLDER = "/tmp/manus_uploads"
WORKSPACE_FOLDER = "/tmp/manus_workspace"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    'txt', 'py', 'js', 'html', 'css', 'json', 'xml', 'yaml', 'yml',
    'md', 'rst', 'csv', 'sql', 'sh', 'bat', 'dockerfile', 'zip',
    'tar', 'gz', 'java', 'cpp', 'c', 'h', 'php', 'rb', 'go', 'rs'
}

# Setup
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("manus_platform.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure workspace directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(WORKSPACE_FOLDER, exist_ok=True)

# Set OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Utility Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_zip_file(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            total_size = sum(f.file_size for f in zip_ref.filelist)
            if total_size > 100 * 1024 * 1024:
                raise ValueError("ZIP file too large")
            zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        logger.error(f"ZIP error: {e}")
        return False

def read_file_content(file_path):
    try:
        if os.path.getsize(file_path) > 1024 * 1024:
            return "[File too large]"
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "[Unreadable or binary file]"

def analyze_project_structure(session_path):
    structure = {
        "files": [],
        "directories": [],
        "total_files": 0,
        "total_size": 0,
        "file_types": {}
    }
    for root, dirs, files in os.walk(session_path):
        for file in files:
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, session_path)
            ext = Path(file).suffix.lower()
            size = os.path.getsize(path)

            structure["files"].append({"path": rel_path, "size": size, "type": ext})
            structure["total_size"] += size
            structure["total_files"] += 1
            structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1

    return structure

# Routes
@app.route('/')
def home():
    return render_template("manus_index.html")

@app.route('/api/health')
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/ask', methods=['POST'])
def ask():
    prompt = request.json.get('prompt')
    if not prompt:
        return jsonify({'error': 'Missing prompt'}), 400
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're a helpful AI coding assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        return jsonify({'response': response['choices'][0]['message']['content']})
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'files' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    session_id = str(uuid.uuid4())
    session_path = os.path.join(WORKSPACE_FOLDER, session_id)
    os.makedirs(session_path, exist_ok=True)

    results = []
    for file in request.files.getlist('files'):
        if file.filename == '':
            continue
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(session_path, filename)
            file.save(filepath)
            if filename.endswith('.zip'):
                extract_dir = os.path.join(session_path, 'extracted')
                os.makedirs(extract_dir, exist_ok=True)
                if extract_zip_file(filepath, extract_dir):
                    shutil.rmtree(filepath, ignore_errors=True)
                    results.append(f"Extracted: {filename}")
                else:
                    results.append(f"Failed to extract: {filename}")
            else:
                results.append(f"Uploaded: {filename}")
    structure = analyze_project_structure(session_path)
    return jsonify({
        "session_id": session_id,
        "files": results,
        "structure": structure
    })

@app.route('/api/process', methods=['POST'])
def process():
    data = request.get_json()
    session_id = data.get('session_id')
    task = data.get('task_description')

    session_path = os.path.join(WORKSPACE_FOLDER, session_id)
    if not os.path.exists(session_path):
        return jsonify({'error': 'Invalid session ID'}), 400

    structure = analyze_project_structure(session_path)
    simulated_response = {
        "session_id": session_id,
        "task": task,
        "language": "Python" if ".py" in structure["file_types"] else "Unknown",
        "suggestions": [
            "Refactor large functions",
            "Add error handling",
            "Write unit tests"
        ]
    }
    return jsonify(simulated_response)

@app.route('/api/download/<session_id>')
def download(session_id):
    session_path = os.path.join(WORKSPACE_FOLDER, session_id)
    if not os.path.exists(session_path):
        return jsonify({'error': 'Invalid session ID'}), 400

    zip_path = os.path.join(UPLOAD_FOLDER, f"{session_id}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(session_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, session_path)
                zipf.write(file_path, arcname)
    return send_file(zip_path, as_attachment=True)

# Clean up old sessions every 30 min
def cleanup_sessions():
    while True:
        time.sleep(1800)
        now = time.time()
        for dir in os.listdir(WORKSPACE_FOLDER):
            path = os.path.join(WORKSPACE_FOLDER, dir)
            if os.path.isdir(path) and now - os.path.getctime(path) > 3600:
                shutil.rmtree(path)
                logger.info(f"Cleaned up: {path}")

cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
cleanup_thread.start()

# Launch
if __name__ == '__main__':
    logger.info("Manus-Genius is live.")
    app.run(debug=True, host='0.0.0.0', port=5001)
