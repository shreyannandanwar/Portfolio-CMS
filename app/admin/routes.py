from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.admin import admin_bp
from app.extensions import db, csrf
from app.models.user import AdminUser
from app.models.blog import BlogPost
from app.models.tag import Tag
from app.services.security import check_password
from app.services.markdown_service import convert_markdown_to_html
from app.services.github_service import get_github_service
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from PIL import Image
import uuid


@admin_bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    """Admin login endpoint"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = AdminUser.query.filter_by(username=username).first()
        
        if user and check_password(password, user.password_hash):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('auth/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    """Admin logout"""
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('public.blog_timeline'))


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard overview"""
    total_posts = BlogPost.query.count()
    published_posts = BlogPost.query.filter_by(is_published=True).count()
    draft_posts = total_posts - published_posts
    total_tags = Tag.query.count()
    
    recent_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_posts=total_posts,
                         published_posts=published_posts,
                         draft_posts=draft_posts,
                         total_tags=total_tags,
                         recent_posts=recent_posts)


@admin_bp.route('/posts')
@login_required
def posts_list():
    """List all blog posts"""
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/posts_list.html', posts=posts)


@admin_bp.route('/posts/new', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def post_new():
    """Create new blog post"""
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        markdown_content = request.form.get('content', '').strip()
        tag_names = request.form.get('tags', '').strip()
        is_published = request.form.get('publish') == 'on'
        
        # Validation
        if not title:
            flash('Title is required', 'error')
            return render_template('admin/post_form.html')
        
        if not markdown_content:
            flash('Content is required', 'error')
            return render_template('admin/post_form.html')
        
        # Convert markdown to HTML
        html_content = convert_markdown_to_html(markdown_content)
        
        # Create slug from title
        slug = title.lower().replace(' ', '-')
        # Remove special characters, keep only alphanumeric and hyphens
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        # Check if slug exists, append number if needed
        base_slug = slug
        counter = 1
        while BlogPost.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create post
        post = BlogPost(
            title=title,
            slug=slug,
            markdown_content=markdown_content,
            html_content=html_content,
            is_published=is_published,
            author_id=current_user.id
        )
        
        # Handle tags
        if tag_names:
            for tag_name in tag_names.split(','):
                tag_name = tag_name.strip()
                if tag_name:
                    # Get or create tag
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name, slug=tag_name.lower().replace(' ', '-'))
                        db.session.add(tag)
                    post.tags.append(tag)
        
        # Save to database
        db.session.add(post)
        db.session.commit()
        
        status = "published" if is_published else "saved as draft"
        flash(f'Post "{title}" {status} successfully!', 'success')
        return redirect(url_for('admin.posts_list'))
    
    # GET request - show form
    return render_template('admin/post_form.html', post=None)


@admin_bp.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def post_edit(post_id):
    """Edit existing blog post"""
    post = BlogPost.query.get_or_404(post_id)
    
    if request.method == 'POST':
        post.title = request.form.get('title', '').strip()
        markdown_content = request.form.get('content', '').strip()
        tag_names = request.form.get('tags', '').strip()
        post.is_published = request.form.get('publish') == 'on'
        
        if not post.title or not markdown_content:
            flash('Title and content are required', 'error')
            return render_template('admin/post_form.html', post=post)
        
        # Update content
        post.markdown_content = markdown_content
        post.html_content = convert_markdown_to_html(markdown_content)
        post.updated_at = datetime.utcnow()
        
        # Update tags
        post.tags.clear()
        if tag_names:
            for tag_name in tag_names.split(','):
                tag_name = tag_name.strip()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name, slug=tag_name.lower().replace(' ', '-'))
                        db.session.add(tag)
                    post.tags.append(tag)
        
        db.session.commit()
        flash(f'Post "{post.title}" updated successfully!', 'success')
        return redirect(url_for('admin.posts_list'))
    
    # GET request - show form with existing data
    tag_string = ', '.join([tag.name for tag in post.tags])
    return render_template('admin/post_form.html', post=post, tag_string=tag_string)


@admin_bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
@csrf.exempt
def post_delete(post_id):
    """Delete blog post"""
    post = BlogPost.query.get_or_404(post_id)
    title = post.title
    
    db.session.delete(post)
    db.session.commit()
    
    flash(f'Post "{title}" deleted successfully!', 'success')
    return redirect(url_for('admin.posts_list'))


# Image Upload Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def optimize_image(image_path, max_width=1200, quality=85):
    """Optimize and resize image"""
    try:
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if too large
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save optimized image
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
            return True
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return False


@admin_bp.route('/upload-image', methods=['POST'])
@login_required
@csrf.exempt
def upload_image():
    """Handle image upload"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'}), 400
    
    try:
        # Create uploads directory if it doesn't exist
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generate unique filename
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(upload_folder, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Optimize image
        if file_ext in ['jpg', 'jpeg', 'png']:
            optimize_image(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Return URL
        image_url = f"/static/uploads/{unique_filename}"
        
        return jsonify({
            'success': True,
            'url': image_url,
            'filename': unique_filename,
            'size': file_size
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/github-sync', methods=['GET', 'POST'])
@login_required
def github_sync():
    """GitHub data sync page and handler"""
    github_service = get_github_service()
    
    if request.method == 'POST':
        # Force refresh GitHub data
        try:
            data = github_service.get_github_data(force_refresh=True)
            if data:
                flash('GitHub data refreshed successfully!', 'success')
            else:
                flash('Failed to fetch GitHub data. Please check your username and try again.', 'error')
        except Exception as e:
            flash(f'Error refreshing GitHub data: {str(e)}', 'error')
        
        return redirect(url_for('admin.github_sync'))
    
    # GET request - show sync page
    cache_info = github_service.get_cache_info()
    github_data = github_service.get_cached_data()
    
    return render_template('admin/github_sync.html', 
                         cache_info=cache_info,
                         github_data=github_data)


@admin_bp.route('/api/github-data')
@login_required
def api_github_data():
    """API endpoint to get GitHub data (for AJAX requests)"""
    github_service = get_github_service()
    data = github_service.get_github_data()
    
    if data:
        return jsonify(data), 200
    else:
        return jsonify({'error': 'Failed to fetch GitHub data'}), 500