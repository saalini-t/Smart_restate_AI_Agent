import os
import logging
from datetime import datetime, timedelta
import json
import random
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from models import EconomicIndicator, PropertyPrice, LocationScore, InvestmentRecommendation, ConstructionPlan

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database connection parameters from environment variables
DB_CONFIG = {
    'dbname': os.environ.get('PGDATABASE'),
    'user': os.environ.get('PGUSER'),
    'password': os.environ.get('PGPASSWORD'),
    'host': os.environ.get('PGHOST'),
    'port': os.environ.get('PGPORT')
}

def get_db_connection():
    """Get a PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {str(e)}")
        # Return None if connection fails, callers should handle this case
        return None

def init_db():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to initialize database: Could not connect to PostgreSQL")
        return False
    
    try:
        with conn.cursor() as cur:
            # Create economic_indicators table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS economic_indicators (
                    id SERIAL PRIMARY KEY,
                    indicator_type VARCHAR(50) NOT NULL,
                    value FLOAT NOT NULL,
                    date TIMESTAMP NOT NULL,
                    country VARCHAR(100) NOT NULL,
                    forecast FLOAT,
                    source VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create property_prices table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS property_prices (
                    id SERIAL PRIMARY KEY,
                    location VARCHAR(255) NOT NULL,
                    price FLOAT NOT NULL,
                    date TIMESTAMP NOT NULL,
                    property_type VARCHAR(50) NOT NULL,
                    predicted_price FLOAT,
                    confidence FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create location_scores table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS location_scores (
                    id SERIAL PRIMARY KEY,
                    location VARCHAR(255) NOT NULL,
                    total_score FLOAT NOT NULL,
                    schools_score FLOAT NOT NULL,
                    hospitals_score FLOAT NOT NULL,
                    transport_score FLOAT NOT NULL,
                    crime_score FLOAT NOT NULL,
                    green_zones_score FLOAT NOT NULL,
                    development_score FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create investment_recommendations table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS investment_recommendations (
                    id SERIAL PRIMARY KEY,
                    location VARCHAR(255) NOT NULL,
                    property_type VARCHAR(50) NOT NULL,
                    recommendation VARCHAR(50) NOT NULL,
                    confidence FLOAT NOT NULL,
                    price_forecast JSON,
                    optimal_time VARCHAR(100),
                    roi_estimate FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create construction_plans table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS construction_plans (
                    id SERIAL PRIMARY KEY,
                    location VARCHAR(255) NOT NULL,
                    optimal_start_date VARCHAR(50) NOT NULL,
                    material_prices JSON NOT NULL,
                    weather_forecast JSON NOT NULL,
                    estimated_cost FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create roi_calculations table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS roi_calculations (
                    id SERIAL PRIMARY KEY,
                    location VARCHAR(255) NOT NULL,
                    property_type VARCHAR(50) NOT NULL,
                    investment_goal VARCHAR(50) NOT NULL,
                    purchase_price FLOAT NOT NULL,
                    roi_percentage FLOAT NOT NULL,
                    breakeven_months INTEGER,
                    monthly_cash_flow FLOAT,
                    total_return FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create alerts table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    location VARCHAR(255) NOT NULL,
                    property_type VARCHAR(50) NOT NULL,
                    condition VARCHAR(20) NOT NULL,
                    threshold_value FLOAT NOT NULL,
                    notification_method VARCHAR(20) NOT NULL,
                    phone_number VARCHAR(20),
                    email VARCHAR(100),
                    frequency VARCHAR(20) NOT NULL,
                    last_triggered TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active BOOLEAN DEFAULT TRUE
                );
            """)
            
            # Create notification_history table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notification_history (
                    id SERIAL PRIMARY KEY,
                    alert_id INTEGER REFERENCES alerts(id),
                    notification_type VARCHAR(20) NOT NULL,
                    recipient VARCHAR(100) NOT NULL,
                    message TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            logger.info("Database tables initialized successfully")
            return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Initialize database tables when the module is loaded
