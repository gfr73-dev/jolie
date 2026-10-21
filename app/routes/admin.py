import secrets
import string
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from app import db
from app.models import (
    InstallationType,
    InstallStatus,
    RegisterItTech,
    RegisterUser,
    AccountManager,
)
from app.services.mail import send_mail
from app.services.session import admin_required, master_admin_required


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "managers": AccountManager.query.count(),
        "techs": RegisterItTech.query.count(),
        "statuses": InstallStatus.query.count(),
        "types": InstallationType.query.count(),
    }

    return render_template(
        "admin/dashboard.html",
        installation_types=InstallationType.query.order_by(
            InstallationType.installation_type,
            InstallationType.printer_type,
        ).all(),
        statuses=InstallStatus.query.order_by(InstallStatus.id).all(),
        techs=RegisterItTech.query.order_by(RegisterItTech.tech_user_name).all(),
        users=RegisterUser.query.order_by(RegisterUser.username).all(),
        account_managers=AccountManager.query.order_by(
            AccountManager.account_manager_email
        ).all(),
        stats=stats,
    )


def make_temporary_password():
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    password_chars = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*()-_=+"),
    ]
    password_chars.extend(secrets.choice(alphabet) for _ in range(6))
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def deliver_user_password(user, password, action):
    try:
        return send_mail(
            [user.username],
            f"JOLIE - {action} da palavra-passe",
            f"A sua palavra-passe de acesso ao JOLIE foi definida pelo administrador.\n\n"
            f"Utilizador: {user.username}\n"
            f"Palavra-passe: {password}\n\n"
            "Por segurança, altere a palavra-passe depois de iniciar sessão.",
        )
    except Exception:
        current_app.logger.exception("Failed to email password to user %s", user.id)
        return False


@admin_bp.post("/users")
@master_admin_required
def add_user():
    username = request.form.get("username", "").strip().lower()
    if not username or "@" not in username:
        flash("Indique um endereço de email válido para o utilizador.", "danger")
        return redirect(url_for("admin.dashboard"))
    if RegisterUser.query.filter_by(username=username).first():
        flash("Já existe um utilizador com esse email.", "warning")
        return redirect(url_for("admin.dashboard"))

    user = RegisterUser(
        username=username,
        is_admin=request.form.get("is_admin") == "on",
        is_master_admin=request.form.get("is_master_admin") == "on",
        is_dir_reg=request.form.get("is_dir_reg") == "on",
        is_can_register=request.form.get("is_can_register") == "on",
        is_active=True,
    )
    password = make_temporary_password()
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    if deliver_user_password(user, password, "criação"):
        flash("Utilizador criado e palavra-passe enviada por email.", "success")
    else:
        flash("Utilizador criado, mas o email não foi enviado. Use Reenviar palavra-passe.", "warning")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/users/<int:user_id>/update")
@master_admin_required
def update_user(user_id):
    user = RegisterUser.query.get_or_404(user_id)
    username = request.form.get("username", "").strip().lower()
    if not username or "@" not in username:
        flash("Indique um endereço de email válido para o utilizador.", "danger")
        return redirect(url_for("admin.dashboard"))
    existing = RegisterUser.query.filter(
        RegisterUser.username == username, RegisterUser.id != user.id
    ).first()
    if existing:
        flash("Já existe um utilizador com esse email.", "warning")
        return redirect(url_for("admin.dashboard"))

    user.username = username
    user.is_admin = request.form.get("is_admin") == "on"
    user.is_master_admin = request.form.get("is_master_admin") == "on"
    user.is_dir_reg = request.form.get("is_dir_reg") == "on"
    user.is_can_register = request.form.get("is_can_register") == "on"
    user.is_active = request.form.get("is_active") == "on"
    db.session.commit()
    flash("Utilizador atualizado.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/users/<int:user_id>/resend-password")
@master_admin_required
def resend_user_password(user_id):
    user = RegisterUser.query.get_or_404(user_id)
    old_password_hash = user.password
    password = make_temporary_password()
    user.set_password(password)
    db.session.commit()
    if deliver_user_password(user, password, "reposição"):
        flash("Nova palavra-passe enviada ao utilizador.", "success")
    else:
        user.password = old_password_hash
        db.session.commit()
        flash("O email não foi enviado e a palavra-passe atual foi mantida. Tente novamente.", "warning")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/statuses")
@admin_required
def add_status():
    status = request.form.get("status", "").strip().upper()
    if not status:
        flash("Preencha o status.", "danger")
        return redirect(url_for("admin.dashboard"))

    if InstallStatus.query.filter_by(status=status).first():
        flash("O status já existe.", "warning")
        return redirect(url_for("admin.dashboard"))

    db.session.add(InstallStatus(status=status, active=True))
    db.session.commit()
    flash("Status criado.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/statuses/<int:status_id>/update")
@admin_required
def update_status(status_id):
    record = InstallStatus.query.get_or_404(status_id)
    status = request.form.get("status", "").strip().upper()
    if not status:
        flash("Preencha o status.", "danger")
        return redirect(url_for("admin.dashboard"))

    record.status = status
    record.active = request.form.get("active") == "on"
    db.session.commit()
    flash("Status atualizado.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/statuses/<int:status_id>/toggle")
@admin_required
def toggle_status(status_id):
    record = InstallStatus.query.get_or_404(status_id)
    record.active = not record.active
    db.session.commit()
    flash("Estado do status atualizado.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/techs")
