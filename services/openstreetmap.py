import logging
import random
import math
from typing import List, Dict, Any, Optional
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_location_details(lat, lng, radius):
    """
    Get location details from OpenStreetMap Nominatim API and Overpass API
    
    Parameters:
    - lat: float (latitude)
    - lng: float (longitude)
    - radius: int (search radius in meters)
    
    Returns:
    - Dict with location details including amenities, green areas, etc.
    """
    logger.info(f"Getting location details for ({lat}, {lng}) with radius {radius}m")
    
    try:
        # Get reverse geocoding information
        location_info = get_reverse_geocode(lat, lng)
        
        # Get nearby amenities using Overpass API
        amenities = get_nearby_amenities(lat, lng, radius)
        
        # Get green areas using Overpass API
        green_areas = get_green_areas(lat, lng, radius)
        
        # Get transportation information
        transportation = get_transportation_info(lat, lng, radius)
        
        # Calculate walkability score
        walkability = calculate_walkability_score(lat, lng, radius)
        
        # Combine all information
        location_details = {
            'address': location_info.get('address', {}),
            'amenities': amenities,
            'green_areas': green_areas,
            'transportation': transportation,
            'walkability_score': walkability
        }
        
        return location_details
    
    except Exception as e:
        logger.error(f"Error getting location details: {str(e)}")
        # Return sample data for development
        return generate_sample_location_details(lat, lng, radius)

def search_locations(query, limit=10):
    """
    Search for locations using OpenStreetMap Nominatim API
    
    Parameters:
    - query: str (search query)
    - limit: int (max results to return)
    
    Returns:
    - List of location details
    """
    logger.info(f"Searching for locations: '{query}'")
    
    try:
        # Nominatim API endpoint
        url = "https://nominatim.openstreetmap.org/search"
        
        # Request headers (Nominatim requires a User-Agent)
        headers = {
            'User-Agent': 'SmartEstateCompass/1.0'
        }
        
        # Request parameters
        params = {
            'q': query,
            'format': 'json',
            'addressdetails': 1,
            'limit': limit
        }
        
        # Make API request
        response = requests.get(url, headers=headers, params=params)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Process results
            locations = []
            for item in data:
                location = {
                    'display_name': item.get('display_name', ''),
                    'lat': float(item.get('lat', 0)),
                    'lng': float(item.get('lon', 0)),
                    'type': item.get('type', ''),
                    'address': item.get('address', {})
                }
                locations.append(location)
            
            return locations
        else:
            logger.error(f"Error searching locations: {response.status_code} - {response.text}")
            # Return sample data for development
            return generate_sample_search_results(query, limit)
    
    except Exception as e:
        logger.error(f"Exception when calling Nominatim API: {str(e)}")
        # Return sample data for development
        return generate_sample_search_results(query, limit)

def get_reverse_geocode(lat, lng):
    """Get reverse geocoding information from Nominatim API"""
    try:
        # Nominatim API endpoint
        url = "https://nominatim.openstreetmap.org/reverse"
        
        # Request headers
        headers = {
            'User-Agent': 'SmartEstateCompass/1.0'
        }
        
        # Request parameters
        params = {
            'lat': lat,
            'lon': lng,
            'format': 'json',
            'addressdetails': 1
        }
        
        # Make API request
        response = requests.get(url, headers=headers, params=params)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            logger.error(f"Error with reverse geocoding: {response.status_code} - {response.text}")
            # Return sample data
            return generate_sample_reverse_geocode(lat, lng)
    
    except Exception as e:
        logger.error(f"Exception with reverse geocoding: {str(e)}")
        # Return sample data
        return generate_sample_reverse_geocode(lat, lng)

