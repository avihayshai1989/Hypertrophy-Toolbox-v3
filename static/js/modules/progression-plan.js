import { showToast } from './toast.js';

export function initializeProgressionPlan() {
    const exerciseSelect = document.getElementById('exerciseSelect');
    const suggestionsContainer = document.getElementById('suggestionsContainer');
    const suggestionsList = document.getElementById('suggestionsList');
    const goalModalElement = document.getElementById('goalSettingModal');
    const goalModal = new bootstrap.Modal(goalModalElement, {
        keyboard: true,
        backdrop: 'static',
    });
    
    // Store the element that had focus before the modal was opened
    let previousActiveElement;
    
    // Handle modal show
    goalModalElement.addEventListener('show.bs.modal', function () {
        // Store the current focus
        previousActiveElement = document.activeElement;
    });
    
    // Reset form when modal is hidden
    goalModalElement.addEventListener('hidden.bs.modal', function () {
        document.getElementById('goalForm').reset();
        const inputs = document.querySelectorAll('#goalForm input:not([type="hidden"])');
        inputs.forEach(input => {
            input.disabled = false;
        });
        // Restore focus to the previous element
        if (previousActiveElement) {
            previousActiveElement.focus();
        }
    });
    
    // Enable form inputs when modal is shown
    goalModalElement.addEventListener('shown.bs.modal', function () {
        const currentValueInput = document.getElementById('currentValue');
        const targetValueInput = document.getElementById('targetValue');
        if (document.getElementById('goalType').value !== 'technique') {
            currentValueInput.disabled = false;
            targetValueInput.disabled = false;
        }
        // Set focus to the first input field
        if (!currentValueInput.disabled) {
            currentValueInput.focus();
        } else {
            document.getElementById('goalDate').focus();
        }
    });
    
    // Add event listener for closing modal
    document.getElementById('closeGoalModal').addEventListener('click', () => {
        goalModal.hide();
    });
    
    // Add keyboard event listener for ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && goalModalElement.classList.contains('show')) {
            goalModal.hide();
        }
    });
    
    console.log('Initializing progression plan with elements:', {
        exerciseSelect,
        suggestionsContainer,
        suggestionsList,
        goalModal
    });
    
    if (!exerciseSelect) {
        console.error('exerciseSelect is null!');
        return;
    }
    
    // Add event listeners
    exerciseSelect.addEventListener('click', () => {
        console.log('Exercise select clicked');
    });
    
    exerciseSelect.addEventListener('change', handleExerciseChange);
    
    // Add event listener for goal setting buttons
    document.addEventListener('click', async function(e) {
        if (e.target.classList.contains('set-goal-btn')) {
            console.log('Goal button clicked:', e.target);
            const goalType = e.target.dataset.goalType;
            const exercise = e.target.dataset.exercise;
            console.log('Goal type:', goalType, 'Exercise:', exercise);
            
            // Pre-fill current values based on goal type
            const currentValueInput = document.getElementById('currentValue');
            const targetValueInput = document.getElementById('targetValue');
            const goalDateInput = document.getElementById('goalDate');
            
            // Set min date to today
            const today = new Date().toISOString().split('T')[0];
            goalDateInput.min = today;
            
            // Default to 4 weeks from now
            const fourWeeksFromNow = new Date();
            fourWeeksFromNow.setDate(fourWeeksFromNow.getDate() + 28);
            goalDateInput.value = fourWeeksFromNow.toISOString().split('T')[0];
            
            // Fetch current value from workout history
            if (goalType !== 'technique') {
                try {
                    console.log(`Fetching current value for ${exercise} (${goalType})`);
                    const response = await fetch('/get_current_value', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ exercise, goal_type: goalType }),
                    });
                    
                    if (!response.ok) {
                        throw new Error('Failed to fetch current value');
                    }
                    
                    const data = await response.json();
                    console.log('Received current value data:', data);
                    
                    if (data.error) {
                        throw new Error(data.error);
                    }
                    
                    // Ensure we're getting a number
                    const currentValue = parseFloat(data.current_value) || 0;
                    console.log('Parsed current value:', currentValue);
                    currentValueInput.value = data.current_value;
                    
                    // Update target value based on current value
                    switch(goalType) {
                        case 'reps':
                            targetValueInput.value = currentValue + 2;
                            break;
                        case 'weight':
                            targetValueInput.value = Math.round((currentValue * 1.05) * 100) / 100;
                            break;
                        case 'sets':
                            targetValueInput.value = currentValue + 1;
                            break;
                    }
                } catch (error) {
                    console.error('Error fetching current value:', error);
                    currentValueInput.value = '0';
                    targetValueInput.value = goalType === 'reps' ? '2' : 
                                           goalType === 'weight' ? '5' : 
                                           goalType === 'sets' ? '1' : '0';
                }
            }
            
            // Customize modal based on goal type
            const modalTitle = document.querySelector('.modal-title');
            switch(goalType) {
                case 'technique':
                    modalTitle.textContent = 'Set Technique Goal';
                    currentValueInput.value = 'N/A';
                    targetValueInput.value = 'N/A';
                    currentValueInput.disabled = true;
                    targetValueInput.disabled = true;
                    break;
                case 'reps':
                    modalTitle.textContent = 'Set Repetition Goal';
                    currentValueInput.disabled = false;
                    targetValueInput.disabled = false;
                    targetValueInput.value = parseInt(currentValueInput.value || 0) + 2;
                    break;
                case 'weight':
                    modalTitle.textContent = 'Set Weight Goal';
                    currentValueInput.disabled = false;
                    targetValueInput.disabled = false;
                    targetValueInput.value = Math.round((parseFloat(currentValueInput.value || 0) * 1.05) * 100) / 100;
                    break;
                case 'sets':
                    modalTitle.textContent = 'Set Volume Goal';
                    currentValueInput.disabled = false;
                    targetValueInput.disabled = false;
                    targetValueInput.value = parseInt(currentValueInput.value || 0) + 1;
                    break;
            }
            
            document.getElementById('goalType').value = goalType;
            document.getElementById('exerciseName').value = exercise;
            
            goalModal.show();
        }
    });
    
    // Handle goal saving
    document.getElementById('saveGoal').addEventListener('click', async function(e) {
        e.preventDefault();
        try {
            const formData = {
                exercise: document.getElementById('exerciseName').value,
                goal_type: document.getElementById('goalType').value,
                current_value: document.getElementById('currentValue').value,
                target_value: document.getElementById('targetValue').value,
                goal_date: document.getElementById('goalDate').value
            };
            
            // Validate form data
            if (!formData.exercise || !formData.goal_type || !formData.goal_date) {
                throw new Error('Please fill in all required fields');
            }
            
            if (formData.goal_type !== 'technique' && (!formData.current_value || !formData.target_value)) {
                throw new Error('Please enter current and target values');
            }
            
            console.log('Saving goal:', formData);
            
            const response = await fetch('/save_progression_goal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to save goal');
            }
            
            goalModal.hide();
            showToast('Goal saved successfully');
            setTimeout(() => {
                location.reload();
            }, 300);
        } catch (error) {
            console.error('Error saving goal:', error);
            showToast('Failed to save goal: ' + error.message, true);
        }
    });
    
    async function handleExerciseChange() {
        console.log('Exercise select changed');
        const exercise = this.value;
        console.log('Selected exercise:', exercise);
        
        if (!exercise) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        try {
            const requestBody = JSON.stringify({ exercise });
            console.log('Sending request with body:', requestBody);
            
            const response = await fetch('/get_exercise_suggestions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: requestBody,
            });
            
            console.log('Response received:', response);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to fetch suggestions');
            }
            
            const suggestions = await response.json();
            console.log('Suggestions data:', suggestions);
            
            if (!Array.isArray(suggestions)) {
                throw new Error('Invalid suggestions data received');
            }
            
            displaySuggestions(suggestions, exercise);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            suggestionsList.innerHTML = `
                <div class="alert alert-danger">
                    Error loading suggestions: ${error.message}
                </div>
            `;
            suggestionsContainer.style.display = 'block';
        }
    }
    
    function displaySuggestions(suggestions, exercise) {
        console.log('Displaying suggestions for:', exercise);
        suggestionsList.innerHTML = '';
        
        if (!suggestions || suggestions.length === 0) {
            suggestionsList.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info">
                        No suggestions available for this exercise yet.
                    </div>
                </div>
            `;
            suggestionsContainer.style.display = 'block';
            return;
        }
        
        suggestions.forEach(suggestion => {
            const card = document.createElement('div');
            card.className = 'col-md-6 col-lg-3';
            card.innerHTML = `
                <div class="card suggestion-card" data-goal-type="${suggestion.type}">
                    <div class="card-body d-flex flex-column">
                        <h5 class="card-title">${suggestion.title}</h5>
                        <p class="card-text">${suggestion.description}</p>
                        <button class="btn btn-primary set-goal-btn mt-auto" 
                                data-goal-type="${suggestion.type}"
                                data-exercise="${exercise}">
                            ${suggestion.action}
                        </button>
                    </div>
                </div>
            `;
            suggestionsList.appendChild(card);
            console.log('Added suggestion card:', suggestion.type);
        });
        
        suggestionsContainer.style.display = 'block';
    }
    
    // Handle focus trap in modal
    goalModalElement.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            const focusableElements = goalModalElement.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            const firstFocusableElement = focusableElements[0];
            const lastFocusableElement = focusableElements[focusableElements.length - 1];

            if (e.shiftKey) { // Shift + Tab
                if (document.activeElement === firstFocusableElement) {
                    lastFocusableElement.focus();
                    e.preventDefault();
                }
            } else { // Tab
                if (document.activeElement === lastFocusableElement) {
                    firstFocusableElement.focus();
                    e.preventDefault();
                }
            }
        }
    });
    
    // Handle goal deletion
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.delete-goal')) {
            const button = e.target.closest('.delete-goal');
            const goalId = button.dataset.goalId;
            
            if (confirm('Are you sure you want to delete this goal?')) {
                try {
                    const response = await fetch(`/delete_progression_goal/${goalId}`, {
                        method: 'DELETE',
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.error || 'Failed to delete goal');
                    }
                    
                    showToast('Goal deleted successfully');
                    // Remove the row from the table
                    button.closest('tr').remove();
                } catch (error) {
                    console.error('Error deleting goal:', error);
                    showToast('Failed to delete goal: ' + error.message, true);
                }
            }
        }
    });
} 

function createSuggestionCard(suggestion) {
    return `
        <div class="col-md-6 col-lg-3 mb-4">
            <div class="card suggestion-card h-100">
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title">${suggestion.title}</h5>
                    <p class="card-text">${suggestion.description}</p>
                    <button class="btn btn-primary set-goal-btn mt-auto" 
                            data-goal-type="${suggestion.type}"
                            onclick="openGoalModal(this)">
                        ${suggestion.action}
                    </button>
                </div>
            </div>
        </div>
    `;
}

function openGoalModal(button) {
    const goalType = button.getAttribute('data-goal-type');
    const modalTitle = document.getElementById('goalModalLabel');
    const currentValueInput = document.getElementById('currentValue');
    const targetValueInput = document.getElementById('targetValue');
    
    // Set appropriate labels and placeholders based on goal type
    switch(goalType) {
        case 'weight':
            modalTitle.textContent = 'Set Weight Goal';
            currentValueInput.placeholder = 'Current weight (kg)';
            targetValueInput.placeholder = 'Target weight (kg)';
            break;
        case 'reps':
            modalTitle.textContent = 'Set Repetition Goal';
            currentValueInput.placeholder = 'Current reps';
            targetValueInput.placeholder = 'Target reps';
            break;
        case 'sets':
            modalTitle.textContent = 'Set Volume Goal';
            currentValueInput.placeholder = 'Current sets';
            targetValueInput.placeholder = 'Target sets';
            break;
        case 'technique':
            modalTitle.textContent = 'Set Technique Goal';
            currentValueInput.placeholder = 'Current proficiency (1-10)';
            targetValueInput.placeholder = 'Target proficiency (1-10)';
            break;
    }
    
    // Get and set current value
    getCurrentValue(goalType);
} 