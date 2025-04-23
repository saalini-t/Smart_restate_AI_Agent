import os
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

from models import EconomicIndicator

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API key from environment
API_KEY = os.environ.get('TRADING_ECONOMICS_API_KEY')

def get_trading_economics_data(category, country, start_date=None, end_date=None):
    """
    Get data from Trading Economics API
    
    Parameters:
    - category: str (e.g., 'interest-rate', 'inflation-rate', 'gdp-growth')
    - country: str (e.g., 'United States', 'Canada')
    - start_date: datetime (optional)
    - end_date: datetime (optional)
    
    Returns:
    - List of data points from Trading Economics API
    """
    logger.info(f"Fetching Trading Economics data for {category} in {country}")
    
    if not API_KEY:
        logger.warning("Trading Economics API key not found in environment variables")
        # Return sample data for development
        return generate_sample_economic_data(category, country, start_date, end_date)
    
    try:
        # Convert country name to format used by Trading Economics API
        country_code = get_country_code(country)
        
        # Format dates for API call
        start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None
        
        # Base URL for Trading Economics API
        base_url = "https://api.tradingeconomics.com/historical/"
        
        # Construct the API endpoint URL
        endpoint = f"{base_url}{category}/{country_code}"
        
        # Add date parameters if provided
        params = {
            'c': API_KEY
        }
        
        if start_date_str:
            params['d1'] = start_date_str
        if end_date_str:
            params['d2'] = end_date_str
        
        # Make API request
        response = requests.get(endpoint, params=params)
        
        # Check if request was successful
        if response.status_code == 200:
            # Process and return the data
            data = response.json()
            return data
        else:
            logger.error(f"Error fetching data from Trading Economics API: {response.status_code} - {response.text}")
            # Return sample data for development
            return generate_sample_economic_data(category, country, start_date, end_date)
    
    except Exception as e:
        logger.error(f"Exception when calling Trading Economics API: {str(e)}")
        # Return sample data for development
        return generate_sample_economic_data(category, country, start_date, end_date)

def get_interest_rates(country, start_date=None, end_date=None):
    """
    Get interest rate data from Trading Economics API
    
    Parameters:
    - country: str (e.g., 'United States', 'Canada')
    - start_date: datetime (optional)
    - end_date: datetime (optional)
    
    Returns:
    - List of EconomicIndicator objects for interest rates
    """
    data = get_trading_economics_data('interest-rate', country, start_date, end_date)
    
    # Convert data to EconomicIndicator objects
    indicators = []
    for item in data:
        try:
            # Extract date and value from API response
            date_str = item.get('Date', '')
            value = item.get('Value', 0.0)
            
            # Parse date string to datetime object
            date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
            
            # Create EconomicIndicator object
            indicator = EconomicIndicator(
                indicator_type='interest-rate',
                value=float(value),
                date=date,
                country=country,
                forecast=None,  # API might provide forecast data
                source='Trading Economics'
            )
            
            indicators.append(indicator)
        except Exception as e:
            logger.error(f"Error processing interest rate data: {str(e)}")
    
    return indicators

def get_inflation_data(country, start_date=None, end_date=None):
    """
    Get inflation data from Trading Economics API
    
    Parameters:
    - country: str (e.g., 'United States', 'Canada')
    - start_date: datetime (optional)
    - end_date: datetime (optional)
    
    Returns:
    - List of EconomicIndicator objects for inflation rates
    """
    data = get_trading_economics_data('inflation-rate', country, start_date, end_date)
    
    # Convert data to EconomicIndicator objects
    indicators = []
    for item in data:
        try:
            # Extract date and value from API response
            date_str = item.get('Date', '')
            value = item.get('Value', 0.0)
            
            # Parse date string to datetime object
            date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
            
            # Create EconomicIndicator object
            indicator = EconomicIndicator(
                indicator_type='inflation-rate',
                value=float(value),
                date=date,
                country=country,
                forecast=None,  # API might provide forecast data
                source='Trading Economics'
            )
            
            indicators.append(indicator)
        except Exception as e:
            logger.error(f"Error processing inflation data: {str(e)}")
    
    return indicators

def get_gdp_data(country, start_date=None, end_date=None):
    """
    Get GDP growth data from Trading Economics API
    
    Parameters:
    - country: str (e.g., 'United States', 'Canada')
    - start_date: datetime (optional)
    - end_date: datetime (optional)
    
    Returns:
    - List of EconomicIndicator objects for GDP growth rates
    """
    data = get_trading_economics_data('gdp-growth', country, start_date, end_date)
    
    # Convert data to EconomicIndicator objects
    indicators = []
    for item in data:
        try:
            # Extract date and value from API response
            date_str = item.get('Date', '')
            value = item.get('Value', 0.0)
            
            # Parse date string to datetime object
            date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
            
            # Create EconomicIndicator object
            indicator = EconomicIndicator(
                indicator_type='gdp-growth',
                value=float(value),
                date=date,
                country=country,
                forecast=None,  # API might provide forecast data
                source='Trading Economics'
            )
            
            indicators.append(indicator)
        except Exception as e:
            logger.error(f"Error processing GDP data: {str(e)}")
    
    return indicators

