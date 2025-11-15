def generate_volume_suggestions(training_days, muscle_volumes, mode="basic"):
    """Generate AI-based suggestions for volume optimization."""
    suggestions = []

    normalized_mode = (mode or "basic").lower()
    if normalized_mode not in {"basic", "advanced"}:
        normalized_mode = "basic"

    # Check overall volume
    total_volume = sum(vol.get('weekly_sets', 0) for vol in muscle_volumes.values())
    if total_volume > training_days * 30:
        suggestions.append({
            'type': 'warning',
            'message': 'Total volume may be too high for recovery. Consider reducing volume for some muscle groups.'
        })

    # Check frequency distribution
    for muscle, data in muscle_volumes.items():
        sets_per_session = data.get('sets_per_session', 0)
        weekly_sets = data.get('weekly_sets', 0)
        if sets_per_session > 10:
            suggestions.append({
                'type': 'warning',
                'message': f'Volume for {muscle} ({sets_per_session} sets/session) may be too high per session. Consider spreading across more days.'
            })
        elif sets_per_session < 3 and weekly_sets > 0:
            suggestions.append({
                'type': 'info',
                'message': f'Volume for {muscle} could be consolidated into fewer sessions for better training effect.'
            })

    if normalized_mode == "basic":
        muscle_groups = {
            'push': ['Chest', 'Front-Shoulder', 'Triceps'],
            'pull': ['Latissimus-Dorsi', 'Rear-Shoulder', 'Biceps'],
            'legs': ['Quadriceps', 'Hamstrings', 'Calves']
        }
    else:
        muscle_groups = {
            'push': [
                'upper-pectoralis', 'mid-lower-pectoralis',
                'anterior-deltoid', 'lateral-deltoid',
                'lateral-head-triceps', 'long-head-triceps', 'medial-head-triceps'
            ],
            'pull': [
                'posterior-deltoid', 'lats',
                'upper-trapezius', 'traps-middle', 'lower-trapezius',
                'short-head-biceps', 'long-head-biceps',
                'wrist-extensors', 'wrist-flexors'
            ],
            'legs': [
                'rectus-femoris', 'inner-quadriceps', 'outer-quadriceps',
                'medial-hamstrings', 'lateral-hamstrings',
                'gluteus-maximus', 'gluteus-medius',
                'soleus', 'tibialis', 'gastrocnemius',
                'groin', 'inner-thigh'
            ]
        }

    for category, muscles in muscle_groups.items():
        category_volume = sum(
            (muscle_volumes.get(label, {}) or {}).get('weekly_sets', 0)
            for label in muscles
            if label in muscle_volumes
        )
        if category_volume < 30:
            suggestions.append({
                'type': 'suggestion',
                'message': f'Consider increasing volume for {category} muscles for balanced development.'
            })

    return suggestions