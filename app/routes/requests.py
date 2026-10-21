import re
import uuid
from html import escape
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    g,
    current_app,
)
from sqlalchemy import inspect as sqlalchemy_inspect, or_
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import (
    RegisterRequest,
    InstallationType,
    InstallStatus,
    RegisterItTech,
    AccountManager,
    RegisterRequestHistory,
)
from app.services.session import login_required
from app.services.as400 import lookup_account
from app.services.mail import send_mail, send_html_mail
from app.services.normalizers import (
    parse_date,
    parse_time,
    upper,
    lower,
    proper,
    empty_to_none,
)

requests_bp = Blueprint("requests", __name__)
ACCOUNT_RE = re.compile(r"^\d{8}$")
STATUS_AWAITING_PRINTER_PICKUP = "AGUARDA RECOLHA IMPRESSORA"
STATUS_PRINTER_COLLECTED = "IMPRESSORA RECOLHIDA"


def can_register(user):
    return bool(user and (user.is_can_register or user.is_admin or user.is_master_admin))

STATUS_AWAITING_PRINTER_VALIDATION = "Aguarda Validação Impressora"
STATUS_PRINTER_VALIDATED = "IMPRESSORA VALIDADA"
STATUS_PRINTER_NOT_VALIDATED = "IMPRESSORA NÃO VALIDADA"


def ensure_status_exists(status_name):
    """Ensure workflow statuses used by business rules exist in install_status."""
    if not status_name:
        return

    exists = InstallStatus.query.filter_by(status=status_name).first()
    if not exists:
        db.session.add(InstallStatus(status=status_name))
        db.session.flush()


def set_request_status(req, status_name):
    """Set request status and keep install_status synchronized."""
    ensure_status_exists(status_name)
    req.status = status_name


def get_catalogs():
    return {
        "installation_types": InstallationType.query.order_by(
            InstallationType.installation_type, InstallationType.printer_type
        ).all(),
        "statuses": InstallStatus.query.order_by(InstallStatus.id).all(),
        "techs": RegisterItTech.query.order_by(RegisterItTech.tech_user_name).all(),
        "account_managers": AccountManager.query.filter_by(active=True)
        .order_by(AccountManager.account_manager_email)
        .all(),
        "quantities": [str(i) for i in range(1, 21)],
        "usb_cables": [
            "Ethernet",
            "Parallel",
            "Print Server Cliente",
            "Print Server DPD",
            "RS232",
            "RS232 Usb Adapt Cliente",
            "RS232 Usb Adapt DPD",
            "Usb",
        ],
    }


def selected_tech(tech_id):
    if not tech_id:
        return None
    return RegisterItTech.query.get(int(tech_id))


@requests_bp.route("/")
@login_required
def index():

    status_filter = request.args.get("status", "").strip()
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)

    query = RegisterRequest.query

    if status_filter:
        query = query.filter(RegisterRequest.status == status_filter)

    if search:
        query = query.filter(
            or_(
                RegisterRequest.account.ilike(f"%{search}%"),
                RegisterRequest.name.ilike(f"%{search}%"),
                RegisterRequest.account_manager.ilike(f"%{search}%"),
                RegisterRequest.printer_requested.ilike(f"%{search}%"),
                RegisterRequest.city.ilike(f"%{search}%"),
            )
        )
    query = query.order_by(RegisterRequest.account.asc())

    pagination = query.paginate(page=page, per_page=25, error_out=False)

    return render_template(
        "requests/index.html",
        requests=pagination.items,
        pagination=pagination,
        search=search,
        status_filter=status_filter,
        statuses=InstallStatus.query.order_by(InstallStatus.id).all(),
    )


@requests_bp.post("/requests/lookup")
@login_required
def lookup():
    if not can_register(g.user):
        return jsonify({"ok": False, "message": "NÃ£o tem permissÃµes para criar pedidos."}), 403
    account = request.form.get("account", "").strip()
    if not ACCOUNT_RE.match(account):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "A conta deve ter exatamente 8 dígitos numéricos.",
                }
            ),
            400,
        )
    if RegisterRequest.query.filter_by(account=account).first():
        return (
            jsonify({"ok": False, "message": "Conta já instalada", "duplicate": True}),
            409,
        )
    data = lookup_account(account)
    if not data:
        return jsonify({"ok": False, "message": "Conta não encontrada no AS400."}), 404
    return jsonify({"ok": True, "data": data})


