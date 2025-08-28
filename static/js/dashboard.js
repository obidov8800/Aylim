// static/js/dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    const menuToggleBtn = document.getElementById('menu-toggle');
    const sidebar = document.querySelector('.sidebar');

    if (menuToggleBtn && sidebar) {
        menuToggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }

    document.addEventListener('click', function(event) {
        if (sidebar && sidebar.classList.contains('show') && !sidebar.contains(event.target) && !menuToggleBtn.contains(event.target)) {
            sidebar.classList.remove('show');
        }
    });
});