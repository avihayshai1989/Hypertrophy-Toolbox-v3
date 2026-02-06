import { createVolumeChart, createProgressChart } from './charts.js';
import { fetchWeeklySummary, fetchSessionSummary } from './summary.js';
import { handleDateChange } from './workout-log.js';

export function initializeUIHandlers() {
    // Handle editable fields
    document.querySelectorAll('.editable').forEach(cell => {
        cell.addEventListener('click', function(e) {
            // Don't trigger if clicking on the input
            if (e.target.classList.contains('editable-input')) {
                return;
            }
            
            const input = this.querySelector('.editable-input');
            const text = this.querySelector('.editable-text');
            
            if (input) {
                text.style.display = 'none';
                input.style.display = 'block';
                input.focus();
                
                // For date inputs, open the picker immediately
                if (input.type === 'date' && typeof input.showPicker === 'function') {
                    try {
                        input.showPicker();
                    } catch (err) {
                        // Silently fail if not supported
                    }
                }
            }
        });
    });
    
    // Initialize date input change handlers
    document.querySelectorAll('.date-editable .date-input').forEach(input => {
        input.addEventListener('change', function() {
            const logId = this.dataset.logId;
            if (logId) {
                handleDateChange({ target: this }, logId);
            }
        });
    });

    // Handle clicking outside editable fields
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.editable') && !e.target.classList.contains('editable-input')) {
            document.querySelectorAll('.editable-input').forEach(input => {
                input.style.display = 'none';
            });
            document.querySelectorAll('.editable-text').forEach(text => {
                // Use flex for date displays, block for others
                text.style.display = text.classList.contains('date-display') ? 'flex' : 'block';
            });
        }
    });

    // Handle routine dropdown click state
    const routineDropdown = document.querySelector('.routine-dropdown');
    if (routineDropdown) {
        routineDropdown.addEventListener('click', function() {
            this.classList.add('clicked');
        });

        // Reset background when clicking outside
        document.addEventListener('click', function(event) {
            if (!routineDropdown.contains(event.target)) {
                routineDropdown.classList.remove('clicked');
            }
        });
    }

    initializeSummaryMethodHandlers();

    // Add validation for editable inputs (excluding date inputs which have their own handler)
    document.querySelectorAll('.editable-input:not(.date-input)').forEach(input => {
        input.addEventListener('input', function() {
            const field = this.closest('[data-field]')?.dataset?.field;
            if (field) {
                const isValid = validateScoredValue(this.value, field);
                this.classList.toggle('is-invalid', !isValid);
                this.classList.toggle('is-valid', isValid);
            }
        });
        
        // Auto-save and close on blur (when focus leaves the input)
        input.addEventListener('blur', function() {
            // Small delay to allow click events to process first
            setTimeout(() => {
                const cell = this.closest('.editable');
                if (cell) {
                    const text = cell.querySelector('.editable-text');
                    if (text) {
                        // Use flex for date displays, block for others
                        text.style.display = text.classList.contains('date-display') ? 'flex' : 'block';
                    }
                    this.style.display = 'none';
                }
            }, 100);
        });
        
        // Add Enter key support to submit and close the input
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                // Trigger change event and blur to close the input
                this.dispatchEvent(new Event('change', { bubbles: true }));
                this.blur();
            } else if (e.key === 'Escape') {
                // Cancel editing on Escape - revert to original value
                e.preventDefault();
                const cell = this.closest('.editable');
                if (cell) {
                    const text = cell.querySelector('.editable-text');
                    // Reset input value to original text (don't save)
                    if (text && text.textContent.trim() !== 'Click to set' && 
                        text.textContent.trim() !== 'Click to set date' &&
                        text.textContent.trim() !== 'Click to edit') {
                        this.value = text.textContent.trim();
                    }
                }
                this.blur();
            }
        });
    });
}

export function initializeFormHandlers() {
    // Add Exercise button handler
    const addExerciseBtn = document.getElementById('add-exercise-btn');
    if (addExerciseBtn) {
        addExerciseBtn.addEventListener('click', () => {
            console.log('Add Exercise button clicked');
            // The actual addExercise function will be imported where needed
        });
    }

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

export function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

export function initializeDropdowns() {
    // Initialize all dropdowns
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    dropdowns.forEach(dropdown => {
        new bootstrap.Dropdown(dropdown);
    });
}

export function handleTableSort() {
    document.querySelectorAll('th[data-sort]').forEach(header => {
        header.addEventListener('click', () => {
            const table = header.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const column = header.dataset.sort;
            const ascending = header.classList.toggle('sort-asc');

            const sortedRows = rows.sort((a, b) => {
                const aValue = a.querySelector(`td[data-${column}]`)?.textContent;
                const bValue = b.querySelector(`td[data-${column}]`)?.textContent;
                return ascending ? 
                    aValue.localeCompare(bValue) : 
                    bValue.localeCompare(aValue);
            });

            tbody.innerHTML = '';
            sortedRows.forEach(row => tbody.appendChild(row));
        });
    });
}

export function initializeDataTables() {
    // DataTables removed - using native table sorting instead
    // If you need advanced table features, consider a lightweight vanilla JS alternative
    const tables = document.querySelectorAll('.data-table');
    tables.forEach(table => {
        initializeTableSorting(table);
    });
}

function initializeTableSorting(table) {
    const headers = table.querySelectorAll('th[data-sortable]');
    headers.forEach((header, index) => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => {
            sortTable(table, index);
        });
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const header = table.querySelectorAll('th')[columnIndex];
    const isAscending = header.classList.contains('sort-asc');
    
    // Remove sort classes from all headers
    table.querySelectorAll('th').forEach(h => {
        h.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add appropriate sort class
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as number
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? bNum - aNum : aNum - bNum;
        }
        
        // String comparison
        return isAscending ? 
            bValue.localeCompare(aValue) : 
            aValue.localeCompare(bValue);
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

export function initializeCharts() {
    const chartContainers = document.querySelectorAll('[data-chart]');
    chartContainers.forEach(container => {
        const chartType = container.dataset.chart;
        const chartData = JSON.parse(container.dataset.chartData || '{}');
        
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);
        
        switch (chartType) {
            case 'volume':
                createVolumeChart(canvas, chartData);
                break;
            case 'progress':
                createProgressChart(canvas, chartData);
                break;
        }
    });
}

export function initializeSummaryMethodHandlers() {
    const methodSelect = document.getElementById('summary-method');
    if (!methodSelect) return;

    methodSelect.addEventListener('change', (e) => {
        const method = e.target.value;
        const currentPath = window.location.pathname;
        
        if (currentPath === '/weekly_summary') {
            fetchWeeklySummary(method);
        } else if (currentPath === '/session_summary') {
            fetchSessionSummary(method);
        }
    });
}

function initializeSuggestionCards() {
    document.querySelectorAll('.suggestion-card').forEach(card => {
        const toggle = card.querySelector('.expand-toggle');
        if (toggle) {
            toggle.addEventListener('click', () => {
                card.classList.toggle('expanded');
                toggle.textContent = card.classList.contains('expanded') ? 'Show Less' : 'Show More';
            });
        }
    });
}

// Call this function when suggestions are loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeSuggestionCards();
}); 