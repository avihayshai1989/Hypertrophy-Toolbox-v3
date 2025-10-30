import { showToast } from './toast.js';

export async function exportToExcel() {
    try {
        const response = await fetch('/export_to_excel', {
            method: 'GET'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to export to Excel');
        }

        // Get filename from Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        const filename = contentDisposition
            ? contentDisposition.split('filename=')[1].replace(/"/g, '')
            : 'workout_plan.xlsx';

        // Create blob from response
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        
        // Create temporary link and trigger download
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast('Successfully exported to Excel');
    } catch (error) {
        console.error('Error exporting to Excel:', error);
        showToast('Failed to export to Excel', true);
    }
}

export async function exportToWorkoutLog() {
    try {
        const response = await fetch('/export_to_workout_log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to export to workout log');
        }

        showToast('Successfully exported to workout log');
        
        // Redirect to workout log page after short delay
        setTimeout(() => {
            window.location.href = '/workout_log';
        }, 1500);
    } catch (error) {
        console.error('Error exporting to workout log:', error);
        showToast('Failed to export to workout log', true);
    }
}

export async function exportSummary(type = 'weekly') {
    try {
        const response = await fetch(`/export_${type}_summary`, {
            method: 'GET'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || `Failed to export ${type} summary`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${type}_summary.xlsx`;
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast(`Successfully exported ${type} summary`);
    } catch (error) {
        console.error(`Error exporting ${type} summary:`, error);
        showToast(`Failed to export ${type} summary`, true);
    }
} 