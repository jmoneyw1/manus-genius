#!/bin/bash
"""
Production startup script for Manus AI Platform
Optimized for Render.com deployment
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment from {env_path}")
except ImportError:
    print("python-dotenv not installed, skipping .env file loading")

# Import configuration to initialize directories and logging
from config import Config

def setup_production_environment():
    """Setup production environment"""
    print("Setting up production environment...")
    
    # Initialize directories
    Config.init_directories()
    print(f"Initialized upload folder: {Config.UPLOAD_FOLDER}")
    print(f"Initialized workspace folder: {Config.WORKSPACE_FOLDER}")
    
    # Setup logging
    logger = Config.setup_logging()
    logger.info("Production environment setup completed")
    
    # Log configuration
    logger.info(f"Host: {Config.HOST}")
    logger.info(f"Port: {Config.PORT}")
    logger.info(f"Debug: {Config.DEBUG}")
    logger.info(f"Max upload size: {Config.MAX_CONTENT_LENGTH // (1024*1024)}MB")
    logger.info(f"OpenAI configured: {bool(Config.OPENAI_API_KEY)}")
    
    return logger

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'flask', 'flask_cors', 'gunicorn', 'openai', 
        'werkzeug', 'pathlib', 'uuid', 'threading'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        sys.exit(1)
    
    print("All dependencies are installed")

def main():
    """Main startup function"""
    print("Starting Manus AI Platform...")
    
    # Check dependencies
    check_dependencies()
    
    # Setup environment
    logger = setup_production_environment()
    
    # Import and start the Flask app
    try:
        from app import app
        logger.info("Flask application imported successfully")
        
        # Check if running with Gunicorn
        if 'gunicorn' in os.environ.get('SERVER_SOFTWARE', ''):
            logger.info("Running with Gunicorn")
            return app
        else:
            # Development mode
            logger.info("Running in development mode")
            app.run(
                host=Config.HOST,
                port=Config.PORT,
                debug=Config.DEBUG
            )
    
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
else:
    # When imported by Gunicorn
    setup_production_environment()
    from app import app as application

