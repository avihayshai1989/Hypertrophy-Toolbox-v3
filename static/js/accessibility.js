/**
 * Accessibility Controller
 * Manages UI scaling and other accessibility features
 */

(function() {
    'use strict';

    const STORAGE_KEY = 'ui-scale-level';
    const DEFAULT_SCALE = 6;
    const MIN_SCALE = 1;
    const MAX_SCALE = 8;

    /**
     * AccessibilityController - Manages accessibility features
     */
    function AccessibilityController() {
        this.currentScale = this.loadScale();
        this.init();
    }

    /**
     * Initialize the controller
     */
    AccessibilityController.prototype.init = function() {
        // Sync localStorage to cookie if they differ (ensures server has latest)
        this.syncCookie();
        
        // Setup controls when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupControls());
        } else {
            this.setupControls();
        }
    };

    /**
     * Sync localStorage scale to cookie (server reads cookie for SSR)
     */
    AccessibilityController.prototype.syncCookie = function() {
        const cookieMatch = document.cookie.match(/ui-scale-level=(\d)/);
        const cookieScale = cookieMatch ? parseInt(cookieMatch[1], 10) : null;
        
        if (cookieScale !== this.currentScale) {
            // Cookie doesn't match localStorage, update cookie
            document.cookie = 'ui-scale-level=' + this.currentScale + '; path=/; max-age=31536000; SameSite=Lax';
        }
    };

    /**
     * Load scale from localStorage
     */
    AccessibilityController.prototype.loadScale = function() {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored !== null) {
            const scale = parseInt(stored, 10);
            if (scale >= MIN_SCALE && scale <= MAX_SCALE) {
                return scale;
            }
        }
        return DEFAULT_SCALE;
    };

    /**
     * Save scale to localStorage AND cookie (cookie is read by server)
     */
    AccessibilityController.prototype.saveScale = function(level) {
        localStorage.setItem(STORAGE_KEY, String(level));
        // Set cookie for server-side rendering (expires in 1 year)
        document.cookie = 'ui-scale-level=' + level + '; path=/; max-age=31536000; SameSite=Lax';
    };

    /**
     * Apply scale to the document
     * Updates inline style on html element (matches server-side rendering)
     * Uses zoom for Chrome/Safari/Edge, transform for Firefox
     */
    AccessibilityController.prototype.applyScale = function(level) {
        const zoomValues = { 1: '0.75', 2: '0.8', 3: '0.85', 4: '0.9', 5: '0.95', 6: '1', 7: '1.1', 8: '1.2' };
        const zoomValue = zoomValues[level];
        
        document.documentElement.setAttribute('data-scale', String(level));
        
        // Check if browser supports zoom (Firefox doesn't)
        const supportsZoom = CSS.supports('zoom', '1');
        
        if (supportsZoom) {
            document.documentElement.style.zoom = zoomValue;
        } else {
            // Firefox fallback: use transform scale on body content
            document.documentElement.style.setProperty('--ui-scale', zoomValue);
            // Don't apply transform to html - let CSS handle it via the data-scale attribute
        }
        
        this.currentScale = level;
        this.updateControlsUI();
    };

    /**
     * Set scale level
     */
    AccessibilityController.prototype.setScale = function(level) {
        // Clamp to valid range
        level = Math.max(MIN_SCALE, Math.min(MAX_SCALE, level));
        
        if (level !== this.currentScale) {
            this.applyScale(level);
            this.saveScale(level);
        }
    };

    /**
     * Increase scale by one level
     */
    AccessibilityController.prototype.increaseScale = function() {
        if (this.currentScale < MAX_SCALE) {
            this.setScale(this.currentScale + 1);
        }
    };

    /**
     * Decrease scale by one level
     */
    AccessibilityController.prototype.decreaseScale = function() {
        if (this.currentScale > MIN_SCALE) {
            this.setScale(this.currentScale - 1);
        }
    };

    /**
     * Reset scale to default
     */
    AccessibilityController.prototype.resetScale = function() {
        this.setScale(DEFAULT_SCALE);
    };

    /**
     * Setup UI controls
     */
    AccessibilityController.prototype.setupControls = function() {
        // Setup scale buttons (1-5)
        const scaleButtons = document.querySelectorAll('.scale-btn[data-scale]');
        scaleButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const scale = parseInt(e.currentTarget.dataset.scale, 10);
                this.setScale(scale);
            });
        });

        // Setup increment/decrement buttons
        const decreaseBtn = document.getElementById('scale-decrease');
        const increaseBtn = document.getElementById('scale-increase');
        
        if (decreaseBtn) {
            decreaseBtn.addEventListener('click', () => this.decreaseScale());
        }
        
        if (increaseBtn) {
            increaseBtn.addEventListener('click', () => this.increaseScale());
        }

        // Setup accessibility dropdown toggle
        const accessibilityToggle = document.querySelector('.accessibility-toggle');
        const accessibilityDropdown = document.querySelector('.accessibility-dropdown');
        
        if (accessibilityToggle && accessibilityDropdown) {
            accessibilityToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                accessibilityDropdown.classList.toggle('open');
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!accessibilityDropdown.contains(e.target)) {
                    accessibilityDropdown.classList.remove('open');
                }
            });

            // Close on escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && accessibilityDropdown.classList.contains('open')) {
                    accessibilityDropdown.classList.remove('open');
                    accessibilityToggle.focus();
                }
            });
        }

        // Update UI to reflect current scale
        this.updateControlsUI();

        // Setup keyboard shortcuts (Ctrl/Cmd + +/-)
        this.setupKeyboardShortcuts();
    };

    /**
     * Update all control UIs to reflect current scale
     */
    AccessibilityController.prototype.updateControlsUI = function() {
        // Update scale buttons active state
        const scaleButtons = document.querySelectorAll('.scale-btn[data-scale]');
        scaleButtons.forEach(btn => {
            const btnScale = parseInt(btn.dataset.scale, 10);
            btn.classList.toggle('active', btnScale === this.currentScale);
            btn.setAttribute('aria-pressed', btnScale === this.currentScale ? 'true' : 'false');
        });

        // Update scale indicator
        const scaleIndicator = document.getElementById('scale-indicator');
        if (scaleIndicator) {
            scaleIndicator.textContent = this.currentScale;
        }

        // Update increment/decrement button states
        const decreaseBtn = document.getElementById('scale-decrease');
        const increaseBtn = document.getElementById('scale-increase');
        
        if (decreaseBtn) {
            decreaseBtn.disabled = this.currentScale <= MIN_SCALE;
            decreaseBtn.setAttribute('aria-disabled', this.currentScale <= MIN_SCALE ? 'true' : 'false');
        }
        
        if (increaseBtn) {
            increaseBtn.disabled = this.currentScale >= MAX_SCALE;
            increaseBtn.setAttribute('aria-disabled', this.currentScale >= MAX_SCALE ? 'true' : 'false');
        }
    };

    /**
     * Setup keyboard shortcuts for scaling
     */
    AccessibilityController.prototype.setupKeyboardShortcuts = function() {
        document.addEventListener('keydown', (e) => {
            // Check for Ctrl/Cmd modifier
            const isModifierPressed = e.ctrlKey || e.metaKey;
            
            if (isModifierPressed) {
                // Ctrl/Cmd + Plus (=) to increase
                if (e.key === '=' || e.key === '+') {
                    e.preventDefault();
                    this.increaseScale();
                }
                // Ctrl/Cmd + Minus to decrease
                else if (e.key === '-') {
                    e.preventDefault();
                    this.decreaseScale();
                }
                // Ctrl/Cmd + 0 to reset
                else if (e.key === '0') {
                    e.preventDefault();
                    this.resetScale();
                }
            }
        });
    };

    // Initialize and expose globally
    window.AccessibilityController = AccessibilityController;
    
    // Auto-initialize
    window.accessibilityController = new AccessibilityController();

})();
