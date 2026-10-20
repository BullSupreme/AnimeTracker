const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require('playwright');

(async () => {
    const root = path.resolve(__dirname, '..');
    const server = http.createServer((request, response) => {
        const file = path.resolve(root, '.' + decodeURIComponent(request.url.split('?')[0]));
        if (!file.startsWith(root + path.sep)) { response.writeHead(403).end(); return; }
        try {
            const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png' };
            response.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
            response.end(fs.readFileSync(file));
        } catch { response.writeHead(404).end(); }
    });
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    let browser;
    try {
        browser = await chromium.launch({ headless: true, executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined });
        const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
        const errors = [];
        const counts = new Map();
        let failTop = false;
        let failDetails = false;
        let slowID = null;
        const media = id => ({ id, idMal: 123, title: { romaji: 'Fixture anime', english: 'Fixture anime' }, coverImage: { large: '' }, averageScore: 85, genres: ['Action'], status: 'FINISHED', isAdult: false });
        const mal = { mal_id: 999999, title: 'MAL-only fixture', title_english: 'MAL-only fixture', score: 9.1, rank: 24, scored_by: 1000, status: 'Finished Airing', genres: [{ name: 'Action' }], images: { jpg: {} } };
        page.on('pageerror', error => errors.push(error.stack || error.message));
        page.on('console', message => { if (process.env.DISCOVERY_DEBUG && message.type() === 'warning') console.log(message.text()); });
        await page.route('**/*', async route => {
            const url = route.request().url();
            if (url.startsWith('http://127.0.0.1:')) return route.continue();
            if (process.env.DISCOVERY_DEBUG) console.log(url);
            if (url.startsWith('https://graphql.anilist.co')) {
                const payload = route.request().postDataJSON();
                const id = payload.variables?.id;
                if (!id) return route.fulfill({ json: { data: { Page: { media: [media(900010)] } } } });
                counts.set(id, (counts.get(id) || 0) + 1);
                if (id === slowID) await new Promise(resolve => setTimeout(resolve, 250));
                if (failDetails) return route.fulfill({ status: 503, json: {} });
                return route.fulfill({ json: { data: { Media: {
                    averageScore: id === slowID ? 99 : 85,
                    trends: { nodes: id === 900001 ? [{ date: 1777600, averageScore: null }] : [{ date: 1000000, averageScore: 80 }, { date: 1086400, averageScore: 81 }, { date: 1691200, averageScore: 82 }, { date: 1777600, averageScore: null }] },
                    recommendations: { edges: [{ node: { mediaRecommendation: { ...media(900001), title: { romaji: 'Safe <b>title</b>' } } } }, { node: { mediaRecommendation: { ...media(900002), isAdult: true } } }] },
                } } } });
            }
            if (url.startsWith('https://api.jikan.moe/')) {
                if (url.includes('/top/anime')) {
                    if (failTop) return route.fulfill({ status: 503, json: {} });
                    return route.fulfill({ json: { data: [mal], pagination: { has_next_page: false } } });
                }
                return route.fulfill({ json: { data: mal } });
            }
            if (process.env.CATALOG_SCREENSHOTS) return route.continue();
            return route.abort();
        });
        await page.goto(`http://127.0.0.1:${server.address().port}/all-anime.html`, { waitUntil: 'domcontentloaded' });
        const first = page.locator('#anime-grid .anime-card').first();
        const firstID = Number(await first.getAttribute('data-anime-id'));
        assert.equal(await page.locator('.score-badge').count(), 0);
        await first.locator('.catalog-explore-btn').click();
        const dialog = page.locator('.catalog-details');
        await dialog.locator('.catalog-history-chart').waitFor();
        assert.equal(await dialog.locator('[data-anilist-score]').textContent(), '85/100');
        assert.equal(await dialog.locator('.catalog-history-chart circle').count(), 3);
        assert.equal((await dialog.locator('.catalog-history-chart path').getAttribute('d')).split('M').length - 1, 2);
        assert.equal(await dialog.locator('.catalog-recommendation').count(), 1);
        assert.equal(await dialog.locator('.catalog-recommendation span').textContent(), 'Safe <b>title</b>');
        assert.equal(await dialog.locator('.catalog-recommendation b').count(), 0);
        await dialog.locator('[data-detail-favorite]').click();
        assert(await first.evaluate(card => card.classList.contains('favorite')));
        if (process.env.CATALOG_SCREENSHOTS) {
            const screenshot = path.join(process.env.CATALOG_SCREENSHOTS, 'catalog-discovery-desktop.png');
            await page.screenshot({ path: screenshot }); console.log(screenshot);
        }
        await page.keyboard.press('Escape');
        await first.locator('.catalog-explore-btn').click();
        assert.equal(counts.get(firstID), 1);
        await dialog.locator('.catalog-recommendation').click();
        await page.waitForFunction(() => document.getElementById('catalog-detail-title').textContent === 'Safe <b>title</b>');
        assert(await dialog.isVisible());
        await page.waitForFunction(() => document.querySelector('[data-history]').textContent.includes('Not enough recorded scores'));
        assert.equal(await dialog.locator('.catalog-history-chart').count(), 0);
        await dialog.locator('[data-detail-back]').click();
        await dialog.locator('.catalog-history-chart').waitFor();
        assert.equal(counts.get(firstID), 1);
        await page.keyboard.press('Escape');

        const second = page.locator('#anime-grid .anime-card').nth(1);
        slowID = Number(await second.getAttribute('data-anime-id'));
        await second.locator('.catalog-explore-btn').click();
        await page.keyboard.press('Escape');
        const oldResponse = page.waitForResponse(response => response.url().startsWith('https://graphql.anilist.co') && response.request().postDataJSON().variables?.id === slowID);
        await first.locator('.catalog-explore-btn').click();
        await oldResponse;
        await page.waitForFunction(() => document.querySelector('[data-anilist-score]').textContent === '85/100');
        assert.equal(await dialog.locator('[data-anilist-score]').textContent(), '85/100');
        await page.keyboard.press('Escape');

        await page.selectOption('#discovery-source', 'anilist');
        await page.waitForFunction(() => document.querySelector('#discovery-source-note').textContent.includes('Source: AniList API.'));
        assert.equal(await page.locator('#anime-grid .anime-card').count(), 1);
        assert(await page.locator('#sort-select').isDisabled());
        await page.selectOption('#discovery-source', 'mal-popular');
        await page.waitForFunction(() => document.querySelector('#discovery-source-note').textContent.includes('MyAnimeList most popular'), null, { timeout: 10000 }).catch(async error => {
            console.log(await page.locator('#discovery-source-note').textContent());
            throw error;
        });
        assert.equal(await page.locator('#anime-grid .anime-card').first().getAttribute('data-anime-id'), 'mal-999999');
        await page.locator('#anime-grid .favorite-btn').click();
        assert(await page.locator('#anime-grid .anime-card').evaluate(card => card.classList.contains('favorite')));
        await page.locator('#anime-grid .catalog-explore-btn').click();
        await page.waitForFunction(() => document.querySelector('[data-mal-score]').textContent === '9.1/10');
        assert((await dialog.locator('[data-history]').textContent()).includes('requires a linked AniList'));
        await page.keyboard.press('Escape');

        failTop = true;
        await page.selectOption('#discovery-source', 'mal-rated');
        await page.waitForFunction(() => document.querySelector('#discovery-source-note').dataset.error === 'true');
        assert.equal(await page.locator('#discovery-source').inputValue(), 'catalog');
        assert(!(await page.locator('#sort-select').isDisabled()));
        await page.selectOption('#discovery-genre', 'Action');
        assert(await page.locator('#anime-grid .anime-card').count() > 0);
        await page.check('#discovery-favorites');
        assert(await page.locator('#anime-grid .anime-card').evaluateAll(cards => cards.every(card => card.classList.contains('favorite'))));
        await page.uncheck('#discovery-favorites');
        await page.selectOption('#discovery-genre', '');
        failDetails = true;
        await page.locator('#anime-grid .anime-card').nth(3).locator('.catalog-explore-btn').click();
        await page.waitForFunction(() => document.querySelector('[data-history]').textContent.includes('temporarily unavailable'));
        await page.setViewportSize({ width: 390, height: 844 });
        const bounds = await dialog.boundingBox();
        assert(bounds.x >= 0 && bounds.x + bounds.width <= 390);
        assert.equal(await dialog.evaluate(el => el.scrollWidth > el.clientWidth), false);
        if (process.env.CATALOG_SCREENSHOTS) {
            const screenshot = path.join(process.env.CATALOG_SCREENSHOTS, 'catalog-discovery-mobile.png');
            await page.screenshot({ path: screenshot }); console.log(screenshot);
        }
        assert.deepEqual(errors, []);
        console.log('Discovery checks passed: no stars, details, score chart gaps, safe recommendations, caching, race protection, favorites, source lists, API failures, filtering, and mobile');
    } finally { await browser?.close(); server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
