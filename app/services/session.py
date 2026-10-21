from functools import wraps
from flask import session, redirect, url_for, flash, g
from app.models import RegisterUser


def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = RegisterUser.query.get(user_id) if user_id else None
    if g.user is not None and not g.user.is_active:
        session.clear()
        g.user = None


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("auth.login"))
        if not (g.user.is_admin or g.user.is_master_admin):
            flash("Não tem permissões de administrador.", "danger")
            return redirect(url_for("requests.index"))
        return view(**kwargs)
    return wrapped_view


def master_admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("auth.login"))
        if not g.user.is_master_admin:
            flash("Não tem permissões de administrador principal.", "danger")
            return redirect(url_for("requests.index"))
        return view(**kwargs)
    return wrapped_view
