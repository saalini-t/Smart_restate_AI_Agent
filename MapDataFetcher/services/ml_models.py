import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from models import EconomicIndicator

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def forecast_market_direction(interest_rates, inflation_data, gdp_data):
    """
    Forecast real estate market direction (boom/dip) based on economic indicators
    
    Parameters:
    - interest_rates: List of EconomicIndicator objects
    - inflation_data: List of EconomicIndicator objects
    - gdp_data: List of EconomicIndicator objects
    
    Returns:
    - Dictionary with forecast data
    """
    logger.info("Forecasting market direction")
    
    try:
        # Convert indicators to pandas DataFrames
        interest_df = indicators_to_dataframe(interest_rates)
        inflation_df = indicators_to_dataframe(inflation_data)
        gdp_df = indicators_to_dataframe(gdp_data)
        
        # Analyze trends
        interest_trend = analyze_trend(interest_df['value']) if not interest_df.empty else 'neutral'
        inflation_trend = analyze_trend(inflation_df['value']) if not inflation_df.empty else 'neutral'
        gdp_trend = analyze_trend(gdp_df['value']) if not gdp_df.empty else 'neutral'
        
        # Market scoring logic (simplified)
        market_score = 0
        
        # Interest rate impact (inversely related to market growth)
        if interest_trend == 'decreasing':
            market_score += 2
        elif interest_trend == 'neutral':
            market_score += 1
        else:  # increasing
            market_score -= 1
        
        # Inflation impact (moderate inflation is positive, high is negative)
        if inflation_trend == 'increasing' and inflation_df['value'].mean() > 4.0:
            market_score -= 1
        elif inflation_trend == 'stable' or (inflation_trend == 'increasing' and inflation_df['value'].mean() <= 4.0):
            market_score += 1
        
        # GDP impact (directly related to market growth)
        if gdp_trend == 'increasing':
            market_score += 2
        elif gdp_trend == 'neutral':
            market_score += 0
        else:  # decreasing
            market_score -= 2
        
        # Market direction determination
        market_direction = 'neutral'
        if market_score >= 3:
            market_direction = 'strong growth'
        elif market_score >= 1:
            market_direction = 'moderate growth'
        elif market_score <= -3:
            market_direction = 'sharp decline'
        elif market_score <= -1:
            market_direction = 'moderate decline'
        
        # Calculate confidence level (0.6 - 0.95)
        confidence = min(0.6 + abs(market_score) * 0.05, 0.95)
        
        # Generate 12-month forecast points
        forecast_points = generate_forecast_points(12, market_direction)
        
        # Return forecast data
        return {
            'market_direction': market_direction,
            'confidence': round(confidence, 2),
            'forecast_points': forecast_points,
            'factors': {
                'interest_rates': {
                    'trend': interest_trend,
                    'impact': 'positive' if interest_trend == 'decreasing' else 'negative' if interest_trend == 'increasing' else 'neutral'
                },
                'inflation': {
                    'trend': inflation_trend,
                    'impact': 'negative' if inflation_trend == 'increasing' and inflation_df['value'].mean() > 4.0 else 'neutral'
                },
                'gdp': {
                    'trend': gdp_trend,
                    'impact': 'positive' if gdp_trend == 'increasing' else 'negative' if gdp_trend == 'decreasing' else 'neutral'
                }
            }
        }
    except Exception as e:
        logger.error(f"Error in forecast_market_direction: {str(e)}")
        # Return a default forecast with error information
        return {
            'market_direction': 'uncertain',
            'confidence': 0.5,
            'forecast_points': generate_forecast_points(12, 'neutral'),
            'error': str(e)
        }

def indicators_to_dataframe(indicators):
    """Convert list of EconomicIndicator objects to pandas DataFrame"""
    if not indicators:
        return pd.DataFrame(columns=['date', 'value'])
    
    data = []
    for indicator in indicators:
        data.append({
            'date': indicator.date,
            'value': indicator.value,
            'forecast': indicator.forecast
        })
    
    df = pd.DataFrame(data)
    df.sort_values('date', inplace=True)
    return df

