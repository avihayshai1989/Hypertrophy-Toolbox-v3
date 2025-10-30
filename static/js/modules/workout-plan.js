import { showToast } from './toast.js';

// Workout plan functionality
export async function fetchWorkoutPlan() {
    try {
        const response = await fetch('/get_workout_plan');
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch workout plan');
        }

        updateWorkoutPlanTable(data);
        updateWorkoutPlanUI(data);
    } catch (error) {
        console.error('Error loading workout plan:', error);
        showToast('Failed to load workout plan', true);
    }
}

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
        .then(response => response.json())
        .then(data => {
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
            showToast('Failed to load exercise details', true);
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
        .then(response => response.json())
        .then(data => {
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
            showToast('Failed to load exercise recommendations', true);
            
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
        if (selectedExercise) {
            updateExerciseDetails(selectedExercise);
            updateExerciseForm(selectedExercise);
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
            if (!selectedRoutine) {
                exerciseSelect.innerHTML = '<option value="">Select Exercise</option>';
                return;
            }

            // Store the selected routine
            routineSelect.dataset.selectedRoutine = selectedRoutine;

            // Fetch exercises for the selected routine
            const response = await fetch(`/get_routine_exercises/${encodeURIComponent(selectedRoutine)}`);
            if (!response.ok) {
                throw new Error('Failed to fetch exercises for routine');
            }

            const exercises = await response.json();
            
            // Update exercise dropdown and maintain selection if possible
            const currentExercise = exerciseSelect.value;
            updateExerciseDropdown(exercises, currentExercise);

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

export function handleAddExercise(e) {
    if (e) e.preventDefault();
    
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
        console.log('Validation failed:', message);
        console.log('Current form values:', { exercise, routine, sets, minRepRange, maxRepRange, weight });
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

    console.log('Sending exercise data:', exerciseData);
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

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to add exercise');
        }
        
        showToast('Exercise added successfully');
        fetchWorkoutPlan(); // Refresh the table
        resetFormFields();
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message || 'Failed to add exercise', true);
    }
}

function resetFormFields() {
    // Preserve the current routine
    const currentRoutine = document.getElementById('routine').value;
    
    // Reset form fields to default values
    document.getElementById('sets').value = '3';
    document.getElementById('rir').value = '3';
    document.getElementById('weight').value = '25';
    document.getElementById('min_rep').value = '6';
    document.getElementById('max_rep_range').value = '8';
    document.getElementById('rpe').value = '7';

    // Restore the routine
    if (currentRoutine) {
        document.getElementById('routine').value = currentRoutine;
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

    // Initial fetch of workout plan
    fetchWorkoutPlan();
}

export function updateWorkoutPlanTable(exercises) {
    const tbody = document.querySelector('#workout_plan_table_body');
    if (!tbody) {
        console.error('Workout plan table body not found');
        return;
    }

    tbody.innerHTML = '';

    // Sort exercises by order
    exercises.sort((a, b) => (a.exercise_order || 0) - (b.exercise_order || 0));

    exercises.forEach(exercise => {
        const row = document.createElement('tr');
        row.dataset.exerciseId = exercise.id;
        
        // Add drag handle and other cells
        row.innerHTML = `
            <td class="drag-handle" title="Drag to reorder">
                <i class="fas fa-grip-vertical"></i>
            </td>
            <td>${exercise.routine || 'N/A'}</td>
            <td>${exercise.exercise || 'N/A'}</td>
            <td>${exercise.primary_muscle_group || 'N/A'}</td>
            <td>${exercise.secondary_muscle_group || 'N/A'}</td>
            <td>${exercise.tertiary_muscle_group || 'N/A'}</td>
            <td>${exercise.advanced_isolated_muscles || 'N/A'}</td>
            <td>${exercise.utility || 'N/A'}</td>
            <td class="editable" data-field="sets">${exercise.sets || 'N/A'}</td>
            <td class="editable" data-field="min_rep_range">${exercise.min_rep_range || 'N/A'}</td>
            <td class="editable" data-field="max_rep_range">${exercise.max_rep_range || 'N/A'}</td>
            <td class="editable" data-field="rir">${exercise.rir || 'N/A'}</td>
            <td class="editable" data-field="rpe">${exercise.rpe || 'N/A'}</td>
            <td class="editable" data-field="weight">${exercise.weight || 'N/A'}</td>
            <td>${exercise.grips || 'N/A'}</td>
            <td>${exercise.stabilizers || 'N/A'}</td>
            <td>${exercise.synergists || 'N/A'}</td>
            <td>
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
    
    if (!response.ok) {
        throw new Error('Failed to update exercise');
    }
    
    return response;
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
                    throw new Error('Failed to update exercise order');
                }

                showToast('Exercise order updated successfully');
            } catch (error) {
                console.error('Error updating exercise order:', error);
                showToast('Failed to update exercise order', true);
                // Optionally refresh the table to restore original order
                fetchWorkoutPlan();
            }
        }
    });
}