// Function to show a toast notification
function showToast(message, isError = false) {
    // Get the toast body element
    const toastBody = document.getElementById("toast-body");

    // Update the toast message
    toastBody.innerText = message;

    // Get the toast container element
    const toastElement = document.getElementById("liveToast");

    // Set toast styles based on success or error
    toastElement.classList.remove("bg-success", "bg-danger");
    toastElement.classList.add(isError ? "bg-danger" : "bg-success");

    // Show the toast notification
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
}

// Access the global routineOptions variable passed from the backend
const routineOptions = window.routineOptions;

// Function to populate routines based on the selected split type
function populateRoutines() {
    // Get the selected split type from the dropdown
    const splitType = document.getElementById("routineType").value;

    // Get the routine dropdown element
    const routineDropdown = document.getElementById("routine");

    // Clear the current options in the routine dropdown
    routineDropdown.innerHTML = '<option value="">Select Routine</option>';

    // Check if the selected split type has associated routines
    if (routineOptions[splitType] && routineOptions[splitType].length > 0) {
        // Populate the dropdown with routines
        routineOptions[splitType].forEach((routine) => {
            const option = document.createElement("option");
            option.value = routine; // Set the option value
            option.textContent = routine; // Set the display text
            routineDropdown.appendChild(option); // Append the option to the dropdown
        });

        // Show a success message
        showToast("Routines populated successfully!");
    } else {
        // Show an error message if no routines are available
        showToast("No routines available for the selected split type.", true);
    }
}

// Event Listener (Optional Enhancement)
// If the routine dropdown changes or needs additional interaction, you can add event listeners here:
// Example:
// document.getElementById("routineType").addEventListener("change", populateRoutines);

function updateFilters(exercise) {
    // Update filter dropdowns based on exercise details
    $("#muscle_filter").val(exercise.primary_muscle_group);
    $("#isolated_muscles_filter").val(exercise.advanced_isolated_muscles);
    // ...
}
