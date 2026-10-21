import logging
import smtplib
import time
from email.message import EmailMessage
from flask import current_app

log = logging.getLogger(__name__)


class _DeadlineSMTP(smtplib.SMTP):
    """SMTP client whose socket operations share one wall-clock deadline."""

    def __init__(self, host, port, timeout):
        self._deadline = time.monotonic() + timeout
        super().__init__(host, port, timeout=timeout)

    def _apply_deadline(self):
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("SMTP send exceeded its time limit")
        if self.sock is not None:
            self.sock.settimeout(remaining)

    def send(self, data):
        self._apply_deadline()
        return super().send(data)

    def getreply(self):
        self._apply_deadline()
        return super().getreply()


def send_mail(to_addresses, subject, body):
    recipients = [addr for addr in to_addresses if addr]
    if not recipients:
        log.info("Email skipped, no recipients. Subject=%s", subject)
        return False

    if not current_app.config["SMTP_ENABLED"]:
        log.info("SMTP disabled. Would send to=%s subject=%s", recipients, subject)
        return False

    msg = EmailMessage()
    msg["From"] = current_app.config["MAIL_FROM"]
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    with _DeadlineSMTP(
        current_app.config["SMTP_HOST"],
        current_app.config["SMTP_PORT"],
        timeout=current_app.config.get("SMTP_TIMEOUT_SECONDS", 15),
    ) as smtp:
        if current_app.config["SMTP_USE_TLS"]:
            smtp.starttls()
        if current_app.config["SMTP_USER"]:
            smtp.login(current_app.config["SMTP_USER"], current_app.config["SMTP_PASSWORD"])
        smtp.send_message(msg)
    return True


def send_html_mail(to_addresses, subject, html_body, text_body=None):
    recipients = [addr for addr in to_addresses if addr]
    if not recipients:
        log.info("HTML email skipped, no recipients. Subject=%s", subject)
        return False

    if not current_app.config["SMTP_ENABLED"]:
        log.info("SMTP disabled. Would send HTML email to=%s subject=%s", recipients, subject)
        return False

    msg = EmailMessage()
    msg["From"] = current_app.config["MAIL_FROM"]
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(text_body or "Este pedido está disponível em formato HTML.")
    msg.add_alternative(html_body, subtype="html")

    with _DeadlineSMTP(
        current_app.config["SMTP_HOST"],
        current_app.config["SMTP_PORT"],
        timeout=current_app.config.get("SMTP_TIMEOUT_SECONDS", 15),
    ) as smtp:
        if current_app.config["SMTP_USE_TLS"]:
            smtp.starttls()
        if current_app.config["SMTP_USER"]:
            smtp.login(current_app.config["SMTP_USER"], current_app.config["SMTP_PASSWORD"])
        refused = smtp.send_message(msg)
    if refused:
        log.warning("HTML email recipient(s) refused: %s", sorted(refused))
        return False
    return True
