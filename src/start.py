#!/usr/bin/env python3
"""Startup script for the PRAGI application."""
import os
import sys
import subprocess
from dotenv import load_dotenv

def run_tests():
    """Run the test suite."""
    print("\nRunning test suite...")
    result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v'], capture_output=True, text=True)
    
    # Print test output
    print(result.stdout)
    if result.stderr:
        print("Test errors:", result.stderr)
    
    return result.returncode == 0

def main():
    """Main startup function."""
    print("\nStarting PRAGI application...")
    
    # Load environment variables
    load_dotenv()
    
    # Run tests first
    if not run_tests():
        print("\n❌ Tests failed. Please fix the failing tests before starting the application.")
        sys.exit(1)
    
    print("\n✅ All tests passed! Starting application...")
    # Start the Flask application
    os.environ['PYTHONPATH'] = os.getcwd()
    os.system('python3 src/web/app.py')

if __name__ == '__main__':
    main() 