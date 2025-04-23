import os
import logging
import random
import math
from typing import Dict, List, Any, Tuple
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API key from environment
API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

def get_geocode(location):
    """
    Get geocoding information for a location from Google Maps API
    
    Parameters:
    - location: str (address or city/state)
    
    Returns:
    - dict with lat, lng, and formatted_address
    """
    logger.info(f"Geocoding location: {location}")
    
    if not API_KEY:
        logger.warning("Google Maps API key not found in environment variables")
        # Return mock data for development
        return generate_mock_geocode(location)
    
    try:
        # Google Maps Geocoding API endpoint
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        # Request parameters
        params = {
            'address': location,
            'key': API_KEY
        }
        
        # Make API request
        response = requests.get(url, params=params)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Check if results were found
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                location_data = {
                    'lat': result['geometry']['location']['lat'],
                    'lng': result['geometry']['location']['lng'],
                    'formatted_address': result['formatted_address']
                }
                return location_data
            else:
                logger.error(f"Geocoding error: {data['status']}")
                # Return mock data if API returns an error
                return generate_mock_geocode(location)
        else:
            logger.error(f"Error fetching geocode data: {response.status_code} - {response.text}")
            # Return mock data if API request fails
            return generate_mock_geocode(location)
    
    except Exception as e:
        logger.error(f"Exception when calling Google Maps API: {str(e)}")
        # Return mock data if an exception occurs
        return generate_mock_geocode(location)

def get_nearby_places(lat, lng, radius, place_type):
    """
    Get nearby places from Google Maps Places API
    
    Parameters:
    - lat: float (latitude)
    - lng: float (longitude)
    - radius: int (search radius in meters)
    - place_type: str (e.g., 'school', 'hospital', 'transit_station', 'park')
    
    Returns:
    - List of places with name, location, and details
    """
    logger.info(f"Finding nearby {place_type}s at ({lat}, {lng})")
    
    if not API_KEY:
        logger.warning("Google Maps API key not found in environment variables")
        # Return mock data for development
        return generate_sample_places(lat, lng, radius, place_type, 10)
    
    try:
        # Google Maps Places API endpoint
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
        # Request parameters
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'type': place_type,
            'key': API_KEY
        }
        
        # Make API request
        response = requests.get(url, params=params)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Check if results were found
            if data['status'] == 'OK' and data['results']:
                places = []
                
                for place in data['results']:
                    place_data = {
                        'name': place.get('name', ''),
                        'location': {
                            'lat': place['geometry']['location']['lat'],
                            'lng': place['geometry']['location']['lng']
                        },
                        'address': place.get('vicinity', ''),
                        'rating': place.get('rating', 0),
                        'user_ratings_total': place.get('user_ratings_total', 0),
                        'place_id': place.get('place_id', ''),
                        'distance': haversine_distance(
                            lat, lng,
                            place['geometry']['location']['lat'],
                            place['geometry']['location']['lng']
                        )
                    }
                    places.append(place_data)
                
                return places
            else:
                logger.error(f"Places API error: {data['status']}")
                # Return mock data if API returns an error
                return generate_sample_places(lat, lng, radius, place_type, 10)
        else:
            logger.error(f"Error fetching places data: {response.status_code} - {response.text}")
            # Return mock data if API request fails
            return generate_sample_places(lat, lng, radius, place_type, 10)
    
    except Exception as e:
        logger.error(f"Exception when calling Google Maps Places API: {str(e)}")
        # Return mock data if an exception occurs
        return generate_sample_places(lat, lng, radius, place_type, 10)

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    # Return distance in meters
    return round(c * r * 1000, 2)

