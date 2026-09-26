# test_mail.py
from app.services.email_service import send_email

print("=== SMTP diagnostics ===")
from app.config.settings import settings
print("smtp_host     :", repr(settings.smtp_host))
print("smtp_port     :", repr(settings.smtp_port))
print("smtp_username :", repr(settings.smtp_username))
print("mail_from     :", repr(settings.mail_from))
print("smtp_encryption:", repr(settings.smtp_encryption))
print("========================")

send_email(
    to_email="promisezema111@gmail.com",      # ← put your own address here
    subject="123456 is your verification code",
    html_body="<html><body><h2>Test</h2><p>Code: <b>123456</b></p></body></html>",
    text_body="Test\n\nCode: 123456\n",
)

print("Done — check the inbox (and spam folder).")