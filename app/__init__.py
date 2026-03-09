    from app.admin import admin_bp
    from app.public import public_bp

    admin_prefix = app.config.get('ADMIN_URL_PREFIX', '/control-panel-9f2c8a')

    app.register_blueprint(admin_bp, url_prefix=admin_prefix)
    app.register_blueprint(public_bp)