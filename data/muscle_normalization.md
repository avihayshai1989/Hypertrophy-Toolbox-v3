# Muscle Normalization Canonical Map

This reference captures the canonical muscle buckets used across the API, database scripts, and reporting dashboards. Update this file (and `utils/constants.py::MUSCLE_ALIAS`) whenever new aliases are discovered.

| Canonical Name | Collapsed Aliases | Notes |
| --- | --- | --- |
| Rectus Abdominis | abs, abdominals, lower abs, upper abdominals |  |
| External Obliques | oblique, obliques |  |
| Latissimus Dorsi | lat, lats, latissimus, latissimus-dorsi, latissimus_dorsi |  |
| Lower Back | back; general, lowerback, lower_back |  |
| Upper Back | upperback, mid; upper back, mid upper back | TODO: confirm whether `Mid/Upper Back` should remain a dedicated bucket |
| Hip-Adductors | hip adductors, hip-adductors, iliopsoas, adductors |  |
| Gluteus Maximus | glute, gluteals, glutes, gluteus maximus |  |
| Hamstrings | hamstring, hams |  |
| Quadriceps | quadricep, quads |  |
| Calves | gastrocnemius |  |
| Forearms | forearms |  |
| Front-Shoulder | anterior delts, front delts, front shoulders |  |
| Middle-Shoulder | delts, lateral delts, medial delts, side delts |  |
| Rear-Shoulder | posterior delts, rear delts, rear shoulders |  |
| Middle-Traps | mid traps, traps (mid-back) |  |
| Trapezius | trap, traps |  |
| Neck | neck |  |
| Biceps | biceps |  |
| Triceps | triceps |  |

## Maintenance Checklist

- [ ] Confirm whether `Mid/Upper Back` should collapse into `Upper Back` or remain a separate reporting group (consult coaching/analytics team).
- [ ] Audit recent normalization logs (`logs/muscle_normalization.md`) for new aliases and backfill this table + `MUSCLE_ALIAS`.
- [ ] When the canonical list changes, update `MUSCLE_GROUPS`, regeneration scripts, and the `test_canonical_primary_mapping` regression.
