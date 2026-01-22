import { showToast } from './toast.js';

/**
 * Helper function to handle standardized API responses
 * @param {Response} response - Fetch response object
 * @returns {Promise<Object>} Extracted data or throws error
 */
async function handleApiResponse(response) {
    const data = await response.json();
    
    // Check if response is in standardized format
    if (data.ok === false) {
        const errorMsg = data.error?.message || data.error || 'An error occurred';
        throw new Error(errorMsg);
    }
    
    // If response.ok is true, return the data property, otherwise return the entire object (backward compatibility)
    return data.ok === true ? (data.data !== undefined ? data.data : data) : data;
}

// Module-level state for routine tabs
let currentRoutineTabFilter = 'all';
let allExercisesCache = [];

// Workout plan functionality
export async function fetchWorkoutPlan() {
    try {
        const response = await fetch('/get_workout_plan');
        
        if (!response.ok) {
            throw new Error('Failed to fetch workout plan');
        }

        const exercises = await handleApiResponse(response);
        
        // Cache all exercises for tab filtering
        allExercisesCache = exercises;
        
        // Update routine tabs based on available routines
        updateRoutineTabs(exercises);
        
        // Apply current tab filter and render
        const filteredExercises = applyRoutineTabFilter(exercises, currentRoutineTabFilter);
        updateWorkoutPlanTable(filteredExercises);
        updateWorkoutPlanUI(exercises); // Always show totals for all exercises
        
        // Table responsiveness is already initialized by table-responsiveness.js autoInit
        // No need to reinitialize here
    } catch (error) {
        console.error('Error loading workout plan:', error);
        showToast(error.message || 'Failed to load workout plan', true);
    }
}

/**
 * Updates the routine tabs based on available routines in the data
 * @param {Array} exercises - Array of exercise objects
 */
function updateRoutineTabs(exercises) {
    const tabsContainer = document.getElementById('routine-tabs');
    if (!tabsContainer) return;
    
    // Get unique routines and count exercises per routine
    const routineCounts = {};
    exercises.forEach(ex => {
        const routine = ex.routine || 'Unknown';
        routineCounts[routine] = (routineCounts[routine] || 0) + 1;
    });
    
    // Sort routines alphabetically for consistent ordering
    const sortedRoutines = Object.keys(routineCounts).sort();
    
    // Update "All" tab count
    const allCountEl = document.getElementById('tab-count-all');
    if (allCountEl) {
        allCountEl.textContent = exercises.length;
    }
    
    // Remove existing dynamic tabs (keep the "All" tab)
    const existingDynamicTabs = tabsContainer.querySelectorAll('.routine-tab[data-dynamic="true"]');
    existingDynamicTabs.forEach(tab => tab.remove());
    
    // Create tabs for each routine
    sortedRoutines.forEach(routine => {
        const tabId = `tab-${routine.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase()}`;
        
        const tabLi = document.createElement('li');
        tabLi.className = 'routine-tab';
        tabLi.setAttribute('data-dynamic', 'true');
        tabLi.setAttribute('role', 'presentation');
        
        const tabBtn = document.createElement('button');
        tabBtn.className = 'routine-tab-btn';
        tabBtn.setAttribute('data-routine', routine);
        tabBtn.setAttribute('role', 'tab');
        tabBtn.setAttribute('aria-selected', 'false');
        tabBtn.setAttribute('aria-controls', 'workout_plan_table_body');
        tabBtn.setAttribute('id', tabId);
        
        // Mark as active if this is the currently selected tab
        if (routine === currentRoutineTabFilter) {
            tabBtn.classList.add('active');
            tabBtn.setAttribute('aria-selected', 'true');
            // Also remove active from "All" tab
            const allTab = tabsContainer.querySelector('[data-routine="all"]');
            if (allTab) {
                allTab.classList.remove('active');
                allTab.setAttribute('aria-selected', 'false');
            }
        }
        
        tabBtn.innerHTML = `
            <span class="tab-label">${routine}</span>
            <span class="tab-count">${routineCounts[routine]}</span>
        `;
        
        tabBtn.addEventListener('click', () => handleRoutineTabClick(routine));
        
        tabLi.appendChild(tabBtn);
        tabsContainer.appendChild(tabLi);
    });
    
    // If current filter is "all", ensure the "All" tab is active
    if (currentRoutineTabFilter === 'all') {
        const allTabBtn = tabsContainer.querySelector('[data-routine="all"]');
        if (allTabBtn) {
            allTabBtn.classList.add('active');
            allTabBtn.setAttribute('aria-selected', 'true');
        }
    }
    
    // If the current filter's routine no longer exists, reset to "all"
    if (currentRoutineTabFilter !== 'all' && !sortedRoutines.includes(currentRoutineTabFilter)) {
        currentRoutineTabFilter = 'all';
        const allTabBtn = tabsContainer.querySelector('[data-routine="all"]');
        if (allTabBtn) {
            allTabBtn.classList.add('active');
            allTabBtn.setAttribute('aria-selected', 'true');
        }
    }
}

