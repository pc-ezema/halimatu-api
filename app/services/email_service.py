from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import settings

def send_otp_email(email: str, otp_code: str):
    """Send OTP verification email - Gmail compatible"""
    subject = "Verify Your Email Address - Halimatu"
    current_year = datetime.now().year

    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verification</title>
    </head>
    <body style="margin:0; padding:20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height:1.6; color:#1a1a1a; background: linear-gradient(135deg, #004aad 0%, #2c3e8f 100%);">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:550px; margin:0 auto; background:#ffffff; border-radius:20px; overflow:hidden; box-shadow:0 20px 40px rgba(0,0,0,0.1);">
            <!-- Header -->
            <tr>
                <td style="background: linear-gradient(135deg, #004aad 0%, #2c3e8f 100%); padding:40px 20px; text-align:center;">
                    <img src="https://res.cloudinary.com/ddj0k8gdw/image/upload/v1769389099/Halimatu-Academy-Images/logo_3_1_bmduex.png" 
                         alt="Halimatu" 
                         style="max-width:70px; height:auto; background:white; border-radius:50%; padding:8px;">
                    <div style="color:white; font-size:22px; font-weight:bold; margin-top:10px;">Halimatu</div>
                </td>
            </tr>
            
            <!-- Content -->
            <tr>
                <td style="padding:40px 30px;">
                    <h2 style="font-size:24px; font-weight:600; color:#1a1a1a; margin-bottom:15px; text-align:center;">Welcome! 🎉</h2>
                    
                    <p style="font-size:16px; color:#4a5568; margin-bottom:30px; text-align:center;">
                        Thanks for joining Halimatu LMS. Please verify your email address to get started.
                    </p>
                    
                    <!-- OTP Box -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%); border-radius:16px; padding:30px; text-align:center; margin:25px 0; border:2px dashed #c7d2fe;">
                        <tr>
                            <td style="text-align:center;">
                                <div style="font-size:13px; text-transform:uppercase; letter-spacing:2px; color:#6b7280; margin-bottom:15px; font-weight:600;">Your Verification Code</div>
                                <div style="font-size:42px; font-weight:bold; letter-spacing:8px; color:#4F46E5; font-family:'Courier New', monospace; background:white; padding:20px 25px; border-radius:12px; display:inline-block; border:1px solid #e0e7ff;">{otp_code}</div>
                                <div style="margin-top:15px; font-size:13px; color:#6b7280; background:#f9fafb; display:inline-block; padding:6px 12px; border-radius:20px;">📋 Click the code above to copy</div>
                                <div style="font-size:13px; color:#6b7280; margin-top:15px;">⏰ Valid for 10 minutes</div>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Features -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f9fafb; border-radius:12px; padding:20px; margin:25px 0;">
                        <tr>
                            <td style="text-align:center;">
                                <div style="font-size:14px; font-weight:600; color:#1f2937; margin-bottom:12px;">What you'll get:</div>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td style="padding:8px 0;">
                                            <span style="display:inline-block; width:28px; height:28px; background:#4F46E5; border-radius:50%; text-align:center; line-height:28px; color:white; font-size:13px; margin-right:12px;">✓</span>
                                            <span style="color:#374151; font-size:13px;">Access to all courses</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px 0;">
                                            <span style="display:inline-block; width:28px; height:28px; background:#4F46E5; border-radius:50%; text-align:center; line-height:28px; color:white; font-size:13px; margin-right:12px;">✓</span>
                                            <span style="color:#374151; font-size:13px;">Track your progress</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px 0;">
                                            <span style="display:inline-block; width:28px; height:28px; background:#4F46E5; border-radius:50%; text-align:center; line-height:28px; color:white; font-size:13px; margin-right:12px;">✓</span>
                                            <span style="color:#374151; font-size:13px;">Earn certificates</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:8px 0;">
                                            <span style="display:inline-block; width:28px; height:28px; background:#4F46E5; border-radius:50%; text-align:center; line-height:28px; color:white; font-size:13px; margin-right:12px;">✓</span>
                                            <span style="color:#374151; font-size:13px;">Connect with instructors</span>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Tip Box -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fffbeb; border-radius:12px; padding:15px; margin:20px 0;">
                        <tr>
                            <td style="text-align:center; color:#92400e; font-size:13px;">
                                💡 <strong>Tip:</strong> Enter this code on the verification page to activate your account.
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            
            <!-- Footer -->
            <tr>
                <td style="background:#f9fafb; padding:25px; text-align:center; border-top:1px solid #e5e7eb;">
                    <div style="font-size:12px; color:#6b7280; margin-bottom:15px;">Need help? Contact us at <a href="mailto:support@halimatu.com" style="color:#004aad;">support@halimatu.com</a></div>
                    <div style="font-size:11px; color:#9ca3af;">© {current_year} Halimatu. All rights reserved.<br>If you didn't create this account, please ignore this email.</div>
                </td>
            </tr>
        </table>
        
        <script>
            (function() {{
                var otpCode = document.querySelector('.otp-code');
                if (otpCode) {{
                    otpCode.style.cursor = 'pointer';
                    otpCode.onclick = function() {{
                        var text = this.innerText;
                        navigator.clipboard.writeText(text).then(function() {{
                            var instruction = document.querySelector('.copy-instruction');
                            var originalText = instruction.innerHTML;
                            instruction.innerHTML = '✓ Copied!';
                            setTimeout(function() {{
                                instruction.innerHTML = originalText;
                            }}, 1500);
                        }});
                    }};
                }}
            }})();
        </script>
    </body>
    </html>
    """
    send_email(email, subject, body)

def send_password_reset_email(email: str, new_password: str):
    """Send password reset email with new password - Gmail compatible"""
    subject = "Your Password Has Been Reset - Halimatu"
    current_year = datetime.now().year

    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset</title>
    </head>
    <body style="margin:0; padding:20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height:1.6; color:#1a1a1a; background: linear-gradient(135deg, #004aad 0%, #2c3e8f 100%);">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:550px; margin:0 auto; background:#ffffff; border-radius:20px; overflow:hidden; box-shadow:0 20px 40px rgba(0,0,0,0.1);">
            <!-- Header -->
            <tr>
                <td style="background: linear-gradient(135deg, #004aad 0%, #2c3e8f 100%); padding:40px 20px; text-align:center;">
                    <img src="https://res.cloudinary.com/ddj0k8gdw/image/upload/v1769389099/Halimatu-Academy-Images/logo_3_1_bmduex.png" 
                         alt="Halimatu" 
                         style="max-width:70px; height:auto; background:white; border-radius:50%; padding:8px;">
                    <div style="color:white; font-size:22px; font-weight:bold; margin-top:10px;">Halimatu</div>
                </td>
            </tr>
            
            <!-- Content -->
            <tr>
                <td style="padding:40px 30px;">
                    <h2 style="font-size:24px; font-weight:600; color:#1a1a1a; margin-bottom:15px; text-align:center;">Password Reset 🔐</h2>
                    
                    <p style="font-size:16px; color:#4a5568; margin-bottom:25px; text-align:center;">
                        Your password has been reset by an administrator. Use the new password below to login.
                    </p>
                    
                    <!-- Password Box -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius:16px; padding:30px; text-align:center; margin:25px 0; border:2px dashed #fcd34d;">
                        <tr>
                            <td style="text-align:center;">
                                <div style="font-size:13px; text-transform:uppercase; letter-spacing:2px; color:#92400e; margin-bottom:15px; font-weight:600;">Your New Password</div>
                                <div style="font-size:32px; font-weight:bold; letter-spacing:2px; color:#d97706; font-family:'Courier New', monospace; background:white; padding:20px 25px; border-radius:12px; display:inline-block; border:1px solid #fed7aa;">{new_password}</div>
                                <div style="margin-top:15px; font-size:13px; color:#92400e; background:#fff3e0; display:inline-block; padding:6px 12px; border-radius:20px;">📋 Click the password above to copy</div>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Warning Box -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fee2e2; border-radius:12px; padding:15px; margin:20px 0;">
                        <tr>
                            <td style="text-align:center; color:#991b1b; font-size:13px;">
                                ⚠️ <strong>Security Notice:</strong> Please change this password after logging in for security reasons.
                            </td>
                        </tr>
                    </table>
                    
                    <p style="font-size:13px; text-align:center; color:#4a5568; margin-top:15px;">
                        If you didn't request this password reset, please contact support immediately.
                    </p>
                </td>
            </tr>
            
            <!-- Footer -->
            <tr>
                <td style="background:#f9fafb; padding:25px; text-align:center; border-top:1px solid #e5e7eb;">
                    <div style="font-size:12px; color:#6b7280; margin-bottom:15px;">Need help? Contact us at <a href="mailto:support@halimatu.com" style="color:#004aad;">support@halimatu.com</a></div>
                    <div style="font-size:11px; color:#9ca3af;">© {current_year} Halimatu. All rights reserved.<br>This is an automated message, please do not reply.</div>
                </td>
            </tr>
        </table>
        
        <script>
            (function() {{
                var passwordCode = document.querySelector('.otp-code');
                if (passwordCode) {{
                    passwordCode.style.cursor = 'pointer';
                    passwordCode.onclick = function() {{
                        var text = this.innerText;
                        navigator.clipboard.writeText(text).then(function() {{
                            var instruction = document.querySelector('.copy-instruction');
                            var originalText = instruction.innerHTML;
                            instruction.innerHTML = '✓ Copied!';
                            setTimeout(function() {{
                                instruction.innerHTML = originalText;
                            }}, 1500);
                        }});
                    }};
                }}
            }})();
        </script>
    </body>
    </html>
    """
    
    send_email(email, subject, body)

