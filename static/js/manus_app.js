// Manus AI Platform - Enhanced Production JavaScript
// Real-time features, file explorer, and improved error handling

class ManusApp {
    constructor() {
        this.currentStep = 1;
        this.sessionId = null;
        this.uploadedFiles = [];
        this.projectStructure = null;
        this.analysisResult = null;
        this.sessionStartTime = Date.now();
        this.notificationTimeout = 5000;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.setupFileExplorer();
        this.setupNotificationSystem();
        this.startSessionTimer();
        this.checkAPIHealth();
    }

    // Event Listeners
    setupEventListeners() {
        // File input
        const fileInput = document.getElementById('file-input');
        const uploadArea = document.getElementById('upload-area');
        const uploadBtn = document.getElementById('upload-btn');
        const clearFilesBtn = document.getElementById('clear-files');
        
        fileInput?.addEventListener('change', (e) => this.handleFileSelect(e));
        uploadArea?.addEventListener('click', () => fileInput?.click());
        uploadBtn?.addEventListener('click', () => this.uploadFiles());
        clearFilesBtn?.addEventListener('click', () => this.clearFiles());

        // Task description
        const taskDescription = document.getElementById('task-description');
        const analyzeBtn = document.getElementById('analyze-btn');
        
        taskDescription?.addEventListener('input', (e) => this.handleTaskInput(e));
        analyzeBtn?.addEventListener('click', () => this.startAnalysis());

        // File explorer
        const toggleExplorer = document.getElementById('toggle-file-explorer');
        const closeExplorer = document.getElementById('close-file-explorer');
        const fileSearch = document.getElementById('file-search');
        const listView = document.getElementById('list-view');
        const gridView = document.getElementById('grid-view');
        
        toggleExplorer?.addEventListener('click', () => this.toggleFileExplorer());
        closeExplorer?.addEventListener('click', () => this.closeFileExplorer());
        fileSearch?.addEventListener('input', (e) => this.searchFiles(e.target.value));
        listView?.addEventListener('click', () => this.setViewMode('list'));
        gridView?.addEventListener('click', () => this.setViewMode('grid'));

        // Results actions
        const downloadBtn = document.getElementById('download-btn');
        const newAnalysisBtn = document.getElementById('new-analysis-btn');
        const exportResults = document.getElementById('export-results');
        
        downloadBtn?.addEventListener('click', () => this.downloadResults());
        newAnalysisBtn?.addEventListener('click', () => this.startNewAnalysis());
        exportResults?.addEventListener('click', () => this.exportResults());

        // Step navigation
        document.querySelectorAll('.step').forEach((step, index) => {
            step.addEventListener('click', () => this.goToStep(index + 1));
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }

    // Drag and Drop
    setupDragAndDrop() {
        const uploadArea = document.getElementById('upload-area');
        
        if (!uploadArea) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => this.highlight(uploadArea), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => this.unhighlight(uploadArea), false);
        });

