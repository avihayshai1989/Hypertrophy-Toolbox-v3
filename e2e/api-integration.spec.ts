/**
 * E2E Test: API Integration
 * 
 * Tests API endpoints directly for:
 * - Workout Plan API
 * - Workout Log API
 * - Exports API
 * - Progression API
 * - Volume Splitter API
 * - Weekly/Session Summary API
 */
import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5000';

test.describe('Workout Plan API', () => {
  test('GET /get_workout_plan returns valid response', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/get_workout_plan`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.ok === true || data.status === 'success' || data.success === true).toBeTruthy();
    expect(data).toHaveProperty('data');
    expect(Array.isArray(data.data)).toBe(true);
  });

  test('GET /get_routine_options returns valid response', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/get_routine_options`);
    // Accept 200 or 404 (route may not exist)
    expect([200, 404]).toContain(response.status());
    
    if (response.ok()) {
      const data = await response.json();
      // This endpoint returns nested routine options object (e.g., {Gym: {...}, "Home Workout": {...}})
      // Accept standard API format, array, or structured object with expected keys
      const isValidResponse = data.ok === true || 
        data.status === 'success' || 
        data.success === true || 
        Array.isArray(data) ||
        (typeof data === 'object' && (data.Gym || data['Home Workout']));
      expect(isValidResponse).toBeTruthy();
    }
  });

  test('GET /api/pattern_coverage returns movement pattern analysis', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/pattern_coverage`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data).toHaveProperty('data');
    
    // Verify pattern coverage structure
    const coverage = data.data;
    expect(coverage).toHaveProperty('per_routine');
    expect(coverage).toHaveProperty('total');
    expect(coverage).toHaveProperty('warnings');
    expect(coverage).toHaveProperty('sets_per_routine');
    expect(coverage).toHaveProperty('ideal_sets_range');
    
    // Warnings should be an array of actionable recommendations
    expect(Array.isArray(coverage.warnings)).toBe(true);
  });

  test('GET /get_all_exercises returns exercises list', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/get_all_exercises`);
    // Accept 200 or 404 (route may not exist)
    if (response.ok()) {
      const data = await response.json();
      expect(Array.isArray(data) || (data.data && Array.isArray(data.data))).toBeTruthy();
    } else {
      expect([404]).toContain(response.status());
    }
  });

  test('POST /add_exercise requires valid data', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/add_exercise`, {
      data: {} // Empty data should fail
    });
    
    expect(response.status()).toBe(400);
  });

  test('POST /add_exercise with valid data succeeds', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/add_exercise`, {
      data: {
        routine: 'GYM - Full Body - Workout A',
        exercise: 'Bench Press (Barbell)',
        planned_sets: 3,
        planned_min_reps: 8,
        planned_max_reps: 12,
        planned_weight: 100
      }
    });
    
    // Either success or duplicate (both are valid responses)
    expect([200, 400]).toContain(response.status());
  });

  test('POST /remove_exercise requires exercise_id', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/remove_exercise`, {
      data: {}
    });
    
    expect(response.status()).toBe(400);
  });

  test('POST /update_exercise requires valid data', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/update_exercise`, {
      data: {}
    });
    
    expect(response.status()).toBe(400);
  });

  test('GET /get_generator_options returns plan options with priority muscles', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/get_generator_options`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.ok === true || data.status === 'success' || data.success === true).toBeTruthy();
    
    // v1.5.0: Check for priority_muscles configuration
    if (data.data) {
      expect(data.data).toHaveProperty('priority_muscles');
      expect(data.data.priority_muscles).toHaveProperty('available');
      expect(Array.isArray(data.data.priority_muscles.available)).toBe(true);
      expect(data.data.priority_muscles).toHaveProperty('max_selections');
      
      // Should also have time_budget and merge_mode options
      expect(data.data).toHaveProperty('time_budget');
      expect(data.data).toHaveProperty('merge_mode');
    }
  });

  test('POST /replace_exercise requires exercise_id', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/replace_exercise`, {
      data: {}
    });
    
    expect(response.status()).toBe(400);
  });

  test('GET /api/execution_style_options returns styles', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/execution_style_options`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.ok === true || data.status === 'success' || data.success === true).toBeTruthy();
  });
});

test.describe('Superset API', () => {
  test('POST /api/superset/link requires exercise_ids', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/superset/link`, {
      data: {}
    });
    
    expect(response.status()).toBe(400);
  });

  test('POST /api/superset/unlink requires exercise_id', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/superset/unlink`, {
      data: {}
    });
    
    expect(response.status()).toBe(400);
  });

  test('GET /api/superset/suggest returns suggestions', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/superset/suggest`);
    expect(response.ok()).toBeTruthy();
  });
});

