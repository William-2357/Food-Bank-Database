#!/usr/bin/env python3
"""
Setup script for the food tracking backend.
This script helps set up the database and install dependencies.
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def install_requirements():
    """Install Python requirements."""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def setup_sqlite_database():
    """Set up SQLite database as a fallback."""
    print("Setting up SQLite database...")
    
    # Create database file
    db_path = Path("food_tracking.db")
    if db_path.exists():
        print("✅ SQLite database already exists")
        return True
    
    try:
        # Create database and tables
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create foods table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS foods (
                id TEXT PRIMARY KEY,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                brand TEXT,
                category TEXT,
                calories INTEGER,
                protein REAL,
                fat REAL,
                carbs REAL,
                fiber REAL,
                sugars REAL,
                sodium REAL,
                allergens TEXT,
                expiry_date TEXT,
                quantity INTEGER DEFAULT 0,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create nutrition_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nutrition_logs (
                id TEXT PRIMARY KEY,
                food_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action TEXT NOT NULL CHECK (action IN ('added', 'removed', 'consumed', 'expired')),
                FOREIGN KEY (food_id) REFERENCES foods (id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ SQLite database created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating SQLite database: {e}")
        return False

def create_env_file():
    """Create .env file with SQLite configuration."""
    env_content = """# Database Configuration (SQLite)
DATABASE_URL=sqlite:///./food_tracking.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Logging
LOG_LEVEL=INFO
"""
    
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file already exists")
        return True
    
    try:
        with open(env_path, "w") as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_database_connection():
    """Test database connection."""
    print("Testing database connection...")
    try:
        from database import test_connection
        if test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Error testing database connection: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up Food Tracking Backend...")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    success = True
    
    # Install requirements
    if not install_requirements():
        success = False
    
    # Create .env file
    if not create_env_file():
        success = False
    
    # Set up SQLite database
    if not setup_sqlite_database():
        success = False
    
    # Test database connection
    if not test_database_connection():
        success = False
    
    print("=" * 50)
    if success:
        print("🎉 Setup completed successfully!")
        print("\nTo start the backend server, run:")
        print("  python main.py")
        print("\nOr with uvicorn:")
        print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print("\nAPI documentation will be available at:")
        print("  http://localhost:8000/docs")
    else:
        print("❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
