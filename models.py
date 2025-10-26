"""
SQLAlchemy models for the food tracking system.
Defines the database schema using SQLAlchemy ORM.
"""

from sqlalchemy import Column, String, Integer, Float, Date, DateTime, Text, JSON, ForeignKey, CheckConstraint, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Food(Base):
    """Food model representing items in the food inventory."""
    
    __tablename__ = "foods"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    barcode = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    category = Column(String, index=True)
    calories = Column(Integer)
    protein = Column(Float)
    fat = Column(Float)
    carbs = Column(Float)
    fiber = Column(Float)
    sugars = Column(Float)
    sodium = Column(Float)
    allergens = Column(JSON)
    expiry_date = Column(Date, index=True)
    quantity = Column(Integer, default=0)
    location = Column(String)
    barcode_image_url = Column(String)
    barcode_image_data = Column(LargeBinary)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to nutrition logs
    nutrition_logs = relationship("NutritionLog", back_populates="food", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Food(id={self.id}, barcode={self.barcode}, name={self.name}, quantity={self.quantity})>"
    
    def to_dict(self):
        """Convert the food object to a dictionary."""
        return {
            "id": str(self.id),
            "barcode": self.barcode,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "calories": self.calories,
            "protein": self.protein,
            "fat": self.fat,
            "carbs": self.carbs,
            "fiber": self.fiber,
            "sugars": self.sugars,
            "sodium": self.sodium,
            "allergens": self.allergens,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "quantity": self.quantity,
            "location": self.location,
            "barcode_image_url": self.barcode_image_url,
            "barcode_image_data": self.barcode_image_data.decode('base64') if self.barcode_image_data else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class NutritionLog(Base):
    """Nutrition log model for tracking food consumption and inventory changes."""
    
    __tablename__ = "nutrition_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    food_id = Column(String, ForeignKey("foods.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    action = Column(String, nullable=False, index=True)
    
    # Add check constraint for valid actions
    __table_args__ = (
        CheckConstraint(
            "action IN ('added', 'removed', 'consumed', 'expired')",
            name="check_valid_action"
        ),
    )
    
    # Relationship to food
    food = relationship("Food", back_populates="nutrition_logs")
    
    def __repr__(self):
        return f"<NutritionLog(id={self.id}, food_id={self.food_id}, action={self.action}, quantity={self.quantity})>"
    
    def to_dict(self):
        """Convert the nutrition log object to a dictionary."""
        return {
            "id": str(self.id),
            "food_id": str(self.food_id),
            "quantity": self.quantity,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "action": self.action
        }
