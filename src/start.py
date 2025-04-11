#!/usr/bin/env python3
"""Startup script for the PRAGI application."""
import os
import sys
import subprocess
import time
import psutil
import redis
import psycopg2
from dotenv import load_dotenv

def check_port(port):
    """Check if a port is in use."""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            return True
    return False

def check_redis():
    """Check if Redis is running and accessible."""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running")
        return True
    except redis.ConnectionError:
        print("❌ Redis is not running")
        return False

def check_postgres():
    """Check if PostgreSQL is running and the database exists."""
    try:
        conn = psycopg2.connect(
            dbname="musartao",
            user="datasundae",
            password="6AV%b9",
            host="localhost",
            port=5432
        )
        conn.close()
        print("✅ PostgreSQL is running and database is accessible")
        return True
    except psycopg2.OperationalError:
        print("❌ PostgreSQL is not running or database is not accessible")
        return False

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'OPENAI_API_KEY',
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET',
        'FLASK_SECRET_KEY'
    ]
    
    load_dotenv()
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def clear_sessions():
    """Clear any existing Flask sessions."""
    session_dir = os.path.join('src', 'web', 'flask_session')
    if os.path.exists(session_dir):
        for file in os.listdir(session_dir):
            file_path = os.path.join(session_dir, file)
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {e}")
    print("✅ Session files cleared")

def main():
    # Check if we're in the correct directory
    if not os.path.exists('src/web/app.py'):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    print("\n🔍 Checking required components...")
    
    # Check environment variables
    env_ok = check_environment()
    
    # Check services
    redis_ok = check_redis()
    postgres_ok = check_postgres()
    
    # Check port availability
    if check_port(5009):
        print("❌ Port 5009 is already in use")
        sys.exit(1)
    print("✅ Port 5009 is available")
    
    # Clear session files
    clear_sessions()
    
    if not all([env_ok, redis_ok, postgres_ok]):
        print("\n❌ Some checks failed. Please fix the issues above and try again.")
        sys.exit(1)
    
    print("\n✅ All checks passed! Starting the application...")
    
    # Set PYTHONPATH
    os.environ['PYTHONPATH'] = os.getcwd()
    
    # Start the Flask application
    try:
        subprocess.run([
            'python3',
            'src/web/app.py'
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Application failed to start: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 