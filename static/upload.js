// Make entire window a drop zone
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const uploadForm = document.getElementById('uploadForm');
const uploadBtn = document.getElementById('uploadBtn');
const fileInfo = document.getElementById('fileInfo');
const messageDiv = document.getElementById('message');
const uploadProgress = document.getElementById('uploadProgress');
const uploadStatus = document.getElementById('uploadStatus');

let selectedFiles = [];
let dragCounter = 0;

// Click to select file
dropZone.addEventListener('click', () => {
    fileInput.click();
});

// File selected via input
fileInput.addEventListener('change', (e) => {
    handleFiles(Array.from(e.target.files));
});

// Make entire window accept drag and drop
document.addEventListener('dragenter', (e) => {
    e.preventDefault();
    dragCounter++;
    if (dragCounter === 1) {
        document.body.classList.add('dragging');
        dropZone.classList.add('drag-over');
    }
});

document.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dragCounter--;
    if (dragCounter === 0) {
        document.body.classList.remove('dragging');
        dropZone.classList.remove('drag-over');
    }
});

document.addEventListener('dragover', (e) => {
    e.preventDefault();
});

document.addEventListener('drop', (e) => {
    e.preventDefault();
    dragCounter = 0;
    document.body.classList.remove('dragging');
    dropZone.classList.remove('drag-over');
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
        handleFiles(files);
    }
});

function handleFiles(files) {
    if (!files || files.length === 0) return;
    
    const maxSize = 500 * 1024 * 1024; // 500MB
    const validFiles = [];
    const invalidFiles = [];
    
    files.forEach(file => {
        if (file.size > maxSize) {
            invalidFiles.push(`${file.name} (too large)`);
        } else if (file.size === 0) {
            invalidFiles.push(`${file.name} (empty file)`);
        } else {
            validFiles.push(file);
        }
    });
    
    if (invalidFiles.length > 0) {
        showMessage(`Invalid files: ${invalidFiles.join(', ')}`, 'error');
    }
    
    if (validFiles.length === 0) {
        selectedFiles = [];
        fileInfo.innerHTML = '';
        uploadBtn.disabled = true;
        return;
    }
    
    selectedFiles = validFiles;
    displaySelectedFiles();
    uploadBtn.disabled = false;
    
    if (invalidFiles.length === 0) {
        messageDiv.innerHTML = '';
    }
}

function displaySelectedFiles() {
    if (selectedFiles.length === 0) {
        fileInfo.innerHTML = '';
        return;
    }
    
    const totalSize = selectedFiles.reduce((sum, file) => sum + file.size, 0);
    
    let html = `<div class="files-summary">
        <strong>${selectedFiles.length} file(s) selected</strong> 
        <span>(Total: ${formatFileSize(totalSize)})</span>
    </div>
    <ul class="selected-files-list">`;
    
    selectedFiles.forEach((file, index) => {
        html += `
            <li class="selected-file-item">
                <span class="file-name">${file.name}</span>
                <span class="file-size-small">${formatFileSize(file.size)}</span>
                <button type="button" class="remove-file-btn" data-index="${index}">✕</button>
            </li>
        `;
    });
    
    html += '</ul>';
    fileInfo.innerHTML = html;
    
    // Add event listeners to remove buttons
    document.querySelectorAll('.remove-file-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const index = parseInt(e.target.getAttribute('data-index'));
            removeFile(index);
        });
    });
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    displaySelectedFiles();
    
    if (selectedFiles.length === 0) {
        uploadBtn.disabled = true;
        fileInput.value = '';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showMessage(text, type) {
    messageDiv.innerHTML = `<div class="message ${type}-message">${text}</div>`;
}

function updateUploadStatus(current, total, currentFileName) {
    uploadStatus.innerHTML = `
        <div class="upload-status-item">
            Uploading ${current} of ${total}: <strong>${currentFileName}</strong>
        </div>
    `;
}

// Form submission
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (selectedFiles.length === 0) {
        showMessage('Please select at least one file!', 'error');
        return;
    }
    
    const password = document.getElementById('password').value;
    const isPublic = document.querySelector('input[name="is_public"]:checked').value === 'true';
    
    uploadBtn.disabled = true;
    uploadProgress.classList.add('active');
    messageDiv.innerHTML = '';
    uploadStatus.innerHTML = '';
    
    let successCount = 0;
    let failCount = 0;
    const failedFiles = [];
    
    for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        updateUploadStatus(i + 1, selectedFiles.length, file.name);
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('password', password);
        formData.append('is_public', isPublic);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                successCount++;
            } else {
                failCount++;
                failedFiles.push(`${file.name} (${data.detail})`);
            }
        } catch (error) {
            failCount++;
            failedFiles.push(`${file.name} (${error.message})`);
        }
    }
    
    uploadProgress.classList.remove('active');
    uploadStatus.innerHTML = '';
    
    // Show results
    let resultMessage = '';
    if (successCount > 0) {
        resultMessage += `Successfully uploaded ${successCount} file(s)! `;
    }
    if (failCount > 0) {
        resultMessage += `Failed to upload ${failCount} file(s): ${failedFiles.join(', ')}`;
    }
    
    showMessage(resultMessage, failCount === 0 ? 'success' : 'error');
    
    if (successCount > 0) {
        // Reset form
        selectedFiles = [];
        fileInfo.innerHTML = '';
        uploadForm.reset();
        fileInput.value = '';
        uploadBtn.disabled = true;
        
        // Redirect to appropriate page after 3 seconds
        setTimeout(() => {
            window.location.href = isPublic ? '/public' : '/private';
        }, 3000);
    } else {
        uploadBtn.disabled = false;
    }
});