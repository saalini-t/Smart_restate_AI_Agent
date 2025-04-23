import logging
from flask import Blueprint, jsonify, request
from services.ml_models import predict_construction_costs
from services.trading_economics import get_material_prices
from services.database import save_construction_plan
from datetime import datetime, timedelta
import random

# Set up logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('construction_planning', __name__, url_prefix='/api/construction-planning')

@bp.route('/estimate', methods=['POST'])
def estimate_construction_costs():
    """
    Estimate construction costs based on location, property type, and area
    
    Request JSON:
    {
        "location": "City, State",
        "property_type": "residential|commercial|industrial",
        "area_sqft": 2000,
        "quality_level": "basic|standard|premium",
        "stories": 1
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Extract parameters
        location = data.get('location')
        property_type = data.get('property_type')
        area_sqft = data.get('area_sqft')
        quality_level = data.get('quality_level', 'standard')
        stories = data.get('stories', 1)
        
        # Validate required parameters
        if not location or not property_type or not area_sqft:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters: location, property_type, and area_sqft are required'
            }), 400
        
        # Get current material prices
        material_prices = get_material_prices()
        
        # Get construction cost estimate
        cost_estimate = predict_construction_costs(
            location=location,
            property_type=property_type,
            area_sqft=float(area_sqft),
            quality_level=quality_level,
            stories=int(stories),
            material_prices=material_prices
        )
        
        # Save construction plan to database (minimal version)
        plan_data = {
            'location': location,
            'optimal_start_date': get_optimal_start_date(location),
            'material_prices': material_prices,
            'weather_forecast': generate_weather_forecast(location, 3),  # 3 months forecast
            'estimated_cost': cost_estimate['total_cost']
        }
        
        # Save plan to database
        save_construction_plan(
            location=location,
            property_type=property_type,
            area_sqft=float(area_sqft),
            quality_level=quality_level,
            plan_data=plan_data
        )
        
        return jsonify({
            'status': 'success',
            'data': cost_estimate
        })
    
    except Exception as e:
        logger.error(f"Error estimating construction costs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to estimate construction costs: {str(e)}"
        }), 500

@bp.route('/materials', methods=['GET'])
def get_material_prices_endpoint():
    """
    Get current material prices for construction
    
    Query parameters:
    - materials: comma-separated list of materials (optional)
    """
    try:
        # Get query parameters
        materials_param = request.args.get('materials')
        
        # Get current material prices
        all_material_prices = get_material_prices()
        
        # Filter by requested materials if specified
        if materials_param:
            requested_materials = [mat.strip() for mat in materials_param.split(',')]
            material_prices = {mat: all_material_prices.get(mat, 0) for mat in requested_materials}
        else:
            material_prices = all_material_prices
        
        return jsonify({
            'status': 'success',
            'data': {
                'materials': material_prices,
                'last_updated': datetime.now().isoformat(),
                'currency': 'USD',
                'notes': 'Prices are average national values and may vary by region'
            }
        })
    
    except Exception as e:
        logger.error(f"Error fetching material prices: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to fetch material prices: {str(e)}"
        }), 500

@bp.route('/weather', methods=['GET'])
def get_weather_forecast():
    """
    Get weather forecast for optimal construction timing
    
    Query parameters:
    - location: str (City, State)
    - months: int (number of months to forecast, default: 3)
    """
    try:
        # Get query parameters
        location = request.args.get('location')
        months = int(request.args.get('months', 3))
        
        # Validate required parameters
        if not location:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: location'
            }), 400
        
        # Generate weather forecast
        forecast = generate_weather_forecast(location, months)
        
        return jsonify({
            'status': 'success',
            'data': {
                'location': location,
                'forecast': forecast
            }
        })
    
    except Exception as e:
        logger.error(f"Error generating weather forecast: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to generate weather forecast: {str(e)}"
        }), 500

@bp.route('/optimal-timing', methods=['POST'])
def get_optimal_construction_timing():
    """
    Get optimal timing for construction based on weather, material prices, and budget
    
    Request JSON:
    {
        "location": "City, State",
        "property_type": "residential|commercial|industrial",
        "area_sqft": 2000,
        "budget": 300000,
        "timeline": {
            "earliest_start": "2023-06-01",
            "latest_completion": "2023-12-31"
        },
        "flexibility": "high|medium|low"
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Extract parameters
        location = data.get('location')
        property_type = data.get('property_type')
        area_sqft = data.get('area_sqft')
        budget = data.get('budget')
        timeline = data.get('timeline', {})
        flexibility = data.get('flexibility', 'medium')
        
        # Validate required parameters
        if not location or not property_type or not area_sqft or not budget:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters: location, property_type, area_sqft, and budget are required'
            }), 400
        
        # Get current material prices
        material_prices = get_material_prices()
        
        # Get construction cost estimate for standard quality
        cost_estimate = predict_construction_costs(
            location=location,
            property_type=property_type,
            area_sqft=float(area_sqft),
            quality_level='standard',
            stories=1,
            material_prices=material_prices
        )
        
        # Check if budget is sufficient
        if cost_estimate['total_cost'] > float(budget):
            return jsonify({
                'status': 'warning',
                'message': 'Budget is insufficient for the planned construction',
                'data': {
                    'estimated_cost': cost_estimate['total_cost'],
                    'budget': float(budget),
                    'shortfall': cost_estimate['total_cost'] - float(budget),
                    'recommendations': [
                        'Consider reducing the area',
                        'Choose a lower quality level',
                        'Wait for material prices to decrease',
                        'Increase your budget'
                    ]
                }
            })
        
        # Get optimal start date
        optimal_date = get_optimal_start_timing(
            location=location,
            area_sqft=float(area_sqft),
            timeline=timeline,
            flexibility=flexibility
        )
        
        # Get weather forecast
        weather_forecast = generate_weather_forecast(location, 12)  # Full year forecast
        
        # Estimate completion time
        completion_time_months = estimate_completion_time(float(area_sqft), property_type)
        completion_date = (
            datetime.strptime(optimal_date['start_date'], '%Y-%m-%d') + 
            timedelta(days=30 * completion_time_months)
        ).strftime('%Y-%m-%d')
        
        # Evaluate favorable construction windows
        construction_windows = identify_construction_windows(
            location=location,
            weather_forecast=weather_forecast,
            property_type=property_type,
            flexibility=flexibility
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'optimal_timing': {
                    'start_date': optimal_date['start_date'],
                    'estimated_completion': completion_date,
                    'duration_months': completion_time_months,
                    'confidence': optimal_date['confidence']
                },
                'cost_summary': {
                    'total_cost': cost_estimate['total_cost'],
                    'cost_per_sqft': cost_estimate['cost_per_sqft'],
                    'budget': float(budget),
                    'buffer': float(budget) - cost_estimate['total_cost']
                },
                'material_recommendations': {
                    'best_purchase_time': optimal_date['material_purchase_time'],
                    'current_prices': {k: v for k, v in material_prices.items() if k in ['lumber', 'concrete', 'steel']}
                },
                'construction_windows': construction_windows,
                'weather_considerations': filter_relevant_weather(weather_forecast, optimal_date['start_date'], completion_time_months)
            }
        })
    
    except Exception as e:
        logger.error(f"Error determining optimal construction timing: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to determine optimal construction timing: {str(e)}"
        }), 500

