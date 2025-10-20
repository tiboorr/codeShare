// Delete functionality
const deleteModal = document.getElementById('deleteModal');
const deleteForm = document.getElementById('deleteForm');
const deleteFileName = document.getElementById('deleteFileName');
const deletePassword = document.getElementById('deletePassword');
const deleteMessage = document.getElementById('deleteMessage');
const cancelDelete = document.getElementById('cancelDelete');

let currentFileId = null;

// Add click listeners to all delete buttons
document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        currentFileId = btn.getAttribute('data-file-id');
        const filename = btn.getAttribute('data-filename');
        
        deleteFileName.textContent = filename;
        deletePassword.value = '';
        deleteMessage.innerHTML = '';
        deleteModal.classList.add('active');
        
        // Focus password input
        setTimeout(() => deletePassword.focus(), 100);
    });
});

// Cancel delete
cancelDelete.addEventListener('click', () => {
    closeModal();
});

// Close modal on outside click
deleteModal.addEventListener('click', (e) => {
    if (e.target === deleteModal) {
        closeModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && deleteModal.classList.contains('active')) {
        closeModal();
    }
});

function closeModal() {
    deleteModal.classList.remove('active');
    currentFileId = null;
}

// Handle delete form submission
deleteForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!currentFileId) return;
    
    const password = deletePassword.value;
    const formData = new FormData();
    formData.append('password', password);
    
    try {
        const response = await fetch(`/delete/${currentFileId}`, {
            method: 'DELETE',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Show success message
            showDeleteMessage('Datoteka uspešno izbrisana!', 'success');
            
            // Remove file item from DOM with animation
            const fileItem = document.getElementById(`file-${currentFileId}`);
            if (fileItem) {
                fileItem.style.transition = 'all 0.3s ease';
                fileItem.style.opacity = '0';
                fileItem.style.transform = 'translateX(-20px)';
                
                setTimeout(() => {
                    fileItem.remove();
                    
                    // Check if there are no more files
                    const filesList = document.querySelector('.files-list');
                    if (filesList && filesList.children.length === 0) {
                        filesList.innerHTML = '<p class="no-files">Še ni naloženih datotek.</p>';
                    }
                }, 300);
            }
            
            // Close modal after delay
            setTimeout(() => {
                closeModal();
            }, 1500);
            
        } else {
            showDeleteMessage(data.detail || 'Napaka pri brisanju datoteke', 'error');
        }
    } catch (error) {
        showDeleteMessage(`Napaka: ${error.message}`, 'error');
    }
});

function showDeleteMessage(text, type) {
    deleteMessage.innerHTML = `<div class="message ${type}-message">${text}</div>`;
}

// Update file list when empty
function checkEmptyFileList() {
    const filesList = document.querySelector('.files-list');
    if (filesList && filesList.children.length === 0) {
        filesList.innerHTML = '<p class="no-files">Še ni naloženih datotek.</p>';
    }
}