        uploadArea.addEventListener('drop', (e) => this.handleDrop(e), false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    highlight(element) {
        element.classList.add('dragover');
    }

    unhighlight(element) {
        element.classList.remove('dragover');
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles(files);
    }

    // File Handling
    handleFileSelect(e) {
        this.handleFiles(e.target.files);
    }

    handleFiles(files) {
        const fileArray = Array.from(files);
        
        // Validate files
        const validFiles = fileArray.filter(file => this.validateFile(file));
        
        if (validFiles.length === 0) {
            this.showNotification('No valid files selected', 'warning');
            return;
        }

        // Add to uploaded files
        this.uploadedFiles = [...this.uploadedFiles, ...validFiles];
        this.updateFileList();
        this.updateUploadButton();
        
        this.showNotification(`${validFiles.length} file(s) added`, 'success');
    }

    validateFile(file) {
        const maxSize = 500 * 1024 * 1024; // 500MB
        const allowedExtensions = [
            'py', 'js', 'ts', 'jsx', 'tsx', 'html', 'css', 'scss', 'sass', 'less',
            'java', 'cpp', 'c', 'h', 'hpp', 'cs', 'php', 'rb', 'go', 'rs', 'swift',
            'kt', 'scala', 'clj', 'hs', 'ml', 'fs', 'vb', 'pas', 'pl', 'r', 'lua',
            'json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf',
            'csv', 'tsv', 'sql', 'db', 'sqlite', 'sqlite3',
            'md', 'rst', 'txt', 'rtf', 'tex', 'adoc', 'org',
            'sh', 'bash', 'zsh', 'fish', 'ps1', 'bat', 'cmd',
            'dockerfile', 'makefile', 'cmake', 'gradle', 'maven',
            'zip', 'tar', 'gz', 'bz2', 'xz', '7z', 'rar',
            'wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac',
            'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv',
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg',
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'
        ];

        // Check file size
        if (file.size > maxSize) {
            this.showNotification(`File "${file.name}" is too large (max 500MB)`, 'error');
            return false;
        }

        // Check file extension
        const extension = file.name.split('.').pop()?.toLowerCase();
        if (!extension || !allowedExtensions.includes(extension)) {
            this.showNotification(`File type "${extension}" is not supported`, 'warning');
            return false;
        }

        return true;
    }

    updateFileList() {
        const fileList = document.getElementById('file-list');
        const fileItems = document.getElementById('file-items');
        const fileCountSummary = document.getElementById('file-count-summary');
        const fileSizeSummary = document.getElementById('file-size-summary');
        
        if (!fileList || !fileItems) return;

        if (this.uploadedFiles.length === 0) {
            fileList.style.display = 'none';
            return;
        }

        fileList.style.display = 'block';
        fileItems.innerHTML = '';

        let totalSize = 0;
        this.uploadedFiles.forEach((file, index) => {
            totalSize += file.size;
            const fileItem = this.createFileItem(file, index);
            fileItems.appendChild(fileItem);
        });

        // Update summary
        if (fileCountSummary) {
            fileCountSummary.textContent = `${this.uploadedFiles.length} file${this.uploadedFiles.length !== 1 ? 's' : ''}`;
        }
        if (fileSizeSummary) {
            fileSizeSummary.textContent = this.formatFileSize(totalSize);
        }
    }

    createFileItem(file, index) {
        const item = document.createElement('div');
        item.className = 'file-item';
        
        const fileType = this.getFileType(file.name);
        const icon = this.getFileIcon(fileType);
        
        item.innerHTML = `
            <div class="file-icon ${fileType}">
                <i class="${icon}"></i>
            </div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-details">
                    <span>${this.formatFileSize(file.size)}</span>
                    <span>${fileType}</span>
                    <span>${new Date(file.lastModified).toLocaleDateString()}</span>
                </div>
            </div>
            <button class="file-remove" onclick="app.removeFile(${index})">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        return item;
    }

    removeFile(index) {
        this.uploadedFiles.splice(index, 1);
        this.updateFileList();
        this.updateUploadButton();
        this.showNotification('File removed', 'info');
    }

    clearFiles() {
        this.uploadedFiles = [];
        this.updateFileList();
        this.updateUploadButton();
        this.showNotification('All files cleared', 'info');
    }

    updateUploadButton() {
        const uploadBtn = document.getElementById('upload-btn');
        if (!uploadBtn) return;

        if (this.uploadedFiles.length > 0) {
            uploadBtn.style.display = 'block';
            uploadBtn.disabled = false;
        } else {
            uploadBtn.style.display = 'none';
        }
    }

    // File Upload
    async uploadFiles() {
        if (this.uploadedFiles.length === 0) {
            this.showNotification('No files to upload', 'warning');
            return;
        }

        this.showLoading('Uploading files...');
        this.showUploadProgress();

        const formData = new FormData();
        this.uploadedFiles.forEach(file => {
            formData.append('files', file);
        });

        try {
            const startTime = Date.now();
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.sessionId = result.session_id;
                this.projectStructure = result.project_structure;
                
                this.hideLoading();
                this.hideUploadProgress();
                this.updateProjectOverview(result);
                this.goToStep(2);
                
                this.showNotification('Files uploaded successfully!', 'success');
                
                // Update header stats
                this.updateHeaderStats();
                
            } else {
                throw new Error(result.message || 'Upload failed');
            }
            
        } catch (error) {
            console.error('Upload error:', error);
            this.hideLoading();
            this.hideUploadProgress();
            this.showNotification(`Upload failed: ${error.message}`, 'error');
        }
    }

    showUploadProgress() {
        const progressSection = document.getElementById('upload-progress');
        if (progressSection) {
            progressSection.style.display = 'block';
            this.animateProgress('upload-progress-fill', 0, 100, 3000);
        }
    }

    hideUploadProgress() {
        const progressSection = document.getElementById('upload-progress');
        if (progressSection) {
            progressSection.style.display = 'none';
        }
    }

    // Task Input
    handleTaskInput(e) {
        const charCount = document.getElementById('char-count');
        const analyzeBtn = document.getElementById('analyze-btn');
        
        const length = e.target.value.length;
        const maxLength = 2000;
        
        if (charCount) {
            charCount.textContent = length;
            charCount.style.color = length > maxLength ? 'var(--error-color)' : 'var(--text-muted)';
        }
        
        if (analyzeBtn) {
            analyzeBtn.disabled = length === 0 || length > maxLength || !this.sessionId;
        }
    }

    // Analysis
    async startAnalysis() {
        const taskDescription = document.getElementById('task-description')?.value;
        
        if (!taskDescription || !this.sessionId) {
            this.showNotification('Please provide a task description', 'warning');
            return;
        }

        this.showLoading('Starting AI analysis...');
        this.showAnalysisProgress();

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    task_description: taskDescription
                })
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.hideLoading();
                this.showNotification('Analysis started!', 'success');
                this.pollAnalysisStatus();
            } else {
                throw new Error(result.message || 'Analysis failed to start');
            }
            
        } catch (error) {
            console.error('Analysis error:', error);
            this.hideLoading();
            this.hideAnalysisProgress();
            this.showNotification(`Analysis failed: ${error.message}`, 'error');
        }
    }

    async pollAnalysisStatus() {
        const pollInterval = 2000; // 2 seconds
        
        const poll = async () => {
            try {
                const response = await fetch(`/api/status/${this.sessionId}`);
                const result = await response.json();
                
                if (result.status === 'success') {
                    const analysisStatus = result.analysis_status;
                    
                    this.updateAnalysisProgress(analysisStatus);
                    
                    if (analysisStatus === 'completed') {
                        this.analysisResult = result.result;
                        this.hideLoading();
                        this.hideAnalysisProgress();
                        this.displayResults(result.result);
                        this.goToStep(3);
                        this.showNotification('Analysis completed!', 'success');
                        return;
                    } else if (analysisStatus === 'failed') {
                        throw new Error(result.error || 'Analysis failed');
                    }
                    
                    // Continue polling
                    setTimeout(poll, pollInterval);
                } else {
                    throw new Error(result.message || 'Failed to get analysis status');
                }
                
            } catch (error) {
                console.error('Polling error:', error);
                this.hideLoading();
                this.hideAnalysisProgress();
                this.showNotification(`Analysis error: ${error.message}`, 'error');
            }
        };
        
        poll();
    }

    showAnalysisProgress() {
        const progressSection = document.getElementById('analyze-progress');
        if (progressSection) {
            progressSection.style.display = 'block';
            this.animateAnalysisSteps();
        }
    }

    hideAnalysisProgress() {
        const progressSection = document.getElementById('analyze-progress');
        if (progressSection) {
            progressSection.style.display = 'none';
        }
    }

    updateAnalysisProgress(status) {
        const progressFill = document.getElementById('analyze-progress-fill');
        const analyzeStatus = document.getElementById('analyze-status');
        const analyzePercentage = document.getElementById('analyze-percentage');
        
        let percentage = 0;
        let statusText = 'Starting analysis...';
        
        switch (status) {
            case 'running':
                percentage = 50;
                statusText = 'AI analysis in progress...';
                break;
            case 'completed':
                percentage = 100;
                statusText = 'Analysis completed!';
                break;
            case 'failed':
                percentage = 0;
                statusText = 'Analysis failed';
                break;
        }
        
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
        if (analyzeStatus) {
            analyzeStatus.textContent = statusText;
        }
        if (analyzePercentage) {
            analyzePercentage.textContent = `${percentage}%`;
        }
    }

    animateAnalysisSteps() {
        const steps = document.querySelectorAll('.step-item');
        let currentStep = 0;
        
        const animateStep = () => {
            if (currentStep < steps.length) {
                steps[currentStep].classList.add('active');
                
                if (currentStep > 0) {
                    steps[currentStep - 1].classList.remove('active');
                    steps[currentStep - 1].classList.add('completed');
                }
                
                currentStep++;
                setTimeout(animateStep, 1500);
            }
        };
        
        animateStep();
    }

    // Results Display
    displayResults(result) {
        const resultsContent = document.getElementById('results-content');
        if (!resultsContent) return;

        resultsContent.style.display = 'block';

        // Update analysis metrics
        this.updateAnalysisMetrics(result.analysis || {});
        
        // Update summary
        this.updateSummary(result.summary || 'No summary available');
        
        // Update recommendations
        this.updateRecommendations(result.recommendations || []);
        
        // Update code changes
        this.updateCodeChanges(result.code_changes || []);
        
        // Update security issues
        this.updateSecurityIssues(result.security_issues || []);
        
        // Update performance issues
        this.updatePerformanceIssues(result.performance_issues || []);
        
        // Update next steps
        this.updateNextSteps(result.next_steps || []);
    }

    updateAnalysisMetrics(analysis) {
        const taskType = document.getElementById('task-type');
        const mainLanguage = document.getElementById('main-language');
        const complexity = document.getElementById('complexity');
        const filesAnalyzed = document.getElementById('files-analyzed');
        
        if (taskType) taskType.textContent = analysis.task_type || '-';
        if (mainLanguage) mainLanguage.textContent = analysis.main_language || '-';
        if (complexity) complexity.textContent = analysis.complexity || '-';
        if (filesAnalyzed) filesAnalyzed.textContent = analysis.files_analyzed || '-';
    }

    updateSummary(summary) {
        const summaryElement = document.getElementById('ai-summary');
        if (summaryElement) {
            summaryElement.innerHTML = `<p>${summary}</p>`;
        }
    }

    updateRecommendations(recommendations) {
        const list = document.getElementById('recommendations-list');
        const count = document.getElementById('recommendation-count');
        
        if (count) count.textContent = recommendations.length;
        
        if (list) {
            list.innerHTML = recommendations.map(rec => `
                <div class="recommendation-item">
                    <i class="fas fa-lightbulb"></i>
                    <div class="content">${rec}</div>
                </div>
            `).join('');
        }
    }

    updateCodeChanges(changes) {
        const list = document.getElementById('code-changes-list');
        const count = document.getElementById('changes-count');
        
        if (count) count.textContent = changes.length;
        
        if (list) {
            list.innerHTML = changes.map(change => `
                <div class="code-change-item">
                    <div class="code-change-header">
                        <div class="code-change-info">
                            <div class="code-change-file">${change.file}</div>
                            <div class="code-change-description">${change.description}</div>
                        </div>
                        <div class="code-change-type ${change.type}">${change.type}</div>
                    </div>
                    ${change.code ? `
                        <div class="code-change-content">
                            <pre><code class="language-${this.getLanguageFromFile(change.file)}">${change.code}</code></pre>
                        </div>
                    ` : ''}
                </div>
            `).join('');
            
            // Highlight code
            if (window.Prism) {
                Prism.highlightAll();
            }
        }
    }

    updateSecurityIssues(issues) {
        const list = document.getElementById('security-issues-list');
        const count = document.getElementById('security-count');
        
        if (count) count.textContent = issues.length;
        
        if (list) {
            list.innerHTML = issues.length > 0 ? issues.map(issue => `
                <div class="issue-item">
                    <i class="fas fa-shield-alt"></i>
                    <div class="content">${issue}</div>
                </div>
            `).join('') : '<p class="no-issues">No security issues found</p>';
        }
    }

    updatePerformanceIssues(issues) {
        const list = document.getElementById('performance-issues-list');
        const count = document.getElementById('performance-count');
        
        if (count) count.textContent = issues.length;
        
        if (list) {
            list.innerHTML = issues.length > 0 ? issues.map(issue => `
                <div class="issue-item">
                    <i class="fas fa-tachometer-alt"></i>
                    <div class="content">${issue}</div>
                </div>
            `).join('') : '<p class="no-issues">No performance issues found</p>';
        }
    }

    updateNextSteps(steps) {
        const list = document.getElementById('next-steps-list');
        
        if (list) {
            list.innerHTML = steps.map(step => `
                <div class="step-item-result">
                    <i class="fas fa-arrow-right"></i>
                    <div class="content">${step}</div>
                </div>
            `).join('');
        }
    }

    // File Explorer
    setupFileExplorer() {
        // File explorer setup is handled by event listeners
    }

    toggleFileExplorer() {
        const modal = document.getElementById('file-explorer-modal');
        if (modal) {
            modal.classList.add('active');
            this.loadFileExplorer();
        }
    }

    closeFileExplorer() {
        const modal = document.getElementById('file-explorer-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    async loadFileExplorer() {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`/api/sessions/${this.sessionId}/files`);
            const result = await response.json();
            
            if (result.status === 'success') {
                this.renderFileTree(result.project_structure);
            }
        } catch (error) {
            console.error('Error loading file explorer:', error);
            this.showNotification('Failed to load file explorer', 'error');
        }
    }

    renderFileTree(structure) {
        const content = document.getElementById('file-explorer-content');
        if (!content || !structure) return;

        const files = structure.files || [];
        
        content.innerHTML = `
            <div class="file-tree">
                ${files.map(file => `
                    <div class="file-tree-item" onclick="app.selectFile('${file.path}')">
                        <i class="${this.getFileIcon(file.type)}"></i>
                        <span class="file-name">${file.path}</span>
                        <span class="file-size">${file.formatted_size}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async selectFile(filePath) {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`/api/sessions/${this.sessionId}/file/${encodeURIComponent(filePath)}`);
            const result = await response.json();
            
            if (result.status === 'success') {
                this.showFileContent(result);
            }
        } catch (error) {
            console.error('Error loading file content:', error);
            this.showNotification('Failed to load file content', 'error');
        }
    }

    showFileContent(fileData) {
        // This could open a modal or sidebar with file content
        console.log('File content:', fileData);
    }

    searchFiles(query) {
        const items = document.querySelectorAll('.file-tree-item');
        
        items.forEach(item => {
            const fileName = item.querySelector('.file-name').textContent.toLowerCase();
            const matches = fileName.includes(query.toLowerCase());
            item.style.display = matches ? 'flex' : 'none';
        });
    }

    setViewMode(mode) {
        const listBtn = document.getElementById('list-view');
        const gridBtn = document.getElementById('grid-view');
        
        if (mode === 'list') {
            listBtn?.classList.add('active');
            gridBtn?.classList.remove('active');
        } else {
            gridBtn?.classList.add('active');
            listBtn?.classList.remove('active');
        }
        
        // Update view (implementation depends on requirements)
    }

    // Utility Functions
    getFileType(filename) {
        const extension = filename.split('.').pop()?.toLowerCase();
        
        const codeExtensions = ['py', 'js', 'ts', 'jsx', 'tsx', 'html', 'css', 'java', 'cpp', 'c', 'php', 'rb', 'go', 'rs'];
        const dataExtensions = ['json', 'xml', 'yaml', 'yml', 'csv', 'sql'];
        const mediaExtensions = ['wav', 'mp3', 'mp4', 'mov', 'jpg', 'jpeg', 'png', 'gif'];
        const archiveExtensions = ['zip', 'tar', 'gz', 'bz2', 'xz', '7z'];
        
        if (codeExtensions.includes(extension)) return 'code';
        if (dataExtensions.includes(extension)) return 'data';
        if (mediaExtensions.includes(extension)) return 'media';
        if (archiveExtensions.includes(extension)) return 'archive';
        
        return 'other';
    }

    getFileIcon(type) {
        const icons = {
            code: 'fas fa-code',
            data: 'fas fa-database',
            media: 'fas fa-photo-video',
            archive: 'fas fa-file-archive',
            other: 'fas fa-file'
        };
        
        return icons[type] || icons.other;
    }

    getLanguageFromFile(filename) {
        const extension = filename.split('.').pop()?.toLowerCase();
        const languageMap = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'jsx': 'jsx',
            'tsx': 'tsx',
            'html': 'html',
            'css': 'css',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'php': 'php',
            'rb': 'ruby',
            'go': 'go',
            'rs': 'rust',
            'json': 'json',
            'xml': 'xml',
            'yaml': 'yaml',
            'yml': 'yaml'
        };
        
        return languageMap[extension] || 'text';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    // Navigation
    goToStep(step) {
        if (step < 1 || step > 3) return;
        
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Show target section
        const targetSection = document.getElementById(`${this.getSectionName(step)}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        // Update step navigation
        document.querySelectorAll('.step').forEach((stepEl, index) => {
            stepEl.classList.remove('active', 'completed');
            
            if (index + 1 === step) {
                stepEl.classList.add('active');
            } else if (index + 1 < step) {
                stepEl.classList.add('completed');
            }
        });
        
        // Update step connectors
        document.querySelectorAll('.step-connector').forEach((connector, index) => {
            connector.classList.toggle('active', index + 1 < step);
        });
        
        this.currentStep = step;
    }

    getSectionName(step) {
        const names = ['upload', 'task', 'results'];
        return names[step - 1] || 'upload';
    }

    // Project Overview
    updateProjectOverview(uploadResult) {
        const overview = document.getElementById('project-overview');
        if (!overview) return;

        overview.style.display = 'block';

        const structure = uploadResult.project_structure;
        
        // Update overview stats
        const fileCount = document.getElementById('file-count');
        const projectSize = document.getElementById('project-size');
        const codeFilesCount = document.getElementById('code-files-count');
        const mediaFilesCount = document.getElementById('media-files-count');
        
        if (fileCount) fileCount.textContent = structure.total_files || 0;
        if (projectSize) projectSize.textContent = structure.formatted_size || '0 KB';
        if (codeFilesCount) codeFilesCount.textContent = structure.code_files_count || 0;
        if (mediaFilesCount) mediaFilesCount.textContent = structure.media_files_count || 0;
        
        // Update file types
        this.updateFileTypes(structure.file_types || {});
    }

    updateFileTypes(fileTypes) {
        const list = document.getElementById('file-types-list');
        if (!list) return;

        list.innerHTML = Object.entries(fileTypes)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10)
            .map(([ext, count]) => `
                <div class="file-type-tag">
                    ${ext}
                    <span class="count">${count}</span>
                </div>
            `).join('');
    }

    updateHeaderStats() {
        const headerStats = document.getElementById('header-stats');
        const filesCount = document.getElementById('files-count');
        const totalSize = document.getElementById('total-size');
        const sessionTime = document.getElementById('session-time');
        
        if (headerStats && this.projectStructure) {
            headerStats.style.display = 'flex';
            
            if (filesCount) {
                filesCount.textContent = this.projectStructure.total_files || 0;
            }
            if (totalSize) {
                totalSize.textContent = this.projectStructure.formatted_size || '0 KB';
            }
        }
    }

    // Session Timer
    startSessionTimer() {
        setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.sessionStartTime) / 1000);
            const sessionTime = document.getElementById('session-time');
            
            if (sessionTime) {
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                sessionTime.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }

    // Progress Animation
    animateProgress(elementId, start, end, duration) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const current = start + (end - start) * progress;
            
            element.style.width = `${current}%`;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }

