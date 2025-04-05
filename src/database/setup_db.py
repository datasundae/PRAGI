"""Database initialization script for PRAGI."""
import os
import sys
from pathlib import Path
import psycopg2
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database using the SQL script."""
    # Load environment variables
    load_dotenv()
    
    # Get database connection parameters from environment
    db_params = {
        "dbname": os.getenv("DB_NAME", "musartao"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432))
    }
    
    # Get the SQL file path
    sql_file = Path(__file__).parent / 'init_db.sql'
    
    try:
        # First try to connect to PostgreSQL server
        logger.info("Connecting to PostgreSQL server...")
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        
        # Create database if it doesn't exist
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_params["dbname"],))
            if not cur.fetchone():
                logger.info(f"Creating database {db_params['dbname']}...")
                # Close existing connections to the database
                conn.close()
                
                # Connect to default database to create new database
                db_params["dbname"] = "postgres"
                conn = psycopg2.connect(**db_params)
                conn.autocommit = True
                
                with conn.cursor() as cur:
                    cur.execute(f"CREATE DATABASE {os.getenv('DB_NAME', 'musartao')}")
                conn.close()
                
                # Reconnect to the new database
                db_params["dbname"] = os.getenv("DB_NAME", "musartao")
                conn = psycopg2.connect(**db_params)
                conn.autocommit = True
        
        # Read and execute the SQL file
        logger.info("Reading SQL initialization file...")
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        logger.info("Executing SQL initialization script...")
        with conn.cursor() as cur:
            cur.execute(sql_script)
        
        logger.info("Database initialization completed successfully!")
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {str(e)}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error(f"SQL file not found: {sql_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_database() 