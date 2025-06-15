document.addEventListener('DOMContentLoaded', () => {
    // Cookie management functions
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
        return null;
    }

    function setCookie(name, value, days) {
        if (value.startsWith('https://anilist.co')) {
            document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`;
            return;
        }
        const expires = new Date(Date.now() + days * 864e5).toUTCString();
        document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
    }

    function sanitizeLink(link) {
        if (!link.startsWith('https://')) {
            return 'https://www.google.com';
        }
        return link;
    }

    // Initialize favorites from cookie
    const favoritesCookie = getCookie('favorites') || '[]';
    let favorites = JSON.parse(favoritesCookie);

    // Tab navigation
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabContents = document.querySelectorAll('.tab-content');

    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');
            
            // Update active states
            navTabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(`${targetTab}-view`).classList.add('active');
            
            // Initialize calendar if switching to calendar view
            if (targetTab === 'calendar') {
                initializeCalendar();
            }
        });
    });

    // List tab navigation
    const listTabs = document.querySelectorAll('.list-tab');
    
    listTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetListTab = tab.getAttribute('data-list-tab');
            
            listTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Show/hide anime cards based on favorites filter
            filterListView(targetListTab === 'favorites');
        });
    });

    // Calendar tab navigation
    const calendarTabs = document.querySelectorAll('.calendar-tab');
    const calendarGrids = document.querySelectorAll('.calendar-grid');

    calendarTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetCalendar = tab.getAttribute('data-calendar-tab');
            
            calendarTabs.forEach(t => t.classList.remove('active'));
            calendarGrids.forEach(g => g.style.display = 'none');
            
            tab.classList.add('active');
            document.getElementById(`calendar-${targetCalendar}`).style.display = 'grid';
            
            // Re-render calendar with appropriate filter
            renderCalendar(targetCalendar === 'favorites');
        });
    });

    // Initialize calendar function
    function initializeCalendar() {
        renderCalendar(false);
    }

    // Render calendar
    function renderCalendar(favoritesOnly = false) {
        const calendarGrid = document.getElementById(favoritesOnly ? 'calendar-favorites' : 'calendar-all');
        calendarGrid.innerHTML = '';
        
        // Clean up any existing tooltips
        document.querySelectorAll('.calendar-tooltip').forEach(tooltip => tooltip.remove());
        
        // Get current date info
        const today = new Date();
        const currentMonth = today.getMonth();
        const currentYear = today.getFullYear();
        const firstDay = new Date(currentYear, currentMonth, 1);
        const lastDay = new Date(currentYear, currentMonth + 1, 0);
        const firstDayOfWeek = firstDay.getDay();
        const daysInMonth = lastDay.getDate();
        
        // Add or update month header
        let monthHeader = calendarGrid.parentElement.querySelector('.calendar-month-header');
        if (!monthHeader) {
            monthHeader = document.createElement('div');
            monthHeader.className = 'calendar-month-header';
            calendarGrid.parentElement.insertBefore(monthHeader, calendarGrid);
        }
        monthHeader.innerHTML = `
            <button class="month-nav-btn" onclick="changeMonth(-1)">‹</button>
            <h3>${firstDay.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</h3>
            <button class="month-nav-btn" onclick="changeMonth(1)">›</button>
        `;
        
        // Add day headers
        const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        dayHeaders.forEach(day => {
            const dayHeader = document.createElement('div');
            dayHeader.className = 'calendar-weekday-header';
            dayHeader.textContent = day;
            calendarGrid.appendChild(dayHeader);
        });
        
        // Group anime by date
        const animeByDate = {};
        window.animeData.forEach(anime => {
            if (favoritesOnly && !favorites.includes(anime.id.toString())) {
                return;
            }
            
            const releaseDate = anime.release_date;
            if (!animeByDate[releaseDate]) {
                animeByDate[releaseDate] = [];
            }
            animeByDate[releaseDate].push(anime);
        });
        
        // Add empty cells for days before month starts
        for (let i = 0; i < firstDayOfWeek; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.className = 'calendar-day empty';
            calendarGrid.appendChild(emptyDay);
        }
        
        // Add days of the month
        for (let day = 1; day <= daysInMonth; day++) {
            const dayDiv = document.createElement('div');
            dayDiv.className = 'calendar-day';
            
            const currentDate = new Date(currentYear, currentMonth, day);
            const dateStr = currentDate.toISOString().split('T')[0];
            const isToday = day === today.getDate() && currentMonth === today.getMonth() && currentYear === today.getFullYear();
            
            if (isToday) {
                dayDiv.classList.add('today');
            }
            
            // Add day number
            const dayNumber = document.createElement('div');
            dayNumber.className = 'calendar-day-number';
            dayNumber.textContent = day;
            dayDiv.appendChild(dayNumber);
            
            // Add anime for this day
            const dayAnime = animeByDate[dateStr] || [];
            const animeContainer = document.createElement('div');
            animeContainer.className = 'calendar-day-anime';
            
            dayAnime.forEach(anime => {
                const animeDiv = document.createElement('div');
                animeDiv.className = 'calendar-anime-item';
                animeDiv.setAttribute('data-anime-id', anime.id);
                
                // Add favorite class if anime is favorited
                if (favorites.includes(anime.id.toString())) {
                    animeDiv.classList.add('favorite');
                }
                
                // Truncate name if too long (max ~35 characters like "Aharen-san wa Hakarenai Season 2")
                const maxLength = 35;
                const displayName = anime.name.length > maxLength 
                    ? anime.name.substring(0, maxLength - 3) + '...' 
                    : anime.name;
                
                animeDiv.innerHTML = `
                    <img class="calendar-anime-thumb" src="${anime.poster_url}" alt="${anime.name}">
                    <span class="calendar-anime-name" title="${anime.name}">${displayName}</span>
                `;
                
                // Create tooltip
                const tooltip = document.createElement('div');
                tooltip.className = 'calendar-tooltip';
                
                // Get the main link (custom or default)
                const customLink = window.customLinks[anime.name] || anime.site_url;
                const linkDomain = new URL(customLink).hostname;
                
                tooltip.innerHTML = `
                    <div class="tooltip-poster-section">
                        <img class="tooltip-poster" src="${anime.poster_url}" alt="${anime.name}">
                        <button class="tooltip-main-link" onclick="window.open('${customLink}', '_blank')">
                            ${linkDomain}
                        </button>
                    </div>
                    <div class="tooltip-info">
                        <h4>${anime.name}</h4>
                        ${anime.english_title ? `<p class="tooltip-english">${anime.english_title}</p>` : ''}
                        <p class="tooltip-episode">Episode ${anime.episode}</p>
                        <div class="tooltip-streaming">
                            ${anime.streaming_links.map(link => `
                                <a href="${link.url}" target="_blank" class="tooltip-streaming-link">
                                    <img src="${link.icon}" alt="${link.site}">
                                    <span>${link.site}</span>
                                </a>
                            `).join('')}
                        </div>
                    </div>
                `;
                document.body.appendChild(tooltip);
                
                // Hover events for tooltip
                animeDiv.addEventListener('mouseenter', (e) => {
                    const rect = animeDiv.getBoundingClientRect();
                    tooltip.style.display = 'flex';
                    tooltip.style.left = `${rect.left}px`;
                    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
                    
                    // Adjust if tooltip goes off screen
                    if (tooltip.offsetLeft < 10) {
                        tooltip.style.left = '10px';
                    }
                    if (tooltip.offsetLeft + tooltip.offsetWidth > window.innerWidth - 10) {
                        tooltip.style.left = `${window.innerWidth - tooltip.offsetWidth - 10}px`;
                    }
                    if (tooltip.offsetTop < 10) {
                        tooltip.style.top = `${rect.bottom + 10}px`;
                    }
                });
                
                animeDiv.addEventListener('mouseleave', () => {
                    tooltip.style.display = 'none';
                });
                
                animeDiv.addEventListener('click', (e) => {
                    e.stopPropagation();
                    tooltip.style.display = 'none';
                    showAnimeModal(anime);
                });
                
                animeContainer.appendChild(animeDiv);
            });
            
            dayDiv.appendChild(animeContainer);
            calendarGrid.appendChild(dayDiv);
        }
        
        // Store current month for navigation
        window.currentCalendarMonth = currentMonth;
        window.currentCalendarYear = currentYear;
    }
    
    // Change month function
    window.changeMonth = function(direction) {
        window.currentCalendarMonth += direction;
        if (window.currentCalendarMonth > 11) {
            window.currentCalendarMonth = 0;
            window.currentCalendarYear++;
        } else if (window.currentCalendarMonth < 0) {
            window.currentCalendarMonth = 11;
            window.currentCalendarYear--;
        }
        
        // Re-render with new month
        const isFavoritesView = document.querySelector('.calendar-tab.active').getAttribute('data-calendar-tab') === 'favorites';
        renderCalendar(isFavoritesView);
    }
    
    // Show all anime for a specific day
    function showDayAnimeList(date, animeList) {
        const modal = document.getElementById('anime-modal');
        const modalBody = document.querySelector('.modal-body');
        
        modalBody.innerHTML = `
            <h2>Anime on ${new Date(date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</h2>
            <div class="day-anime-list">
                ${animeList.map(anime => `
                    <div class="day-anime-item" onclick="showAnimeModal(${JSON.stringify(anime).replace(/"/g, '&quot;')})">
                        <img src="${anime.poster_url}" alt="${anime.name}">
                        <div class="day-anime-info">
                            <h3>${anime.name}</h3>
                            <p>Episode ${anime.episode}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        modal.classList.add('active');
    }

    // Modal functionality
    const modal = document.getElementById('anime-modal');
    const modalClose = document.querySelector('.modal-close');
    const modalBody = document.querySelector('.modal-body');

    function showAnimeModal(anime) {
        const customLink = window.customLinks[anime.name] || anime.site_url;
        const isFavorite = favorites.includes(anime.id.toString());
        
        const linkDomain = new URL(customLink).hostname;
        
        modalBody.innerHTML = `
            <div class="modal-anime-content">
                <div class="modal-poster-section">
                    <img class="modal-poster" src="${anime.poster_url}" alt="${anime.name}">
                    <button class="modal-favorite-btn ${isFavorite ? 'active' : ''}" data-anime-id="${anime.id}">
                        <span class="favorite-icon">${isFavorite ? '♥' : '♡'}</span>
                        <span class="favorite-text">${isFavorite ? 'Favorited' : 'Add to Favorites'}</span>
                    </button>
                </div>
                <div class="modal-info-section">
                    ${anime.english_title ? `<div class="modal-english-title">${anime.english_title}</div>` : ''}
                    <h2 class="modal-title">${anime.name}</h2>
                    <div class="modal-episode-info">
                        <span class="episode-badge">Episode ${anime.episode}</span>
                        <span class="release-date">Airs: ${anime.release_date}</span>
                    </div>
                    <div class="modal-streaming-section">
                        <div class="streaming-header">
                            <h3>Streaming Links</h3>
                            <button class="modal-main-link" onclick="window.open('${customLink}', '_blank')">
                                ${linkDomain}
                            </button>
                        </div>
                        <div class="modal-streaming-links">
                            ${anime.streaming_links.map(link => `
                                <a href="${link.url}" target="_blank" class="modal-streaming-link">
                                    <img src="${link.icon}" alt="${link.site}">
                                    <span>${link.site}</span>
                                </a>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add favorite functionality to modal button
        const modalFavoriteBtn = modalBody.querySelector('.modal-favorite-btn');
        modalFavoriteBtn.addEventListener('click', () => {
            const animeId = modalFavoriteBtn.getAttribute('data-anime-id');
            toggleFavorite(animeId);
            
            // Update modal button state
            const isFav = favorites.includes(animeId);
            modalFavoriteBtn.classList.toggle('active', isFav);
            modalFavoriteBtn.querySelector('.favorite-icon').textContent = isFav ? '♥' : '♡';
            modalFavoriteBtn.querySelector('.favorite-text').textContent = isFav ? 'Favorited' : 'Add to Favorites';
        });
        
        modal.classList.add('active');
    }

    modalClose.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });

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

    // Update favorite states across all cards
    function updateFavoriteStates() {
        document.querySelectorAll('.anime-card').forEach(card => {
            const animeId = card.getAttribute('data-anime-id');
            const isFavorite = favorites.includes(animeId);
            const favoriteIcon = card.querySelector('.favorite-icon');
            
            card.classList.toggle('favorite', isFavorite);
            if (favoriteIcon) {
                favoriteIcon.textContent = isFavorite ? '♥' : '♡';
            }
        });
        
        // Re-apply current list filter if favorites view is active
        const activeListTab = document.querySelector('.list-tab.active');
        if (activeListTab && activeListTab.getAttribute('data-list-tab') === 'favorites') {
            filterListView(true);
        }
    }

    // Filter list view based on favorites
    function filterListView(favoritesOnly = false) {
        const animeCards = document.querySelectorAll('#list-view .anime-card');
        const timeSections = document.querySelectorAll('#list-view .time-section');
        
        animeCards.forEach(card => {
            const animeId = card.getAttribute('data-anime-id');
            const isFavorite = favorites.includes(animeId);
            
            if (favoritesOnly) {
                card.style.display = isFavorite ? 'flex' : 'none';
            } else {
                card.style.display = 'flex';
            }
        });
        
        // Hide/show time sections if they have no visible cards
        timeSections.forEach(section => {
            const visibleCards = section.querySelectorAll('.anime-card[style="display: flex"], .anime-card:not([style*="display: none"])');
            const hasVisibleCards = Array.from(visibleCards).some(card => {
                const computedStyle = window.getComputedStyle(card);
                return computedStyle.display !== 'none';
            });
            
            if (favoritesOnly) {
                section.style.display = hasVisibleCards ? 'block' : 'none';
            } else {
                section.style.display = 'block';
            }
        });
    }

    // Initialize anime cards
    const animeCards = document.querySelectorAll('.anime-card');
    let currentCard = null;

    animeCards.forEach(card => {
        const animeName = card.getAttribute('data-name');
        const encodedName = encodeURIComponent(animeName);
        const animeId = card.getAttribute('data-anime-id');
        const siteUrl = card.getAttribute('data-site-url');
        const cookieLink = getCookie(`link_${encodedName}`);

        // Set custom link if exists
        if (cookieLink) {
            card.setAttribute('data-link', sanitizeLink(cookieLink));
        }

        const currentLink = card.getAttribute('data-link');
        const linkChanged = cookieLink && cookieLink !== siteUrl;

        // Update custom link indicator
        const customLinkBadge = card.querySelector('.custom-link-badge');
        if (linkChanged) {
            customLinkBadge.style.display = 'block';
            updateFavicon(customLinkBadge, currentLink);
        }

        // Update favorite state
        const favoriteBtn = card.querySelector('.favorite-btn');
        const favoriteIcon = card.querySelector('.favorite-icon');
        if (favorites.includes(animeId)) {
            card.classList.add('favorite');
            favoriteIcon.textContent = '♥';
        }

        // Card click handler
        card.addEventListener('click', (e) => {
            // Prevent click if clicking on button or streaming links
            if (e.target.closest('.favorite-btn') || 
                e.target.closest('.streaming-links') || 
                e.target.closest('.context-menu')) {
                return;
            }
            
            const link = card.getAttribute('data-link');
            if (link) window.open(link, '_blank');
        });

        // Context menu
        card.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            currentCard = card;
            showContextMenu(e.pageX, e.pageY);
        });

        // Favorite button click
        favoriteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleFavorite(animeId);
        });
    });

    // Update favicon function
    function updateFavicon(badge, link) {
        const customFaviconSpan = badge.querySelector('.custom-favicon');
        if (!customFaviconSpan) return;

        customFaviconSpan.innerHTML = '';
        
        if (link.startsWith('https://anilist.co')) {
            badge.style.display = 'none';
            return;
        }

        try {
            const urlObj = new URL(link);
            const faviconUrl = `https://www.google.com/s2/favicons?sz=32&domain_url=${urlObj.origin}`;
            const faviconImg = document.createElement('img');
            faviconImg.src = faviconUrl;
            faviconImg.alt = 'Custom Link';
            customFaviconSpan.appendChild(faviconImg);
        } catch (e) {
            console.error('Invalid URL for favicon:', e);
        }
    }

    // Context menu
    const contextMenu = document.getElementById('context-menu');
    const editLinkItem = document.getElementById('edit-link');

    function showContextMenu(x, y) {
        contextMenu.style.display = 'block';
        
        // Use viewport coordinates instead of page coordinates
        const viewportX = x - window.pageXOffset;
        const viewportY = y - window.pageYOffset;
        
        contextMenu.style.left = `${viewportX}px`;
        contextMenu.style.top = `${viewportY}px`;
        
        // Adjust if menu goes off screen
        const rect = contextMenu.getBoundingClientRect();
        if (rect.right > window.innerWidth) {
            contextMenu.style.left = `${viewportX - rect.width}px`;
        }
        if (rect.bottom > window.innerHeight) {
            contextMenu.style.top = `${viewportY - rect.height}px`;
        }
    }

    function hideContextMenu() {
        contextMenu.style.display = 'none';
        currentCard = null;
    }

    document.addEventListener('click', (e) => {
        if (!contextMenu.contains(e.target)) {
            hideContextMenu();
        }
    });

    document.addEventListener('scroll', hideContextMenu);
    document.addEventListener('resize', hideContextMenu);

    editLinkItem.addEventListener('click', () => {
        if (currentCard) {
            const animeName = currentCard.getAttribute('data-name');
            const encodedName = encodeURIComponent(animeName);
            const currentLink = currentCard.getAttribute('data-link');
            const siteUrl = currentCard.getAttribute('data-site-url');
            let newLink = prompt(`Edit streaming link for ${animeName}:`, currentLink);

            if (newLink && newLink.trim()) {
                let trimmedLink = sanitizeLink(newLink.trim());

                currentCard.setAttribute('data-link', trimmedLink);
                setCookie(`link_${encodedName}`, trimmedLink, 30);

                // For GitHub Pages, we only store links locally in cookies/localStorage
                // since we can't persist server-side changes
                const badge = currentCard.querySelector('.custom-link-badge');
                if (trimmedLink !== siteUrl) {
                    badge.style.display = 'block';
                    updateFavicon(badge, trimmedLink);
                } else {
                    badge.style.display = 'none';
                }
            }
            hideContextMenu();
        }
    });

    // Add modal styles
    const modalStyles = document.createElement('style');
    modalStyles.textContent = `
        .modal-anime-content {
            display: flex;
            gap: 2rem;
        }
        
        .modal-poster-section {
            flex-shrink: 0;
        }
        
        .modal-poster {
            width: 250px;
            height: 375px;
            object-fit: cover;
            border-radius: 12px;
            margin-bottom: 1rem;
        }
        
        .modal-favorite-btn {
            width: 100%;
            padding: 0.75rem;
            background: var(--bg-card);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 1rem;
            cursor: pointer;
            transition: all var(--transition-normal);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        
        .modal-favorite-btn:hover {
            background: var(--bg-card-hover);
            border-color: var(--accent-gold);
        }
        
        .modal-favorite-btn.active {
            background: var(--accent-gold);
            color: var(--bg-primary);
            border-color: var(--accent-gold);
        }
        
        .modal-info-section {
            flex: 1;
        }
        
        .modal-english-title {
            font-size: 1rem;
            color: var(--text-secondary);
            font-style: italic;
            margin-bottom: 0.5rem;
        }
        
        .modal-title {
            font-size: 2rem;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }
        
        .modal-episode-info {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .streaming-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .modal-streaming-section h3 {
            margin: 0;
            color: var(--text-primary);
        }
        
        .modal-streaming-links {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .modal-streaming-link {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            text-decoration: none;
            color: var(--text-primary);
            transition: all var(--transition-normal);
        }
        
        .modal-streaming-link:hover {
            background: var(--bg-card-hover);
            border-color: var(--accent-primary);
            transform: translateY(-2px);
        }
        
        .modal-streaming-link img {
            width: 24px;
            height: 24px;
            object-fit: cover;
            border-radius: 4px;
        }
        
        .modal-main-link {
            display: inline-block;
            padding: 0.4rem 0.8rem;
            background: var(--accent-primary);
            border: none;
            border-radius: 6px;
            color: white;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            transition: all var(--transition-normal);
            margin: 0;
        }
        
        .modal-main-link:hover {
            background: var(--accent-secondary);
            transform: translateY(-1px);
        }
        
        @media (max-width: 768px) {
            .modal-anime-content {
                flex-direction: column;
            }
            
            .modal-poster {
                width: 100%;
                max-width: 200px;
                height: auto;
                margin: 0 auto 1rem;
            }
        }
    `;
    document.head.appendChild(modalStyles);
});