def get_optimal_start_date(location):
    """Determine optimal construction start date for a location"""
    import random
    
    # Get current date
    current_date = datetime.now()
    
    # Generate a random start date in the next 2-6 months
    months_ahead = random.randint(2, 6)
    optimal_date = current_date + timedelta(days=30 * months_ahead)
    
    return optimal_date.strftime('%Y-%m-%d')

def generate_weather_forecast(location, months):
    """Generate weather forecast for a location"""
    import random
    
    # Base temperatures for different regions
    region_bases = {
        'north': {'summer': 80, 'winter': 30, 'spring': 60, 'fall': 65},
        'south': {'summer': 95, 'winter': 50, 'spring': 75, 'fall': 80},
        'east': {'summer': 85, 'winter': 35, 'spring': 65, 'fall': 70},
        'west': {'summer': 90, 'winter': 45, 'spring': 70, 'fall': 75},
        'midwest': {'summer': 85, 'winter': 25, 'spring': 60, 'fall': 65}
    }
    
    # Determine region based on location
    region = 'midwest'  # Default
    if 'new york' in location.lower() or 'boston' in location.lower():
        region = 'east'
    elif 'florida' in location.lower() or 'texas' in location.lower():
        region = 'south'
    elif 'california' in location.lower() or 'oregon' in location.lower():
        region = 'west'
    elif 'illinois' in location.lower() or 'michigan' in location.lower():
        region = 'midwest'
    
    # Generate forecast for each month
    forecast = []
    current_date = datetime.now()
    
    for i in range(months):
        month_date = current_date + timedelta(days=30 * i)
        month = month_date.month
        
        # Determine season
        if 3 <= month <= 5:
            season = 'spring'
        elif 6 <= month <= 8:
            season = 'summer'
        elif 9 <= month <= 11:
            season = 'fall'
        else:
            season = 'winter'
        
        # Get base temperature for this region and season
        base_temp = region_bases[region][season]
        
        # Generate random variations
        avg_temp = base_temp + random.uniform(-5, 5)
        precipitation_days = round(random.uniform(5, 15))
        
        # More precipitation in spring, fewer in summer/fall
        if season == 'spring':
            precipitation_days += 3
        elif season in ['summer', 'fall']:
            precipitation_days -= 2
        
        # Calculate construction-favorable days (higher in summer, lower in winter)
        if season == 'summer':
            favorable_days = round(random.uniform(20, 28))
        elif season in ['spring', 'fall']:
            favorable_days = round(random.uniform(15, 25))
        else:  # winter
            favorable_days = round(random.uniform(8, 18))
        
        # Add to forecast
        forecast.append({
            'month': month_date.strftime('%Y-%m'),
            'avg_temp': round(avg_temp, 1),
            'precipitation_days': precipitation_days,
            'favorable_days': favorable_days,
            'season': season
        })
    
    return forecast