def get_nearby_amenities(lat, lng, radius):
    """Get nearby amenities using Overpass API"""
    try:
        # Overpass API endpoint
        url = "https://overpass-api.de/api/interpreter"
        
        # Convert radius to degrees (approximate)
        radius_deg = radius / 111000  # 111km per degree
        
        # Overpass query
        query = f"""
        [out:json];
        (
          node["amenity"](around:{radius},{lat},{lng});
          way["amenity"](around:{radius},{lat},{lng});
          relation["amenity"](around:{radius},{lat},{lng});
        );
        out center;
        """
        
        # Make API request
        response = requests.post(url, data={'data': query})
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            amenities = []
            for element in data.get('elements', []):
                # Extract center coordinates for ways and relations
                if element['type'] == 'way' or element['type'] == 'relation':
                    if 'center' in element:
                        element_lat = element['center']['lat']
                        element_lng = element['center']['lon']
                    else:
                        continue
                else:  # For nodes
                    element_lat = element['lat']
                    element_lng = element['lon']
                
                amenity = {
                    'type': element.get('tags', {}).get('amenity', 'unknown'),
                    'name': element.get('tags', {}).get('name', 'Unnamed'),
                    'lat': element_lat,
                    'lng': element_lng,
                    'distance': haversine_distance(lat, lng, element_lat, element_lng)
                }
                amenities.append(amenity)
            
            return amenities
        else:
            logger.error(f"Error fetching amenities: {response.status_code} - {response.text}")
            # Return sample data
            return generate_sample_amenities(lat, lng, radius)
    
    except Exception as e:
        logger.error(f"Exception fetching amenities: {str(e)}")
        # Return sample data
        return generate_sample_amenities(lat, lng, radius)

def get_green_areas(lat, lng, radius):
    """Get green areas using Overpass API"""
    try:
        # Overpass API endpoint
        url = "https://overpass-api.de/api/interpreter"
        
        # Overpass query for parks, gardens, forests, etc.
        query = f"""
        [out:json];
        (
          node["leisure"="park"](around:{radius},{lat},{lng});
          way["leisure"="park"](around:{radius},{lat},{lng});
          relation["leisure"="park"](around:{radius},{lat},{lng});
          
          node["landuse"="forest"](around:{radius},{lat},{lng});
          way["landuse"="forest"](around:{radius},{lat},{lng});
          relation["landuse"="forest"](around:{radius},{lat},{lng});
          
          node["natural"="water"](around:{radius},{lat},{lng});
          way["natural"="water"](around:{radius},{lat},{lng});
          relation["natural"="water"](around:{radius},{lat},{lng});
        );
        out center;
        """
        
        # Make API request
        response = requests.post(url, data={'data': query})
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            green_areas = []
            for element in data.get('elements', []):
                # Extract center coordinates for ways and relations
                if element['type'] == 'way' or element['type'] == 'relation':
                    if 'center' in element:
                        element_lat = element['center']['lat']
                        element_lng = element['center']['lon']
                    else:
                        continue
                else:  # For nodes
                    element_lat = element['lat']
                    element_lng = element['lon']
                
                area = {
                    'type': element.get('tags', {}).get('leisure') or element.get('tags', {}).get('landuse') or element.get('tags', {}).get('natural', 'unknown'),
                    'name': element.get('tags', {}).get('name', 'Unnamed Area'),
                    'lat': element_lat,
                    'lng': element_lng,
                    'distance': haversine_distance(lat, lng, element_lat, element_lng)
                }
                green_areas.append(area)
            
            return green_areas
        else:
            logger.error(f"Error fetching green areas: {response.status_code} - {response.text}")
            # Return sample data
            return generate_sample_green_areas(lat, lng, radius)
    
    except Exception as e:
        logger.error(f"Exception fetching green areas: {str(e)}")
        # Return sample data
        return generate_sample_green_areas(lat, lng, radius)