def generate_mock_geocode(location):
    """Generate mock geocoding data for development/testing"""
    logger.info(f"Generating mock geocode for {location}")
    
    # Sample locations with coordinates
    sample_locations = {
        'New York': {'lat': 40.7128, 'lng': -74.0060, 'address': 'New York, NY, USA'},
        'Los Angeles': {'lat': 34.0522, 'lng': -118.2437, 'address': 'Los Angeles, CA, USA'},
        'Chicago': {'lat': 41.8781, 'lng': -87.6298, 'address': 'Chicago, IL, USA'},
        'Houston': {'lat': 29.7604, 'lng': -95.3698, 'address': 'Houston, TX, USA'},
        'Phoenix': {'lat': 33.4484, 'lng': -112.0740, 'address': 'Phoenix, AZ, USA'},
        'Philadelphia': {'lat': 39.9526, 'lng': -75.1652, 'address': 'Philadelphia, PA, USA'},
        'San Antonio': {'lat': 29.4241, 'lng': -98.4936, 'address': 'San Antonio, TX, USA'},
        'San Diego': {'lat': 32.7157, 'lng': -117.1611, 'address': 'San Diego, CA, USA'},
        'Dallas': {'lat': 32.7767, 'lng': -96.7970, 'address': 'Dallas, TX, USA'},
        'San Francisco': {'lat': 37.7749, 'lng': -122.4194, 'address': 'San Francisco, CA, USA'}
    }
    
    # Try to match the location to a sample
    for city, data in sample_locations.items():
        if city.lower() in location.lower():
            return {
                'lat': data['lat'],
                'lng': data['lng'],
                'formatted_address': data['address']
            }
    
    # If no match, generate random coordinates in continental US
    return {
        'lat': random.uniform(25, 49),
        'lng': random.uniform(-125, -70),
        'formatted_address': f"{location}, USA"
    }

def generate_sample_places(lat, lng, radius, place_type, count):
    """Generate sample places for development/testing"""
    logger.info(f"Generating {count} sample {place_type}s near ({lat}, {lng})")
    
    # Different place types have different naming patterns
    place_name_prefixes = {
        'school': ['Elementary School', 'High School', 'Middle School', 'Academy', 'University'],
        'hospital': ['Hospital', 'Medical Center', 'Clinic', 'Health Center'],
        'transit_station': ['Station', 'Transit Center', 'Stop', 'Terminal'],
        'park': ['Park', 'Gardens', 'Playground', 'Recreation Area'],
        'restaurant': ['Restaurant', 'Cafe', 'Bistro', 'Diner'],
        'shopping_mall': ['Mall', 'Shopping Center', 'Galleria', 'Plaza'],
        'supermarket': ['Supermarket', 'Grocery', 'Market', 'Food Store']
    }
    
    # Sample street names
    street_names = ['Main', 'Oak', 'Pine', 'Maple', 'Cedar', 'Elm', 'Washington', 'Lincoln', 'Jefferson', 'Adams']
    
    # Get appropriate prefixes for the place type
    prefixes = place_name_prefixes.get(place_type, ['Business'])
    
    places = []
    for i in range(count):
        # Generate random offset from center within the radius
        # Convert radius from meters to degrees (very approximate)
        radius_deg = radius / 111000  # 111km per degree
        
        # Random direction
        angle = random.uniform(0, 2 * math.pi)
        
        # Random distance within radius
        distance = random.uniform(0, radius_deg)
        
        # Calculate new point
        new_lat = lat + distance * math.cos(angle)
        new_lng = lng + distance * math.sin(angle)
        
        # Calculate actual distance in meters
        distance = haversine_distance(lat, lng, new_lat, new_lng)
        
        # Generate place name
        prefix = random.choice(prefixes)
        name = f"{random.choice(['North', 'South', 'East', 'West', 'Central'])} {random.choice(street_names)} {prefix}"
        
        # Generate place data
        place = {
            'name': name,
            'location': {
                'lat': new_lat,
                'lng': new_lng
            },
            'address': f"{random.randint(100, 9999)} {random.choice(street_names)} St",
            'rating': round(random.uniform(2.0, 5.0), 1),
            'user_ratings_total': random.randint(5, 500),
            'place_id': f"place_{i}_{random.randint(10000, 99999)}",
            'distance': distance
        }
        
        places.append(place)
    
    return places