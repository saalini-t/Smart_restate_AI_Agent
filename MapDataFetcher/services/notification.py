import os
import logging
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# SendGrid configuration
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

# Flask-Mail configuration (for fallback)
mail = None

def init_mail_app(app):
    """Initialize Flask-Mail with the app"""
    global mail
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
    mail = Mail(app)
    return mail

def send_sms_notification(to_phone_number, message):
    """
    Send SMS notification using Twilio
    
    Args:
        to_phone_number (str): Recipient phone number in E.164 format (+1XXXXXXXXXX)
        message (str): SMS content
        
    Returns:
        dict: Result of the operation with status and details
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        logger.error("Twilio credentials not configured. Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables.")
        return {
            'success': False,
            'message': 'Twilio credentials not configured'
        }
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send SMS message
        twilio_message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        
        logger.info(f"SMS sent successfully with SID: {twilio_message.sid}")
        return {
            'success': True,
            'message': 'SMS sent successfully',
            'sid': twilio_message.sid
        }
        
    except Exception as e:
        logger.error(f"Failed to send SMS: {str(e)}")
        return {
            'success': False,
            'message': f'Failed to send SMS: {str(e)}'
        }

def send_email_notification(to_email, subject, body, html_content=None):
    """
    Send email notification using SendGrid or Flask-Mail as fallback
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Plain text email body
        html_content (str, optional): HTML content for the email
        
    Returns:
        dict: Result of the operation with status and details
    """
    # Try SendGrid first
    if SENDGRID_API_KEY:
        try:
            message = Mail(
                from_email=os.environ.get('FROM_EMAIL', 'noreply@smartestatecompass.com'),
                to_emails=to_email,
                subject=subject,
                plain_text_content=body,
                html_content=html_content or body
            )
            
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            
            logger.info(f"Email sent via SendGrid with status code: {response.status_code}")
            return {
                'success': True,
                'message': 'Email sent successfully via SendGrid',
                'status_code': response.status_code
            }
            
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {str(e)}")
            # Fall back to Flask-Mail if SendGrid fails
    
    # Use Flask-Mail as fallback
    if mail:
        try:
            msg = Message(
                subject=subject,
                recipients=[to_email],
                body=body,
                html=html_content or body
            )
            
            mail.send(msg)
            
            logger.info(f"Email sent via Flask-Mail to {to_email}")
            return {
                'success': True,
                'message': 'Email sent successfully via Flask-Mail'
            }
            
        except Exception as e:
            logger.error(f"Failed to send email via Flask-Mail: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}'
            }
    
    # If both methods fail or are not configured
    logger.error("Email services not configured. Please set SENDGRID_API_KEY or configure Flask-Mail.")
    return {
        'success': False,
        'message': 'Email services not configured'
    }