def get_housing_data(country, start_date=None, end_date=None):
    """
    Get housing market data from Trading Economics API
    
    Parameters:
    - country: str (e.g., 'United States', 'Canada')
    - start_date: datetime (optional)
    - end_date: datetime (optional)
    
    Returns:
    - Dictionary with housing market indicators
    """
    # Housing data might be available under different categories
    housing_price_data = get_trading_economics_data('housing-index', country, start_date, end_date)
    housing_starts_data = get_trading_economics_data('housing-starts', country, start_date, end_date)
    home_sales_data = get_trading_economics_data('home-sales', country, start_date, end_date)
    
    # Process and combine various housing indicators
    housing_indicators = {
        'housing_price_index': process_housing_indicator(housing_price_data, 'housing-index', country),
        'housing_starts': process_housing_indicator(housing_starts_data, 'housing-starts', country),
        'home_sales': process_housing_indicator(home_sales_data, 'home-sales', country)
    }
    
    return housing_indicators

def process_housing_indicator(data, indicator_type, country):
    """Process housing indicator data into EconomicIndicator objects"""
    indicators = []
    for item in data:
        try:
            # Extract date and value from API response
            date_str = item.get('Date', '')
            value = item.get('Value', 0.0)
            
            # Parse date string to datetime object
            date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
            
            # Create EconomicIndicator object
            indicator = EconomicIndicator(
                indicator_type=indicator_type,
                value=float(value),
                date=date,
                country=country,
                forecast=None,
                source='Trading Economics'
            )
            
            indicators.append(indicator.to_dict())
        except Exception as e:
            logger.error(f"Error processing {indicator_type} data: {str(e)}")
    
    return indicators

def get_material_prices():
    """
    Get construction material prices from Trading Economics API
    
    Returns:
    - Dictionary with material prices
    """
    # List of materials to fetch
    materials = ['lumber', 'steel', 'concrete', 'copper', 'aluminum']
    
    material_prices = {}
    
    try:
        if not API_KEY:
            logger.warning("Trading Economics API key not found in environment variables")
            # Return sample data for development
            return generate_sample_material_prices()
        
        # Base URL for Trading Economics API
        base_url = "https://api.tradingeconomics.com/commodities"
        
        # Make API request for commodities
        response = requests.get(f"{base_url}?c={API_KEY}")
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant material prices
            for item in data:
                name = item.get('Name', '').lower()
                for material in materials:
                    if material in name:
                        material_prices[material] = item.get('Last', 0.0)
            
            # Fill in missing materials with defaults
            for material in materials:
                if material not in material_prices:
                    material_prices[material] = get_default_material_price(material)
            
            return material_prices
        else:
            logger.error(f"Error fetching material prices: {response.status_code} - {response.text}")
            # Return sample data for development
            return generate_sample_material_prices()
    
    except Exception as e:
        logger.error(f"Exception when calling Trading Economics API for material prices: {str(e)}")
        # Return sample data for development
        return generate_sample_material_prices()

def get_country_code(country_name):
    """Convert country name to code used by Trading Economics API"""
    country_codes = {
        'United States': 'united-states',
        'Canada': 'canada',
        'United Kingdom': 'united-kingdom',
        'Australia': 'australia',
        'Germany': 'germany',
        'France': 'france',
        'Japan': 'japan',
        'China': 'china',
        'India': 'india',
        'Brazil': 'brazil'
    }
    
    # Convert to lowercase and standardize
    country_name_lower = country_name.lower()
    
    # Check if country name is in the dictionary
    for name, code in country_codes.items():
        if name.lower() == country_name_lower:
            return code
    
    # If not found, try to generate a code from the name
    return country_name.lower().replace(' ', '-')

def get_default_material_price(material):
    """Get default price for a construction material"""
    default_prices = {
        'lumber': 400.0,
        'steel': 900.0,
        'concrete': 110.0,
        'copper': 4.0,
        'aluminum': 2.0,
        'insulation': 0.5,
        'drywall': 12.0
    }
    
    return default_prices.get(material, 100.0)

# Sample data generation for development without API access
def generate_sample_economic_data(category, country, start_date=None, end_date=None):
    """Generate sample economic data for development/testing"""
    logger.info(f"Generating sample data for {category} in {country}")
    
    # Set default dates if not provided
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        # Default to 1 year of data
        start_date = end_date - timedelta(days=365)
    
    # Calculate number of data points (monthly data)
    delta = end_date - start_date
    num_months = max(1, delta.days // 30)
    
    # Base values and trends for different categories
    base_values = {
        'interest-rate': 3.5,
        'inflation-rate': 2.8,
        'gdp-growth': 2.1,
        'housing-index': 150,
        'housing-starts': 1400,
        'home-sales': 600
    }
    
    # Volatility for different categories
    volatility = {
        'interest-rate': 0.2,
        'inflation-rate': 0.3,
        'gdp-growth': 0.4,
        'housing-index': 3.0,
        'housing-starts': 50,
        'home-sales': 20
    }
    
    # Generate data points
    data = []
    base_value = base_values.get(category, 2.0)
    vol = volatility.get(category, 0.2)
    trend = random.choice([-0.02, -0.01, 0, 0.01, 0.02])  # Random trend
    
    for i in range(num_months):
        date = start_date + timedelta(days=i*30)
        # Add trend and some randomness
        value = base_value * (1 + trend * i) + random.uniform(-vol, vol)
        
        data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Value': round(value, 2),
            'Country': country,
            'Category': category
        })
    
    return data

def generate_sample_material_prices():
    """Generate sample construction material prices for development/testing"""
    logger.info("Generating sample material prices")
    
    return {
        'lumber': round(random.uniform(350, 450), 2),
        'steel': round(random.uniform(800, 1000), 2),
        'concrete': round(random.uniform(90, 130), 2),
        'copper': round(random.uniform(3.5, 4.5), 2),
        'aluminum': round(random.uniform(1.8, 2.2), 2),
        'insulation': round(random.uniform(0.4, 0.6), 2),
        'drywall': round(random.uniform(10, 14), 2)
    }