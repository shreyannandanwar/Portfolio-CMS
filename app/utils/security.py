def add_security_headers(app):
    """Add security headers to all responses"""
    
    @app.after_request
    def set_security_headers(response):
        """Set security headers"""
        
        # Content Security Policy
        if app.config.get('ENV') == 'production':
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.github.com;"
            )
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # XSS Protection (for older browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS - Force HTTPS (only in production with HTTPS)
        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains'
            )
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy (disable unnecessary features)
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=()'
        )
        
        return response