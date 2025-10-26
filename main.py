"""
FastAPI application for the food tracking system.
Provides REST API endpoints for managing food inventory and nutrition logs.
"""

import os
import sys

# Set library path for pyzbar on macOS
if sys.platform == 'darwin':
    # Try to find zbar library
    possible_paths = [
        '/opt/homebrew/opt/zbar/lib',
        '/usr/local/opt/zbar/lib',
        '/opt/homebrew/lib'
    ]
    for path in possible_paths:
        if os.path.exists(path):
            os.environ.setdefault('DYLD_LIBRARY_PATH', path)
            os.environ['DYLD_LIBRARY_PATH'] = f"{path}:{os.environ.get('DYLD_LIBRARY_PATH', '')}"
            break

from fastapi import FastAPI, Depends, HTTPException, status, Query
import requests
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from contextlib import asynccontextmanager
import logging
import pandas as pd
from datetime import datetime
import base64
import io

from database import get_db, create_tables, test_connection
from crud import (
    create_food, get_food_by_barcode, get_food_by_id, get_all_foods,
    search_foods, update_food, update_quantity, delete_food, delete_food_by_barcode,
    log_nutrition_event, get_nutrition_logs, bulk_import_from_dataframe,
    get_foods_by_category, get_expiring_foods, get_low_stock_foods
)
from schemas import (
    FoodCreate, FoodUpdate, FoodResponse, NutritionLogCreate, NutritionLogResponse,
    FoodSearchRequest, QuantityUpdateRequest, BulkImportRequest, BulkImportResponse,
    FoodInventoryResponse, ExpiringFoodsRequest, LowStockRequest, ErrorResponse,
    BarcodeImageUploadRequest, BarcodeImageUploadResponse
)
from barcode_detector import detect_barcodes_with_preprocessing, validate_barcode_format

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    try:
        create_tables()
        if test_connection():
            logger.info("Database connection successful")
        else:
            logger.error("Database connection failed")
    except Exception as e:
        logger.error(f"Startup error: {e}")
    yield
    # Cleanup code can go here if needed

# Create FastAPI app
app = FastAPI(
    title="Food Tracking API",
    description="API for managing food inventory and nutrition tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now()}


# Food endpoints
@app.post("/foods/", response_model=FoodResponse, status_code=status.HTTP_201_CREATED)
async def create_food_endpoint(food: FoodCreate, db: Session = Depends(get_db)):
    """Create a new food item (allows duplicates)."""
    try:
        # Always create new food item (no duplicate checking)
        food_data = food.dict()
        created_food = create_food(db, food_data)
        logger.info(f"Created new food: {food.barcode}")
        return created_food
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating food: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/foods/{food_id}", response_model=FoodResponse)
async def get_food_endpoint(food_id: str, db: Session = Depends(get_db)):
    """Get a food item by ID."""
    food = get_food_by_id(db, food_id)
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )
    return food


@app.get("/foods/barcode/{barcode}", response_model=FoodResponse)
async def get_food_by_barcode_endpoint(barcode: str, db: Session = Depends(get_db)):
    """Get a food item by barcode."""
    food = get_food_by_barcode(db, barcode)
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )
    return food


@app.get("/foods/", response_model=List[FoodResponse])
async def get_foods_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all food items with pagination."""
    foods = get_all_foods(db, skip=skip, limit=limit)
    return foods


@app.get("/foods/search/", response_model=List[FoodResponse])
async def search_foods_endpoint(
    q: str = Query(..., description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Search food items by name or brand."""
    foods = search_foods(db, q, skip=skip, limit=limit)
    return foods


@app.put("/foods/{food_id}", response_model=FoodResponse)
async def update_food_endpoint(
    food_id: str,
    food_update: FoodUpdate,
    db: Session = Depends(get_db)
):
    """Update a food item."""
    # Filter out None values
    update_data = {k: v for k, v in food_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )
    
    updated_food = update_food(db, food_id, update_data)
    if not updated_food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )
    return updated_food