def send_password_reset_with_otp(email: str, otp_code: str):
    """Send password reset email with OTP code"""
    subject = "Password Reset - Halimatu"
    current_year = datetime.now().year

    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset</title>
    </head>
    <body style="margin:0; padding:20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height:1.6; color:#1a1a1a; background: linear-gradient(135deg, #004aad 0%, #2c3e8f 100%);">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:550px; margin:0 auto; background:#ffffff; border-radius:20px; overflow:hidden; box-shadow:0 20px 40px rgba(0,0,0,0.1);">
            <!-- Header -->
            <tr>
                <td style="background: linear-gradient(135deg, #004aad 0%, #2c3e8f 100%); padding:40px 20px; text-align:center;">
                    <img src="https://res.cloudinary.com/ddj0k8gdw/image/upload/v1769389099/Halimatu-Academy-Images/logo_3_1_bmduex.png" 
                         alt="Halimatu" 
                         style="max-width:70px; height:auto; background:white; border-radius:50%; padding:8px;">
                    <div style="color:white; font-size:22px; font-weight:bold; margin-top:10px;">Halimatu</div>
                </td>
            </tr>
            
            <!-- Content -->
            <tr>
                <td style="padding:40px 30px;">
                    <h2 style="font-size:24px; font-weight:600; color:#1a1a1a; margin-bottom:15px; text-align:center;">Reset Your Password 🔐</h2>
                    
                    <p style="font-size:16px; color:#4a5568; margin-bottom:25px; text-align:center;">
                        We received a request to reset your password. Use the code below to create a new password.
                    </p>
                    
                    <!-- OTP Box -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius:16px; padding:30px; text-align:center; margin:25px 0; border:2px dashed #fcd34d;">
                        <tr>
                            <td style="text-align:center;">
                                <div style="font-size:13px; text-transform:uppercase; letter-spacing:2px; color:#92400e; margin-bottom:15px; font-weight:600;">Password Reset Code</div>
                                <div style="font-size:42px; font-weight:bold; letter-spacing:8px; color:#d97706; font-family:'Courier New', monospace; background:white; padding:20px 25px; border-radius:12px; display:inline-block; border:1px solid #fed7aa;">{otp_code}</div>
                                <div style="margin-top:15px; font-size:13px; color:#92400e; background:#fff3e0; display:inline-block; padding:6px 12px; border-radius:20px;">📋 Click the code above to copy</div>
                                <div style="font-size:13px; color:#92400e; margin-top:15px;">⏰ Valid for 10 minutes</div>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Warning Box -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fee2e2; border-radius:12px; padding:15px; margin:20px 0;">
                        <tr>
                            <td style="text-align:center; color:#991b1b; font-size:13px;">
                                ⚠️ <strong>Security Notice:</strong> If you didn't request this, please ignore this email. Your account remains secure.
                            </td>
                        </tr>
                    </table>
                    
                    <p style="font-size:13px; text-align:center; color:#4a5568; margin-top:15px;">
                        Enter this code on the password reset page to continue.
                    </p>
                </td>
            </tr>
            
            <!-- Footer -->
            <tr>
                <td style="background:#f9fafb; padding:25px; text-align:center; border-top:1px solid #e5e7eb;">
                    <div style="font-size:12px; color:#6b7280; margin-bottom:15px;">Need help? Contact us at <a href="mailto:support@halimatu.com" style="color:#004aad;">support@halimatu.com</a></div>
                    <div style="font-size:11px; color:#9ca3af;">© {current_year} Halimatu. All rights reserved.<br>This is an automated message, please do not reply.</div>
                </td>
            </tr>
        </table>
        
        <script>
            (function() {{
                var otpCode = document.querySelector('.otp-code');
                if (otpCode) {{
                    otpCode.style.cursor = 'pointer';
                    otpCode.onclick = function() {{
                        var text = this.innerText;
                        navigator.clipboard.writeText(text).then(function() {{
                            var instruction = document.querySelector('.copy-instruction');
                            var originalText = instruction.innerHTML;
                            instruction.innerHTML = '✓ Copied!';
                            setTimeout(function() {{
                                instruction.innerHTML = originalText;
                            }}, 1500);
                        }});
                    }};
                }}
            }})();
        </script>
    </body>
    </html>
    """
    
    send_email(email, subject, body)

def send_new_password_email(email: str, new_password: str, user_name: str = "User"):
    """Send new password email with the latest format"""
    subject = "Your Password Has Been Reset - Halimatu"
    current_year = datetime.now().year

    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset - Halimatu</title>
    </head>
    <body style="margin:0; padding:20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height:1.6; color:#1a1a1a; background: linear-gradient(135deg, #004aad 0%, #2c3e8f 100%);">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:550px; margin:0 auto; background:#ffffff; border-radius:20px; overflow:hidden; box-shadow:0 20px 40px rgba(0,0,0,0.1);">
            <!-- Header -->
            <tr>
                <td style="background: linear-gradient(135deg, #004aad 0%, #2c3e8f 100%); padding:40px 20px; text-align:center;">
                    <img src="https://res.cloudinary.com/ddj0k8gdw/image/upload/v1769389099/Halimatu-Academy-Images/logo_3_1_bmduex.png" 
                         alt="Halimatu" 
                         style="max-width:70px; height:auto; background:white; border-radius:50%; padding:8px;">
                    <div style="color:white; font-size:22px; font-weight:bold; margin-top:10px;">Halimatu</div>
                </td>
            </tr>
            
            <!-- Content -->
            <tr>
                <td style="padding:40px 30px;">
                    <h2 style="font-size:24px; font-weight:600; color:#1a1a1a; margin-bottom:15px; text-align:center;">Password Reset 🔐</h2>
                    
                    <p style="font-size:16px; color:#4a5568; margin-bottom:15px; text-align:center;">
                        Hello <strong>{user_name}</strong>,
                    </p>
                    
                    <p style="font-size:16px; color:#4a5568; margin-bottom:25px; text-align:center;">
                        Your password has been reset by an administrator. Use the new password below to login.
                    </p>
                    
                    <!-- Password Box -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius:16px; padding:30px; text-align:center; margin:25px 0; border:2px dashed #fcd34d;">
                        <tr>
                            <td style="text-align:center;">
                                <div style="font-size:13px; text-transform:uppercase; letter-spacing:2px; color:#92400e; margin-bottom:15px; font-weight:600;">Your New Password</div>
                                <div style="font-size:32px; font-weight:bold; letter-spacing:2px; color:#d97706; font-family:'Courier New', monospace; background:white; padding:20px 25px; border-radius:12px; display:inline-block; border:1px solid #fed7aa;">{new_password}</div>
                                <div style="margin-top:15px; font-size:13px; color:#92400e; background:#fff3e0; display:inline-block; padding:6px 12px; border-radius:20px;">📋 Click the password above to copy</div>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Warning Box -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fee2e2; border-radius:12px; padding:15px; margin:20px 0;">
                        <tr>
                            <td style="text-align:center; color:#991b1b; font-size:13px;">
                                ⚠️ <strong>Security Notice:</strong> Please change this password after logging in for security reasons.
                            </td>
                        </tr>
                    </table>
                    
                    <p style="font-size:13px; text-align:center; color:#4a5568; margin-top:15px;">
                        If you didn't request this password reset, please contact support immediately.
                    </p>
                    
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:30px;">
                        <tr>
                            <td style="text-align:center;">
                                <a href="https://halimatu.farmsglobal.org/login" style="display:inline-block; background:#004aad; color:white; text-decoration:none; padding:12px 30px; border-radius:8px; font-weight:600;">Login to Your Account →</a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            
            <!-- Footer -->
            <tr>
                <td style="background:#f9fafb; padding:25px; text-align:center; border-top:1px solid #e5e7eb;">
                    <div style="font-size:12px; color:#6b7280; margin-bottom:15px;">Need help? Contact us at <a href="mailto:support@halimatu.com" style="color:#004aad;">support@halimatu.com</a></div>
                    <div style="font-size:11px; color:#9ca3af;">© {current_year} Halimatu. All rights reserved.<br>This is an automated message, please do not reply.</div>
                </td>
            </tr>
        </table>
        
        <script>
            (function() {{
                var passwordElement = document.querySelector('.otp-code');
                if (passwordElement) {{
                    passwordElement.style.cursor = 'pointer';
                    passwordElement.onclick = function() {{
                        var text = this.innerText;
                        navigator.clipboard.writeText(text).then(function() {{
                            var instruction = document.querySelector('.copy-instruction');
                            var originalText = instruction.innerHTML;
                            instruction.innerHTML = '✓ Copied!';
                            setTimeout(function() {{
                                instruction.innerHTML = originalText;
                            }}, 1500);
                        }});
                    }};
                }}
            }})();
        </script>
    </body>
    </html>
    """
    
    send_email(email, subject, body)
    
def send_email(to_email: str, subject: str, html_body: str):
    """Generic sender"""
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.mail_from
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Create SMTP connection
        if settings.smtp_encryption.lower() == "tls":
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
        elif settings.smtp_encryption.lower() == "ssl":
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
            
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")