def analyze_trend(series):
    """Analyze trend in a time series"""
    if len(series) < 2:
        return 'neutral'
    
    try:
        # Calculate linear regression on the last 6 points or all points if fewer
        n_points = min(6, len(series))
        X = np.arange(n_points).reshape(-1, 1)
        y = series.tail(n_points).values
        
        model = LinearRegression()
        model.fit(X, y)
        
        slope = model.coef_[0]
        
        # Determine trend based on slope
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    except Exception as e:
        logger.error(f"Error analyzing trend: {str(e)}")
        return 'neutral'

def generate_forecast_points(months, trend):
    """Generate forecast points for the next n months"""
    forecast_points = []
    start_index = 100  # Arbitrary starting index
    
    # Set growth factors based on trend
    if trend == 'strong growth':
        monthly_change = random.uniform(0.8, 1.5)
        volatility = 0.3
    elif trend == 'moderate growth':
        monthly_change = random.uniform(0.3, 0.8)
        volatility = 0.2
    elif trend == 'neutral':
        monthly_change = random.uniform(-0.2, 0.3)
        volatility = 0.2
    elif trend == 'moderate decline':
        monthly_change = random.uniform(-0.8, -0.3)
        volatility = 0.3
    elif trend == 'sharp decline':
        monthly_change = random.uniform(-1.5, -0.8)
        volatility = 0.4
    else:
        monthly_change = 0
        volatility = 0.1
    
    for i in range(months):
        month_date = datetime.now() + timedelta(days=30 * i)
        # Add some randomness to the change
        change = monthly_change + random.uniform(-volatility, volatility)
        index_value = start_index * (1 + change/100) ** i
        
        forecast_points.append({
            'date': month_date.strftime('%Y-%m'),
            'index': round(index_value, 2),
            'change_pct': round(change, 2)
        })
    
    return forecast_points

def predict_property_prices(location, property_type, area_sqft, bedrooms=None, bathrooms=None, year_built=None, forecast_period='1y'):
    """
    Predict property prices for a given location and property type
    
    Parameters:
    - location: str (City, State)
    - property_type: str (residential, commercial, land)
    - area_sqft: float
    - bedrooms: int (optional)
    - bathrooms: int (optional)
    - year_built: int (optional)
    - forecast_period: str (6m, 1y, 5y)
    
    Returns:
    - Dictionary with price predictions and forecast
    """
    logger.info(f"Predicting property prices for {location}, {property_type}")
    
    try:
        # Estimate base price
        base_price_per_sqft = estimate_base_price(location, property_type)
        
        # Calculate current estimated price
        current_price = base_price_per_sqft * area_sqft
        
        # Apply adjustments for residential properties
        if property_type == 'residential' and bedrooms and bathrooms:
            # Adjust for number of bedrooms
            if bedrooms <= 1:
                bedroom_factor = 0.9
            elif bedrooms == 2:
                bedroom_factor = 1.0
            elif bedrooms == 3:
                bedroom_factor = 1.1
            elif bedrooms == 4:
                bedroom_factor = 1.2
            else:
                bedroom_factor = 1.25
            
            # Adjust for number of bathrooms
            if bathrooms <= 1:
                bathroom_factor = 0.95
            elif bathrooms == 2:
                bathroom_factor = 1.05
            else:
                bathroom_factor = 1.1
            
            current_price *= bedroom_factor * bathroom_factor
        
        # Adjust for year built if available
        if year_built:
            current_year = datetime.now().year
            age = current_year - year_built
            
            if age <= 2:
                age_factor = 1.2  # New construction premium
            elif age <= 10:
                age_factor = 1.1
            elif age <= 20:
                age_factor = 1.0
            elif age <= 40:
                age_factor = 0.9
            else:
                age_factor = 0.85
            
            current_price *= age_factor
        
        # Determine forecast period in months
        if forecast_period == '6m':
            forecast_months = 6
        elif forecast_period == '1y':
            forecast_months = 12
        elif forecast_period == '5y':
            forecast_months = 60
        else:
            forecast_months = 12  # Default to 1 year
        
        # Generate price forecast
        forecast = forecast_property_price(location, property_type, current_price, forecast_months)
        
        # Market assessment (undervalued or overvalued)
        market_assessment = assess_market_value(location, property_type, current_price)
        
        # Calculate confidence score (0.6 - 0.9)
        if bedrooms and bathrooms and year_built:
            confidence = 0.85  # More information means higher confidence
        elif bedrooms and bathrooms:
            confidence = 0.8
        elif year_built:
            confidence = 0.75
        else:
            confidence = 0.7
        
        # Return prediction data
        return {
            'current_price': round(current_price, 2),
            'price_per_sqft': round(base_price_per_sqft, 2),
            'confidence': round(confidence, 2),
            'market_assessment': market_assessment,
            'forecast': forecast
        }
    except Exception as e:
        logger.error(f"Error in predict_property_prices: {str(e)}")
        # Return error information
        return {
            'error': str(e),
            'current_price': None,
            'confidence': 0.5
        }

