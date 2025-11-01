function DarkMode() {
    this.darkModeToggle = document.getElementById('darkModeToggle');
    if (!this.darkModeToggle) return;

    // Respect system preference if no explicit choice stored
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const stored = localStorage.getItem('darkMode');
    this.isDarkMode = stored === null ? prefersDark : stored === 'true';

    this.applyTheme(this.isDarkMode, false);
    this.updateToggleAppearance(this.isDarkMode);

    // Toggle click
    this.darkModeToggle.addEventListener('click', () => {
        this.isDarkMode = !this.isDarkMode;
        localStorage.setItem('darkMode', String(this.isDarkMode));
        this.applyTheme(this.isDarkMode, true);
        this.updateToggleAppearance(this.isDarkMode);
    });

    // Sync with system preference if user hasn't chosen explicitly
    if (stored === null && window.matchMedia) {
        const mql = window.matchMedia('(prefers-color-scheme: dark)');
        const systemChange = (e) => {
            this.isDarkMode = e.matches;
            this.applyTheme(this.isDarkMode, true);
            this.updateToggleAppearance(this.isDarkMode);
        };
        // Modern browsers
        if (typeof mql.addEventListener === 'function') {
            mql.addEventListener('change', systemChange);
        } else if (typeof mql.addListener === 'function') {
            mql.addListener(systemChange);
        }
    }
}

DarkMode.prototype.updateToggleAppearance = function(isDark) {
    const iconElement = this.darkModeToggle.querySelector('i');
    const textElement = this.darkModeToggle.querySelector('span');
    
    if (isDark) {
        iconElement.classList.remove('fa-moon');
        iconElement.classList.add('fa-sun');
        textElement.textContent = 'Light Mode';
        this.darkModeToggle.classList.remove('active');
    } else {
        iconElement.classList.remove('fa-sun');
        iconElement.classList.add('fa-moon');
        textElement.textContent = 'Dark Mode';
        this.darkModeToggle.classList.add('active');
    }
};

// Apply theme instantly - completely instant switch
DarkMode.prototype.applyTheme = function(isDark, animate) {
    const root = document.documentElement;
    // Disable all transitions temporarily for instant switch
    if (animate) {
        root.classList.add('theme-animating');
    }
    // Apply theme immediately
    if (isDark) {
        root.setAttribute('data-theme', 'dark');
    } else {
        root.setAttribute('data-theme', 'light');
    }
    // Remove animation class immediately after theme is applied
    if (animate) {
        // Force reflow to ensure theme is applied
        void root.offsetHeight;
        // Remove class in next frame to allow re-enable of transitions
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                root.classList.remove('theme-animating');
            });
        });
    }
};

// Initialize dark mode when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => new DarkMode());