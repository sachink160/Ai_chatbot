from django.core.mail import send_mail
from django.conf import settings

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")  # Replace with your Django project 
django.setup()

def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email using Django's SMTP backend.

    Args:
        to (str): The recipient's email address.
        subject (str): The subject line of the email.
        body (str): The main content of the email.

    Returns:
        str: A confirmation message indicating the email was sent.
    """
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [to],
            fail_silently=False,
        )
        return f"✅ Email sent to {to} with subject '{subject}'"
    except Exception as e:
        return f"❌ Failed to send email: {e}"