    // Loading States
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        const messageEl = document.getElementById('loading-message');
        
        if (overlay) {
            overlay.classList.add('active');
        }
        if (messageEl) {
            messageEl.textContent = message;
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }

    // Notification System
    setupNotificationSystem() {
        // Notification system is ready
    }

    showNotification(message, type = 'info', duration = this.notificationTimeout) {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icons = {
            success: 'fas fa-check',
            error: 'fas fa-exclamation-triangle',
            warning: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle'
        };
        
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="${icons[type] || icons.info}"></i>
            </div>
            <div class="notification-content">
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(notification);
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, duration);
        }
    }

    // API Health Check
    async checkAPIHealth() {
        try {
            const response = await fetch('/api/health');
            const result = await response.json();
            
            if (result.status === 'healthy') {
                console.log('API is healthy:', result);
            } else {
                this.showNotification('API health check failed', 'warning');
            }
        } catch (error) {
            console.error('Health check failed:', error);
            this.showNotification('Unable to connect to API', 'error');
        }
    }

    // Downloads
    async downloadResults() {
        if (!this.sessionId) {
            this.showNotification('No session to download', 'warning');
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
                
                this.showNotification('Results downloaded successfully', 'success');
            } else {
                throw new Error('Download failed');
            }
        } catch (error) {
            console.error('Download error:', error);
            this.showNotification('Download failed', 'error');
        }
    }

    exportResults() {
        if (!this.analysisResult) {
            this.showNotification('No results to export', 'warning');
            return;
        }

        const data = JSON.stringify(this.analysisResult, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `manus_analysis_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        this.showNotification('Results exported successfully', 'success');
    }

    // New Analysis
    startNewAnalysis() {
        // Reset state
        this.sessionId = null;
        this.uploadedFiles = [];
        this.projectStructure = null;
        this.analysisResult = null;
        this.sessionStartTime = Date.now();
        
        // Reset UI
        document.getElementById('task-description').value = '';
        document.getElementById('file-input').value = '';
        this.updateFileList();
        this.updateUploadButton();
        
        // Hide sections
        document.getElementById('project-overview').style.display = 'none';
        document.getElementById('results-content').style.display = 'none';
        document.getElementById('header-stats').style.display = 'none';
        
        // Go to first step
        this.goToStep(1);
        
        this.showNotification('Ready for new analysis', 'info');
    }

    // Keyboard Shortcuts
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Enter to proceed to next step
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            
            if (this.currentStep === 1 && this.uploadedFiles.length > 0) {
                this.uploadFiles();
            } else if (this.currentStep === 2 && document.getElementById('task-description').value) {
                this.startAnalysis();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            this.closeFileExplorer();
        }
    }
}

// Task Examples
function setTaskExample(text) {
    const textarea = document.getElementById('task-description');
    if (textarea) {
        textarea.value = text;
        textarea.dispatchEvent(new Event('input'));
        textarea.focus();
    }
}

// Footer Functions
function showHelp() {
    app.showNotification('Help documentation coming soon!', 'info');
}

function showDocumentation() {
    app.showNotification('Documentation available on GitHub', 'info');
}

function reportIssue() {
    app.showNotification('Please report issues on our GitHub repository', 'info');
}

function showPrivacy() {
    app.showNotification('Privacy policy coming soon', 'info');
}

function showTerms() {
    app.showNotification('Terms of service coming soon', 'info');
}

function showStatus() {
    app.checkAPIHealth();
}

// Initialize app when DOM is loaded
let app;

document.addEventListener('DOMContentLoaded', () => {
    app = new ManusApp();
    console.log('Manus AI Platform initialized');
});

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    if (app) {
        app.showNotification('An unexpected error occurred', 'error');
    }
});

// Service worker registration (for future PWA features)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}

