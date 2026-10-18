document.addEventListener('DOMContentLoaded', () => {
    const rail = document.getElementById('recent-days-rail');
    const toggle = document.getElementById('recent-days-toggle');
    const popup = document.getElementById('recent-day-popup');
    if (!rail || !toggle || !popup) return;
    const buttons = [...rail.querySelectorAll('[data-recent-day]')];
    const panels = [...popup.querySelectorAll('[data-recent-lineup]')];
    const title = popup.querySelector('h2');
    const close = popup.querySelector('.recent-day-close');
    let selected = null;
    const header = document.querySelector('header');
    if (header) {
        const positionBelowHeader = () => {
            const top = Math.max(78, Math.ceil(header.getBoundingClientRect().height) + 12);
            document.documentElement.style.setProperty('--recent-days-top', `${top}px`);
        };
        positionBelowHeader();
        new ResizeObserver(positionBelowHeader).observe(header);
    }

    function closePopup() {
        popup.hidden = true;
        popup.querySelectorAll('.trailer-close-btn').forEach(button => button.click());
        buttons.forEach(button => button.setAttribute('aria-expanded', 'false'));
        selected?.focus();
    }

    function setRail(open) {
        rail.hidden = !open;
        toggle.setAttribute('aria-expanded', String(open));
        if (!open && !popup.hidden) closePopup();
    }

    setRail(window.matchMedia('(min-width: 1760px)').matches);
    toggle.addEventListener('click', () => setRail(rail.hidden));
    buttons.forEach(button => button.addEventListener('click', () => {
        popup.querySelectorAll('.trailer-close-btn').forEach(control => control.click());
        selected = button;
        panels.forEach(panel => { panel.hidden = panel.dataset.recentLineup !== button.dataset.recentDay; });
        buttons.forEach(day => day.setAttribute('aria-expanded', String(day === button)));
        title.textContent = button.dataset.dayTitle;
        popup.hidden = false;
        popup.scrollTop = 0;
        close.focus({ preventScroll: true });
    }));
    close.addEventListener('click', closePopup);
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && !popup.hidden && !document.querySelector('#anime-modal.active')) {
            closePopup();
        }
    });
});
