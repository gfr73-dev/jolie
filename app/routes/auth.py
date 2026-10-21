from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app import db
from app.models import RegisterUser
from app.services.session import load_logged_in_user

auth_bp = Blueprint("auth", __name__)

auth_bp.before_app_request(load_logged_in_user)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = RegisterUser.query.filter_by(username=username, is_active=True).first()
        if not user or not user.check_password(password):
            flash("Utilizador ou password inválidos.", "danger")
            return render_template("login.html", username=username)
        session.clear()
        session["user_id"] = user.id
        flash("Login efetuado com sucesso.", "success")
        return redirect(url_for("requests.index"))
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sessão terminada.", "info")
    return redirect(url_for("auth.login"))
