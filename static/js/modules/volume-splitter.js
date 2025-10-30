export function initializeVolumeSplitter() {
    initializeTooltips();
    const calculateBtn = document.getElementById('calculate-volume');
    const resetBtn = document.getElementById('reset-volume');
    const exportBtn = document.getElementById('export-volume');
    const resultsSection = document.querySelector('.results-section');
    
    calculateBtn.addEventListener('click', calculateVolume);
    resetBtn.addEventListener('click', resetValues);
    exportBtn.addEventListener('click', exportVolumePlan);
    loadVolumeHistory();
    
    // Add event delegation for load buttons
    document.getElementById('history-body').addEventListener('click', function(e) {
        if (e.target.classList.contains('load-plan')) {
            const planId = e.target.dataset.planId;
            loadPlan(planId);
        }
    });
    
    const exportExcelBtn = document.getElementById('export-to-excel-btn');
    if (exportExcelBtn) {
        exportExcelBtn.addEventListener('click', exportToExcel);
    }
}

function initializeTooltips() {
    // Training frequency tooltip
    tippy('#training-days', {
        content: 'Choose a realistic frequency that you can maintain consistently. More training days allow for better volume distribution.',
        placement: 'right'
    });
    
    // Volume input tooltips
    document.querySelectorAll('.volume-input').forEach(input => {
        const muscle = input.dataset.muscle;
        tippy(input, {
            content: `
                <div class="tooltip-content">
                    <h6>${muscle} Training Guidelines:</h6>
                    <ul>
                        <li>Minimum: 12 sets/week for growth</li>
                        <li>Maximum: 20 sets/week to avoid overtraining</li>
                        <li>Optimal: 6-8 sets per session</li>
                    </ul>
                </div>
            `,
            allowHTML: true,
            placement: 'right'
        });
    });
}

function calculateVolume() {
    const trainingDays = parseInt(document.getElementById('training-days').value);
    const volumes = {};
    
    document.querySelectorAll('.volume-input').forEach(input => {
        volumes[input.dataset.muscle] = parseInt(input.value) || 0;
    });
    
    fetch('/api/calculate_volume', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            training_days: trainingDays,
            volumes: volumes
        })
    })
    .then(response => response.json())
    .then(data => {
        displayResults(data.results);
        displaySuggestions(data.suggestions);
        document.querySelector('.results-section').classList.remove('d-none');
    });
}

function displayResults(results) {
    const tbody = document.getElementById('results-body');
    tbody.innerHTML = '';
    
    Object.entries(results).forEach(([muscle, data]) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${muscle}</td>
            <td>${data.weekly_sets}</td>
            <td>${data.sets_per_session}</td>
            <td class="status-${data.status}">
                ${data.status.charAt(0).toUpperCase() + data.status.slice(1)}
            </td>
        `;
        tbody.appendChild(row);
    });
}

function resetValues() {
    document.querySelectorAll('.volume-input').forEach(input => {
        input.value = 0;
    });
    document.querySelector('.results-section').classList.add('d-none');
}

function loadPlan(planId) {
    fetch(`/api/volume_plan/${planId}`)
        .then(response => response.json())
        .then(plan => {
            // Set training days
            document.getElementById('training-days').value = plan.training_days;
            
            // Set volume inputs
            document.querySelectorAll('.volume-input').forEach(input => {
                const muscle = input.dataset.muscle;
                const volume = plan.volumes[muscle];
                input.value = volume ? volume.weekly_sets : 0;
            });
            
            // Recalculate distribution
            calculateVolume();
        })
        .catch(error => {
            console.error('Error loading plan:', error);
            alert('Failed to load plan. Please try again.');
        });
}

function exportVolumePlan() {
    const trainingDays = parseInt(document.getElementById('training-days').value);
    const volumes = {};
    
    document.querySelectorAll('.volume-input').forEach(input => {
        volumes[input.dataset.muscle] = parseInt(input.value) || 0;
    });
    
    const data = {
        training_days: trainingDays,
        volumes: volumes
    };
    
    fetch('/api/save_volume_plan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('Volume plan saved successfully!');
            loadVolumeHistory(); // Refresh history
        } else {
            alert('Failed to save volume plan. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error saving plan:', error);
        alert('Failed to save plan. Please try again.');
    });
}

function displaySuggestions(suggestions) {
    const container = document.querySelector('.suggestions-container');
    container.innerHTML = '';
    
    suggestions.forEach(suggestion => {
        const card = document.createElement('div');
        card.className = `suggestion-card suggestion-${suggestion.type}`;
        card.innerHTML = `
            <p class="mb-0">${suggestion.message}</p>
        `;
        container.appendChild(card);
    });
    
    document.querySelector('.ai-suggestions-section').classList.remove('d-none');
}

function loadVolumeHistory() {
    fetch('/api/volume_history')
        .then(response => response.json())
        .then(history => {
            const tbody = document.getElementById('history-body');
            tbody.innerHTML = '';
            
            Object.entries(history).forEach(([id, data]) => {
                const row = document.createElement('tr');
                const totalVolume = Object.values(data.muscles)
                    .reduce((sum, muscle) => sum + muscle.weekly_sets, 0);
                
                row.innerHTML = `
                    <td>${new Date(data.created_at).toLocaleDateString()}</td>
                    <td>${data.training_days} days</td>
                    <td>${totalVolume} sets</td>
                    <td>
                        <button class="btn btn-sm btn-primary load-plan" 
                                data-plan-id="${id}">Load</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        });
}

function exportToExcel() {
    const trainingDays = parseInt(document.getElementById('training-days').value);
    const volumes = {};
    
    document.querySelectorAll('.volume-input').forEach(input => {
        volumes[input.dataset.muscle] = parseInt(input.value) || 0;
    });
    
    const data = {
        training_days: trainingDays,
        volumes: volumes
    };
    
    fetch('/api/export_volume_excel', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `volume_plan_${new Date().toISOString().slice(0,10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    })
    .catch(error => {
        console.error('Error exporting to Excel:', error);
        alert('Failed to export plan. Please try again.');
    });
} 