const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const context = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../js/catalog-history.js'), 'utf8'), context);
const { seasonWindow, seasonPoints } = context.window.catalogScoreHistory;
const winter = seasonWindow({ season: 'WINTER', season_year: 2021 });
assert.equal(winter.start, Date.UTC(2021, 0, 1) / 1000);
assert.equal(winter.end, Date.UTC(2021, 3, 1) / 1000);
assert.equal(winter.label, 'Winter 2021');
assert.equal(seasonWindow({ season: 'FALL', season_year: 2026 }).end, Date.UTC(2027, 0, 1) / 1000);
const leap = seasonWindow({ season: 'winter', season_year: 2024 });
assert.equal((leap.end - leap.start) / 86400, 91);
assert.equal(seasonWindow({ start_date: '2021-05-12' }).label, 'Spring 2021');
assert.equal(seasonWindow({ start_date: '2021-13-01' }), null);
assert.equal(seasonWindow({}), null);
const nodes = [
    { date: winter.start - 1, averageScore: 99 },
    { date: winter.start, averageScore: 80 },
    { date: winter.start, averageScore: 81 },
    { date: winter.end - 1, averageScore: 85 },
    { date: winter.end, averageScore: 100 },
    { date: winter.start + 86400, averageScore: null },
    { date: winter.start + 172800, averageScore: 0 },
    { date: winter.start + 259200, averageScore: 101 },
];
const points = seasonPoints(nodes, winter);
assert.equal(points.length, 2);
assert.equal(points[0].averageScore, 81);
assert.equal(points[1].averageScore, 85);
console.log('Season-history helpers passed: original quarter, year rollover, leap year, start-date fallback, boundaries, deduplication, and missing scores');
