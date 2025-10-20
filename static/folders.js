// Folder management functionality
const folderList = document.getElementById('folderList');
const newFolderBtn = document.getElementById('newFolderBtn');
const newFolderModal = document.getElementById('newFolderModal');
const newFolderForm = document.getElementById('newFolderForm');
const folderNameInput = document.getElementById('folderName');
const newFolderMessage = document.getElementById('newFolderMessage');
const cancelNewFolder = document.getElementById('cancelNewFolder');

const renameFolderModal = document.getElementById('renameFolderModal');
const renameFolderForm = document.getElementById('renameFolderForm');
const renameFolderNameInput = document.getElementById('renameFolderName');
const renameFolderMessage = document.getElementById('renameFolderMessage');
const cancelRenameFolder = document.getElementById('cancelRenameFolder');

const assignFolderModal = document.getElementById('assignFolderModal');
const assignFileName = document.getElementById('assignFileName');
const folderCheckboxList = document.getElementById('folderCheckboxList');
const saveAssignments = document.getElementById('saveAssignments');
const cancelAssignFolder = document.getElementById('cancelAssignFolder');
const assignFolderMessage = document.getElementById('assignFolderMessage');

let folders = [];
let currentRenameFolderId = null;
let currentAssignFileId = null;
let currentAssignFileDbId = null;

// Load folders on page load
document.addEventListener('DOMContentLoaded', () => {
    loadFolders();
    updateUncategorizedCount();
});

// New folder button
newFolderBtn.addEventListener('click', () => {
    folderNameInput.value = '';
    newFolderMessage.innerHTML = '';
    newFolderModal.classList.add('active');
    setTimeout(() => folderNameInput.focus(), 100);
});

// Cancel new folder
cancelNewFolder.addEventListener('click', () => {
    closeModal(newFolderModal);
});

// Cancel rename folder
cancelRenameFolder.addEventListener('click', () => {
    closeModal(renameFolderModal);
    currentRenameFolderId = null;
});

// Cancel assign folder
cancelAssignFolder.addEventListener('click', () => {
    closeModal(assignFolderModal);
    currentAssignFileId = null;
    currentAssignFileDbId = null;
});

// Close modals on outside click
[newFolderModal, renameFolderModal, assignFolderModal].forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal(modal);
        }
    });
});

// Close modals on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        if (newFolderModal.classList.contains('active')) {
            closeModal(newFolderModal);
        }
        if (renameFolderModal.classList.contains('active')) {
            closeModal(renameFolderModal);
            currentRenameFolderId = null;
        }
        if (assignFolderModal.classList.contains('active')) {
            closeModal(assignFolderModal);
            currentAssignFileId = null;
            currentAssignFileDbId = null;
        }
    }
});

function closeModal(modal) {
    modal.classList.remove('active');
}

// Create new folder
newFolderForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = folderNameInput.value.trim();
    if (!name) return;
    
    const password = prompt('Vnesite geslo za nalaganje:');
    if (!password) return;
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('is_public', window.isPublicView);
    formData.append('password', password);
    
    try {
        const response = await fetch('/api/folders', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showFolderMessage(newFolderMessage, 'Mapa uspešno ustvarjena!', 'success');
            setTimeout(() => {
                closeModal(newFolderModal);
                loadFolders();
            }, 1000);
        } else {
            showFolderMessage(newFolderMessage, data.detail || 'Napaka pri ustvarjanju mape', 'error');
        }
    } catch (error) {
        showFolderMessage(newFolderMessage, `Napaka: ${error.message}`, 'error');
    }
});

// Rename folder
renameFolderForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!currentRenameFolderId) return;
    
    const name = renameFolderNameInput.value.trim();
    if (!name) return;
    
    const password = prompt('Vnesite geslo za nalaganje:');
    if (!password) return;
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('password', password);
    
    try {
        const response = await fetch(`/api/folders/${currentRenameFolderId}`, {
            method: 'PUT',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showFolderMessage(renameFolderMessage, 'Mapa uspešno preimenovana!', 'success');
            setTimeout(() => {
                closeModal(renameFolderModal);
                currentRenameFolderId = null;
                loadFolders();
            }, 1000);
        } else {
            showFolderMessage(renameFolderMessage, data.detail || 'Napaka pri preimenovanju mape', 'error');
        }
    } catch (error) {
        showFolderMessage(renameFolderMessage, `Napaka: ${error.message}`, 'error');
    }
});

