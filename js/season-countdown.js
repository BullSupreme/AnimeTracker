(() => {
    function updateCountdowns() {
        const now = new Date();
        const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
        document.querySelectorAll('[data-season-start]').forEach(badge => {
            const [year, month, day] = badge.dataset.seasonStart.split('-').map(Number);
            // Compare calendar days in UTC to avoid daylight-saving hour differences.
            const days = Math.round((Date.UTC(year, month - 1, day) - today) / 86400000);
            badge.textContent = days < 0 ? 'Season underway' : days === 0 ? 'Starts today'
                : `Starts in ${days} ${days === 1 ? 'day' : 'days'}`;
        });
    }

    updateCountdowns();
    setInterval(updateCountdowns, 60000);
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) updateCountdowns();
    });
})();
