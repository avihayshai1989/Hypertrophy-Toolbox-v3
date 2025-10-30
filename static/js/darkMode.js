function DarkMode() {
    this.darkModeToggle = document.getElementById('darkModeToggle');
    console.log('darkModeToggle element:', this.darkModeToggle);
    
    if (!this.darkModeToggle) {
        console.error('Dark mode toggle button not found!');
        return;
    }
    
    // Get the stored theme
    this.isDarkMode = localStorage.getItem('darkMode') === 'true';
    console.log('Initializing dark mode, isDarkMode:', this.isDarkMode);
    
    // Initialize dark mode state
    if (this.isDarkMode) {
        document.documentElement.setAttribute('data-theme', 'dark');
        this.updateToggleAppearance(true);
    } else {
        this.darkModeToggle.classList.add('active');
        this.updateToggleAppearance(false);
    }
    
    // Set up event listeners
    console.log('Setting up event listeners');
    this.darkModeToggle.addEventListener('click', () => {
        this.isDarkMode = !this.isDarkMode;
        localStorage.setItem('darkMode', this.isDarkMode);
        
        if (this.isDarkMode) {
            document.documentElement.setAttribute('data-theme', 'dark');
            this.darkModeToggle.classList.remove('active');
            this.updateToggleAppearance(true);
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            this.darkModeToggle.classList.add('active');
            this.updateToggleAppearance(false);
        }
    });
}

DarkMode.prototype.updateToggleAppearance = function(isDark) {
    const iconElement = this.darkModeToggle.querySelector('i');
    const textElement = this.darkModeToggle.querySelector('span');
    
    if (isDark) {
        iconElement.classList.remove('fa-moon');
        iconElement.classList.add('fa-sun');
        textElement.textContent = 'Light Mode';
    } else {
        iconElement.classList.remove('fa-sun');
        iconElement.classList.add('fa-moon');
        textElement.textContent = 'Dark Mode';
    }
};

// Initialize dark mode when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded'); // Debug log
    new DarkMode();
}); 