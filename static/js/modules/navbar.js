export function initializeNavHighlighting() {
    const currentPath = window.location.pathname;
    
    // Normalize path - keep root path as '/' but remove trailing slashes for others
    const normalizedPath = currentPath === '/' ? '/' : 
        (currentPath.endsWith('/') ? currentPath.slice(0, -1) : currentPath);
    
    console.log('Current path:', currentPath);
    console.log('Normalized path:', normalizedPath);
    
    // Remove active class from all nav items first
    document.querySelectorAll('.nav-link, .navbar-brand').forEach(link => {
        link.classList.remove('active');
        console.log('Removed active from:', link.id);
    });
    
    const pathMap = {
        '/': 'nav-brand',
        '/workout_plan': 'nav-workout-plan',
        '/weekly_summary': 'nav-weekly-summary',
        '/session_summary': 'nav-session-summary',
        '/workout_log': 'nav-workout-log',
        '/progression': 'nav-progression-plan'
    };
    
    console.log('Looking for navId:', pathMap[normalizedPath]);
    
    // Add active class to current page's nav item
    const navId = pathMap[normalizedPath];
    console.log('NavId for path:', navId);
    if (navId) {
        const navItem = document.getElementById(navId);
        console.log('Found navItem:', navItem);
        if (navItem) {
            // Add active class to current nav item
            navItem.classList.add('active');
            console.log('Added active to:', navId);
        }
    }
}

// Initialize navbar highlighting both immediately and after DOM load
export function initializeNavbar() {
    // Re-initialize after DOM content is loaded
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM loaded, initializing navbar');
        initializeNavHighlighting();
    });
    
    // Re-initialize after navigation
    window.addEventListener('popstate', () => {
        console.log('Navigation occurred');
        initializeNavHighlighting();
    });
    
    // Add load event listener
    window.addEventListener('load', () => {
        console.log('Window loaded');
        initializeNavHighlighting();
    });
} 