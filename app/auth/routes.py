from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.auth import auth_bp
from app.models.user import AdminUser
from app.services.security import check_password


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = AdminUser.query.first()

        if not user or not user.is_active:
            flash("Unauthorized", "error")
            return redirect(url_for("auth.login"))

        if user.username != username or not check_password(password, user.password_hash):
            flash("Invalid credentials", "error")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("admin.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
