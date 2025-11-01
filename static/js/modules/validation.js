/**
 * Form validation utilities with inline error display.
 */

import { showInlineError, clearInlineError, clearAllInlineErrors } from './toast.js';

/**
 * Validation rules
 */
const validationRules = {
    required: (value) => {
        if (typeof value === 'string') {
            return value.trim().length > 0;
        }
        return value !== null && value !== undefined;
    },
    
    email: (value) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(value);
    },
    
    minLength: (value, min) => {
        return value.length >= min;
    },
    
    maxLength: (value, max) => {
        return value.length <= max;
    },
    
    number: (value) => {
        return !isNaN(parseFloat(value)) && isFinite(value);
    },
    
    positiveNumber: (value) => {
        return validationRules.number(value) && parseFloat(value) > 0;
    },
    
    integer: (value) => {
        return Number.isInteger(Number(value));
    },
    
    range: (value, min, max) => {
        const num = parseFloat(value);
        return num >= min && num <= max;
    },
    
    pattern: (value, regex) => {
        return new RegExp(regex).test(value);
    },
    
    date: (value) => {
        const date = new Date(value);
        return date instanceof Date && !isNaN(date);
    }
};

/**
 * Error messages for validation rules
 */
const errorMessages = {
    required: 'This field is required',
    email: 'Please enter a valid email address',
    minLength: (min) => `Must be at least ${min} characters`,
    maxLength: (max) => `Must be no more than ${max} characters`,
    number: 'Please enter a valid number',
    positiveNumber: 'Please enter a positive number',
    integer: 'Please enter a whole number',
    range: (min, max) => `Must be between ${min} and ${max}`,
    pattern: 'Invalid format',
    date: 'Please enter a valid date'
};

/**
 * Validate a single field
 * 
 * @param {string} fieldId - ID of the field to validate
 * @param {Object} rules - Validation rules object
 * @returns {boolean} True if valid, false otherwise
 */
export function validateField(fieldId, rules) {
    const field = document.getElementById(fieldId);
    if (!field) {
        console.warn(`Field with ID '${fieldId}' not found`);
        return false;
    }

    const value = field.value;
    clearInlineError(fieldId);

    // Check each validation rule
    for (const [rule, ruleValue] of Object.entries(rules)) {
        let isValid = true;
        let errorMessage = '';

        switch (rule) {
            case 'required':
                isValid = validationRules.required(value);
                errorMessage = errorMessages.required;
                break;
            
            case 'email':
                if (value && ruleValue) {
                    isValid = validationRules.email(value);
                    errorMessage = errorMessages.email;
                }
                break;
            
            case 'minLength':
                if (value) {
                    isValid = validationRules.minLength(value, ruleValue);
                    errorMessage = errorMessages.minLength(ruleValue);
                }
                break;
            
            case 'maxLength':
                if (value) {
                    isValid = validationRules.maxLength(value, ruleValue);
                    errorMessage = errorMessages.maxLength(ruleValue);
                }
                break;
            
            case 'number':
                if (value && ruleValue) {
                    isValid = validationRules.number(value);
                    errorMessage = errorMessages.number;
                }
                break;
            
            case 'positiveNumber':
                if (value && ruleValue) {
                    isValid = validationRules.positiveNumber(value);
                    errorMessage = errorMessages.positiveNumber;
                }
                break;
            
            case 'integer':
                if (value && ruleValue) {
                    isValid = validationRules.integer(value);
                    errorMessage = errorMessages.integer;
                }
                break;
            
            case 'range':
                if (value && ruleValue) {
                    isValid = validationRules.range(value, ruleValue.min, ruleValue.max);
                    errorMessage = errorMessages.range(ruleValue.min, ruleValue.max);
                }
                break;
            
            case 'pattern':
                if (value && ruleValue) {
                    isValid = validationRules.pattern(value, ruleValue);
                    errorMessage = errorMessages.pattern;
                }
                break;
            
            case 'date':
                if (value && ruleValue) {
                    isValid = validationRules.date(value);
                    errorMessage = errorMessages.date;
                }
                break;
            
            case 'custom':
                // Custom validation function
                if (typeof ruleValue === 'function') {
                    const result = ruleValue(value, field);
                    if (typeof result === 'object') {
                        isValid = result.valid;
                        errorMessage = result.message;
                    } else {
                        isValid = result;
                        errorMessage = 'Invalid value';
                    }
                }
                break;
        }

        if (!isValid) {
            showInlineError(fieldId, errorMessage);
            return false;
        }
    }

    // Field is valid
    field.classList.add('is-valid');
    return true;
}

/**
 * Validate an entire form
 * 
 * @param {string} formId - ID of the form to validate
 * @param {Object} validationSchema - Object mapping field IDs to validation rules
 * @returns {boolean} True if all fields are valid, false otherwise
 */
export function validateForm(formId, validationSchema) {
    const form = document.getElementById(formId);
    if (!form) {
        console.warn(`Form with ID '${formId}' not found`);
        return false;
    }

    // Clear all existing errors
    clearAllInlineErrors(formId);

    let isFormValid = true;

    // Validate each field
    for (const [fieldId, rules] of Object.entries(validationSchema)) {
        const isFieldValid = validateField(fieldId, rules);
        if (!isFieldValid) {
            isFormValid = false;
        }
    }

    return isFormValid;
}

/**
 * Setup real-time validation for a field
 * 
 * @param {string} fieldId - ID of the field
 * @param {Object} rules - Validation rules
 */
export function setupFieldValidation(fieldId, rules) {
    const field = document.getElementById(fieldId);
    if (!field) {
        console.warn(`Field with ID '${fieldId}' not found`);
        return;
    }

    // Validate on blur
    field.addEventListener('blur', () => {
        validateField(fieldId, rules);
    });

    // Clear error on input (but don't validate until blur)
    field.addEventListener('input', () => {
        clearInlineError(fieldId);
        field.classList.remove('is-valid');
    });
}

/**
 * Setup real-time validation for an entire form
 * 
 * @param {string} formId - ID of the form
 * @param {Object} validationSchema - Object mapping field IDs to validation rules
 */
export function setupFormValidation(formId, validationSchema) {
    for (const [fieldId, rules] of Object.entries(validationSchema)) {
        setupFieldValidation(fieldId, rules);
    }
}

/**
 * Validate form on submit
 * 
 * @param {string} formId - ID of the form
 * @param {Object} validationSchema - Object mapping field IDs to validation rules
 * @param {Function} onValid - Callback function to execute if form is valid
 */
export function handleFormSubmit(formId, validationSchema, onValid) {
    const form = document.getElementById(formId);
    if (!form) {
        console.warn(`Form with ID '${formId}' not found`);
        return;
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const isValid = validateForm(formId, validationSchema);
        
        if (isValid && typeof onValid === 'function') {
            onValid(e);
        }
    });
}

/**
 * Export validation rules for external use
 */
export { validationRules, errorMessages };

