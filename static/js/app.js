import { showToast } from './modules/toast.js';
import { fetchWorkoutPlan, handleRoutineSelection, updateExerciseDetails, updateExerciseForm, handleAddExercise } from './modules/workout-plan.js';
import { initializeWorkoutLog, deleteWorkoutLog, updateScoredValue, handleDateChange } from './modules/workout-log.js';
import { initializeFilters, initializeAdvancedFilters, initializeSearchFilter, initializeFilterKeyboardEvents } from './modules/filters.js';
import { addExercise, removeExercise } from './modules/exercises.js';
import { initializeUIHandlers, initializeFormHandlers, initializeTooltips, initializeDropdowns, handleTableSort } from './modules/ui-handlers.js';
import { exportToExcel, exportToWorkoutLog, exportSummary } from './modules/exports.js';
import { initializeWorkoutPlanHandlers, updateWorkoutPlanUI } from './modules/workout-plan.js';
import { initializeWorkoutLogFilters } from './modules/workout-log.js';
import { initializeDataTables, initializeCharts } from './modules/ui-handlers.js';
import { 
    fetchWeeklySummary,
    fetchSessionSummary 
} from './modules/summary.js';
import { 
    updateProgressionDate,
    updateProgressionStatus 
} from './modules/workout-log.js';
import { validateScoredValue } from './modules/workout-log.js';
import { 
    checkProgressionStatus,
    initializeProgressionChecks 
} from './modules/workout-log.js';
import { initializeNavHighlighting } from './modules/navbar.js';
import { initializeNavbar } from './modules/navbar.js';
import { initializeNavbarEnhancements } from './modules/navbar-enhancements.js';
import { initializeProgressionPlan } from './modules/progression-plan.js';
import { initializeVolumeSplitter } from './modules/volume-splitter.js';
import { initializeWorkoutDropdowns } from './modules/workout-dropdowns.js';

const APP_DEBUG = false;
const appDebugLog = (...args) => {
    if (APP_DEBUG) {
        console.log(...args);
    }
};

// Make certain functions globally available
window.addExercise = addExercise;
window.removeExercise = removeExercise;
window.exportToExcel = exportToExcel;
window.exportToWorkoutLog = exportToWorkoutLog;
window.exportSummary = exportSummary;
window.deleteWorkoutLog = deleteWorkoutLog;
window.updateExerciseDetails = updateExerciseDetails;
window.updateExerciseForm = updateExerciseForm;
window.updateProgressionDate = updateProgressionDate;
window.updateProgressionStatus = updateProgressionStatus;
window.validateScoredValue = validateScoredValue;
window.checkProgressionStatus = checkProgressionStatus;
window.handleAddExercise = handleAddExercise;
window.updateScoredValue = updateScoredValue;
window.handleDateChange = handleDateChange;

// Initialize navbar
initializeNavbar();
initializeNavbarEnhancements();

// Initialize workout plan dropdowns
initializeWorkoutDropdowns();

// Page initializer functions
function initializeHomePage() {
    appDebugLog('Initializing Home page');
    return {
        cleanup: () => {
            appDebugLog('Cleaning up Home page');
        }
    };
}

function initializeWeeklySummary() {
    appDebugLog('Initializing Weekly Summary page');
    initializeCharts();
    fetchWeeklySummary();
    return {
        cleanup: () => {
            appDebugLog('Cleaning up Weekly Summary page');
        }
    };
}

function initializeSessionSummary() {
    appDebugLog('Initializing Session Summary page');
    initializeCharts();
    fetchSessionSummary();
    return {
        cleanup: () => {
            appDebugLog('Cleaning up Session Summary page');
        }
    };
}

function initializeWorkoutPlan() {
    appDebugLog('Initializing Workout Plan page');
    initializeFilters();
    initializeFilterKeyboardEvents();
    initializeAdvancedFilters();
    initializeSearchFilter();
    handleRoutineSelection();
    initializeWorkoutPlanHandlers();
    // fetchWorkoutPlan is already called inside initializeWorkoutPlanHandlers
    return {
        cleanup: () => {
            appDebugLog('Cleaning up Workout Plan page');
        }
    };
}

function initializeProgressionPage() {
    appDebugLog('Initializing Progression Plan page');
    initializeProgressionPlan();
}

const pageInitializers = {
    '/': initializeHomePage,
    '/workout_plan': initializeWorkoutPlan,
    '/workout_log': initializeWorkoutLog,
    '/weekly_summary': initializeWeeklySummary,
    '/session_summary': initializeSessionSummary,
    '/progression': initializeProgressionPage,
    '/volume_splitter': initializeVolumeSplitter
};

document.addEventListener("DOMContentLoaded", () => {
    const currentPath = window.location.pathname;

    // Common initializations
    const commonInit = () => {
        initializeUIHandlers();
        initializeFormHandlers();
        initializeTooltips();
        initializeDropdowns();
        handleTableSort();
    };

    // Initialize common elements
    commonInit();

    // Initialize page-specific functionality
    const initializer = pageInitializers[currentPath];
    if (initializer) {
        initializer();
    } else {
        appDebugLog(`No specific initialization for path: ${currentPath}`);
    }
});

function initializeModules() {
    const path = window.location.pathname;
    appDebugLog(`Initializing modules for path: ${path}`);

    switch (path) {
        // ... other cases ...
        case '/progression':
            appDebugLog('Initializing Progression Plan page');
            initializeProgressionPage();
            break;
    }
}

// Ensure erase data button only exists on welcome page
document.addEventListener('DOMContentLoaded', function() {
    // Remove any errant erase data buttons outside welcome page
    if (!document.querySelector('.welcome-container')) {
        const errantButtons = document.querySelectorAll('#eraseDataBtn, .erase-data-btn');
        errantButtons.forEach(button => button.remove());
    }
});