@requests_bp.route("/requests/new", methods=["GET", "POST"])
@login_required
def create_request():
    if not can_register(g.user):
        flash("NÃ£o tem permissÃµes para criar pedidos.", "danger")
        return redirect(url_for("requests.index"))
    catalogs = get_catalogs()
    if request.method == "POST":
        account = request.form.get("account", "").strip()
        if not ACCOUNT_RE.match(account):
            flash(
                "A conta deve ter exatamente 8 dígitos numéricos. Nenhuma consulta ao AS400 foi efetuada.",
                "danger",
            )
            return render_template(
                "requests/form.html",
                mode="create",
                req=None,
                form_data=request.form,
                **catalogs,
            )
        if RegisterRequest.query.filter_by(account=account).first():
            flash("Conta já instalada", "warning")
            return render_template(
                "requests/form.html", mode="create", req=None, **catalogs
            )

        installation_type = InstallationType.query.get(
            request.form.get("installation_type_id")
        )
        if not installation_type:
            flash("Selecione o tipo de instalação/impressora.", "danger")
            return render_template(
                "requests/form.html", mode="create", req=None, **catalogs
            )

        manager = AccountManager.query.get(request.form.get("account_manager_id"))
        if not manager or not manager.active:
            flash("Não selecionou o Gestor de Conta.", "danger")
            return render_template(
                "requests/form.html", mode="create", req=None, **catalogs
            )

        tech = selected_tech(request.form.get("account_it_id"))
        if not tech:
            flash("Não preencheu o campo Gestor IT Instalação.", "danger")
            return render_template(
                "requests/form.html", mode="create", req=None, **catalogs
            )

        required = {
            "phn": "Não preencheu o Campo do Telefone.",
            "contact": "Não preencheu o Campo do Contacto.",
            "envios_dia": "Não preencheu o número de envios diários.",
        }
        for field, message in required.items():
            if not request.form.get(field, "").strip():
                flash(message, "danger")
                return render_template(
                    "requests/form.html", mode="create", req=None, **catalogs
                )

        req = RegisterRequest(
            docuid=uuid.uuid4().hex,
            qty=request.form.get("qty", "1"),
            createdby=g.user.username,
            install_date=parse_date(request.form.get("install_date")),
            date_schedule=parse_date(request.form.get("date_schedule")),
            time_schedule=parse_time(request.form.get("time_schedule")),
            status=installation_type.printer_initial_status,
            install_type=installation_type.installation_type,
            account=account,
            ccc=empty_to_none(request.form.get("ccc", "")),
            name=upper(request.form.get("name", "")),
            address1=upper(request.form.get("address1", "")),
            address2=upper(request.form.get("address2", "")),
            zip=empty_to_none(request.form.get("zip", "")),
            city=upper(request.form.get("city", "")),
            no_values_from_odbc=empty_to_none(
                request.form.get("no_values_from_odbc", "ODBC")
            ),
            phn=request.form.get("phn", "").strip(),
            contact=proper(request.form.get("contact", "")),
            email=lower(request.form.get("email", "")),
            gps_n=empty_to_none(request.form.get("gps_n", "")),
            gps_n_1=empty_to_none(request.form.get("gps_n_1", "")),
            account_manager=manager.account_manager,
            account_manager_email=manager.account_manager_email,
            account_dir_reg=manager.account_manager_dir_reg_email,
            printer_requested=installation_type.printer_type,
            printer_install_type=installation_type.installation_type,
            envios_dia=request.form.get("envios_dia", "").strip(),
            printer_requested_qty=request.form.get("printer_requested_qty", "1"),
            account_it=tech.tech_user_name,
            account_it_email=tech.tech_user_email,
            account_it_support=empty_to_none(
                request.form.get("account_it_support", "A preencher pelo DSI")
            ),
            printer_1=empty_to_none(request.form.get("printer_1", "")),
            usb_cable_1=empty_to_none(request.form.get("usb_cable_1", "9 Pin Cable")),
            adapt_925_1=request.form.get("adapt_925_1", "NO"),
            key_1=empty_to_none(request.form.get("key_1", "")),
            obs_migracao=proper(request.form.get("obs_migracao", "")),
            normalizada_1=request.form.get("normalizada_1", "NÃO"),
            db_ok_1=empty_to_none(request.form.get("db_ok_1", "")),
            db_nok_1=empty_to_none(request.form.get("db_nok_1", "")),
            obs_normalizada_1=proper(request.form.get("obs_normalizada_1", "")),
            requires_printer_validation=installation_type.requires_validation,
        )

        try:
            db.session.add(req)
            if req.requires_printer_validation:
                set_request_status(req, STATUS_AWAITING_PRINTER_VALIDATION)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Conta já instalada", "warning")
            return render_template(
                "requests/form.html", mode="create", req=None, **catalogs
            )

        record_url = url_for("requests.view_request", request_id=req.id, _external=True)
        if req.requires_printer_validation:
            send_mail(
                [req.account_dir_reg],
                f"Validação de impressora pendente - Conta {req.account}",
                "Foi criado um pedido de instalação que necessita de validação.\n\n"
                f"Conta: {req.account}\n"
                f"Cliente: {req.name}\n"
                f"Gestor de Conta: {req.account_manager_email}\n\n"
                f"Validar aqui:\n{record_url}",
            )
        else:
            send_mail(
                [req.account_it_email],
                f"Novo pedido de instalação - Conta {req.account}",
                f"Foi criado um novo pedido de instalação para a conta {req.account}.\n\nAbrir pedido:\n{record_url}",
            )
        flash("Pedido gravado com sucesso.", "success")
        return redirect(url_for("requests.view_request", request_id=req.id))
    return render_template("requests/form.html", mode="create", req=None, **catalogs)


