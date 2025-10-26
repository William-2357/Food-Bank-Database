"""
CRUD operations for the food tracking system.
Provides functions to create, read, update, and delete food items and nutrition logs.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, date
import pandas as pd
import logging

from models import Food, NutritionLog
from database import get_db_session

logger = logging.getLogger(__name__)


# Food CRUD Operations

def create_food(db: Session, food_data: Dict[str, Any]) -> Food:
    """
    Create a new food item in the database.
    
    Args:
        db: Database session
        food_data: Dictionary containing food information
        
    Returns:
        Food: The created food object
    """
    try:
        food = Food(**food_data)
        db.add(food)
        db.commit()
        db.refresh(food)
        logger.info(f"Created food item: {food.name} (barcode: {food.barcode})")
        return food
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating food item: {e}")
        raise


def get_food_by_barcode(db: Session, barcode: str) -> Optional[Food]:
    """
    Get a food item by its barcode.
    
    Args:
        db: Database session
        barcode: The barcode to search for
        
    Returns:
        Food or None: The food item if found, None otherwise
    """
    return db.query(Food).filter(Food.barcode == barcode).first()


def get_food_by_id(db: Session, food_id: str) -> Optional[Food]:
    """
    Get a food item by its ID.
    
    Args:
        db: Database session
        food_id: The UUID of the food item
        
    Returns:
        Food or None: The food item if found, None otherwise
    """
    return db.query(Food).filter(Food.id == food_id).first()


def get_all_foods(db: Session, skip: int = 0, limit: int = 100) -> List[Food]:
    """
    Get all food items with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List[Food]: List of food items
    """
    return db.query(Food).offset(skip).limit(limit).all()


def search_foods(db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Food]:
    """
    Search food items by name or brand.
    
    Args:
        db: Database session
        query: Search query string
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List[Food]: List of matching food items
    """
    return db.query(Food).filter(
        or_(
            Food.name.ilike(f"%{query}%"),
            Food.brand.ilike(f"%{query}%")
        )
    ).offset(skip).limit(limit).all()


def update_food(db: Session, food_id: str, food_data: Dict[str, Any]) -> Optional[Food]:
    """
    Update a food item.
    
    Args:
        db: Database session
        food_id: The UUID of the food item to update
        food_data: Dictionary containing updated food information
        
    Returns:
        Food or None: The updated food item if found, None otherwise
    """
    try:
        food = db.query(Food).filter(Food.id == food_id).first()
        if not food:
            return None
            
        for key, value in food_data.items():
            if hasattr(food, key):
                setattr(food, key, value)
        
        db.commit()
        db.refresh(food)
        logger.info(f"Updated food item: {food.name} (ID: {food.id})")
        return food
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating food item: {e}")
        raise


def update_quantity(db: Session, food_id: str, quantity_change: int, action: str = "added") -> Optional[Food]:
    """
    Update the quantity of a food item and log the change.
    
    Args:
        db: Database session
        food_id: The UUID of the food item
        quantity_change: The amount to add/subtract
        action: The action being performed ('added', 'removed', 'consumed', 'expired')
        
    Returns:
        Food or None: The updated food item if found, None otherwise
    """
    try:
        food = db.query(Food).filter(Food.id == food_id).first()
        if not food:
            return None
        
        # Create nutrition log entry
        nutrition_log = NutritionLog(
            food_id=food_id,
            quantity=abs(quantity_change),
            action=action
        )
        db.add(nutrition_log)
        
        # Update quantity (the trigger will handle this automatically)
        db.commit()
        db.refresh(food)
        
        logger.info(f"Updated quantity for {food.name}: {action} {abs(quantity_change)} units")
        return food
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating quantity: {e}")
        raise


def delete_food(db: Session, food_id: str) -> bool:
    """
    Delete a food item.
    
    Args:
        db: Database session
        food_id: The UUID of the food item to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        food = db.query(Food).filter(Food.id == food_id).first()
        if not food:
            return False
            
        db.delete(food)
        db.commit()
        logger.info(f"Deleted food item: {food.name} (ID: {food_id})")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting food item: {e}")
        raise


# Nutrition Log Operations

def log_nutrition_event(db: Session, food_id: str, quantity: int, action: str) -> NutritionLog:
    """
    Log a nutrition event (consumption, addition, etc.).
    
    Args:
        db: Database session
        food_id: The UUID of the food item
        quantity: The quantity involved
        action: The action being performed
        
    Returns:
        NutritionLog: The created nutrition log entry
    """
    try:
        nutrition_log = NutritionLog(
            food_id=food_id,
            quantity=quantity,
            action=action
        )
        db.add(nutrition_log)
        db.commit()
        db.refresh(nutrition_log)
        logger.info(f"Logged nutrition event: {action} {quantity} units for food {food_id}")
        return nutrition_log
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging nutrition event: {e}")
        raise


