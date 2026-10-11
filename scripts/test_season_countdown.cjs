const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

let current = '2026-12-31T12:00:00';
class TestDate extends Date {
    constructor() { super(current); }
}
const badge = { dataset: { seasonStart: '2027-01-01' }, textContent: '' };
let interval;
let visibilityChanged;
const document = {
    hidden: false,
    querySelectorAll: () => [badge],
    addEventListener: (_, callback) => { visibilityChanged = callback; },
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../js/season-countdown.js'), 'utf8'), {
    Date: TestDate, document, setInterval: callback => { interval = callback; },
});
assert.equal(badge.textContent, 'Starts in 1 day');
current = '2027-01-01T12:00:00';
interval();
assert.equal(badge.textContent, 'Starts today');
current = '2027-01-02T12:00:00';
visibilityChanged();
assert.equal(badge.textContent, 'Season underway');
badge.dataset.seasonStart = '2027-04-01';
current = '2027-03-07T12:00:00';
interval();
assert.equal(badge.textContent, 'Starts in 25 days');
console.log('Browser countdown: day rollover, visibility refresh, and DST-safe dates passed');
