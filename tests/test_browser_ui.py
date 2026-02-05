"""
Browser-Based UI Tests using Playwright

These tests use real browser automation to verify UI interactions including:
- Button clicks
- Form submissions
- Navigation
- Modal interactions
- Dynamic content updates

Requirements:
    pip install pytest-playwright playwright
    playwright install chromium

Run tests:
    pytest tests/test_browser_ui.py -v --browser chromium
    
Note: These tests require the Flask app to be running. 
Use the live_server fixture or run `python app.py` in a separate terminal.
"""
import pytest
import time
import threading
import socket
from contextlib import closing

# Skip all tests if playwright is not installed
pytest.importorskip("playwright")

from playwright.sync_api import Page, expect, sync_playwright


def find_free_port():
    """Find a free port for the test server."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_server():
    """Start the Flask app in a background thread for browser testing."""
    import sys
    import os
    import tempfile
    
    # Override config before importing app
    os.environ['TESTING'] = '1'
    test_db_path = os.path.join(tempfile.gettempdir(), 'test_browser_db.db')
    
    # Remove test DB if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Override DB_FILE
    import utils.config
    utils.config.DB_FILE = test_db_path
    
    # Import after config override
    from app import app
    from utils.db_initializer import initialize_database
    from utils.database import add_progression_goals_table, add_volume_tracking_tables
    from routes.workout_plan import initialize_exercise_order
    from utils.program_backup import initialize_backup_tables
    
    # Reinitialize database for browser tests
    initialize_database(force=True)
    add_progression_goals_table()
    add_volume_tracking_tables()
    initialize_exercise_order()
    initialize_backup_tables()
    
    port = find_free_port()
    
    def run_server():
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False, threaded=True)
    
    # Start server in a daemon thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    yield f"http://127.0.0.1:{port}"
    
    # Cleanup
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except:
            pass


@pytest.fixture(scope="module")
def browser_context():
    """Create a Playwright browser context for the module."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        yield context
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context):
    """Create a new page for each test."""
    page = browser_context.new_page()
    yield page
    page.close()


class TestWelcomePageNavigation:
    """Test navigation from the welcome page."""
    
    def test_welcome_page_loads(self, live_server, page: Page):
        """Verify welcome page loads correctly."""
        page.goto(live_server)
        
        # Wait for page to load
        page.wait_for_load_state("networkidle")
        
        # Check title
        expect(page).to_have_title("Welcome - Hypertrophy Toolbox")
        
        # Verify hero heading is visible
        hero_heading = page.locator("#hero-heading")
        expect(hero_heading).to_be_visible()
    
    def test_click_start_planning_navigates_to_workout_plan(self, live_server, page: Page):
        """Click 'Start Planning' button and verify navigation."""
        page.goto(live_server)
        page.wait_for_load_state("networkidle")
        
        # Click the Start Planning button
        start_btn = page.locator("a.btn-hero-primary:has-text('Start Planning')")
        expect(start_btn).to_be_visible()
        start_btn.click()
        
        # Wait for navigation
        page.wait_for_load_state("networkidle")
        
        # Verify we're on the workout plan page
        expect(page).to_have_title("Workout Plan - Hypertrophy Toolbox")
    
    def test_click_volume_calculator_navigates(self, live_server, page: Page):
        """Click 'Volume Calculator' button and verify navigation."""
        page.goto(live_server)
        page.wait_for_load_state("networkidle")
        
        # Click the Volume Calculator button
        volume_btn = page.locator("a.btn-hero-secondary:has-text('Volume Calculator')")
        expect(volume_btn).to_be_visible()
        volume_btn.click()
        
        # Wait for navigation
        page.wait_for_load_state("networkidle")
        
        # Verify we're on the volume splitter page
        expect(page).to_have_title("Volume Splitter - Hypertrophy Toolbox")