def estimate_base_price(location, property_type):
    """Estimate base price per sqft based on location and property type"""
    # Base prices for sample locations
    base_prices = {
        'New York': {'residential': 750, 'commercial': 950, 'land': 450},
        'Los Angeles': {'residential': 650, 'commercial': 850, 'land': 400},
        'Chicago': {'residential': 350, 'commercial': 500, 'land': 200},
        'Houston': {'residential': 200, 'commercial': 350, 'land': 100},
        'Phoenix': {'residential': 180, 'commercial': 300, 'land': 90},
        'Philadelphia': {'residential': 225, 'commercial': 375, 'land': 125},
        'San Antonio': {'residential': 160, 'commercial': 280, 'land': 80},
        'San Diego': {'residential': 570, 'commercial': 780, 'land': 350},
        'Dallas': {'residential': 210, 'commercial': 360, 'land': 110},
        'San Francisco': {'residential': 1050, 'commercial': 1200, 'land': 600}
    }
    
    # Extract city from location (assumes 'City, State' format)
    city = location.split(',')[0].strip()
    
    # Get base price for the location, or use default if not found
    if city in base_prices:
        return base_prices[city].get(property_type, 300)
    else:
        # Default base prices if location not found
        default_prices = {'residential': 300, 'commercial': 400, 'land': 150}
        return default_prices.get(property_type, 300)

def forecast_property_price(location, property_type, current_price, months):
    """Generate property price forecast for specified number of months"""
    # Get annual growth rate for the location and property type
    annual_growth_rate = estimate_growth_rate(location, property_type)
    
    # Convert annual growth rate to monthly
    monthly_growth_rate = (1 + annual_growth_rate) ** (1/12) - 1
    
    # Generate forecast points
    forecast = []
    price = current_price
    
    for i in range(months):
        month_date = datetime.now() + timedelta(days=30 * i)
        
        # Add some randomness to monthly growth
        month_growth = monthly_growth_rate + random.uniform(-0.005, 0.005)
        price = price * (1 + month_growth)
        
        # Record forecast point
        forecast.append({
            'date': month_date.strftime('%Y-%m'),
            'price': round(price, 2),
            'change_pct': round(month_growth * 100, 2)
        })
    
    return forecast

