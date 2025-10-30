def get_volume_class(total_sets):
    """Return the CSS class for volume classification."""
    if total_sets < 10:
        return "low-volume"
    elif total_sets < 20:
        return "medium-volume"
    elif total_sets < 30:
        return "high-volume"
    else:
        return "ultra-volume"

def get_volume_label(total_sets):
    """Return the text label for volume classification."""
    if total_sets < 10:
        return "Low Volume"
    elif total_sets < 20:
        return "Medium Volume"
    elif total_sets < 30:
        return "High Volume"
    else:
        return "Ultra Volume"

def get_volume_tooltip(volume_label, total_sets):
    ranges = {
        'Low Volume': 'Below 10 sets',
        'Medium Volume': '10-19 sets',
        'High Volume': '20-29 sets',
        'Ultra Volume': '30+ sets'
    }
    return f"{volume_label}: {ranges[volume_label]} (Current: {total_sets} sets)"

def get_category_tooltip(category):
    tooltips = {
        'Mechanic': 'Classification based on joint involvement in the exercise',
        'Utility': 'Classification based on exercise role in training',
        'Force': 'Classification based on primary force direction'
    }
    return tooltips.get(category, '')

def get_subcategory_tooltip(category, subcategory):
    tooltips = {
        'Mechanic': {
            'Compound': 'Multi-joint exercises like squats and bench press',
            'Isolated': 'Single-joint exercises focusing on specific muscles'
        },
        'Utility': {
            'Auxiliary': 'Supportive exercises that complement main lifts',
            'Basic': 'Foundational exercises targeting major muscle groups'
        },
        'Force': {
            'Push': 'Exercises involving pushing motions away from body',
            'Pull': 'Exercises involving pulling motions toward body'
        }
    }
    return tooltips.get(category, {}).get(subcategory, '') 