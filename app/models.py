from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class RegisterUser(db.Model):
    __tablename__ = "register_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    user_dir_reg = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_master_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_dir_reg = db.Column(db.Boolean, nullable=False, default=False)
    is_can_register = db.Column(db.Boolean, nullable=False, default=False)

    def set_password(self, value):
        self.password = generate_password_hash(value)

    def check_password(self, value):
        if self.password.startswith("pbkdf2:") or self.password.startswith("scrypt:"):
            return check_password_hash(self.password, value)
        return self.password == value


class AccountManager(db.Model):
    __tablename__ = "account_managers"

    id = db.Column(db.Integer, primary_key=True)

    account_manager = db.Column(
        db.String(255),
        nullable=False,
    )

    account_manager_email = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
    )

    account_manager_dir_reg_email = db.Column(
        db.String(255),
        nullable=False,
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )


class RegisterItTech(db.Model):
    __tablename__ = "register_it_tech"

    id = db.Column(db.Integer, primary_key=True)
    tech_user_name = db.Column("Tech User Name", db.String(255), nullable=False)
    tech_user_email = db.Column("Tech user email", db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)


class InstallationType(db.Model):
    __tablename__ = "installation_types"

    id = db.Column(db.Integer, primary_key=True)
    installation_type = db.Column(db.String(120), nullable=False)
    printer_type = db.Column(db.String(120), nullable=False, index=True)
    printer_initial_status = db.Column(db.String(120), nullable=False)
    requires_validation = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    @property
    def label(self):
        return f"{self.installation_type} - {self.printer_type}"


class InstallStatus(db.Model):
    __tablename__ = "install_status"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(120), unique=True, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)


class RegisterRequest(db.Model):
    __tablename__ = "register_request"

    id = db.Column(db.Integer, primary_key=True)
    docuid = db.Column(db.String(64), unique=True, nullable=False)
    qty = db.Column(db.String(20), nullable=False, default="1")
    createdby = db.Column(db.String(255), nullable=False)
    creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    install_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(120), nullable=False, default="POR GRAVAR", index=True)
    install_type = db.Column("INSTALL_TYPE", db.String(120), nullable=True)
    account_install_check = db.Column(
        "ACCOUNT_INSTALL_CHECK", db.String(255), nullable=True
    )
    no_values_from_odbc = db.Column(db.String(255), nullable=True, default="ODBC")
    date_schedule = db.Column(db.Date, nullable=True)
    time_schedule = db.Column(db.Time, nullable=True)

    account = db.Column(db.String(8), unique=True, nullable=False, index=True)
    ccc = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(255), nullable=True)
    address1 = db.Column(db.String(255), nullable=True)
    address2 = db.Column(db.String(255), nullable=True)
    zip = db.Column(db.String(30), nullable=True)
    city = db.Column(db.String(120), nullable=True)

    phn = db.Column(db.String(80), nullable=False)
    contact = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    gps_n = db.Column(db.String(80), nullable=True)
    gps_n_1 = db.Column(db.String(80), nullable=True)

    # Historical snapshot copied from account_managers at request creation time.
    account_manager = db.Column(db.String(255), nullable=False)
    account_manager_email = db.Column(db.String(255), nullable=True)
    account_assist = db.Column(db.String(255), nullable=True)
    account_dir_reg = db.Column(db.String(255), nullable=True)

    printer_requested = db.Column(db.String(120), nullable=False)
    printer_install_type = db.Column(db.String(120), nullable=True)
    envios_dia = db.Column(db.String(60), nullable=False)
    printer_requested_qty = db.Column(db.String(20), nullable=False, default="1")

    account_it = db.Column(db.String(255), nullable=False)
    account_it_email = db.Column(db.String(255), nullable=True)
    account_it_support = db.Column(
        db.String(255), nullable=True, default="A preencher pelo DSI"
    )

    printer_1 = db.Column(db.String(255), nullable=True)
    usb_cable_1 = db.Column(db.String(120), nullable=True, default="9 Pin Cable")
    adapt_925_1 = db.Column("925_adapt_1", db.String(10), nullable=True, default="NO")
    key_1 = db.Column(db.String(255), nullable=True)
    obs_migracao = db.Column(db.Text, nullable=True)
    normalizada_1 = db.Column(db.String(10), nullable=True, default="NÃO")
    db_ok_1 = db.Column(db.Integer, nullable=True)
    db_nok_1 = db.Column(db.Integer, nullable=True)
    obs_normalizada_1 = db.Column(db.Text, nullable=True)

    requires_printer_validation = db.Column(db.Boolean, nullable=False, default=False)
    is_printer_validated = db.Column(
        db.String(30), nullable=True
    )  # validated, not_validated, or null
    printer_validation_changed_by = db.Column(db.String(255), nullable=True)
    printer_validation_changed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def validation_label(self):
        if self.is_printer_validated == "validated":
            return "Impressora validada"
        if self.is_printer_validated == "not_validated":
            return "Impressora não validada"
        return "Pendente"


class RegisterRequestHistory(db.Model):
    """Archived requests, with the same columns and constraints as register_request."""

    __table__ = RegisterRequest.__table__.to_metadata(
        db.metadata, name="register_request_his"
    )
