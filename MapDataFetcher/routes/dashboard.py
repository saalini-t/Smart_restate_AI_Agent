import logging
from flask import Blueprint, request, jsonify, send_file
import json
from datetime import datetime, timedelta
import io
import os
from services.database import get_property_history, get_economic_indicators
from services.ml_models import forecast_market_direction
from services.pdf_generator import generate_dashboard_pdf, generate_report_pdf

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('/summary', methods=['GET'])
def get_dashboard_summary():
    """
    Get a summary of data for the user dashboard
    
    Query parameters:
    - user_id: str
    - location: str (optional, user's primary location)
    """
    try:
        user_id = request.args.get('user_id')
        location = request.args.get('location', 'United States')  # Default to US if no location
        
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
            
        # Get current date
        current_date = datetime.now()
        three_months_ago = current_date - timedelta(days=90)
        one_year_ahead = current_date + timedelta(days=365)
        
        # Get economic indicators
        interest_rates = get_economic_indicators('interest-rate', three_months_ago, current_date)
        inflation_data = get_economic_indicators('inflation-rate', three_months_ago, current_date)
        gdp_data = get_economic_indicators('gdp-growth', three_months_ago, current_date)
        
        # Get market direction forecast
        market_forecast = forecast_market_direction(interest_rates, inflation_data, gdp_data)
        
        # Get property price data if location is specified
        property_trends = None
        if location and location != 'United States':
            property_trends = get_property_history(location, period='1y')
        
        # Prepare dashboard data
        dashboard_data = {
            'market_summary': {
                'interest_rate': interest_rates[-1].value if interest_rates else None,
                'inflation_rate': inflation_data[-1].value if inflation_data else None,
                'gdp_growth': gdp_data[-1].value if gdp_data else None,
                'market_direction': market_forecast.get('direction', 'stable'),
                'confidence': market_forecast.get('confidence', 0.7)
            },
            'property_trends': [p.to_dict() for p in property_trends] if property_trends else None,
            'alerts_count': 3,  # Placeholder, should be fetched from alerts database
            'saved_searches_count': 5,  # Placeholder, should be fetched from user data
            'recent_calculations': []  # Placeholder for recent ROI calculations
        }
        
        return jsonify({
            'status': 'success',
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/market-indicators', methods=['GET'])
def get_market_indicators():
    """
    Get detailed market indicators for dashboard charts
    
    Query parameters:
    - period: str (1m, 3m, 6m, 1y, 5y) - default: 1y
    - country: str - default: United States
    """
    try:
        period = request.args.get('period', '1y')
        country = request.args.get('country', 'United States')
        
        # Calculate date range based on period
        end_date = datetime.now()
        if period == '1m':
            start_date = end_date - timedelta(days=30)
        elif period == '3m':
            start_date = end_date - timedelta(days=90)
        elif period == '6m':
            start_date = end_date - timedelta(days=180)
        elif period == '1y':
            start_date = end_date - timedelta(days=365)
        elif period == '5y':
            start_date = end_date - timedelta(days=365 * 5)
        else:
            start_date = end_date - timedelta(days=365)  # Default to 1 year
        
        # Get indicators
        interest_rates = get_economic_indicators('interest-rate', start_date, end_date, country)
        inflation_data = get_economic_indicators('inflation-rate', start_date, end_date, country)
        gdp_data = get_economic_indicators('gdp-growth', start_date, end_date, country)
        housing_index = get_economic_indicators('housing-index', start_date, end_date, country)
        
        # Format data for charts
        chart_data = {
            'interest_rates': [{'date': i.date.strftime('%Y-%m-%d'), 'value': i.value} for i in interest_rates],
            'inflation': [{'date': i.date.strftime('%Y-%m-%d'), 'value': i.value} for i in inflation_data],
            'gdp': [{'date': i.date.strftime('%Y-%m-%d'), 'value': i.value} for i in gdp_data],
            'housing_index': [{'date': i.date.strftime('%Y-%m-%d'), 'value': i.value} for i in housing_index]
        }
        
        return jsonify({
            'status': 'success',
            'data': chart_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching market indicators: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/export-pdf', methods=['POST'])
def export_dashboard_pdf():
    """
    Generate a PDF report of dashboard data
    
    Request JSON:
    {
        "user_id": "user123",
        "location": "San Francisco, CA",
        "include_economic_data": true,
        "include_property_data": true,
        "include_predictions": true,
        "timeframe": "1y"
    }
    """
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        location = data.get('location', 'United States')
        include_economic_data = data.get('include_economic_data', True)
        include_property_data = data.get('include_property_data', True)
        include_predictions = data.get('include_predictions', True)
        timeframe = data.get('timeframe', '1y')
        
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
            
        # Generate PDF
        pdf_bytes = generate_dashboard_pdf(
            user_id=user_id,
            location=location,
            include_economic_data=include_economic_data,
            include_property_data=include_property_data,
            include_predictions=include_predictions,
            timeframe=timeframe
        )
        
        # Prepare PDF for download
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"smart_estate_report_{timestamp}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            attachment_filename=filename,
            cache_timeout=0
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/export-property-report', methods=['POST'])
def export_property_report():
    """
    Generate a detailed PDF report for a specific property
    
    Request JSON:
    {
        "location": "San Francisco, CA",
        "property_type": "residential",
        "property_details": {
            "address": "123 Main St",
            "area_sqft": 2000,
            "bedrooms": 3,
            "bathrooms": 2,
            "year_built": 2010
        },
        "include_location_score": true,
        "include_price_prediction": true,
        "include_investment_analysis": true
    }
    """
    try:
        data = request.get_json()
        
        location = data.get('location')
        property_type = data.get('property_type')
        property_details = data.get('property_details', {})
        include_location_score = data.get('include_location_score', True)
        include_price_prediction = data.get('include_price_prediction', True)
        include_investment_analysis = data.get('include_investment_analysis', True)
        
        if not location or not property_type:
            return jsonify({
                'status': 'error',
                'message': 'Location and property type are required'
            }), 400
        
        # Generate property report PDF
        pdf_bytes = generate_report_pdf(
            location=location,
            property_type=property_type,
            property_details=property_details,
            include_location_score=include_location_score,
            include_price_prediction=include_price_prediction,
            include_investment_analysis=include_investment_analysis
        )
        
        # Prepare PDF for download
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        address_slug = property_details.get('address', '').replace(' ', '_').lower()
        filename = f"property_report_{address_slug}_{timestamp}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            attachment_filename=filename,
            cache_timeout=0
        )
        
    except Exception as e:
        logger.error(f"Error generating property report: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500