def estimate_growth_rate(location, property_type):
    """Estimate annual growth rate based on location and property type"""
    # Sample growth rates for different locations
    growth_rates = {
        'New York': {'residential': 0.04, 'commercial': 0.035, 'land': 0.045},
        'Los Angeles': {'residential': 0.045, 'commercial': 0.04, 'land': 0.05},
        'Chicago': {'residential': 0.025, 'commercial': 0.02, 'land': 0.03},
        'Houston': {'residential': 0.035, 'commercial': 0.03, 'land': 0.04},
        'Phoenix': {'residential': 0.05, 'commercial': 0.045, 'land': 0.055},
        'Philadelphia': {'residential': 0.025, 'commercial': 0.02, 'land': 0.03},
        'San Antonio': {'residential': 0.04, 'commercial': 0.035, 'land': 0.045},
        'San Diego': {'residential': 0.045, 'commercial': 0.04, 'land': 0.05},
        'Dallas': {'residential': 0.04, 'commercial': 0.035, 'land': 0.045},
        'San Francisco': {'residential': 0.035, 'commercial': 0.03, 'land': 0.04}
    }
    
    # Extract city from location
    city = location.split(',')[0].strip()
    
    # Get growth rate for the location, or use default if not found
    if city in growth_rates:
        return growth_rates[city].get(property_type, 0.03)
    else:
        # Default growth rates if location not found
        default_rates = {'residential': 0.03, 'commercial': 0.025, 'land': 0.035}
        return default_rates.get(property_type, 0.03)

def assess_market_value(location, property_type, estimated_price):
    """Assess if property is undervalued or overvalued"""
    # Simplified assessment using random values
    assessment = random.choice(['undervalued', 'fairly valued', 'overvalued'])
    
    # Calculate percentage
    if assessment == 'undervalued':
        percentage = random.uniform(5, 15)
    elif assessment == 'overvalued':
        percentage = random.uniform(5, 15)
    else:
        percentage = random.uniform(0, 3)
    
    return {
        'assessment': assessment,
        'percentage': round(percentage, 1)
    }

def predict_investment_timing(location, property_type, investment_goal, timeframe, 
                             interest_rates, inflation_data, budget=None, roi_expectation=None):
    """
    Predict optimal investment timing based on market conditions and goals
    
    Parameters:
    - location: str (City, State)
    - property_type: str (residential, commercial, land)
    - investment_goal: str (flip, rent, hold)
    - timeframe: int (years)
    - interest_rates: List of EconomicIndicator objects
    - inflation_data: List of EconomicIndicator objects
    - budget: float (optional)
    - roi_expectation: float (optional, expected ROI percentage)
    
    Returns:
    - Dictionary with investment timing recommendation
    """
    logger.info(f"Predicting investment timing for {location}, {property_type}, goal: {investment_goal}")
    
    try:
        # Convert timeframe to months
        months = timeframe * 12
        
        # Analyze interest rate and inflation trends
        interest_df = indicators_to_dataframe(interest_rates)
        inflation_df = indicators_to_dataframe(inflation_data)
        
        interest_trend = analyze_trend(interest_df['value']) if not interest_df.empty else 'neutral'
        inflation_trend = analyze_trend(inflation_df['value']) if not inflation_df.empty else 'neutral'
        
        # Decide on basic recommendation based on trends and investment goal
        if investment_goal == 'flip':
            if interest_trend == 'decreasing' and inflation_trend != 'increasing':
                recommendation = 'buy'
                confidence = 0.85
                optimal_time = '1-3 months'
            elif interest_trend == 'increasing' and inflation_trend == 'increasing':
                recommendation = 'wait'
                confidence = 0.8
                optimal_time = '6-12 months'
            else:
                recommendation = 'neutral'
                confidence = 0.7
                optimal_time = '3-6 months'
        elif investment_goal == 'rent':
            if interest_trend != 'increasing':
                recommendation = 'buy'
                confidence = 0.8
                optimal_time = '1-3 months'
            else:
                recommendation = 'neutral'
                confidence = 0.7
                optimal_time = '3-6 months'
        else:  # hold
            if interest_trend == 'decreasing' or inflation_trend == 'increasing':
                recommendation = 'buy'
                confidence = 0.75
                optimal_time = '1-6 months'
            else:
                recommendation = 'neutral'
                confidence = 0.65
                optimal_time = '6-12 months'
        
        # Estimate property value
        base_price_per_sqft = estimate_base_price(location, property_type)
        average_size = {'residential': 2000, 'commercial': 5000, 'land': 10000}
        current_price = base_price_per_sqft * average_size.get(property_type, 2000)
        
        # Estimate ROI
        roi_estimate = calculate_expected_roi(location, property_type, investment_goal, timeframe, current_price)
        
        # Adjust recommendation based on budget if provided
        if budget and budget < current_price:
            if recommendation == 'buy':
                recommendation = 'save'
                optimal_time = f"{round((current_price - budget) / (budget * 0.2))} months" # Assuming 20% savings rate
        
        # Adjust recommendation based on ROI expectation if provided
        if roi_expectation and roi_estimate < roi_expectation:
            if recommendation == 'buy':
                recommendation = 'research alternatives'
                confidence -= 0.1
        
        # Generate price forecast for the property
        price_forecast = forecast_property_price(location, property_type, current_price, min(months, 24))
        
        # Return the recommendation data
        return {
            'recommendation': recommendation,
            'confidence': round(confidence, 2),
            'optimal_time': optimal_time,
            'price_forecast': price_forecast,
            'roi_estimate': round(roi_estimate, 2),
            'factors': {
                'interest_rates': interest_trend,
                'inflation': inflation_trend,
                'market_direction': 'favorable' if recommendation == 'buy' else 'uncertain' if recommendation == 'neutral' else 'unfavorable'
            }
        }
    except Exception as e:
        logger.error(f"Error in predict_investment_timing: {str(e)}")
        # Return error information
        return {
            'recommendation': 'uncertain',
            'confidence': 0.5,
            'error': str(e)
        }