/**
 * Handles routine tab click events
 * @param {string} routine - The routine name or 'all'
 */
function handleRoutineTabClick(routine) {
    const tabsContainer = document.getElementById('routine-tabs');
    if (!tabsContainer) return;
    
    // Update active state on all tabs
    tabsContainer.querySelectorAll('.routine-tab-btn').forEach(btn => {
        const isTarget = btn.getAttribute('data-routine') === routine;
        btn.classList.toggle('active', isTarget);
        btn.setAttribute('aria-selected', isTarget ? 'true' : 'false');
    });
    
    // Update current filter
    currentRoutineTabFilter = routine;
    
    // Apply filter and re-render table
    const filteredExercises = applyRoutineTabFilter(allExercisesCache, routine);
    updateWorkoutPlanTable(filteredExercises);
}

/**
 * Filters exercises by routine
 * @param {Array} exercises - Array of exercise objects
 * @param {string} routineFilter - The routine to filter by, or 'all'
 * @returns {Array} Filtered exercises
 */
function applyRoutineTabFilter(exercises, routineFilter) {
    if (routineFilter === 'all') {
        return exercises;
    }
    return exercises.filter(ex => ex.routine === routineFilter);
}

/**
 * Gets the current routine tab filter value (for external modules if needed)
 * @returns {string} Current routine filter
 */
export function getCurrentRoutineTabFilter() {
    return currentRoutineTabFilter;
}

/**
 * Resets the routine tab filter to 'all' (for external modules if needed)
 */
export function resetRoutineTabFilter() {
    currentRoutineTabFilter = 'all';
    const tabsContainer = document.getElementById('routine-tabs');
    if (tabsContainer) {
        tabsContainer.querySelectorAll('.routine-tab-btn').forEach(btn => {
            const isAll = btn.getAttribute('data-routine') === 'all';
            btn.classList.toggle('active', isAll);
            btn.setAttribute('aria-selected', isAll ? 'true' : 'false');
        });
    }
}

    const WORKOUT_PLAN_DEBUG = false;
    const workoutPlanDebugLog = (...args) => {
        if (WORKOUT_PLAN_DEBUG) {
            console.log(...args);
        }
    };
