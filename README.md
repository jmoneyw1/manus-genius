# Manus AI Platform - Render.com Deployment

This repository contains the Manus AI Platform optimized for production deployment on Render.com.

## Quick Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## Features

- 🚀 **Production Ready**: Optimized with Gunicorn for high performance
- 📁 **Enhanced File Support**: 50+ file types including archives, media, and code
- 🤖 **OpenAI Integration**: Async AI-powered code analysis
- 🔒 **Secure**: Input validation, file size limits, and security checks
- 📊 **Scalable**: Session management and background processing
- 🌐 **Modern UI**: Responsive design with real-time updates

## Supported File Types

### Code Files
Python, JavaScript, TypeScript, Java, C/C++, C#, PHP, Ruby, Go, Rust, Swift, Kotlin, and more

### Data Files
JSON, XML, YAML, CSV, SQL, databases

### Media Files
Audio: WAV, MP3, M4A, FLAC, OGG, AAC
Video: MP4, MOV, AVI, MKV, WebM
Images: JPG, PNG, GIF, SVG, WebP

### Archives
ZIP, TAR, GZ, BZ2, XZ, 7Z (automatically extracted)

### Documentation
Markdown, reStructuredText, LaTeX, AsciiDoc

## Environment Variables

### Required
- `OPENAI_API_KEY`: Your OpenAI API key for AI analysis

### Optional
- `PORT`: Server port (default: 5001)
- `MAX_UPLOAD_SIZE`: Maximum file size in bytes (default: 500MB)
- `WORKERS`: Number of Gunicorn workers (default: 4)
- `LOG_LEVEL`: Logging level (default: INFO)

## Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd manus-platform
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start development server:
```bash
python app.py
```

## Production Deployment

### Render.com (Recommended)

1. Fork this repository
2. Connect to Render.com
3. Create a new Web Service
4. Set environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `ENVIRONMENT`: production
5. Deploy!

### Manual Deployment

1. Use the production start script:
```bash
./start.sh
```

2. Or start with Gunicorn directly:
```bash
gunicorn --config gunicorn.conf.py wsgi:application
```

## API Endpoints

### Core Endpoints
- `POST /api/upload` - Upload files and archives
- `POST /api/analyze` - Start AI analysis (async)
- `GET /api/status/<session_id>` - Check analysis status
- `GET /api/stream/<session_id>` - Stream analysis results
- `GET /api/download/<session_id>` - Download results

### Utility Endpoints
- `GET /api/health` - Health check
- `GET /api/sessions/<session_id>/files` - List session files
- `GET /api/sessions/<session_id>/file/<path>` - Get file content

## Architecture

### Backend
- **Flask**: Web framework
- **Gunicorn**: WSGI server for production
- **OpenAI**: AI-powered code analysis
- **Async Processing**: Background analysis with status updates

### Frontend
- **Modern UI**: Dark theme with smooth animations
- **Real-time Updates**: Progress tracking and streaming results
- **File Explorer**: Browse uploaded files and project structure
- **Responsive Design**: Works on desktop and mobile

### Security
- Input validation and sanitization
- File type restrictions
- Archive extraction safety checks
- Session isolation and cleanup
- Rate limiting ready

## Scaling

The platform is designed for easy scaling:

- **Horizontal Scaling**: Multiple Gunicorn workers
- **Session Storage**: Ready for Redis integration
- **Database**: Prepared for PostgreSQL
- **Queue System**: Celery integration ready
- **Monitoring**: Structured logging and health checks

## Configuration

### File Upload Limits
- Default: 500MB per file
- Configurable via `MAX_UPLOAD_SIZE`
- Archive extraction: 1GB limit

### Session Management
- Default timeout: 1 hour
- Automatic cleanup every 30 minutes
- Configurable via environment variables

### OpenAI Integration
- Model: GPT-4 (configurable)
- Max tokens: 2000 (configurable)
- Temperature: 0.7 (configurable)
- Async processing with fallback

## Monitoring

### Health Check
```bash
curl http://localhost:5001/api/health
```

### Logs
- Structured JSON logging
- Request/response tracking
- Error monitoring
- Performance metrics

## Security

### File Upload Security
- File type validation
- Size limits
- Archive bomb protection
- Path traversal prevention

### API Security
- CORS configuration
- Input validation
- Session isolation
- Error handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the logs for debugging

---

**Manus AI Platform** - Empowering developers with AI-driven code analysis and solutions.

