import logging
import os
from flask import Blueprint, request, jsonify
from services.database import save_alert, get_user_alerts, delete_alert
from services.notification import send_sms_notification, send_email_notification

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('alert_system', __name__, url_prefix='/api/alerts')

@bp.route('/create', methods=['POST'])
def create_alert():
    """
    Create a new alert for price changes, investment opportunities, etc.
    
    Request JSON:
    {
        "user_id": "user123",  # identifier for the user
        "alert_type": "price_change|investment_opportunity|market_trend",
        "location": "City, State",
        "property_type": "residential|commercial|land",
        "condition": "above|below|equal",  # e.g., "price below 500000"
        "threshold_value": 500000,
        "notification_method": "sms|email|both",
        "phone_number": "+1234567890",  # required for SMS
        "email": "user@example.com",   # required for email
        "frequency": "immediately|daily|weekly"
    }
    """
    try:
        data = request.get_json()
        
        # Required fields
        user_id = data.get('user_id')
        alert_type = data.get('alert_type')
        location = data.get('location')
        property_type = data.get('property_type')
        condition = data.get('condition')
        threshold_value = data.get('threshold_value')
        notification_method = data.get('notification_method')
        frequency = data.get('frequency', 'immediately')
        
        # Notification method specific fields
        phone_number = data.get('phone_number')
        email = data.get('email')
        
        # Input validation
        if not all([user_id, alert_type, location, property_type, condition, threshold_value, notification_method]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400
            
        if notification_method in ['sms', 'both'] and not phone_number:
            return jsonify({
                'status': 'error',
                'message': 'Phone number is required for SMS notifications'
            }), 400
            
        if notification_method in ['email', 'both'] and not email:
            return jsonify({
                'status': 'error',
                'message': 'Email is required for email notifications'
            }), 400
        
        # Save alert to database
        alert_id = save_alert(
            user_id=user_id,
            alert_type=alert_type,
            location=location,
            property_type=property_type,
            condition=condition,
            threshold_value=threshold_value,
            notification_method=notification_method,
            phone_number=phone_number,
            email=email,
            frequency=frequency
        )
        
        if alert_id:
            return jsonify({
                'status': 'success',
                'message': 'Alert created successfully',
                'alert_id': alert_id
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create alert'
            }), 500
    
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/list', methods=['GET'])
def list_alerts():
    """
    Get all alerts for a specific user
    
    Query parameters:
    - user_id: str (required)
    """
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
            
        alerts = get_user_alerts(user_id)
        
        return jsonify({
            'status': 'success',
            'data': alerts
        })
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/delete/<int:alert_id>', methods=['DELETE'])
def delete_alert_endpoint(alert_id):
    """
    Delete a specific alert
    
    Path parameter:
    - alert_id: int
    """
    try:
        result = delete_alert(alert_id)
        
        if result:
            return jsonify({
                'status': 'success',
                'message': 'Alert deleted successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to delete alert or alert not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error deleting alert: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/test-notification', methods=['POST'])
def test_notification():
    """
    Send a test notification to verify SMS and email setup
    
    Request JSON:
    {
        "notification_method": "sms|email|both",
        "phone_number": "+1234567890",  # required for SMS
        "email": "user@example.com",    # required for email
        "message": "This is a test message"
    }
    """
    try:
        data = request.get_json()
        
        notification_method = data.get('notification_method')
        phone_number = data.get('phone_number')
        email = data.get('email')
        message = data.get('message', 'This is a test notification from Smart Estate Compass')
        
        # Validation
        if not notification_method:
            return jsonify({
                'status': 'error',
                'message': 'Notification method is required'
            }), 400
            
        results = {}
        
        # Send SMS if requested
        if notification_method in ['sms', 'both']:
            if not phone_number:
                return jsonify({
                    'status': 'error',
                    'message': 'Phone number is required for SMS notifications'
                }), 400
                
            sms_result = send_sms_notification(phone_number, message)
            results['sms'] = sms_result
            
        # Send email if requested
        if notification_method in ['email', 'both']:
            if not email:
                return jsonify({
                    'status': 'error',
                    'message': 'Email is required for email notifications'
                }), 400
                
            email_result = send_email_notification(
                to_email=email,
                subject="Smart Estate Compass Test Notification",
                body=message
            )
            results['email'] = email_result
            
        return jsonify({
            'status': 'success',
            'message': 'Test notification(s) sent',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500