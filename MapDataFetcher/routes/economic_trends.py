import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from services.trading_economics import get_interest_rates, get_inflation_data, get_gdp_data, get_housing_data
from services.ml_models import forecast_market_direction
from services.database import save_economic_indicator, get_economic_indicators

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('economic_trends', __name__, url_prefix='/api/economic-trends')

@bp.route('', methods=['GET'])
def get_economic_trends():
    """
    Get economic trends overview including interest rates, inflation, GDP, 
    and market direction forecast
    
    Query parameters:
        - country: str (default: 'United States')
        - period: str (default: '1y') - Options: '1m', '3m', '6m', '1y', '5y'
    """
    try:
        country = request.args.get('country', 'United States')
        period = request.args.get('period', '1y')
        
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
        
        # Get data for each indicator
        interest_rates = get_interest_rates(country, start_date, end_date)
        inflation_data = get_inflation_data(country, start_date, end_date)
        gdp_data = get_gdp_data(country, start_date, end_date)
        housing_data = get_housing_data(country, start_date, end_date)
        
        # Generate market forecast
        market_forecast = forecast_market_direction(interest_rates, inflation_data, gdp_data)
        
        # Structure the response
        response_data = {
            'interest_rates': [rate.to_dict() for rate in interest_rates] if interest_rates else [],
            'inflation_data': [infl.to_dict() for infl in inflation_data] if inflation_data else [],
            'gdp_data': [gdp.to_dict() for gdp in gdp_data] if gdp_data else [],
            'housing_data': housing_data,
            'market_forecast': market_forecast
        }
        
        return jsonify({
            'status': 'success',
            'data': response_data
        })
    
    except Exception as e:
        logger.error(f"Error fetching economic trends: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to fetch economic trends: {str(e)}"
        }), 500

@bp.route('/interest-rates', methods=['GET'])
def get_interest_rates_endpoint():
    """Get interest rates for a specified country and time period"""
    try:
        country = request.args.get('country', 'United States')
        period = request.args.get('period', '1y')
        
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
        
        interest_rates = get_interest_rates(country, start_date, end_date)
        
        # Convert objects to dict for JSON response
        rates_data = [rate.to_dict() for rate in interest_rates] if interest_rates else []
        
        return jsonify({
            'status': 'success',
            'data': rates_data
        })
    
    except Exception as e:
        logger.error(f"Error fetching interest rates: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to fetch interest rates: {str(e)}"
        }), 500

@bp.route('/inflation', methods=['GET'])
def get_inflation_endpoint():
    """Get inflation data for a specified country and time period"""
    try:
        country = request.args.get('country', 'United States')
        period = request.args.get('period', '1y')
        
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
        
        inflation_data = get_inflation_data(country, start_date, end_date)
        
        # Convert objects to dict for JSON response
        inflation_dict = [infl.to_dict() for infl in inflation_data] if inflation_data else []
        
        return jsonify({
            'status': 'success',
            'data': inflation_dict
        })
    
    except Exception as e:
        logger.error(f"Error fetching inflation data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to fetch inflation data: {str(e)}"
        }), 500

@bp.route('/gdp', methods=['GET'])
def get_gdp_endpoint():
    """Get GDP data for a specified country and time period"""
    try:
        country = request.args.get('country', 'United States')
        period = request.args.get('period', '1y')
        
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
        
        gdp_data = get_gdp_data(country, start_date, end_date)
        
        # Convert objects to dict for JSON response
        gdp_dict = [gdp.to_dict() for gdp in gdp_data] if gdp_data else []
        
        return jsonify({
            'status': 'success',
            'data': gdp_dict
        })
    
    except Exception as e:
        logger.error(f"Error fetching GDP data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to fetch GDP data: {str(e)}"
        }), 500

@bp.route('/forecast', methods=['GET'])
def get_market_forecast():
    """Get real estate market direction forecast (boom/dip)"""
    try:
        country = request.args.get('country', 'United States')
        
        # Get necessary data for forecast
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Use 1 year of data for forecast
        
        interest_rates = get_interest_rates(country, start_date, end_date)
        inflation_data = get_inflation_data(country, start_date, end_date)
        gdp_data = get_gdp_data(country, start_date, end_date)
        
        # Generate forecast
        forecast = forecast_market_direction(interest_rates, inflation_data, gdp_data)
        
        return jsonify({
            'status': 'success',
            'data': forecast
        })
    
    except Exception as e:
        logger.error(f"Error generating market forecast: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to generate market forecast: {str(e)}"
        }), 500