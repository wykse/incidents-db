import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from decouple import config


def send_email(subject: str, body: str, table_html: str, image_url: str):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = config("EMAIL")
    receiver_email = config("RECEIVER_EMAIL")

    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    html = f"<p>{body}</p><br><img src='{image_url}'><br>{table_html}"
    html = MIMEText(html, "html")

    message.attach(html)

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, config("EMAIL_PASSWORD"))
        server.sendmail(sender_email, receiver_email, message.as_string())