def get_transportation_info(lat, lng, radius):
    """Get transportation information using Overpass API"""
    try:
        # Overpass API endpoint
        url = "https://overpass-api.de/api/interpreter"
        
        # Overpass query for transportation nodes
        query = f"""
        [out:json];
        (
          node["public_transport"](around:{radius},{lat},{lng});
          node["highway"="bus_stop"](around:{radius},{lat},{lng});
          node["railway"="station"](around:{radius},{lat},{lng});
          node["railway"="subway_entrance"](around:{radius},{lat},{lng});
          way["highway"="primary"](around:{radius},{lat},{lng});
          way["highway"="secondary"](around:{radius},{lat},{lng});
        );
        out center;
        """
        
        # Make API request
        response = requests.post(url, data={'data': query})
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            transportation = []
            for element in data.get('elements', []):
                # Extract center coordinates for ways and relations
                if element['type'] == 'way' or element['type'] == 'relation':
                    if 'center' in element:
                        element_lat = element['center']['lat']
                        element_lng = element['center']['lon']
                    else:
                        continue
                else:  # For nodes
                    element_lat = element['lat']
                    element_lng = element['lon']
                
                # Determine type
                if element.get('tags', {}).get('railway') == 'station':
                    transport_type = 'train_station'
                elif element.get('tags', {}).get('railway') == 'subway_entrance':
                    transport_type = 'subway'
                elif element.get('tags', {}).get('highway') == 'bus_stop':
                    transport_type = 'bus_stop'
                elif element.get('tags', {}).get('highway') in ('primary', 'secondary'):
                    transport_type = 'major_road'
                else:
                    transport_type = element.get('tags', {}).get('public_transport', 'unknown')
                
                transport = {
                    'type': transport_type,
                    'name': element.get('tags', {}).get('name', 'Unnamed'),
                    'lat': element_lat,
                    'lng': element_lng,
                    'distance': haversine_distance(lat, lng, element_lat, element_lng)
                }
                transportation.append(transport)
            
            return transportation
        else:
            logger.error(f"Error fetching transportation: {response.status_code} - {response.text}")
            # Return sample data
            return generate_sample_transportation(lat, lng, radius)
    
    except Exception as e:
        logger.error(f"Exception fetching transportation: {str(e)}")
        # Return sample data
        return generate_sample_transportation(lat, lng, radius)

def calculate_walkability_score(lat, lng, radius=1000):
    """
    Calculate walkability score for a location based on nearby amenities
    
    Parameters:
    - lat: float (latitude)
    - lng: float (longitude)
    - radius: int (search radius in meters)
    
    Returns:
    - Walkability score (0-100)
    """
    try:
        # Get amenities
        amenities = get_nearby_amenities(lat, lng, radius)
        
        # Get transportation
        transportation = get_transportation_info(lat, lng, radius)
        
        # Count amenities by category
        grocery_stores = 0
        restaurants = 0
        retail = 0
        entertainment = 0
        schools = 0
        
        for amenity in amenities:
            amenity_type = amenity['type'].lower()
            if amenity_type in ('supermarket', 'grocery', 'marketplace'):
                grocery_stores += 1
            elif amenity_type in ('restaurant', 'cafe', 'pub', 'bar', 'fast_food'):
                restaurants += 1
            elif amenity_type in ('shop', 'mall', 'department_store'):
                retail += 1
            elif amenity_type in ('cinema', 'theatre', 'arts_centre', 'library'):
                entertainment += 1
            elif amenity_type in ('school', 'university', 'college'):
                schools += 1
        
        # Count transportation options
        public_transit = 0
        for option in transportation:
            if option['type'] in ('bus_stop', 'train_station', 'subway', 'tram_stop'):
                public_transit += 1
        
        # Calculate walkability score components
        grocery_score = min(3, grocery_stores) * 6  # Max 18 points
        restaurant_score = min(5, restaurants) * 3  # Max 15 points
        retail_score = min(5, retail) * 2  # Max 10 points
        entertainment_score = min(4, entertainment) * 3  # Max 12 points
        school_score = min(3, schools) * 5  # Max 15 points
        transit_score = min(6, public_transit) * 5  # Max 30 points
        
        # Calculate total score (normalize to 0-100)
        total_score = grocery_score + restaurant_score + retail_score + entertainment_score + school_score + transit_score
        normalized_score = min(100, total_score)
        
        return normalized_score
    
    except Exception as e:
        logger.error(f"Error calculating walkability: {str(e)}")
        # Return random score between 30-90 for development
        return random.randint(30, 90)

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

# Sample data generation functions for development
def generate_sample_location_details(lat, lng, radius):
    """Generate sample location details for development"""
    logger.info(f"Generating sample location details for ({lat}, {lng})")
    
    # Generate sample address
    address = generate_sample_reverse_geocode(lat, lng).get('address', {})
    
    # Generate sample amenities
    amenities = generate_sample_amenities(lat, lng, radius)
    
    # Generate sample green areas
    green_areas = generate_sample_green_areas(lat, lng, radius)
    
    # Generate sample transportation
    transportation = generate_sample_transportation(lat, lng, radius)
    
    # Calculate sample walkability score
    walkability = random.randint(30, 90)
    
    return {
        'address': address,
        'amenities': amenities,
        'green_areas': green_areas,
        'transportation': transportation,
        'walkability_score': walkability
    }

