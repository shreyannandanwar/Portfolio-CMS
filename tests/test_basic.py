import pytest
import sys
import os
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import AdminUser
from app.models.blog import BlogPost
from app.services.security import hash_password


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create test admin user (no email field in AdminUser model)
        admin = AdminUser(
            username='testadmin',
            password_hash=hash_password('testpass123')
        )
        db.session.add(admin)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Create authenticated test client"""
    # Login
    client.post('/control-panel-9f2c8a/login', data={
        'username': 'testadmin',
        'password': 'testpass123'
    })
    return client


class TestPublicRoutes:
    """Test public-facing routes"""
    
    def test_homepage(self, client):
        """Test homepage loads"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Portfolio' in response.data or b'Welcome' in response.data
    
    def test_blog_timeline(self, client):
        """Test blog timeline loads"""
        response = client.get('/blog')
        assert response.status_code == 200
        assert b'Writing' in response.data
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'


class TestAuthentication:
    """Test authentication system"""
    
    def test_login_page_loads(self, client):
        """Test login page is accessible"""
        response = client.get('/control-panel-9f2c8a/login')
        assert response.status_code == 200
        assert b'Login' in response.data or b'login' in response.data
    
    def test_valid_login(self, client):
        """Test login with valid credentials"""
        response = client.post('/control-panel-9f2c8a/login', data={
            'username': 'testadmin',
            'password': 'testpass123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'dashboard' in response.data
    
    def test_invalid_login(self, client):
        """Test login with invalid credentials"""
        response = client.post('/control-panel-9f2c8a/login', data={
            'username': 'testadmin',
            'password': 'wrongpassword'
        })
        assert b'Invalid' in response.data or b'invalid' in response.data
    
    def test_dashboard_requires_auth(self, client):
        """Test dashboard requires authentication"""
        response = client.get('/control-panel-9f2c8a/dashboard')
        assert response.status_code == 302  # Redirect to login
    
    def test_logout(self, auth_client):
        """Test logout functionality"""
        response = auth_client.get('/control-panel-9f2c8a/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify can't access dashboard after logout
        response = auth_client.get('/control-panel-9f2c8a/dashboard')
        assert response.status_code == 302


class TestBlogFunctionality:
    """Test blog CRUD operations"""
    
    def test_create_post(self, auth_client, app):
        """Test creating a blog post"""
        response = auth_client.post('/control-panel-9f2c8a/posts/new', data={
            'title': 'Test Post',
            'content': '# Test Content\n\nThis is a test.',
            'tags': 'test, python',
            'publish': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify post was created
        with app.app_context():
            post = BlogPost.query.filter_by(title='Test Post').first()
            assert post is not None
            assert post.is_published == True
            assert 'test' in [tag.name for tag in post.tags]
    
    def test_view_published_post(self, auth_client, app, client):
        """Test viewing a published post"""
        # Create post
        auth_client.post('/control-panel-9f2c8a/posts/new', data={
            'title': 'Public Test Post',
            'content': 'Public content',
            'tags': 'test',
            'publish': 'on'
        })
        
        # Get post slug
        with app.app_context():
            post = BlogPost.query.filter_by(title='Public Test Post').first()
            slug = post.slug
        
        # Verify public can view it
        response = client.get(f'/blog/{slug}')
        assert response.status_code == 200
        assert b'Public Test Post' in response.data
    
    def test_draft_not_public(self, auth_client, app, client):
        """Test draft posts are not publicly visible"""
        # Create draft
        auth_client.post('/control-panel-9f2c8a/posts/new', data={
            'title': 'Draft Post',
            'content': 'Draft content',
            'tags': 'test'
            # No publish checkbox
        })
        
        # Get post slug
        with app.app_context():
            post = BlogPost.query.filter_by(title='Draft Post').first()
            slug = post.slug
        
        # Verify public can't view it
        response = client.get(f'/blog/{slug}')
        assert response.status_code == 404


class TestErrorPages:
    """Test custom error pages"""
    
    def test_404_error(self, client):
        """Test 404 error page"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        assert b'404' in response.data or b'Not Found' in response.data
    
    def test_403_error(self, client):
        """Test 403 error when accessing admin without auth"""
        response = client.get('/control-panel-9f2c8a/dashboard')
        assert response.status_code == 302  # Redirects to login


class TestGitHubIntegration:
    """Test GitHub sync functionality"""
    
    def test_github_sync_page_requires_auth(self, client):
        """Test GitHub sync requires authentication"""
        response = client.get('/control-panel-9f2c8a/github-sync')
        assert response.status_code == 302
    
    def test_github_sync_page_loads(self, auth_client):
        """Test GitHub sync page loads for authenticated users"""
        response = auth_client.get('/control-panel-9f2c8a/github-sync')
        assert response.status_code == 200
        assert b'GitHub' in response.data or b'github' in response.data


class TestProductionDbCreateAll:
    """Ensure db.create_all() is not called on production startup unless AUTO_CREATE_DB is set."""

    _PROD_ENV = {
        'SECRET_KEY': 'test-secret-key-for-prod-tests',
        'DATABASE_URL': 'postgresql://user:pass@localhost/testdb',
    }

    def test_production_skips_create_all_by_default(self):
        """create_app('production') must NOT call db.create_all() without AUTO_CREATE_DB."""
        env_patch = {**self._PROD_ENV}
        env_patch.pop('AUTO_CREATE_DB', None)

        with patch.dict(os.environ, env_patch, clear=False):
            os.environ.pop('AUTO_CREATE_DB', None)
            with patch('app.extensions.db.create_all') as mock_create_all:
                try:
                    create_app('production')
                except Exception:
                    # A connection error is acceptable; what matters is create_all was not called.
                    pass
                mock_create_all.assert_not_called()

    def test_production_calls_create_all_when_auto_create_db_set(self):
        """create_app('production') MUST call db.create_all() when AUTO_CREATE_DB=1."""
        env_patch = {**self._PROD_ENV, 'AUTO_CREATE_DB': '1'}

        with patch.dict(os.environ, env_patch, clear=False):
            with patch('app.extensions.db.create_all') as mock_create_all:
                try:
                    create_app('production')
                except Exception:
                    pass
                mock_create_all.assert_called_once()

    def test_development_always_calls_create_all(self):
        """Development/testing environments must always call db.create_all() regardless of AUTO_CREATE_DB."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('AUTO_CREATE_DB', None)
            with patch('app.extensions.db.create_all') as mock_create_all:
                try:
                    create_app('testing')
                except Exception:
                    # A missing-module or connection error is acceptable;
                    # what matters is that create_all WAS called.
                    pass
                mock_create_all.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])