#!/bin/bash

# Exit on error
set -e

echo "Installing PRAGI (Personal RAG Interface) for macOS..."

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install system dependencies
echo "Installing system dependencies..."
brew install postgresql@15
brew install redis
brew install tesseract
brew install poppler

# Install pgvector
echo "Installing pgvector..."
brew install libpq
brew services start postgresql@15
export PATH="/usr/local/opt/postgresql@15/bin:$PATH"

# Wait for PostgreSQL to start
sleep 5

# Create database if it doesn't exist
if ! psql -lqt | cut -d \| -f 1 | grep -qw musartao; then
    echo "Creating database..."
    createdb musartao
fi

# Install pgvector extension
echo "Installing pgvector extension..."
psql -d musartao -c 'CREATE EXTENSION IF NOT EXISTS vector;'

# Set up Python virtual environment
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install PRAGI with development dependencies
echo "Installing PRAGI..."
pip install -e ".[dev]"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp sample.env .env
    echo "Please update .env with your configuration"
fi

# Initialize the database
echo "Initializing database..."
python -m src.database.setup_db

# Start Redis
echo "Starting Redis..."
brew services start redis

echo "Installation complete!"
echo "Next steps:"
echo "1. Update the .env file with your configuration"
echo "2. Start the application with: pragi"
echo "3. Access the interface at http://localhost:5009" 