def estimate_completion_time(area_sqft, property_type):
    """Estimate construction completion time in months"""
    # Base time: 1 month per 1000 sqft for standard residential
    base_time = area_sqft / 1000
    
    # Adjust for property type
    if property_type == 'commercial':
        base_time *= 1.5  # Commercial takes 50% longer
    elif property_type == 'industrial':
        base_time *= 1.2  # Industrial takes 20% longer
    
    # Add buffer time
    buffer = max(1, base_time * 0.2)  # At least 1 month buffer
    
    return round(base_time + buffer, 1)

def get_optimal_start_timing(location, area_sqft, timeline, flexibility):
    """Determine optimal start timing based on various factors"""
    import random
    
    # Get weather forecast
    weather_forecast = generate_weather_forecast(location, 12)
    
    # Calculate best weather windows
    best_weather_scores = []
    for i in range(len(weather_forecast) - 3):  # Need at least 3 consecutive months
        # Calculate average favorable days over 3 months
        avg_favorable = sum(m['favorable_days'] for m in weather_forecast[i:i+3]) / 3
        best_weather_scores.append({
            'start_month': i,
            'score': avg_favorable,
            'start_date': (datetime.now() + timedelta(days=30 * i)).strftime('%Y-%m-%d')
        })
    
    # Sort by score descending
    best_weather_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # Apply timeline constraints if provided
    if timeline and 'earliest_start' in timeline and 'latest_completion' in timeline:
        earliest_start = datetime.strptime(timeline['earliest_start'], '%Y-%m-%d')
        latest_completion = datetime.strptime(timeline['latest_completion'], '%Y-%m-%d')
        
        # Filter based on timeline
        filtered_scores = []
        for score in best_weather_scores:
            start_date = datetime.strptime(score['start_date'], '%Y-%m-%d')
            completion_time = estimate_completion_time(area_sqft, 'residential')  # Default to residential
            completion_date = start_date + timedelta(days=30 * completion_time)
            
            if start_date >= earliest_start and completion_date <= latest_completion:
                filtered_scores.append(score)
        
        if filtered_scores:
            best_weather_scores = filtered_scores
    
    # Select based on flexibility
    if flexibility == 'low':
        # Very specific timing, take the absolute best
        selected_timing = best_weather_scores[0]
    elif flexibility == 'medium':
        # Some flexibility, choose from top 3
        selected_timing = random.choice(best_weather_scores[:3]) if len(best_weather_scores) >= 3 else best_weather_scores[0]
    else:  # high flexibility
        # Very flexible, choose from top 5
        selected_timing = random.choice(best_weather_scores[:5]) if len(best_weather_scores) >= 5 else best_weather_scores[0]
    
    # Add material purchase recommendation (1-2 months before construction)
    material_purchase_date = (
        datetime.strptime(selected_timing['start_date'], '%Y-%m-%d') - 
        timedelta(days=random.randint(30, 60))
    )
    
    # Ensure material purchase date is not in the past
    current_date = datetime.now()
    if material_purchase_date < current_date:
        material_purchase_date = current_date + timedelta(days=15)
    
    return {
        'start_date': selected_timing['start_date'],
        'start_month_index': selected_timing['start_month'],
        'weather_score': selected_timing['score'],
        'confidence': random.uniform(0.75, 0.95),
        'material_purchase_time': material_purchase_date.strftime('%Y-%m-%d')
    }

