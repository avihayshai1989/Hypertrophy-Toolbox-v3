function updateMuscleStats(data) {
    data.forEach(stat => {
        if (stat.muscle_type === 'primary' ||
            stat.muscle_type === 'secondary' ||
            stat.muscle_type === 'tertiary' ||
            stat.muscle_type === 'advanced_isolated') {
            // Update stats...
        }
    });
} 