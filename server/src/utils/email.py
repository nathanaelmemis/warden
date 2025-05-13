import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import uuid

def send_email(app: str, recipient_email: str, message: str):
    # Set up MIME
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{app} Verification Code"
    msg["From"] = f"{app} NoReply <Keinorman2123@gmail.com>"
    msg["To"] = recipient_email

    # Attach HTML content
    msg.attach(MIMEText(message, "plain"))

    # Send email
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(os.environ["EMAIL_SERVICE_USER"], os.environ["EMAIL_SERVICE_PASSWORD"])
        server.sendmail(os.environ["EMAIL_SERVICE_USER"], recipient_email, msg.as_string())