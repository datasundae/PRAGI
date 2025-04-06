import os
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from src.database.postgres_vector_db import PostgreSQLVectorDB
from src.processing.rag_document import RAGDocument
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from oauthlib.oauth2 import WebApplicationClient
import requests
from werkzeug.middleware.proxy_fix import ProxyFix
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken
import warnings
import secrets
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import re
from flask_session import Session
from typing import List
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import functools
import redis

# Load environment variables
load_dotenv()

# Suppress specific warnings about tokenizers
warnings.filterwarnings("ignore", message=".*tokenizers.*")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Debug environment variables
logger.info(f"GOOGLE_CLIENT_ID: {os.getenv('GOOGLE_CLIENT_ID')}")
logger.info(f"GOOGLE_CLIENT_SECRET: {os.getenv('GOOGLE_CLIENT_SECRET')}")
logger.info(f"GOOGLE_REDIRECT_URI: {os.getenv('GOOGLE_REDIRECT_URI')}")

# Allow OAuthlib to not use HTTPS for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = True  # Enable in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
app.config['SESSION_USE_SIGNER'] = True

# Initialize Flask-Session
Session(app)

# Initialize OpenAI client
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    logger.error("OPENAI_API_KEY environment variable is not set")
    raise ValueError("OpenAI API key is required")

try:
    client = OpenAI(api_key=api_key)
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    raise

# Initialize vector database
vector_db = PostgreSQLVectorDB(
    dbname="musartao",
    user="datasundae",
    password="6AV%b9",
    host="localhost",
    port=5432
)

# Initialize sentence transformer model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Google OAuth2 configuration
CLIENT_SECRETS_FILE = 'google_client_secret_804506683754-9ogj9ju96r0e88fb6v7t7usga753hh0h.apps.googleusercontent.com.json'
if not os.path.exists(CLIENT_SECRETS_FILE):
    raise ValueError(f"Client secrets file not found at: {CLIENT_SECRETS_FILE}")

# Load client secrets
with open(CLIENT_SECRETS_FILE) as f:
    client_secrets = json.load(f)
    GOOGLE_CLIENT_ID = client_secrets['web']['client_id']
    GOOGLE_CLIENT_SECRET = client_secrets['web']['client_secret']

GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://127.0.0.1:5009/callback')
ALLOWED_DOMAINS = ['datasundae.com']  # List of allowed email domains

# OAuth2 scopes
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize rate limiter with more generous limits
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri="memory://"
)

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        
        # Check domain restriction
        email = session.get('user_id', '')  # Changed from user_email to user_id
        domain = email.split('@')[-1] if '@' in email else ''
        if domain not in ALLOWED_DOMAINS:
            session.clear()
            return redirect(url_for('login'))
            
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def before_request():
    """Initialize session before each request."""
    if not session.get('_fresh'):
        session['_fresh'] = True
        session.permanent = True
        logger.info(f"Session initialized: {session}")
    # Ensure session is marked as modified to trigger save
    session.modified = True

@app.after_request
def after_request(response):
    """Ensure session is saved after each request."""
    session.modified = True
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

def init_models():
    """Initialize models after the fork to avoid tokenizer warnings"""
    global vector_db, model
    if vector_db is None:
        try:
            vector_db = PostgreSQLVectorDB()
            logger.info("Successfully connected to vector database")
        except Exception as e:
            logger.error(f"Failed to connect to vector database: {str(e)}")
            raise

def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model("gpt-4-turbo-preview")
    return len(encoding.encode(text))

