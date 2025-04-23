import logging
from flask import Blueprint, jsonify, request
from services.ml_models import predict_property_prices
from services.database import get_property_history, save_property_data

# Set up logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('property_price', __name__, url_prefix='/api/property-price')

@bp.route('/predict', methods=['POST'])
def predict_prices():
    """
    Predict property prices for a specific location and property type
    
    Request JSON:
    {
        "location": "City, State",
        "property_type": "residential|commercial|land",
        "area_sqft": 2000,
        "bedrooms": 3,  # Optional for residential
        "bathrooms": 2,  # Optional for residential
        "year_built": 2010,  # Optional
        "forecast_period": "6m|1y|5y"
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Extract parameters
        location = data.get('location')
        property_type = data.get('property_type')
        area_sqft = data.get('area_sqft')
        bedrooms = data.get('bedrooms')
        bathrooms = data.get('bathrooms')
        year_built = data.get('year_built')
        forecast_period = data.get('forecast_period', '1y')
        
        # Validate required parameters
        if not location or not property_type or not area_sqft:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters: location, property_type, and area_sqft are required'
            }), 400
        
        # Call prediction service
        prediction = predict_property_prices(
            location=location,
            property_type=property_type,
            area_sqft=float(area_sqft),
            bedrooms=int(bedrooms) if bedrooms else None,
            bathrooms=int(bathrooms) if bathrooms else None,
            year_built=int(year_built) if year_built else None,
            forecast_period=forecast_period
        )
        
        return jsonify({
            'status': 'success',
            'data': prediction
        })
    
    except Exception as e:
        logger.error(f"Error predicting property prices: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to predict property prices: {str(e)}"
        }), 500

@bp.route('/history', methods=['GET'])
def get_price_history():
    """
    Get historical property price data for a location
    
    Query parameters:
    - location: str (City, State)
    - property_type: str (optional)
    - period: str (default: '1y') - Options: '1m', '3m', '6m', '1y', '5y'
    """
    try:
        # Get query parameters
        location = request.args.get('location')
        property_type = request.args.get('property_type')
        period = request.args.get('period', '1y')
        
        # Validate required parameters
        if not location:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: location'
            }), 400
        
        # Get property price history
        history = get_property_history(
            location=location,
            property_type=property_type,
            period=period
        )
        
        # Convert to dictionaries for JSON serialization
        price_history = [price.to_dict() for price in history] if history else []
        
        return jsonify({
            'status': 'success',
            'data': price_history
        })
    
    except Exception as e:
        logger.error(f"Error fetching property price history: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to fetch property price history: {str(e)}"
        }), 500

@bp.route('/valuation', methods=['GET'])
def get_property_valuation():
    """
    Get current property valuation (under/overvalued assessment)
    
    Query parameters:
    - location: str (City, State)
    - property_type: str (optional)
    """
    try:
        # Get query parameters
        location = request.args.get('location')
        property_type = request.args.get('property_type', 'residential')
        
        # Validate required parameters
        if not location:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: location'
            }), 400
        
        # Call prediction service with a default area to get market assessment
        prediction = predict_property_prices(
            location=location,
            property_type=property_type,
            area_sqft=2000  # Default size for assessment
        )
        
        # Extract market assessment
        valuation = {
            'location': location,
            'property_type': property_type,
            'assessment': prediction.get('market_assessment', {}),
            'confidence': prediction.get('confidence', 0.7)
        }
        
        return jsonify({
            'status': 'success',
            'data': valuation
        })
    
    except Exception as e:
        logger.error(f"Error getting property valuation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to get property valuation: {str(e)}"
        }), 500