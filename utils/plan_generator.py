"""
Auto Starter Plan Generator.

Generates workout plans based on movement patterns, user preferences,
and evidence-based programming principles.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from utils.database import DatabaseHandler
from utils.logger import get_logger
from utils.movement_patterns import (
    MovementPattern,
    MovementSubpattern,
    MovementCategory,
    SlotDefinition,
    PrescriptionRules,
    SESSION_BLUEPRINTS,
    ENVIRONMENT_EQUIPMENT,
    HOME_BASIC_EQUIPMENT,
    classify_exercise,
    get_pattern_category,
)

logger = get_logger()


@dataclass
class GeneratorConfig:
    """Configuration for the plan generator."""
    
    # Required inputs
    training_days: int = 2  # 1-5
    environment: str = "gym"  # "gym" or "home"
    experience_level: str = "novice"  # "novice", "intermediate", "advanced"
    goal: str = "hypertrophy"  # "hypertrophy", "strength", "general"
    
    # Volume scaling (1.0 = normal, 0.8 = reduced for heavy lifters)
    volume_scale: float = 1.0
    
    # Optional constraints
    equipment_whitelist: Optional[List[str]] = None
    exclude_exercises: Optional[List[str]] = None
    preferred_exercises: Optional[Dict[str, List[str]]] = None  # pattern -> list of exercises
    movement_restrictions: Optional[Dict[str, bool]] = None  # e.g., {"no_overhead_press": True}
    target_muscle_groups: Optional[List[str]] = None  # Filter to specific muscle groups
    
    # Behavior flags
    beginner_consistency_mode: bool = True  # Keep same main lifts across sessions for novices
    persist: bool = True  # Insert into user_selection
    overwrite: bool = True  # Delete existing routines before inserting
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.training_days < 1 or self.training_days > 5:
            raise ValueError("training_days must be between 1 and 5")
        if self.environment not in ("gym", "home"):
            raise ValueError("environment must be 'gym' or 'home'")
        if self.experience_level not in ("novice", "intermediate", "advanced"):
            raise ValueError("experience_level must be 'novice', 'intermediate', or 'advanced'")
        if self.goal not in ("hypertrophy", "strength", "general"):
            raise ValueError("goal must be 'hypertrophy', 'strength', or 'general'")
        if self.volume_scale <= 0 or self.volume_scale > 2:
            raise ValueError("volume_scale must be between 0 and 2")


@dataclass
class ExerciseRow:
    """A single exercise entry in the generated plan."""
    routine: str
    exercise: str
    sets: int
    min_rep_range: int
    max_rep_range: int
    rir: int
    rpe: float
    weight: float
    exercise_order: int
    
    # Metadata (not persisted)
    pattern: Optional[str] = None
    role: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "routine": self.routine,
            "exercise": self.exercise,
            "sets": self.sets,
            "min_rep_range": self.min_rep_range,
            "max_rep_range": self.max_rep_range,
            "rir": self.rir,
            "rpe": self.rpe,
            "weight": self.weight,
            "exercise_order": self.exercise_order,
            "pattern": self.pattern,
            "role": self.role,
        }


@dataclass
class GeneratedPlan:
    """The complete generated workout plan."""
    routines: Dict[str, List[ExerciseRow]]
    config: GeneratorConfig
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "routines": {
                routine: [ex.to_dict() for ex in exercises]
                for routine, exercises in self.routines.items()
            },
            "config": {
                "training_days": self.config.training_days,
                "environment": self.config.environment,
                "experience_level": self.config.experience_level,
                "goal": self.config.goal,
                "volume_scale": self.config.volume_scale,
            },
        }
    
    @property
    def total_exercises(self) -> int:
        """Total number of exercises across all routines."""
        return sum(len(exercises) for exercises in self.routines.values())
    
    @property
    def total_sets_per_routine(self) -> Dict[str, int]:
        """Total sets per routine."""
        return {
            routine: sum(ex.sets for ex in exercises)
            for routine, exercises in self.routines.items()
        }


class ExerciseSelector:
    """Handles exercise selection based on patterns and constraints."""
    
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self._exercise_cache: Optional[List[Dict[str, Any]]] = None
        self._used_exercises: Set[str] = set()
    
    def _get_available_equipment(self) -> Set[str]:
        """Get equipment available based on environment and whitelist."""
        base_equipment = ENVIRONMENT_EQUIPMENT.get(self.config.environment, set())
        
        if self.config.equipment_whitelist:
            return base_equipment & set(self.config.equipment_whitelist)
        
        return base_equipment
    
    def _load_exercises(self) -> List[Dict[str, Any]]:
        """Load all exercises from database with their patterns."""
        if self._exercise_cache is not None:
            return self._exercise_cache
        
        query = """
            SELECT 
                exercise_name,
                primary_muscle_group,
                secondary_muscle_group,
                mechanic,
                utility,
                equipment,
                difficulty,
                movement_pattern,
                movement_subpattern
            FROM exercises
            WHERE exercise_name IS NOT NULL
            ORDER BY exercise_name
        """
        
        try:
            with DatabaseHandler() as db:
                results = db.fetch_all(query)
                self._exercise_cache = [dict(row) for row in results]
                return self._exercise_cache
        except Exception as e:
            logger.exception("Failed to load exercises from database")
            return []
    
    def _is_exercise_allowed(self, exercise: Dict[str, Any]) -> bool:
        """Check if an exercise passes all constraints."""
        exercise_name = exercise.get("exercise_name", "")
        
        # Check exclusion list
        if self.config.exclude_exercises:
            if exercise_name in self.config.exclude_exercises:
                return False
        
        # Check equipment constraints
        equipment = exercise.get("equipment")
        if equipment:
            available = self._get_available_equipment()
            if equipment not in available:
                return False
        
        # Check target muscle groups filter
        if self.config.target_muscle_groups:
            primary = (exercise.get("primary_muscle_group") or "").lower()
            secondary = (exercise.get("secondary_muscle_group") or "").lower()
            
            # Check if exercise targets any of the selected muscle groups
            target_lower = [m.lower() for m in self.config.target_muscle_groups]
            matches_target = any(
                target in primary or target in secondary or primary in target or secondary in target
                for target in target_lower
                if target and (primary or secondary)
            )
            
            if not matches_target and (primary or secondary):
                return False
        
        # Check difficulty level
        difficulty = (exercise.get("difficulty") or "").lower()
        level = self.config.experience_level
        
        difficulty_ranks = {"beginner": 1, "intermediate": 2, "advanced": 3}
        exercise_rank = difficulty_ranks.get(difficulty, 2)
        user_rank = difficulty_ranks.get(level, 1)
        
        # Novice can't do advanced exercises
        if level == "novice" and exercise_rank > 2:
            return False
        
        # Check movement restrictions
        if self.config.movement_restrictions:
            if self.config.movement_restrictions.get("no_overhead_press"):
                name_lower = exercise_name.lower()
                if any(kw in name_lower for kw in ["overhead", "military", "shoulder press"]):
                    return False
            
            if self.config.movement_restrictions.get("no_deadlift"):
                name_lower = exercise_name.lower()
                if "deadlift" in name_lower:
                    return False
        
        return True
    
    def _score_exercise(
        self,
        exercise: Dict[str, Any],
        slot: SlotDefinition,
        routine: str,
    ) -> float:
        """Score an exercise for a given slot. Higher is better."""
        score = 0.0
        exercise_name = exercise.get("exercise_name", "")
        
        # Check if exercise matches requested pattern
        stored_pattern = exercise.get("movement_pattern")
        if stored_pattern and stored_pattern == slot.pattern.value:
            score += 100
        else:
            # Try to classify on the fly
            pattern, subpattern = classify_exercise(
                exercise_name,
                exercise.get("primary_muscle_group"),
                exercise.get("mechanic"),
            )
            if pattern == slot.pattern:
                score += 100
            else:
                return -1000  # Pattern doesn't match
        
        # Subpattern preference bonus
        if slot.subpattern_preference:
            stored_subpattern = exercise.get("movement_subpattern")
            if stored_subpattern == slot.subpattern_preference.value:
                score += 30
            else:
                # Check by name keywords
                name_lower = exercise_name.lower()
                subpattern_keywords = {
                    MovementSubpattern.BILATERAL_SQUAT: ["squat", "leg press"],
                    MovementSubpattern.UNILATERAL_SQUAT: ["split", "lunge", "step"],
                    MovementSubpattern.HIP_THRUST: ["hip thrust", "bridge"],
                    MovementSubpattern.DEADLIFT: ["deadlift", "rdl", "romanian"],
                    MovementSubpattern.BICEP_CURL: ["curl", "bicep"],
                    MovementSubpattern.TRICEP_EXTENSION: ["extension", "pushdown", "skull"],
                    MovementSubpattern.LEG_CURL: ["leg curl", "hamstring"],
                    MovementSubpattern.LEG_EXTENSION: ["leg extension"],
                    MovementSubpattern.CALF_RAISE: ["calf"],
                    MovementSubpattern.LATERAL_RAISE: ["lateral", "side raise"],
                }
                keywords = subpattern_keywords.get(slot.subpattern_preference, [])
                if any(kw in name_lower for kw in keywords):
                    score += 20
        
        # Role-based scoring
        utility = (exercise.get("utility") or "").lower()
        mechanic = (exercise.get("mechanic") or "").lower()
        
        if slot.role == "main":
            # Prefer Basic utility for main lifts
            if utility == "basic":
                score += 20
            # Prefer Compound exercises for main lifts
            if mechanic == "compound":
                score += 15
        else:  # accessory
            # Auxiliary is fine for accessories
            if utility in ("auxiliary", "basic"):
                score += 10
            # Isolated exercises are good for isolation slots
            if slot.pattern in (MovementPattern.UPPER_ISOLATION, MovementPattern.LOWER_ISOLATION):
                if mechanic in ("isolated", "isolation"):
                    score += 15
        
        # Preferred exercises get a big boost
        if self.config.preferred_exercises:
            pattern_prefs = self.config.preferred_exercises.get(slot.pattern.value, [])
            if exercise_name in pattern_prefs:
                score += 50
        
        # Penalize already-used exercises (unless beginner consistency mode)
        if exercise_name in self._used_exercises:
            if self.config.beginner_consistency_mode and self.config.experience_level == "novice":
                # For novices, only penalize accessories, not main lifts
                if slot.role == "main":
                    score += 5  # Actually prefer consistency for main lifts
                else:
                    score -= 30
            else:
                score -= 40  # Variety is preferred for non-novices
        
        # Small random factor to break ties
        score += random.uniform(0, 5)
        
        return score
    
    def select_exercise(self, slot: SlotDefinition, routine: str) -> Optional[Dict[str, Any]]:
        """Select the best exercise for a given slot."""
        exercises = self._load_exercises()
        
        candidates = []
        for exercise in exercises:
            if not self._is_exercise_allowed(exercise):
                continue
            
            score = self._score_exercise(exercise, slot, routine)
            if score > -1000:  # Pattern matched
                candidates.append((score, exercise))
        
        if not candidates:
            logger.warning(
                "No suitable exercise found for pattern %s in routine %s",
                slot.pattern.value,
                routine,
            )
            return None
        
        # Sort by score (descending) and pick the best
        candidates.sort(key=lambda x: x[0], reverse=True)
        selected = candidates[0][1]
        
        # Mark as used
        self._used_exercises.add(selected["exercise_name"])
        
        return selected
    
    def reset_used_exercises(self):
        """Reset the used exercises tracker (between routines if needed)."""
        self._used_exercises.clear()


class PrescriptionCalculator:
    """Calculates sets, reps, and intensity for exercises."""
    
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.rules = PrescriptionRules()
    
    def get_sets(self, role: str) -> int:
        """Get number of sets for a given role."""
        base_sets = self.rules.SETS_BY_ROLE.get(
            self.config.experience_level,
            {"main": 3, "accessory": 2}
        ).get(role, 3)
        
        # Apply volume scaling
        scaled = int(round(base_sets * self.config.volume_scale))
        
        # Ensure minimum of 1 set
        return max(1, scaled)
    
    def get_rep_range(self, role: str, is_core: bool = False) -> Tuple[int, int]:
        """Get rep range for a given role and goal."""
        goal_ranges = self.rules.REP_RANGES.get(
            self.config.goal,
            self.rules.REP_RANGES["hypertrophy"]
        )
        
        if is_core:
            return goal_ranges.get("core", (10, 15))
        
        return goal_ranges.get(role, (8, 12))
    
    def get_rir(self, role: str) -> int:
        """Get RIR for a given role."""
        return self.rules.RIR_DEFAULTS.get(role, 2)
    
    def get_rpe(self, role: str) -> float:
        """Get RPE for a given role."""
        return self.rules.RPE_DEFAULTS.get(role, 8.0)
    
    def calculate_prescription(
        self,
        slot: SlotDefinition,
        exercise_name: str,
    ) -> Dict[str, Any]:
        """Calculate complete prescription for an exercise."""
        role = slot.role
        is_core = slot.pattern in (MovementPattern.CORE_STATIC, MovementPattern.CORE_DYNAMIC)
        
        # Core exercises use "core" role for RIR/RPE but "accessory" for sets
        rir_role = "core" if is_core else role
        sets_role = "accessory" if is_core else role
        
        min_reps, max_reps = self.get_rep_range(role, is_core)
        
        return {
            "sets": self.get_sets(sets_role),
            "min_rep_range": min_reps,
            "max_rep_range": max_reps,
            "rir": self.get_rir(rir_role),
            "rpe": self.get_rpe(rir_role),
            "weight": 0.0,  # Placeholder for new trainees
        }


class PlanGenerator:
    """Main class for generating workout plans."""
    
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.selector = ExerciseSelector(config)
        self.prescriber = PrescriptionCalculator(config)
    
    def _get_blueprint(self) -> Dict[str, List[SlotDefinition]]:
        """Get the session blueprint for the configured training days."""
        return SESSION_BLUEPRINTS.get(self.config.training_days, SESSION_BLUEPRINTS[2])
    
    def _build_routine(self, routine_name: str, slots: List[SlotDefinition]) -> List[ExerciseRow]:
        """Build a single routine from its slot definitions."""
        exercises = []
        
        for order, slot in enumerate(slots, start=1):
            selected = self.selector.select_exercise(slot, routine_name)
            
            if selected is None:
                logger.warning(
                    "Skipping slot %d (%s) in routine %s - no exercise found",
                    order,
                    slot.pattern.value,
                    routine_name,
                )
                continue
            
            prescription = self.prescriber.calculate_prescription(
                slot,
                selected["exercise_name"],
            )
            
            row = ExerciseRow(
                routine=routine_name,
                exercise=selected["exercise_name"],
                sets=prescription["sets"],
                min_rep_range=prescription["min_rep_range"],
                max_rep_range=prescription["max_rep_range"],
                rir=prescription["rir"],
                rpe=prescription["rpe"],
                weight=prescription["weight"],
                exercise_order=order,
                pattern=slot.pattern.value,
                role=slot.role,
            )
            exercises.append(row)
        
        return exercises
    
    def _adjust_volume(self, routines: Dict[str, List[ExerciseRow]]) -> Dict[str, List[ExerciseRow]]:
        """Adjust volume to meet session constraints."""
        rules = PrescriptionRules()
        
        for routine_name, exercises in routines.items():
            total_sets = sum(ex.sets for ex in exercises)
            
            # If over max, reduce accessory sets first
            while total_sets > rules.MAX_SETS_PER_SESSION:
                # Find accessories with sets > 1
                for ex in reversed(exercises):
                    if ex.role == "accessory" and ex.sets > 1:
                        ex.sets -= 1
                        total_sets -= 1
                        break
                else:
                    # No more accessories to reduce, reduce main lifts
                    for ex in reversed(exercises):
                        if ex.sets > 2:
                            ex.sets -= 1
                            total_sets -= 1
                            break
                    else:
                        break  # Can't reduce further
            
            # If under min, increase main lift sets
            while total_sets < rules.MIN_SETS_PER_SESSION:
                for ex in exercises:
                    if ex.role == "main" and ex.sets < 5:
                        ex.sets += 1
                        total_sets += 1
                        if total_sets >= rules.MIN_SETS_PER_SESSION:
                            break
                else:
                    break  # Can't increase further
        
        return routines
    
    def generate(self) -> GeneratedPlan:
        """Generate the complete workout plan."""
        blueprint = self._get_blueprint()
        routines: Dict[str, List[ExerciseRow]] = {}
        
        for routine_name, slots in blueprint.items():
            # For novice beginner consistency mode, only reset between
            # completely different routine types
            if not (self.config.beginner_consistency_mode and 
                    self.config.experience_level == "novice"):
                self.selector.reset_used_exercises()
            
            exercises = self._build_routine(routine_name, slots)
            routines[routine_name] = exercises
        
        # Adjust total volume if needed
        routines = self._adjust_volume(routines)
        
        return GeneratedPlan(routines=routines, config=self.config)
    
    def persist(self, plan: GeneratedPlan) -> Dict[str, int]:
        """Persist the generated plan to the database.
        
        Returns:
            Dictionary with routine names and number of exercises inserted
        """
        if not self.config.persist:
            return {}
        
        results = {}
        routine_names = list(plan.routines.keys())
        
        try:
            with DatabaseHandler() as db:
                # Handle overwrite behavior
                if self.config.overwrite:
                    # Delete existing rows for the routines we're about to create
                    for routine in routine_names:
                        # First delete related workout logs
                        db.execute_query(
                            """
                            DELETE FROM workout_log 
                            WHERE workout_plan_id IN (
                                SELECT id FROM user_selection WHERE routine = ?
                            )
                            """,
                            (routine,),
                        )
                        # Then delete the user_selection rows
                        db.execute_query(
                            "DELETE FROM user_selection WHERE routine = ?",
                            (routine,),
                        )
                else:
                    # Generate new routine names to avoid clobbering
                    # Check for existing routines and add suffix
                    for i, routine in enumerate(routine_names):
                        existing = db.fetch_one(
                            "SELECT COUNT(*) as count FROM user_selection WHERE routine = ?",
                            (routine,),
                        )
                        if existing and existing.get("count", 0) > 0:
                            # Find a unique suffix
                            suffix = 1
                            while True:
                                new_name = f"{routine}_gen{suffix}"
                                check = db.fetch_one(
                                    "SELECT COUNT(*) as count FROM user_selection WHERE routine = ?",
                                    (new_name,),
                                )
                                if not check or check.get("count", 0) == 0:
                                    # Update the routine name in the plan
                                    old_exercises = plan.routines.pop(routine)
                                    for ex in old_exercises:
                                        ex.routine = new_name
                                    plan.routines[new_name] = old_exercises
                                    break
                                suffix += 1
                
                # Get the current max exercise_order
                max_order_result = db.fetch_one(
                    "SELECT COALESCE(MAX(exercise_order), 0) AS max_order FROM user_selection"
                )
                base_order = 0
                if max_order_result is not None:
                    base_order = max_order_result.get("max_order", 0) or 0
                
                # Insert exercises
                insert_query = """
                    INSERT INTO user_selection 
                    (routine, exercise, sets, min_rep_range, max_rep_range, rir, rpe, weight, exercise_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                for routine_name, exercises in plan.routines.items():
                    inserted = 0
                    for ex in exercises:
                        base_order += 1
                        try:
                            db.execute_query(
                                insert_query,
                                (
                                    ex.routine,
                                    ex.exercise,
                                    ex.sets,
                                    ex.min_rep_range,
                                    ex.max_rep_range,
                                    ex.rir,
                                    ex.rpe,
                                    ex.weight,
                                    base_order,
                                ),
                            )
                            inserted += 1
                        except Exception as e:
                            logger.warning(
                                "Failed to insert exercise %s into routine %s: %s",
                                ex.exercise,
                                ex.routine,
                                e,
                            )
                    
                    results[routine_name] = inserted
                    logger.info(
                        "Inserted %d exercises into routine %s",
                        inserted,
                        routine_name,
                    )
        
        except Exception as e:
            logger.exception("Failed to persist generated plan")
            raise
        
        return results


def generate_starter_plan(
    training_days: int = 3,
    environment: str = "gym",
    experience_level: str = "novice",
    goal: str = "hypertrophy",
    volume_scale: float = 1.0,
    equipment_whitelist: Optional[List[str]] = None,
    exclude_exercises: Optional[List[str]] = None,
    preferred_exercises: Optional[Dict[str, List[str]]] = None,
    movement_restrictions: Optional[Dict[str, bool]] = None,
    target_muscle_groups: Optional[List[str]] = None,
    beginner_consistency_mode: bool = True,
    persist: bool = True,
    overwrite: bool = True,
) -> Dict[str, Any]:
    """
    Generate a starter workout plan.
    
    Args:
        training_days: Number of training sessions per week (1-5)
        environment: "gym" or "home"
        experience_level: "novice", "intermediate", or "advanced"
        goal: "hypertrophy", "strength", or "general"
        volume_scale: Volume multiplier (default 1.0)
        equipment_whitelist: List of allowed equipment types
        exclude_exercises: List of exercises to exclude
        preferred_exercises: Dict mapping pattern to preferred exercise names
        movement_restrictions: Dict of movement restrictions (e.g., {"no_overhead_press": True})
        target_muscle_groups: List of muscle groups to target (filter exercises)
        beginner_consistency_mode: Keep same main lifts for novices
        persist: Whether to save to database
        overwrite: Whether to overwrite existing routines
        
    Returns:
        Dictionary containing the generated plan and metadata
    """
    config = GeneratorConfig(
        training_days=training_days,
        environment=environment,
        experience_level=experience_level,
        goal=goal,
        volume_scale=volume_scale,
        equipment_whitelist=equipment_whitelist,
        exclude_exercises=exclude_exercises,
        preferred_exercises=preferred_exercises,
        movement_restrictions=movement_restrictions,
        target_muscle_groups=target_muscle_groups,
        beginner_consistency_mode=beginner_consistency_mode,
        persist=persist,
        overwrite=overwrite,
    )
    
    generator = PlanGenerator(config)
    plan = generator.generate()
    
    result = plan.to_dict()
    result["total_exercises"] = plan.total_exercises
    result["sets_per_routine"] = plan.total_sets_per_routine
    
    if persist:
        try:
            inserted = generator.persist(plan)
            result["persisted"] = True
            result["inserted_counts"] = inserted
        except Exception as e:
            result["persisted"] = False
            result["persist_error"] = str(e)
    else:
        result["persisted"] = False
    
    return result