def get_relevant_context(query: str) -> List[str]:
    """Get relevant context from the vector database."""
    try:
        logger.info(f"Attempting to retrieve context from books database...")
        logger.info(f"Searching for context related to: {query}")
        
        # Perform vector similarity search
        logger.info("Performing vector similarity search...")
        results = vector_db.search(query, k=10)  # Increased k to get more potential matches
        
        if not results:
            logger.info("No relevant documents found")
            return []
            
        logger.info(f"Found {len(results)} relevant documents")
        
        # Filter results by similarity threshold
        filtered_results = [(doc, sim) for doc, sim in results if sim > 0.3]  # Only keep reasonably similar results
        
        if not filtered_results:
            logger.info("No documents passed similarity threshold")
            return []
            
        logger.info(f"Filtered to {len(filtered_results)} relevant documents")
        
        # Process and return context
        context_parts = []
        total_tokens = 0
        max_tokens = 20000  # Limit total tokens to avoid OpenAI rate limits
        max_doc_tokens = 4000  # Maximum tokens per document
        
        for i, (doc, similarity) in enumerate(filtered_results, 1):
            logger.info(f"Processing document {i}/{len(filtered_results)}")
            logger.info(f"Document {i} metadata: {doc.metadata}")  # Log full metadata for debugging
            
            # Get document text from either text or content attribute
            doc_text = getattr(doc, 'text', None) or getattr(doc, 'content', None)
            if not doc_text:
                logger.warning(f"Document {i} has no text or content")
                logger.warning(f"Document {i} attributes: {dir(doc)}")  # Log available attributes
                continue
            
            logger.info(f"Document {i} text length: {len(doc_text)}")
            
            # Truncate document text if needed
            doc_tokens = count_tokens(doc_text)
            if doc_tokens > max_doc_tokens:
                logger.info(f"Document {i} exceeds token limit ({doc_tokens} tokens), truncating...")
                # Truncate text to roughly max_doc_tokens
                encoding = tiktoken.encoding_for_model("gpt-4-turbo-preview")
                tokens = encoding.encode(doc_text)
                doc_text = encoding.decode(tokens[:max_doc_tokens])
                doc_tokens = count_tokens(doc_text)
                logger.info(f"Document {i} truncated to {doc_tokens} tokens")
            
            # Format the document with its metadata
            formatted_doc = f"""
From '{doc.metadata.get('title', 'Unknown Title')}' by {doc.metadata.get('author', 'Unknown Author')}
Page: {doc.metadata.get('page', 'Unknown')}
Similarity Score: {similarity:.4f}

{doc_text}
"""
            
            # Count tokens in the formatted document
            formatted_tokens = count_tokens(formatted_doc)
            logger.info(f"Document {i} formatted token count: {formatted_tokens}")
            
            # Check if adding this document would exceed the token limit
            if total_tokens + formatted_tokens > max_tokens:
                logger.info(f"Token limit reached ({total_tokens} tokens), stopping context collection")
                break
                
            context_parts.append(formatted_doc)
            total_tokens += formatted_tokens
            
        logger.info(f"Successfully retrieved context from vector database")
        logger.info(f"Context length: {len(context_parts)}")
        logger.info(f"Total tokens: {total_tokens}")
        return context_parts
        
    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
        return []

def filter_sensitive_info(text):
    """Filter out sensitive information from text."""
    # Add patterns for sensitive information
    patterns = [
        r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',  # SSN
        r'\b\d{16}\b',  # Credit card numbers
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
        r'\b\d{10}\b',  # Phone numbers
        r'\b\d{9}\b',  # Account numbers
    ]
    
    filtered_text = text
    for pattern in patterns:
        filtered_text = re.sub(pattern, '[REDACTED]', filtered_text)
    return filtered_text

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to home
    if 'user_id' in session:
        logger.info(f"User already logged in: {session.get('user_id')}")
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        return redirect(url_for('google_login'))
        
    # Clear any existing session data
    session.clear()
    logger.info("Session cleared for new login")
    return render_template('login.html')

@app.route('/google_login')
def google_login():
    """Redirect to Google OAuth2 login."""
    try:
        # Create OAuth2 flow using environment variables
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI]
                }
            },
            scopes=SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        session['state'] = state
        logger.info(f"Stored state in session: {state}")
        logger.info(f"Redirecting to Google OAuth2 login with URL: {authorization_url}")
        return redirect(authorization_url)
        
    except Exception as e:
        logger.error(f"Error in google_login: {str(e)}")
        session.clear()
        return redirect(url_for('login'))

@app.route('/callback')
def callback():
    """Handle Google OAuth2 callback."""
    try:
        if 'state' not in session:
            logger.error("No state found in session")
            return redirect(url_for('login'))
            
        state = session['state']
        logger.info(f"Retrieved state from session: {state}")
        logger.info(f"Callback URL: {request.url}")
        
        # Create OAuth2 flow using environment variables
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI]
                }
            },
            scopes=SCOPES,
            state=state,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        
        logger.info("Fetching token...")
        flow.fetch_token(
            authorization_response=request.url
        )
        logger.info("Token fetched successfully")
        
        credentials = flow.credentials
        logger.info("Verifying ID token...")
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, requests.Request(), GOOGLE_CLIENT_ID
        )
        logger.info("ID token verified successfully")
        
        # Check if email domain is allowed
        email = id_info['email']
        domain = email.split('@')[1]
        
        if domain not in ALLOWED_DOMAINS:
            logger.error(f"Access denied for domain: {domain}")
            return "Access denied. Only datasundae.com email addresses are allowed.", 403
        
        # Store user info in session
        session['user_id'] = email
        session['user_name'] = id_info.get('name', email)
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # Make session permanent and ensure it's saved
        session.permanent = True
        session.modified = True
        
        logger.info(f"Successfully logged in user: {email}")
        logger.info(f"Session data after login: {session}")
        return redirect(url_for('home'))
        
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
        session.clear()
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Clear the session and log out the user."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('home.html')

