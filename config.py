import os
import logging
from pathlib import Path

# Environment variables with defaults
class Config:
    # Server configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5001))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # File upload configuration
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_SIZE', 500 * 1024 * 1024))  # 500MB default
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/manus_uploads')
    WORKSPACE_FOLDER = os.getenv('WORKSPACE_FOLDER', '/tmp/manus_workspace')
    
    # OpenAI configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', 2000))
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', 0.7))
    
    # Session configuration
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))  # 1 hour
    CLEANUP_INTERVAL = int(os.getenv('CLEANUP_INTERVAL', 1800))  # 30 minutes
    
    # Security configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'manus_platform.log')
    
    # Supported file extensions
    ALLOWED_EXTENSIONS = {
        # Code files
        'py', 'js', 'ts', 'jsx', 'tsx', 'html', 'css', 'scss', 'sass', 'less',
        'java', 'cpp', 'c', 'h', 'hpp', 'cs', 'php', 'rb', 'go', 'rs', 'swift',
        'kt', 'scala', 'clj', 'hs', 'ml', 'fs', 'vb', 'pas', 'pl', 'r', 'lua',
        
        # Data files
        'json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf',
        'csv', 'tsv', 'sql', 'db', 'sqlite', 'sqlite3',
        
        # Documentation
        'md', 'rst', 'txt', 'rtf', 'tex', 'adoc', 'org',
        
        # Scripts and configs
        'sh', 'bash', 'zsh', 'fish', 'ps1', 'bat', 'cmd',
        'dockerfile', 'makefile', 'cmake', 'gradle', 'maven',
        
        # Archives
        'zip', 'tar', 'gz', 'bz2', 'xz', '7z', 'rar',
        
        # Media files
        'wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac',
        'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv',
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg',
        
        # Other
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'
    }
    
    # Archive extensions for extraction
    ARCHIVE_EXTENSIONS = {'zip', 'tar', 'gz', 'bz2', 'xz', '7z'}
    
    @classmethod
    def init_directories(cls):
        """Initialize required directories"""
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.WORKSPACE_FOLDER, exist_ok=True)
    
    @classmethod
    def setup_logging(cls):
        """Setup structured logging"""
        log_level = getattr(logging, cls.LOG_LEVEL.upper(), logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # Setup file handler
        file_handler = logging.FileHandler(cls.LOG_FILE)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        return root_logger

