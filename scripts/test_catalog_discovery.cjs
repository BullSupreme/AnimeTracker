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
        const historyPages = [];
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
                if (process.env.DISCOVERY_LIVE_HISTORY) return route.continue();
                const payload = route.request().postDataJSON();
                const id = payload.variables?.id;
                if (payload.query.includes('mediaTrends')) {
                    const { start, end, page: number } = payload.variables;
                    assert.equal(start, Date.UTC(2021, 0, 1) / 1000 - 1);
                    assert.equal(end, Date.UTC(2021, 3, 1) / 1000);
                    historyPages.push(number);
                    const firstDay = start + 1;
                    const nodes = id === 900001 ? [] : number === 1 ? [
                        { date: firstDay + 8 * 86400, averageScore: 80 },
                        { date: firstDay + 9 * 86400, averageScore: 81 },
                        { date: firstDay + 10 * 86400, averageScore: null },
                    ] : [
                        { date: firstDay + 16 * 86400, averageScore: 82 },
                        { date: firstDay - 1, averageScore: 99 }, { date: end, averageScore: 99 },
                    ];
                    return route.fulfill({ json: { data: { Page: { pageInfo: { hasNextPage: id !== 900001 && number === 1 }, mediaTrends: nodes } } } });
                }
                assert.equal(payload.query.includes('perPage: 25'), true);
                counts.set(id, (counts.get(id) || 0) + 1);
                if (id === slowID) await new Promise(resolve => setTimeout(resolve, 250));
                if (failDetails) return route.fulfill({ status: 503, json: {} });
                return route.fulfill({ json: { data: { Media: {
                    averageScore: id === slowID ? 99 : 85,
                    season: 'WINTER', seasonYear: 2021,
                    recommendations: { edges: [
                        { node: { mediaRecommendation: { ...media(900001), title: { romaji: 'Safe <b>title</b>' } } } },
                        { node: { mediaRecommendation: { ...media(900002), isAdult: true } } },
                        { node: { mediaRecommendation: media(900001) } },
                        { node: { mediaRecommendation: media(id) } },
                        ...Array.from({ length: 30 }, (_, index) => ({ node: { mediaRecommendation: media(910000 + index) } })),
                    ] },
                } } } });
            }
            if (url.startsWith('https://api.jikan.moe/')) {
                if (process.env.DISCOVERY_LIVE_HISTORY) return route.abort();
                assert(!url.includes('/top/anime'));
                return route.fulfill({ json: { data: mal } });
            }
            if (process.env.CATALOG_SCREENSHOTS) return route.continue();
            return route.abort();
        });
        await page.goto(`http://127.0.0.1:${server.address().port}/all-anime.html`, { waitUntil: 'domcontentloaded' });
        if (process.env.DISCOVERY_LIVE_HISTORY) {
            await page.selectOption('#season-select', '');
            await page.locator('#search-input').fill('Horimiya');
            const horimiya = page.locator('#anime-grid .anime-card[data-anime-id="124080"]');
            await horimiya.waitFor();
            await horimiya.locator('.catalog-explore-btn').click();
            const history = page.locator('.catalog-details [data-history]');
            await history.locator('.catalog-history-chart').waitFor({ timeout: 30000 });
            assert((await history.textContent()).includes('Winter 2021'));
            const dates = await history.locator('circle title').allTextContents();
            assert(dates.length > 25);
            assert(dates.every(label => label.includes('2021')));
            console.log(`Live Horimiya chart verified: Winter 2021, ${dates.length} daily scores, ${dates[0]} through ${dates.at(-1)}`);
            if (process.env.CATALOG_SCREENSHOTS) {
                const screenshot = path.join(process.env.CATALOG_SCREENSHOTS, 'horimiya-original-season.png');
                await page.screenshot({ path: screenshot }); console.log(screenshot);
            }
            assert.deepEqual(errors, []);
            return;
        }
        const first = page.locator('#anime-grid .anime-card').first();
        const firstID = Number(await first.getAttribute('data-anime-id'));
        assert.equal(await page.locator('.score-badge').count(), 0);
        assert.equal(await page.locator('.catalog-discovery-controls, #discovery-source, #discovery-genre, #discovery-status, #discovery-favorites').count(), 0);
        await first.locator('.catalog-explore-btn').click();
        const dialog = page.locator('.catalog-details');
        await dialog.locator('.catalog-history-chart').waitFor();
        assert.equal(await dialog.locator('[data-anilist-score]').textContent(), '85/100');
        assert.equal(await dialog.locator('.catalog-history-chart circle').count(), 3);
        assert.deepEqual(historyPages.slice(0, 2), [1, 2]);
        assert((await dialog.locator('[data-history]').textContent()).includes('Winter 2021'));
        const axis = await dialog.locator('.catalog-history-chart text').allTextContents();
        assert(axis.includes('Jan 1') && axis.includes('Mar 31'));
        assert.equal((await dialog.locator('.catalog-history-chart path').getAttribute('d')).split('M').length - 1, 2);
        assert.equal(await dialog.locator('.catalog-recommendation').count(), 24);
        assert.equal(await dialog.locator('.catalog-recommendation span').first().textContent(), 'Safe <b>title</b>');
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
        await dialog.locator('.catalog-recommendation').first().click();
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
        console.log('Discovery checks passed: no extra toolbar, 24 recommendations, safe titles, details, chart gaps, caching, race protection, favorites, API failures, and mobile');
    } finally { await browser?.close(); server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
