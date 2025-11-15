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
    "Abdominals": "Rectus Abdominis",
    "Abs": "Rectus Abdominis",
    "Rectus Abdominis": "Rectus Abdominis",
    "Gastrocnemius": "Calves",
    "Glutes": "Gluteus Maximus",
    "Gluteus Maximus": "Gluteus Maximus",
    "Hip Adductors": "Hip-Adductors",
    "Iliopsoas": "Hip-Adductors",
    "Deltoid; Anterior": "Front-Shoulder",
    "Deltoid; Posterior": "Rear-Shoulder",
    "Deltoid; Lateral": "Middle-Shoulder",
    "Delts": "Middle-Shoulder",
    "External Obliques": "External Obliques",
    "Obliques": "External Obliques",
    "Trapezius": "Trapezius",
    "Traps": "Trapezius",
    "Back; General": "Lower Back",
    "Mid; Upper Back": "Upper Back",
    "Latissimus Dorsi": "Latissimus Dorsi",
    "Latissimus_Dorsi": "Latissimus Dorsi",
    "Latissimus-Dorsi": "Latissimus Dorsi",
}
