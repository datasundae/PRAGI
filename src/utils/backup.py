"""Script to create a backup package of the application and database."""
import os
import sys
import shutil
import json
from datetime import datetime
import logging
from pathlib import Path
import subprocess
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_backup_package():
    """Create a backup package of the application and database."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Create backup directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"backup_{timestamp}")
        backup_dir.mkdir(exist_ok=True)
        
        logger.info(f"Creating backup package in {backup_dir}")
        
        # 1. Export database
        db_name = os.getenv("DB_NAME", "musartao")
        db_user = os.getenv("DB_USER", "postgres")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        
        # Create database dump
        dump_file = backup_dir / "database_dump.sql"
        logger.info("Exporting database...")
        subprocess.run([
            "pg_dump",
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "-f", str(dump_file)
        ], check=True)
        
        # 2. Copy application files
        logger.info("Copying application files...")
        app_files = [
            "src",
            "requirements.txt",
            "requirements-core.txt",
            ".env",
            "README.md"
        ]
        
        for file in app_files:
            if os.path.exists(file):
                if os.path.isdir(file):
                    shutil.copytree(file, backup_dir / file)
                else:
                    shutil.copy2(file, backup_dir / file)
        
        # 3. Copy logs directory if it exists
        if os.path.exists("logs"):
            shutil.copytree("logs", backup_dir / "logs")
        
        # 4. Create setup instructions
        setup_instructions = f"""Setup Instructions for PRAGI Backup {timestamp}

1. Install Dependencies:
   pip install -r requirements.txt
   pip install -r requirements-core.txt

2. Set up PostgreSQL:
   - Install PostgreSQL if not already installed
   - Create a new database:
     createdb {db_name}
   - Restore the database:
     psql -h localhost -U {db_user} -d {db_name} < database_dump.sql

3. Configure Environment:
   - Copy .env file to your project root
   - Update the following variables in .env:
     - DB_NAME: {db_name}
     - DB_USER: {db_user}
     - DB_HOST: localhost
     - DB_PORT: {db_port}
     - Other environment variables as needed

4. Start the Application:
   PYTHONPATH=/path/to/project python src/web/app.py

Note: Make sure to update any file paths in the configuration that might be specific to the original system.
"""
        
        with open(backup_dir / "SETUP_INSTRUCTIONS.md", "w") as f:
            f.write(setup_instructions)
        
        # 5. Create a zip archive
        logger.info("Creating zip archive...")
        shutil.make_archive(f"pragi_backup_{timestamp}", "zip", backup_dir)
        
        # 6. Clean up temporary directory
        shutil.rmtree(backup_dir)
        
        logger.info(f"Backup package created successfully: pragi_backup_{timestamp}.zip")
        return True
        
    except Exception as e:
        logger.error(f"Error creating backup package: {str(e)}")
        return False

if __name__ == "__main__":
    create_backup_package() 