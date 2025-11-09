"""
Security Tests for CSRF Protection
Tests that all endpoints are protected against CSRF attacks
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.dashboard.app import app


class TestCSRFProtection:
    """Test CSRF protection on API endpoints"""

    @pytest.fixture
    def client(self):
        """Create Flask test client"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def client_no_csrf(self):
        """Create Flask test client without CSRF (for testing)"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client

    def get_csrf_token(self, client):
        """Helper to get CSRF token"""
        response = client.get('/api/csrf-token')
        return response.json['csrf_token']

    def test_get_requests_dont_require_csrf(self, client):
        """Test that GET requests work without CSRF token"""
        response = client.get('/api/status')
        # Should succeed even without CSRF token
        assert response.status_code in [200, 401, 404]  # Any non-4XX from CSRF

    def test_post_without_csrf_fails(self, client):
        """Test that POST without CSRF token fails"""
        response = client.post('/api/start', json={'mode': 'paper'})
        # Should return 400 Bad Request due to missing CSRF token
        assert response.status_code == 400

    def test_post_with_csrf_succeeds(self, client):
        """Test that POST with valid CSRF token succeeds"""
        # Get CSRF token
        csrf_token = self.get_csrf_token(client)

        # Make POST request with CSRF token
        response = client.post(
            '/api/start',
            json={'mode': 'paper'},
            headers={'X-CSRFToken': csrf_token}
        )

        # Should not fail due to CSRF (may fail for other reasons)
        assert response.status_code != 400 or b'CSRF' not in response.data

    def test_emergency_stop_requires_csrf(self, client):
        """Test that emergency stop endpoint requires CSRF token"""
        response = client.post('/api/emergency-stop')
        assert response.status_code == 400

    def test_csrf_token_endpoint_works(self, client):
        """Test that CSRF token endpoint returns valid token"""
        response = client.get('/api/csrf-token')
        assert response.status_code == 200
        assert 'csrf_token' in response.json
        assert len(response.json['csrf_token']) > 0

    def test_invalid_csrf_token_fails(self, client):
        """Test that invalid CSRF token is rejected"""
        response = client.post(
            '/api/start',
            json={'mode': 'paper'},
            headers={'X-CSRFToken': 'invalid_token_12345'}
        )
        assert response.status_code == 400

    def test_csrf_in_html_meta_tag(self, client):
        """Test that CSRF token is injected in HTML pages"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'csrf-token' in response.data  # Meta tag present

    def test_all_post_endpoints_protected(self, client):
        """Test that all POST endpoints require CSRF"""
        post_endpoints = [
            '/api/start',
            '/api/stop',
            '/api/pause',
            '/api/resume',
            '/api/emergency-stop',
        ]

        for endpoint in post_endpoints:
            response = client.post(endpoint, json={})
            # Should fail due to CSRF, not other errors
            assert response.status_code == 400, f"{endpoint} not protected"


class TestSessionSecurity:
    """Test session cookie security settings"""

    @pytest.fixture
    def client(self):
        """Create Flask test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_session_cookie_httponly(self):
        """Test that session cookies are HttpOnly"""
        assert app.config.get('SESSION_COOKIE_HTTPONLY', True) is True

    def test_session_cookie_samesite(self):
        """Test that session cookies have SameSite attribute"""
        assert app.config.get('SESSION_COOKIE_SAMESITE') == 'Lax'

    def test_secret_key_is_set(self):
        """Test that Flask secret key is configured"""
        assert app.config['SECRET_KEY'] is not None
        assert len(app.config['SECRET_KEY']) >= 32  # Should be at least 32 bytes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
