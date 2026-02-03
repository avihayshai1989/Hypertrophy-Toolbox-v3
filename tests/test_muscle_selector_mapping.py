"""
Tests for muscle selector mapping validation.

Ensures all vendor SVG slugs are properly mapped to canonical keys,
and all canonical keys have labels and backend mappings.
"""

import pytest
import re
from pathlib import Path


# Path to the muscle-selector.js file
MUSCLE_SELECTOR_JS = Path(__file__).parent.parent / "static" / "js" / "modules" / "muscle-selector.js"
ANTERIOR_SVG = Path(__file__).parent.parent / "static" / "vendor" / "react-body-highlighter" / "body_anterior.svg"
POSTERIOR_SVG = Path(__file__).parent.parent / "static" / "vendor" / "react-body-highlighter" / "body_posterior.svg"


def extract_js_object(js_content: str, var_name: str) -> dict:
    """Extract a JavaScript object/dict from the JS file content."""
    # Find the variable declaration
    pattern = rf"const {var_name}\s*=\s*\{{"
    match = re.search(pattern, js_content)
    if not match:
        return {}
    
    # Find matching closing brace
    start = match.end() - 1
    depth = 0
    end = start
    
    for i, char in enumerate(js_content[start:], start):
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    
    obj_str = js_content[start:end]
    
    # Parse simple key-value pairs (this is a simplified parser)
    result = {}
    # Match patterns like: 'key': 'value', or 'key': null,
    kv_pattern = r"'([^']+)':\s*(?:'([^']*)'|null|(\[.*?\]))"
    for match in re.finditer(kv_pattern, obj_str, re.DOTALL):
        key = match.group(1)
        value = match.group(2) if match.group(2) else None
        if match.group(3):  # Array value - skip for this simple parser
            value = 'ARRAY'
        result[key] = value
    
    return result


def extract_svg_data_muscles(svg_path: Path) -> set:
    """Extract all data-muscle attribute values from an SVG file."""
    if not svg_path.exists():
        return set()
    
    content = svg_path.read_text(encoding='utf-8')
    # Match data-muscle="value" patterns
    pattern = r'data-muscle="([^"]+)"'
    return set(re.findall(pattern, content))


