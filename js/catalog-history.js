(() => {
    const seasons = ['WINTER', 'SPRING', 'SUMMER', 'FALL'];
    function seasonWindow(anime) {
        let season = String(anime.season || '').toUpperCase();
        if (season === 'AUTUMN') season = 'FALL';
        let year = anime.season_year ?? anime.seasonYear;
        if (!seasons.includes(season) || !Number.isInteger(year)) {
            const match = /^(\d{4})-(\d{2})(?:-\d{2})?$/.exec(anime.start_date || '');
            if (!match || Number(match[2]) < 1 || Number(match[2]) > 12) return null;
            year = Number(match[1]);
            season = seasons[Math.floor((Number(match[2]) - 1) / 3)];
        }
        if (year < 1000 || year > 9999) return null;
        const month = seasons.indexOf(season) * 3;
        return { start: Date.UTC(year, month, 1) / 1000, end: Date.UTC(year, month + 3, 1) / 1000,
            label: `${season[0] + season.slice(1).toLowerCase()} ${year}` };
    }

    function seasonPoints(nodes, window) {
        const unique = new Map();
        for (const node of nodes || []) {
            if (Number.isFinite(node.date) && node.date >= window.start && node.date < window.end
                && Number.isFinite(node.averageScore) && node.averageScore > 0 && node.averageScore <= 100) unique.set(node.date, node);
        }
        return [...unique.values()].sort((a, b) => a.date - b.date);
    }
    window.catalogScoreHistory = { seasonWindow, seasonPoints };
})();
