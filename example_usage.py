"""
Example usage of the food tracking backend system.
Demonstrates how to use the CRUD operations and bulk import functionality.
"""

import pandas as pd
from datetime import date, datetime
from database import get_db_session, create_tables, test_connection
from crud import (
    create_food, get_food_by_barcode, get_food_by_id, search_foods,
    update_quantity, log_nutrition_event, bulk_import_from_dataframe,
    get_expiring_foods, get_low_stock_foods
)


def example_basic_operations():
    """Example of basic CRUD operations."""
    print("=== Basic CRUD Operations Example ===")
    
    with get_db_session() as db:
        # Create a food item
        food_data = {
            "barcode": "1234567890123",
            "name": "Organic Canned Beans",
            "brand": "Healthy Choice",
            "category": "Canned Goods",
            "calories": 250,
            "protein": 12.0,
            "fat": 1.0,
            "carbs": 45.0,
            "fiber": 8.0,
            "sugars": 2.0,
            "sodium": 400.0,
            "allergens": ["soy"],
            "expiry_date": date(2024, 12, 31),
            "quantity": 50,
            "location": "Pantry A1"
        }
        
        food = create_food(db, food_data)
        print(f"Created food: {food.name} (ID: {food.id})")
        
        # Get food by barcode
        found_food = get_food_by_barcode(db, "1234567890123")
        print(f"Found by barcode: {found_food.name if found_food else 'Not found'}")
        
        # Update quantity (consume some)
        updated_food = update_quantity(db, str(food.id), -5, "consumed")
        print(f"Updated quantity: {updated_food.quantity} units remaining")
        
        # Log a nutrition event
        log_nutrition_event(db, str(food.id), 2, "consumed")
        print(f"Logged consumption of 2 units")


def example_bulk_import():
    """Example of bulk importing from pandas DataFrame."""
    print("\n=== Bulk Import Example ===")
    
    # Create sample data
    sample_data = [
        {
            "barcode": "111111111111",
            "name": "Whole Wheat Bread",
            "brand": "Bakery Fresh",
            "category": "Bakery",
            "calories": 80,
            "protein": 3.0,
            "fat": 1.0,
            "carbs": 15.0,
            "fiber": 2.0,
            "sugars": 2.0,
            "sodium": 150.0,
            "allergens": ["wheat", "gluten"],
            "expiry_date": "2024-01-15",
            "quantity": 10,
            "location": "Bakery Section"
        },
        {
            "barcode": "222222222222",
            "name": "Almond Milk",
            "brand": "Plant Based Co",
            "category": "Dairy Alternatives",
            "calories": 30,
            "protein": 1.0,
            "fat": 2.5,
            "carbs": 1.0,
            "fiber": 0.0,
            "sugars": 0.0,
            "sodium": 50.0,
            "allergens": ["tree nuts"],
            "expiry_date": "2024-02-01",
            "quantity": 20,
            "location": "Dairy Cooler"
        },
        {
            "barcode": "333333333333",
            "name": "Greek Yogurt",
            "brand": "Protein Plus",
            "category": "Dairy",
            "calories": 100,
            "protein": 15.0,
            "fat": 0.0,
            "carbs": 6.0,
            "fiber": 0.0,
            "sugars": 4.0,
            "sodium": 50.0,
            "allergens": ["milk"],
            "expiry_date": "2024-01-20",
            "quantity": 15,
            "location": "Dairy Cooler"
        }
    ]
    
    # Convert to DataFrame
    df = pd.DataFrame(sample_data)
    print(f"Created DataFrame with {len(df)} rows")
    
    # Import the data
    results = bulk_import_from_dataframe(df)
    print(f"Import results:")
    print(f"  - Total rows: {results['total_rows']}")
    print(f"  - Inserted: {results['inserted']}")
    print(f"  - Updated: {results['updated']}")
    print(f"  - Errors: {results['errors']}")
    
    if results['error_details']:
        print(f"  - Error details: {results['error_details']}")


def example_inventory_management():
    """Example of inventory management features."""
    print("\n=== Inventory Management Example ===")
    
    with get_db_session() as db:
        # Search for foods
        search_results = search_foods(db, "bread")
        print(f"Found {len(search_results)} foods matching 'bread':")
        for food in search_results:
            print(f"  - {food.name} ({food.brand}) - {food.quantity} units")
        
        # Check for expiring foods
        expiring_foods = get_expiring_foods(db, days_ahead=30)
        print(f"\nFound {len(expiring_foods)} foods expiring in the next 30 days:")
        for food in expiring_foods:
            print(f"  - {food.name} expires on {food.expiry_date} - {food.quantity} units")
        
        # Check for low stock
        low_stock_foods = get_low_stock_foods(db, threshold=10)
        print(f"\nFound {len(low_stock_foods)} foods with low stock (≤10 units):")
        for food in low_stock_foods:
            print(f"  - {food.name} - {food.quantity} units remaining")


def example_api_integration():
    """Example of how to integrate with the FastAPI endpoints."""
    print("\n=== API Integration Example ===")
    
    import requests
    import json
    
    base_url = "http://localhost:8000"
    
    # Example API calls (uncomment when server is running)
    """
    # Create a food item
    food_data = {
        "barcode": "444444444444",
        "name": "Energy Bar",
        "brand": "Power Foods",
        "category": "Snacks",
        "calories": 200,
        "protein": 10.0,
        "fat": 8.0,
        "carbs": 25.0,
        "quantity": 30
    }
    
    response = requests.post(f"{base_url}/foods/", json=food_data)
    if response.status_code == 201:
        food = response.json()
        print(f"Created food via API: {food['name']} (ID: {food['id']})")
    
    # Get food by barcode
    response = requests.get(f"{base_url}/foods/barcode/444444444444")
    if response.status_code == 200:
        food = response.json()
        print(f"Retrieved food via API: {food['name']}")
    
    # Update quantity
    quantity_data = {
        "quantity_change": -3,
        "action": "consumed"
    }
    response = requests.put(f"{base_url}/foods/{food['id']}/quantity", json=quantity_data)
    if response.status_code == 200:
        updated_food = response.json()
        print(f"Updated quantity via API: {updated_food['quantity']} units remaining")
    """
    
    print("API integration examples (uncomment when server is running)")


def main():
    """Run all examples."""
    print("Food Tracking Backend - Usage Examples")
    print("=" * 50)
    
    # Test database connection
    if not test_connection():
        print("Database connection failed. Please check your PostgreSQL setup.")
        return
    
    # Create tables if they don't exist
    create_tables()
    print("Database tables created/verified")
    
    try:
        # Run examples
        example_basic_operations()
        example_bulk_import()
        example_inventory_management()
        example_api_integration()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nTo start the API server, run:")
        print("  python main.py")
        print("\nThen visit http://localhost:8000/docs for API documentation")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
