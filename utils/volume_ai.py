def generate_volume_suggestions(training_days, muscle_volumes):
    """
    Generate AI-based suggestions for volume optimization
    """
    suggestions = []
    
    # Check overall volume
    total_volume = sum(vol['weekly_sets'] for vol in muscle_volumes.values())
    if total_volume > training_days * 30:
        suggestions.append({
            'type': 'warning',
            'message': 'Total volume may be too high for recovery. Consider reducing volume for some muscle groups.'
        })
    
    # Check frequency distribution
    for muscle, data in muscle_volumes.items():
        sets_per_session = data['sets_per_session']
        if sets_per_session > 10:
            suggestions.append({
                'type': 'warning',
                'message': f'Volume for {muscle} ({sets_per_session} sets/session) may be too high per session. Consider spreading across more days.'
            })
        elif sets_per_session < 3 and data['weekly_sets'] > 0:
            suggestions.append({
                'type': 'info',
                'message': f'Volume for {muscle} could be consolidated into fewer sessions for better training effect.'
            })
    
    # Suggest balanced volume
    muscle_groups = {
        'push': ['Chest', 'Front-Shoulder', 'Triceps'],
        'pull': ['Latissimus-Dorsi', 'Rear-Shoulder', 'Biceps'],
        'legs': ['Quadriceps', 'Hamstrings', 'Calves']
    }
    
    for category, muscles in muscle_groups.items():
        category_volume = sum(muscle_volumes.get(m, {}).get('weekly_sets', 0) for m in muscles)
        if category_volume < 30:
            suggestions.append({
                'type': 'suggestion',
                'message': f'Consider increasing volume for {category} muscles for balanced development.'
            })
    
    return suggestions 