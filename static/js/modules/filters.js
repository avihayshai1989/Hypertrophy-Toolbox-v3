import { showToast } from './toast.js';

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

        if (Object.keys(filters).length === 0) {
            showToast("Please select at least one filter", true);
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
        showToast(`Found ${data.length} matching exercises`);
    } catch (error) {
        console.error("Error filtering exercises:", error);
        showToast("Failed to filter exercises", true);
    }
}

export function initializeFilters() {
    // Add filter button click handler
    const filterBtn = document.getElementById("filter-btn");
    if (filterBtn) {
        filterBtn.addEventListener("click", filterExercises);
    }

    // Add interaction effects for filter dropdowns
    document.querySelectorAll('.filter-dropdown').forEach(dropdown => {
        dropdown.addEventListener('change', function() {
            if (this.value) {
                this.style.backgroundColor = '#fff';
                filterExercises();
            } else {
                this.style.backgroundColor = '#e3f2fd';
            }
        });
    });

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
            filterExercises();
        });
    }

    // Initialize live search
    initializeLiveSearch();
}

function clearFilters() {
    // Get all filter dropdowns
    const filterDropdowns = document.querySelectorAll('.filter-dropdown');
    
    // Reset each dropdown to default value
    filterDropdowns.forEach(dropdown => {
        dropdown.value = '';
    });
    
    // Reset routine dropdown if it exists
    const routineDropdown = document.getElementById('routine');
    if (routineDropdown) {
        routineDropdown.value = '';
    }
    
    // Reset exercise dropdown if it exists
    const exerciseDropdown = document.getElementById('exercise');
    if (exerciseDropdown) {
        exerciseDropdown.value = '';
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

export function initializeLiveSearch() {
    const searchInput = document.getElementById('exercise-search');
    const exerciseDropdown = document.getElementById('exercise');
    
    if (!searchInput || !exerciseDropdown) return;

    // Store original options for filtering
    const originalOptions = Array.from(exerciseDropdown.options).slice(1); // Skip first "Select Exercise" option
    
    // Add debounce to avoid showing toast too frequently
    let debounceTimer;
    
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        
        // Reset dropdown to only include the first "Select Exercise" option
        exerciseDropdown.innerHTML = exerciseDropdown.options[0].outerHTML;
        
        // Filter and add matching options
        const matchingOptions = originalOptions.filter(option => 
            option.text.toLowerCase().includes(searchTerm)
        );
        
        matchingOptions.forEach(option => {
            exerciseDropdown.appendChild(option.cloneNode(true));
        });
        
        // Visual feedback
        exerciseDropdown.classList.add('filtered');
        setTimeout(() => exerciseDropdown.classList.remove('filtered'), 300);

        // Clear previous timer
        clearTimeout(debounceTimer);
        
        // Set new timer to show toast after user stops typing (500ms delay)
        debounceTimer = setTimeout(() => {
            const matchCount = matchingOptions.length;
            const message = searchTerm 
                ? `Found ${matchCount} matching exercise${matchCount !== 1 ? 's' : ''}`
                : `Showing all ${originalOptions.length} exercises`;
            showToast(message, false);
        }, 500);
    });
} 