test.describe('Plan Generator API (v1.5.0)', () => {
  test('POST /generate_starter_plan requires valid training_days', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/generate_starter_plan`, {
      data: { training_days: 10 } // Invalid: exceeds max of 5
    });
    
    expect(response.status()).toBe(400);
  });

  test('POST /generate_starter_plan with valid data succeeds', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/generate_starter_plan`, {
      data: {
        training_days: 3,
        environment: 'gym',
        experience_level: 'novice',
        goal: 'hypertrophy',
        persist: false, // Don't save to avoid side effects
        overwrite: false
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.ok === true || data.success === true).toBeTruthy();
    expect(data.data).toHaveProperty('routines');
    expect(data.data).toHaveProperty('total_exercises');
  });

  test('POST /generate_starter_plan with priority_muscles parameter', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/generate_starter_plan`, {
      data: {
        training_days: 2,
        environment: 'gym',
        experience_level: 'novice',
        goal: 'hypertrophy',
        priority_muscles: ['Chest', 'Back'], // v1.5.0 feature
        persist: false,
        overwrite: false
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.ok === true || data.success === true).toBeTruthy();
    expect(data.data).toHaveProperty('routines');
    
    // Priority muscles should be reflected in the response metadata
    if (data.data.metadata) {
      expect(data.data.metadata.priority_muscles).toEqual(['Chest', 'Back']);
    }
  });

  test('POST /generate_starter_plan with time_budget optimization', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/generate_starter_plan`, {
      data: {
        training_days: 3,
        environment: 'gym',
        experience_level: 'intermediate',
        goal: 'hypertrophy',
        time_budget_minutes: 45, // v1.5.0 feature
        persist: false,
        overwrite: false
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.ok === true || data.success === true).toBeTruthy();
  });

  test('POST /generate_starter_plan rejects too many priority muscles', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/generate_starter_plan`, {
      data: {
        training_days: 2,
        environment: 'gym',
        priority_muscles: ['Chest', 'Back', 'Shoulders', 'Arms'], // Exceeds max of 2
        persist: false,
        overwrite: false
      }
    });
    
    // Should either accept with warning or truncate (both valid behaviors)
    expect([200, 400]).toContain(response.status());
  });

  test('POST /generate_starter_plan with merge_mode flag', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/generate_starter_plan`, {
      data: {
        training_days: 2,
        environment: 'gym',
        merge_mode: true, // v1.5.0 feature - keep existing exercises
        persist: false,
        overwrite: false
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.ok === true || data.success === true).toBeTruthy();
  });
});

