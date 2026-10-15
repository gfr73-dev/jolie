from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import (
    InstallationType,
    InstallStatus,
    RegisterItTech,
    RegisterUser,
    AccountManager,
)
from app.services.session import admin_required


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