def generate_sample_reverse_geocode(lat, lng):
    """Generate sample reverse geocoding data"""
    # Sample city names based on rough US geography
    west_cities = ['Los Angeles', 'San Francisco', 'Seattle', 'Portland', 'San Diego']
    central_cities = ['Chicago', 'Denver', 'Dallas', 'Houston', 'St. Louis']
    east_cities = ['New York', 'Boston', 'Philadelphia', 'Washington', 'Miami']
    
    if lng < -100:  # Western US
        city = random.choice(west_cities)
    elif lng < -85:  # Central US
        city = random.choice(central_cities)
    else:  # Eastern US
        city = random.choice(east_cities)
    
    # Sample street names
    streets = ['Main St', 'Oak Ave', 'Pine St', 'Maple Dr', 'Washington Blvd', 'Park Ave']
    
    return {
        'address': {
            'road': random.choice(streets),
            'house_number': str(random.randint(100, 9999)),
            'city': city,
            'state': 'Sample State',
            'postcode': f"{random.randint(10000, 99999)}",
            'country': 'United States'
        },
        'lat': lat,
        'lon': lng,
        'display_name': f"{random.randint(100, 9999)} {random.choice(streets)}, {city}, Sample State, United States"
    }

def generate_sample_amenities(lat, lng, radius):
    """Generate sample amenities data"""
    amenity_types = [
        'restaurant', 'cafe', 'bar', 'supermarket', 'school', 
        'pharmacy', 'hospital', 'bank', 'post_office', 'library'
    ]
    
    count = random.randint(5, 15)
    amenities = []
    
    for i in range(count):
        # Generate random offset from center
        radius_deg = radius / 111000  # 111km per degree
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, radius_deg)
        
        # Calculate new point
        amenity_lat = lat + distance * math.cos(angle)
        amenity_lng = lng + distance * math.sin(angle)
        
        # Calculate actual distance
        actual_distance = haversine_distance(lat, lng, amenity_lat, amenity_lng)
        
        # Choose amenity type
        amenity_type = random.choice(amenity_types)
        
        # Generate name based on type
        if amenity_type == 'restaurant':
            name = f"{random.choice(['Italian', 'Chinese', 'Mexican', 'Thai', 'American'])} Restaurant"
        elif amenity_type == 'cafe':
            name = f"{random.choice(['Coffee', 'Tea', 'Espresso'])} House"
        elif amenity_type == 'supermarket':
            name = f"{random.choice(['Fresh', 'Super', 'Market'])} Groceries"
        elif amenity_type == 'school':
            name = f"{random.choice(['Lincoln', 'Washington', 'Jefferson'])} School"
        elif amenity_type == 'hospital':
            name = f"{random.choice(['City', 'General', 'Memorial'])} Hospital"
        else:
            name = f"{amenity_type.capitalize()} {random.randint(1, 10)}"
        
        amenities.append({
            'type': amenity_type,
            'name': name,
            'lat': amenity_lat,
            'lng': amenity_lng,
            'distance': actual_distance
        })
    
    return amenities

def generate_sample_green_areas(lat, lng, radius):
    """Generate sample green areas data"""
    area_types = ['park', 'forest', 'garden', 'water', 'nature_reserve']
    
    count = random.randint(2, 8)
    areas = []
    
    for i in range(count):
        # Generate random offset from center
        radius_deg = radius / 111000  # 111km per degree
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, radius_deg)
        
        # Calculate new point
        area_lat = lat + distance * math.cos(angle)
        area_lng = lng + distance * math.sin(angle)
        
        # Calculate actual distance
        actual_distance = haversine_distance(lat, lng, area_lat, area_lng)
        
        # Choose area type
        area_type = random.choice(area_types)
        
        # Generate name based on type
        if area_type == 'park':
            name = f"{random.choice(['Central', 'City', 'Memorial', 'River'])} Park"
        elif area_type == 'forest':
            name = f"{random.choice(['Green', 'Pine', 'Oak', 'Cedar'])} Forest"
        elif area_type == 'water':
            name = f"{random.choice(['Blue', 'Silver', 'Crystal'])} Lake"
        else:
            name = f"{random.choice(['Nature', 'Wildlife', 'Botanical'])} {area_type.capitalize()}"
        
        areas.append({
            'type': area_type,
            'name': name,
            'lat': area_lat,
            'lng': area_lng,
            'distance': actual_distance
        })
    
    return areas

