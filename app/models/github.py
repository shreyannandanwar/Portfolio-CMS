from datetime import datetime
from app.extensions import db


class GitHubProfile(db.Model):
    __tablename__ = "github_profiles"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)

    avatar_url = db.Column(db.String(500))
    profile_url = db.Column(db.String(500))
    bio = db.Column(db.Text)

    public_repos = db.Column(db.Integer)
    followers = db.Column(db.Integer)
    following = db.Column(db.Integer)

    last_synced_at = db.Column(db.DateTime, default=datetime.utcnow)

    repos = db.relationship(
        "GitHubRepo",
        backref="profile",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<GitHubProfile {self.username}>"


class GitHubRepo(db.Model):
    __tablename__ = "github_repos"

    id = db.Column(db.Integer, primary_key=True)

    profile_id = db.Column(
        db.Integer,
        db.ForeignKey("github_profiles.id"),
        nullable=False
    )

    repo_id = db.Column(db.BigInteger, unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(300), nullable=False)

    description = db.Column(db.Text)
    html_url = db.Column(db.String(500), nullable=False)

    language = db.Column(db.String(100))
    stars = db.Column(db.Integer, default=0)
    forks = db.Column(db.Integer, default=0)

    topics = db.Column(db.Text)  # comma-separated topics
    is_visible = db.Column(db.Boolean, default=True)

    updated_at = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow)

    def has_topic(self, topic: str) -> bool:
        if not self.topics:
            return False
        return topic.lower() in self.topics.lower().split(",")

    def __repr__(self):
        return f"<GitHubRepo {self.full_name}>"

class GitHubCache(db.Model):
    __tablename__ = 'github_cache'

    id = db.Column(db.Integer, primary_key=True)
    # We only ever keep one row (the latest snapshot).
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)

    # Store the full payload as JSON.
    # SQLAlchemy maps JSON → JSONB on PostgreSQL, TEXT on SQLite (dev/test).
    payload = db.Column(db.JSON, nullable=False)

    cached_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<GitHubCache {self.username} @ {self.cached_at}>'