def calculate_expected_roi(location, property_type, investment_goal, timeframe, current_price):
    """Calculate expected ROI based on investment parameters"""
    # Estimate annual growth rate
    annual_growth_rate = estimate_growth_rate(location, property_type)
    
    # Calculate ROI differently based on investment goal
    if investment_goal == 'flip':
        # For flipping, consider renovation costs and shorter timeframe
        renovation_cost = current_price * 0.15  # Assume 15% renovation cost
        selling_price = current_price * (1 + annual_growth_rate) * 1.2  # Sale premium after renovation
        
        # Calculate ROI
        investment = current_price + renovation_cost
        profit = selling_price - investment
        roi = (profit / investment) * 100
        
    elif investment_goal == 'rent':
        # For renting, calculate ROI based on rental income and property appreciation
        monthly_rent = estimate_monthly_rent(location, property_type, current_price)
        annual_rental_income = monthly_rent * 12
        
        # Assume operating expenses (30% of rental income)
        annual_expenses = annual_rental_income * 0.3
        
        # Calculate net income over the timeframe
        net_annual_income = annual_rental_income - annual_expenses
        total_rental_income = net_annual_income * timeframe
        
        # Calculate property appreciation
        future_value = current_price * (1 + annual_growth_rate) ** timeframe
        appreciation = future_value - current_price
        
        # Calculate ROI (cash flow + appreciation)
        roi = ((total_rental_income + appreciation) / current_price) * 100
        
    else:  # hold
        # For holding, calculate ROI based on property appreciation only
        future_value = current_price * (1 + annual_growth_rate) ** timeframe
        appreciation = future_value - current_price
        
        # Calculate ROI
        roi = (appreciation / current_price) * 100
    
    # Add some randomness to the ROI
    roi = roi * random.uniform(0.9, 1.1)
    
    return roi