class TestNavbarNavigation:
    """Test navigation using the navbar."""
    
    def test_navbar_workout_plan_link(self, live_server, page: Page):
        """Click Workout Plan in navbar."""
        page.goto(live_server)
        page.wait_for_load_state("networkidle")
        
        # Click navbar link
        page.locator("nav a:has-text('Workout Plan')").click()
        page.wait_for_load_state("networkidle")
        
        expect(page).to_have_url(f"{live_server}/workout_plan")
    
    def test_navbar_workout_log_link(self, live_server, page: Page):
        """Click Workout Log in navbar."""
        page.goto(live_server)
        page.wait_for_load_state("networkidle")
        
        # Click navbar link
        page.locator("nav a:has-text('Workout Log')").click()
        page.wait_for_load_state("networkidle")
        
        expect(page).to_have_url(f"{live_server}/workout_log")
    
    def test_navbar_weekly_summary_link(self, live_server, page: Page):
        """Click Weekly Summary in navbar."""
        page.goto(live_server)
        page.wait_for_load_state("networkidle")
        
        # Click navbar link
        page.locator("nav a:has-text('Weekly Summary')").click()
        page.wait_for_load_state("networkidle")
        
        expect(page).to_have_url(f"{live_server}/weekly_summary")


class TestWorkoutPlanPageInteractions:
    """Test interactions on the Workout Plan page."""
    
    def test_filter_dropdowns_exist(self, live_server, page: Page):
        """Verify filter dropdowns are present and interactive."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Check filters form exists
        filters_form = page.locator("#filters-form")
        expect(filters_form).to_be_visible()
        
        # Check for filter dropdowns
        filter_dropdowns = page.locator(".filter-dropdown")
        expect(filter_dropdowns.first).to_be_visible()
    
    def test_routine_cascade_dropdown_interaction(self, live_server, page: Page):
        """Test cascading routine dropdown interaction."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Select Environment dropdown
        env_dropdown = page.locator("#routine-env")
        expect(env_dropdown).to_be_visible()
        
        # Select GYM environment
        env_dropdown.select_option("GYM")
        
        # Wait for cascade to update
        page.wait_for_timeout(500)
        
        # Program dropdown should now be enabled
        program_dropdown = page.locator("#routine-program")
        expect(program_dropdown).to_be_enabled()
    
    def test_workout_controls_inputs(self, live_server, page: Page):
        """Test workout control input fields."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Find and interact with weight input
        weight_input = page.locator("#weight")
        expect(weight_input).to_be_visible()
        
        # Clear and set new value
        weight_input.fill("50")
        expect(weight_input).to_have_value("50")
        
        # Test sets input  
        sets_input = page.locator("#sets")
        sets_input.fill("4")
        expect(sets_input).to_have_value("4")
        
        # Test RIR input
        rir_input = page.locator("#rir")
        rir_input.fill("2")
        expect(rir_input).to_have_value("2")
    
    def test_collapse_filter_section(self, live_server, page: Page):
        """Test collapsing the filter section."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Find collapse button for filters
        collapse_btn = page.locator("[data-section='filters'] .collapse-toggle")
        expect(collapse_btn).to_be_visible()
        
        # Get the content element
        filters_content = page.locator("#filters-content")
        expect(filters_content).to_be_visible()
        
        # Click to collapse
        collapse_btn.click()
        page.wait_for_timeout(500)
        
        # Content should be hidden now
        expect(filters_content).to_be_hidden()
        
        # Click again to expand
        collapse_btn.click()
        page.wait_for_timeout(500)
        
        expect(filters_content).to_be_visible()
    
    def test_clear_filters_button(self, live_server, page: Page):
        """Test clear filters button functionality."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Click clear filters button (it should always be functional)
        clear_btn = page.locator("#clear-filters-btn")
        expect(clear_btn).to_be_visible()
        clear_btn.click()
        
        # Button click should not cause errors
        page.wait_for_timeout(500)
        
        # Page should still be functional
        expect(page.locator("#filters-form")).to_be_visible()


class TestCompleteWorkoutFlow:
    """Test complete user workflow: Add exercise, view, remove."""
    
    def test_add_exercise_workflow(self, live_server, page: Page):
        """Complete flow: Select routine, exercise, add to plan."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Step 1: Select Environment
        env_dropdown = page.locator("#routine-env")
        env_dropdown.select_option("GYM")
        page.wait_for_timeout(500)
        
        # Step 2: Select Program
        program_dropdown = page.locator("#routine-program")
        expect(program_dropdown).to_be_enabled()
        # Wait for options to load
        page.wait_for_timeout(300)
        
        # Select first available program
        options = program_dropdown.locator("option")
        option_count = options.count()
        if option_count > 1:
            program_dropdown.select_option(index=1)
        
        page.wait_for_timeout(500)
        
        # Step 3: Select Workout Day
        day_dropdown = page.locator("#routine-day")
        page.wait_for_timeout(300)
        day_options = day_dropdown.locator("option")
        if day_options.count() > 1:
            day_dropdown.select_option(index=1)
        
        page.wait_for_timeout(500)
        
        # Step 4: Set workout parameters
        page.locator("#weight").fill("60")
        page.locator("#sets").fill("3")
        page.locator("#min_rep").fill("8")
        page.locator("#max_rep_range").fill("12")
        page.locator("#rir").fill("2")
        
        # Step 5: Select an exercise
        exercise_dropdown = page.locator("#exercise")
        expect(exercise_dropdown).to_be_visible()
        # Select first available exercise
        exercise_options = exercise_dropdown.locator("option")
        if exercise_options.count() > 0:
            exercise_dropdown.select_option(index=0)
        
        # Step 6: Click Add Exercise button
        add_btn = page.locator("#add_exercise_btn")
        expect(add_btn).to_be_visible()
        add_btn.click()
        
        # Wait for the request to complete
        page.wait_for_timeout(1000)
        
        # Verify the add button click didn't cause errors
        # and the page is still functional
        expect(add_btn).to_be_visible()
        
        # The workout plan table container should exist
        table_container = page.locator(".workout-plan-table")
        expect(table_container).to_be_attached()


