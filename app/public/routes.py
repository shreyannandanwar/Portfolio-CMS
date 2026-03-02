from flask import render_template, abort, request
from app.public import public_bp
from app.models.blog import BlogPost
from app.services.github_service import get_github_service


@public_bp.route('/')
def home():
    """Homepage - can be your portfolio landing page later"""
    # Get GitHub data for homepage
    github_service = get_github_service()
    github_data = github_service.get_github_data()
    
    # Get featured repositories (top 6 by stars)
    featured_repos = []
    if github_data and 'repositories' in github_data:
        repos = sorted(
            github_data['repositories'], 
            key=lambda x: x['stars'], 
            reverse=True
        )[:6]
        featured_repos = repos
    
    return render_template('home.html', 
                         github_data=github_data,
                         featured_repos=featured_repos)


@public_bp.route('/blog')
def blog_timeline():
    """Public blog timeline - shows all published posts with search and pagination"""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '', type=str)
    
    # Base query - only published posts
    query = BlogPost.query.filter_by(is_published=True)
    
    # Apply search if provided
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            (BlogPost.title.ilike(search_pattern)) |
            (BlogPost.markdown_content.ilike(search_pattern))
        )
    
    # Paginate results (10 posts per page)
    pagination = query.order_by(BlogPost.created_at.desc()).paginate(
        page=page,
        per_page=10,
        error_out=False
    )
    
    return render_template('blog_timeline.html', 
                         posts=pagination.items,
                         pagination=pagination,
                         search_query=search_query)


@public_bp.route('/blog/<slug>')
def blog_detail(slug):
    """Individual blog post view"""
    # Only show if published
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    return render_template('blog_detail.html', post=post)