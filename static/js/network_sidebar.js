// static/js/network_sidebar.js
document.addEventListener('DOMContentLoaded', function() {
    // Активация текущей страницы в сайдбаре
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.network-sidebar .nav-link');
    
    navLinks.forEach(function(link) {
        const linkPath = link.getAttribute('href');
        if (linkPath && currentPath.includes(linkPath) && linkPath !== '/network/') {
            link.classList.add('active');
        }
    });
    
    // Для главной страницы сети
    if (currentPath === '/network/' || currentPath === '/network') {
        const mainLink = document.querySelector('a[href*="equipment_list"]');
        if (mainLink) mainLink.classList.add('active');
    }
});