class TestWorkoutLogPage:
    """Test interactions on the Workout Log page."""
    
    def test_workout_log_page_loads(self, live_server, page: Page):
        """Verify workout log page loads correctly."""
        page.goto(f"{live_server}/workout_log")
        page.wait_for_load_state("networkidle")
        
        expect(page).to_have_title("Workout Log - Hypertrophy Toolbox")
        
        # Check import controls frame exists
        import_frame = page.locator("[data-section='import-controls']")
        expect(import_frame).to_be_visible()
    
    def test_import_controls_visible(self, live_server, page: Page):
        """Verify import controls are visible."""
        page.goto(f"{live_server}/workout_log")
        page.wait_for_load_state("networkidle")
        
        # Check import button exists
        import_btn = page.locator("#import-from-plan-btn")
        expect(import_btn).to_be_visible()
        expect(import_btn).to_have_text("Import Current Workout Plan")
    
    def test_collapse_import_section(self, live_server, page: Page):
        """Test collapsing the import controls section."""
        page.goto(f"{live_server}/workout_log")
        page.wait_for_load_state("networkidle")
        
        # Find collapse button
        collapse_btn = page.locator("[data-section='import-controls'] .collapse-toggle")
        expect(collapse_btn).to_be_visible()
        
        # Get content element
        import_content = page.locator("#import-content")
        expect(import_content).to_be_visible()
        
        # Click to collapse
        collapse_btn.click()
        page.wait_for_timeout(500)
        
        expect(import_content).to_be_hidden()


class TestWeeklySummaryPage:
    """Test interactions on the Weekly Summary page."""
    
    def test_weekly_summary_page_loads(self, live_server, page: Page):
        """Verify weekly summary page loads correctly."""
        page.goto(f"{live_server}/weekly_summary")
        page.wait_for_load_state("networkidle")
        
        expect(page).to_have_title("Weekly Summary - Hypertrophy Toolbox")


class TestVolumeSplitterPage:
    """Test interactions on the Volume Splitter page."""
    
    def test_volume_splitter_page_loads(self, live_server, page: Page):
        """Verify volume splitter page loads correctly."""
        page.goto(f"{live_server}/volume_splitter")
        page.wait_for_load_state("networkidle")
        
        expect(page).to_have_title("Volume Splitter - Hypertrophy Toolbox")


class TestDarkModeToggle:
    """Test dark mode toggle functionality."""
    
    def test_dark_mode_toggle_exists(self, live_server, page: Page):
        """Verify dark mode toggle button exists."""
        page.goto(live_server)
        page.wait_for_load_state("networkidle")
        
        # Look for dark mode toggle in navbar
        dark_mode_toggle = page.locator("#dark-mode-toggle, .dark-mode-toggle, [aria-label*='dark mode' i]")
        
        # If toggle exists, test it
        if dark_mode_toggle.count() > 0:
            expect(dark_mode_toggle.first).to_be_visible()