@admin_required
def add_tech():
    name = request.form.get("tech_user_name", "").strip()
    email = request.form.get("tech_user_email", "").strip().lower()
    if not name or not email:
        flash("Preencha o nome e email do técnico.", "danger")
        return redirect(url_for("admin.dashboard"))

    db.session.add(
        RegisterItTech(
            tech_user_name=name,
            tech_user_email=email,
            active=True,
        )
    )
    db.session.commit()
    flash("Técnico criado.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/techs/<int:tech_id>/update")
@admin_required
def update_tech(tech_id):
    tech = RegisterItTech.query.get_or_404(tech_id)
    name = request.form.get("tech_user_name", "").strip()
    email = request.form.get("tech_user_email", "").strip().lower()
    if not name or not email:
        flash("Preencha o nome e email do técnico.", "danger")
        return redirect(url_for("admin.dashboard"))

    tech.tech_user_name = name
    tech.tech_user_email = email
    tech.active = request.form.get("active") == "on"
    db.session.commit()
    flash("Técnico atualizado.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/techs/<int:tech_id>/toggle")
@admin_required
def toggle_tech(tech_id):
    tech = RegisterItTech.query.get_or_404(tech_id)
    tech.active = not tech.active
    db.session.commit()
    flash("Estado do técnico atualizado.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/account-managers")
@admin_required
def add_account_manager():
    manager_name = request.form.get("account_manager", "").strip()
    manager_email = request.form.get("account_manager_email", "").strip().lower()
    dir_reg_email = request.form.get(
        "account_manager_dir_reg_email", ""
    ).strip().lower()
    active = request.form.get("active") == "on"

    if not manager_name:
        flash("Preencha o nome do gestor.", "danger")
        return redirect(url_for("admin.dashboard"))

    if not manager_email or not dir_reg_email:
        flash("Preencha o email do gestor e o email da direção regional.", "danger")
        return redirect(url_for("admin.dashboard"))

    existing = AccountManager.query.filter_by(
        account_manager_email=manager_email
    ).first()

    if existing:
        existing.account_manager = manager_name
        existing.account_manager_dir_reg_email = dir_reg_email
        existing.active = active
        flash("Gestor de conta atualizado.", "success")
    else:
        db.session.add(
            AccountManager(
                account_manager=manager_name,
                account_manager_email=manager_email,
                account_manager_dir_reg_email=dir_reg_email,
                active=active,
            )
        )
        flash("Gestor de conta criado.", "success")

    db.session.commit()
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/account-managers/<int:manager_id>/update")
@admin_required
def update_account_manager(manager_id):
    manager = AccountManager.query.get_or_404(manager_id)
    manager_name = request.form.get("account_manager", "").strip()
    manager_email = request.form.get("account_manager_email", "").strip().lower()
    dir_reg_email = request.form.get(
        "account_manager_dir_reg_email", ""
    ).strip().lower()

    if not manager_name:
        flash("Preencha o nome do gestor.", "danger")
        return redirect(url_for("admin.dashboard"))

    if not manager_email or not dir_reg_email:
        flash("Preencha o email do gestor e o email da direção regional.", "danger")
        return redirect(url_for("admin.dashboard"))

    manager.account_manager = manager_name
    manager.account_manager_email = manager_email
    manager.account_manager_dir_reg_email = dir_reg_email
    manager.active = request.form.get("active") == "on"
    db.session.commit()
    flash("Gestor atualizado.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/account-managers/<int:manager_id>/toggle")
@admin_required
def toggle_account_manager(manager_id):
    manager = AccountManager.query.get_or_404(manager_id)
    manager.active = not manager.active
    db.session.commit()
    flash("Estado do gestor atualizado.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/installation-types")
@admin_required
def add_installation_type():
    record = InstallationType(
        installation_type=request.form.get("installation_type", "").strip(),
        printer_type=request.form.get("printer_type", "").strip(),
        printer_initial_status=request.form.get("printer_initial_status", "")
        .strip()
        .upper(),
        requires_validation=request.form.get("requires_validation") == "on",
        active=True,
    )

    if record.installation_type and record.printer_type and record.printer_initial_status:
        db.session.add(record)
        db.session.commit()
        flash("Tipo de instalação criado.", "success")
    else:
        flash("Preencha todos os campos obrigatórios do tipo de instalação.", "danger")

    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/installation-types/<int:type_id>/update")
@admin_required
def update_installation_type(type_id):
    record = InstallationType.query.get_or_404(type_id)
    record.installation_type = request.form.get("installation_type", "").strip()
    record.printer_type = request.form.get("printer_type", "").strip()
    record.printer_initial_status = request.form.get("printer_initial_status", "") \
        .strip() \
        .upper()
    record.requires_validation = request.form.get("requires_validation") == "on"
    record.active = request.form.get("active") == "on"

    if not record.installation_type or not record.printer_type or not record.printer_initial_status:
        flash("Preencha todos os campos obrigatórios do tipo de instalação.", "danger")
        return redirect(url_for("admin.dashboard"))

    db.session.commit()
    flash("Tipo de instalação atualizado.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/installation-types/<int:type_id>/toggle")
@admin_required
def toggle_installation_type(type_id):
    record = InstallationType.query.get_or_404(type_id)
    record.active = not record.active
    db.session.commit()
    flash("Estado do tipo de instalação atualizado.", "success")
    return redirect(url_for("admin.dashboard"))