@requests_bp.route("/requests/<int:request_id>", methods=["GET", "POST"])
@login_required
def view_request(request_id):
    req = RegisterRequest.query.get_or_404(request_id)
    catalogs = get_catalogs()
    if request.method == "POST":
        if g.user.is_admin:
            new_status = request.form.get("status", req.status).strip()
            if new_status:
                set_request_status(req, new_status)
            req.install_date = parse_date(request.form.get("install_date"))
            req.date_schedule = parse_date(request.form.get("date_schedule"))
            print("RAW:", request.form.get("time_schedule"))
            print("PARSED:", parse_time(request.form.get("time_schedule")))
            req.time_schedule = parse_time(request.form.get("time_schedule"))
            req.account_it_support = empty_to_none(
                request.form.get("account_it_support", req.account_it_support or "")
            )
            req.printer_1 = empty_to_none(
                request.form.get("printer_1", req.printer_1 or "")
            )
            req.usb_cable_1 = empty_to_none(
                request.form.get("usb_cable_1", req.usb_cable_1 or "")
            )
            req.adapt_925_1 = request.form.get("adapt_925_1", req.adapt_925_1 or "NO")
            req.key_1 = empty_to_none(request.form.get("key_1", req.key_1 or ""))
            req.db_ok_1 = empty_to_none(request.form.get("db_ok_1", req.db_ok_1 or ""))
            req.db_nok_1 = empty_to_none(
                request.form.get("db_nok_1", req.db_nok_1 or "")
            )
        db.session.commit()
        flash("Pedido atualizado.", "success")
        return redirect(url_for("requests.view_request", request_id=req.id))
    return render_template("requests/view.html", req=req, **catalogs)