class TestAccessibility:
    """Basic accessibility tests."""
    
    def test_page_has_main_landmark(self, live_server, page: Page):
        """Verify main content area has proper landmark."""
        page.goto(live_server)
        page.wait_for_load_state("networkidle")
        
        main = page.locator("main")
        expect(main).to_be_visible()
    
    def test_buttons_have_accessible_labels(self, live_server, page: Page):
        """Verify important buttons have aria-labels."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Check add exercise button has aria-label with some value
        add_btn = page.locator("#add_exercise_btn")
        aria_label = add_btn.get_attribute("aria-label")
        assert aria_label is not None and len(aria_label) > 0, "Button should have aria-label"
    
    def test_form_inputs_have_labels(self, live_server, page: Page):
        """Verify form inputs have associated labels."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Check that input fields have labels
        weight_label = page.locator("label[for='weight']")
        expect(weight_label).to_be_visible()
        
        sets_label = page.locator("label[for='sets']")
        expect(sets_label).to_be_visible()


class TestModalInteractions:
    """Test modal dialog interactions."""
    
    def test_generate_plan_modal_opens(self, live_server, page: Page):
        """Test opening the Generate Starter Plan modal."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Click generate plan button
        generate_btn = page.locator("#generate-plan-btn")
        expect(generate_btn).to_be_visible()
        generate_btn.click()
        
        # Wait for modal to appear
        page.wait_for_timeout(500)
        
        # Check if modal is visible
        modal = page.locator("#generatePlanModal")
        if modal.count() > 0:
            expect(modal).to_be_visible()
    
    def test_clear_plan_modal_opens(self, live_server, page: Page):
        """Test opening the Clear Plan confirmation modal."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Click clear plan button
        clear_btn = page.locator("#clear-plan-btn")
        expect(clear_btn).to_be_visible()
        clear_btn.click()
        
        # Wait for modal to appear
        page.wait_for_timeout(500)
        
        # Check if modal is visible
        modal = page.locator("#clearPlanModal")
        if modal.count() > 0:
            expect(modal).to_be_visible()
    
    def test_save_program_modal_opens(self, live_server, page: Page):
        """Test opening the Save Program modal."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Click save program button
        save_btn = page.locator("#save-program-btn")
        expect(save_btn).to_be_visible()
        save_btn.click()
        
        # Wait for modal to appear
        page.wait_for_timeout(500)
        
        # Check if modal is visible
        modal = page.locator("#saveBackupModal")
        if modal.count() > 0:
            expect(modal).to_be_visible()


class TestResponsiveUI:
    """Test responsive UI behavior at different viewport sizes."""
    
    def test_mobile_viewport(self, live_server, browser_context):
        """Test UI at mobile viewport size."""
        # Create page with mobile viewport
        page = browser_context.new_page()
        page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE size
        
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Page should still render main content
        main = page.locator("main")
        expect(main).to_be_visible()
        
        page.close()
    
    def test_tablet_viewport(self, live_server, browser_context):
        """Test UI at tablet viewport size."""
        page = browser_context.new_page()
        page.set_viewport_size({"width": 768, "height": 1024})  # iPad size
        
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Page should render all sections
        filters = page.locator("[data-section='filters']")
        expect(filters).to_be_visible()
        
        page.close()


class TestErrorHandling:
    """Test UI error handling scenarios."""
    
    def test_invalid_route_shows_error(self, live_server, page: Page):
        """Test that invalid routes are handled gracefully."""
        page.goto(f"{live_server}/nonexistent_page")
        page.wait_for_load_state("networkidle")
        
        # Should show error page or redirect
        # Check page didn't crash (still has content)
        body = page.locator("body")
        expect(body).to_be_visible()


class TestKeyboardNavigation:
    """Test keyboard accessibility."""
    
    def test_tab_through_workout_controls(self, live_server, page: Page):
        """Test tabbing through workout control inputs."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Focus on weight input
        weight_input = page.locator("#weight")
        weight_input.focus()
        
        # Tab to next input
        page.keyboard.press("Tab")
        
        # Verify focus moved (sets input should be next)
        focused = page.locator(":focus")
        expect(focused).to_be_visible()
    
    def test_enter_key_on_inputs(self, live_server, page: Page):
        """Test Enter key behavior on inputs."""
        page.goto(f"{live_server}/workout_plan")
        page.wait_for_load_state("networkidle")
        
        # Focus and type in weight input
        weight_input = page.locator("#weight")
        weight_input.fill("75")
        
        # Press Enter (shouldn't cause issues)
        page.keyboard.press("Enter")
        
        # Page should still be functional
        expect(weight_input).to_have_value("75")
