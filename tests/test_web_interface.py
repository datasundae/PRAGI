import unittest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, session
from src.web.app import app
from src.database.db_connection import db
from src.database.postgres_vector_db import PostgreSQLVectorDB
import os
from pathlib import Path
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import numpy as np

class TestWebBasics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.app = app.test_client()
        cls.app.testing = True
        cls.project_root = str(Path(__file__).parent.parent)

    def setUp(self):
        """Set up before each test."""
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page_redirect(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login' in response.location)

    def test_login_page_loads(self):
        """Test that the login page loads with correct elements."""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign in with Google', response.data)

    def test_static_files_serve(self):
        """Test that static files are served correctly."""
        response = self.app.get('/static/css/style.css')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/css', response.content_type)

class TestOAuthFlow(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Mock OAuth flow
        self.mock_flow = Mock(spec=Flow)
        self.mock_flow.authorization_url.return_value = ('https://mock-auth-url', 'mock-state')

    @patch('google_auth_oauthlib.flow.Flow.from_client_config')
    def test_google_login_initialization(self, mock_flow_create):
        """Test Google login initialization and redirect."""
        mock_flow_create.return_value = self.mock_flow
        
        with self.app as client:
            response = client.get('/google_login')
            self.assertEqual(response.status_code, 302)
            self.assertTrue(session.get('state'))
            self.mock_flow.authorization_url.assert_called_once()

    @patch('google_auth_oauthlib.flow.Flow.from_client_config')
    def test_oauth_callback_success(self, mock_flow_create):
        """Test successful OAuth callback handling."""
        mock_flow = Mock(spec=Flow)
        mock_flow_create.return_value = mock_flow
        mock_flow.fetch_token.return_value = {'access_token': 'mock-token'}
        mock_flow.credentials = Mock(spec=Credentials)
        
        with self.app as client:
            with client.session_transaction() as sess:
                sess['state'] = 'test-state'
            
            response = client.get('/callback?state=test-state&code=test-code')
            self.assertEqual(response.status_code, 302)
            self.assertTrue('/' in response.location)

    def test_oauth_callback_invalid_state(self):
        """Test OAuth callback with invalid state."""
        with self.app as client:
            response = client.get('/callback?state=invalid-state&code=test-code')
            self.assertEqual(response.status_code, 302)
            self.assertTrue('/login' in response.location)

class TestDatabaseOperations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app.test_client()
        cls.app.testing = True
        # Set up test database connection
        cls.test_db = PostgreSQLVectorDB(
            dbname="musartao",
            user="datasundae",
            password="6AV%b9",
            host="localhost",
            port=5432
        )

    def setUp(self):
        """Create test session and mock authentication."""
        self.app = app.test_client()
        with self.app.session_transaction() as sess:
            sess['authenticated'] = True
            sess['user_email'] = 'test@datasundae.com'

    @patch('src.database.postgres_vector_db.PostgreSQLVectorDB.search')
    def test_vector_search(self, mock_search):
        """Test vector search functionality."""
        # Mock search results
        mock_results = [
            (Mock(text="Test document 1", metadata={"title": "Test 1"}), 0.95),
            (Mock(text="Test document 2", metadata={"title": "Test 2"}), 0.85)
        ]
        mock_search.return_value = mock_results
        
        response = self.app.post('/query', json={
            'query': 'test query',
            'max_results': 2
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['results']), 2)
        mock_search.assert_called_once()

    def test_invalid_query(self):
        """Test handling of invalid query parameters."""
        response = self.app.post('/query', json={
            'query': '',  # Empty query
            'max_results': 5
        })
        self.assertEqual(response.status_code, 400)

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_session_expiry(self):
        """Test that expired sessions are handled correctly."""
        with self.app as client:
            # Set an expired session
            with client.session_transaction() as sess:
                sess['authenticated'] = True
                sess['user_email'] = 'test@datasundae.com'
                sess.permanent = True
                # Simulate expired session
                from datetime import datetime, timedelta
                sess._expires = datetime.utcnow() - timedelta(days=1)
            
            response = client.get('/')
            self.assertEqual(response.status_code, 302)
            self.assertTrue('/login' in response.location)

    def test_unauthorized_access(self):
        """Test that unauthorized access is prevented."""
        response = self.app.get('/protected_resource')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login' in response.location)

    def test_domain_restriction(self):
        """Test that only allowed domains can access the application."""
        with self.app as client:
            with client.session_transaction() as sess:
                sess['user_email'] = 'test@unauthorized-domain.com'
            
            response = client.get('/')
            self.assertEqual(response.status_code, 302)
            self.assertTrue('/login' in response.location)

    def test_csrf_protection(self):
        """Test CSRF protection on POST endpoints."""
        response = self.app.post('/query', json={
            'query': 'test'
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 400)  # Should fail without CSRF token

class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with self.app.session_transaction() as sess:
            sess['authenticated'] = True
            sess['user_email'] = 'test@datasundae.com'

    @patch('src.database.postgres_vector_db.PostgreSQLVectorDB.search')
    def test_database_error_handling(self, mock_search):
        """Test handling of database errors."""
        mock_search.side_effect = Exception("Database error")
        
        response = self.app.post('/query', json={
            'query': 'test query',
            'max_results': 5
        })
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Make multiple rapid requests
        responses = []
        for _ in range(60):  # Exceed rate limit
            response = self.app.post('/query', json={
                'query': 'test query'
            })
            responses.append(response.status_code)
        
        self.assertIn(429, responses)  # Should see rate limit error

if __name__ == '__main__':
    unittest.main() 