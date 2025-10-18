// Search functionality
const searchInput = document.getElementById('searchInput');
const searchCount = document.getElementById('searchCount');
const filesList = document.getElementById('filesList');
const noResults = document.getElementById('noResults');

if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase().trim();
        const fileItems = document.querySelectorAll('.file-item');
        let visibleCount = 0;

        fileItems.forEach(item => {
            const filename = item.getAttribute('data-filename');
            
            if (filename.includes(searchTerm)) {
                item.style.display = '';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });

        // Update results count
        if (searchTerm) {
            searchCount.textContent = `${visibleCount} result${visibleCount !== 1 ? 's' : ''}`;
            searchCount.style.display = 'inline';
        } else {
            searchCount.style.display = 'none';
        }

        // Show/hide no results message
        if (visibleCount === 0 && searchTerm) {
            noResults.style.display = 'block';
            if (filesList) filesList.style.display = 'none';
        } else {
            noResults.style.display = 'none';
            if (filesList) filesList.style.display = 'block';
        }
    });

    // Clear search on Escape key
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input'));
            searchInput.blur();
        }
    });
}