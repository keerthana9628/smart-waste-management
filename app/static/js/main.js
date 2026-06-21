// ============================================================
// Smart Waste Management System - Main JS
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

    // ---------------------------------------------------------
    // Dark mode toggle (persisted in localStorage)
    // ---------------------------------------------------------
    const darkModeToggle = document.getElementById('darkModeToggle');
    const htmlEl = document.documentElement;
    const savedTheme = localStorage.getItem('swms-theme') || 'light';
    htmlEl.setAttribute('data-bs-theme', savedTheme);
    updateDarkModeIcon(savedTheme);

    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            const current = htmlEl.getAttribute('data-bs-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            htmlEl.setAttribute('data-bs-theme', next);
            localStorage.setItem('swms-theme', next);
            updateDarkModeIcon(next);
        });
    }

    function updateDarkModeIcon(theme) {
        if (!darkModeToggle) return;
        const icon = darkModeToggle.querySelector('i');
        if (!icon) return;
        icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
    }

    // ---------------------------------------------------------
    // Sidebar toggle (mobile)
    // ---------------------------------------------------------
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth < 992 &&
                sidebar.classList.contains('show') &&
                !sidebar.contains(e.target) &&
                !sidebarToggle.contains(e.target)) {
                sidebar.classList.remove('show');
            }
        });
    }

    // ---------------------------------------------------------
    // Auto-dismiss alerts after 5 seconds
    // ---------------------------------------------------------
    document.querySelectorAll('.alert').forEach((alertEl) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
            bsAlert.close();
        }, 5000);
    });

});

// ============================================================
// Helper: simulate IoT sensor update for a bin (used in console
// for demo/testing - call updateBinLevel(binId, newLevel))
// ============================================================
async function updateBinLevel(binId, fillLevel) {
    const response = await fetch(`/bins/${binId}/update-level`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fill_level: fillLevel })
    });
    const data = await response.json();
    console.log('Bin update response:', data);
    return data;
}
