from setuptools import setup, find_packages
import os
from typing import List

def read_requirements(filename: str) -> List[str]:
    """Read requirements from file."""
    with open(filename) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read the contents of README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pragi",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "flask",
        "flask-limiter",
        "flask-wtf",
        "flask-session",
        "sentence-transformers",
        "psycopg2-binary",
        "python-dotenv",
        "cryptography",
        "numpy",
        "openai",
        "tiktoken",
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client",
        "pdf2image",
        "beautifulsoup4",
        "requests",
        "werkzeug",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "black>=24.1.0",
            "isort>=5.13.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pragi=pragi.web.app:main",
        ],
    },
    author="datasundae",
    author_email="hagen@datasundae.com",
    description="A modular RAG system for personal document management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="rag, nlp, document-management, vector-database, openai",
    url="https://github.com/datasundae/PRAGI",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        "pragi": [
            "templates/*.html",
            "static/*",
            "database/init_db.sql",
        ],
    },
    data_files=[
        ("", ["LICENSE", "README.md", "requirements.txt", "sample.env"]),
    ],
) 