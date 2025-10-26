# Food Tracking Backend API

A comprehensive backend system for food tracking and inventory management with barcode scanning integration.

## Features

- **Food Inventory Management**: Store and manage food items with nutritional data
- **Barcode Integration**: Fast lookups by barcode for scanning systems
- **Nutrition Logging**: Track food consumption and inventory changes
- **Bulk Import**: Import food data from pandas DataFrames or CSV files
- **Expiration Tracking**: Monitor expiring foods and low stock alerts
- **RESTful API**: Complete FastAPI-based API with automatic documentation

## Tech Stack

- **Database**: PostgreSQL with SQLAlchemy ORM
- **API Framework**: FastAPI with automatic OpenAPI documentation
- **Data Validation**: Pydantic schemas
- **Data Processing**: Pandas for bulk operations
- **Authentication**: Ready for JWT integration

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip or conda

### Installation

1. **Clone and navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database:**
   ```bash
   # Create database
   createdb food_tracking
   
   # Run schema
   psql food_tracking < schema.sql
   ```

5. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your database credentials
   ```

6. **Start the API server:**
   ```bash
   python main.py
   # Or with uvicorn directly:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Food Management

- `POST /foods/` - Create a new food item
- `GET /foods/{food_id}` - Get food by ID
- `GET /foods/barcode/{barcode}` - Get food by barcode
- `GET /foods/` - List all foods (paginated)
- `GET /foods/search/` - Search foods by name/brand
- `PUT /foods/{food_id}` - Update food item
- `PUT /foods/{food_id}/quantity` - Update quantity and log change
- `DELETE /foods/{food_id}` - Delete food item

### Nutrition Logging

- `POST /nutrition-logs/` - Log nutrition event
- `GET /nutrition-logs/` - Get nutrition logs (with optional food filter)

### Bulk Operations

- `POST /foods/bulk-import` - Import multiple foods from JSON data

### Inventory Management

- `GET /inventory/` - Get inventory (optionally filtered by category)
- `GET /inventory/expiring` - Get foods expiring soon
- `GET /inventory/low-stock` - Get foods with low stock

## Usage Examples

### Python Integration

```python
import pandas as pd
from crud import bulk_import_from_dataframe, get_food_by_barcode
from database import get_db_session

# Bulk import from DataFrame
df = pd.DataFrame([
    {
        "barcode": "123456789012",
        "name": "Canned Beans",
        "brand": "Generic Brand",
        "category": "Canned Goods",
        "calories": 250,
        "protein": 12.0,
        "fat": 1.0,
        "carbs": 45.0,
        "quantity": 24
    },
    {
        "barcode": "098765432109",
        "name": "Oat Milk",
        "brand": "Plant Based Co",
        "category": "Dairy Alternatives",
        "calories": 90,
        "fat": 3.0,
        "carbs": 8.0,
        "quantity": 10
    }
])

# Import the data
results = bulk_import_from_dataframe(df)
print(f"Imported: {results['inserted']}, Updated: {results['updated']}, Errors: {results['errors']}")

# Look up food by barcode
with get_db_session() as db:
    food = get_food_by_barcode(db, "123456789012")
    if food:
        print(f"Found: {food.name} - Quantity: {food.quantity}")
```

### API Usage

```bash
# Create a food item
curl -X POST "http://localhost:8000/foods/" \
  -H "Content-Type: application/json" \
  -d '{
    "barcode": "123456789012",
    "name": "Canned Beans",
    "brand": "Generic Brand",
    "category": "Canned Goods",
    "calories": 250,
    "protein": 12.0,
    "quantity": 24
  }'

# Get food by barcode
curl "http://localhost:8000/foods/barcode/123456789012"

# Update quantity
curl -X PUT "http://localhost:8000/foods/{food_id}/quantity" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity_change": -5,
    "action": "consumed"
  }'

# Bulk import
curl -X POST "http://localhost:8000/foods/bulk-import" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {
        "barcode": "123456789012",
        "name": "Canned Beans",
        "calories": 250,
        "quantity": 24
      }
    ]
  }'
```

## Database Schema

### Foods Table
- `id` (UUID, Primary Key)
- `barcode` (TEXT, Unique)
- `name` (TEXT)
- `brand` (TEXT, Optional)
- `category` (TEXT, Optional)
- `calories` (INTEGER, Optional)
- `protein`, `fat`, `carbs`, `fiber`, `sugars`, `sodium` (FLOAT, Optional)
- `allergens` (TEXT[], Optional)
- `expiry_date` (DATE, Optional)
- `quantity` (INTEGER, Default: 0)
- `location` (TEXT, Optional)
- `created_at` (TIMESTAMPTZ)

### Nutrition Logs Table
- `id` (UUID, Primary Key)
- `food_id` (UUID, Foreign Key)
- `quantity` (INTEGER)
- `timestamp` (TIMESTAMPTZ)
- `action` (TEXT: 'added', 'removed', 'consumed', 'expired')

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

### Code Structure

```
backend/
├── main.py              # FastAPI application
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── crud.py             # Database operations
├── database.py         # Database connection
├── schema.sql           # Database schema
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Production Deployment

### Environment Variables

```bash
DATABASE_URL=postgresql://user:password@host:port/database
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
LOG_LEVEL=INFO
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Integration with Frontend

This backend is designed to work seamlessly with the existing Next.js frontend. The API endpoints match the expected data structure from the barcode scanner component.

### Frontend Integration Points

1. **Barcode Scanning**: Use `GET /foods/barcode/{barcode}` to look up scanned items
2. **Food Submission**: Use `POST /foods/` to create new food entries
3. **Inventory Management**: Use inventory endpoints for stock management
4. **Bulk Operations**: Use bulk import for CSV uploads or API integrations

## License

This project is part of the Cal Hacks food tracking system and is available under the MIT License.