def identify_construction_windows(location, weather_forecast, property_type, flexibility):
    """Identify favorable construction windows based on weather"""
    # Calculate scores for each month
    scores = []
    
    for i, month in enumerate(weather_forecast):
        # Base score is the number of favorable days
        base_score = month['favorable_days']
        
        # Adjust score based on temperature (penalize extremes)
        if month['avg_temp'] > 90:
            temp_factor = 0.8  # Too hot
        elif month['avg_temp'] < 40:
            temp_factor = 0.7  # Too cold
        else:
            temp_factor = 1.0  # Good temperature
        
        # Adjust score based on precipitation (penalize high precipitation)
        if month['precipitation_days'] > 15:
            precip_factor = 0.7  # Very rainy
        elif month['precipitation_days'] > 10:
            precip_factor = 0.85  # Moderately rainy
        else:
            precip_factor = 1.0  # Low precipitation
        
        # Calculate final score
        final_score = base_score * temp_factor * precip_factor
        
        # Add to scores
        scores.append({
            'month': month['month'],
            'score': round(final_score, 1),
            'favorable_days': month['favorable_days'],
            'rating': 'Excellent' if final_score > 22 else 'Good' if final_score > 18 else 'Average' if final_score > 14 else 'Poor'
        })
    
    # Determine construction windows based on flexibility
    if flexibility == 'low':
        # Need consecutive high-scoring months
        windows = []
        current_window = []
        
        for i, score in enumerate(scores):
            if score['score'] > 18:  # Good or Excellent
                if not current_window:
                    current_window = [score]
                else:
                    current_window.append(score)
                    
                    # If we have 3 consecutive good months, that's a window
                    if len(current_window) >= 3:
                        windows.append({
                            'start': current_window[0]['month'],
                            'end': current_window[-1]['month'],
                            'duration': len(current_window),
                            'average_score': round(sum(s['score'] for s in current_window) / len(current_window), 1),
                            'rating': 'Excellent' if sum(s['score'] for s in current_window) / len(current_window) > 22 else 'Good'
                        })
            else:
                current_window = []
        
        return windows
    
    else:  # medium or high flexibility
        # Group months by season and calculate average scores
        seasons = []
        season_months = []
        
        for i, score in enumerate(scores):
            month_date = datetime.strptime(score['month'], '%Y-%m')
            month = month_date.month
            
            # Determine season
            if 3 <= month <= 5:
                season = 'Spring'
            elif 6 <= month <= 8:
                season = 'Summer'
            elif 9 <= month <= 11:
                season = 'Fall'
            else:
                season = 'Winter'
            
            # Check if we're starting a new season
            if not season_months or season_months[-1]['season'] != season:
                season_months.append({
                    'season': season,
                    'months': [score],
                    'start': score['month']
                })
            else:
                season_months[-1]['months'].append(score)
                season_months[-1]['end'] = score['month']
        
        # Calculate average scores for each season
        for season in season_months:
            avg_score = sum(m['score'] for m in season['months']) / len(season['months'])
            season['average_score'] = round(avg_score, 1)
            season['rating'] = 'Excellent' if avg_score > 22 else 'Good' if avg_score > 18 else 'Average' if avg_score > 14 else 'Poor'
        
        return season_months

def filter_relevant_weather(weather_forecast, start_date, duration_months):
    """Filter weather forecast to only include relevant months for construction"""
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    start_month = start_date_obj.strftime('%Y-%m')
    
    # Find the index of the start month
    start_index = -1
    for i, month in enumerate(weather_forecast):
        if month['month'] == start_month:
            start_index = i
            break
    
    if start_index == -1:
        # If start month not found, return entire forecast
        return weather_forecast
    
    # Return forecast for the construction period
    end_index = min(start_index + int(duration_months), len(weather_forecast))
    return weather_forecast[start_index:end_index]