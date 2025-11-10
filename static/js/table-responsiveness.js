/**
 * Table Responsiveness JavaScript
 * 
 * Provides:
 * - Column visibility toggles with localStorage persistence
 * - Density mode switching (comfortable/compact)
 * - ResizeObserver-based dynamic rows-per-page calculation
 * - Accessibility-compliant interactions
 * 
 * Usage:
 *   TableResponsiveness.initColumnChooser(tableElement, 'workout_plan');
 *   TableResponsiveness.fitRowsToViewport('.tbl-wrap', { onPageSize: (rows) => updatePagination(rows) });
 */

(function () {
  'use strict';

  // ============================================================
  // UTILITY FUNCTIONS
  // ============================================================

  const qs = (selector, root = document) => root.querySelector(selector);
  const qsa = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  const STORAGE_KEY = 'hypertrophy_tbl_prefs';

  /**
   * Get preferences from localStorage
   * @returns {Object} Preferences object
   */
  function getPrefs() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : {};
    } catch (error) {
      console.warn('Failed to parse table preferences from localStorage:', error);
      return {};
    }
  }

  /**
   * Save preferences to localStorage
   * @param {Object} prefs - Preferences to save
   */
  function setPrefs(prefs) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    } catch (error) {
      console.warn('Failed to save table preferences to localStorage:', error);
    }
  }

  /**
   * Debounce function to limit execution rate
   * @param {Function} func - Function to debounce
   * @param {number} wait - Wait time in milliseconds
   * @returns {Function} Debounced function
   */
  function debounce(func, wait = 250) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // ============================================================
  // COLUMN CHOOSER
  // ============================================================

  /**
   * Initialize column chooser for a table
   * @param {HTMLElement} tableEl - Table element
   * @param {string} pageKey - Unique identifier for the page (e.g., 'workout_plan')
   */
  function initColumnChooser(tableEl, pageKey) {
    if (!tableEl || !pageKey) {
      console.warn('initColumnChooser: tableEl and pageKey are required');
      return;
    }

    const wrapper = tableEl.closest('.tbl-wrap');
    if (!wrapper) return;

    // Find or create column chooser UI in the parent container
    let chooserEl = qs('[data-col-chooser]', wrapper.parentElement);

    if (!chooserEl) {
      // Create column chooser UI
      chooserEl = createColumnChooserUI(tableEl, pageKey);
    }

    const menu = qs('[data-col-chooser-menu]', chooserEl);
    if (!menu) return;

    // Load preferences
    const prefs = getPrefs();
    const hiddenCols = new Set(prefs[pageKey]?.hidden || []);

    // Setup checkboxes
    qsa('input[type=checkbox][data-col]', menu).forEach(checkbox => {
      const colClass = checkbox.dataset.col;
      checkbox.checked = !hiddenCols.has(colClass);

      checkbox.addEventListener('change', () => {
        toggleColumn(tableEl, colClass, checkbox.checked, pageKey);
      });

      // Apply initial visibility
      if (!checkbox.checked) {
        applyColumnVisibility(tableEl, colClass, false);
      }
    });

    // Setup trigger button
    const trigger = qs('[data-col-chooser-trigger]', chooserEl);
    if (trigger) {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        menu.classList.toggle('active');
        trigger.setAttribute('aria-expanded', menu.classList.contains('active'));

        // Smart positioning to prevent overflow
        if (menu.classList.contains('active')) {
          positionMenuToAvoidOverflow(trigger, menu);
        }
      });

      // Close menu when clicking outside
      document.addEventListener('click', (e) => {
        if (!chooserEl.contains(e.target)) {
          menu.classList.remove('active');
          trigger.setAttribute('aria-expanded', 'false');
        }
      });

      // Handle escape key
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && menu.classList.contains('active')) {
          menu.classList.remove('active');
          trigger.setAttribute('aria-expanded', 'false');
          trigger.focus();
        }
      });
    }
  }

  /**
   * Position menu to avoid viewport overflow
   * Forces layout and uses ResizeObserver for reliable timing
   * @param {HTMLElement} trigger - Trigger button
   * @param {HTMLElement} menu - Menu element
   */
  function positionMenuToAvoidOverflow(trigger, menu) {
    let hasPositioned = false;

    // Force the browser to apply display: block from CSS
    // by triggering a reflow
    const computedDisplay = window.getComputedStyle(menu).display;

    if (computedDisplay === 'none') {
      console.warn('Menu still has display: none, forcing layout...');
      // This shouldn't happen, but if it does, force it
      menu.style.display = 'block';
    }

    // Use requestAnimationFrame to ensure CSS is applied
    requestAnimationFrame(() => {
      // Use ResizeObserver to position menu when it finishes rendering
      const resizeObserver = new ResizeObserver(() => {
        if (hasPositioned) return; // Only position once
        hasPositioned = true;

        performMenuPositioning(trigger, menu);
        resizeObserver.disconnect();
      });

      // Start observing immediately
      resizeObserver.observe(menu);

      // Fallback: if ResizeObserver doesn't fire, use timeout
      setTimeout(() => {
        if (!hasPositioned) {
          hasPositioned = true;
          performMenuPositioning(trigger, menu);
          resizeObserver.disconnect();
        }
      }, 100);
    });
  }

  /**
   * Perform actual menu positioning calculations
   * @param {HTMLElement} trigger - Trigger button
   * @param {HTMLElement} menu - Menu element
   */
  function performMenuPositioning(trigger, menu) {
    const triggerRect = trigger.getBoundingClientRect();
    const menuRect = menu.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const padding = 10; // Keep 10px away from viewport edges

    // Validate that menu has rendered with actual dimensions
    if (menuRect.height === 0 || menuRect.width === 0) {
      console.warn('Menu has zero dimensions, deferring positioning');
      setTimeout(() => performMenuPositioning(trigger, menu), 50);
      return;
    }

    // Calculate available space
    const spaceBelow = viewportHeight - triggerRect.bottom - padding;
    const spaceAbove = triggerRect.top - padding;
    const menuHeight = menuRect.height;

    console.log('Menu positioning:', {
      menuHeight,
      spaceAbove,
      spaceBelow,
      triggerTop: triggerRect.top,
      triggerBottom: triggerRect.bottom,
      viewportHeight
    });

    // Switch to fixed positioning to avoid being clipped by parent overflow
    menu.style.position = 'fixed';

    // Vertical positioning - calculate fixed position relative to viewport
    let fixedTop;
    if (spaceBelow < menuHeight && spaceAbove > menuHeight) {
      // Position ABOVE the trigger
      fixedTop = triggerRect.top - menuHeight - 10;
      menu.setAttribute('data-menu-position', 'above');
      console.log('Positioning menu ABOVE trigger at fixedTop:', fixedTop);
    } else {
      // Position BELOW the trigger (default)
      fixedTop = triggerRect.bottom + 10;
      menu.setAttribute('data-menu-position', 'below');
      console.log('Positioning menu BELOW trigger at fixedTop:', fixedTop);
    }

    // Horizontal positioning - align left but check for right edge
    let fixedLeft = triggerRect.left;

    if (fixedLeft + 280 > viewportWidth - padding) {
      // Align to right if it would overflow
      fixedLeft = triggerRect.right - 280;
      console.log('Aligning menu to right at fixedLeft:', fixedLeft);
    } else {
      console.log('Aligning menu to left at fixedLeft:', fixedLeft);
    }

    // Apply fixed positioning with calculated pixel values
    menu.style.top = Math.max(padding, fixedTop) + 'px';
    menu.style.left = Math.max(padding, fixedLeft) + 'px';
    menu.style.bottom = 'auto';
    menu.style.right = 'auto';
  }

  /**
   * Create column chooser UI if it doesn't exist
   * @param {HTMLElement} tableEl - Table element
   * @param {string} pageKey - Page identifier
   * @returns {HTMLElement} Chooser element
   */
  function createColumnChooserUI(tableEl, pageKey) {
    const wrapper = tableEl.closest('.tbl-wrap');
    if (!wrapper) return null;

    // Create controls container
    const controls = document.createElement('div');
    controls.className = 'tbl-controls';
    controls.setAttribute('data-col-chooser', '');

    // Create trigger button
    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'tbl-col-chooser-trigger';
    trigger.setAttribute('data-col-chooser-trigger', '');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-haspopup', 'true');
    trigger.innerHTML = '<i class="fas fa-columns" aria-hidden="true"></i> Columns';

    // Create menu
    const menu = document.createElement('div');
    menu.className = 'tbl-col-chooser-menu';
    menu.setAttribute('data-col-chooser-menu', '');
    menu.setAttribute('role', 'menu');

    // Find columns with priority classes
    const columns = [];
    qsa('th[class*="col--"]', tableEl).forEach(th => {
      const classList = Array.from(th.classList);
      const priorityClass = classList.find(c => c.startsWith('col--'));
      if (priorityClass && th.textContent.trim()) {
        columns.push({
          class: priorityClass,
          label: th.textContent.trim(),
          priority: priorityClass.split('--')[1] // 'high', 'med', 'low'
        });
      }
    });

    // Sort by priority (high -> med -> low)
    const priorityOrder = { high: 1, med: 2, low: 3 };
    columns.sort((a, b) => (priorityOrder[a.priority] || 99) - (priorityOrder[b.priority] || 99));

    // Create checkboxes for each column
    columns.forEach(col => {
      const label = document.createElement('label');
      label.setAttribute('role', 'menuitemcheckbox');

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.checked = true;
      checkbox.dataset.col = col.class;
      checkbox.setAttribute('aria-label', `Toggle ${col.label} column`);

      const span = document.createElement('span');
      span.textContent = col.label;

      label.appendChild(checkbox);
      label.appendChild(span);
      menu.appendChild(label);
    });

    // Assemble
    const chooserContainer = document.createElement('div');
    chooserContainer.className = 'tbl-col-chooser';
    chooserContainer.appendChild(trigger);
    chooserContainer.appendChild(menu);

    // Add attributes to controls container if not present
    if (!controls.getAttribute('role')) {
      controls.setAttribute('role', 'toolbar');
      controls.setAttribute('aria-label', 'Table controls');
    }

    controls.appendChild(chooserContainer);

    // Insert before table wrapper if not already in DOM
    if (!controls.parentElement) {
      wrapper.parentElement.insertBefore(controls, wrapper);
    }

    return controls;
  }

  /**
   * Toggle column visibility
   * @param {HTMLElement} tableEl - Table element
   * @param {string} colClass - Column class to toggle
   * @param {boolean} show - Whether to show the column
   * @param {string} pageKey - Page identifier
   */
  function toggleColumn(tableEl, colClass, show, pageKey) {
    applyColumnVisibility(tableEl, colClass, show);

    // Update preferences
    const prefs = getPrefs();
    if (!prefs[pageKey]) {
      prefs[pageKey] = { hidden: [] };
    }

    const hiddenSet = new Set(prefs[pageKey].hidden || []);

    if (show) {
      hiddenSet.delete(colClass);
    } else {
      hiddenSet.add(colClass);
    }

    prefs[pageKey].hidden = Array.from(hiddenSet);
    setPrefs(prefs);
  }

  /**
   * Apply column visibility to table
   * @param {HTMLElement} tableEl - Table element
   * @param {string} colClass - Column class
   * @param {boolean} show - Whether to show the column
   */
  function applyColumnVisibility(tableEl, colClass, show) {
    const cells = qsa(`.${colClass}`, tableEl);
    cells.forEach(cell => {
      cell.style.display = show ? '' : 'none';
    });
  }

  // ============================================================
  // DENSITY TOGGLE
  // ============================================================

  /**
   * Initialize density toggle for a table
   * @param {HTMLElement} tableEl - Table element
   * @param {string} pageKey - Page identifier
   */
  function initDensityToggle(tableEl, pageKey) {
    if (!tableEl || !pageKey) return;

    const wrapper = tableEl.closest('.tbl-wrap');
    if (!wrapper) return;

    // Find or create density toggle - look in parent for existing controls
    let toggleBtn = qs('[data-density-toggle]', wrapper.parentElement);

    if (!toggleBtn) {
      toggleBtn = createDensityToggle(tableEl, pageKey);
    }

    if (!toggleBtn) return;

    // Load preference
    const prefs = getPrefs();
    const density = prefs[pageKey]?.density || 'comfortable';
    applyDensity(tableEl, density);

    // Remove any existing click listeners by cloning
    const newBtn = toggleBtn.cloneNode(true);
    toggleBtn.parentElement.replaceChild(newBtn, toggleBtn);
    toggleBtn = newBtn;

    // Setup toggle with fresh listener
    toggleBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();

      const currentDensity = tableEl.classList.contains('tbl--compact') ? 'compact' : 'comfortable';
      const newDensity = currentDensity === 'comfortable' ? 'compact' : 'comfortable';

      applyDensity(tableEl, newDensity);

      // Save preference
      const prefs = getPrefs();
      if (!prefs[pageKey]) {
        prefs[pageKey] = {};
      }
      prefs[pageKey].density = newDensity;
      setPrefs(prefs);

      // Update button text
      updateDensityButtonText(toggleBtn, newDensity);
    });

    // Set initial button text
    updateDensityButtonText(toggleBtn, density);
  }

  /**
   * Create density toggle button
   * @param {HTMLElement} tableEl - Table element
   * @param {string} pageKey - Page identifier
   * @returns {HTMLElement} Toggle button
   */
  function createDensityToggle(tableEl, pageKey) {
    const wrapper = tableEl.closest('.tbl-wrap');
    if (!wrapper || !wrapper.parentElement) return null;

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'tbl-density-toggle';
    button.setAttribute('data-density-toggle', '');
    button.setAttribute('aria-label', 'Toggle table density');
    button.setAttribute('title', 'Toggle between comfortable and compact density');
    button.innerHTML = '<i class="fas fa-compress-arrows-alt" aria-hidden="true"></i> <span class="density-text">Comfortable</span>';

    // Find or reuse existing controls container
    let controls = qs('.tbl-controls', wrapper.parentElement);
    if (!controls) {
      controls = document.createElement('div');
      controls.className = 'tbl-controls';
      controls.setAttribute('role', 'toolbar');
      controls.setAttribute('aria-label', 'Table controls');
      wrapper.parentElement.insertBefore(controls, wrapper);
    }

    controls.appendChild(button);
    return button;
  }

  /**
   * Apply density mode to table
   * @param {HTMLElement} tableEl - Table element
   * @param {string} density - 'comfortable' or 'compact'
   */
  function applyDensity(tableEl, density) {
    if (density === 'compact') {
      tableEl.classList.add('tbl--compact');
    } else {
      tableEl.classList.remove('tbl--compact');
    }
  }

  /**
   * Update density button text
   * @param {HTMLElement} button - Button element
   * @param {string} density - Current density
   */
  function updateDensityButtonText(button, density) {
    const textSpan = qs('.density-text', button);
    if (textSpan) {
      textSpan.textContent = density === 'comfortable' ? 'Comfortable' : 'Compact';
    }
    button.setAttribute('aria-label', `Switch to ${density === 'comfortable' ? 'compact' : 'comfortable'} density`);
  }

  // ============================================================
  // DYNAMIC ROWS PER PAGE (ResizeObserver)
  // ============================================================

  /**
   * Automatically calculate optimal rows per page based on container height
   * @param {string|HTMLElement} containerSel - Container selector or element
   * @param {Object} opts - Options
   * @param {string} opts.headerSel - Header selector
   * @param {string} opts.toolbarSel - Toolbar selector
   * @param {string} opts.footerSel - Footer selector
   * @param {string} opts.rowSel - Row selector
   * @param {number} opts.rowHeight - Approximate row height in pixels
   * @param {number} opts.minRows - Minimum rows to show
   * @param {number} opts.maxRows - Maximum rows to show
   * @param {Function} opts.onPageSize - Callback when page size changes
   */
  function fitRowsToViewport(containerSel, opts = {}) {
    const {
      headerSel = '[data-tbl-header]',
      toolbarSel = '[data-tbl-toolbar]',
      footerSel = '[data-tbl-footer]',
      rowSel = 'tbody tr',
      rowHeight = 42,
      minRows = 10,
      maxRows = 100,
      onPageSize = null
    } = opts;

    const container = typeof containerSel === 'string' ? qs(containerSel) : containerSel;
    if (!container) {
      console.warn('fitRowsToViewport: container not found');
      return;
    }

    const calculatePageSize = debounce(() => {
      const containerHeight = container.clientHeight || container.offsetHeight;

      // Calculate fixed heights
      const headerEl = qs(headerSel, container);
      const toolbarEl = qs(toolbarSel, container);
      const footerEl = qs(footerSel, container);

      const headerHeight = headerEl?.offsetHeight || 0;
      const toolbarHeight = toolbarEl?.offsetHeight || 0;
      const footerHeight = footerEl?.offsetHeight || 0;

      // Calculate available height
      const availableHeight = containerHeight - headerHeight - toolbarHeight - footerHeight;

      // Calculate rows
      const calculatedRows = Math.floor(availableHeight / rowHeight);
      const optimalRows = Math.max(minRows, Math.min(maxRows, calculatedRows));

      // Call callback
      if (typeof onPageSize === 'function') {
        onPageSize(optimalRows);
      }
    }, 250);

    // Setup ResizeObserver
    const resizeObserver = new ResizeObserver(calculatePageSize);
    resizeObserver.observe(container);

    // Initial calculation
    calculatePageSize();

    // Return cleanup function
    return () => {
      resizeObserver.disconnect();
    };
  }

  // ============================================================
  // AUTO-INITIALIZATION
  // ============================================================

  /**
   * Auto-initialize responsive features on tables with data attributes
   */
  function autoInit() {
    // Find all tables with data-responsive attribute
    qsa('[data-table-responsive]').forEach(table => {
      const pageKey = table.dataset.tableResponsive;
      if (!pageKey) return;

      // Initialize column chooser
      initColumnChooser(table, pageKey);

      // Initialize density toggle
      initDensityToggle(table, pageKey);

      // Initialize dynamic rows (if callback provided)
      const onPageSize = table.dataset.tableOnPageSize;
      if (onPageSize && window[onPageSize]) {
        const wrapper = table.closest('.tbl-wrap');
        if (wrapper) {
          fitRowsToViewport(wrapper, {
            onPageSize: window[onPageSize]
          });
        }
      }
    });
  }

  // Auto-init on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit);
  } else {
    autoInit();
  }

  // ============================================================
  // PUBLIC API
  // ============================================================

  window.TableResponsiveness = {
    initColumnChooser,
    initDensityToggle,
    fitRowsToViewport,
    getPrefs,
    setPrefs,
    autoInit
  };

})();

