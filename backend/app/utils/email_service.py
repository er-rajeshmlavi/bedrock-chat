"""
Email utility for sending summaries via email
Supports Gmail SMTP with app passwords
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending summaries"""
    
    def __init__(
        self, 
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email or os.getenv("SMTP_EMAIL")
        self.sender_password = sender_password or os.getenv("SMTP_PASSWORD")
    
    def send_summary_email(
        self,
        recipient_email: str,
        summary_content: str,
        summary_type: str = "general",
        subject_prefix: str = "Chat Summary"
    ) -> dict:
        """
        Send a summary email to the specified recipient
        
        Args:
            recipient_email: Email address to send to
            summary_content: The summary content to send
            summary_type: Type of summary (general, key_points, etc.)
            subject_prefix: Prefix for email subject
            
        Returns:
            Dict with success status and message
        """
        try:
            if not self.sender_email or not self.sender_password:
                return {
                    "success": False,
                    "error": "Email credentials not configured. Please set SMTP_EMAIL and SMTP_PASSWORD environment variables."
                }
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            # Create subject with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            msg['Subject'] = f"{subject_prefix} - {summary_type.title()} ({timestamp})"
            
            # Create email body
            body = self._create_email_body(summary_content, summary_type, timestamp)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable encryption
            server.login(self.sender_email, self.sender_password)
            
            text = msg.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()
            
            logger.info(f"Summary email sent successfully to {recipient_email}")
            
            return {
                "success": True,
                "message": f"Summary email sent successfully to {recipient_email}",
                "sent_at": timestamp,
                "subject": msg['Subject']
            }
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _create_email_body(self, summary_content: str, summary_type: str, timestamp: str) -> str:
        """Create formatted HTML email body"""
        
        # Define icons and colors for different summary types
        type_info = {
            "general": {"icon": "📄", "color": "#2563eb"},
            "key_points": {"icon": "🔑", "color": "#dc2626"},
            "action_items": {"icon": "✅", "color": "#16a34a"},
            "technical": {"icon": "⚙️", "color": "#9333ea"}
        }
        
        info = type_info.get(summary_type, type_info["general"])
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Chat Summary</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background-color: {info['color']};
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    padding: 30px;
                }}
                .summary-type {{
                    background-color: #f8f9fa;
                    border-left: 4px solid {info['color']};
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .summary-text {{
                    white-space: pre-wrap;
                    font-size: 16px;
                    line-height: 1.8;
                    color: #333;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 14px;
                    color: #666;
                    border-top: 1px solid #e9ecef;
                }}
                .timestamp {{
                    color: #6c757d;
                    font-size: 14px;
                    margin-top: 20px;
                }}
                .powered-by {{
                    margin-top: 15px;
                    font-size: 12px;
                    color: #999;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{info['icon']} Chat Summary</h1>
                </div>
                
                <div class="content">
                    <div class="summary-type">
                        <strong>{info['icon']} {summary_type.replace('_', ' ').title()} Summary</strong>
                    </div>
                    
                    <div class="summary-text">
{summary_content}
                    </div>
                    
                    <div class="timestamp">
                        <strong>Generated:</strong> {timestamp}
                    </div>
                </div>
                
                <div class="footer">
                    <p>This summary was automatically generated by your AI assistant.</p>
                    <div class="powered-by">
                        Powered by Bedrock Chat Summary Tool
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_body


# Singleton instance
email_service = EmailService()


def send_summary_email(
    recipient_email: str,
    summary_content: str,
    summary_type: str = "general",
    sender_email: Optional[str] = None,
    sender_password: Optional[str] = None
) -> dict:
    """
    Convenience function to send summary email
    
    Args:
        recipient_email: Email to send to
        summary_content: Summary text
        summary_type: Type of summary
        sender_email: Override sender email
        sender_password: Override sender password
    """
    service = EmailService(sender_email=sender_email, sender_password=sender_password)
    return service.send_summary_email(recipient_email, summary_content, summary_type)
