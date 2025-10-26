-- PostgreSQL Schema for Food Tracking System
-- This schema creates the necessary tables for storing food data and nutrition logs

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create foods table
CREATE TABLE IF NOT EXISTS foods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    barcode TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    brand TEXT,
    category TEXT,
    calories INTEGER,
    protein FLOAT,
    fat FLOAT,
    carbs FLOAT,
    fiber FLOAT,
    sugars FLOAT,
    sodium FLOAT,
    allergens TEXT[],
    expiry_date DATE,
    quantity INTEGER DEFAULT 0,
    location TEXT,
    barcode_image_url TEXT,
    barcode_image_data BYTEA,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create nutrition_logs table
CREATE TABLE IF NOT EXISTS nutrition_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    food_id UUID NOT NULL REFERENCES foods(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    action TEXT NOT NULL CHECK (action IN ('added', 'removed', 'consumed', 'expired'))
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_foods_barcode ON foods(barcode);
CREATE INDEX IF NOT EXISTS idx_foods_category ON foods(category);
CREATE INDEX IF NOT EXISTS idx_foods_expiry_date ON foods(expiry_date);
CREATE INDEX IF NOT EXISTS idx_nutrition_logs_food_id ON nutrition_logs(food_id);
CREATE INDEX IF NOT EXISTS idx_nutrition_logs_timestamp ON nutrition_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_nutrition_logs_action ON nutrition_logs(action);

-- Create a function to automatically update quantity when nutrition logs are added
CREATE OR REPLACE FUNCTION update_food_quantity()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.action = 'added' THEN
        UPDATE foods SET quantity = quantity + NEW.quantity WHERE id = NEW.food_id;
    ELSIF NEW.action = 'removed' OR NEW.action = 'consumed' OR NEW.action = 'expired' THEN
        UPDATE foods SET quantity = GREATEST(0, quantity - NEW.quantity) WHERE id = NEW.food_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update quantities
CREATE TRIGGER trigger_update_food_quantity
    AFTER INSERT ON nutrition_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_food_quantity();

-- Create a view for food inventory with current quantities
CREATE OR REPLACE VIEW food_inventory AS
SELECT 
    f.id,
    f.barcode,
    f.name,
    f.brand,
    f.category,
    f.calories,
    f.protein,
    f.fat,
    f.carbs,
    f.fiber,
    f.sugars,
    f.sodium,
    f.allergens,
    f.expiry_date,
    f.quantity,
    f.location,
    f.created_at,
    CASE 
        WHEN f.expiry_date IS NULL THEN 'No expiry date'
        WHEN f.expiry_date < CURRENT_DATE THEN 'Expired'
        WHEN f.expiry_date <= CURRENT_DATE + INTERVAL '7 days' THEN 'Expires soon'
        ELSE 'Fresh'
    END as expiry_status
FROM foods f
WHERE f.quantity > 0
ORDER BY f.expiry_date ASC NULLS LAST;
