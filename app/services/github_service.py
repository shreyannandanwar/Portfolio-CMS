import requests
from datetime import datetime, timedelta
import json
import os


class GitHubService:
    """Service for fetching and caching GitHub data"""
    
    def __init__(self, username):
        self.username = username
        self.base_url = "https://api.github.com"
        self.cache_duration = timedelta(
            days=int(os.getenv('GITHUB_CACHE_DURATION_DAYS', 30))
        )
        # ✅ FIX: define cache file path
        os.makedirs('instance', exist_ok=True)
        safe_username = (username or "default").replace("/", "_")
        self.cache_file = os.path.join('instance', f'github_cache_{safe_username}.json')

    def _make_request(self, endpoint):
        """Make request to GitHub API"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Flask-Portfolio-App'
        }
        token = os.getenv('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"GitHub API error: {e}")
            return None

    def _save_to_db(self, data: dict) -> bool:
        """Upsert the cache row in PostgreSQL."""
        try:
            from app.extensions import db
            from app.models.github import GitHubCache

            row = GitHubCache.query.filter_by(username=self.username).first()
            if row:
                row.payload = data
                row.cached_at = datetime.utcnow()
            else:
                row = GitHubCache(
                    username=self.username,
                    payload=data,
                    cached_at=datetime.utcnow(),
                )
                db.session.add(row)
            db.session.commit()
            logger.info('GitHub cache saved to DB for %s', self.username)
            return True
        except Exception as exc:
            logger.error('Error saving GitHub cache to DB: %s', exc)
            return False
    
    def fetch_user_data(self):
        """Fetch user profile data"""
        return self._make_request(f"/users/{self.username}")
    
    def fetch_repositories(self, sort='updated', max_repos=30):
        """Fetch user repositories"""
        repos = self._make_request(
            f"/users/{self.username}/repos?sort={sort}&per_page={max_repos}"
        )
        
        if not repos:
            return []
        
        # Filter and format repository data
        formatted_repos = []
        for repo in repos:
            if not repo.get('fork', False):  # Skip forked repos
                formatted_repos.append({
                    'name': repo['name'],
                    'description': repo.get('description', ''),
                    'url': repo['html_url'],
                    'homepage': repo.get('homepage'),
                    'stars': repo['stargazers_count'],
                    'forks': repo['forks_count'],
                    'language': repo.get('language'),
                    'topics': repo.get('topics', []),
                    'created_at': repo['created_at'],
                    'updated_at': repo['updated_at'],
                    'size': repo['size'],
                })
        
        return formatted_repos
    
    def fetch_user_stats(self):
        """Fetch aggregated user statistics"""
        user_data = self.fetch_user_data()
        repos = self.fetch_repositories(max_repos=100)
        
        if not user_data or not repos:
            return None
        
        # Calculate statistics
        total_stars = sum(repo['stars'] for repo in repos)
        total_forks = sum(repo['forks'] for repo in repos)
        
        languages : dict[str, int] = {}
        for repo in repos:
            lang = repo.get('language')
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        
        # Get top languages
        top_languages = sorted(
            languages.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            'username': self.username,
            'name': user_data.get('name'),
            'bio': user_data.get('bio'),
            'avatar_url': user_data.get('avatar_url'),
            'public_repos': user_data.get('public_repos'),
            'followers': user_data.get('followers'),
            'following': user_data.get('following'),
            'total_stars': total_stars,
            'total_forks': total_forks,
            'top_languages': top_languages,
            'profile_url': user_data.get('html_url'),
        }
    
    def get_cached_data(self):
        """Get data from cache if valid"""
        if not os.path.exists(self.cache_file):
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            
            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cache['cached_at'])
            if datetime.now() - cached_time < self.cache_duration:
                return cache['data']
            
            return None
        except Exception as e:
            print(f"Error reading cache: {e}")
            return None
    
    def save_to_cache(self, data):
        """Save data to cache"""
        try:
            # Ensure instance directory exists
            os.makedirs('instance', exist_ok=True)
            
            cache = {
                'cached_at': datetime.now().isoformat(),
                'data': data
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving cache: {e}")
            return False
    
    def get_github_data(self, force_refresh=False):
        """Get GitHub data (from cache or fresh)"""
        # Try cache first unless forced refresh
        if not force_refresh:
            cached_data = self.get_cached_data()
            if cached_data:
                logger.debug('Serving GitHub data from DB cache')
                return cached_data
        
        print("Fetching fresh GitHub data...")
        logger.info('Fetching fresh GitHub data from API for %s', self.username)
        
        # Fetch fresh data
        user_stats = self.fetch_user_stats()
        repositories = self.fetch_repositories()
        
        if not user_stats or not repositories:
            # If fetch failed, try to return stale cache
            cached_data = self.get_cached_data()
            if cached_data:
                print("API failed, using stale cache")
                return cached_data
            return None
        
        data = {
            'user_stats': user_stats,
            'repositories': repositories,
            'fetched_at': datetime.now().isoformat()
        }
        
        # Save to cache
        self.save_to_cache(data)
        
        return data
    
    def get_cache_info(self):
        """Get information about the cache"""
        if not os.path.exists(self.cache_file):
            return {
                'exists': False,
                'cached_at': None,
                'is_stale': False,
                'age_days': 0
            }
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            
            cached_time = datetime.fromisoformat(cache['cached_at'])
            age = datetime.now() - cached_time
            is_stale = age >= self.cache_duration
            
            return {
                'exists': True,
                'cached_at': cached_time.strftime('%B %d, %Y at %I:%M %p'),
                'is_stale': is_stale,
                'age_days': age.days
            }
        except Exception as e:
            print(f"Error getting cache info: {e}")
            return {
                'exists': False,
                'cached_at': None,
                'is_stale': False,
                'age_days': 0
            }


def get_github_service():
    """Factory function to get GitHub service with configured username"""
    # You can configure your GitHub username here or via environment variable
    username = os.getenv('GITHUB_USERNAME', 'your-github-username')
    return GitHubService(username)