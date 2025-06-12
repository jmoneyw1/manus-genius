// Manus AI Platform JavaScript
class ManusApp {
    constructor() {
        this.currentStep = 1;
        this.sessionId = null;
        this.selectedFiles = [];
        this.projectStructure = null;
        
        this.initializeEventListeners();
        this.updateStepNavigation();
    }

    initializeEventListeners() {
        // File upload handling
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        
        // Upload button
        document.getElementById('upload-btn').addEventListener('click', this.uploadFiles.bind(this));
        
        // Task description
        const taskDescription = document.getElementById('task-description');
        taskDescription.addEventListener('input', this.validateTaskForm.bind(this));
        
        // Process button
        document.getElementById('process-btn').addEventListener('click', this.processTask.bind(this));
        
        // Action buttons
        document.getElementById('download-btn').addEventListener('click', this.downloadResults.bind(this));
        document.getElementById('new-task-btn').addEventListener('click', this.startNewTask.bind(this));
    }

    handleDragOver(e) {
        e.preventDefault();
        document.getElementById('upload-area').classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        document.getElementById('upload-area').classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        document.getElementById('upload-area').classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        this.processSelectedFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processSelectedFiles(files);
    }

    processSelectedFiles(files) {
        this.selectedFiles = files.filter(file => this.isValidFile(file));
        
        if (this.selectedFiles.length === 0) {
            this.showMessage('No valid files selected. Please select supported file types.', 'error');
            return;
        }
        
        this.displaySelectedFiles();
        document.getElementById('upload-btn').style.display = 'block';
    }

    isValidFile(file) {
        const allowedExtensions = [
            'py', 'js', 'html', 'css', 'json', 'xml', 'yaml', 'yml', 
            'md', 'rst', 'csv', 'sql', 'sh', 'bat', 'dockerfile', 'zip', 
            'tar', 'gz', 'java', 'cpp', 'c', 'h', 'php', 'rb', 'go', 'rs', 'txt'
        ];
        
        const extension = file.name.split('.').pop().toLowerCase();
        return allowedExtensions.includes(extension);
    }

