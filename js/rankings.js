// Rankings page functionality

document.addEventListener('DOMContentLoaded', function() {
    const limitSelect = document.getElementById('limit-select');
    const sortSelect = document.getElementById('sort-select');
    const toggleOnePieceBtn = document.getElementById('toggle-onepiece');
    const updateBtn = document.getElementById('update-btn');
    const table = document.getElementById('rankings-table');
    const tbody = table.querySelector('tbody');
    
    // Store original data
    let originalRows = Array.from(tbody.querySelectorAll('tr'));
    
    // Update functionality
    if (updateBtn) {
        updateBtn.addEventListener('click', function() {
            showUpdateModal();
        });
    }
    
    // Limit selector
    if (limitSelect) {
        limitSelect.addEventListener('change', function() {
        const limit = this.value;
        const rows = tbody.querySelectorAll('tr');
        
        rows.forEach((row, index) => {
            if (limit === 'all') {
                row.style.display = '';
            } else {
                const numLimit = parseInt(limit);
                row.style.display = index < numLimit ? '' : 'none';
            }
        });
        
        // Update rank numbers
        updateRankNumbers();
        });
    }
    
    // Sort functionality
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            sortTable(this.value);
        });
    }
    
    // Column header sorting
    const sortableHeaders = table.querySelectorAll('th.sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const sortType = this.dataset.sort;
            if (sortSelect) sortSelect.value = sortType;
            sortTable(sortType);
        });
    });
    
    // One Piece toggle
    if (toggleOnePieceBtn) {
        toggleOnePieceBtn.addEventListener('click', function() {
        const isHidden = this.dataset.hidden === 'true';
        const onePieceRow = tbody.querySelector('tr .anime-title a[href*="anime/21"]')?.closest('tr');
        
        if (onePieceRow) {
            if (isHidden) {
                // Show One Piece
                onePieceRow.style.display = '';
                this.textContent = '🏴‍☠️ Hide One Piece';
                this.dataset.hidden = 'false';
            } else {
                // Hide One Piece
                onePieceRow.style.display = 'none';
                this.textContent = '🏴‍☠️ Show One Piece';
                this.dataset.hidden = 'true';
            }
            
            // Update rank numbers
            updateRankNumbers();
        }
        });
    }
    
    function sortTable(sortType) {
        let rows = Array.from(tbody.querySelectorAll('tr'));
        
        rows.sort((a, b) => {
            switch(sortType) {
                case 'overall':
                    const aOverallElem = a.querySelector('.overall-score strong');
                    const bOverallElem = b.querySelector('.overall-score strong');
                    const aOverall = aOverallElem ? parseFloat(aOverallElem.textContent) || 0 : 0;
                    const bOverall = bOverallElem ? parseFloat(bOverallElem.textContent) || 0 : 0;
                    return bOverall - aOverall;
                
                case 'anilist':
                    const aRankElem = a.querySelector('.anilist-data strong');
                    const bRankElem = b.querySelector('.anilist-data strong');
                    const aRank = aRankElem ? parseInt(aRankElem.textContent.replace('#', '')) || 999 : 999;
                    const bRank = bRankElem ? parseInt(bRankElem.textContent.replace('#', '')) || 999 : 999;
                    return aRank - bRank;
                
                case 'mal':
                    const aMalElem = a.querySelector('.mal-data strong');
                    const bMalElem = b.querySelector('.mal-data strong');
                    const aMal = aMalElem ? parseFloat(aMalElem.textContent) || 0 : 0;
                    const bMal = bMalElem ? parseFloat(bMalElem.textContent) || 0 : 0;
                    return bMal - aMal;
                
                case 'anitrendz':
                    const aAniElem = a.querySelector('.anitrendz-data strong');
                    const bAniElem = b.querySelector('.anitrendz-data strong');
                    const aAni = aAniElem ? parseInt(aAniElem.textContent.replace('#', '')) || 999 : 999;
                    const bAni = bAniElem ? parseInt(bAniElem.textContent.replace('#', '')) || 999 : 999;
                    return aAni - bAni;
                
                case 'weekly':
                    const aWeeklyElem = a.querySelector('.weekly-score strong');
                    const bWeeklyElem = b.querySelector('.weekly-score strong');
                    const aWeekly = aWeeklyElem ? parseFloat(aWeeklyElem.textContent) || 0 : 0;
                    const bWeekly = bWeeklyElem ? parseFloat(bWeeklyElem.textContent) || 0 : 0;
                    return bWeekly - aWeekly;
                
                default:
                    return 0;
            }
        });
        
        // Clear and re-append sorted rows
        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));
        
        // Update rank numbers and medals
        updateRankNumbers();
    }
    
    function updateRankNumbers() {
        const visibleRows = Array.from(tbody.querySelectorAll('tr')).filter(row => row.style.display !== 'none');
        
        visibleRows.forEach((row, index) => {
            const rankCell = row.querySelector('.rank');
            const rank = index + 1;
            let medal = '';
            
            if (rank === 1) medal = '🥇';
            else if (rank === 2) medal = '🥈';
            else if (rank === 3) medal = '🥉';
            
            rankCell.textContent = `${rank} ${medal}`;
        });
    }
    
    // Update modal functions
    function showUpdateModal() {
        const modal = document.getElementById('update-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalStatus = document.getElementById('modal-status');
        const modalClose = document.getElementById('modal-close');
        const spinner = document.querySelector('.loading-spinner');
        
        // Reset modal state
        modalTitle.textContent = 'Updating Rankings...';
        modalStatus.innerHTML = '<p>🔄 Starting update process...</p>';
        modalClose.style.display = 'none';
        spinner.style.display = 'block';
        modal.style.display = 'flex';
        
        // Start the update process
        performUpdate();
    }
    
    async function performUpdate() {
        const modalStatus = document.getElementById('modal-status');
        const modalTitle = document.getElementById('modal-title');
        const modalClose = document.getElementById('modal-close');
        const spinner = document.querySelector('.loading-spinner');
        
        try {
            modalStatus.innerHTML = '<p>📡 Fetching fresh data from APIs...</p>';
            
            const response = await fetch('/update-rankings');
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            let html = '';
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                html += decoder.decode(value);
                
                // Extract and display status updates
                const statusMatch = html.match(/<p[^>]*>(.*?)<\/p>/g);
                if (statusMatch) {
                    const statusHtml = statusMatch.map(p => p).join('');
                    modalStatus.innerHTML = statusHtml;
                }
            }
            
            // Update completed
            spinner.style.display = 'none';
            modalTitle.textContent = 'Update Complete!';
            modalClose.style.display = 'inline-block';
            
            // Auto-refresh the page after a delay
            setTimeout(() => {
                window.location.reload();
            }, 3000);
            
        } catch (error) {
            spinner.style.display = 'none';
            modalTitle.textContent = 'Update Failed';
            modalStatus.innerHTML = `<p>❌ Error: ${error.message}</p>`;
            modalClose.style.display = 'inline-block';
        }
    }
    
    // Close modal functionality
    const modalClose = document.getElementById('modal-close');
    if (modalClose) {
        modalClose.addEventListener('click', function() {
            document.getElementById('update-modal').style.display = 'none';
        });
    }
    
    // Add pulse animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { background-color: rgba(102, 126, 234, 0.3); }
            50% { background-color: rgba(102, 126, 234, 0.6); }
            100% { background-color: rgba(102, 126, 234, 0.3); }
        }
    `;
    document.head.appendChild(style);
});