@app.put("/foods/{food_id}/quantity", response_model=FoodResponse)
async def update_quantity_endpoint(
    food_id: str,
    quantity_update: QuantityUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update food quantity and log the change."""
    updated_food = update_quantity(
        db, food_id, quantity_update.quantity_change, quantity_update.action
    )
    if not updated_food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )
    return updated_food


@app.delete("/foods/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_food_endpoint(food_id: str, db: Session = Depends(get_db)):
    """Delete a food item."""
    success = delete_food(db, food_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )


@app.delete("/foods/barcode/{barcode}", status_code=status.HTTP_200_OK)
async def delete_food_by_barcode_endpoint(barcode: str, db: Session = Depends(get_db)):
    """Delete all food items with a specific barcode."""
    success = delete_food_by_barcode(db, barcode)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No food items found with this barcode"
        )
    return {"message": f"All food items with barcode {barcode} have been deleted"}


# Barcode image upload endpoint
@app.post("/barcode/upload-image", response_model=BarcodeImageUploadResponse)
async def upload_barcode_image(
    request: BarcodeImageUploadRequest,
    db: Session = Depends(get_db)
):
    """
    Upload an image containing a barcode, detect it, fetch product data from OpenFoodFacts,
    and optionally save to database.
    """
    try:
        # Validate action
        if request.action not in ['scan', 'scan_and_save']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be 'scan' or 'scan_and_save'"
            )
        
        # Detect barcodes in the image
        logger.info("Detecting barcodes in uploaded image...")
        barcodes = detect_barcodes_with_preprocessing(request.imageData, request.imageFormat)
        
        if not barcodes:
            return BarcodeImageUploadResponse(
                success=False,
                message="No barcode detected in the uploaded image",
                error="No barcode found"
            )
        
        # Get the first valid barcode
        barcode = barcodes[0]
        
        if not validate_barcode_format(barcode):
            return BarcodeImageUploadResponse(
                success=False,
                message="Invalid barcode format detected",
                error="Invalid barcode format"
            )
        
        logger.info(f"Barcode detected: {barcode}")
        
        # Fetch product data from OpenFoodFacts
        openfoodfacts_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        
        try:
            response = requests.get(openfoodfacts_url, timeout=10)
            
            if response.status_code != 200 or response.json().get('status') == 0:
                return BarcodeImageUploadResponse(
                    success=True,
                    barcode=barcode,
                    message="Barcode detected but product not found in OpenFoodFacts database"
                )
        except Exception as e:
            logger.error(f"Error fetching from OpenFoodFacts: {e}")
            return BarcodeImageUploadResponse(
                success=False,
                message="Error fetching product data from OpenFoodFacts",
                error=str(e)
            )
        
        product = response.json()['product']
        
        # Extract product information
        # Process product data based on OpenFoodFacts structure
        # Reference: https://world.openfoodfacts.org/
        nutriments = product.get('nutriments', {})
        
        food_data = {
            "barcode": barcode,
            "name": product.get('product_name', 'Unknown Product').strip(),
            "brand": product.get('brands', '').strip() or None,
            "category": product.get('categories', '').split(',')[0].strip() if product.get('categories') else None,
            "calories": round(nutriments.get('energy-kcal_100g', 0)) if nutriments.get('energy-kcal_100g') else None,
            "protein": round(nutriments.get('proteins_100g', 0), 2) if nutriments.get('proteins_100g') else None,
            "fat": round(nutriments.get('fat_100g', 0), 2) if nutriments.get('fat_100g') else None,
            "carbs": round(nutriments.get('carbohydrates_100g', 0), 2) if nutriments.get('carbohydrates_100g') else None,
            "fiber": round(nutriments.get('fiber_100g', 0), 2) if nutriments.get('fiber_100g') else None,
            "sugars": round(nutriments.get('sugars_100g', 0), 2) if nutriments.get('sugars_100g') else None,
            "sodium": round(nutriments.get('sodium_100g', 0), 2) if nutriments.get('sodium_100g') else None,
            "allergens": product.get('allergens', '').split(',') if product.get('allergens') else [],
            "quantity": 1
        }
        
        # Remove None values
        food_data = {k: v for k, v in food_data.items() if v is not None and v != '' and v != []}
        
        # If action is scan_and_save, save to database
        if request.action == 'scan_and_save':
            try:
                # Check if food already exists
                existing_food = get_food_by_barcode(db, barcode)
                if existing_food:
                    return BarcodeImageUploadResponse(
                        success=True,
                        barcode=barcode,
                        product_data=existing_food.to_dict(),
                        message="Barcode detected and food already exists in database"
                    )
                
                # Create food item
                created_food = create_food(db, food_data)
                
                logger.info(f"Successfully saved product {created_food.name} to database")
                
                return BarcodeImageUploadResponse(
                    success=True,
                    barcode=barcode,
                    product_data=created_food.to_dict(),
                    message="Barcode detected and product saved to database"
                )
                
            except Exception as e:
                logger.error(f"Error saving to database: {e}")
                return BarcodeImageUploadResponse(
                    success=True,
                    barcode=barcode,
                    product_data=food_data,
                    message="Barcode detected but error occurred while saving to database"
                )
        
        # For scan-only action, return product data without saving
        return BarcodeImageUploadResponse(
            success=True,
            barcode=barcode,
            product_data=food_data,
            message="Barcode detected successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing barcode image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing barcode image: {str(e)}"
        )


# Nutrition log endpoints
@app.post("/nutrition-logs/", response_model=NutritionLogResponse, status_code=status.HTTP_201_CREATED)
async def create_nutrition_log_endpoint(
    nutrition_log: NutritionLogCreate,
    db: Session = Depends(get_db)
):
    """Create a new nutrition log entry."""
    # Verify food exists
    food = get_food_by_id(db, str(nutrition_log.food_id))
    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )
    
    created_log = log_nutrition_event(
        db, str(nutrition_log.food_id), nutrition_log.quantity, nutrition_log.action
    )
    return created_log


@app.get("/nutrition-logs/", response_model=List[NutritionLogResponse])
async def get_nutrition_logs_endpoint(
    food_id: Optional[str] = Query(None, description="Filter by food ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get nutrition logs, optionally filtered by food ID."""
    logs = get_nutrition_logs(db, food_id, skip=skip, limit=limit)
    return logs


# Bulk operations
@app.post("/foods/bulk-import", response_model=BulkImportResponse)
async def bulk_import_endpoint(
    import_data: BulkImportRequest,
    db: Session = Depends(get_db)
):
    """Import multiple food items from a list."""
    try:
        # Convert to DataFrame
        df = pd.DataFrame(import_data.data)
        results = bulk_import_from_dataframe(df)
        return BulkImportResponse(**results)
    except Exception as e:
        logger.error(f"Bulk import error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk import failed: {str(e)}"
        )


# Inventory management endpoints
@app.get("/inventory/", response_model=List[FoodResponse])
async def get_inventory_endpoint(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """Get food inventory, optionally filtered by category."""
    if category:
        foods = get_foods_by_category(db, category)
    else:
        foods = get_all_foods(db)
    return foods


@app.get("/inventory/expiring", response_model=List[FoodResponse])
async def get_expiring_foods_endpoint(
    days_ahead: int = Query(7, ge=1, le=365, description="Days ahead to check"),
    db: Session = Depends(get_db)
):
    """Get foods that are expiring within the specified number of days."""
    foods = get_expiring_foods(db, days_ahead)
    return foods


@app.get("/inventory/low-stock", response_model=List[FoodResponse])
async def get_low_stock_foods_endpoint(
    threshold: int = Query(5, ge=0, description="Quantity threshold"),
    db: Session = Depends(get_db)
):
    """Get foods with low stock (quantity below threshold)."""
    foods = get_low_stock_foods(db, threshold)
    return foods


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": str(exc.status_code),
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "500",
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