init_db()

# Economic Indicators functions
def save_economic_indicator(indicator_data):
    """Save economic indicator data to PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to save economic indicator: Database connection failed")
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO economic_indicators 
                (indicator_type, value, date, country, forecast, source)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                indicator_data.indicator_type,
                indicator_data.value,
                indicator_data.date,
                indicator_data.country,
                indicator_data.forecast,
                indicator_data.source
            ))
            result = cur.fetchone()
            conn.commit()
            logger.debug(f"Saved economic indicator with ID: {result[0]}")
            return result[0]  # Return the ID of the inserted record
    except Exception as e:
        logger.error(f"Error saving economic indicator: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_economic_indicators(indicator_type, start_date, end_date, country=None):
    """Get economic indicator data from PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to get economic indicators: Database connection failed")
        # Return sample data for development purposes
        return generate_sample_economic_indicators(indicator_type, start_date, end_date, country)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT * FROM economic_indicators 
                WHERE indicator_type = %s AND date BETWEEN %s AND %s
            """
            params = [indicator_type, start_date, end_date]
            
            if country:
                query += " AND country = %s"
                params.append(country)
                
            query += " ORDER BY date;"
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            # Convert to EconomicIndicator objects
            indicators = []
            for row in results:
                indicator = EconomicIndicator(
                    indicator_type=row['indicator_type'],
                    value=row['value'],
                    date=row['date'],
                    country=row['country'],
                    forecast=row['forecast'],
                    source=row['source']
                )
                indicators.append(indicator)
            
            return indicators
    except Exception as e:
        logger.error(f"Error fetching economic indicators: {str(e)}")
        # Return sample data for development purposes
        return generate_sample_economic_indicators(indicator_type, start_date, end_date, country)
    finally:
        conn.close()

# Property Price functions
def save_property_data(location, property_type, data):
    """Save property price data to PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to save property data: Database connection failed")
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO property_prices 
                (location, price, date, property_type, predicted_price, confidence)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                location,
                data.price,
                data.date,
                property_type,
                data.predicted_price,
                data.confidence
            ))
            result = cur.fetchone()
            conn.commit()
            logger.debug(f"Saved property data with ID: {result[0]}")
            return result[0]  # Return the ID of the inserted record
    except Exception as e:
        logger.error(f"Error saving property data: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_property_history(location, property_type=None, period='1y'):
    """Get property price history from PostgreSQL"""
    conn = get_db_connection()
    
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
    
    if conn is None:
        logger.error("Failed to get property history: Database connection failed")
        # Return sample data for development purposes
        return generate_sample_property_history(location, property_type, start_date, end_date)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT * FROM property_prices 
                WHERE location = %s AND date BETWEEN %s AND %s
            """
            params = [location, start_date, end_date]
            
            if property_type:
                query += " AND property_type = %s"
                params.append(property_type)
                
            query += " ORDER BY date;"
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            # Convert to PropertyPrice objects
            property_prices = []
            for row in results:
                price = PropertyPrice(
                    location=row['location'],
                    price=row['price'],
                    date=row['date'],
                    property_type=row['property_type'],
                    predicted_price=row['predicted_price'],
                    confidence=row['confidence']
                )
                property_prices.append(price)
            
            return property_prices
    except Exception as e:
        logger.error(f"Error fetching property history: {str(e)}")
        # Return sample data for development purposes
        return generate_sample_property_history(location, property_type, start_date, end_date)
    finally:
        conn.close()

# Location Score functions
def save_location_score(location, score_data):
    """Save location intelligence score to PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to save location score: Database connection failed")
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO location_scores 
                (location, total_score, schools_score, hospitals_score, transport_score, 
                crime_score, green_zones_score, development_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                location,
                score_data.total_score,
                score_data.schools_score,
                score_data.hospitals_score,
                score_data.transport_score,
                score_data.crime_score,
                score_data.green_zones_score,
                score_data.development_score
            ))
            result = cur.fetchone()
            conn.commit()
            logger.debug(f"Saved location score with ID: {result[0]}")
            return result[0]  # Return the ID of the inserted record
    except Exception as e:
        logger.error(f"Error saving location score: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_location_score(location):
    """Get location intelligence score from PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to get location score: Database connection failed")
        # Return sample data for development purposes
        return generate_sample_location_score(location)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM location_scores 
                WHERE location = %s
                ORDER BY created_at DESC
                LIMIT 1;
            """, (location,))
            result = cur.fetchone()
            
            if result:
                # Convert to LocationScore object
                score = LocationScore(
                    location=result['location'],
                    total_score=result['total_score'],
                    schools_score=result['schools_score'],
                    hospitals_score=result['hospitals_score'],
                    transport_score=result['transport_score'],
                    crime_score=result['crime_score'],
                    green_zones_score=result['green_zones_score'],
                    development_score=result['development_score']
                )
                return score
            else:
                # Return sample data if not found
                return generate_sample_location_score(location)
    except Exception as e:
        logger.error(f"Error fetching location score: {str(e)}")
        # Return sample data for development purposes
        return generate_sample_location_score(location)
    finally:
        conn.close()

