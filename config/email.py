import os
from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("EMAIL_USER"),
    MAIL_PASSWORD = os.getenv("EMAIL_PASS"),
    MAIL_FROM = os.getenv("EMAIL_USER"),
    MAIL_PORT = 465,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_email(subject: str, recipients: list, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    print("E-mail enviado!")