export function reloadWorkoutPlan(data) {
    const workoutTable = document.querySelector("#workout-plan-table tbody");
    if (!workoutTable) {
        console.error("Workout plan table not found in the DOM");
        return;
    }

    // Clear existing rows
    workoutTable.innerHTML = "";

    // Add all exercises to the table
    data.forEach((item) => {
        if (!item.id) {
            console.error("Missing ID for exercise:", item);
            return;
        }

        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${item.id}</td>
            <td>${item.routine || "N/A"}</td>
            <td>${item.exercise || "N/A"}</td>
            <td>${item.primary_muscle_group || "N/A"}</td>
            <td>${item.secondary_muscle_group || "N/A"}</td>
            <td>${item.tertiary_muscle_group || "N/A"}</td>
            <td>${item.advanced_isolated_muscles || "N/A"}</td>
            <td>${item.utility || "N/A"}</td>
            <td>${item.sets || "N/A"}</td>
            <td>${item.min_rep_range || "N/A"}</td>
            <td>${item.max_rep_range || "N/A"}</td>
            <td>${item.rir || "N/A"}</td>
            <td>${item.rpe !== null ? item.rpe : "N/A"}</td>
            <td>${item.weight || "N/A"}</td>
            <td>${item.grips || "N/A"}</td>
            <td>${item.stabilizers || "N/A"}</td>
            <td>${item.synergists || "N/A"}</td>
            <td>
                <button class="btn btn-danger btn-sm text-white" onclick="removeExercise(${item.id})">
                    <i class="fas fa-trash"></i> Remove
                </button>
            </td>`;
        workoutTable.appendChild(row);
    });
}

export function updateExerciseDetails(exercise) {
    if (!exercise) return;

    const detailsContainer = document.getElementById('exercise-details');
    if (!detailsContainer) return;

    fetch(`/get_exercise_info/${exercise}`)
        .then(async response => {
            if (!response.ok) {
                throw new Error('Failed to fetch exercise details');
            }
            const data = await handleApiResponse(response);
            
            detailsContainer.innerHTML = `
                <div class="exercise-info">
                    <h5>Exercise Details</h5>
                    <div class="detail-row">
                        <span class="detail-label">Primary Muscle:</span>
                        <span class="detail-value">${data.primary_muscle_group || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Secondary Muscle:</span>
                        <span class="detail-value">${data.secondary_muscle_group || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Equipment:</span>
                        <span class="detail-value">${data.equipment || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Force Type:</span>
                        <span class="detail-value">${data.force || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Level:</span>
                        <span class="detail-value">${data.level || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Mechanic:</span>
                        <span class="detail-value">${data.mechanic || 'N/A'}</span>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error('Error fetching exercise details:', error);
            showToast(error.message || 'Failed to load exercise details', true);
        });
}

export function updateExerciseForm(exercise) {
    if (!exercise) return;

    // Preserve the currently selected routine
    const selectedRoutine = document.getElementById('routine').value;

    // Define default values
    const defaultValues = {
        'sets': '3',
        'min_rep': '6',
        'max_rep_range': '8',
        'rir': '3',
        'weight': '25',  // Default weight is 25
        'rpe': '7'
    };

    // Update form fields based on selected exercise
    fetch(`/get_exercise_info/${exercise}`)
        .then(async response => {
            if (!response.ok) {
                throw new Error('Failed to fetch exercise info');
            }
            const data = await handleApiResponse(response);
            
            // Set values with fallback to defaults
            document.getElementById('sets').value = data.recommended_sets || defaultValues.sets;
            document.getElementById('min_rep').value = data.min_reps || defaultValues.min_rep;
            document.getElementById('max_rep_range').value = data.max_reps || defaultValues.max_rep_range;
            document.getElementById('rir').value = data.recommended_rir || defaultValues.rir;
            document.getElementById('weight').value = data.recommended_weight || defaultValues.weight;
            document.getElementById('rpe').value = data.rpe_based ? (data.recommended_rpe || defaultValues.rpe) : defaultValues.rpe;

            // Restore the selected routine
            if (selectedRoutine) {
                document.getElementById('routine').value = selectedRoutine;
            }
        })
        .catch(error => {
            console.error('Error updating exercise form:', error);
            showToast(error.message || 'Failed to load exercise recommendations', true);
            
            // On error, set default values
            document.getElementById('sets').value = defaultValues.sets;
            document.getElementById('min_rep').value = defaultValues.min_rep;
            document.getElementById('max_rep_range').value = defaultValues.max_rep_range;
            document.getElementById('rir').value = defaultValues.rir;
            document.getElementById('weight').value = defaultValues.weight;
            document.getElementById('rpe').value = defaultValues.rpe;
        });
}

export function handleExerciseSelection() {
    const exerciseSelect = document.getElementById('exercise');
    if (!exerciseSelect) return;

    exerciseSelect.addEventListener('change', (e) => {
        const selectedExercise = e.target.value;
        
        // Clear validation error when user selects a valid value
        if (selectedExercise) {
            setFieldValidationState('exercise', false);
            updateExerciseDetails(selectedExercise);
            // Note: updateExerciseForm is NOT called here to preserve user-entered
            // workout control values (weight, sets, RIR, etc.). The controls are
            // only reset after clicking "Add Exercise" in sendExerciseData().
        }
    });
}

export function handleRoutineSelection() {
    const routineSelect = document.getElementById('routine');
    const exerciseSelect = document.getElementById('exercise');
    if (!routineSelect || !exerciseSelect) return;

    routineSelect.addEventListener('change', async (e) => {
        try {
            const selectedRoutine = e.target.value;
            
            // Clear validation error when user selects a valid routine
            if (selectedRoutine) {
                setFieldValidationState('routine', false);
            }
            
            if (!selectedRoutine) {
                // If routine is cleared, reapply filters (if any) or show all exercises
                const { filterExercises } = await import('./filters.js');
                await filterExercises(true); // Preserve selection when clearing routine
                return;
            }

            // Store the selected routine
            routineSelect.dataset.selectedRoutine = selectedRoutine;

            // Check if there are active filters
            const filters = {};
            const filterElements = document.querySelectorAll('#filters-form select.filter-dropdown');
            filterElements.forEach(select => {
                if (select.value && select.id !== 'exercise' && select.id !== 'routine') {
                    const filterKey = select.dataset.filterKey || select.id;
                    filters[filterKey] = select.value;
                }
            });

            // If there are active filters, apply them to get filtered exercises
            if (Object.keys(filters).length > 0) {
                    workoutPlanDebugLog('DEBUG: Applying filters after routine selection:', filters);
                const { filterExercises } = await import('./filters.js');
                // Preserve the currently selected exercise when reapplying filters
                await filterExercises(true);
            } else {
                // No active filters, fetch exercises for the selected routine
                const response = await fetch(`/get_routine_exercises/${encodeURIComponent(selectedRoutine)}`);
                if (!response.ok) {
                    throw new Error('Failed to fetch exercises for routine');
                }

                const exercises = await handleApiResponse(response);
                
                // Update exercise dropdown and maintain selection if possible
                const currentExercise = exerciseSelect.value;
                updateExerciseDropdown(exercises, currentExercise);
            }

        } catch (error) {
            console.error('Error fetching routine exercises:', error);
            showToast('Failed to load exercises for routine', true);
        }
    });
}

function updateExerciseDropdown(exercises, currentExercise = '') {
    const exerciseDropdown = document.getElementById('exercise');
    if (!exerciseDropdown) return;

    // Store current selection
    const previousValue = currentExercise || exerciseDropdown.value;

    // Clear and rebuild dropdown
    exerciseDropdown.innerHTML = '<option value="">Select Exercise</option>';
    
    if (Array.isArray(exercises)) {
        exercises.forEach(exercise => {
            const option = document.createElement('option');
            option.value = exercise;
            option.textContent = exercise;
            // Restore previous selection if it exists in new options
            if (exercise === previousValue) {
                option.selected = true;
            }
            exerciseDropdown.appendChild(option);
        });
    }

    // Trigger change event if the value changed
    if (exerciseDropdown.value !== previousValue) {
        exerciseDropdown.dispatchEvent(new Event('change'));
    }

    // Add visual feedback
    exerciseDropdown.classList.add('filter-applied');
    setTimeout(() => {
        exerciseDropdown.classList.remove('filter-applied');
    }, 2000);
}

export function updateWorkoutPlanUI(data) {
    // Update summary statistics
    const totalSets = data.reduce((sum, item) => sum + (parseInt(item.sets) || 0), 0);
    const totalExercises = data.length;
    
    const statsContainer = document.getElementById('workout-stats');
    if (statsContainer) {
        statsContainer.innerHTML = `
            <div class="stat-item">
                <h6>Total Exercises</h6>
                <span>${totalExercises}</span>
            </div>
            <div class="stat-item">
                <h6>Total Sets</h6>
                <span>${totalSets}</span>
            </div>
        `;
    }
}

/**
 * Highlights a required field with validation error styling
 * @param {string} fieldId - The ID of the field to highlight
 * @param {boolean} isInvalid - Whether to add or remove the invalid state
 */
function setFieldValidationState(fieldId, isInvalid) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    
    // Find the parent container for label highlighting
    const container = field.closest('.selection-field') || field.closest('.col-lg-6') || field.closest('.col-12');
    
    // Check if there's an enhanced dropdown wrapper
    const wpddContainer = field.closest('.wpdd');
    
    // Check if this is the hidden routine field (for cascade selector)
    const isCascadeRoutine = fieldId === 'routine' && field.type === 'hidden';
    
    if (isInvalid) {
        if (isCascadeRoutine) {
            // For cascade selector, highlight all incomplete dropdowns
            highlightIncompleteCascadeDropdowns();
        } else {
            // Add invalid class to the native select (for non-enhanced state)
            field.classList.add('is-invalid-required');
            
            // Add invalid class to enhanced dropdown container if it exists
            if (wpddContainer) {
                wpddContainer.classList.add('is-invalid-required');
            }
            
            // Highlight the parent container/label
            if (container) {
                container.classList.add('has-validation-error');
            }
        }
    } else {
        if (isCascadeRoutine) {
            // Clear cascade dropdown validation
            clearCascadeDropdownValidation();
        } else {
            // Remove invalid classes
            field.classList.remove('is-invalid-required');
            
            if (wpddContainer) {
                wpddContainer.classList.remove('is-invalid-required');
            }
            
            if (container) {
                container.classList.remove('has-validation-error');
            }
        }
    }
}

/**
 * Highlights incomplete cascade dropdowns
 */
function highlightIncompleteCascadeDropdowns() {
    const envSelect = document.getElementById('routine-env');
    const programSelect = document.getElementById('routine-program');
    const routineSelect = document.getElementById('routine-day');
    
    // Check which dropdowns are incomplete and highlight them
    if (envSelect && !envSelect.value) {
        envSelect.classList.add('is-invalid-required');
        envSelect.closest('.cascade-dropdown-wrapper')?.classList.add('has-validation-error');
        envSelect.focus();
    } else if (programSelect && !programSelect.value) {
        programSelect.classList.add('is-invalid-required');
        programSelect.closest('.cascade-dropdown-wrapper')?.classList.add('has-validation-error');
        programSelect.focus();
    } else if (routineSelect && !routineSelect.value) {
        routineSelect.classList.add('is-invalid-required');
        routineSelect.closest('.cascade-dropdown-wrapper')?.classList.add('has-validation-error');
        routineSelect.focus();
    }
}

/**
 * Clears validation from cascade dropdowns
 */
function clearCascadeDropdownValidation() {
    const cascadeDropdowns = ['routine-env', 'routine-program', 'routine-day'];
    cascadeDropdowns.forEach(id => {
        const dropdown = document.getElementById(id);
        if (dropdown) {
            dropdown.classList.remove('is-invalid-required');
            dropdown.closest('.cascade-dropdown-wrapper')?.classList.remove('has-validation-error');
        }
    });
}

/**
 * Clears validation error highlighting from Routine and Exercise fields
 */
function clearRequiredFieldValidation() {
    setFieldValidationState('routine', false);
    setFieldValidationState('exercise', false);
}

/**
 * Validates required selection fields (Routine and Exercise) and highlights missing ones
 * @returns {boolean} - True if validation passes, false if fields are missing
 */
function validateRequiredSelections() {
    const routineSelect = document.getElementById('routine');
    const exerciseSelect = document.getElementById('exercise');
    
    const routine = routineSelect?.value;
    const exercise = exerciseSelect?.value;
    
    let isValid = true;
    let firstInvalidField = null;
    
    // Validate Routine (required)
    if (!routine) {
        setFieldValidationState('routine', true);
        isValid = false;
        firstInvalidField = firstInvalidField || routineSelect;
    } else {
        setFieldValidationState('routine', false);
    }
    
    // Validate Exercise (required)
    if (!exercise) {
        setFieldValidationState('exercise', true);
        isValid = false;
        // Only focus exercise if routine is already selected
        if (routine) {
            firstInvalidField = firstInvalidField || exerciseSelect;
        }
    } else {
        setFieldValidationState('exercise', false);
    }
    
    // Focus the first invalid field (prioritize routine)
    if (firstInvalidField) {
        // For enhanced dropdowns, click the button to open it
        const wpddContainer = firstInvalidField.closest('.wpdd');
        if (wpddContainer) {
            const wpddButton = wpddContainer.querySelector('.wpdd-button');
            if (wpddButton) {
                wpddButton.focus();
            }
        } else {
            firstInvalidField.focus();
        }
    }
    
    return isValid;
}

export function handleAddExercise(e) {
    if (e) e.preventDefault();
    
    // First, validate required selection fields (Routine and Exercise) with visual feedback
    if (!validateRequiredSelections()) {
        // Show toast for missing required selection fields
        const routine = document.getElementById('routine')?.value;
        const exercise = document.getElementById('exercise')?.value;
        
        const missingSelections = [];
        if (!routine) missingSelections.push('Routine');
        if (!exercise) missingSelections.push('Exercise');
        
        if (missingSelections.length > 0) {
            showToast(`Please select: ${missingSelections.join(' and ')}`, true);
            return;
        }
    }
    
    // Get all required form values
    const exercise = document.getElementById('exercise')?.value;
    const routine = document.getElementById('routine')?.value;
    const sets = document.getElementById('sets')?.value;
    const minRepRange = document.getElementById('min_rep')?.value;
    const maxRepRange = document.getElementById('max_rep_range')?.value;
    const rir = document.getElementById('rir')?.value;
    const weight = document.getElementById('weight')?.value;
    const rpe = document.getElementById('rpe')?.value;

    // Detailed validation
    const missingFields = [];
    if (!exercise) missingFields.push('Exercise');
    if (!routine) missingFields.push('Routine');
    if (!sets) missingFields.push('Sets');
    if (!minRepRange) missingFields.push('Min Rep Range');
    if (!maxRepRange) missingFields.push('Max Rep Range');
    if (!weight) missingFields.push('Weight');

    if (missingFields.length > 0) {
        const message = `Please fill in the following required fields: ${missingFields.join(', ')}`;
            workoutPlanDebugLog('Validation failed:', message);
            workoutPlanDebugLog('Current form values:', { exercise, routine, sets, minRepRange, maxRepRange, weight });
        showToast(message, true);
        return;
    }

    // Prepare exercise data
    const exerciseData = {
        exercise: exercise,
        routine: routine,
        sets: parseInt(sets),
        min_rep_range: parseInt(minRepRange),
        max_rep_range: parseInt(maxRepRange),
        rir: parseInt(rir || 0),
        weight: parseFloat(weight),
        rpe: rpe ? parseFloat(rpe) : null
    };

        workoutPlanDebugLog('Sending exercise data:', exerciseData);
    sendExerciseData(exerciseData);
}

async function sendExerciseData(exerciseData) {
    try {
        const response = await fetch('/add_exercise', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(exerciseData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            const errorMsg = errorData.error?.message || errorData.error || 'Failed to add exercise';
            throw new Error(errorMsg);
        }
        
        const data = await handleApiResponse(response);
        const message = data.message || 'Exercise added successfully';
        
        showToast(message);
        fetchWorkoutPlan(); // Refresh the table
        resetFormFields();
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message || 'Failed to add exercise', true);
    }
}

function resetFormFields() {
    // Preserve the current routine and exercise
    const currentRoutine = document.getElementById('routine').value;
    const currentExercise = document.getElementById('exercise').value;
    
    // Reset form fields to default values
    document.getElementById('sets').value = '3';
    document.getElementById('rir').value = '3';
    document.getElementById('weight').value = '25';
    document.getElementById('min_rep').value = '6';
    document.getElementById('max_rep_range').value = '8';
    document.getElementById('rpe').value = '7';

    // Restore the routine and exercise
    if (currentRoutine) {
        document.getElementById('routine').value = currentRoutine;
    }
    if (currentExercise) {
        document.getElementById('exercise').value = currentExercise;
        // Trigger change event for enhanced dropdown to update display
        document.getElementById('exercise').dispatchEvent(new Event('change', { bubbles: true }));
    }
}

function initializeDefaultValues() {
    const defaultValues = {
        'weight': 25,
        'sets': 3,
        'rir': 3,
        'rpe': 7,
        'min_rep': 6,
        'max_rep_range': 8
    };

    // Set default values for each input field
    Object.entries(defaultValues).forEach(([id, value]) => {
        const input = document.getElementById(id);
        if (input) {
            input.value = value;
            
            // Add event listener to validate input
            input.addEventListener('input', function() {
                const min = parseInt(this.min) || 0;
                const max = parseInt(this.max) || Infinity;
                let value = parseInt(this.value) || defaultValues[id];
                
                // Ensure value is within bounds
                value = Math.max(min, Math.min(max, value));
                this.value = value;
            });
        }
    });
}

export function initializeWorkoutPlanHandlers() {
    // Initialize default values
    initializeDefaultValues();

    // Add exercise button handler
    const addExerciseBtn = document.getElementById('add_exercise_btn');
    if (addExerciseBtn) {
        addExerciseBtn.addEventListener('click', handleAddExercise);
    }

    // Handle exercise selection changes
    handleExerciseSelection();
    
    // Handle routine selection changes
    handleRoutineSelection();
    
    // Initialize routine tabs - "All" tab click handler
    initializeRoutineTabs();

    // Initial fetch of workout plan
    fetchWorkoutPlan();
}

/**
 * Initializes the routine tabs click handlers
 */
function initializeRoutineTabs() {
    const allTabBtn = document.querySelector('#routine-tabs [data-routine="all"]');
    if (allTabBtn) {
        allTabBtn.addEventListener('click', () => handleRoutineTabClick('all'));
    }
}

export function updateWorkoutPlanTable(exercises) {
    const tbody = document.querySelector('#workout_plan_table_body');
    if (!tbody) {
        console.error('Workout plan table body not found');
        return;
    }

    tbody.innerHTML = '';

    // Sort exercises by order (null/0 values should come before numbered ones to maintain legacy order,
    // then by exercise_order ascending for properly ordered items)
    exercises.sort((a, b) => {
        const orderA = a.exercise_order || 0;
        const orderB = b.exercise_order || 0;
        // Both have order values - sort ascending
        return orderA - orderB;
    });

    exercises.forEach(exercise => {
        const row = document.createElement('tr');
        row.dataset.exerciseId = exercise.id;
        
        // Add drag handle and other cells with priority classes and data-labels
        row.innerHTML = `
            <td class="drag-handle" title="Drag to reorder">
                <i class="fas fa-grip-vertical"></i>
            </td>
            <td class="col--high" data-label="Routine">${exercise.routine || 'N/A'}</td>
            <td class="col--high" data-label="Exercise">${exercise.exercise || 'N/A'}</td>
            <td class="col--med" data-label="Primary Muscle">${exercise.primary_muscle_group || 'N/A'}</td>
            <td class="col--low" data-label="Secondary Muscle">${exercise.secondary_muscle_group || 'N/A'}</td>
            <td class="col--low" data-label="Tertiary Muscle">${exercise.tertiary_muscle_group || 'N/A'}</td>
            <td class="col--low" data-label="Isolated Muscles">${exercise.advanced_isolated_muscles || 'N/A'}</td>
            <td class="col--low" data-label="Utility">${exercise.utility || 'N/A'}</td>
            <td class="col--high is-num editable" data-field="sets" data-label="Sets">${exercise.sets || 'N/A'}</td>
            <td class="col--high is-num editable" data-field="min_rep_range" data-label="Min Rep">${exercise.min_rep_range || 'N/A'}</td>
            <td class="col--high is-num editable" data-field="max_rep_range" data-label="Max Rep">${exercise.max_rep_range || 'N/A'}</td>
            <td class="col--med is-num editable" data-field="rir" data-label="RIR">${exercise.rir || 'N/A'}</td>
            <td class="col--med is-num editable" data-field="rpe" data-label="RPE">${exercise.rpe || 'N/A'}</td>
            <td class="col--high is-num editable" data-field="weight" data-label="Weight">${exercise.weight || 'N/A'}</td>
            <td class="col--low" data-label="Grips">${exercise.grips || 'N/A'}</td>
            <td class="col--low" data-label="Stabilizers">${exercise.stabilizers || 'N/A'}</td>
            <td class="col--low" data-label="Synergists">${exercise.synergists || 'N/A'}</td>
            <td class="col--high" data-label="Actions">
                <button class="btn btn-danger btn-sm text-white" onclick="removeExercise(${exercise.id})">
                    <i class="fas fa-trash"></i> Remove
                </button>
            </td>
        `;

        // Add click handlers for editable cells
        row.querySelectorAll('.editable').forEach(cell => {
            cell.addEventListener('click', () => {
                makeTableCellEditable(cell, exercise.id, cell.dataset.field);
            });
        });
        
        tbody.appendChild(row);
    });

    // Initialize drag and drop after populating the table
    initializeDragAndDrop();
}

function makeTableCellEditable(cell, exerciseId, fieldName) {
    const originalValue = cell.textContent;
    const input = document.createElement('input');
    input.type = 'number';
    input.value = originalValue;
    input.className = 'form-control form-control-sm';
    
    // Add validation rules based on field type
    switch(fieldName) {
        case 'sets':
            input.min = 1;
            input.max = 10;
            break;
        case 'min_rep_range':
        case 'max_rep_range':
            input.min = 1;
            input.max = 30;
            break;
        case 'rir':
            input.min = 0;
            input.max = 10;
            break;
        case 'rpe':
            input.min = 1;
            input.max = 10;
            input.step = 0.5;
            break;
        case 'weight':
            input.min = 0;
            input.step = 0.5;
            break;
    }

    cell.textContent = '';
    cell.appendChild(input);
    input.focus();

    input.addEventListener('blur', async () => {
        const newValue = input.value;
        if (newValue !== originalValue) {
            try {
                const response = await updateExerciseField(exerciseId, fieldName, newValue);
                if (response.ok) {
                    cell.textContent = newValue;
                    showToast('Exercise updated successfully');
                } else {
                    throw new Error('Update failed');
                }
            } catch (error) {
                console.error('Error updating exercise:', error);
                cell.textContent = originalValue;
                showToast('Failed to update exercise', true);
            }
        } else {
            cell.textContent = originalValue;
        }
    });

    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            input.blur();
        }
    });
}

async function updateExerciseField(exerciseId, fieldName, value) {
    const updates = { [fieldName]: value };
    const response = await fetch('/update_exercise', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            id: exerciseId,
            updates: updates
        })
    });
    
    // Let handleApiResponse handle all response parsing to avoid consuming body twice
    const data = await handleApiResponse(response);
    return data;
}

// Add this function to initialize drag-and-drop
function initializeDragAndDrop() {
    const tbody = document.querySelector('#workout_plan_table_body');
    if (!tbody) return;

    Sortable.create(tbody, {
        animation: 150,
        handle: '.drag-handle',
        onEnd: async function(evt) {
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const orderData = rows.map((row, index) => ({
                id: parseInt(row.dataset.exerciseId),
                order: index + 1
            }));

            try {
                const response = await fetch('/update_exercise_order', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(orderData)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    const errorMsg = errorData.error?.message || errorData.error || 'Failed to update exercise order';
                    throw new Error(errorMsg);
                }

                const data = await handleApiResponse(response);
                const message = data.message || 'Exercise order updated successfully';
                showToast(message);
            } catch (error) {
                console.error('Error updating exercise order:', error);
                showToast(error.message || 'Failed to update exercise order', true);
                // Optionally refresh the table to restore original order
                fetchWorkoutPlan();
            }
        }
    });
}