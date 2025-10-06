import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from environs import env


def send_mail(
    v_subject: str,
    v_body: str,
    to_address: List[str] | str,
    log_dir: str,
    log_name: str,
    send_log_file: bool,
) -> None:
    """
    Šalje mail unutar kojega se nalaze proslijeđena poruka i opcionalno log file.

    Args:
        v_subject (str): Subject maila.
        v_body (str): Poruka maila.
        to_address (List[str] | str): Primatelj/i maila.
        log_dir (str): Direktorij u kojemu se nalazi log file.
        log_name (str): Naziv log filea.
        send_log_file (bool): Da li se šalje log file ili ne.
    """
    from_address = env("SENDER_MAIL_ADDRESS")

    msg = MIMEMultipart()

    msg["From"] = from_address
    if isinstance(to_address, str):
        msg["To"] = to_address
    if isinstance(to_address, list):
        msg["To"] = ", ".join(to_address)
    msg["Subject"] = v_subject

    body = v_body
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if send_log_file:
        attachment = open(os.path.join(log_dir, log_name), "rb")

        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment; filename= %s" % log_name)

        msg.attach(part)

    # Port 25 za mogućnost anonimnog slanja
    server = smtplib.SMTP("mail.hnb.hr", 25)
    text = msg.as_string()
    server.sendmail(from_address, to_address, text)
    server.quit()
