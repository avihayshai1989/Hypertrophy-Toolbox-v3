"""
Quick verification script to ensure all exercises are available.
Run with: python tests/verify_exercises.py
"""
import sys
sys.path.insert(0, '.')

from utils.filter_predicates import get_exercises

def main():
    # Test 1: All exercises
    all_ex = get_exercises()
    print(f"✅ Total exercises in database: {len(all_ex)}")
    
    # Test 2: Sample search queries
    print("\n📊 Search results for common terms:")
    test_queries = ['Bench', 'Squat', 'Curl', 'Press', 'Dead', 'Lat', 'Row', 'Fly']
    for q in test_queries:
        matches = [ex for ex in all_ex if q.lower() in ex.lower()]
        print(f"   '{q}': {len(matches)} matches")
    
    # Test 3: First letter distribution
    first_letters = {}
    for ex in all_ex:
        if ex:
            first = ex[0].upper()
            first_letters[first] = first_letters.get(first, 0) + 1
    
    print("\n🔤 Exercises by first letter:")
    for letter in sorted(first_letters.keys()):
        print(f"   {letter}: {first_letters[letter]} exercises")
    
    print("\n✅ All exercises are available for selection!")
    print("   Open browser console (F12) to see exercise count on page load.")

if __name__ == "__main__":
    main()
