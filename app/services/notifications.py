import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Service for sending email notifications.
    
    For development, this can use a local SMTP debugger like MailHog.
    For production, configure with a real email service.
    """
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.enabled = settings.EMAIL_ENABLED

    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email with both HTML and plain text versions.
        """
        if not self.enabled:
            logger.info(f"Email sending disabled. Would have sent to {to_email}: {subject}")
            return True
            
        if not text_content:
            text_content = f"Please view this email in an HTML-compatible email client.\n\n{subject}"
            
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            # Add plain text and HTML parts
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            
            message.attach(part1)
            message.attach(part2)
            
            # Connect to server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(
                    self.from_email,
                    [to_email],
                    message.as_string()
                )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
            
    async def send_order_confirmation(
        self,
        to_email: str,
        order_details: Dict[str, Any]
    ) -> bool:
        """
        Send order confirmation email.
        """
        subject = f"Order Confirmation #{order_details['id']}"
        
        # Build HTML content
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .order-details {{ border: 1px solid #ddd; padding: 15px; }}
                    .items {{ width: 100%; border-collapse: collapse; }}
                    .items th, .items td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <h1>Thank you for your order!</h1>
                <p>We've received your order and are processing it now.</p>
                
                <div class="order-details">
                    <h2>Order #{order_details['id']}</h2>
                    <p><strong>Date:</strong> {order_details['created_at']}</p>
                    <p><strong>Status:</strong> {order_details['status']}</p>
                    <p><strong>Total:</strong> ${order_details['total_amount']:.2f}</p>
                    
                    <h3>Items:</h3>
                    <table class="items">
                        <tr>
                            <th>Product</th>
                            <th>Quantity</th>
                            <th>Price</th>
                        </tr>
        """
        
        # Add items to the email
        for item in order_details['items']:
            html_content += f"""
                <tr>
                    <td>{item['product_name']}</td>
                    <td>{item['quantity']}</td>
                    <td>${item['unit_price']:.2f}</td>
                </tr>
            """
            
        html_content += f"""
                    </table>
                    
                    <h3>Shipping Address:</h3>
                    <p>{order_details['shipping_address']}</p>
                </div>
                
                <div class="footer">
                    <p>If you have any questions, please contact our customer support.</p>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)

email_service = EmailService()