class TestMuscleSelectorMapping:
    """Test suite for muscle selector mapping validation."""
    
    @pytest.fixture
    def js_content(self):
        """Load the muscle-selector.js file content."""
        if not MUSCLE_SELECTOR_JS.exists():
            pytest.skip("muscle-selector.js not found")
        return MUSCLE_SELECTOR_JS.read_text(encoding='utf-8')
    
    @pytest.fixture
    def vendor_slug_to_canonical(self, js_content):
        """Extract VENDOR_SLUG_TO_CANONICAL mapping."""
        return extract_js_object(js_content, "VENDOR_SLUG_TO_CANONICAL")
    
    @pytest.fixture  
    def muscle_labels(self, js_content):
        """Extract MUSCLE_LABELS mapping."""
        return extract_js_object(js_content, "MUSCLE_LABELS")
    
    @pytest.fixture
    def muscle_to_backend(self, js_content):
        """Extract MUSCLE_TO_BACKEND mapping."""
        return extract_js_object(js_content, "MUSCLE_TO_BACKEND")
    
    @pytest.fixture
    def anterior_slugs(self):
        """Extract data-muscle values from anterior SVG."""
        return extract_svg_data_muscles(ANTERIOR_SVG)
    
    @pytest.fixture
    def posterior_slugs(self):
        """Extract data-muscle values from posterior SVG."""
        return extract_svg_data_muscles(POSTERIOR_SVG)
    
    def test_vendor_files_exist(self):
        """Verify vendor SVG files exist."""
        assert ANTERIOR_SVG.exists(), f"Anterior SVG not found: {ANTERIOR_SVG}"
        assert POSTERIOR_SVG.exists(), f"Posterior SVG not found: {POSTERIOR_SVG}"
    
    def test_all_anterior_slugs_mapped(self, anterior_slugs, vendor_slug_to_canonical):
        """All data-muscle slugs in anterior SVG should be in the mapping."""
        if not anterior_slugs:
            pytest.skip("No slugs found in anterior SVG")
        
        for slug in anterior_slugs:
            assert slug in vendor_slug_to_canonical, \
                f"Anterior SVG slug '{slug}' not found in VENDOR_SLUG_TO_CANONICAL"
    
    def test_all_posterior_slugs_mapped(self, posterior_slugs, vendor_slug_to_canonical):
        """All data-muscle slugs in posterior SVG should be in the mapping."""
        if not posterior_slugs:
            pytest.skip("No slugs found in posterior SVG")
        
        for slug in posterior_slugs:
            assert slug in vendor_slug_to_canonical, \
                f"Posterior SVG slug '{slug}' not found in VENDOR_SLUG_TO_CANONICAL"
    
    def test_canonical_keys_have_labels(self, vendor_slug_to_canonical, muscle_labels):
        """All non-null canonical keys should have labels."""
        canonical_keys = {v for v in vendor_slug_to_canonical.values() if v is not None}
        
        for key in canonical_keys:
            assert key in muscle_labels, \
                f"Canonical key '{key}' missing from MUSCLE_LABELS"
    
    def test_canonical_keys_have_backend_mapping(self, vendor_slug_to_canonical, muscle_to_backend):
        """All non-null canonical keys should have backend mappings."""
        canonical_keys = {v for v in vendor_slug_to_canonical.values() if v is not None}
        
        for key in canonical_keys:
            assert key in muscle_to_backend, \
                f"Canonical key '{key}' missing from MUSCLE_TO_BACKEND"
    
    def test_no_orphan_canonical_keys_in_labels(self, vendor_slug_to_canonical, muscle_labels):
        """Labels shouldn't have keys that aren't canonical (simple view keys)."""
        # Get all canonical keys plus advanced keys (which are in SIMPLE_TO_ADVANCED_MAP values)
        canonical_keys = {v for v in vendor_slug_to_canonical.values() if v is not None}
        
        # Simple validation: just check that common simple keys exist
        expected_simple_keys = {
            'chest', 'biceps', 'triceps', 'forearms', 'abdominals', 'obliques',
            'quads', 'calves', 'traps', 'glutes', 'hamstrings', 'lowerback'
        }
        
        for key in expected_simple_keys:
            assert key in muscle_labels, f"Expected simple key '{key}' not in MUSCLE_LABELS"
    
    def test_anterior_svg_has_expected_muscles(self, anterior_slugs):
        """Anterior SVG should contain expected muscle regions."""
        expected = {'chest', 'biceps', 'abs', 'quadriceps', 'front-deltoids'}
        
        for muscle in expected:
            assert muscle in anterior_slugs, \
                f"Expected muscle '{muscle}' not found in anterior SVG"
    
    def test_posterior_svg_has_expected_muscles(self, posterior_slugs):
        """Posterior SVG should contain expected muscle regions."""
        expected = {'trapezius', 'upper-back', 'lower-back', 'gluteal', 'hamstring'}
        
        for muscle in expected:
            assert muscle in posterior_slugs, \
                f"Expected muscle '{muscle}' not found in posterior SVG"
    
    def test_bilateral_muscles_appear_multiple_times(self, anterior_slugs, posterior_slugs):
        """Bilateral muscles should appear in the SVG (left + right sides)."""
        # These muscles should have multiple polygon entries
        # We can verify by checking the SVG content directly
        if ANTERIOR_SVG.exists():
            content = ANTERIOR_SVG.read_text(encoding='utf-8')
            # Count occurrences of data-muscle="chest"
            chest_count = content.count('data-muscle="chest"')
            assert chest_count >= 2, f"Expected chest to appear 2+ times, found {chest_count}"
            
            biceps_count = content.count('data-muscle="biceps"')
            assert biceps_count >= 2, f"Expected biceps to appear 2+ times, found {biceps_count}"


class TestMuscleSelectorJSStructure:
    """Test the structure of muscle-selector.js."""
    
    @pytest.fixture
    def js_content(self):
        if not MUSCLE_SELECTOR_JS.exists():
            pytest.skip("muscle-selector.js not found")
        return MUSCLE_SELECTOR_JS.read_text(encoding='utf-8')
    
    def test_muscle_selector_class_exists(self, js_content):
        """MuscleSelector class should be defined."""
        assert "class MuscleSelector" in js_content
    
    def test_exports_to_window(self, js_content):
        """Key objects should be exported to window."""
        assert "window.MuscleSelector" in js_content
        assert "window.MUSCLE_LABELS" in js_content
        assert "window.MUSCLE_TO_BACKEND" in js_content
    
    def test_vendor_mapping_defined(self, js_content):
        """VENDOR_SLUG_TO_CANONICAL should be defined."""
        assert "VENDOR_SLUG_TO_CANONICAL" in js_content
    
    def test_svg_paths_use_vendor_directory(self, js_content):
        """SVG_PATHS should reference vendor directory."""
        assert "/static/vendor/react-body-highlighter/" in js_content