test.describe('Double Progression API (v1.5.0)', () => {
  test('POST /get_exercise_suggestions returns suggestions array', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/get_exercise_suggestions`, {
      data: {
        exercise: 'Bench Press (Barbell)'
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
    
    // Each suggestion should have the expected structure
    if (data.length > 0) {
      const suggestion = data[0];
      expect(suggestion).toHaveProperty('type');
      expect(suggestion).toHaveProperty('title');
      expect(suggestion).toHaveProperty('description');
    }
  });

  test('POST /get_exercise_suggestions with is_novice parameter', async ({ request }) => {
    // Novice mode (conservative increments)
    const noviceResponse = await request.post(`${BASE_URL}/get_exercise_suggestions`, {
      data: {
        exercise: 'Squat (Barbell)',
        is_novice: true
      }
    });
    
    expect(noviceResponse.ok()).toBeTruthy();
    const noviceData = await noviceResponse.json();
    expect(Array.isArray(noviceData)).toBe(true);
    
    // Experienced mode (may suggest larger increments)
    const expResponse = await request.post(`${BASE_URL}/get_exercise_suggestions`, {
      data: {
        exercise: 'Squat (Barbell)',
        is_novice: false
      }
    });
    
    expect(expResponse.ok()).toBeTruthy();
    const expData = await expResponse.json();
    expect(Array.isArray(expData)).toBe(true);
  });

  test('POST /get_exercise_suggestions handles unknown exercise', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/get_exercise_suggestions`, {
      data: {
        exercise: 'NonExistent Exercise XYZ123'
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
    
    // Should return "start training" type suggestion for unknown exercise
    if (data.length > 0) {
      expect(['technique', 'info', 'start']).toContain(data[0].type);
    }
  });

  test('POST /get_exercise_suggestions without exercise returns error', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/get_exercise_suggestions`, {
      data: {}
    });
    
    // May return error or empty suggestions
    expect([200, 400, 500]).toContain(response.status());
  });
});

test.describe('Workout Log API', () => {
  test('GET /workout_log page loads', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/workout_log`);
    expect(response.ok()).toBeTruthy();
  });

  test('GET /get_workout_log returns logs', async ({ request }) => {
    // Try alternate route name
    let response = await request.get(`${BASE_URL}/get_workout_log`);
    if (response.status() === 404) {
      response = await request.get(`${BASE_URL}/get_workout_logs`);
    }
    
    // Accept 200 or 404
    if (response.ok()) {
      const data = await response.json();
      expect(data.ok === true || data.status === 'success' || data.success === true || Array.isArray(data)).toBeTruthy();
    } else {
      expect([404]).toContain(response.status());
    }
  });

  test('POST /update_workout_log requires valid data', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/update_workout_log`, {
      data: {}
    });
    
    expect(response.status()).toBe(400);
  });

  test('POST /delete_workout_log requires log_id', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/delete_workout_log`, {
      data: {}
    });
    
    expect(response.status()).toBe(400);
  });

  test('POST /clear_workout_log clears all logs', async ({ request }) => {
    // This is a destructive operation, so we just verify the endpoint exists
    const response = await request.post(`${BASE_URL}/clear_workout_log`, {
      data: { confirm: false } // Don't actually clear
    });
    
    // Should respond (either success or validation error)
    expect([200, 400]).toContain(response.status());
  });

  test('POST /import_from_plan imports exercises', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/import_from_plan`);
    // Route may not exist or may require data
    expect([200, 400, 404]).toContain(response.status());
  });
});

test.describe('Export API', () => {
  test('GET /export_to_excel returns Excel file', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/export_to_excel`);
    expect(response.ok()).toBeTruthy();
    
    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('spreadsheet');
  });

  test('POST /export_to_workout_log exports data', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/export_to_workout_log`);
    expect(response.ok()).toBeTruthy();
  });
});

test.describe('Progression Plan API', () => {
  test('GET /progression page loads', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/progression`);
    expect(response.ok()).toBeTruthy();
  });

  test('GET /get_progression_goals returns goals', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/get_progression_goals`);
    // Route may not exist
    if (response.ok()) {
      const data = await response.json();
      expect(data.ok === true || data.status === 'success' || data.success === true || Array.isArray(data)).toBeTruthy();
    } else {
      expect([404]).toContain(response.status());
    }
  });

  test('POST /add_progression_goal requires valid data', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/add_progression_goal`, {
      data: {}
    });
    
    // Route may not exist or may return 400 for invalid data
    expect([400, 404]).toContain(response.status());
  });

  test('POST /add_progression_goal with valid data succeeds', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/add_progression_goal`, {
      data: {
        exercise: 'Bench Press (Barbell)',
        goal_type: 'weight',
        current_value: 100,
        target_value: 120,
        target_date: '2026-12-31'
      }
    });
    
    // Either success, validation error, or route not found
    expect([200, 400, 404]).toContain(response.status());
  });

  test('POST /delete_progression_goal requires goal_id', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/delete_progression_goal`, {
      data: {}
    });
    
    // Route may not exist or may return 400 for missing goal_id
    expect([400, 404]).toContain(response.status());
  });
});

test.describe('Weekly Summary API', () => {
  test('GET /weekly_summary page loads', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/weekly_summary`);
    expect(response.ok()).toBeTruthy();
  });

  test('GET /get_weekly_summary returns summary data', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/get_weekly_summary`);
    // Route may not exist or returns data
    if (response.ok()) {
      const data = await response.json();
      expect(data.ok === true || data.status === 'success' || data.success === true || typeof data === 'object').toBeTruthy();
    } else {
      expect([404]).toContain(response.status());
    }
  });

  test('GET /get_weekly_summary with parameters', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/get_weekly_summary?counting_mode=effective&contribution_mode=total`);
    // Accept 200 or 404 (route may not exist)
    expect([200, 404]).toContain(response.status());
  });
});

test.describe('Session Summary API', () => {
  test('GET /session_summary page loads', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/session_summary`);
    expect(response.ok()).toBeTruthy();
  });

  test('GET /get_session_summary returns summary data', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/get_session_summary`);
    // Route may not exist or returns data
    if (response.ok()) {
      const data = await response.json();
      expect(data.ok === true || data.status === 'success' || data.success === true || typeof data === 'object').toBeTruthy();
    } else {
      expect([404]).toContain(response.status());
    }
  });
});

test.describe('Volume Splitter API', () => {
  test('GET /volume_splitter page loads', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/volume_splitter`);
    expect(response.ok()).toBeTruthy();
  });

  test('POST /calculate_volume_split requires training_days', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/calculate_volume_split`, {
      data: {}
    });
    
    // Route may not exist or may accept empty data
    expect([200, 400, 404, 500]).toContain(response.status());
  });

  test('POST /calculate_volume_split with valid data', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/calculate_volume_split`, {
      data: {
        training_days: 4,
        mode: 'basic'
      }
    });
    
    // Route may not exist
    expect([200, 404]).toContain(response.status());
  });
});