def estimate_monthly_rent(location, property_type, property_value):
    """Estimate monthly rent based on property value and location"""
    # Simplified rent calculation using price-to-rent ratios
    price_to_rent_ratios = {
        'New York': {'residential': 20, 'commercial': 12},
        'Los Angeles': {'residential': 22, 'commercial': 13},
        'Chicago': {'residential': 16, 'commercial': 10},
        'Houston': {'residential': 14, 'commercial': 9},
        'Phoenix': {'residential': 15, 'commercial': 10},
        'Philadelphia': {'residential': 15, 'commercial': 10},
        'San Antonio': {'residential': 14, 'commercial': 9},
        'San Diego': {'residential': 20, 'commercial': 12},
        'Dallas': {'residential': 15, 'commercial': 10},
        'San Francisco': {'residential': 25, 'commercial': 14}
    }
    
    # Extract city from location
    city = location.split(',')[0].strip()
    
    # Get price-to-rent ratio for the location, or use default if not found
    if city in price_to_rent_ratios and property_type in price_to_rent_ratios[city]:
        ratio = price_to_rent_ratios[city][property_type]
    else:
        # Default ratios if location or property type not found
        default_ratios = {'residential': 18, 'commercial': 11, 'land': 40}
        ratio = default_ratios.get(property_type, 18)
    
    # Calculate monthly rent (property value / annual price-to-rent ratio * 12)
    monthly_rent = property_value / (ratio * 12)
    
    return monthly_rent

def predict_construction_costs(location, property_type, area_sqft, quality_level, stories, material_prices):
    """
    Predict construction costs based on location, property type, and specifications
    
    Parameters:
    - location: str (City, State)
    - property_type: str (residential, commercial, industrial)
    - area_sqft: float
    - quality_level: str (basic, standard, premium)
    - stories: int
    - material_prices: dict with current material prices
    
    Returns:
    - Dictionary with cost estimates
    """
    logger.info(f"Estimating construction costs for {location}, {property_type}")
    
    try:
        # Estimate base construction cost per sqft
        base_cost = estimate_construction_base_cost(location, property_type, quality_level)
        
        # Adjust for multiple stories
        if stories > 1:
            story_factor = 1 + (stories - 1) * 0.05
        else:
            story_factor = 1
        
        # Calculate basic cost
        basic_cost = base_cost * area_sqft * story_factor
        
        # Calculate detailed material costs
        materials_breakdown = calculate_material_costs(property_type, area_sqft, quality_level, material_prices)
        
        # Labor cost (typically 35-40% of total cost)
        labor_cost = basic_cost * 0.4
        
        # Soft costs (permits, architectural, engineering, etc.) - typically 15-20% of construction cost
        soft_costs = basic_cost * 0.18
        
        # Contingency (5-10% of total cost)
        contingency = basic_cost * 0.08
        
        # Calculate total cost
        total_cost = basic_cost + soft_costs + contingency
        
        # Return cost breakdown
        return {
            'total_cost': round(total_cost, 2),
            'cost_per_sqft': round(total_cost / area_sqft, 2),
            'breakdown': {
                'materials': round(basic_cost * 0.6, 2),
                'labor': round(labor_cost, 2),
                'soft_costs': round(soft_costs, 2),
                'contingency': round(contingency, 2)
            },
            'materials_breakdown': materials_breakdown,
            'time_estimate': f"{round(area_sqft/1000) + 2}-{round(area_sqft/800) + 4} months",
            'confidence': 0.85
        }
    except Exception as e:
        logger.error(f"Error in predict_construction_costs: {str(e)}")
        # Return error information
        return {
            'error': str(e),
            'total_cost': None,
            'confidence': 0.5
        }

def estimate_construction_base_cost(location, property_type, quality_level):
    """Estimate base construction cost per sqft based on location, type, and quality"""
    # Base costs for different property types and quality levels
    base_costs = {
        'residential': {'basic': 125, 'standard': 175, 'premium': 300},
        'commercial': {'basic': 150, 'standard': 200, 'premium': 350},
        'industrial': {'basic': 100, 'standard': 150, 'premium': 250}
    }
    
    # Location factors (cost multipliers for different cities)
    location_factors = {
        'New York': 1.5,
        'Los Angeles': 1.35,
        'Chicago': 1.2,
        'Houston': 0.95,
        'Phoenix': 0.9,
        'Philadelphia': 1.15,
        'San Antonio': 0.9,
        'San Diego': 1.25,
        'Dallas': 0.95,
        'San Francisco': 1.6
    }
    
    # Get base cost for property type and quality level
    base_cost = base_costs.get(property_type, {}).get(quality_level, 175)
    
    # Apply location factor
    city = location.split(',')[0].strip()
    location_factor = location_factors.get(city, 1.0)
    
    return base_cost * location_factor

