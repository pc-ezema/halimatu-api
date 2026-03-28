from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import settings

def send_otp_email(email: str, otp_code: str):
    """Send OTP verification email"""
    subject = "Verify Your Email Address - Halimatu"
    current_year = datetime.now().year

    body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verification</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                background: linear-gradient(135deg, #004aad 0%, oklch(48.8% .243 264.376) 100%);
                padding: 20px;
            }}
            
            .email-wrapper {{
                max-width: 550px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            
            .header {{
                background: linear-gradient(135deg, #004aad 0%, oklch(48.8% .243 264.376) 100%);
                padding: 40px 20px;
                text-align: center;
            }}
            
            .logo-container {{
                margin-bottom: 15px;
            }}
            
            .logo {{
                max-width: 70px;
                height: auto;
                background: white;
                border-radius: 50%;
                padding: 8px;
            }}
            
            .company-name {{
                color: white;
                font-size: 22px;
                font-weight: bold;
                margin-top: 5px;
            }}
            
            .content {{
                padding: 40px 30px;
            }}
            
            .greeting {{
                font-size: 24px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 15px;
                text-align: center;
            }}
            
            .message {{
                font-size: 16px;
                color: #4a5568;
                margin-bottom: 30px;
                text-align: center;
            }}
            
            .otp-container {{
                background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
                border-radius: 16px;
                padding: 30px;
                text-align: center;
                margin: 25px 0;
                border: 2px dashed #c7d2fe;
            }}
            
            .otp-label {{
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #6b7280;
                margin-bottom: 15px;
                font-weight: 600;
            }}
            
            .otp-code {{
                font-size: 42px;
                font-weight: bold;
                letter-spacing: 8px;
                color: #4F46E5;
                font-family: 'Courier New', 'SF Mono', monospace;
                background: white;
                padding: 20px 25px;
                border-radius: 12px;
                display: inline-block;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                border: 1px solid #e0e7ff;
                user-select: all;
                cursor: pointer;
            }}
            
            .copy-instruction {{
                margin-top: 15px;
                font-size: 13px;
                color: #6b7280;
                background: #f9fafb;
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
            }}
            
            .expiry-info {{
                font-size: 13px;
                color: #6b7280;
                margin-top: 15px;
            }}
            
            .features {{
                background: #f9fafb;
                border-radius: 12px;
                padding: 20px;
                margin: 25px 0;
            }}
            
            .feature-title {{
                font-size: 14px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 12px;
                text-align: center;
            }}
            
            .feature-item {{
                display: flex;
                align-items: center;
                margin-bottom: 12px;
            }}
            
            .feature-icon {{
                width: 28px;
                height: 28px;
                background: #4F46E5;
                border-radius: 50%;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 13px;
                margin-right: 12px;
                flex-shrink: 0;
            }}
            
            .feature-text {{
                color: #374151;
                font-size: 13px;
            }}
            
            .tip-box {{
                background: #fffbeb;
                border-radius: 12px;
                padding: 15px;
                margin: 20px 0;
                text-align: center;
            }}
            
            .tip-text {{
                color: #92400e;
                font-size: 13px;
            }}
            
            .footer {{
                background: #f9fafb;
                padding: 25px;
                text-align: center;
                border-top: 1px solid #e5e7eb;
            }}
            
            .help-text {{
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 15px;
            }}
            
            .copyright {{
                font-size: 11px;
                color: #9ca3af;
                margin-top: 15px;
            }}
            
            @media only screen and (max-width: 480px) {{
                .content {{
                    padding: 25px 20px;
                }}
                .otp-code {{
                    font-size: 32px;
                    letter-spacing: 5px;
                    padding: 15px 20px;
                }}
                .greeting {{
                    font-size: 20px;
                }}
            }}
            
            /* Copy feedback animation */
            @keyframes copyFeedback {{
                0% {{ transform: scale(1); background-color: white; }}
                50% {{ transform: scale(1.05); background-color: #e0e7ff; }}
                100% {{ transform: scale(1); background-color: white; }}
            }}
            
            .copy-feedback {{
                animation: copyFeedback 0.3s ease;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <!-- Header with Logo -->
            <div class="header">
                <div class="logo-container">
                    <img src="https://res.cloudinary.com/ddj0k8gdw/image/upload/v1769389099/Halimatu-Academy-Images/logo_3_1_bmduex.png" 
                        alt="Halimatu" 
                        class="logo">
                </div>
                <div class="company-name">Halimatu</div>
            </div>
            
            <!-- Main Content -->
            <div class="content">
                <div class="greeting">
                    Welcome! 🎉
                </div>
                
                <div class="message">
                    Thanks for joining Halimatu LMS. Please verify your email address to get started.
                </div>
                
                <!-- OTP Code Box - Easy to Copy -->
                <div class="otp-container">
                    <div class="otp-label">Your Verification Code</div>
                    <div class="otp-code" id="otpCode">{otp_code}</div>
                    <div class="copy-instruction">
                        📋 Click the code above to copy
                    </div>
                    <div class="expiry-info">
                        ⏰ Valid for 10 minutes
                    </div>
                </div>
                
                <!-- Quick Features -->
                <div class="features">
                    <div class="feature-title">What you'll get:</div>
                    <div class="feature-item">
                        <div class="feature-icon">✓</div>
                        <div class="feature-text">Access to all courses</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">✓</div>
                        <div class="feature-text">Track your progress</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">✓</div>
                        <div class="feature-text">Earn certificates</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon">✓</div>
                        <div class="feature-text">Connect with instructors</div>
                    </div>
                </div>
                
                <!-- Help Tip -->
                <div class="tip-box">
                    <div class="tip-text">
                        💡 <strong>Tip:</strong> Enter this code on the verification page to activate your account.
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <div class="help-text">
                    Need help? Contact us at support@halimatu.com
                </div>
                <div class="copyright">
                    © {current_year} Halimatu. All rights reserved.<br>
                    If you didn't create this account, please ignore this email.
                </div>
            </div>
        </div>
        
        <script>
            // Add click-to-copy functionality
            const otpElement = document.getElementById('otpCode');
            if (otpElement) {{
                otpElement.addEventListener('click', function() {{
                    const text = this.innerText;
                    navigator.clipboard.writeText(text).then(() => {{
                        // Add visual feedback
                        this.classList.add('copy-feedback');
                        setTimeout(() => {{
                            this.classList.remove('copy-feedback');
                        }}, 300);
                        
                        // Optional: Show temporary tooltip
                        const instruction = document.querySelector('.copy-instruction');
                        const originalText = instruction.innerHTML;
                        instruction.innerHTML = '✓ Copied!';
                        setTimeout(() => {{
                            instruction.innerHTML = originalText;
                        }}, 1500);
                    }});
                }});
            }}
        </script>
    </body>
    </html>
    """
    send_email(email, subject, body)

def send_password_reset_email(email: str, otp_code: str):
    """Send password reset email"""
    subject = "Password Reset - Halimatu"
    current_year = datetime.now().year

    body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                background: linear-gradient(135deg, #004aad 0%, oklch(48.8% .243 264.376) 100%);
                padding: 20px;
            }}
            
            .email-wrapper {{
                max-width: 550px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            
            .header {{
                background: linear-gradient(135deg, #004aad 0%, oklch(48.8% .243 264.376) 100%);
                padding: 40px 20px;
                text-align: center;
            }}
            
            .logo-container {{
                margin-bottom: 15px;
            }}
            
            .logo {{
                max-width: 70px;
                height: auto;
                background: white;
                border-radius: 50%;
                padding: 8px;
            }}
            
            .company-name {{
                color: white;
                font-size: 22px;
                font-weight: bold;
                margin-top: 5px;
            }}
            
            .content {{
                padding: 40px 30px;
            }}
            
            .greeting {{
                font-size: 24px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 15px;
                text-align: center;
            }}
            
            .message {{
                font-size: 16px;
                color: #4a5568;
                margin-bottom: 25px;
                text-align: center;
            }}
            
            .otp-container {{
                background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                border-radius: 16px;
                padding: 30px;
                text-align: center;
                margin: 25px 0;
                border: 2px dashed #fcd34d;
            }}
            
            .otp-label {{
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #92400e;
                margin-bottom: 15px;
                font-weight: 600;
            }}
            
            .otp-code {{
                font-size: 42px;
                font-weight: bold;
                letter-spacing: 8px;
                color: #d97706;
                font-family: 'Courier New', 'SF Mono', monospace;
                background: white;
                padding: 20px 25px;
                border-radius: 12px;
                display: inline-block;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                border: 1px solid #fed7aa;
                user-select: all;
                cursor: pointer;
            }}
            
            .copy-instruction {{
                margin-top: 15px;
                font-size: 13px;
                color: #92400e;
                background: #fff3e0;
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
            }}
            
            .expiry-info {{
                font-size: 13px;
                color: #92400e;
                margin-top: 15px;
            }}
            
            .warning-box {{
                background: #fee2e2;
                border-radius: 12px;
                padding: 15px;
                margin: 20px 0;
                text-align: center;
            }}
            
            .warning-text {{
                color: #991b1b;
                font-size: 13px;
            }}
            
            .footer {{
                background: #f9fafb;
                padding: 25px;
                text-align: center;
                border-top: 1px solid #e5e7eb;
            }}
            
            .help-text {{
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 15px;
            }}
            
            .copyright {{
                font-size: 11px;
                color: #9ca3af;
                margin-top: 15px;
            }}
            
            @media only screen and (max-width: 480px) {{
                .content {{
                    padding: 25px 20px;
                }}
                .otp-code {{
                    font-size: 32px;
                    letter-spacing: 5px;
                    padding: 15px 20px;
                }}
                .greeting {{
                    font-size: 20px;
                }}
            }}
            
            @keyframes copyFeedback {{
                0% {{ transform: scale(1); background-color: white; }}
                50% {{ transform: scale(1.05); background-color: #fed7aa; }}
                100% {{ transform: scale(1); background-color: white; }}
            }}
            
            .copy-feedback {{
                animation: copyFeedback 0.3s ease;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <div class="logo-container">
                    <img src="https://res.cloudinary.com/ddj0k8gdw/image/upload/v1769389099/Halimatu-Academy-Images/logo_3_1_bmduex.png" 
                        alt="Halimatu" 
                        class="logo">
                </div>
                <div class="company-name">Halimatu</div>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Reset Your Password 🔐
                </div>
                
                <div class="message">
                    We received a request to reset your password. Use the code below to create a new password.
                </div>
                
                <div class="otp-container">
                    <div class="otp-label">Password Reset Code</div>
                    <div class="otp-code" id="otpCode">{otp_code}</div>
                    <div class="copy-instruction">
                        📋 Click the code above to copy
                    </div>
                    <div class="expiry-info">
                        ⏰ Valid for 10 minutes
                    </div>
                </div>
                
                <div class="warning-box">
                    <div class="warning-text">
                        ⚠️ <strong>Security Notice:</strong> If you didn't request this, please ignore this email. 
                        Your account remains secure.
                    </div>
                </div>
                
                <div class="message" style="font-size: 13px; text-align: center; margin-top: 15px;">
                    Enter this code on the password reset page to continue.
                </div>
            </div>
            
            <div class="footer">
                <div class="help-text">
                    Need help? Contact support@halimatu.com
                </div>
                <div class="copyright">
                    © {current_year} Halimatu LMS. All rights reserved.<br>
                    This is an automated message, please do not reply.
                </div>
            </div>
        </div>
        
        <script>
            const otpElement = document.getElementById('otpCode');
            if (otpElement) {{
                otpElement.addEventListener('click', function() {{
                    const text = this.innerText;
                    navigator.clipboard.writeText(text).then(() => {{
                        this.classList.add('copy-feedback');
                        setTimeout(() => {{
                            this.classList.remove('copy-feedback');
                        }}, 300);
                        
                        const instruction = document.querySelector('.copy-instruction');
                        const originalText = instruction.innerHTML;
                        instruction.innerHTML = '✓ Copied!';
                        setTimeout(() => {{
                            instruction.innerHTML = originalText;
                        }}, 1500);
                    }});
                }});
            }}
        </script>
    </body>
    </html>
    """
    
    send_email(email, subject, body)

def send_email(to_email: str, subject: str, html_body: str):
    """Generic email sender"""
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
        # Don't raise exception to avoid breaking the API response