@requests_bp.post("/requests/<int:request_id>/details")
@login_required
def update_request_details(request_id):
    if not g.user.is_admin:
        flash("Não tem permissões de administrador.", "danger")
        return redirect(url_for("requests.view_request", request_id=request_id))

    req = RegisterRequest.query.get_or_404(request_id)
    manager = AccountManager.query.get(request.form.get("account_manager_id"))
    tech = selected_tech(request.form.get("account_it_id"))
    installation_type = InstallationType.query.get(
        request.form.get("installation_type_id")
    )
    contact = request.form.get("contact", "").strip()
    phn = request.form.get("phn", "").strip()
    email = request.form.get("email", "").strip().lower()
    quantity = request.form.get("printer_requested_qty", "").strip()

    if not manager or not manager.active:
        flash("Selecione um gestor de conta ativo.", "danger")
        return redirect(url_for("requests.view_request", request_id=req.id))
    if not tech:
        flash("Selecione um técnico IT.", "danger")
        return redirect(url_for("requests.view_request", request_id=req.id))
    if not installation_type:
        flash("Selecione o tipo de instalação e impressora.", "danger")
        return redirect(url_for("requests.view_request", request_id=req.id))
    if not all((contact, phn)):
        flash("Contacto e telefone são obrigatórios.", "danger")
        return redirect(url_for("requests.view_request", request_id=req.id))
    if len(contact) > 160 or len(phn) > 80 or len(email) > 255:
        flash("Um ou mais campos de contacto excedem o tamanho permitido.", "danger")
        return redirect(url_for("requests.view_request", request_id=req.id))
    if email and "@" not in email:
        flash("Indique um endereço de email válido.", "danger")
        return redirect(url_for("requests.view_request", request_id=req.id))
    if quantity not in get_catalogs()["quantities"]:
        flash("Selecione uma quantidade entre 1 e 20.", "danger")
        return redirect(url_for("requests.view_request", request_id=req.id))

    req.account_manager = manager.account_manager
    req.account_manager_email = manager.account_manager_email
    req.account_dir_reg = manager.account_manager_dir_reg_email
    req.account_it = tech.tech_user_name
    req.account_it_email = tech.tech_user_email
    req.install_type = installation_type.installation_type
    req.printer_install_type = installation_type.installation_type
    req.printer_requested = installation_type.printer_type
    req.printer_requested_qty = quantity
    req.contact = contact
    req.phn = phn
    req.email = email or None
    db.session.commit()
    flash("Dados do pedido atualizados.", "success")
    return redirect(url_for("requests.view_request", request_id=req.id))


@requests_bp.route("/validation")
@login_required
def validation_queue():
    rows = (
        RegisterRequest.query.filter(
            RegisterRequest.requires_printer_validation.is_(True),
            RegisterRequest.is_printer_validated.is_(None),
        )
        .order_by(RegisterRequest.creation.desc())
        .all()
    )
    return render_template("requests/validation_queue.html", requests=rows)


@requests_bp.route("/requests/<int:request_id>/validate-printer", methods=["POST"])
@login_required
def validate_printer(request_id):
    req = RegisterRequest.query.get_or_404(request_id)

    if req.is_printer_validated:
        flash(
            "A validação da impressora já foi concluída e não pode ser alterada.",
            "warning",
        )
        return redirect(url_for("requests.view_request", request_id=req.id))

    if not (g.user.is_admin or g.user.is_dir_reg):
        flash("Não tem permissões para alterar a validação de impressora.", "danger")
        return redirect(url_for("requests.view_request", request_id=req.id))

    decision = request.form.get("is_printer_validated")
    if decision not in ["validated", "not_validated"]:
        flash("Selecione uma opção de validação.", "danger")
        return redirect(url_for("requests.view_request", request_id=req.id))

    req.is_printer_validated = decision

    if decision == "validated":
        set_request_status(req, STATUS_PRINTER_VALIDATED)
    elif decision == "not_validated":
        set_request_status(req, STATUS_PRINTER_NOT_VALIDATED)

    req.printer_validation_changed_by = g.user.username
    req.printer_validation_changed_at = datetime.utcnow()
    db.session.commit()

    record_url = url_for("requests.view_request", request_id=req.id, _external=True)
    if decision == "validated":
        send_mail(
            [req.account_it_email],
            f"Impressora validada - Conta {req.account}",
            f"A impressora da conta {req.account} foi validada.\n\nAbrir pedido:\n{record_url}",
        )
        flash(
            "Impressora validada. O pedido foi atualizado para IMPRESSORA VALIDADA e o técnico IT foi notificado.",
            "success",
        )
    else:
        send_mail(
            [req.account_it_email, req.account_manager_email],
            f"Impressora não validada - Conta {req.account}",
            f"A impressora da conta {req.account} não foi validada.\n\nAbrir pedido:\n{record_url}",
        )
        flash(
            "Impressora marcada como não validada. O pedido foi atualizado para IMPRESSORA NÃO VALIDADA. Técnico IT e gestor de conta foram notificados.",
            "warning",
        )
    return redirect(url_for("requests.view_request", request_id=req.id))