    displaySelectedFiles() {
        const fileList = document.getElementById('file-list');
        const fileItems = document.getElementById('file-items');
        
        fileItems.innerHTML = '';
        
        this.selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const extension = file.name.split('.').pop().toLowerCase();
            const fileSize = this.formatFileSize(file.size);
            
            fileItem.innerHTML = `
                <div class="file-info">
                    <div class="file-icon ${extension}">${extension.toUpperCase()}</div>
                    <div class="file-details">
                        <h5>${file.name}</h5>
                        <div class="file-size">${fileSize}</div>
                    </div>
                </div>
                <button class="file-remove" onclick="manusApp.removeFile(${index})">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            fileItems.appendChild(fileItem);
        });
        
        fileList.style.display = 'block';
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        
        if (this.selectedFiles.length === 0) {
            document.getElementById('file-list').style.display = 'none';
            document.getElementById('upload-btn').style.display = 'none';
        } else {
            this.displaySelectedFiles();
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async uploadFiles() {
        if (this.selectedFiles.length === 0) {
            this.showMessage('Please select files to upload.', 'error');
            return;
        }

        const uploadBtn = document.getElementById('upload-btn');
        const progressSection = document.getElementById('upload-progress');
        
        // Show progress
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
        progressSection.style.display = 'block';
        
        try {
            const formData = new FormData();
            this.selectedFiles.forEach(file => {
                formData.append('files', file);
            });
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.sessionId = data.session_id;
                this.projectStructure = data.project_structure;
                
                this.showMessage(`Successfully uploaded ${data.uploaded_files.length} files!`, 'success');
                this.updateProjectOverview();
                this.goToStep(2);
            } else {
                throw new Error(data.message || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showMessage(`Upload failed: ${error.message}`, 'error');
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Files';
            progressSection.style.display = 'none';
        }
    }

    updateProjectOverview() {
        if (!this.projectStructure) return;
        
        const overview = document.getElementById('project-overview');
        document.getElementById('file-count').textContent = this.projectStructure.total_files;
        document.getElementById('project-size').textContent = this.formatFileSize(this.projectStructure.total_size);
        
        const fileTypes = Object.keys(this.projectStructure.file_types).slice(0, 3).join(', ');
        document.getElementById('file-types').textContent = fileTypes || 'Various';
        
        overview.style.display = 'block';
        this.validateTaskForm();
    }

    validateTaskForm() {
        const taskDescription = document.getElementById('task-description').value.trim();
        const processBtn = document.getElementById('process-btn');
        
        processBtn.disabled = !taskDescription || !this.sessionId;
    }

    async processTask() {
        const taskDescription = document.getElementById('task-description').value.trim();
        
        if (!taskDescription || !this.sessionId) {
            this.showMessage('Please provide a task description.', 'error');
            return;
        }

        const processBtn = document.getElementById('process-btn');
        const progressSection = document.getElementById('process-progress');
        
        // Show progress
        processBtn.disabled = true;
        processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        progressSection.style.display = 'block';
        
        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    task_description: taskDescription
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.displayResults(data.solution);
                this.goToStep(3);
            } else {
                throw new Error(data.message || 'Processing failed');
            }
        } catch (error) {
            console.error('Processing error:', error);
            this.showMessage(`Processing failed: ${error.message}`, 'error');
        } finally {
            processBtn.disabled = false;
            processBtn.innerHTML = '<i class="fas fa-magic"></i> Analyze with AI';
            progressSection.style.display = 'none';
        }
    }

    displayResults(solution) {
        const resultsContent = document.getElementById('results-content');
        
        // Update analysis summary
        document.getElementById('task-type').textContent = solution.analysis.task_type || 'General';
        document.getElementById('main-language').textContent = solution.analysis.main_language || 'Mixed';
        document.getElementById('complexity').textContent = solution.analysis.complexity || 'Medium';
        document.getElementById('files-analyzed').textContent = solution.analysis.files_analyzed || '0';
        
        // Update explanation
        document.getElementById('ai-explanation').textContent = solution.explanation || 'Analysis completed.';
        
        // Update recommendations
        const recommendationsList = document.getElementById('recommendations-list');
        recommendationsList.innerHTML = '';
        
        solution.recommendations.forEach(recommendation => {
            const li = document.createElement('li');
            li.textContent = recommendation;
            recommendationsList.appendChild(li);
        });
        
        // Update code changes
        const codeChangesList = document.getElementById('code-changes-list');
        codeChangesList.innerHTML = '';
        
        solution.code_changes.forEach(change => {
            const changeDiv = document.createElement('div');
            changeDiv.className = 'code-change';
            
            changeDiv.innerHTML = `
                <div class="code-change-header">
                    <h5>${change.file}</h5>
                    <p>${change.description}</p>
                </div>
                <div class="code-change-content">
                    <pre><code class="language-${this.getLanguageFromFile(change.file)}">${this.escapeHtml(change.code)}</code></pre>
                </div>
            `;
            
            codeChangesList.appendChild(changeDiv);
        });
        
        // Show results
        resultsContent.style.display = 'block';
        
        // Highlight code
        if (window.Prism) {
            Prism.highlightAll();
        }
    }

    getLanguageFromFile(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        const languageMap = {
            'py': 'python',
            'js': 'javascript',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'php': 'php',
            'rb': 'ruby',
            'go': 'go',
            'rs': 'rust'
        };
        
        return languageMap[extension] || 'text';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async downloadResults() {
        if (!this.sessionId) {
            this.showMessage('No session to download.', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/download/${this.sessionId}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `manus_result_${this.sessionId}.zip`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showMessage('Results downloaded successfully!', 'success');
            } else {
                throw new Error('Download failed');
            }
        } catch (error) {
            console.error('Download error:', error);
            this.showMessage(`Download failed: ${error.message}`, 'error');
        }
    }

    startNewTask() {
        // Reset the application state
        this.currentStep = 1;
        this.sessionId = null;
        this.selectedFiles = [];
        this.projectStructure = null;
        
        // Reset UI
        document.getElementById('file-list').style.display = 'none';
        document.getElementById('upload-btn').style.display = 'none';
        document.getElementById('project-overview').style.display = 'none';
        document.getElementById('results-content').style.display = 'none';
        document.getElementById('task-description').value = '';
        document.getElementById('file-input').value = '';
        
        // Clear any messages
        const existingMessages = document.querySelectorAll('.message');
        existingMessages.forEach(msg => msg.remove());
        
        this.goToStep(1);
        this.showMessage('Ready for a new task!', 'success');
    }

    goToStep(step) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Show target section
        document.getElementById(`${this.getSectionName(step)}-section`).classList.add('active');
        
        this.currentStep = step;
        this.updateStepNavigation();
    }

    getSectionName(step) {
        const names = ['', 'upload', 'task', 'results'];
        return names[step];
    }

    updateStepNavigation() {
        document.querySelectorAll('.step').forEach((step, index) => {
            const stepNumber = index + 1;
            step.classList.remove('active', 'completed');
            
            if (stepNumber === this.currentStep) {
                step.classList.add('active');
            } else if (stepNumber < this.currentStep) {
                step.classList.add('completed');
            }
        });
    }

    showMessage(text, type = 'info') {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.message');
        existingMessages.forEach(msg => msg.remove());
        
        // Create new message
        const message = document.createElement('div');
        message.className = `message ${type}`;
        message.textContent = text;
        
        // Insert at the top of the current section
        const currentSection = document.querySelector('.section.active');
        currentSection.insertBefore(message, currentSection.firstChild);
        
        // Auto-remove after 5 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                if (message.parentNode) {
                    message.remove();
                }
            }, 5000);
        }
    }
}

// Global functions for template usage
window.setTaskExample = function(example) {
    document.getElementById('task-description').value = example;
    manusApp.validateTaskForm();
};

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.manusApp = new ManusApp();
});

