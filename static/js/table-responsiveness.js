const TABLE_RESPONSIVENESS_DEBUG = false;
const tableDebugLog = (...args) => {
  if (TABLE_RESPONSIVENESS_DEBUG) {
    console.log(...args);
  }
};
const tableDebugTrace = (...args) => {
  if (TABLE_RESPONSIVENESS_DEBUG) {
    console.trace(...args);
  }
};

tableDebugLog('[TableResponsiveness] Version 2024-11-11-03 loaded');

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

  // Track last time any column chooser menu opened to avoid instant auto-close
  let lastMenuOpenTimestamp = 0;

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

  /**
   * Ensure a shared controls container exists for the responsive table
   * @param {HTMLElement} wrapper - The table wrapper element
   * @returns {HTMLElement|null} Controls container element
   */
  function getOrCreateControlsContainer(wrapper) {
    if (!wrapper) {
      return null;
    }

    // Prefer controls container inside the wrapper so it stays visually tied to the table
    let controls = qs('.tbl-controls', wrapper);

    // If an older container exists on the parent, move it inside the wrapper
    if (!controls && wrapper.parentElement) {
      const parentControls = qs('.tbl-controls', wrapper.parentElement);
      if (parentControls) {
        controls = parentControls;
        wrapper.insertBefore(controls, wrapper.firstChild);
      }
    }

    if (!controls) {
      controls = document.createElement('div');
      controls.className = 'tbl-controls';
      wrapper.insertBefore(controls, wrapper.firstChild);
    }

    if (!controls.getAttribute('role')) {
      controls.setAttribute('role', 'toolbar');
      controls.setAttribute('aria-label', 'Table controls');
    }

    return controls;
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
  tableDebugLog('[initColumnChooser] Starting for pageKey:', pageKey);
    
    if (!tableEl || !pageKey) {
      console.warn('initColumnChooser: tableEl and pageKey are required');
      return;
    }

    const wrapper = tableEl.closest('.tbl-wrap');
    if (!wrapper || !wrapper.parentElement) {
      console.warn('[initColumnChooser] No wrapper found');
      return;
    }

  // Check if already initialized for this specific table
  const existingChooser = qs('.tbl-col-chooser[data-table-key="' + pageKey + '"]', wrapper);
    if (existingChooser) {
  tableDebugLog('[initColumnChooser] Already initialized for', pageKey, '- exiting');
      return; // Already initialized
    }
    
  tableDebugLog('[initColumnChooser] Creating new column chooser for', pageKey);
  tableDebugTrace('[initColumnChooser] Called from:');

    // Create column chooser UI
    const chooserEl = createColumnChooserUI(tableEl, pageKey);
    if (!chooserEl) return;

    // Mark with page key to prevent duplicate initialization
    chooserEl.dataset.tableKey = pageKey;

    const menu = qs('[data-col-chooser-menu]', chooserEl);
    const trigger = qs('[data-col-chooser-trigger]', chooserEl);
    if (!menu || !trigger) return;

    // Load preferences
    const prefs = getPrefs();
    const hiddenCols = new Set(prefs[pageKey]?.hidden || []);

    // Setup checkboxes
    qsa('input[type=checkbox][data-col]', menu).forEach(checkbox => {
      const colIdentifier = checkbox.dataset.col; // Now stores data-label value
      checkbox.checked = !hiddenCols.has(colIdentifier);
  tableDebugLog('[Checkbox Setup] Column:', colIdentifier, 'Checked:', checkbox.checked);

      checkbox.addEventListener('change', () => {
  tableDebugLog('[Checkbox Change] Column:', colIdentifier, 'New state:', checkbox.checked);
        toggleColumn(tableEl, colIdentifier, checkbox.checked, pageKey);
      });

      // Apply initial visibility
      if (!checkbox.checked) {
        applyColumnVisibility(tableEl, colIdentifier, false);
      }
    });

    // Setup trigger button click handler - no need to check for duplicate since
    // initColumnChooser already prevents duplicate initialization
  tableDebugLog('[initColumnChooser] Attaching click listener to trigger:', trigger);
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const isActive = menu.classList.contains('active');
  tableDebugLog('[Columns Button] Clicked, isActive:', isActive, 'trigger element:', trigger);
      
      if (isActive) {
        // Close menu
  tableDebugLog('[Columns Button] Closing menu');
        menu.classList.remove('active');
        trigger.setAttribute('aria-expanded', 'false');
        // Reset positioning when closed
        menu.style.position = '';
        menu.style.top = '';
        menu.style.left = '';
        menu.style.right = '';
        menu.style.bottom = '';
        menu.style.width = '';
      } else {
        // Open menu
  tableDebugLog('[Columns Button] Opening menu');
        lastMenuOpenTimestamp = Date.now();
        menu.classList.add('active');
        trigger.setAttribute('aria-expanded', 'true');
        positionMenuToAvoidOverflow(trigger, menu);
      }
    });

    // Set up global event handlers only once
    if (!window._tblControlsGlobalHandlersSet) {
      window._tblControlsGlobalHandlersSet = true;
      
      // Close menu when clicking outside
      document.addEventListener('click', (e) => {
        // Use setTimeout to allow the trigger button's click handler to run first
        setTimeout(() => {
          const allMenus = qsa('.tbl-col-chooser-menu.active');
          allMenus.forEach(activeMenu => {
            const chooser = activeMenu.closest('[data-col-chooser]');
            const trigger = chooser ? qs('[data-col-chooser-trigger]', chooser) : null;
            
            // Close if clicking outside the chooser AND not clicking the trigger
            if (chooser && !chooser.contains(e.target)) {
              tableDebugLog('[Global Click] Closing menu - clicked outside');
              activeMenu.classList.remove('active');
              if (trigger) {
                trigger.setAttribute('aria-expanded', 'false');
              }
              // Reset positioning
              activeMenu.style.position = '';
              activeMenu.style.top = '';
              activeMenu.style.left = '';
              activeMenu.style.right = '';
              activeMenu.style.bottom = '';
              activeMenu.style.width = '';
            }
          });
        }, 0);
      });

      // Close menu when scrolling
      const closeOnScroll = () => {
        if (Date.now() - lastMenuOpenTimestamp < 200) {
          return; // Ignore scroll events fired immediately after opening
        }
        if (qsa('.tbl-col-chooser-menu.active').length) {
          tableDebugLog('[Global Scroll] Closing menu');
        }
        const allMenus = qsa('.tbl-col-chooser-menu.active');
        allMenus.forEach(activeMenu => {
          activeMenu.classList.remove('active');
          const chooser = activeMenu.closest('[data-col-chooser]');
          if (chooser) {
            const menuTrigger = qs('[data-col-chooser-trigger]', chooser);
            if (menuTrigger) {
              menuTrigger.setAttribute('aria-expanded', 'false');
            }
          }
          // Reset positioning
          activeMenu.style.position = '';
          activeMenu.style.top = '';
          activeMenu.style.left = '';
          activeMenu.style.right = '';
          activeMenu.style.bottom = '';
          activeMenu.style.width = '';
        });
      };
      
      window.addEventListener('scroll', closeOnScroll, { passive: true });

      // Handle escape key
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          tableDebugLog('[Global Keydown] Escape pressed, closing menus');
          const allMenus = qsa('.tbl-col-chooser-menu.active');
          allMenus.forEach(activeMenu => {
            activeMenu.classList.remove('active');
            const chooser = activeMenu.closest('[data-col-chooser]');
            if (chooser) {
              const menuTrigger = qs('[data-col-chooser-trigger]', chooser);
              if (menuTrigger) {
                menuTrigger.setAttribute('aria-expanded', 'false');
                menuTrigger.focus();
              }
            }
            // Reset positioning
            activeMenu.style.position = '';
            activeMenu.style.top = '';
            activeMenu.style.left = '';
            activeMenu.style.right = '';
            activeMenu.style.bottom = '';
            activeMenu.style.width = '';
          });
        }
      });
    }
    
    // Also close on scroll within the table container (per-instance handler)
    const tableContainer = trigger.closest('.tbl-wrap');
    if (tableContainer && !tableContainer.dataset.scrollHandlerSet) {
      tableContainer.dataset.scrollHandlerSet = 'true';
      tableContainer.addEventListener('scroll', () => {
        if (Date.now() - lastMenuOpenTimestamp < 200) {
          return;
        }
        if (menu.classList.contains('active')) {
          tableDebugLog('[Table Scroll] Closing menu');
          menu.classList.remove('active');
          trigger.setAttribute('aria-expanded', 'false');
          // Reset positioning
          menu.style.position = '';
          menu.style.top = '';
          menu.style.left = '';
          menu.style.right = '';
          menu.style.bottom = '';
          menu.style.width = '';
        }
      }, { passive: true });
    }
  }

  /**
   * Position menu to avoid viewport overflow
   * Uses fixed positioning to avoid being clipped by parent overflow containers
   * @param {HTMLElement} trigger - Trigger button
   * @param {HTMLElement} menu - Menu element
   */
  function positionMenuToAvoidOverflow(trigger, menu) {
    // Use requestAnimationFrame to get accurate measurements after menu is visible
    requestAnimationFrame(() => {
      const triggerRect = trigger.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const padding = 10;
      
      // Estimate menu height (it should be visible now with visibility:visible)
      // Force a layout to get dimensions
      const menuHeight = menu.offsetHeight || 400; // fallback to max-height
      const menuWidth = 280; // max-width from CSS

      // Calculate available space
      const spaceBelow = viewportHeight - triggerRect.bottom - padding;
      const spaceAbove = triggerRect.top - padding;

      // Use fixed positioning to escape parent overflow clipping
      menu.style.position = 'fixed';
      menu.style.width = menuWidth + 'px';

      // Vertical positioning - prefer below, only go above if necessary
      if (spaceBelow < menuHeight && spaceAbove > spaceBelow && spaceAbove > menuHeight) {
        // Position ABOVE the trigger
        menu.style.top = 'auto';
        menu.style.bottom = (viewportHeight - triggerRect.top + 10) + 'px';
      } else {
        // Position BELOW the trigger (default and preferred)
        menu.style.top = (triggerRect.bottom + 10) + 'px';
        menu.style.bottom = 'auto';
      }

      // Horizontal positioning
      const idealLeft = triggerRect.left;
      
      if (idealLeft + menuWidth > viewportWidth - padding) {
        // Align to right edge of trigger
        menu.style.left = 'auto';
        menu.style.right = (viewportWidth - triggerRect.right) + 'px';
      } else {
        // Align to left edge of trigger
        menu.style.left = idealLeft + 'px';
        menu.style.right = 'auto';
      }
    });
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

    const controls = getOrCreateControlsContainer(wrapper);
    if (!controls) return null;

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

    // Find all columns with data-label attributes (each column individually)
    const columns = [];
    qsa('th[data-label]', tableEl).forEach((th, index) => {
      const dataLabel = th.getAttribute('data-label');
      const classList = Array.from(th.classList);
      const priorityClass = classList.find(c => c.startsWith('col--'));
      
      if (dataLabel && priorityClass) {
        columns.push({
          dataLabel: dataLabel,
          label: dataLabel, // Use data-label as display text
          priority: priorityClass.split('--')[1], // 'high', 'med', 'low'
          index: index // Keep track of column index for uniqueness
        });
      }
    });

  tableDebugLog('[createColumnChooserUI] Found columns:', columns.map(c => ({ label: c.label, priority: c.priority, index: c.index })));

    // Sort by priority (high -> med -> low) then by index
    const priorityOrder = { high: 1, med: 2, low: 3 };
    columns.sort((a, b) => {
      const priorityDiff = (priorityOrder[a.priority] || 99) - (priorityOrder[b.priority] || 99);
      return priorityDiff !== 0 ? priorityDiff : a.index - b.index;
    });

    // Create checkboxes for each column
    columns.forEach(col => {
      const label = document.createElement('label');
      label.setAttribute('role', 'menuitemcheckbox');

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.checked = true;
      checkbox.dataset.col = col.dataLabel; // Use data-label as identifier
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
    chooserContainer.setAttribute('data-col-chooser', '');
    chooserContainer.appendChild(trigger);
    chooserContainer.appendChild(menu);

    controls.appendChild(chooserContainer);
    return chooserContainer;
  }

  /**
   * Toggle column visibility
   * @param {HTMLElement} tableEl - Table element
   * @param {string} colIdentifier - Column identifier (data-label value)
   * @param {boolean} show - Whether to show the column
   * @param {string} pageKey - Page identifier
   */
  function toggleColumn(tableEl, colIdentifier, show, pageKey) {
  tableDebugLog('[toggleColumn] Called with:', { colIdentifier, show, pageKey });
    applyColumnVisibility(tableEl, colIdentifier, show);

    // Update preferences
    const prefs = getPrefs();
    if (!prefs[pageKey]) {
      prefs[pageKey] = { hidden: [] };
    }

    const hiddenSet = new Set(prefs[pageKey].hidden || []);

    if (show) {
      hiddenSet.delete(colIdentifier);
    } else {
      hiddenSet.add(colIdentifier);
    }

    prefs[pageKey].hidden = Array.from(hiddenSet);
  tableDebugLog('[toggleColumn] Updated hidden columns:', prefs[pageKey].hidden);
    setPrefs(prefs);
  }

  /**
   * Apply column visibility to table
   * @param {HTMLElement} tableEl - Table element
   * @param {string} colIdentifier - Column identifier (data-label value)
   * @param {boolean} show - Whether to show the column
   */
  function applyColumnVisibility(tableEl, colIdentifier, show) {
  tableDebugLog('[applyColumnVisibility] Called with:', { colIdentifier, show });
    
    // Find the column index by matching the data-label in the header
    const headers = qsa('th[data-label]', tableEl);
    let columnIndex = -1;
    
    headers.forEach((th, index) => {
      if (th.getAttribute('data-label') === colIdentifier) {
        columnIndex = index;
  tableDebugLog('[applyColumnVisibility] Found column at index:', index, 'Header text:', th.textContent.trim());
      }
    });
    
    if (columnIndex === -1) {
      console.warn(`[applyColumnVisibility] Column with data-label "${colIdentifier}" not found`);
      return;
    }
    
    // Hide/show the header cell
    const header = headers[columnIndex];
    if (header) {
      header.style.display = show ? '' : 'none';
  tableDebugLog('[applyColumnVisibility] Header display set to:', header.style.display || 'default');
    }
    
    // Hide/show all corresponding body cells using nth-child selector
    // Note: nth-child is 1-indexed, and we need to account for the drag handle column
    const nthChildIndex = columnIndex + 2; // +1 for nth-child indexing, +1 for drag handle
  tableDebugLog('[applyColumnVisibility] Using nth-child selector:', nthChildIndex);
  const bodyCells = qsa(`tbody tr td:nth-child(${nthChildIndex})`, tableEl);
  tableDebugLog('[applyColumnVisibility] Found', bodyCells.length, 'body cells to toggle');
    bodyCells.forEach(cell => {
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

    // Remove existing listeners by replacing with a clone
    // This ensures we don't have duplicate listeners
    const newToggleBtn = toggleBtn.cloneNode(true);
    if (toggleBtn.parentElement) {
      toggleBtn.parentElement.replaceChild(newToggleBtn, toggleBtn);
      toggleBtn = newToggleBtn;
    }

    // Setup toggle with listener
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
  if (!wrapper) return null;

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'tbl-density-toggle';
    button.setAttribute('data-density-toggle', '');
    button.setAttribute('aria-label', 'Toggle table density');
    button.setAttribute('title', 'Toggle between comfortable and compact density');
    button.innerHTML = '<i class="fas fa-compress-arrows-alt" aria-hidden="true"></i> <span class="density-text">Comfortable</span>';

    // Find or reuse existing controls container
    const controls = getOrCreateControlsContainer(wrapper);
    if (!controls) return null;

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
    const tables = qsa('[data-table-responsive]');
    
    tables.forEach(table => {
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

