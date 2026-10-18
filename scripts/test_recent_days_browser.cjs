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
        const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
        const errors = [];
        page.on('pageerror', error => errors.push(error.stack));
        await page.route('https://**', route => process.env.RECENT_DAYS_SCREENSHOTS ? route.continue() : route.abort());
        await page.goto(`http://127.0.0.1:${server.address().port}/index.html`, { waitUntil: 'domcontentloaded' });
        const rail = page.locator('#recent-days-rail');
        const popup = page.locator('#recent-day-popup');
        assert(await rail.isVisible());
        assert.equal(await rail.locator('[data-recent-day]').count(), 7);
        const dates = await rail.locator('[data-recent-day]').evaluateAll(buttons => buttons.map(b => b.dataset.recentDay));
        for (let i = 1; i < dates.length; i++) assert.equal((Date.parse(dates[i - 1]) - Date.parse(dates[i])) / 864e5, 1);
        const before = await page.locator('main').boundingBox();
        await rail.locator('button').nth(1).click();
        assert(await popup.isVisible());
        assert(await rail.isVisible());
        assert.deepEqual(await page.locator('main').boundingBox(), before);
        const visiblePanel = popup.locator('[data-recent-lineup]:visible');
        assert.equal(await visiblePanel.getAttribute('data-recent-lineup'), dates[1]);
        assert(await visiblePanel.locator('.anime-card').count() > 0);
        if (process.env.RECENT_DAYS_SCREENSHOTS) {
            await page.waitForFunction(() => [...document.querySelectorAll('[data-recent-lineup]:not([hidden]) .anime-poster')].slice(0, 3).every(img => img.complete && img.naturalWidth > 0), null, { timeout: 10000 }).catch(() => {});
            await visiblePanel.locator('.anime-grid').evaluate(el => Promise.all(el.getAnimations().map(animation => animation.finished)));
            const screenshot = path.join(process.env.RECENT_DAYS_SCREENSHOTS, 'recent-days-desktop.png');
            await page.screenshot({ path: screenshot });
            console.log(screenshot);
        }
        const first = visiblePanel.locator('.anime-card').first();
        const id = await first.getAttribute('data-anime-id');
        await first.locator('.favorite-btn').click();
        assert(await first.evaluate(card => card.classList.contains('favorite')));
        assert((await page.context().cookies()).some(cookie => cookie.name === 'favorites' && decodeURIComponent(cookie.value).includes(id)));
        assert((await first.locator('.main-link-btn').getAttribute('href')).includes('anilist.co'));
        const allCount = await visiblePanel.locator('.anime-card').count();
        // The popup covers the controls visually; invoke the actual filter button handler.
        await page.locator('.list-tab[data-list-tab="favorites"]').evaluate(button => button.click());
        assert.equal(await visiblePanel.locator('.anime-card:visible').count(), 1);
        assert.equal(await visiblePanel.locator('.anime-card:visible').getAttribute('data-anime-id'), id);
        await rail.locator('button').nth(1).click();
        assert.equal(await visiblePanel.locator('.anime-card:visible').count(), 1);
        await first.locator('.favorite-btn').click();
        assert.equal(await visiblePanel.locator('.anime-card:visible').count(), 0);
        assert.equal(await visiblePanel.locator('.recent-day-no-data:visible').textContent(), 'No favorite anime aired on this day.');
        await page.locator('.list-tab[data-list-tab="all"]').evaluate(button => button.click());
        assert.equal(await visiblePanel.locator('.anime-card:visible').count(), allCount);
        await first.locator('.favorite-btn').click();
        await page.selectOption('#layout-selector', 'table');
        assert.equal(await popup.locator('.table-cell-title').count(), 0);
        await rail.locator('button').nth(2).click();
        assert.equal(await popup.locator('[data-recent-lineup]:visible').getAttribute('data-recent-lineup'), dates[2]);
        await page.keyboard.press('Escape');
        assert(!(await popup.isVisible()));
        assert(await rail.isVisible());
        await page.setViewportSize({ width: 390, height: 844 });
        await page.reload();
        await page.selectOption('#layout-selector', 'grid');
        const mobileWidth = await page.evaluate(() => document.documentElement.scrollWidth);
        assert(!(await rail.isVisible()));
        await page.locator('#recent-days-toggle').click();
        await rail.locator('button').nth(1).click();
        assert(await rail.isVisible());
        const railBox = await rail.boundingBox();
        const popupBox = await popup.boundingBox();
        const headerBox = await page.locator('header').boundingBox();
        assert(popupBox.y >= headerBox.y + headerBox.height);
        assert(popupBox.x >= railBox.x + railBox.width);
        assert(popupBox.x + popupBox.width <= 390);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), mobileWidth);
        const savedFavorite = popup.locator('[data-recent-lineup]:visible .anime-card').first();
        assert(await savedFavorite.evaluate(card => card.classList.contains('favorite')));
        await savedFavorite.locator('.favorite-btn').click();
        assert(await page.locator(`.anime-card[data-anime-id="${id}"]`).evaluateAll(cards => cards.every(card => !card.classList.contains('favorite'))));
        if (process.env.RECENT_DAYS_SCREENSHOTS) {
            const screenshot = path.join(process.env.RECENT_DAYS_SCREENSHOTS, 'recent-days-mobile.png');
            await page.screenshot({ path: screenshot });
            console.log(screenshot);
        }
        assert.deepEqual(errors, []);
        console.log('Browser checks passed: seven days, unchanged main layout, day switching, favorites-only popups, empty state, live filtering, links, table isolation, Escape, and mobile');
    } finally {
        await browser?.close();
        server.close();
    }
})().catch(error => { console.error(error); process.exitCode = 1; });
