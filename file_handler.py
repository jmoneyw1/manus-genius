import os
import zipfile
import tarfile
import shutil
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from werkzeug.utils import secure_filename
from config import Config

logger = logging.getLogger(__name__)

class FileHandler:
    """Enhanced file handling with support for multiple formats and extraction"""
    
    def __init__(self):
        self.config = Config
        
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        if not filename or '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in self.config.ALLOWED_EXTENSIONS
    
    def is_archive_file(self, filename: str) -> bool:
        """Check if file is an archive that should be extracted"""
        if not filename or '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in self.config.ARCHIVE_EXTENSIONS
    
    def get_file_type(self, filename: str) -> str:
        """Get file type category"""
        if not filename or '.' not in filename:
            return 'unknown'
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        # Code files
        code_extensions = {
            'py', 'js', 'ts', 'jsx', 'tsx', 'html', 'css', 'scss', 'sass', 'less',
            'java', 'cpp', 'c', 'h', 'hpp', 'cs', 'php', 'rb', 'go', 'rs', 'swift',
            'kt', 'scala', 'clj', 'hs', 'ml', 'fs', 'vb', 'pas', 'pl', 'r', 'lua'
        }
        
        # Data files
        data_extensions = {
            'json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf',
            'csv', 'tsv', 'sql', 'db', 'sqlite', 'sqlite3'
        }
        
        # Media files
        audio_extensions = {'wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac'}
        video_extensions = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv'}
        image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg'}
        
        # Documentation
        doc_extensions = {'md', 'rst', 'txt', 'rtf', 'tex', 'adoc', 'org'}
        
        if extension in code_extensions:
            return 'code'
        elif extension in data_extensions:
            return 'data'
        elif extension in audio_extensions:
            return 'audio'
        elif extension in video_extensions:
            return 'video'
        elif extension in image_extensions:
            return 'image'
        elif extension in doc_extensions:
            return 'documentation'
        elif extension in self.config.ARCHIVE_EXTENSIONS:
            return 'archive'
        else:
            return 'other'
    
    def extract_archive(self, archive_path: str, extract_to: str) -> Tuple[bool, str, List[str]]:
        """
        Extract archive file to specified directory
        Returns: (success, error_message, extracted_files)
        """
        try:
            extracted_files = []
            filename = os.path.basename(archive_path)
            extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            # Security checks
            if not os.path.exists(archive_path):
                return False, "Archive file not found", []
            
            file_size = os.path.getsize(archive_path)
            if file_size > self.config.MAX_CONTENT_LENGTH:
                return False, f"Archive too large: {file_size} bytes", []
            
            # Create extraction directory
            os.makedirs(extract_to, exist_ok=True)
            
            if extension == 'zip':
                return self._extract_zip(archive_path, extract_to)
            elif extension in ['tar', 'gz', 'bz2', 'xz']:
                return self._extract_tar(archive_path, extract_to)
            else:
                return False, f"Unsupported archive format: {extension}", []
                
        except Exception as e:
            logger.error(f"Error extracting archive {archive_path}: {str(e)}")
            return False, f"Extraction failed: {str(e)}", []
    
    def _extract_zip(self, zip_path: str, extract_to: str) -> Tuple[bool, str, List[str]]:
        """Extract ZIP file with security checks"""
        try:
            extracted_files = []
            total_size = 0
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Security checks
                for file_info in zip_ref.filelist:
                    # Check for zip bombs
                    total_size += file_info.file_size
                    if total_size > 1024 * 1024 * 1024:  # 1GB limit
                        return False, "Archive too large when extracted (>1GB)", []
                    
                    # Check for directory traversal
                    if '..' in file_info.filename or file_info.filename.startswith('/'):
                        return False, f"Unsafe file path: {file_info.filename}", []
                    
                    # Check filename length
                    if len(file_info.filename) > 255:
                        return False, f"Filename too long: {file_info.filename[:50]}...", []
                
                # Extract files
                for file_info in zip_ref.filelist:
                    if not file_info.is_dir():
                        try:
                            zip_ref.extract(file_info, extract_to)
                            extracted_files.append(file_info.filename)
                        except Exception as e:
                            logger.warning(f"Failed to extract {file_info.filename}: {str(e)}")
            
            logger.info(f"Successfully extracted {len(extracted_files)} files from ZIP")
            return True, "", extracted_files
            
        except zipfile.BadZipFile:
            return False, "Invalid or corrupted ZIP file", []
        except Exception as e:
            logger.error(f"ZIP extraction error: {str(e)}")
            return False, f"ZIP extraction failed: {str(e)}", []
    
    def _extract_tar(self, tar_path: str, extract_to: str) -> Tuple[bool, str, List[str]]:
        """Extract TAR file with security checks"""
        try:
            extracted_files = []
            
            # Determine compression type
            if tar_path.endswith('.tar.gz') or tar_path.endswith('.tgz'):
                mode = 'r:gz'
            elif tar_path.endswith('.tar.bz2') or tar_path.endswith('.tbz2'):
                mode = 'r:bz2'
            elif tar_path.endswith('.tar.xz'):
                mode = 'r:xz'
            else:
                mode = 'r'
            
            with tarfile.open(tar_path, mode) as tar_ref:
                # Security checks
                total_size = 0
                for member in tar_ref.getmembers():
                    # Check for tar bombs
                    total_size += member.size
                    if total_size > 1024 * 1024 * 1024:  # 1GB limit
                        return False, "Archive too large when extracted (>1GB)", []
                    
                    # Check for directory traversal
                    if '..' in member.name or member.name.startswith('/'):
                        return False, f"Unsafe file path: {member.name}", []
                    
                    # Check for special files
                    if member.isdev() or member.isfifo() or member.issym():
                        return False, f"Unsafe file type: {member.name}", []
                
                # Extract files
                for member in tar_ref.getmembers():
                    if member.isfile():
                        try:
                            tar_ref.extract(member, extract_to)
                            extracted_files.append(member.name)
                        except Exception as e:
                            logger.warning(f"Failed to extract {member.name}: {str(e)}")
            
            logger.info(f"Successfully extracted {len(extracted_files)} files from TAR")
            return True, "", extracted_files
            
        except tarfile.TarError as e:
            return False, f"Invalid or corrupted TAR file: {str(e)}", []
        except Exception as e:
            logger.error(f"TAR extraction error: {str(e)}")
            return False, f"TAR extraction failed: {str(e)}", []
    
    def read_file_content(self, file_path: str, max_size: int = 1024*1024) -> str:
        """Read file content safely with size limits"""
        try:
            if not os.path.exists(file_path):
                return "[File not found]"
            
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                return f"[File too large: {self.format_file_size(file_size)}]"
            
            # Try to read as text with multiple encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        # Check if content looks like text
                        if self._is_text_content(content):
                            return content
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, return binary info
            return f"[Binary file: {self.format_file_size(file_size)}]"
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return f"[Error reading file: {str(e)}]"
    
    def _is_text_content(self, content: str) -> bool:
        """Check if content appears to be text"""
        if not content:
            return True
        
        # Check for null bytes (common in binary files)
        if '\x00' in content:
            return False
        
        # Check ratio of printable characters
        printable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
        ratio = printable_chars / len(content)
        
        return ratio > 0.7  # At least 70% printable characters
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def analyze_project_structure(self, workspace_path: str) -> Dict:
        """Analyze project structure with enhanced metadata"""
        structure = {
            "files": [],
            "directories": [],
            "total_files": 0,
            "total_size": 0,
            "file_types": {},
            "file_categories": {},
            "content": {},
            "large_files": [],
            "binary_files": [],
            "code_files": [],
            "media_files": []
        }
        
        try:
            for root, dirs, files in os.walk(workspace_path):
                rel_root = os.path.relpath(root, workspace_path)
                if rel_root != '.':
                    structure["directories"].append(rel_root)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, workspace_path)
                    
                    try:
                        file_size = os.path.getsize(file_path)
                        file_type = self.get_file_type(file)
                        extension = Path(file).suffix.lower()
                        
                        file_info = {
                            "path": rel_path,
                            "size": file_size,
                            "extension": extension,
                            "type": file_type,
                            "formatted_size": self.format_file_size(file_size)
                        }
                        
                        structure["files"].append(file_info)
                        structure["total_files"] += 1
                        structure["total_size"] += file_size
                        
                        # Count file types and categories
                        structure["file_types"][extension] = structure["file_types"].get(extension, 0) + 1
                        structure["file_categories"][file_type] = structure["file_categories"].get(file_type, 0) + 1
                        
                        # Categorize files
                        if file_size > 10 * 1024 * 1024:  # Files larger than 10MB
                            structure["large_files"].append(file_info)
                        
                        if file_type == 'code':
                            structure["code_files"].append(file_info)
                        elif file_type in ['audio', 'video', 'image']:
                            structure["media_files"].append(file_info)
                        
                        # Read content for small text files
                        if (file_type in ['code', 'data', 'documentation'] and 
                            file_size < 100*1024):  # 100KB limit
                            content = self.read_file_content(file_path, 100*1024)
                            if not content.startswith('['):  # Not an error message
                                structure["content"][rel_path] = content
                        
                    except Exception as e:
                        logger.warning(f"Error analyzing file {rel_path}: {str(e)}")
                        continue
        
        except Exception as e:
            logger.error(f"Error analyzing project structure: {str(e)}")
        
        return structure
    
    def cleanup_session(self, session_id: str) -> bool:
        """Clean up session files and directories"""
        try:
            session_workspace = os.path.join(self.config.WORKSPACE_FOLDER, session_id)
            if os.path.exists(session_workspace):
                shutil.rmtree(session_workspace)
                logger.info(f"Cleaned up session: {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {str(e)}")
            return False