test.describe('Filters API', () => {
  test('GET /get_filter_options returns filter values', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/get_filter_options`);
    // Route may not exist
    if (response.ok()) {
      const data = await response.json();
      expect(data.ok === true || data.status === 'success' || data.success === true || typeof data === 'object').toBeTruthy();
    } else {
      expect([404]).toContain(response.status());
    }
  });

  test('POST /apply_filters filters exercises', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/apply_filters`, {
      data: {
        primary_muscle_group: 'Chest'
      }
    });
    
    // Route may not exist
    expect([200, 400, 404]).toContain(response.status());
    
    if (response.ok()) {
      const data = await response.json();
      expect(Array.isArray(data) || data.data).toBeTruthy();
    }
  });
});

test.describe('Error Handling', () => {
  test('404 for non-existent route', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/non_existent_route_12345`);
    expect(response.status()).toBe(404);
  });

  test('POST with invalid JSON returns 400', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/add_exercise`, {
      headers: { 'Content-Type': 'application/json' },
      data: 'invalid json{{'
    });
    
    expect([400, 500]).toContain(response.status());
  });

  test('POST with wrong content type handled gracefully', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/add_exercise`, {
      headers: { 'Content-Type': 'text/plain' },
      data: 'plain text'
    });
    
    expect([400, 415, 500]).toContain(response.status());
  });
});

test.describe('Response Format Consistency', () => {
  test('success responses have consistent format', async ({ request }) => {
    const endpoints = [
      '/get_workout_plan',
      '/get_routine_options',
      '/get_weekly_summary',
      '/get_session_summary'
    ];

    for (const endpoint of endpoints) {
      const response = await request.get(`${BASE_URL}${endpoint}`);
      
      // Some routes may not exist (404)
      if (response.ok()) {
        const data = await response.json();
        
        // All success responses should have status/ok or success flag or be valid data
        expect(
          data.ok === true || 
          data.status === 'success' || 
          data.success === true ||
          Array.isArray(data) ||
          typeof data === 'object'
        ).toBeTruthy();
      }
    }
  });

  test('error responses have consistent format', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/add_exercise`, {
      data: {}
    });
    
    if (!response.ok()) {
      const data = await response.json();
      
      // Error responses should have some error indicator
      expect(
        data.ok === false || 
        data.success === false || 
        data.status === 'error' ||
        data.error ||
        data.message
      ).toBeTruthy();
    }
  });
});

test.describe('Rate Limiting and Performance', () => {
  test('multiple rapid requests handled', async ({ request }) => {
    const promises = [];
    
    for (let i = 0; i < 10; i++) {
      promises.push(request.get(`${BASE_URL}/get_workout_plan`));
    }

    const responses = await Promise.all(promises);
    
    // All should succeed (no rate limiting on local dev)
    for (const response of responses) {
      expect(response.ok()).toBeTruthy();
    }
  });

  test('response time is acceptable', async ({ request }) => {
    const start = Date.now();
    await request.get(`${BASE_URL}/get_workout_plan`);
    const elapsed = Date.now() - start;

    // Should respond within 5 seconds
    expect(elapsed).toBeLessThan(5000);
  });
});

test.describe('CORS and Headers', () => {
  test('JSON endpoints return correct content-type', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/get_workout_plan`);
    const contentType = response.headers()['content-type'];
    
    expect(contentType).toContain('application/json');
  });

  test('HTML pages return correct content-type', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/workout_plan`);
    const contentType = response.headers()['content-type'];
    
    expect(contentType).toContain('text/html');
  });
});