def calculate_material_costs(property_type, area_sqft, quality_level, material_prices):
    """Calculate detailed material costs breakdown"""
    # Material quantity requirements per sqft
    material_requirements = {
        'lumber': 0.5,  # board feet per sqft
        'concrete': 0.03,  # cubic yards per sqft
        'steel': 0.001,  # tons per sqft
        'insulation': 1.0,  # sqft per sqft
        'drywall': 1.0  # sqft per sqft
    }
    
    # Quality level adjustments
    quality_factors = {
        'basic': 0.8,
        'standard': 1.0,
        'premium': 1.4
    }
    
    quality_factor = quality_factors.get(quality_level, 1.0)
    
    # Calculate materials
    materials_breakdown = {}
    for material, requirement in material_requirements.items():
        quantity = requirement * area_sqft * quality_factor
        unit_price = material_prices.get(material, 1.0)  # Default to 1.0 if price not provided
        cost = quantity * unit_price
        
        materials_breakdown[material] = {
            'quantity': round(quantity, 2),
            'unit_price': round(unit_price, 2),
            'cost': round(cost, 2)
        }
    
    return materials_breakdown

def calculate_investment_roi(location, property_type, purchase_price, investment_goal, timeframe, 
                            additional_investment=0, expected_rent=0, expected_expenses=0):
    """
    Calculate detailed ROI for an investment based on various parameters
    
    Args:
        location (str): Property location (city, state)
        property_type (str): Type of property (residential, commercial, land)
        purchase_price (float): Property purchase price
        investment_goal (str): Investment strategy (flip, rent, hold)
        timeframe (int): Investment timeframe in years
        additional_investment (float, optional): Renovation or improvement costs
        expected_rent (float, optional): Monthly rental income for rental properties
        expected_expenses (float, optional): Monthly expenses for rental properties
        
    Returns:
        dict: Dictionary with ROI calculation results
    """
    total_investment = purchase_price + additional_investment
    
    # Calculate property value appreciation over time
    # Get annual appreciation rate estimate for the location and property type
    appreciation_rate = estimate_growth_rate(location, property_type)
    future_value = purchase_price * ((1 + appreciation_rate) ** timeframe)
    appreciation_gain = future_value - purchase_price
    
    # Strategy-specific calculations
    if investment_goal == 'flip':
        # For flipping, calculate ROI based on quick sale after improvements
        # Typically assumes 3-9 months holding period
        holding_period = min(1, timeframe)  # Cap at 1 year if timeframe is longer
        
        # Estimate transaction costs (closing costs, agent fees, etc.)
        transaction_costs = purchase_price * 0.05 + future_value * 0.06
        
        # Estimate holding costs (taxes, insurance, utilities, financing)
        monthly_holding_cost = purchase_price * 0.01 / 12  # Roughly 1% of purchase price annually
        holding_costs = monthly_holding_cost * (holding_period * 12)
        
        # Calculate profit
        profit = future_value - purchase_price - additional_investment - transaction_costs - holding_costs
        
        # Calculate ROI
        roi_percentage = (profit / total_investment) * 100
        
        # Estimate breakeven time (months)
        if profit <= 0:
            breakeven_months = timeframe * 12 * 2  # If no profit, return double the timeframe as a penalty
        else:
            breakeven_months = 0  # For flipping, breakeven is at the moment of sale
        
        return {
            'roi_percentage': roi_percentage,
            'breakeven_months': breakeven_months,
            'monthly_cash_flow': 0,  # No monthly cash flow for flipping
            'total_return': profit,
            'future_value': future_value,
            'total_costs': transaction_costs + holding_costs + additional_investment,
            'strategy': 'flip',
            'appreciation_rate': appreciation_rate * 100,
            'timeframe_years': timeframe,
            'return_drivers': {
                'appreciation': appreciation_gain,
                'improvements': additional_investment * 0.3,  # Assume 30% return on improvements
                'market_timing': future_value * 0.05  # Simplified market timing impact
            }
        }
        
    elif investment_goal == 'rent':
        # For rental properties, calculate cash flow and ROI including rental income
        
        # If expected rent not provided, estimate it
        if expected_rent <= 0:
            expected_rent = estimate_monthly_rent(location, property_type, purchase_price)
            
        # If expected expenses not provided, estimate them
        if expected_expenses <= 0:
            # Typical expenses include property management, maintenance, vacancy, taxes, insurance
            expected_expenses = expected_rent * 0.4  # Roughly 40% of rent goes to expenses
            
        # Calculate monthly cash flow
        monthly_cash_flow = expected_rent - expected_expenses
        annual_cash_flow = monthly_cash_flow * 12
        
        # Calculate total rental income over the investment period
        total_rental_income = annual_cash_flow * timeframe
        
        # Calculate total return (cash flow + appreciation)
        total_return = total_rental_income + appreciation_gain
        
        # Calculate ROI
        roi_percentage = (total_return / total_investment) * 100
        annual_roi = roi_percentage / timeframe
        
        # Estimate breakeven time (months)
        if monthly_cash_flow <= 0:
            breakeven_months = float('inf')  # Never breaks even with negative cash flow
        else:
            breakeven_months = total_investment / monthly_cash_flow
            
        return {
            'roi_percentage': roi_percentage,
            'annual_roi': annual_roi,
            'breakeven_months': breakeven_months,
            'monthly_cash_flow': monthly_cash_flow,
            'annual_cash_flow': annual_cash_flow,
            'total_return': total_return,
            'future_value': future_value,
            'total_rental_income': total_rental_income,
            'strategy': 'rent',
            'appreciation_rate': appreciation_rate * 100,
            'cap_rate': (annual_cash_flow / purchase_price) * 100,  # Capitalization rate
            'cash_on_cash_return': (annual_cash_flow / total_investment) * 100,
            'timeframe_years': timeframe,
            'return_drivers': {
                'rental_income': total_rental_income,
                'appreciation': appreciation_gain
            }
        }
        
    else:  # 'hold' strategy
        # For buy and hold, focus primarily on long-term appreciation
        
        # Estimate property tax and insurance costs
        annual_holding_costs = purchase_price * 0.015  # Roughly 1.5% of purchase price
        total_holding_costs = annual_holding_costs * timeframe
        
        # Calculate profit
        profit = future_value - purchase_price - total_holding_costs
        
        # Calculate ROI
        roi_percentage = (profit / total_investment) * 100
        annual_roi = roi_percentage / timeframe
        
        # Breakeven calculation
        value_increase_per_year = appreciation_gain / timeframe
        annual_costs = annual_holding_costs
        
        if value_increase_per_year <= annual_costs:
            breakeven_months = float('inf')  # Never breaks even if appreciation doesn't exceed costs
        else:
            years_to_breakeven = total_investment / (value_increase_per_year - annual_costs)
            breakeven_months = years_to_breakeven * 12
            
        return {
            'roi_percentage': roi_percentage,
            'annual_roi': annual_roi,
            'breakeven_months': breakeven_months,
            'monthly_cash_flow': -annual_holding_costs / 12,  # Negative cash flow from holding costs
            'total_return': profit,
            'future_value': future_value,
            'total_holding_costs': total_holding_costs,
            'strategy': 'hold',
            'appreciation_rate': appreciation_rate * 100,
            'timeframe_years': timeframe,
            'return_drivers': {
                'appreciation': appreciation_gain,
                'market_timing': future_value * 0.1  # Simplified market timing impact (higher for long-term)
            }
        }