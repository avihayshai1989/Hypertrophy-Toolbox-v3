import { showToast } from './toast.js';
import { fetchWorkoutPlan } from './workout-plan.js';

export function addExercise() {
    console.log('addExercise function called');

    const exercise = document.getElementById('exercise')?.value;
    const routine = document.getElementById('routine')?.value;
    const sets = document.getElementById('sets')?.value;
    const minRepRange = document.getElementById('min_rep')?.value;
    const maxRepRange = document.getElementById('max_rep_range')?.value;
    const rir = document.getElementById('rir')?.value;
    const weight = document.getElementById('weight')?.value;
    const rpe = document.getElementById('rpe')?.value;

    // Validate required fields
    if (!exercise || !routine || !sets || !minRepRange || !maxRepRange || !weight) {
        showToast('Please fill in all required fields', true);
        return;
    }

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
        fetchWorkoutPlan();
        resetFormFields();
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message || 'Failed to add exercise', true);
    }
}

export async function removeExercise(exerciseId) {
    if (!exerciseId) {
        console.error("Error: exercise ID is required to remove an exercise.");
        showToast("Exercise ID is missing. Unable to remove exercise.", true);
        return;
    }

    try {
        const response = await fetch("/remove_exercise", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: exerciseId }),
        });

        const result = await response.json();
        
        if (response.ok) {
            showToast(result.message || "Exercise removed successfully!");
            fetchWorkoutPlan();
        } else {
            throw new Error(result.message || "Failed to remove exercise");
        }
    } catch (error) {
        console.error("Error removing exercise:", error);
        showToast(`Unable to remove exercise: ${error.message}`, true);
    }
}

function resetFormFields() {
    document.getElementById('sets').value = '1';
    document.getElementById('rir').value = '0';
    document.getElementById('weight').value = '100';
    document.getElementById('min_rep').value = '3';
    document.getElementById('max_rep_range').value = '5';
    if (document.getElementById('rpe')) {
        document.getElementById('rpe').value = '';
    }
}

export async function clearWorkoutPlan() {
    try {
        // Close the modal
        const modal = document.getElementById('clearPlanModal');
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }

        const response = await fetch('/clear_workout_plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();
        
        if (response.ok) {
            showToast(result.message || 'Workout plan cleared successfully!');
            fetchWorkoutPlan(); // Refresh the table to show empty state
        } else {
            throw new Error(result.error?.message || result.message || 'Failed to clear workout plan');
        }
    } catch (error) {
        console.error('Error clearing workout plan:', error);
        showToast(`Unable to clear workout plan: ${error.message}`, true);
    }
} 