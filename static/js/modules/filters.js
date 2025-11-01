import { showToast } from './toast.js';

// Debounce timer for filtering
let filterDebounceTimer = null;

export async function filterExercises() {
    try {
        const filters = {};
        const filterElements = document.querySelectorAll('#filters-form select');
        const exerciseDropdown = document.getElementById("exercise");
        
        filterElements.forEach(select => {
            if (select.value && select.id !== 'exercise') {  // Exclude exercise dropdown from filters
                filters[select.id] = select.value;
            }
        });

        console.log("DEBUG: Collected filters:", filters);

        // If no filters are selected, reload all exercises
        if (Object.keys(filters).length === 0) {
            const response = await fetch("/get_all_exercises");
            if (response.ok) {
                const data = await response.json();
                if (exerciseDropdown && Array.isArray(data)) {
                    updateExerciseDropdown(data);
                    showToast(`Showing all ${data.length} exercises`);
                }
            }
            return;
        }

        const response = await fetch("/filter_exercises", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(filters)
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Failed to filter exercises");
        }

        updateExerciseDropdown(data);
        showToast(`Found ${data.length} matching exercise${data.length !== 1 ? 's' : ''}`);
    } catch (error) {
        console.error("Error filtering exercises:", error);
        showToast("Failed to filter exercises", true);
    }
}

// Debounced version of filterExercises to avoid too many API calls
function debouncedFilterExercises() {
    // Clear existing timer
    if (filterDebounceTimer) {
        clearTimeout(filterDebounceTimer);
    }
    
    // Set new timer (300ms debounce)
    filterDebounceTimer = setTimeout(() => {
        filterExercises();
    }, 300);
}

export function initializeFilters() {
    // Add auto-filtering on change for all filter dropdowns
    // Use event delegation to catch changes from both native selects and enhanced dropdowns
    const workoutContainer = document.getElementById('workout');
    if (workoutContainer) {
        workoutContainer.addEventListener('change', function(event) {
            const select = event.target;
            
            // Only process filter dropdowns (not exercise dropdown or routine dropdown)
            // Check if it's a select element in the filters form
            if (select.tagName === 'SELECT' && 
                select.closest('#filters-form') && 
                select.classList.contains('filter-dropdown') &&
                select.id !== 'exercise') {
                
                // Update visual feedback
                if (select.value) {
                    select.style.backgroundColor = '#fff';
                } else {
                    select.style.backgroundColor = '#e3f2fd';
                }
                
                // Auto-filter with debounce
                debouncedFilterExercises();
            }
        });
    }

    // Add clear filters button event listener
    const clearFiltersBtn = document.getElementById('clear-filters-btn');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearFilters);
    }

    // Initialize filter form submit handler
    const filterForm = document.getElementById('filters-form');
    if (filterForm) {
        filterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            // Clear debounce and filter immediately
            if (filterDebounceTimer) {
                clearTimeout(filterDebounceTimer);
            }
            filterExercises();
        });
    }
}

async function clearFilters() {
    // Get all select dropdowns in the filters form
    const allSelects = document.querySelectorAll('#filters-form select');
    
    // Reset each dropdown to empty/default value and trigger change event
    allSelects.forEach(select => {
        select.value = '';
        // Manually dispatch change event to ensure enhanced dropdowns update
        select.dispatchEvent(new Event('change', { bubbles: true }));
    });
    
    // Reset routine dropdown if it exists
    const routineDropdown = document.getElementById('routine');
    if (routineDropdown) {
        routineDropdown.value = '';
        routineDropdown.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    // Reset exercise dropdown if it exists
    const exerciseDropdown = document.getElementById('exercise');
    if (exerciseDropdown) {
        exerciseDropdown.value = '';
        exerciseDropdown.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    // Reload all exercises in the exercise dropdown
    try {
        const response = await fetch("/get_all_exercises");
        if (response.ok) {
            const data = await response.json();
            if (exerciseDropdown && Array.isArray(data)) {
                // Clear existing options
                exerciseDropdown.innerHTML = '<option value="">Select Exercise</option>';
                
                // Add all exercises
                data.forEach(exercise => {
                    if (exercise) {
                        const option = document.createElement("option");
                        option.value = exercise;
                        option.textContent = exercise;
                        exerciseDropdown.appendChild(option);
                    }
                });
                
                // Remove filter-applied class if it exists
                exerciseDropdown.classList.remove('filter-applied', 'filtered');
                
                // Trigger rebuild event for enhanced dropdown
                exerciseDropdown.dispatchEvent(new CustomEvent('wpdd-rebuild', { bubbles: true }));
            }
        }
    } catch (error) {
        console.error("Error reloading exercises:", error);
    }
    
    // Show success toast notification
    showToast('Filters cleared successfully');
}

function updateExerciseDropdown(exercises) {
    const exerciseDropdown = document.getElementById("exercise");
    if (!exerciseDropdown) return;

    exerciseDropdown.innerHTML = '<option value="">Select Exercise</option>';
    
    exercises.forEach(exercise => {
        const option = document.createElement("option");
        option.value = exercise;
        option.textContent = exercise;
        exerciseDropdown.appendChild(option);
    });

    // Trigger rebuild of enhanced dropdown if it exists
    const enhancedContainer = exerciseDropdown.closest('.wpdd');
    if (enhancedContainer) {
        // Dispatch a custom event to trigger rebuild
        const rebuildEvent = new CustomEvent('wpdd-rebuild', { bubbles: true });
        exerciseDropdown.dispatchEvent(rebuildEvent);
    }

    // Add glow effect
    exerciseDropdown.classList.add('filter-applied');
    
    // Remove glow effect after 2 seconds
    setTimeout(() => {
        exerciseDropdown.classList.remove('filter-applied');
    }, 2000);
}

export function initializeAdvancedFilters() {
    const advancedFilters = document.querySelectorAll('.advanced-filter');
    advancedFilters.forEach(filter => {
        filter.addEventListener('change', () => {
            const category = filter.dataset.category;
            const value = filter.value;
            updateFilteredView(category, value);
        });
    });
}

export function updateFilteredView(category, value) {
    const rows = document.querySelectorAll('tr[data-category]');
    rows.forEach(row => {
        if (!value || row.dataset.category === value) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

export function initializeSearchFilter() {
    const searchInput = document.getElementById('search-filter');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
}

// Add keyboard event handling for filters
export function initializeFilterKeyboardEvents() {
    const filterInputs = document.querySelectorAll('#filters-form select, #filters-form input');
    filterInputs.forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                filterExercises();
            }
        });
    });
}
