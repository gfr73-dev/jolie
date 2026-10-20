import os
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy.engine import URL


PROJECT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
SHARED_MYSQL_ENV_FILE = Path(
    os.environ.get(
        "MYSQL_APP_ENV_FILE",
        Path(__file__).resolve().parents[2] / ".mysql-app.env",
    )
).expanduser()
load_dotenv(PROJECT_ENV_FILE)
load_dotenv(SHARED_MYSQL_ENV_FILE, override=True)


def mysql_database_url(database: str) -> URL:
    password = os.getenv("MYSQL_APP_PASSWORD")
    if not password:
        raise RuntimeError(
            "MYSQL_APP_PASSWORD is not configured. Run mysql_security_setup.py on the XAMPP host."
        )
    return URL.create(
        "mysql+pymysql",
        username=os.getenv("MYSQL_APP_USER", "flask_apps"),
        password=password,
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=database,
        query={"charset": "utf8mb4"},
    )


@dataclass(frozen=True)
class AccountManager:
    name: str
    email: str = ""
    assistant: str = ""
    dir_reg: str = ""


def parse_account_managers(raw: str):
    managers = []
    for chunk in raw.split(";"):
        parts = [p.strip() for p in chunk.split("|")]
        if not parts or not parts[0]:
            continue
        while len(parts) < 4:
            parts.append("")
        managers.append(AccountManager(parts[0], parts[1], parts[2], parts[3]))
    return managers


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    SQLALCHEMY_DATABASE_URI = mysql_database_url("JOLIE")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AS400_ENABLED = os.getenv("AS400_ENABLED", "false").lower() == "true"
    AS400_DSN = os.getenv("AS400_DSN", "cli000")
    AS400_UID = os.getenv("AS400_UID", "mobile")
    AS400_PWD = os.getenv("AS400_PWD", "mobile")
    AS400_CLIENT_TABLE = os.getenv("AS400_CLIENT_TABLE", "APIDATA.CLI000")
    AS400_BIC_TABLE = os.getenv("AS400_BIC_TABLE", "OPERACOES.BIC3TAB")

    SMTP_ENABLED = os.getenv("SMTP_ENABLED", "false").lower() == "true"
    SMTP_HOST = os.getenv("SMTP_HOST", "dpd.relay.tmes.trendmicro.eu")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
    SMTP_TIMEOUT_SECONDS = int(os.getenv("SMTP_TIMEOUT_SECONDS", "10"))
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "metricas.dsi@dpd.pt")

    ACCOUNT_MANAGERS_RAW = os.getenv(
        "ACCOUNT_MANAGERS",
        "Escolha o Gestor|||;Gestor Exemplo|gestor.exemplo@yourdomain.pt||dir.regional@yourdomain.pt",
    )
