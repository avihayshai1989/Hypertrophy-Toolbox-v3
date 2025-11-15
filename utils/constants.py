"""Canonical constants used across the Hypertrophy Toolbox backend."""
from __future__ import annotations

MUSCLE_GROUPS = [
    "Rectus Abdominis",
    "Biceps",
    "Calves",
    "Chest",
    "External Obliques",
    "Forearms",
    "Front-Shoulder",  # TODO: evaluate collapsing into anatomical deltoid naming once UI migrates
    "Gluteus Maximus",
    "Hamstrings",
    "Hip-Adductors",
    "Latissimus Dorsi",
    "Lower Back",
    "Middle-Shoulder",
    "Middle-Traps",
    "Neck",
    "Quadriceps",
    "Rear-Shoulder",
    "Trapezius",
    "Triceps",
    "Upper Back",
]

FORCE = {
    "push": "Push",
    "pull": "Pull",
    "pull & push": "Push/Pull",
    "pull / push": "Push/Pull",
    "push & pull": "Push/Pull",
    "pull or push": "Push/Pull",
    "hold": "Hold",
    "dynamic to static": "Dynamic to Static",
}

MECHANIC = {
    "compound": "Compound",
    "isolation": "Isolated",
    "isolated": "Isolated",
}

UTILITY = {
    "basic": "Basic",
    "auxiliary": "Auxiliary",
    "basic or auxiliary": "Basic",
    "auxiliary or basic": "Auxiliary",
}

DIFFICULTY = {
    "beginner": "Beginner",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
}

EQUIPMENT_SYNONYMS = {
    "smith-machine": "Smith_Machine",
    "smith_machine": "Smith_Machine",
    "smith machine": "Smith_Machine",
}

MUSCLE_ALIAS = {
    # Core / anterior trunk
    "Rectus Abdominis": "Rectus Abdominis",
    "Abdominals": "Rectus Abdominis",
    "Abs": "Rectus Abdominis",
    "Lower Abs": "Rectus Abdominis",
    "Upper Abdominals": "Rectus Abdominis",
    # Latissimus / back
    "Latissimus Dorsi": "Latissimus Dorsi",
    "Latissimus_Dorsi": "Latissimus Dorsi",
    "Latissimus-Dorsi": "Latissimus Dorsi",
    "Latissimus": "Latissimus Dorsi",
    "Lats": "Latissimus Dorsi",
    "Lat": "Latissimus Dorsi",
    "Latissimus dorsi": "Latissimus Dorsi",
    # General back groupings
    "Back; General": "Lower Back",
    "Lower Back": "Lower Back",
    "Lowerback": "Lower Back",
    "Lower_Back": "Lower Back",
    "Upper Back": "Upper Back",
    "Upperback": "Upper Back",
    "Mid; Upper Back": "Upper Back",
    "Mid Upper Back": "Upper Back",
    "Mid/Upper Back": "Upper Back",  # TODO: confirm if this should remain a dedicated grouping
    "Mid/upper Back": "Upper Back",  # TODO: confirm if this should remain a dedicated grouping
    # Hip adductors & related
    "Hip Adductors": "Hip-Adductors",
    "Hip-Adductors": "Hip-Adductors",
    "Iliopsoas": "Hip-Adductors",
    "Adductors": "Hip-Adductors",
    # Glutes
    "Gluteus Maximus": "Gluteus Maximus",
    "Glutes": "Gluteus Maximus",
    "Glute": "Gluteus Maximus",
    "Gluteals": "Gluteus Maximus",
    # Hamstrings
    "Hamstrings": "Hamstrings",
    "Hamstring": "Hamstrings",
    "Hams": "Hamstrings",
    # Quadriceps
    "Quadriceps": "Quadriceps",
    "Quads": "Quadriceps",
    "Quadricep": "Quadriceps",
    # Calves
    "Calves": "Calves",
    "Gastrocnemius": "Calves",
    # Forearms
    "Forearms": "Forearms",
    # Neck
    "Neck": "Neck",
    # Shoulders
    "Front-Shoulder": "Front-Shoulder",
    "Front Shoulder": "Front-Shoulder",
    "Front-Shoulders": "Front-Shoulder",
    "Front Shoulders": "Front-Shoulder",
    "Front Delts": "Front-Shoulder",
    "Front Deltoids": "Front-Shoulder",
    "Anterior Delts": "Front-Shoulder",
    "Anterior Deltoids": "Front-Shoulder",
    "Deltoid; Anterior": "Front-Shoulder",
    "Middle-Shoulder": "Middle-Shoulder",
    "Middle Shoulder": "Middle-Shoulder",
    "Side Delts": "Middle-Shoulder",
    "Lateral Delts": "Middle-Shoulder",
    "Medial Delts": "Middle-Shoulder",
    "Deltoid; Lateral": "Middle-Shoulder",
    "Delts": "Middle-Shoulder",
    "Rear-Shoulder": "Rear-Shoulder",
    "Rear Shoulder": "Rear-Shoulder",
    "Rear Delts": "Rear-Shoulder",
    "Rear Deltoids": "Rear-Shoulder",
    "Posterior Delts": "Rear-Shoulder",
    "Deltoid; Posterior": "Rear-Shoulder",
    # Trapezius / traps
    "Trapezius": "Trapezius",
    "Traps": "Trapezius",
    "Trap": "Trapezius",
    "Middle-Traps": "Middle-Traps",
    "Middle Traps": "Middle-Traps",
    "Mid Traps": "Middle-Traps",
    "Traps (Mid-Back)": "Middle-Traps",
    # Obliques
    "External Obliques": "External Obliques",
    "Obliques": "External Obliques",
    "Oblique": "External Obliques",
    # Arms
    "Biceps": "Biceps",
    "Triceps": "Triceps",
}
