import logging
from flask import Blueprint, request, jsonify
from services.database import save_roi_calculation, get_roi_history
from services.ml_models import calculate_investment_roi

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('roi_calculator', __name__, url_prefix='/api/roi-calculator')

@bp.route('/calculate', methods=['POST'])
def calculate_roi():
    """
    Calculate potential ROI for an investment
    
    Request JSON:
    {
        "location": "City, State",
        "property_type": "residential|commercial|land",
        "purchase_price": 500000,
        "investment_goal": "flip|rent|hold",
        "timeframe": 5,  # years
        "additional_investment": 50000,  # optional, renovations etc.
        "expected_rent": 2500,  # optional, monthly for rental properties
        "expected_expenses": 500  # optional, monthly expenses
    }
    """
    try:
        data = request.get_json()
        
        # Required fields
        location = data.get('location')
        property_type = data.get('property_type')
        purchase_price = data.get('purchase_price')
        investment_goal = data.get('investment_goal')
        timeframe = data.get('timeframe')
        
        # Optional fields with defaults
        additional_investment = data.get('additional_investment', 0)
        expected_rent = data.get('expected_rent', 0)
        expected_expenses = data.get('expected_expenses', 0)
        
        # Input validation
        if not all([location, property_type, purchase_price, investment_goal, timeframe]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400
        
        # Calculate ROI
        roi_result = calculate_investment_roi(
            location=location,
            property_type=property_type,
            purchase_price=purchase_price,
            investment_goal=investment_goal,
            timeframe=timeframe,
            additional_investment=additional_investment,
            expected_rent=expected_rent,
            expected_expenses=expected_expenses
        )
        
        # Save calculation to database
        save_roi_calculation(location, property_type, investment_goal, purchase_price, roi_result)
        
        return jsonify({
            'status': 'success',
            'data': roi_result
        })
    
    except Exception as e:
        logger.error(f"Error calculating ROI: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/history', methods=['GET'])
def get_roi_history_endpoint():
    """
    Get historical ROI calculations for a location
    
    Query parameters:
    - location: str (City, State)
    - property_type: str (optional)
    - limit: int (optional, default: 10)
    """
    try:
        location = request.args.get('location')
        property_type = request.args.get('property_type')
        limit = int(request.args.get('limit', 10))
        
        if not location:
            return jsonify({
                'status': 'error',
                'message': 'Location is required'
            }), 400
            
        history = get_roi_history(location, property_type, limit)
        
        return jsonify({
            'status': 'success',
            'data': [item.to_dict() for item in history]
        })
        
    except Exception as e:
        logger.error(f"Error fetching ROI history: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500