def get_nutrition_logs(db: Session, food_id: Optional[str] = None, 
                      skip: int = 0, limit: int = 100) -> List[NutritionLog]:
    """
    Get nutrition logs, optionally filtered by food ID.
    
    Args:
        db: Database session
        food_id: Optional food ID to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List[NutritionLog]: List of nutrition log entries
    """
    query = db.query(NutritionLog)
    if food_id:
        query = query.filter(NutritionLog.food_id == food_id)
    
    return query.order_by(desc(NutritionLog.timestamp)).offset(skip).limit(limit).all()


# Bulk Import Operations

def bulk_import_from_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Import food data from a pandas DataFrame.
    Performs upsert operations (insert or update if barcode exists).
    
    Args:
        df: Pandas DataFrame containing food data
        
    Returns:
        Dict: Summary of import results
    """
    results = {
        "total_rows": len(df),
        "inserted": 0,
        "updated": 0,
        "errors": 0,
        "error_details": []
    }
    
    with get_db_session() as db:
        for index, row in df.iterrows():
            try:
                # Convert row to dictionary, handling NaN values
                food_data = row.to_dict()
                food_data = {k: v for k, v in food_data.items() if pd.notna(v)}
                
                # Convert expiry_date string to date object if present
                if 'expiry_date' in food_data and isinstance(food_data['expiry_date'], str):
                    try:
                        from datetime import datetime
                        food_data['expiry_date'] = datetime.strptime(food_data['expiry_date'], '%Y-%m-%d').date()
                    except ValueError:
                        # Invalid date format, remove it
                        food_data.pop('expiry_date', None)
                
                # Check if food already exists by barcode
                existing_food = get_food_by_barcode(db, food_data.get('barcode'))
                
                if existing_food:
                    # Update existing food
                    for key, value in food_data.items():
                        if hasattr(existing_food, key) and key != 'id':
                            setattr(existing_food, key, value)
                    db.commit()
                    results["updated"] += 1
                    logger.info(f"Updated food: {food_data.get('name', 'Unknown')}")
                else:
                    # Create new food
                    create_food(db, food_data)
                    results["inserted"] += 1
                    logger.info(f"Inserted food: {food_data.get('name', 'Unknown')}")
                    
            except Exception as e:
                results["errors"] += 1
                error_msg = f"Row {index}: {str(e)}"
                results["error_details"].append(error_msg)
                logger.error(error_msg)
    
    logger.info(f"Bulk import completed: {results['inserted']} inserted, {results['updated']} updated, {results['errors']} errors")
    return results


def get_foods_by_category(db: Session, category: str) -> List[Food]:
    """
    Get all foods in a specific category.
    
    Args:
        db: Database session
        category: The category to filter by
        
    Returns:
        List[Food]: List of foods in the category
    """
    return db.query(Food).filter(Food.category == category).all()


def get_expiring_foods(db: Session, days_ahead: int = 7) -> List[Food]:
    """
    Get foods that are expiring within the specified number of days.
    
    Args:
        db: Database session
        days_ahead: Number of days to look ahead for expiration
        
    Returns:
        List[Food]: List of foods expiring soon
    """
    from datetime import timedelta
    expiry_date = date.today() + timedelta(days=days_ahead)
    
    return db.query(Food).filter(
        and_(
            Food.expiry_date <= expiry_date,
            Food.expiry_date >= date.today(),
            Food.quantity > 0
        )
    ).order_by(asc(Food.expiry_date)).all()


def get_low_stock_foods(db: Session, threshold: int = 5) -> List[Food]:
    """
    Get foods with low stock (quantity below threshold).
    
    Args:
        db: Database session
        threshold: The quantity threshold for low stock
        
    Returns:
        List[Food]: List of foods with low stock
    """
    return db.query(Food).filter(
        and_(
            Food.quantity <= threshold,
            Food.quantity >= 0
        )
    ).order_by(asc(Food.quantity)).all()


def delete_food_by_barcode(db: Session, barcode: str) -> bool:
    """
    Delete all food items with a specific barcode.
    
    Args:
        db: Database session
        barcode: The barcode to delete
        
    Returns:
        bool: True if any items were deleted, False otherwise
    """
    try:
        foods_to_delete = db.query(Food).filter(Food.barcode == barcode).all()
        if not foods_to_delete:
            return False
            
        for food in foods_to_delete:
            db.delete(food)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
