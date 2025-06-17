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
    
    // Load anime data for popups
    let animeData = {};
    loadAnimeData();
    
    // Cookie management functions
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
        return null;
    }

    function setCookie(name, value, days) {
        const expires = new Date(Date.now() + days * 864e5).toUTCString();
        document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
    }
    
    // Initialize favorites from cookie
    const favoritesCookie = getCookie('favorites') || '[]';
    let favorites = JSON.parse(favoritesCookie);
    
    // Toggle favorite function
    function toggleFavorite(animeId) {
        const id = animeId.toString();
        if (favorites.includes(id)) {
            favorites = favorites.filter(fav => fav !== id);
        } else {
            favorites.push(id);
        }
        setCookie('favorites', JSON.stringify(favorites), 30);
        updateFavoriteStates();
    }
    
    // Update favorite states across all rows
    function updateFavoriteStates() {
        const rows = tbody.querySelectorAll('tr[data-anime-id]');
        rows.forEach(row => {
            const animeId = row.dataset.animeId;
            const isFavorite = favorites.includes(animeId);
            row.classList.toggle('favorite', isFavorite);
            
            // Clean up rank cell - remove any hearts
            const rankCell = row.querySelector('.rank');
            if (rankCell) {
                // Get the pure rank text (number or medal emoji)
                let rankText = rankCell.textContent.replace(/♥/g, '').trim();
                
                // Remove any existing heart spans
                const existingHeart = rankCell.querySelector('.favorite-heart');
                if (existingHeart) {
                    existingHeart.remove();
                }
                
                // Set the clean rank text
                rankCell.textContent = rankText;
            }
        });
    }
    
    // Apply initial favorite states
    updateFavoriteStates();
    
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
            
            // Clear rank cell and set new rank
            rankCell.textContent = medal || rank;
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
    
    // Load anime data from JSON files
    async function loadAnimeData() {
        try {
            // Load all anime data files
            const [seasonalResponse, otherResponse] = await Promise.all([
                fetch('../data/anime_data.json'),
                fetch('../data/other_anime_sorted.json')
            ]);
            
            const seasonalData = await seasonalResponse.json();
            const otherData = await otherResponse.json();
            
            // Combine all anime data
            // anime_data.json is already an array
            // other_anime_sorted.json has an other_anime property
            const allAnime = [...seasonalData, ...(otherData.other_anime || [])];
            
            allAnime.forEach(anime => {
                animeData[anime.id] = anime;
            });
            
            // Add click handlers to anime rows
            addAnimeClickHandlers();
        } catch (error) {
            console.error('Failed to load anime data:', error);
        }
    }
    
    // Add click handlers to anime containers
    function addAnimeClickHandlers() {
        const animeRows = tbody.querySelectorAll('tr[data-anime-id]');
        
        animeRows.forEach(row => {
            row.style.cursor = 'pointer';
            
            // Extract ranking data from the table row
            const animeId = row.dataset.animeId;
            if (animeData[animeId]) {
                // Extract MAL score and members
                const malData = row.querySelector('.mal-data');
                if (malData) {
                    const malScoreEl = malData.querySelector('strong');
                    const malMembersEl = malData.querySelector('small');
                    if (malScoreEl) {
                        animeData[animeId].mal_score = parseFloat(malScoreEl.textContent);
                    }
                    if (malMembersEl) {
                        const membersText = malMembersEl.textContent.replace(/[^\d,]/g, '');
                        animeData[animeId].mal_members = parseInt(membersText.replace(/,/g, ''));
                    }
                }
                
                // Extract overall score
                const overallScoreEl = row.querySelector('.overall-score strong');
                if (overallScoreEl) {
                    animeData[animeId].overall_score = parseFloat(overallScoreEl.textContent);
                }
                
                // Extract AniList rank from table
                const anilistData = row.querySelector('.anilist-data strong');
                if (anilistData) {
                    const rankText = anilistData.textContent.replace('#', '');
                    animeData[animeId].anilist_rank = parseInt(rankText);
                }
            }
            
            // Find the anime title link and prevent default behavior
            const animeTitleLink = row.querySelector('.anime-title a');
            if (animeTitleLink) {
                animeTitleLink.addEventListener('click', function(e) {
                    e.preventDefault();
                    if (animeData[animeId]) {
                        showAnimeModal(animeData[animeId]);
                    }
                });
            }
            
            // Also handle clicks on the row itself
            row.addEventListener('click', function(e) {
                // Don't open modal if clicking on a link (except the anime title link)
                if (e.target.tagName === 'A' && !e.target.closest('.anime-title')) return;
                
                if (animeData[animeId]) {
                    showAnimeModal(animeData[animeId]);
                }
            });
        });
    }
    
    // Show anime modal
    function showAnimeModal(anime) {
        const modal = document.getElementById('anime-modal');
        const modalPoster = document.getElementById('modal-poster');
        const modalTitle = document.getElementById('modal-title-anime');
        const modalEnglishTitle = document.getElementById('modal-english-title');
        const modalEpisode = document.getElementById('modal-episode');
        const modalRelease = document.getElementById('modal-release');
        const modalLinks = document.getElementById('modal-links');
        const modalScoreInfo = document.getElementById('modal-score-info');
        const modalAnilistLink = document.getElementById('modal-anilist-link');
        const modalFavoriteBtn = document.getElementById('modal-favorite-btn');
        
        // Set basic info
        modalPoster.src = anime.poster_url || '';
        modalPoster.alt = anime.name;
        modalTitle.textContent = anime.name;
        modalEnglishTitle.textContent = anime.english_title || '';
        
        // Set episode info
        if (anime.next_episode_number && anime.next_airing_date) {
            modalEpisode.textContent = `Episode ${anime.next_episode_number}`;
            modalRelease.textContent = `Airs: ${anime.next_airing_date}`;
        } else {
            modalEpisode.textContent = `Episode ${anime.episode}`;
            modalRelease.textContent = `Airs: ${anime.release_date || 'Ongoing'}`;
        }
        
        // Set AniList link
        if (anime.site_url) {
            modalAnilistLink.onclick = function() {
                window.open(anime.site_url, '_blank');
            };
        }
        
        // Set favorite button
        modalFavoriteBtn.dataset.animeId = anime.id;
        const isFavorite = favorites.includes(anime.id.toString());
        modalFavoriteBtn.classList.toggle('active', isFavorite);
        modalFavoriteBtn.querySelector('.favorite-icon').textContent = isFavorite ? '♥' : '♡';
        modalFavoriteBtn.querySelector('.favorite-text').textContent = isFavorite ? 'Favorited' : 'Add to Favorites';
        
        // Set streaming links
        modalLinks.innerHTML = '';
        if (anime.streaming_links && anime.streaming_links.length > 0) {
            anime.streaming_links.forEach(link => {
                const linkEl = document.createElement('a');
                linkEl.href = link.url;
                linkEl.target = '_blank';
                linkEl.className = 'modal-streaming-link';
                
                // Add favicon if available
                if (link.icon) {
                    const icon = document.createElement('img');
                    icon.src = link.icon;
                    icon.alt = link.site;
                    linkEl.appendChild(icon);
                }
                
                const textSpan = document.createElement('span');
                textSpan.textContent = link.site;
                linkEl.appendChild(textSpan);
                
                modalLinks.appendChild(linkEl);
            });
        } else {
            modalLinks.innerHTML = '<p>No streaming links available</p>';
        }
        
        // Set score info
        modalScoreInfo.innerHTML = `
            <div class="score-item">
                <strong>AniList:</strong> ${anime.anilist_rank ? '#' + anime.anilist_rank : (anime.popularity_rank ? '#' + anime.popularity_rank : 'N/A')}
                ${anime.anilist_score ? ' (Score: ' + anime.anilist_score + '/100)' : ''}
            </div>
            <div class="score-item">
                <strong>MAL:</strong> ${anime.mal_score || 'N/A'}/10
                ${anime.mal_members ? ' (' + anime.mal_members.toLocaleString() + ' members)' : ''}
            </div>
            <div class="score-item">
                <strong>Overall Score:</strong> ${anime.overall_score ? anime.overall_score.toFixed(1) : 'N/A'}
            </div>
        `;
        
        // Show modal
        modal.style.display = 'flex';
    }
    
    // Add favorite button click handler
    const modalFavoriteBtn = document.getElementById('modal-favorite-btn');
    if (modalFavoriteBtn) {
        modalFavoriteBtn.addEventListener('click', function() {
            const animeId = this.dataset.animeId;
            if (animeId) {
                toggleFavorite(animeId);
                
                // Update button state
                const isFav = favorites.includes(animeId);
                this.classList.toggle('active', isFav);
                this.querySelector('.favorite-icon').textContent = isFav ? '♥' : '♡';
                this.querySelector('.favorite-text').textContent = isFav ? 'Favorited' : 'Add to Favorites';
            }
        });
    }
    
    // Update countdown
    function updateCountdown(anime) {
        const modalCountdown = document.getElementById('modal-countdown');
        
        let targetDate;
        if (anime.next_airing_date && anime.next_airing_date !== 'Ongoing') {
            targetDate = anime.next_airing_date;
        } else if (anime.release_date && anime.release_date !== 'Ongoing') {
            targetDate = anime.release_date;
        }
        
        if (targetDate) {
            const target = new Date(targetDate);
            const now = new Date();
            const diff = target - now;
            
            if (diff > 0) {
                const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                
                modalCountdown.textContent = `${days}d ${hours}h ${minutes}m`;
            } else {
                modalCountdown.textContent = 'Released';
            }
        } else {
            modalCountdown.textContent = 'N/A';
        }
    }
    
    // Close modal handlers
    const animeModal = document.getElementById('anime-modal');
    const closeBtn = animeModal?.querySelector('.close');
    
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            animeModal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === animeModal) {
            animeModal.style.display = 'none';
        }
    });
});