@app.route('/ingest', methods=['POST'])
@login_required
@limiter.limit("100 per minute")
def ingest():
    try:
        data = request.get_json()
        if not data or 'content' not in data or 'person' not in data:
            return jsonify({'error': 'Content and person are required'}), 400

        content = data['content']
        person = data['person']

        if not content.strip() or not person.strip():
            return jsonify({'error': 'Content and person cannot be empty'}), 400

        # Create metadata
        metadata = {
            'person': person,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'web_interface'
        }

        # Create RAG document
        doc = RAGDocument(text=content, metadata=metadata)

        # Add to vector database
        try:
            doc_ids = vector_db.add_documents([doc])
            return jsonify({'success': True, 'doc_ids': doc_ids})
        except Exception as e:
            logger.error(f"Error adding document to vector database: {str(e)}")
            return jsonify({'error': 'Failed to store document'}), 500

    except Exception as e:
        logger.error(f"Error in ingest endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(RateLimitError)
)
def get_openai_response(client, messages, model="gpt-4-turbo-preview", temperature=0.7, max_tokens=1000):
    """Get response from OpenAI with retry logic."""
    try:
        return client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except RateLimitError as e:
        logger.warning(f"OpenAI rate limit hit, will retry: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error in OpenAI API call: {str(e)}")
        raise

@app.route('/chat', methods=['POST'])
@login_required
@limiter.limit("100 per minute")
@csrf.exempt  # Exempt from CSRF for API endpoint
def chat():
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400

        message = data['message']
        if not message.strip():
            return jsonify({'error': 'Message cannot be empty'}), 400

        # Get relevant context
        context = get_relevant_context(message)
        
        # Format system message with context
        system_message = "You are a helpful AI assistant with access to a knowledge base. "
        if context:
            system_message += "Here is some relevant information from the knowledge base:\n\n"
            system_message += "\n\n".join(context)
        else:
            system_message += "No specific information found in the knowledge base for this query."
        
        # Call OpenAI API with retry logic
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return jsonify({
                'response': response.choices[0].message.content,
                'has_context': bool(context)
            })
            
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {str(e)}")
            return jsonify({'error': 'Service is busy. Please try again in a moment.'}), 429
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return jsonify({'error': 'Failed to generate response'}), 500
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def truncate_text(text: str, max_tokens: int) -> str:
    """Truncate text to fit within token limit.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens allowed
        
    Returns:
        Truncated text
    """
    # Simple implementation - split by words and take first N words
    # This is a rough approximation since we're not using the actual tokenizer
    words = text.split()
    return " ".join(words[:max_tokens]) + "..."

@limiter.limit("100 per minute")
@app.route('/query', methods=['POST'])
@csrf.exempt
@login_required
def query():
    try:
        # Validate CSRF token
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing query parameter"}), 400

        query_text = data['query']
        if not query_text or not isinstance(query_text, str):
            return jsonify({"error": "Invalid query parameter"}), 400

        # Perform the search
        results = vector_db.search(query_text, k=5)
        
        # Format results
        formatted_results = []
        for doc, score in results:
            # Convert numpy float to Python float for JSON serialization
            formatted_results.append({
                "text": doc.text,
                "metadata": doc.metadata,
                "score": float(score)
            })
        
        return jsonify({"results": formatted_results}), 200
        
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/protected_resource')
@login_required
@limiter.limit("100 per hour")
def protected_resource():
    """Example protected resource endpoint."""
    try:
        # Get user information from session
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
            
        return jsonify({
            'message': 'Access granted to protected resource',
            'user': user_id
        })
        
    except Exception as e:
        logger.error(f"Error accessing protected resource: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors."""
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({'error': 'An internal server error occurred'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint to verify critical components."""
    status = {
        'status': 'healthy',
        'components': {
            'session': False,
            'database': False,
            'openai': False
        },
        'timestamp': datetime.now().isoformat()
    }
    
    # Test session
    try:
        session['health_check'] = True
        del session['health_check']
        status['components']['session'] = True
    except Exception as e:
        app.logger.error(f"Session health check failed: {str(e)}")
    
    # Test database
    try:
        db = PostgreSQLVectorDB()
        db.test_connection()
        status['components']['database'] = True
    except Exception as e:
        app.logger.error(f"Database health check failed: {str(e)}")
    
    # Test OpenAI (just check if key exists)
    try:
        if client:
            status['components']['openai'] = True
    except Exception as e:
        app.logger.error(f"OpenAI health check failed: {str(e)}")
    
    return jsonify(status)

if __name__ == '__main__':
    app.run(debug=True, port=5009) 