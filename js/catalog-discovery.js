(() => {
    const app = window.catalogDiscovery;
    if (!app) return;
    const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const validID = id => Number.isInteger(Number(id)) && Number(id) > 0;
    const safeImage = value => {
        try { const url = new URL(value); return url.protocol === 'https:' ? url.href : ''; } catch { return ''; }
    };
    const entries = new Map(app.catalog.map(anime => [String(anime.id), anime]));
    const cache = new Map();
    let malQueue = Promise.resolve();
    let detailRequest = 0;
    let currentAnime = null;
    const detailHistory = [];

    async function request(url, body) {
        const key = url + (body || '');
        const existing = cache.get(key);
        if (existing && existing.expires > Date.now()) return existing.promise;
        const load = async () => {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 12000);
            try {
                const response = await fetch(url, {
                    signal: controller.signal,
                    ...(body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body } : {}),
                });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const json = await response.json();
                if (json.errors?.length) throw new Error('Source query failed');
                return json;
            } finally { clearTimeout(timeout); }
        };
        // Space request starts to respect Jikan's minute limit without blocking on a slow response.
        const promise = url.startsWith('https://api.jikan.moe/')
            ? malQueue.then(load) : load();
        if (url.startsWith('https://api.jikan.moe/')) {
            malQueue = malQueue.then(() => new Promise(resolve => setTimeout(resolve, 1100)));
        }
        cache.set(key, { expires: Date.now() + 30 * 60000, promise });
        try { return await promise; } catch (error) { cache.delete(key); throw error; }
    }

    function fromAniList(media) {
        const known = entries.get(String(media.id)) || {};
        const anime = { ...known, id: media.id, mal_id: media.idMal || known.mal_id,
            name: media.title?.romaji || media.title?.english || known.name || 'Untitled anime',
            english_title: media.title?.english || null,
            poster_url: safeImage(media.coverImage?.large) || known.poster_url || '',
            site_url: `https://anilist.co/anime/${media.id}/`, anilist_score: media.averageScore,
            popularity: media.popularity ?? known.popularity ?? 0,
            season: media.season || known.season, season_year: media.seasonYear || known.season_year,
            episodes: media.episodes ?? known.episodes, status: media.status || known.status,
            genres: Array.isArray(media.genres) ? media.genres : known.genres || [],
        };
        entries.set(String(anime.id), anime);
        return anime;
    }


    const dialog = document.createElement('dialog');
    dialog.className = 'catalog-details';
    dialog.setAttribute('aria-labelledby', 'catalog-detail-title');
    dialog.innerHTML = `<div class="catalog-dialog-bar"><div><button type="button" data-detail-back hidden>Back</button><span>Explore anime</span></div><button type="button" data-detail-close>Close</button></div><div class="catalog-detail-body"></div>`;
    document.body.appendChild(dialog);
    const body = dialog.querySelector('.catalog-detail-body');
    dialog.querySelector('[data-detail-close]').addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => { detailRequest++; currentAnime = null; detailHistory.length = 0; });
    const backButton = dialog.querySelector('[data-detail-back]');
    backButton.addEventListener('click', () => {
        const anime = detailHistory.pop();
        if (anime) openDetails(anime, false);
    });
    dialog.addEventListener('click', event => {
        if (event.target !== dialog) return;
        const bounds = dialog.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
    });

    function score(value, maximum) {
        return typeof value === 'number' && Number.isFinite(value) && value > 0 && value <= maximum ? `${value}/${maximum}` : 'No score available';
    }

    function renderHistory(nodes) {
        const unique = new Map();
        for (const node of nodes || []) {
            if (Number.isFinite(node.date) && node.date > 0 && Number.isFinite(node.averageScore) && node.averageScore > 0 && node.averageScore <= 100) unique.set(node.date, node);
        }
        const points = [...unique.values()].sort((a, b) => a.date - b.date);
        const target = body.querySelector('[data-history]');
        if (points.length < 2) {
            target.innerHTML = '<p class="catalog-detail-note">Not enough recorded scores for a chart. Missing history is not estimated.</p>';
            return;
        }
        const low = Math.max(0, Math.floor(Math.min(...points.map(p => p.averageScore))) - 2);
        const high = Math.min(100, Math.ceil(Math.max(...points.map(p => p.averageScore))) + 2);
        const x = p => 40 + (p.date - points[0].date) / (points.at(-1).date - points[0].date) * 620;
        const y = p => 154 - (p.averageScore - low) / Math.max(1, high - low) * 130;
        let segments = '';
        points.forEach((p, index) => { segments += `${index && p.date - points[index - 1].date <= 172800 ? 'L' : 'M'}${x(p).toFixed(1)},${y(p).toFixed(1)} `; });
        const format = timestamp => new Date(timestamp * 1000).toLocaleDateString(undefined, { month: 'short', day: 'numeric', timeZone: 'UTC' });
        target.innerHTML = `<svg class="catalog-history-chart" viewBox="0 0 700 190" role="img" aria-label="AniList daily scores, ${points.length} recorded observations, scale ${low} to ${high} out of 100">
            <line x1="40" y1="24" x2="660" y2="24"/><line x1="40" y1="154" x2="660" y2="154"/>
            <text x="5" y="28">${high}</text><text x="5" y="158">${low}</text><path d="${segments}"/>
            ${points.map(p => `<circle cx="${x(p).toFixed(1)}" cy="${y(p).toFixed(1)}" r="3"><title>${escape(format(p.date))}: ${p.averageScore}/100</title></circle>`).join('')}
            <text x="40" y="180">${escape(format(points[0].date))}</text><text x="660" y="180" text-anchor="end">${escape(format(points.at(-1).date))}</text></svg>
            <p class="catalog-detail-note">Latest ${points.length} available daily scores from AniList, out of 100. Gaps longer than two days are not connected.</p>`;
    }

    function renderRecommendations(edges, currentID) {
        const seen = new Set([String(currentID)]);
        const recommendations = [];
        for (const edge of edges || []) {
            const media = edge?.node?.mediaRecommendation;
            if (!media || media.isAdult || !validID(media.id) || seen.has(String(media.id))) continue;
            seen.add(String(media.id));
            recommendations.push(fromAniList(media));
            if (recommendations.length === 24) break;
        }
        const target = body.querySelector('[data-recommendations]');
        target.innerHTML = recommendations.length ? `<div class="catalog-recommendations">${recommendations.map(a => `<button type="button" class="catalog-recommendation" data-explore-id="${escape(a.id)}" aria-label="${escape('Explore ' + (a.english_title || a.name))}"><img src="${escape(safeImage(a.poster_url))}" alt="" loading="lazy"><span>${escape(a.english_title || a.name)}</span></button>`).join('')}</div>`
            : '<p class="catalog-detail-note">No community recommendations available yet.</p>';
    }

    async function openDetails(anime, remember = true) {
        if (remember && dialog.open && currentAnime && currentAnime.id !== anime.id) detailHistory.push(currentAnime);
        currentAnime = anime;
        backButton.hidden = detailHistory.length === 0;
        const token = ++detailRequest;
        if (typeof stopAllTrailers === 'function') stopAllTrailers();
        const aniID = validID(anime.id) ? Number(anime.id) : null;
        const malID = validID(anime.mal_id) ? Number(anime.mal_id) : null;
        const label = anime.english_title || anime.name;
        body.innerHTML = `<div class="catalog-detail-heading"><img class="catalog-detail-poster" src="${escape(safeImage(anime.poster_url))}" alt="">
            <div><h2 id="catalog-detail-title">${escape(label)}</h2>${anime.english_title && anime.english_title !== anime.name ? `<p>${escape(anime.name)}</p>` : ''}
            <p>${escape([anime.season, anime.season_year, anime.status?.replaceAll('_', ' '), anime.episodes ? `${anime.episodes} episodes` : null].filter(Boolean).join(' / '))}</p>
            <p>${escape((anime.genres || []).join(' / '))}</p>
            <div class="catalog-detail-links">${aniID ? `<a href="https://anilist.co/anime/${aniID}/" target="_blank" rel="noopener noreferrer">AniList</a>` : ''}
            ${malID ? `<a href="https://myanimelist.net/anime/${malID}" target="_blank" rel="noopener noreferrer">MyAnimeList</a>` : ''}
            <button type="button" data-detail-favorite>${app.isFavorite(anime.id) ? 'Favorited' : 'Add to favorites'}</button></div></div></div>
            <div class="catalog-detail-ratings"><div class="catalog-rating"><small>AniList community rating</small><strong data-anilist-score>${escape(score(anime.anilist_score, 100))}</strong><span data-anilist-note>${aniID ? 'Checking latest score...' : 'No linked AniList entry'}</span></div>
            <div class="catalog-rating"><small>MyAnimeList community rating</small><strong data-mal-score>${escape(score(anime.mal_score, 10))}</strong><span data-mal-note>${malID ? 'Loading via Jikan...' : 'No linked MAL entry'}</span></div></div>
            <section class="catalog-detail-section"><h3>Score history</h3><div data-history><p class="catalog-detail-note">${aniID ? 'Loading AniList daily scores...' : 'Score history requires a linked AniList entry.'}</p></div></section>
            <section class="catalog-detail-section"><h3>More like this</h3><p class="catalog-detail-note">Community recommendations from AniList, not generated guesses.</p><div data-recommendations><p class="catalog-detail-note">${aniID ? 'Loading recommendations...' : 'Recommendations require a linked AniList entry.'}</p></div></section>`;
        body.querySelector('[data-detail-favorite]').addEventListener('click', event => {
            app.toggleFavorite(anime.id);
            event.currentTarget.textContent = app.isFavorite(anime.id) ? 'Favorited' : 'Add to favorites';
        });
        if (!dialog.open) dialog.showModal();
        else (backButton.hidden ? dialog.querySelector('[data-detail-close]') : backButton).focus({ preventScroll: true });
        dialog.scrollTop = 0;
        const isCurrent = () => token === detailRequest && dialog.open;
        if (aniID) {
            const query = `query ($id: Int!) { Media(id: $id, type: ANIME) { averageScore
                trends(sort: DATE_DESC, perPage: 25) { nodes { date averageScore } }
                recommendations(sort: RATING_DESC, perPage: 25) { edges { node { mediaRecommendation {
                    id idMal title { romaji english } coverImage { large } averageScore popularity season seasonYear episodes status genres isAdult
                } } } }
            } }`;
            request('https://graphql.anilist.co', JSON.stringify({ query, variables: { id: aniID } })).then(json => {
                if (!isCurrent()) return;
                const media = json.data.Media;
                if (!media) throw new Error('No media');
                body.querySelector('[data-anilist-score]').textContent = score(media.averageScore, 100);
                body.querySelector('[data-anilist-note]').textContent = 'Latest available weighted average';
                renderHistory(media.trends?.nodes);
                renderRecommendations(media.recommendations?.edges, aniID);
            }).catch(() => {
                if (!isCurrent()) return;
                body.querySelector('[data-anilist-note]').textContent = 'Live source unavailable; showing saved rating if available';
                body.querySelector('[data-history]').innerHTML = '<p class="catalog-detail-note">History is temporarily unavailable. Try again later.</p>';
                body.querySelector('[data-recommendations]').innerHTML = '<p class="catalog-detail-note">Recommendations are temporarily unavailable. Try again later.</p>';
            });
        }
        if (malID) {
            request(`https://api.jikan.moe/v4/anime/${malID}`).then(json => {
                if (!isCurrent()) return;
                const data = json.data;
                body.querySelector('[data-mal-score]').textContent = score(data.score, 10);
                body.querySelector('[data-mal-note]').textContent = [data.rank ? `MAL overall rating rank #${data.rank}` : null, data.scored_by ? `${Number(data.scored_by).toLocaleString()} ratings` : null, 'via Jikan'].filter(Boolean).join(' / ');
            }).catch(() => {
                if (isCurrent()) body.querySelector('[data-mal-note]').textContent = 'MAL source temporarily unavailable; try again later';
            });
        }
    }

    document.addEventListener('click', event => {
        const button = event.target.closest('[data-explore-id]');
        if (button) {
            event.preventDefault();
            const anime = entries.get(button.dataset.exploreId);
            if (anime) openDetails(anime);
            return;
        }
        const card = event.target.closest('#anime-grid .all-anime-card');
        if (!card || event.target.closest('a, button, summary, details, iframe')) return;
        const anime = entries.get(card.dataset.animeId);
        if (anime) openDetails(anime);
    });
})();
