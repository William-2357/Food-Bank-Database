"""
Pydantic schemas for request/response validation in the FastAPI application.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


# Base schemas
class FoodBase(BaseModel):
    """Base schema for food items."""
    barcode: str = Field(..., description="Product barcode")
    name: str = Field(..., description="Food name")
    brand: Optional[str] = Field(None, description="Brand name")
    category: Optional[str] = Field(None, description="Food category")
    calories: Optional[int] = Field(None, ge=0, description="Calories per serving")
    protein: Optional[float] = Field(None, ge=0, description="Protein in grams")
    fat: Optional[float] = Field(None, ge=0, description="Fat in grams")
    carbs: Optional[float] = Field(None, ge=0, description="Carbohydrates in grams")
    fiber: Optional[float] = Field(None, ge=0, description="Fiber in grams")
    sugars: Optional[float] = Field(None, ge=0, description="Sugars in grams")
    sodium: Optional[float] = Field(None, ge=0, description="Sodium in mg")
    allergens: Optional[List[str]] = Field(None, description="List of allergens")
    expiry_date: Optional[date] = Field(None, description="Expiration date")
    quantity: Optional[int] = Field(0, ge=0, description="Current quantity in stock")
    location: Optional[str] = Field(None, description="Storage location")
    barcode_image_url: Optional[str] = Field(None, description="URL of uploaded barcode image")
    barcode_image_data: Optional[str] = Field(None, description="Base64 encoded barcode image data")


class FoodCreate(FoodBase):
    """Schema for creating a new food item."""
    pass


class BarcodeImageUploadRequest(BaseModel):
    """Schema for barcode image upload requests."""
    imageData: str = Field(..., description="Base64 encoded image data")
    imageFormat: str = Field(..., description="Image format (e.g., 'jpeg', 'png')")
    action: str = Field("scan", description="Action to perform: 'scan' or 'scan_and_save'")
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['scan', 'scan_and_save']
        if v not in valid_actions:
            raise ValueError(f'Action must be one of: {valid_actions}')
        return v


class BarcodeImageUploadResponse(BaseModel):
    """Schema for barcode image upload responses."""
    success: bool
    barcode: Optional[str] = None
    product_data: Optional[Dict[str, Any]] = None
    message: str
    error: Optional[str] = None


class FoodUpdate(BaseModel):
    """Schema for updating a food item."""
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    calories: Optional[int] = Field(None, ge=0)
    protein: Optional[float] = Field(None, ge=0)
    fat: Optional[float] = Field(None, ge=0)
    carbs: Optional[float] = Field(None, ge=0)
    fiber: Optional[float] = Field(None, ge=0)
    sugars: Optional[float] = Field(None, ge=0)
    sodium: Optional[float] = Field(None, ge=0)
    allergens: Optional[List[str]] = None
    expiry_date: Optional[date] = None
    quantity: Optional[int] = Field(None, ge=0)
    location: Optional[str] = None
    barcode_image_url: Optional[str] = None
    barcode_image_data: Optional[str] = None


class FoodResponse(FoodBase):
    """Schema for food item responses."""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class NutritionLogBase(BaseModel):
    """Base schema for nutrition logs."""
    food_id: UUID = Field(..., description="ID of the food item")
    quantity: int = Field(..., gt=0, description="Quantity involved in the action")
    action: str = Field(..., description="Action performed")
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['added', 'removed', 'consumed', 'expired']
        if v not in valid_actions:
            raise ValueError(f'Action must be one of: {valid_actions}')
        return v


class NutritionLogCreate(NutritionLogBase):
    """Schema for creating a nutrition log entry."""
    pass


class NutritionLogResponse(NutritionLogBase):
    """Schema for nutrition log responses."""
    id: UUID
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Request/Response schemas for API endpoints
class FoodSearchRequest(BaseModel):
    """Schema for food search requests."""
    query: str = Field(..., description="Search query")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class QuantityUpdateRequest(BaseModel):
    """Schema for updating food quantity."""
    quantity_change: int = Field(..., description="Quantity change (positive or negative)")
    action: str = Field(..., description="Action being performed")
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['added', 'removed', 'consumed', 'expired']
        if v not in valid_actions:
            raise ValueError(f'Action must be one of: {valid_actions}')
        return v


class BulkImportRequest(BaseModel):
    """Schema for bulk import requests."""
    data: List[Dict[str, Any]] = Field(..., description="List of food items to import")
    
    @validator('data')
    def validate_data(cls, v):
        if not v:
            raise ValueError('Data list cannot be empty')
        return v


class BulkImportResponse(BaseModel):
    """Schema for bulk import responses."""
    total_rows: int
    inserted: int
    updated: int
    errors: int
    error_details: List[str]


class FoodInventoryResponse(BaseModel):
    """Schema for food inventory responses."""
    id: UUID
    barcode: str
    name: str
    brand: Optional[str]
    category: Optional[str]
    calories: Optional[int]
    protein: Optional[float]
    fat: Optional[float]
    carbs: Optional[float]
    fiber: Optional[float]
    sugars: Optional[float]
    sodium: Optional[float]
    allergens: Optional[List[str]]
    expiry_date: Optional[date]
    quantity: int
    location: Optional[str]
    created_at: datetime
    expiry_status: str


class ExpiringFoodsRequest(BaseModel):
    """Schema for expiring foods requests."""
    days_ahead: int = Field(7, ge=1, le=365, description="Number of days to look ahead")


class LowStockRequest(BaseModel):
    """Schema for low stock requests."""
    threshold: int = Field(5, ge=0, description="Quantity threshold for low stock")


# Error schemas
class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses."""
    detail: List[Dict[str, Any]]
    error_code: str = "validation_error"
    timestamp: datetime = Field(default_factory=datetime.now)
