import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from app.config import settings
from app.logging.log_streamer import log_streamer

class EmailService:
    @staticmethod
    def send_alert(subject, body, is_html=False):
        """Send email alert asynchronously"""
        if not settings.EMAIL_ENABLED:
            return
        
        def _send():
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = f"[Transcription Server] {subject}"
                msg['From'] = settings.EMAIL_SENDER
                msg['To'] = ", ".join(settings.EMAIL_RECIPIENTS)
                
                if is_html:
                    msg.attach(MIMEText(body, 'html'))
                else:
                    msg.attach(MIMEText(body, 'plain'))
                
                with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                    server.starttls()
                    server.login(settings.EMAIL_SENDER, settings.EMAIL_PASSWORD)
                    server.sendmail(Config.EMAIL_SENDER, Config.EMAIL_RECIPIENTS, msg.as_string())
                
                log_streamer.info("EmailService", f"Alert sent: {subject}")
                
            except Exception as e:
                log_streamer.error("EmailService", f"Failed to send email: {e}")
        
        # Send in background thread
        thread = threading.Thread(target=_send, daemon=True)
        thread.start()
    
    @staticmethod
    def send_failure_alert(call_id, error_message, error_type="Processing Error"):
        """Send failure notification"""
        subject = f"Call Processing Failed - {call_id}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #e74c3c;">⚠️ Call Processing Failed</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Call ID:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{call_id}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Error Type:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{error_type}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Error Message:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{error_message}</td>
                </tr>
            </table>
            <p style="color: #666; margin-top: 20px;">
                Please check the server dashboard for more details.
            </p>
        </body>
        </html>
        """
        
        EmailService.send_alert(subject, body, is_html=True)
    
    @staticmethod
    def send_daily_summary(stats):
        """Send daily summary email"""
        subject = "Daily Transcription Summary"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #3498db;">📊 Daily Transcription Summary</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Total Calls</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{stats.get('today_calls', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Successful</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: #27ae60;">{stats.get('today_success', 0)}</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Failed</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: #e74c3c;">{stats.get('failed', 0)}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>API Calls</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{stats.get('api_calls_today', 0)}</td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        EmailService.send_alert(subject, body, is_html=True)