def generate_sample_transportation(lat, lng, radius):
    """Generate sample transportation data"""
    transport_types = ['bus_stop', 'train_station', 'subway', 'tram_stop', 'major_road']
    
    count = random.randint(3, 12)
    transportation = []
    
    for i in range(count):
        # Generate random offset from center
        radius_deg = radius / 111000  # 111km per degree
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, radius_deg)
        
        # Calculate new point
        transport_lat = lat + distance * math.cos(angle)
        transport_lng = lng + distance * math.sin(angle)
        
        # Calculate actual distance
        actual_distance = haversine_distance(lat, lng, transport_lat, transport_lng)
        
        # Choose transport type
        transport_type = random.choice(transport_types)
        
        # Generate name based on type
        if transport_type == 'bus_stop':
            name = f"Bus Stop #{random.randint(10, 99)}"
        elif transport_type == 'train_station':
            name = f"{random.choice(['Central', 'North', 'South', 'East', 'West'])} Station"
        elif transport_type == 'subway':
            name = f"Subway #{random.choice(['A', 'B', 'C', 'D', '1', '2', '3'])} Station"
        elif transport_type == 'tram_stop':
            name = f"Tram {random.randint(1, 10)} Stop"
        else:
            name = f"{random.choice(['Main', 'Broadway', 'Market', 'State'])} Street"
        
        transportation.append({
            'type': transport_type,
            'name': name,
            'lat': transport_lat,
            'lng': transport_lng,
            'distance': actual_distance
        })
    
    return transportation

def generate_sample_search_results(query, limit):
    """Generate sample search results for development"""
    logger.info(f"Generating sample search results for: '{query}'")
    
    results = []
    
    # Sample cities
    sample_cities = [
        {'name': 'New York', 'lat': 40.7128, 'lng': -74.0060, 'state': 'NY'},
        {'name': 'Los Angeles', 'lat': 34.0522, 'lng': -118.2437, 'state': 'CA'},
        {'name': 'Chicago', 'lat': 41.8781, 'lng': -87.6298, 'state': 'IL'},
        {'name': 'Houston', 'lat': 29.7604, 'lng': -95.3698, 'state': 'TX'},
        {'name': 'Phoenix', 'lat': 33.4484, 'lng': -112.0740, 'state': 'AZ'},
        {'name': 'Philadelphia', 'lat': 39.9526, 'lng': -75.1652, 'state': 'PA'},
        {'name': 'San Antonio', 'lat': 29.4241, 'lng': -98.4936, 'state': 'TX'},
        {'name': 'San Diego', 'lat': 32.7157, 'lng': -117.1611, 'state': 'CA'},
        {'name': 'Dallas', 'lat': 32.7767, 'lng': -96.7970, 'state': 'TX'},
        {'name': 'San Francisco', 'lat': 37.7749, 'lng': -122.4194, 'state': 'CA'}
    ]
    
    # Filter cities based on query
    filtered_cities = []
    for city in sample_cities:
        if query.lower() in city['name'].lower() or query.lower() in city['state'].lower():
            filtered_cities.append(city)
    
    # Use filtered cities if any, otherwise use random cities
    source_cities = filtered_cities if filtered_cities else sample_cities
    
    # Generate results
    for i in range(min(limit, len(source_cities))):
        city = source_cities[i]
        
        result = {
            'display_name': f"{city['name']}, {city['state']}, USA",
            'lat': city['lat'],
            'lng': city['lng'],
            'type': 'city',
            'address': {
                'city': city['name'],
                'state': city['state'],
                'country': 'USA'
            }
        }
        
        results.append(result)
    
    return results