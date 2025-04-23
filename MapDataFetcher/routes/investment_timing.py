import logging
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from services.ml_models import predict_investment_timing
from services.trading_economics import get_interest_rates, get_inflation_data
from services.database import get_investment_history, save_investment_recommendation

# Set up logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('investment_timing', __name__, url_prefix='/api/investment-timing')

@bp.route('/recommend', methods=['POST'])
def get_investment_recommendation():
    """
    Get investment timing recommendation based on user's investment goals
    
    Request JSON:
    {
        "location": "City, State",
        "property_type": "residential|commercial|land",
        "investment_goal": "flip|rent|hold",
        "timeframe": 5,  # years
        "budget": 500000,  # optional
        "roi_expectation": 15  # expected ROI percentage, optional
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Extract parameters
        location = data.get('location')
        property_type = data.get('property_type')
        investment_goal = data.get('investment_goal')
        timeframe = data.get('timeframe')
        budget = data.get('budget')
        roi_expectation = data.get('roi_expectation')
        
        # Validate required parameters
        if not location or not property_type or not investment_goal or not timeframe:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters: location, property_type, investment_goal, and timeframe are required'
            }), 400
        
        # Get economic indicators for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Use 1 year of data
        
        interest_rates = get_interest_rates('United States', start_date, end_date)
        inflation_data = get_inflation_data('United States', start_date, end_date)
        
        # Get investment recommendation
        recommendation = predict_investment_timing(
            location=location,
            property_type=property_type,
            investment_goal=investment_goal,
            timeframe=int(timeframe),
            interest_rates=interest_rates,
            inflation_data=inflation_data,
            budget=float(budget) if budget else None,
            roi_expectation=float(roi_expectation) if roi_expectation else None
        )
        
        # Save recommendation to database
        save_investment_recommendation(
            location=location,
            property_type=property_type,
            investment_goal=investment_goal,
            timeframe=int(timeframe),
            recommendation=recommendation
        )
        
        return jsonify({
            'status': 'success',
            'data': recommendation
        })
    
    except Exception as e:
        logger.error(f"Error getting investment recommendation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to get investment recommendation: {str(e)}"
        }), 500

@bp.route('/history', methods=['GET'])
def get_recommendation_history():
    """
    Get historical investment recommendations for a location
    
    Query parameters:
    - location: str (City, State)
    - property_type: str (optional)
    - limit: int (optional, default: 10)
    """
    try:
        # Get query parameters
        location = request.args.get('location')
        property_type = request.args.get('property_type')
        limit = int(request.args.get('limit', 10))
        
        # Validate required parameters
        if not location:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: location'
            }), 400
        
        # Get investment recommendation history
        history = get_investment_history(
            location=location,
            property_type=property_type,
            limit=limit
        )
        
        # Convert to dictionaries for JSON serialization
        recommendations = [rec.to_dict() for rec in history] if history else []
        
        return jsonify({
            'status': 'success',
            'data': recommendations
        })
    
    except Exception as e:
        logger.error(f"Error fetching investment history: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to fetch investment history: {str(e)}"
        }), 500

@bp.route('/momentum', methods=['GET'])
def get_price_momentum():
    """
    Get price momentum data for a location
    
    Query parameters:
    - location: str (City, State)
    - property_type: str (optional)
    - period: str (optional, default: '1y')
    """
    try:
        # Get query parameters
        location = request.args.get('location')
        property_type = request.args.get('property_type', 'residential')
        period = request.args.get('period', '1y')
        
        # Validate required parameters
        if not location:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: location'
            }), 400
        
        # Get economic indicators for analysis
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
        
        # Get economic indicators
        interest_rates = get_interest_rates('United States', start_date, end_date)
        inflation_data = get_inflation_data('United States', start_date, end_date)
        
        # Calculate momentum score
        momentum_score = calculate_momentum_score(interest_rates, inflation_data, location, property_type)
        
        # Get recommendation for investment decision
        recommendation = determine_investment_action(momentum_score)
        
        return jsonify({
            'status': 'success',
            'data': {
                'location': location,
                'property_type': property_type,
                'period': period,
                'momentum_score': momentum_score,
                'recommendation': recommendation,
                'indicators': {
                    'interest_rates': [rate.to_dict() for rate in interest_rates][-3:],  # Last 3 data points
                    'inflation': [inflation.to_dict() for inflation in inflation_data][-3:]  # Last 3 data points
                }
            }
        })
    
    except Exception as e:
        logger.error(f"Error calculating price momentum: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to calculate price momentum: {str(e)}"
        }), 500

@bp.route('/roi', methods=['POST'])
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
        # Get JSON data from request
        data = request.get_json()
        
        # Extract parameters
        location = data.get('location')
        property_type = data.get('property_type')
        purchase_price = data.get('purchase_price')
        investment_goal = data.get('investment_goal')
        timeframe = data.get('timeframe')
        additional_investment = data.get('additional_investment', 0)
        expected_rent = data.get('expected_rent')
        expected_expenses = data.get('expected_expenses', 0)
        
        # Validate required parameters
        if not location or not property_type or not purchase_price or not investment_goal or not timeframe:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters: location, property_type, purchase_price, investment_goal, and timeframe are required'
            }), 400
        
        # Calculate ROI based on investment goal
        if investment_goal == 'flip':
            roi_data = calculate_flip_roi(
                location=location,
                property_type=property_type,
                purchase_price=float(purchase_price),
                renovation_cost=float(additional_investment),
                timeframe=int(timeframe)
            )
        elif investment_goal == 'rent':
            # Ensure expected_rent is provided for rental properties
            if not expected_rent:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required parameter for rental properties: expected_rent'
                }), 400
            
            roi_data = calculate_rental_roi(
                location=location,
                property_type=property_type,
                purchase_price=float(purchase_price),
                renovation_cost=float(additional_investment),
                monthly_rent=float(expected_rent),
                monthly_expenses=float(expected_expenses),
                timeframe=int(timeframe)
            )
        else:  # hold
            roi_data = calculate_hold_roi(
                location=location,
                property_type=property_type,
                purchase_price=float(purchase_price),
                renovation_cost=float(additional_investment),
                timeframe=int(timeframe)
            )
        
        return jsonify({
            'status': 'success',
            'data': roi_data
        })
    
    except Exception as e:
        logger.error(f"Error calculating ROI: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to calculate ROI: {str(e)}"
        }), 500

def calculate_momentum_score(interest_rates, inflation_data, location, property_type):
    """Calculate momentum score based on economic indicators and location"""
    import random
    
    # Analyze interest rate trend
    if interest_rates and len(interest_rates) > 1:
        # Compare last rate with first rate
        first_rate = interest_rates[0].value
        last_rate = interest_rates[-1].value
        
        if last_rate < first_rate:
            interest_score = 20  # Decreasing rates are good for real estate
        elif last_rate > first_rate:
            interest_score = -10  # Increasing rates are bad for real estate
        else:
            interest_score = 5  # Stable rates are neutral
    else:
        interest_score = 0
    
    # Analyze inflation trend
    if inflation_data and len(inflation_data) > 1:
        # Compare last inflation with first inflation
        first_inflation = inflation_data[0].value
        last_inflation = inflation_data[-1].value
        
        if last_inflation > 4.0:
            inflation_score = -5  # High inflation is generally bad
        elif last_inflation > first_inflation:
            inflation_score = 5  # Moderate increasing inflation can be good for real estate
        else:
            inflation_score = 0  # Stable or decreasing inflation is neutral
    else:
        inflation_score = 0
    
    # Location factor (would ideally be based on more detailed market analysis)
    location_factor = 0
    hot_markets = ['New York', 'San Francisco', 'Los Angeles', 'Seattle', 'Austin', 'Miami']
    
    if any(market in location for market in hot_markets):
        location_factor = 10
    
    # Property type factor
    if property_type == 'residential':
        type_factor = 5
    elif property_type == 'commercial':
        type_factor = 0  # Neutral
    else:  # land
        type_factor = -5  # Land typically has slower momentum
    
    # Calculate total momentum score
    total_score = interest_score + inflation_score + location_factor + type_factor
    
    # Add some randomness to simulate other market factors
    total_score += random.randint(-5, 5)
    
    # Normalize to -100 to 100 scale
    normalized_score = max(-100, min(100, total_score * 3))
    
    return round(normalized_score, 1)

def determine_investment_action(momentum_score):
    """Determine investment action based on momentum score"""
    if momentum_score > 60:
        return {
            'action': 'Strong Buy',
            'confidence': 'High',
            'description': 'Market conditions are highly favorable for investment.'
        }
    elif momentum_score > 20:
        return {
            'action': 'Buy',
            'confidence': 'Medium',
            'description': 'Market conditions are favorable for investment.'
        }
    elif momentum_score > -20:
        return {
            'action': 'Hold',
            'confidence': 'Medium',
            'description': 'Market conditions are neutral. Monitor the market before making decisions.'
        }
    elif momentum_score > -60:
        return {
            'action': 'Sell',
            'confidence': 'Medium',
            'description': 'Market conditions are unfavorable. Consider selling properties not performing well.'
        }
    else:
        return {
            'action': 'Strong Sell',
            'confidence': 'High',
            'description': 'Market conditions are highly unfavorable. Consider selling properties to preserve capital.'
        }

def calculate_flip_roi(location, property_type, purchase_price, renovation_cost, timeframe):
    """Calculate ROI for a property flip"""
    import random
    
    # Initial investment
    initial_investment = purchase_price + renovation_cost
    
    # Holding costs (taxes, insurance, utilities) - approx 1-2% of purchase price per year
    monthly_holding_cost = purchase_price * 0.015 / 12
    holding_period_months = min(timeframe * 12, 12)  # Assume flips take no more than 12 months
    total_holding_costs = monthly_holding_cost * holding_period_months
    
    # Selling costs (agent commission, closing costs) - approx 7-8% of sale price
    selling_cost_percent = 0.075
    
    # Estimate appreciation based on location and renovation impact
    market_appreciation = 0.03  # 3% annual market appreciation
    renovation_impact = renovation_cost / purchase_price  # Renovation ROI factor
    
    # Location adjustment
    hot_markets = ['New York', 'San Francisco', 'Los Angeles', 'Seattle', 'Austin', 'Miami']
    if any(market in location for market in hot_markets):
        market_adjustment = 1.2  # 20% better returns in hot markets
    else:
        market_adjustment = 1.0
    
    # Calculate projected sale price
    renovation_value_multiplier = 1.5  # Each $1 in renovation typically adds $1.5 in value
    market_appreciation_factor = (1 + market_appreciation) ** (holding_period_months / 12)
    
    projected_sale_price = (
        purchase_price * market_appreciation_factor + 
        renovation_cost * renovation_value_multiplier
    ) * market_adjustment
    
    # Add some randomness to simulate market variability
    projected_sale_price *= random.uniform(0.95, 1.05)
    
    # Calculate selling costs
    selling_costs = projected_sale_price * selling_cost_percent
    
    # Calculate net profit
    net_profit = projected_sale_price - initial_investment - total_holding_costs - selling_costs
    
    # Calculate ROI
    roi_percent = (net_profit / initial_investment) * 100
    
    # Calculate annualized ROI
    annualized_roi = ((1 + roi_percent / 100) ** (12 / holding_period_months) - 1) * 100
    
    return {
        'investment_type': 'flip',
        'location': location,
        'property_type': property_type,
        'initial_investment': round(initial_investment, 2),
        'holding_period': f"{holding_period_months} months",
        'projected_sale_price': round(projected_sale_price, 2),
        'total_costs': round(total_holding_costs + selling_costs, 2),
        'net_profit': round(net_profit, 2),
        'roi_percent': round(roi_percent, 2),
        'annualized_roi_percent': round(annualized_roi, 2),
        'confidence': 'medium'  # Confidence level in the projection
    }

def calculate_rental_roi(location, property_type, purchase_price, renovation_cost, monthly_rent, monthly_expenses, timeframe):
    """Calculate ROI for a rental property"""
    import random
    
    # Initial investment
    initial_investment = purchase_price + renovation_cost
    
    # Monthly cash flow
    monthly_cash_flow = monthly_rent - monthly_expenses
    
    # Calculate annual cash flow
    annual_cash_flow = monthly_cash_flow * 12
    
    # Estimate property appreciation
    annual_appreciation_rate = 0.03  # 3% annual appreciation
    
    # Location adjustment
    hot_markets = ['New York', 'San Francisco', 'Los Angeles', 'Seattle', 'Austin', 'Miami']
    if any(market in location for market in hot_markets):
        annual_appreciation_rate *= 1.5  # Higher appreciation in hot markets
    
    # Property type adjustment
    if property_type == 'commercial':
        annual_appreciation_rate *= 0.9  # Commercial properties often appreciate slower
    
    # Calculate future property value
    future_value = purchase_price * ((1 + annual_appreciation_rate) ** timeframe)
    
    # Add some randomness to simulate market variability
    future_value *= random.uniform(0.95, 1.05)
    
    # Calculate selling costs at end of period (if selling)
    selling_cost_percent = 0.075
    selling_costs = future_value * selling_cost_percent
    
    # Calculate total rental income over the period
    total_rental_income = annual_cash_flow * timeframe
    
    # Calculate equity gained through appreciation
    equity_gain = future_value - purchase_price - selling_costs
    
    # Calculate total return
    total_return = total_rental_income + equity_gain
    
    # Calculate cash-on-cash ROI (annual cash flow / initial investment)
    cash_on_cash_roi = (annual_cash_flow / initial_investment) * 100
    
    # Calculate total ROI
    total_roi = (total_return / initial_investment) * 100
    
    # Calculate annualized ROI
    annualized_roi = ((1 + total_roi / 100) ** (1 / timeframe) - 1) * 100
    
    return {
        'investment_type': 'rental',
        'location': location,
        'property_type': property_type,
        'initial_investment': round(initial_investment, 2),
        'monthly_cash_flow': round(monthly_cash_flow, 2),
        'annual_cash_flow': round(annual_cash_flow, 2),
        'projected_future_value': round(future_value, 2),
        'total_rental_income': round(total_rental_income, 2),
        'equity_gain': round(equity_gain, 2),
        'total_return': round(total_return, 2),
        'cash_on_cash_roi_percent': round(cash_on_cash_roi, 2),
        'total_roi_percent': round(total_roi, 2),
        'annualized_roi_percent': round(annualized_roi, 2),
        'confidence': 'medium'  # Confidence level in the projection
    }

def calculate_hold_roi(location, property_type, purchase_price, renovation_cost, timeframe):
    """Calculate ROI for a buy and hold strategy"""
    import random
    
    # Initial investment
    initial_investment = purchase_price + renovation_cost
    
    # Estimate property appreciation
    annual_appreciation_rate = 0.03  # 3% annual appreciation
    
    # Location adjustment
    hot_markets = ['New York', 'San Francisco', 'Los Angeles', 'Seattle', 'Austin', 'Miami']
    if any(market in location for market in hot_markets):
        annual_appreciation_rate *= 1.5  # Higher appreciation in hot markets
    
    # Property type adjustment
    if property_type == 'land':
        annual_appreciation_rate *= 1.2  # Land can appreciate faster in the long term
    elif property_type == 'commercial':
        annual_appreciation_rate *= 0.9  # Commercial properties often appreciate slower
    
    # Calculate future property value
    future_value = purchase_price * ((1 + annual_appreciation_rate) ** timeframe)
    
    # Add some randomness to simulate market variability
    future_value *= random.uniform(0.95, 1.05)
    
    # Calculate selling costs
    selling_cost_percent = 0.075
    selling_costs = future_value * selling_cost_percent
    
    # Calculate annual property tax and maintenance
    annual_costs = purchase_price * 0.02  # About 2% of property value annually
    total_holding_costs = annual_costs * timeframe
    
    # Calculate net profit
    net_profit = future_value - purchase_price - selling_costs - total_holding_costs
    
    # Calculate ROI
    roi_percent = (net_profit / initial_investment) * 100
    
    # Calculate annualized ROI
    annualized_roi = ((1 + roi_percent / 100) ** (1 / timeframe) - 1) * 100
    
    return {
        'investment_type': 'hold',
        'location': location,
        'property_type': property_type,
        'initial_investment': round(initial_investment, 2),
        'holding_period': f"{timeframe} years",
        'projected_future_value': round(future_value, 2),
        'total_holding_costs': round(total_holding_costs, 2),
        'selling_costs': round(selling_costs, 2),
        'net_profit': round(net_profit, 2),
        'roi_percent': round(roi_percent, 2),
        'annualized_roi_percent': round(annualized_roi, 2),
        'confidence': 'medium'  # Confidence level in the projection
    }