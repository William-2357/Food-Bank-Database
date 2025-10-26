#!/usr/bin/env python3
"""
Debug script to test the backend models and database.
"""

import sys
import traceback

def test_imports():
    """Test if all imports work."""
    try:
        from models import Food, NutritionLog
        print("✅ Models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection."""
    try:
        from database import test_connection, create_tables
        if test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        traceback.print_exc()
        return False

def test_food_creation():
    """Test creating a food item."""
    try:
        from database import get_db_session
        from models import Food
        
        with get_db_session() as db:
            # Test creating a simple food item
            food_data = {
                "barcode": "test123",
                "name": "Test Food",
                "brand": "Test Brand",
                "calories": 100,
                "quantity": 1
            }
            
            food = Food(**food_data)
            db.add(food)
            db.commit()
            db.refresh(food)
            
            print(f"✅ Food created successfully: {food.id}")
            return True
            
    except Exception as e:
        print(f"❌ Food creation failed: {e}")
        traceback.print_exc()
        return False

def test_food_with_allergens():
    """Test creating a food item with allergens."""
    try:
        from database import get_db_session
        from models import Food
        
        with get_db_session() as db:
            # Test creating a food item with allergens
            food_data = {
                "barcode": "test456",
                "name": "Test Food with Allergens",
                "brand": "Test Brand",
                "calories": 100,
                "allergens": ["gluten", "dairy"],
                "quantity": 1
            }
            
            food = Food(**food_data)
            db.add(food)
            db.commit()
            db.refresh(food)
            
            print(f"✅ Food with allergens created successfully: {food.id}")
            print(f"   Allergens: {food.allergens}")
            return True
            
    except Exception as e:
        print(f"❌ Food with allergens creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🔍 Debugging Backend Issues...")
    print("=" * 50)
    
    tests = [
        ("Import Models", test_imports),
        ("Database Connection", test_database_connection),
        ("Simple Food Creation", test_food_creation),
        ("Food with Allergens", test_food_with_allergens),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
