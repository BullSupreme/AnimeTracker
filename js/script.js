document.addEventListener('DOMContentLoaded', () => {
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

    function deleteCookie(name) {
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`;
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
    
    // Check URL hash to switch to specific tab
    const hash = window.location.hash.substring(1); // Remove the # symbol
    if (hash === 'calendar') {
        // Find and click the calendar tab
        const calendarTab = document.querySelector('.nav-tab[data-tab="calendar"]');
        if (calendarTab) {
            // Use setTimeout to ensure DOM is ready
            setTimeout(() => {
                calendarTab.click();
                // Clear the hash to prevent issues
                history.replaceState(null, null, window.location.pathname);
            }, 100);
        }
    }
    
    // Check sessionStorage for calendar request from rankings
    if (sessionStorage.getItem('openCalendar') === 'true') {
        sessionStorage.removeItem('openCalendar');
        const calendarTab = document.querySelector('.nav-tab[data-tab="calendar"]');
        if (calendarTab) {
            setTimeout(() => {
                calendarTab.click();
            }, 50);
        }
    }

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

    // Layout switching functionality
    const layoutSelector = document.getElementById('layout-selector');
    const listView = document.getElementById('list-view');
    
    // Load saved layout preference
    const savedLayout = getCookie('layout') || 'grid';
    if (layoutSelector) {
        layoutSelector.value = savedLayout;
        applyLayout(savedLayout);
    }
    
    // Handle layout changes
    if (layoutSelector) {
        layoutSelector.addEventListener('change', (e) => {
            const selectedLayout = e.target.value;
            applyLayout(selectedLayout);
            setCookie('layout', selectedLayout, 365); // Save for 1 year
        });
    }
    
    function applyLayout(layout) {
        // Remove all layout classes
        listView.classList.remove('layout-grid', 'layout-compact', 'layout-table', 'layout-poster');
        
        // Add the selected layout class
        listView.classList.add(`layout-${layout}`);
        
        // Special handling for different layouts
        if (layout === 'table') {
            addTableHeaders();
            restructureForTable();
        } else {
            removeTableHeaders();
            restoreOriginalStructure();
            if (layout === 'compact') {
                restructureForCompact();
            }
        }
    }
    
    function addTableHeaders() {
        // Add table headers for table layout
        const sections = document.querySelectorAll('.time-section');
        sections.forEach(section => {
            const grid = section.querySelector('.anime-grid');
            if (grid && !grid.querySelector('.table-header')) {
                const headerRow = document.createElement('div');
                headerRow.className = 'table-header anime-card';
                headerRow.style.fontWeight = 'bold';
                headerRow.style.background = 'var(--bg-secondary)';
                headerRow.innerHTML = `
                    <div class="table-cell-poster">Poster</div>
                    <div class="table-cell-title">Title</div>
                    <div class="table-cell-episode">Episode</div>
                    <div class="table-cell-streaming">Streaming</div>
                `;
                grid.insertBefore(headerRow, grid.firstChild);
            }
        });
    }
    
    function removeTableHeaders() {
        // Remove table headers
        document.querySelectorAll('.table-header').forEach(header => {
            header.remove();
        });
    }
    
    function restructureForTable() {
        // Restructure anime cards for table layout
        const animeCards = document.querySelectorAll('.anime-card:not(.table-header)');
        animeCards.forEach(card => {
            // Skip if already restructured
            if (card.querySelector('.table-cell-poster')) return;
            
            // Get original elements
            const imageWrapper = card.querySelector('.card-image-wrapper');
            const poster = imageWrapper?.querySelector('.anime-poster');
            const cardInfo = card.querySelector('.card-info');
            const title = cardInfo?.querySelector('.anime-title');
            const episodeInfo = cardInfo?.querySelector('.episode-info');
            const streamingLinks = cardInfo?.querySelector('.streaming-links');
            
            // Store original structure
            card.setAttribute('data-original-structure', card.innerHTML);
            
            // Create table cell structure
            card.innerHTML = `
                <div class="table-cell-poster">
                    ${poster ? `<img src="${poster.src}" alt="${poster.alt}">` : ''}
                </div>
                <div class="table-cell-title">
                    ${title ? title.textContent : 'Unknown Title'}
                </div>
                <div class="table-cell-episode">
                    ${episodeInfo ? episodeInfo.textContent : 'N/A'}
                </div>
                <div class="table-cell-streaming">
                    ${streamingLinks ? streamingLinks.innerHTML : ''}
                </div>
            `;
        });
    }
    
    function restoreOriginalStructure() {
        // Restore original structure for non-table layouts
        const animeCards = document.querySelectorAll('.anime-card:not(.table-header)');
        animeCards.forEach(card => {
            const originalStructure = card.getAttribute('data-original-structure');
            if (originalStructure) {
                card.innerHTML = originalStructure;
                card.removeAttribute('data-original-structure');
            }
        });
    }
    
    function restructureForCompact() {
        // Restructure card-info for compact layout
        const animeCards = document.querySelectorAll('.anime-card');
        animeCards.forEach(card => {
            const cardInfo = card.querySelector('.card-info');
            if (!cardInfo || cardInfo.querySelector('.anime-info-text')) return;
            
            // Get all the elements we need to reorganize
            const englishTitle = cardInfo.querySelector('.anime-english-title');
            const title = cardInfo.querySelector('.anime-title');
            const episodeInfo = cardInfo.querySelector('.episode-info');
            const streamingLinks = cardInfo.querySelector('.streaming-links');
            
            // Create wrapper for text info
            const infoTextWrapper = document.createElement('div');
            infoTextWrapper.className = 'anime-info-text';
            
            // Move title and episode info into the wrapper
            if (englishTitle) infoTextWrapper.appendChild(englishTitle);
            if (title) infoTextWrapper.appendChild(title);
            if (episodeInfo) infoTextWrapper.appendChild(episodeInfo);
            
            // Clear card-info and rebuild structure
            cardInfo.innerHTML = '';
            cardInfo.appendChild(infoTextWrapper);
            if (streamingLinks) cardInfo.appendChild(streamingLinks);
        });
    }

    // Change month function
    function changeMonth(direction) {
        window.currentCalendarMonth = (window.currentCalendarMonth !== undefined ? window.currentCalendarMonth : new Date().getMonth()) + direction;
        window.currentCalendarYear = window.currentCalendarYear !== undefined ? window.currentCalendarYear : new Date().getFullYear();
        
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
        
        // Use global calendar month/year if set, otherwise use current date
        const currentMonth = window.currentCalendarMonth !== undefined ? window.currentCalendarMonth : today.getMonth();
        const currentYear = window.currentCalendarYear !== undefined ? window.currentCalendarYear : today.getFullYear();
        
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
            <button class="month-nav-btn" id="prev-month-btn">‹</button>
            <h3>${firstDay.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</h3>
            <button class="month-nav-btn" id="next-month-btn">›</button>
        `;
        
        // Add event listeners for month navigation
        const prevBtn = monthHeader.querySelector('#prev-month-btn');
        const nextBtn = monthHeader.querySelector('#next-month-btn');
        
        prevBtn.addEventListener('click', () => changeMonth(-1));
        nextBtn.addEventListener('click', () => changeMonth(1));
        
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
        
        // Combine current and upcoming anime for calendar view
        const allAnime = [];
        if (window.animeData && Array.isArray(window.animeData)) {
            allAnime.push(...window.animeData);
        }
        if (window.upcomingAnime && Array.isArray(window.upcomingAnime)) {
            allAnime.push(...window.upcomingAnime);
        }
        
        allAnime.forEach(anime => {
            if (favoritesOnly && !favorites.includes(anime.id.toString())) {
                return;
            }
            
            // Add anime to both release_date and next_airing_date if they're different
            const dates = [];
            if (anime.release_date && anime.release_date !== 'TBD') {
                dates.push(anime.release_date);
            }
            if (anime.next_airing_date && anime.next_airing_date !== anime.release_date) {
                dates.push(anime.next_airing_date);
            }
            
            dates.forEach(date => {
                if (!animeByDate[date]) {
                    animeByDate[date] = [];
                }
                animeByDate[date].push(anime);
            });
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
            // Format date as YYYY-MM-DD in local timezone (not UTC)
            const year = currentDate.getFullYear();
            const month = String(currentDate.getMonth() + 1).padStart(2, '0');
            const dayStr = String(currentDate.getDate()).padStart(2, '0');
            const dateStr = `${year}-${month}-${dayStr}`;
            const dayOfWeek = currentDate.getDay(); // 0 = Sunday, 6 = Saturday
            const isToday = day === today.getDate() && currentMonth === today.getMonth() && currentYear === today.getFullYear();
            const isWeekend = dayOfWeek === 0 || dayOfWeek === 6; // Sunday or Saturday
            
            if (isToday) {
                dayDiv.classList.add('today');
            }
            
            if (isWeekend) {
                dayDiv.classList.add('weekend');
            }
            
            // Add day number (clickable)
            const dayNumber = document.createElement('div');
            dayNumber.className = 'calendar-day-number';
            dayNumber.textContent = day;
            
            // Make day number clickable if there are anime for this day
            const dayAnime = animeByDate[dateStr] || [];
            if (dayAnime.length > 0) {
                dayNumber.classList.add('clickable');
                dayDiv.classList.add('has-anime');
                
                // Make entire day clickable
                dayDiv.addEventListener('click', (e) => {
                    // Only trigger if clicking on the day itself, not on anime items
                    if (!e.target.closest('.calendar-anime-item')) {
                        showExpandedDayView(dateStr, dayAnime);
                    }
                });
            }
            
            dayDiv.appendChild(dayNumber);
            
            // Add anime for this day
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
    
    // Show expanded day view
    function showExpandedDayView(date, animeList) {
        const modal = document.getElementById('anime-modal');
        const modalBody = document.querySelector('.modal-body');
        
        // Parse the date components to avoid timezone issues
        const [yearStr, monthStr, dayStr] = date.split('-');
        const dateObj = new Date(parseInt(yearStr), parseInt(monthStr) - 1, parseInt(dayStr));
        const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' });
        const dayNumber = parseInt(dayStr);
        const monthName = dateObj.toLocaleDateString('en-US', { month: 'long' });
        const year = parseInt(yearStr);
        
        modalBody.innerHTML = `
            <div class="expanded-day-view">
                <div class="expanded-day-header">
                    <div class="expanded-day-number">${dayNumber}</div>
                    <div class="expanded-day-info">
                        <h2>${dayName}</h2>
                        <p>${monthName} ${year}</p>
                        <p class="anime-count">${animeList.length} anime airing</p>
                    </div>
                </div>
                <div class="expanded-day-anime-grid">
                    ${animeList.map(anime => {
                        const customLink = window.customLinks[anime.name] || anime.site_url;
                        const isFavorite = favorites.includes(anime.id.toString());
                        
                        return `
                            <div class="expanded-anime-card ${isFavorite ? 'favorite' : ''}" data-anime-id="${anime.id}" onclick="showAnimeModal(${JSON.stringify(anime).replace(/"/g, '&quot;')})">
                                <div class="expanded-anime-poster">
                                    <img src="${anime.poster_url}" alt="${anime.name}">
                                    <div class="expanded-anime-overlay">
                                        <button class="expanded-favorite-btn" onclick="event.stopPropagation(); toggleFavorite('${anime.id}')">
                                            ${isFavorite ? '♥' : '♡'}
                                        </button>
                                    </div>
                                </div>
                                <div class="expanded-anime-info">
                                    <h3 class="expanded-anime-title" title="${anime.name}">${anime.name}</h3>
                                    ${anime.english_title ? `<p class="expanded-anime-english">${anime.english_title}</p>` : ''}
                                    <div class="expanded-anime-details">
                                        <span class="expanded-episode-badge">Episode ${anime.episode}</span>
                                        <a href="${customLink}" target="_blank" class="main-link-btn" onclick="event.stopPropagation()">
                                            ${new URL(customLink).hostname}
                                        </a>
                                        ${anime.next_airing_date && anime.next_airing_date !== anime.release_date ? 
                                            `<span class="expanded-next-episode">Next: ${anime.next_episode_number || anime.episode + 1}</span>` : ''}
                                    </div>
                                    <div class="expanded-streaming-links">
                                        ${anime.streaming_links.slice(0, 3).map(link => `
                                            <a href="${link.url}" target="_blank" class="expanded-streaming-link" title="${link.site}" onclick="event.stopPropagation()">
                                                <img src="${link.icon}" alt="${link.site}">
                                            </a>
                                        `).join('')}
                                        ${anime.streaming_links.length > 3 ? `<span class="more-links">+${anime.streaming_links.length - 3}</span>` : ''}
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
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
    let currentAnimeData = null;

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
                e.target.closest('.streaming-links-overlay') ||
                e.target.closest('.main-link-btn') ||
                e.target.closest('.nine-anime-btn') ||
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
            // Find the full anime data object when the menu is opened
            currentAnimeData = window.animeData.find(a => a.id.toString() === card.dataset.animeId);
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
    const copyMainTitleItem = document.getElementById('copy-main-title');
    const copyEnglishTitleItem = document.getElementById('copy-english-title');

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

                // If user sets link back to anilist.co (default), remove the custom link cookie
                if (trimmedLink.startsWith('https://anilist.co')) {
                    deleteCookie(`link_${encodedName}`);
                } else {
                    setCookie(`link_${encodedName}`, trimmedLink, 30);
                }

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
        
        /* Expanded Day View Styles */
        .expanded-day-view {
            width: 100%;
            max-width: 1200px;
        }
        
        .expanded-day-header {
            display: flex;
            align-items: center;
            gap: 2rem;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border-color);
        }
        
        .expanded-day-number {
            font-size: 4rem;
            font-weight: bold;
            color: var(--accent-primary);
            background: var(--bg-card);
            border: 2px solid var(--accent-primary);
            border-radius: 12px;
            width: 100px;
            height: 100px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        
        .expanded-day-info h2 {
            margin: 0 0 0.5rem 0;
            font-size: 2.5rem;
            color: var(--text-primary);
        }
        
        .expanded-day-info p {
            margin: 0;
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
        
        .anime-count {
            color: var(--accent-gold) !important;
            font-weight: 500;
        }
        
        .expanded-day-anime-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
        }
        
        .expanded-anime-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            transition: all var(--transition-normal);
        }
        
        .expanded-anime-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
            border-color: var(--accent-primary);
        }
        
        .expanded-anime-card.favorite {
            border-color: var(--accent-gold);
        }
        
        .expanded-anime-poster {
            position: relative;
            height: 180px;
            overflow: hidden;
        }
        
        .expanded-anime-poster img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .expanded-anime-overlay {
            position: absolute;
            top: 0;
            right: 0;
            padding: 0.5rem;
            background: linear-gradient(135deg, transparent 30%, rgba(0,0,0,0.8));
            opacity: 0;
            transition: opacity var(--transition-normal);
        }
        
        .expanded-anime-card:hover .expanded-anime-overlay {
            opacity: 1;
        }
        
        .expanded-favorite-btn {
            background: none;
            border: none;
            color: var(--accent-gold);
            font-size: 1.5rem;
            cursor: pointer;
            transition: transform var(--transition-normal);
        }
        
        .expanded-favorite-btn:hover {
            transform: scale(1.2);
        }
        
        .expanded-anime-info {
            padding: 1rem;
        }
        
        .expanded-anime-title {
            margin: 0 0 0.5rem 0;
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
            line-height: 1.3;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .expanded-anime-english {
            margin: 0 0 0.75rem 0;
            font-size: 0.9rem;
            color: var(--text-secondary);
            font-style: italic;
            display: -webkit-box;
            -webkit-line-clamp: 1;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .expanded-anime-details {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
        }
        
        .expanded-episode-badge {
            background: var(--accent-primary);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .expanded-next-episode {
            background: var(--accent-secondary);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .expanded-streaming-links {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .expanded-streaming-link {
            width: 28px;
            height: 28px;
            border-radius: 4px;
            overflow: hidden;
            transition: transform var(--transition-normal);
        }
        
        .expanded-streaming-link:hover {
            transform: scale(1.1);
        }
        
        .expanded-streaming-link img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .more-links {
            background: var(--bg-secondary);
            color: var(--text-secondary);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
        }
        
        .expanded-view-details {
            width: 100%;
            padding: 0.5rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-primary);
            cursor: pointer;
            transition: all var(--transition-normal);
        }
        
        .expanded-view-details:hover {
            background: var(--accent-primary);
            color: white;
            border-color: var(--accent-primary);
        }
        
        .calendar-day-number.clickable {
            cursor: pointer;
            transition: all var(--transition-normal);
        }
        
        .calendar-day-number.clickable:hover {
            background: var(--accent-primary);
            color: white;
            border-radius: 4px;
            transform: scale(1.1);
        }
        
        @media (max-width: 768px) {
            .expanded-day-header {
                flex-direction: column;
                text-align: center;
                gap: 1rem;
            }
            
            .expanded-day-number {
                width: 80px;
                height: 80px;
                font-size: 3rem;
            }
            
            .expanded-day-info h2 {
                font-size: 2rem;
            }
            
            .expanded-day-anime-grid {
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 1rem;
            }
        }
    `;
    document.head.appendChild(modalStyles);

    // Rank badge tooltip functionality
    function initRankTooltips() {
        // Create tooltip element
        const tooltip = document.createElement('div');
        tooltip.className = 'rank-tooltip';
        document.body.appendChild(tooltip);

        // Add event listeners to all rank badges
        document.addEventListener('mouseover', (e) => {
            if (e.target.classList.contains('popularity-rank-badge')) {
                const tooltipText = e.target.getAttribute('data-tooltip');
                if (tooltipText) {
                    tooltip.textContent = tooltipText;
                    
                    // Position tooltip above the badge
                    const rect = e.target.getBoundingClientRect();
                    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
                    tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
                    
                    // Show tooltip
                    tooltip.classList.add('show');
                }
            }
        });

        document.addEventListener('mouseout', (e) => {
            if (e.target.classList.contains('popularity-rank-badge')) {
                tooltip.classList.remove('show');
            }
        });
    }

    // Initialize rank tooltips
    initRankTooltips();
    // Show More functionality for upcoming anime
function initShowMoreButtons() {
    const showMoreBtn = document.getElementById('show-more-upcoming');
    
    if (showMoreBtn) {
        // Get all upcoming anime cards in the grid
        const upcomingGrid = document.querySelector('.upcoming-grid');
        if (!upcomingGrid) return;
        
        const allUpcomingCards = upcomingGrid.querySelectorAll('.anime-card');
        // Cards after the first 20 are the ones to show/hide
        const extraCards = Array.from(allUpcomingCards).slice(20);
        
        showMoreBtn.addEventListener('click', () => {
            const showMoreText = showMoreBtn.querySelector('.show-more-text');
            const showLessText = showMoreBtn.querySelector('.show-less-text');
            const isExpanded = showMoreBtn.classList.contains('expanded');
            
            if (isExpanded) {
                // Hide extra anime
                extraCards.forEach(anime => {
                    anime.classList.add('hidden-upcoming');
                });
                showMoreText.style.display = 'inline';
                showLessText.style.display = 'none';
                showMoreBtn.classList.remove('expanded');
            } else {
                // Show extra anime
                extraCards.forEach(anime => {
                    anime.classList.remove('hidden-upcoming');
                });
                showMoreText.style.display = 'none';
                showLessText.style.display = 'inline';
                showMoreBtn.classList.add('expanded');
            }
            
            // Re-initialize calendar to include newly shown anime
            if (document.getElementById('calendar-view').classList.contains('active')) {
                initializeCalendar();
            }
        });
    }
}

// Initialize show more buttons
initShowMoreButtons();
    
// Initialize show more buttons
    initShowMoreButtons();

    // --- New Code for Copying Titles ---
    function showCopyFeedback(element, feedbackText) {
        // Find the text part of the menu item, ignoring the icon
        const textNode = Array.from(element.childNodes).find(node => node.nodeType === Node.TEXT_NODE);
        if (textNode) {
            const originalText = textNode.textContent;
            textNode.textContent = ` ${feedbackText}`; // The space at the start looks better
            setTimeout(() => {
                textNode.textContent = originalText;
            }, 1200); // A little longer to see the message
        }
    }

if (copyMainTitleItem) {
        copyMainTitleItem.addEventListener('click', () => {
            if (currentAnimeData && currentAnimeData.name) {
                navigator.clipboard.writeText(currentAnimeData.name).then(() => {
                    showCopyFeedback(copyMainTitleItem, 'Copied!');
                });
            }
            hideContextMenu();
        });
    }

    if (copyEnglishTitleItem) {
        copyEnglishTitleItem.addEventListener('click', () => {
            if (currentAnimeData && currentAnimeData.english_title) {
                navigator.clipboard.writeText(currentAnimeData.english_title).then(() => {
                    showCopyFeedback(copyEnglishTitleItem, 'Copied!');
                });
            } else {
                showCopyFeedback(copyEnglishTitleItem, "No English Title!");
            }
            hideContextMenu();
        });
    }
    // --- End of New Code ---

}); // This is the closing bracket for the main DOMContentLoaded listener