@requests_bp.post("/requests/<int:request_id>/printer-pickup")
@login_required
def request_printer_pickup(request_id):
    req = RegisterRequest.query.get_or_404(request_id)
    if not can_register(g.user):
        flash("Sem permissao para solicitar a recolha.", "danger")
        return redirect(url_for("requests.view_request", request_id=req.id))
    if request.form.get("confirm") != "yes":
        flash("Recolha nao confirmada.", "info")
        return redirect(url_for("requests.view_request", request_id=req.id))

    set_request_status(req, STATUS_AWAITING_PRINTER_PICKUP)
    db.session.commit()
    record_url = url_for("requests.view_request", request_id=req.id, _external=True)

    def row(label, value):
        safe_value = escape(str(value or ""))
        return f"<tr><th style='text-align:left;padding:4px 12px 4px 0'>{escape(label)}</th><td>{safe_value}</td></tr>"

    details = [
        ("Conta", req.account), ("Cliente", req.name),
        ("Morada", " ".join(filter(None, [req.address1, req.address2, req.zip, req.city]))),
        ("Contacto", req.contact), ("Telefone", req.phn), ("Email", req.email),
        ("Gestor", req.account_manager), ("Email do gestor", req.account_manager_email),
        ("Técnico IT", req.account_it), ("Email do técnico IT", req.account_it_email),
        ("Instalação", req.install_type), ("Impressora", req.printer_requested),
        ("Quantidade", req.printer_requested_qty), ("Status", req.status),
        ("Validacao da impressora", req.validation_label()),
        ("Observações", req.obs_migracao),
    ]
    body = (
        "<html><body><h2>Recolha de impressora</h2><table>"
        + "".join(row(k, v) for k, v in details)
        + "</table><p><a href='"
        + escape(record_url, quote=True)
        + "'>Abrir pedido</a></p></body></html>"
    )
    try:
        sent = send_html_mail(
            ["ajuda@dpd.pt"],
            f"Recolha de impressora {req.account} {req.name or ''}".strip(),
            body,
            text_body=f"Recolha de impressora\n\nAbrir pedido: {record_url}",
        )
    except Exception:
        current_app.logger.exception(
            "Failed to send printer pickup email for request %s", req.id
        )
        sent = False
    if sent:
        flash("Pedido de recolha enviado para ajuda@dpd.pt.", "success")
    else:
        flash("Estado atualizado, mas o email nao foi enviado. Pode tentar novamente mais tarde.", "warning")
    return redirect(url_for("requests.view_request", request_id=req.id))


@requests_bp.post("/requests/<int:request_id>/printer-collected")
@login_required
def confirm_printer_collected(request_id):
    req = RegisterRequest.query.get_or_404(request_id)
    if not g.user.is_admin:
        flash("Apenas administradores podem confirmar a recolha.", "danger")
    elif request.form.get("confirm") != "yes":
        flash("Recolha nao confirmada.", "info")
    else:
        set_request_status(req, STATUS_PRINTER_COLLECTED)
        db.session.commit()
        flash("Impressora marcada como recolhida.", "success")
    return redirect(url_for("requests.view_request", request_id=req.id))


@requests_bp.post("/requests/<int:request_id>/move-to-history")
@login_required
def move_to_history(request_id):
    req = RegisterRequest.query.get_or_404(request_id)
    if not g.user.is_admin:
        flash("Nao foi possivel mover o pedido para o historico.", "danger")
        return redirect(url_for("requests.view_request", request_id=request_id))

    try:
        source_attrs_by_column = {
            prop.columns[0].name: prop.key
            for prop in sqlalchemy_inspect(RegisterRequest).column_attrs
        }
        history = RegisterRequestHistory()
        for prop in sqlalchemy_inspect(RegisterRequestHistory).column_attrs:
            source_attr = source_attrs_by_column[prop.columns[0].name]
            setattr(history, prop.key, getattr(req, source_attr))

        db.session.add(history)
        db.session.flush()
        db.session.delete(req)
        db.session.commit()
    except Exception:
        current_app.logger.exception(
            "Failed to move request %s to register_request_his", request_id
        )
        db.session.rollback()
        flash("Nao foi possivel mover o pedido para o historico.", "danger")
        return redirect(url_for("requests.view_request", request_id=request_id))
    flash("Pedido movido para o historico.", "success")
    return redirect(url_for("requests.index"))