// Load folders from API
async function loadFolders() {
    try {
        let url = `/api/folders?is_public=${window.isPublicView}`;
        if (!window.isPublicView && window.privatePassword) {
            url += `&password=${encodeURIComponent(window.privatePassword)}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (response.ok) {
            folders = data.folders;
            renderFolders();
            updateUncategorizedCount();
        }
    } catch (error) {
        console.error('Error loading folders:', error);
    }
}

// Render folders in sidebar
function renderFolders() {
    // Keep uncategorized, clear the rest
    const uncategorized = folderList.querySelector('.uncategorized');
    folderList.innerHTML = '';
    folderList.appendChild(uncategorized);
    
    folders.forEach(folder => {
        const folderItem = document.createElement('div');
        folderItem.className = 'folder-item';
        folderItem.dataset.folderId = folder.id;
        
        folderItem.innerHTML = `
            <span class="folder-icon">📁</span>
            <span class="folder-name">${escapeHtml(folder.name)}</span>
            <span class="folder-count">${folder.file_count}</span>
            <div class="folder-actions">
                <button class="btn-icon rename-folder" title="Preimenuj">✏️</button>
                <button class="btn-icon delete-folder" title="Izbriši">🗑️</button>
            </div>
        `;
        
        folderList.appendChild(folderItem);
        
        // Click to filter
        folderItem.addEventListener('click', (e) => {
            if (!e.target.classList.contains('btn-icon')) {
                filterByFolder(folder.id);
                setActiveFolder(folderItem);
            }
        });
        
        // Rename folder
        folderItem.querySelector('.rename-folder').addEventListener('click', (e) => {
            e.stopPropagation();
            currentRenameFolderId = folder.id;
            renameFolderNameInput.value = folder.name;
            renameFolderMessage.innerHTML = '';
            renameFolderModal.classList.add('active');
            setTimeout(() => renameFolderNameInput.focus(), 100);
        });
        
        // Delete folder
        folderItem.querySelector('.delete-folder').addEventListener('click', async (e) => {
            e.stopPropagation();
            
            if (!confirm(`Ali ste prepričani, da želite izbrisati mapo "${folder.name}"?\nDatoteke bodo ostale, vendar ne bodo več v mapi.`)) {
                return;
            }
            
            const password = prompt('Vnesite geslo za brisanje:');
            if (!password) return;
            
            const formData = new FormData();
            formData.append('password', password);
            
            try {
                const response = await fetch(`/api/folders/${folder.id}`, {
                    method: 'DELETE',
                    body: formData
                });
                
                if (response.ok) {
                    loadFolders();
                    filterByFolder('uncategorized');
                } else {
                    const data = await response.json();
                    alert(data.detail || 'Napaka pri brisanju mape');
                }
            } catch (error) {
                alert(`Napaka: ${error.message}`);
            }
        });
    });
}

// Filter files by folder
function filterByFolder(folderId) {
    const fileItems = document.querySelectorAll('.file-item');
    
    fileItems.forEach(item => {
        const fileFolders = item.dataset.folders ? item.dataset.folders.split(',') : [];
        
        if (folderId === 'uncategorized') {
            // Show files with no folders
            item.style.display = fileFolders.length === 0 || fileFolders[0] === '' ? '' : 'none';
        } else {
            // Show files in this folder
            item.style.display = fileFolders.includes(String(folderId)) ? '' : 'none';
        }
    });
    
    // Clear search when filtering by folder
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = '';
        searchInput.dispatchEvent(new Event('input'));
    }
}

// Set active folder in sidebar
function setActiveFolder(folderItem) {
    document.querySelectorAll('.folder-item').forEach(item => {
        item.classList.remove('active');
    });
    folderItem.classList.add('active');
}

// Update uncategorized count
function updateUncategorizedCount() {
    const fileItems = document.querySelectorAll('.file-item');
    let uncategorizedCount = 0;
    
    fileItems.forEach(item => {
        const fileFolders = item.dataset.folders ? item.dataset.folders.split(',') : [];
        if (fileFolders.length === 0 || fileFolders[0] === '') {
            uncategorizedCount++;
        }
    });
    
    const uncategorizedCountEl = document.getElementById('uncategorizedCount');
    if (uncategorizedCountEl) {
        uncategorizedCountEl.textContent = uncategorizedCount;
    }
}

// Set up assign to folder buttons
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.btn-folder-assign').forEach(btn => {
        btn.addEventListener('click', async () => {
            currentAssignFileId = btn.dataset.fileId;
            currentAssignFileDbId = btn.dataset.fileDbId;
            const filename = btn.dataset.filename;
            
            assignFileName.textContent = filename;
            assignFolderMessage.innerHTML = '';
            
            // Render folder checkboxes
            const fileFoldersEl = btn.closest('.file-item');
            const currentFolders = fileFoldersEl.dataset.folders ? 
                fileFoldersEl.dataset.folders.split(',').map(id => parseInt(id)) : [];
            
            let html = '';
            folders.forEach(folder => {
                const checked = currentFolders.includes(folder.id) ? 'checked' : '';
                html += `
                    <label class="folder-checkbox-item">
                        <input type="checkbox" value="${folder.id}" ${checked}>
                        <span>${escapeHtml(folder.name)}</span>
                    </label>
                `;
            });
            
            if (folders.length === 0) {
                html = '<p class="no-folders">Ni map. Ustvarite prvo mapo!</p>';
            }
            
            folderCheckboxList.innerHTML = html;
            assignFolderModal.classList.add('active');
        });
    });
});

// Save folder assignments
saveAssignments.addEventListener('click', async () => {
    if (!currentAssignFileId || !currentAssignFileDbId) return;
    
    const password = prompt('Vnesite geslo za nalaganje:');
    if (!password) return;
    
    const checkboxes = folderCheckboxList.querySelectorAll('input[type="checkbox"]');
    const selectedFolders = [];
    checkboxes.forEach(cb => {
        if (cb.checked) {
            selectedFolders.push(parseInt(cb.value));
        }
    });
    
    // Get current folders for this file
    const fileItem = document.querySelector(`#file-${currentAssignFileId}`);
    const currentFolders = fileItem.dataset.folders ? 
        fileItem.dataset.folders.split(',').map(id => parseInt(id)).filter(id => !isNaN(id)) : [];
    
    // Determine what to add and remove
    const toAdd = selectedFolders.filter(id => !currentFolders.includes(id));
    const toRemove = currentFolders.filter(id => !selectedFolders.includes(id));
    
    try {
        // Add to folders
        for (const folderId of toAdd) {
            const formData = new FormData();
            formData.append('file_id', currentAssignFileId);
            formData.append('password', password);
            
            const response = await fetch(`/api/folders/${folderId}/files`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Napaka pri dodajanju datoteke v mapo');
            }
        }
        
        // Remove from folders
        for (const folderId of toRemove) {
            const formData = new FormData();
            formData.append('password', password);
            
            const response = await fetch(`/api/folders/${folderId}/files/${currentAssignFileId}`, {
                method: 'DELETE',
                body: formData
            });
            
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Napaka pri odstranjevanju datoteke iz mape');
            }
        }
        
        showFolderMessage(assignFolderMessage, 'Mape uspešno posodobljene!', 'success');
        
        setTimeout(() => {
            closeModal(assignFolderModal);
            currentAssignFileId = null;
            currentAssignFileDbId = null;
            // Reload page to update folder assignments
            window.location.reload();
        }, 1000);
        
    } catch (error) {
        showFolderMessage(assignFolderMessage, error.message, 'error');
    }
});

// Show message in folder modal
function showFolderMessage(element, text, type) {
    element.innerHTML = `<div class="message ${type}-message">${text}</div>`;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Click on uncategorized folder
document.querySelector('.uncategorized').addEventListener('click', () => {
    filterByFolder('uncategorized');
    setActiveFolder(document.querySelector('.uncategorized'));
});
