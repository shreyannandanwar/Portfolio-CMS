from app.extensions import db


class BlogPostTag(db.Model):
    __tablename__ = "blog_post_tags"

    blog_post_id = db.Column(
        db.Integer,
        db.ForeignKey("blog_posts.id"),
        primary_key=True
    )

    tag_id = db.Column(
        db.Integer,
        db.ForeignKey("tags.id"),
        primary_key=True
    )