# Investment Recommendation functions
def save_investment_recommendation(location, property_type, investment_goal, timeframe, recommendation):
    """Save investment timing recommendation to PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to save investment recommendation: Database connection failed")
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO investment_recommendations 
                (location, property_type, recommendation, confidence, price_forecast, optimal_time, roi_estimate)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                location,
                property_type,
                recommendation.recommendation,
                recommendation.confidence,
                json.dumps(recommendation.price_forecast),
                recommendation.optimal_time,
                recommendation.roi_estimate
            ))
            result = cur.fetchone()
            conn.commit()
            logger.debug(f"Saved investment recommendation with ID: {result[0]}")
            return result[0]  # Return the ID of the inserted record
    except Exception as e:
        logger.error(f"Error saving investment recommendation: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_investment_history(location, property_type=None, limit=10):
    """Get investment recommendation history from PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to get investment history: Database connection failed")
        # Return sample data for development purposes
        return generate_sample_investment_history(location, property_type, limit)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT * FROM investment_recommendations 
                WHERE location = %s
            """
            params = [location]
            
            if property_type:
                query += " AND property_type = %s"
                params.append(property_type)
                
            query += " ORDER BY created_at DESC LIMIT %s;"
            params.append(limit)
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            # Convert to InvestmentRecommendation objects
            recommendations = []
            for row in results:
                rec = InvestmentRecommendation(
                    location=row['location'],
                    recommendation=row['recommendation'],
                    confidence=row['confidence'],
                    price_forecast=json.loads(row['price_forecast']),
                    optimal_time=row['optimal_time'],
                    roi_estimate=row['roi_estimate']
                )
                recommendations.append(rec)
            
            return recommendations if recommendations else generate_sample_investment_history(location, property_type, limit)
    except Exception as e:
        logger.error(f"Error fetching investment history: {str(e)}")
        # Return sample data for development purposes
        return generate_sample_investment_history(location, property_type, limit)
    finally:
        conn.close()

# Construction Plan functions
def save_construction_plan(location, property_type, area_sqft, quality_level, plan_data):
    """Save construction plan to PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to save construction plan: Database connection failed")
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO construction_plans 
                (location, optimal_start_date, material_prices, weather_forecast, estimated_cost)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                location,
                plan_data.optimal_start_date,
                json.dumps(plan_data.material_prices),
                json.dumps(plan_data.weather_forecast),
                plan_data.estimated_cost
            ))
            result = cur.fetchone()
            conn.commit()
            logger.debug(f"Saved construction plan with ID: {result[0]}")
            return result[0]  # Return the ID of the inserted record
    except Exception as e:
        logger.error(f"Error saving construction plan: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_construction_history(location, property_type=None, limit=10):
    """Get construction plan history from PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to get construction history: Database connection failed")
        # Return sample data for development purposes
        return generate_sample_construction_history(location, limit)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT * FROM construction_plans 
                WHERE location = %s
                ORDER BY created_at DESC LIMIT %s;
            """
            params = [location, limit]
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            # Convert to ConstructionPlan objects
            plans = []
            for row in results:
                plan = ConstructionPlan(
                    location=row['location'],
                    optimal_start_date=row['optimal_start_date'],
                    material_prices=json.loads(row['material_prices']),
                    weather_forecast=json.loads(row['weather_forecast']),
                    estimated_cost=row['estimated_cost']
                )
                plans.append(plan)
            
            return plans if plans else generate_sample_construction_history(location, limit)
    except Exception as e:
        logger.error(f"Error fetching construction history: {str(e)}")
        # Return sample data for development purposes
        return generate_sample_construction_history(location, limit)
    finally:
        conn.close()

# Data generation functions for development purposes
def generate_sample_economic_indicators(indicator_type, start_date, end_date, country=None):
    """Generate sample economic indicators for development/testing"""
    logger.info(f"Generating sample economic indicators for {indicator_type}")
    
    if not country:
        country = "United States"
    
    # Calculate number of data points (monthly data)
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    delta = end_date - start_date
    num_months = max(1, delta.days // 30)
    
    # Base values for different indicator types
    base_values = {
        'interest-rate': 3.5,
        'inflation-rate': 2.8,
        'gdp-growth': 2.1,
        'housing-index': 150
    }
    
    # Volatility for different indicator types
    volatility = {
        'interest-rate': 0.3,
        'inflation-rate': 0.4,
        'gdp-growth': 0.5,
        'housing-index': 2.0
    }
    
    # Generate data points
    indicators = []
    base_value = base_values.get(indicator_type, 2.0)
    vol = volatility.get(indicator_type, 0.3)
    
    for i in range(num_months):
        date = start_date + timedelta(days=i*30)
        value = base_value + random.uniform(-vol, vol)
        forecast = value + random.uniform(-vol/2, vol) if random.random() > 0.5 else None
        
        indicator = EconomicIndicator(
            indicator_type=indicator_type,
            value=round(value, 2),
            date=date,
            country=country,
            forecast=round(forecast, 2) if forecast else None,
            source="Sample Data"
        )
        indicators.append(indicator)
    
    return indicators

def generate_sample_property_history(location, property_type, start_date, end_date):
    """Generate sample property price history for development/testing"""
    logger.info(f"Generating sample property history for {location}")
    
    if not property_type:
        property_type = random.choice(["residential", "commercial", "land"])
    
    # Base prices for different property types
    base_prices = {
        "residential": 350000,
        "commercial": 750000,
        "land": 200000
    }
    
    # Volatility for different property types
    volatility = {
        "residential": 10000,
        "commercial": 25000,
        "land": 5000
    }
    
    # Calculate number of data points (monthly data)
    delta = end_date - start_date
    num_months = max(1, delta.days // 30)
    
    # Generate data points
    prices = []
    base_price = base_prices.get(property_type, 300000)
    vol = volatility.get(property_type, 10000)
    
    for i in range(num_months):
        date = start_date + timedelta(days=i*30)
        price = base_price + random.uniform(-vol, vol)
        predicted_price = price * (1 + random.uniform(0.01, 0.05)) if random.random() > 0.3 else None
        confidence = random.uniform(0.6, 0.9) if predicted_price else None
        
        price_obj = PropertyPrice(
            location=location,
            price=round(price, 2),
            date=date,
            property_type=property_type,
            predicted_price=round(predicted_price, 2) if predicted_price else None,
            confidence=round(confidence, 2) if confidence else None
        )
        prices.append(price_obj)
    
    return prices

def generate_sample_location_score(location):
    """Generate sample location intelligence score for development/testing"""
    logger.info(f"Generating sample location score for {location}")
    
    # Generate random scores for different criteria
    schools_score = random.uniform(60, 95)
    hospitals_score = random.uniform(55, 90)
    transport_score = random.uniform(50, 95)
    crime_score = random.uniform(40, 95)
    green_zones_score = random.uniform(45, 90)
    development_score = random.uniform(50, 95)
    
    # Calculate total score as weighted average
    total_score = (
        schools_score * 0.2 + 
        hospitals_score * 0.15 + 
        transport_score * 0.2 + 
        crime_score * 0.2 + 
        green_zones_score * 0.1 + 
        development_score * 0.15
    )
    
    # Round scores for better readability
    return LocationScore(
        location=location,
        total_score=round(total_score, 1),
        schools_score=round(schools_score, 1),
        hospitals_score=round(hospitals_score, 1),
        transport_score=round(transport_score, 1),
        crime_score=round(crime_score, 1),
        green_zones_score=round(green_zones_score, 1),
        development_score=round(development_score, 1)
    )

def generate_sample_investment_history(location, property_type, limit):
    """Generate sample investment recommendations for development/testing"""
    logger.info(f"Generating sample investment history for {location}")
    
    if not property_type:
        property_types = ["residential", "commercial", "land"]
    else:
        property_types = [property_type]
    
    recommendations = []
    
    for i in range(min(limit, 5)):
        # Choose random property type if not specified
        p_type = property_type if property_type else random.choice(property_types)
        
        # Generate random recommendation data
        rec_types = ["buy", "hold", "sell"]
        weights = [0.5, 0.3, 0.2]
        recommendation = random.choices(rec_types, weights=weights, k=1)[0]
        
        confidence = random.uniform(0.6, 0.95)
        
        # Generate price forecast for next 12 months
        price_forecast = []
        current_price = random.uniform(300000, 800000)
        for month in range(1, 13):
            future_date = datetime.now() + timedelta(days=month*30)
            change_pct = random.uniform(-0.03, 0.07)
            projected_price = current_price * (1 + change_pct)
            
            price_forecast.append({
                "date": future_date.strftime("%Y-%m"),
                "price": round(projected_price, 2),
                "change_pct": round(change_pct * 100, 2)
            })
            current_price = projected_price
        
        # Other recommendation details
        optimal_time = f"{random.randint(1, 12)} months" if recommendation == "buy" else None
        roi_estimate = random.uniform(5, 15) if recommendation != "sell" else None
        
        # Create recommendation object
        rec_obj = InvestmentRecommendation(
            location=location,
            recommendation=recommendation,
            confidence=round(confidence, 2),
            price_forecast=price_forecast,
            optimal_time=optimal_time,
            roi_estimate=round(roi_estimate, 2) if roi_estimate else None
        )
        recommendations.append(rec_obj)
    
    return recommendations

def generate_sample_construction_history(location, limit):
    """Generate sample construction plans for development/testing"""
    logger.info(f"Generating sample construction history for {location}")
    
    plans = []
def save_roi_calculation(location, property_type, investment_goal, purchase_price, roi_data):
    """Save ROI calculation to PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to save ROI calculation: Database connection failed")
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO roi_calculations 
                (location, property_type, investment_goal, purchase_price, roi_percentage, 
                breakeven_months, monthly_cash_flow, total_return)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                location,
                property_type,
                investment_goal,
                purchase_price,
                roi_data.get('roi_percentage', 0),
                roi_data.get('breakeven_months', 0),
                roi_data.get('monthly_cash_flow', 0),
                roi_data.get('total_return', 0)
            ))
            result = cur.fetchone()
            conn.commit()
            logger.debug(f"Saved ROI calculation with ID: {result[0]}")
            return result[0]  # Return the ID of the inserted record
    except Exception as e:
        logger.error(f"Error saving ROI calculation: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_roi_history(location, property_type=None, limit=10):
    """Get ROI calculation history from PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to get ROI history: Database connection failed")
        # Return sample data for development purposes
        return generate_sample_roi_history(location, property_type, limit)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT * FROM roi_calculations 
                WHERE location = %s
            """
            params = [location]
            
            if property_type:
                query += " AND property_type = %s"
                params.append(property_type)
                
            query += " ORDER BY created_at DESC LIMIT %s;"
            params.append(limit)
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            # Convert to dictionary objects
            roi_history = []
            for row in results:
                roi_history.append({
                    'id': row['id'],
                    'location': row['location'],
                    'property_type': row['property_type'],
                    'investment_goal': row['investment_goal'],
                    'purchase_price': row['purchase_price'],
                    'roi_percentage': row['roi_percentage'],
                    'breakeven_months': row['breakeven_months'],
                    'monthly_cash_flow': row['monthly_cash_flow'],
                    'total_return': row['total_return'],
                    'created_at': row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return roi_history
    except Exception as e:
        logger.error(f"Error fetching ROI history: {str(e)}")
        # Return sample data for development purposes
        return generate_sample_roi_history(location, property_type, limit)
    finally:
        conn.close()

def generate_sample_roi_history(location, property_type=None, limit=10):
    """Generate sample ROI history for development/testing"""
    logger.info(f"Generating sample ROI history for {location}")
    
    # Generate sample ROI calculations
    roi_history = []
    for i in range(min(limit, 5)):
        investment_goals = ['flip', 'rent', 'hold']
        property_types = ['residential', 'commercial', 'land'] if property_type is None else [property_type]
        
        # Generate a sample ROI calculation
        roi_calculation = {
            'id': i + 1,
            'location': location,
            'property_type': random.choice(property_types),
            'investment_goal': random.choice(investment_goals),
            'purchase_price': 300000 + random.uniform(-50000, 200000),
            'roi_percentage': random.uniform(5, 25),
            'breakeven_months': random.randint(24, 120),
            'monthly_cash_flow': random.uniform(500, 3000) if 'rent' in investment_goals else 0,
            'total_return': random.uniform(50000, 300000),
            'created_at': (datetime.now() - timedelta(days=i*7)).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        roi_history.append(roi_calculation)
    
    return roi_history

# Alert system functions
def save_alert(user_id, alert_type, location, property_type, condition, threshold_value, 
              notification_method, phone_number=None, email=None, frequency='immediately'):
    """Save alert to PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to save alert: Database connection failed")
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO alerts 
                (user_id, alert_type, location, property_type, condition, threshold_value, 
                notification_method, phone_number, email, frequency)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                user_id,
                alert_type,
                location,
                property_type,
                condition,
                threshold_value,
                notification_method,
                phone_number,
                email,
                frequency
            ))
            result = cur.fetchone()
            conn.commit()
            logger.debug(f"Saved alert with ID: {result[0]}")
            return result[0]  # Return the ID of the inserted record
    except Exception as e:
        logger.error(f"Error saving alert: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_user_alerts(user_id):
    """Get all alerts for a user from PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to get user alerts: Database connection failed")
        # Return sample data for development purposes
        return generate_sample_alerts(user_id)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM alerts 
                WHERE user_id = %s AND active = TRUE
                ORDER BY created_at DESC;
            """, (user_id,))
            
            results = cur.fetchall()
            
            # Convert to dictionary objects
            alerts = []
            for row in results:
                alerts.append({
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'alert_type': row['alert_type'],
                    'location': row['location'],
                    'property_type': row['property_type'],
                    'condition': row['condition'],
                    'threshold_value': row['threshold_value'],
                    'notification_method': row['notification_method'],
                    'phone_number': row['phone_number'],
                    'email': row['email'],
                    'frequency': row['frequency'],
                    'last_triggered': row['last_triggered'].strftime('%Y-%m-%d %H:%M:%S') if row['last_triggered'] else None,
                    'created_at': row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return alerts
    except Exception as e:
        logger.error(f"Error fetching user alerts: {str(e)}")
        # Return sample data for development purposes
        return generate_sample_alerts(user_id)
    finally:
        conn.close()

def delete_alert(alert_id):
    """Delete or deactivate an alert in PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to delete alert: Database connection failed")
        return False
    
    try:
        with conn.cursor() as cur:
            # Instead of deleting, we set active = FALSE to keep history
            cur.execute("""
                UPDATE alerts
                SET active = FALSE
                WHERE id = %s
                RETURNING id;
            """, (alert_id,))
            
            result = cur.fetchone()
            conn.commit()
            
            if result:
                logger.debug(f"Deactivated alert with ID: {result[0]}")
                return True
            else:
                logger.warning(f"No alert found with ID: {alert_id}")
                return False
    except Exception as e:
        logger.error(f"Error deleting alert: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def save_notification(alert_id, notification_type, recipient, message, status):
    """Save notification history to PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to save notification: Database connection failed")
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO notification_history 
                (alert_id, notification_type, recipient, message, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                alert_id,
                notification_type,
                recipient,
                message,
                status
            ))
            result = cur.fetchone()
            conn.commit()
            logger.debug(f"Saved notification history with ID: {result[0]}")
            return result[0]  # Return the ID of the inserted record
    except Exception as e:
        logger.error(f"Error saving notification history: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()

def generate_sample_alerts(user_id):
    """Generate sample alerts for development/testing"""
    logger.info(f"Generating sample alerts for user {user_id}")
    
    # Sample alert types
    alert_types = ['price_change', 'investment_opportunity', 'market_trend']
    property_types = ['residential', 'commercial', 'land']
    conditions = ['above', 'below', 'equal']
    
    # Generate sample alerts
    alerts = []
    for i in range(3):  # Generate 3 sample alerts
        alert = {
            'id': i + 1,
            'user_id': user_id,
            'alert_type': random.choice(alert_types),
            'location': random.choice(['San Francisco, CA', 'New York, NY', 'Austin, TX']),
            'property_type': random.choice(property_types),
            'condition': random.choice(conditions),
            'threshold_value': random.randint(200000, 1000000),
            'notification_method': random.choice(['sms', 'email', 'both']),
            'phone_number': '+1234567890',
            'email': 'user@example.com',
            'frequency': random.choice(['immediately', 'daily', 'weekly']),
            'last_triggered': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None,
            'created_at': (datetime.now() - timedelta(days=random.randint(30, 90))).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        alerts.append(alert)
    
    return alerts

# Continue with the original function
def generate_sample_construction_history(location, limit):
    """Generate sample construction plans for development/testing"""
    logger.info(f"Generating sample construction history for {location}")
    
    plans = []
    
    for i in range(min(limit, 3)):
        # Generate random construction plan data
        current_date = datetime.now()
        start_month = random.randint(1, 6)
        optimal_start_date = (current_date + timedelta(days=30*start_month)).strftime("%Y-%m-%d")
        
        # Material prices
        material_prices = {
            "lumber": round(random.uniform(2.5, 4.5), 2),
            "concrete": round(random.uniform(90, 120), 2),
            "steel": round(random.uniform(700, 950), 2),
            "insulation": round(random.uniform(0.5, 1.2), 2),
            "drywall": round(random.uniform(10, 15), 2)
        }
        
        # Weather forecast for next 3 months
        weather_forecast = []
        for month in range(3):
            month_date = current_date + timedelta(days=30*month)
            weather_forecast.append({
                "month": month_date.strftime("%Y-%m"),
                "avg_temp": round(random.uniform(50, 85), 1),
                "precipitation_days": random.randint(3, 12),
                "favorable_days": random.randint(15, 25)
            })
        
        # Estimated cost
        estimated_cost = random.uniform(200000, 800000)
        
        # Create construction plan object
        plan_obj = ConstructionPlan(
            location=location,
            optimal_start_date=optimal_start_date,
            material_prices=material_prices,
            weather_forecast=weather_forecast,
            estimated_cost=round(estimated_cost, 2)
        )
        plans.append(plan_obj)
    
    return plans