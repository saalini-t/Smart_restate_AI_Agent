import logging
from flask import Blueprint, jsonify, request
from services.google_maps import get_nearby_places, get_geocode
from services.openstreetmap import get_location_details
from services.database import save_location_score, get_location_score
from models import LocationScore

# Set up logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('location_intelligence', __name__, url_prefix='/api/location-intelligence')

@bp.route('/score', methods=['GET'])
def get_location_score_endpoint():
    """
    Get location intelligence score for a specific location
    
    Query parameters:
    - location: str (address, city, or coordinates)
    - radius: int (optional, search radius in meters, default: 1000)
    """
    try:
        # Get query parameters
        location = request.args.get('location')
        radius = int(request.args.get('radius', 1000))
        
        # Validate required parameters
        if not location:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: location'
            }), 400
        
        # Check if location score exists in database
        cached_score = get_location_score(location)
        
        if cached_score:
            return jsonify({
                'status': 'success',
                'data': cached_score.to_dict()
            })
        
        # If not in database, calculate new score
        
        # First, geocode the location to get coordinates
        geocode_result = get_geocode(location)
        
        if not geocode_result:
            return jsonify({
                'status': 'error',
                'message': 'Failed to geocode the location'
            }), 400
        
        lat = geocode_result['lat']
        lng = geocode_result['lng']
        formatted_address = geocode_result['formatted_address']
        
        # Get nearby places for different categories
        schools = get_nearby_places(lat, lng, radius, 'school')
        hospitals = get_nearby_places(lat, lng, radius, 'hospital')
        transport = get_nearby_places(lat, lng, radius, 'transit_station')
        parks = get_nearby_places(lat, lng, radius, 'park')
        
        # Get additional location details from OpenStreetMap
        location_details = get_location_details(lat, lng, radius)
        
        # Calculate scores for each category (0-100)
        schools_score = calculate_category_score(schools, 'school')
        hospitals_score = calculate_category_score(hospitals, 'hospital')
        transport_score = calculate_category_score(transport, 'transport')
        
        # Calculate crime score (dummy implementation for now)
        crime_score = 75  # Default value, would be replaced with real data
        
        # Calculate green zones score
        green_zones_score = calculate_green_score(parks, location_details.get('green_areas', []))
        
        # Calculate development score
        development_score = calculate_development_score(location_details)
        
        # Calculate total score (weighted average)
        total_score = (
            schools_score * 0.2 + 
            hospitals_score * 0.15 + 
            transport_score * 0.2 + 
            crime_score * 0.2 + 
            green_zones_score * 0.1 + 
            development_score * 0.15
        )
        
        # Create location score object
        location_score = LocationScore(
            location=formatted_address,
            total_score=round(total_score, 1),
            schools_score=round(schools_score, 1),
            hospitals_score=round(hospitals_score, 1),
            transport_score=round(transport_score, 1),
            crime_score=round(crime_score, 1),
            green_zones_score=round(green_zones_score, 1),
            development_score=round(development_score, 1)
        )
        
        # Save score to database
        save_location_score(formatted_address, location_score)
        
        return jsonify({
            'status': 'success',
            'data': location_score.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error calculating location score: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to calculate location score: {str(e)}"
        }), 500

@bp.route('/compare', methods=['GET'])
def compare_locations():
    """
    Compare multiple locations based on their intelligence scores
    
    Query parameters:
    - locations: comma-separated list of locations
    - radius: int (optional, search radius in meters, default: 1000)
    """
    try:
        # Get query parameters
        locations_param = request.args.get('locations')
        radius = int(request.args.get('radius', 1000))
        
        # Validate required parameters
        if not locations_param:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: locations'
            }), 400
        
        # Split locations by comma
        locations = [loc.strip() for loc in locations_param.split(',')]
        
        # Get score for each location
        location_scores = []
        
        for location in locations:
            # First check if score exists in database
            cached_score = get_location_score(location)
            
            if cached_score:
                location_scores.append(cached_score.to_dict())
                continue
            
            # If not in database, geocode and calculate
            geocode_result = get_geocode(location)
            
            if not geocode_result:
                # Skip this location if geocoding fails
                logger.warning(f"Failed to geocode location: {location}")
                continue
            
            lat = geocode_result['lat']
            lng = geocode_result['lng']
            formatted_address = geocode_result['formatted_address']
            
            # Get nearby places for different categories
            schools = get_nearby_places(lat, lng, radius, 'school')
            hospitals = get_nearby_places(lat, lng, radius, 'hospital')
            transport = get_nearby_places(lat, lng, radius, 'transit_station')
            parks = get_nearby_places(lat, lng, radius, 'park')
            
            # Get additional location details from OpenStreetMap
            location_details = get_location_details(lat, lng, radius)
            
            # Calculate scores for each category
            schools_score = calculate_category_score(schools, 'school')
            hospitals_score = calculate_category_score(hospitals, 'hospital')
            transport_score = calculate_category_score(transport, 'transport')
            crime_score = 75  # Default value
            green_zones_score = calculate_green_score(parks, location_details.get('green_areas', []))
            development_score = calculate_development_score(location_details)
            
            # Calculate total score
            total_score = (
                schools_score * 0.2 + 
                hospitals_score * 0.15 + 
                transport_score * 0.2 + 
                crime_score * 0.2 + 
                green_zones_score * 0.1 + 
                development_score * 0.15
            )
            
            # Create location score object
            location_score = LocationScore(
                location=formatted_address,
                total_score=round(total_score, 1),
                schools_score=round(schools_score, 1),
                hospitals_score=round(hospitals_score, 1),
                transport_score=round(transport_score, 1),
                crime_score=round(crime_score, 1),
                green_zones_score=round(green_zones_score, 1),
                development_score=round(development_score, 1)
            )
            
            # Save score to database
            save_location_score(formatted_address, location_score)
            
            # Add to results
            location_scores.append(location_score.to_dict())
        
        return jsonify({
            'status': 'success',
            'data': location_scores
        })
    
    except Exception as e:
        logger.error(f"Error comparing locations: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to compare locations: {str(e)}"
        }), 500

@bp.route('/heatmap', methods=['GET'])
def get_heatmap_data():
    """
    Get heatmap data for a specific area
    
    Query parameters:
    - center: str (center point of the map, address or coordinates)
    - radius: int (optional, search radius in meters, default: 5000)
    - type: str (optional, type of heatmap: 'all', 'schools', 'hospitals', 'transport', 'crime', 'green', default: 'all')
    """
    try:
        # Get query parameters
        center = request.args.get('center')
        radius = int(request.args.get('radius', 5000))
        heatmap_type = request.args.get('type', 'all')
        
        # Validate required parameters
        if not center:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: center'
            }), 400
        
        # Geocode the center point
        geocode_result = get_geocode(center)
        
        if not geocode_result:
            return jsonify({
                'status': 'error',
                'message': 'Failed to geocode the center point'
            }), 400
        
        center_lat = geocode_result['lat']
        center_lng = geocode_result['lng']
        
        # Generate heatmap points based on type
        heatmap_points = []
        
        # Generate a grid of points within the radius
        grid_size = min(20, radius // 500)  # Limit grid size
        step_size = radius / grid_size
        
        for i in range(-grid_size, grid_size + 1):
            for j in range(-grid_size, grid_size + 1):
                # Calculate point coordinates
                point_lat = center_lat + (i * step_size / 111000)  # 111km per degree latitude
                point_lng = center_lng + (j * step_size / (111000 * math.cos(math.radians(center_lat))))
                
                # Check if point is within radius
                distance = haversine_distance(center_lat, center_lng, point_lat, point_lng)
                
                if distance <= radius:
                    # Calculate score for this point
                    if heatmap_type == 'all' or heatmap_type == 'schools':
                        schools = get_nearby_places(point_lat, point_lng, 1000, 'school')
                        schools_score = calculate_category_score(schools, 'school')
                    else:
                        schools_score = 0
                    
                    if heatmap_type == 'all' or heatmap_type == 'hospitals':
                        hospitals = get_nearby_places(point_lat, point_lng, 1000, 'hospital')
                        hospitals_score = calculate_category_score(hospitals, 'hospital')
                    else:
                        hospitals_score = 0
                    
                    if heatmap_type == 'all' or heatmap_type == 'transport':
                        transport = get_nearby_places(point_lat, point_lng, 1000, 'transit_station')
                        transport_score = calculate_category_score(transport, 'transport')
                    else:
                        transport_score = 0
                    
                    if heatmap_type == 'all' or heatmap_type == 'green':
                        parks = get_nearby_places(point_lat, point_lng, 1000, 'park')
                        location_details = get_location_details(point_lat, point_lng, 1000)
                        green_score = calculate_green_score(parks, location_details.get('green_areas', []))
                    else:
                        green_score = 0
                    
                    # Default crime score (would be replaced with real data)
                    crime_score = 75 if heatmap_type == 'all' or heatmap_type == 'crime' else 0
                    
                    # Calculate total score based on selected type
                    if heatmap_type == 'all':
                        total_score = (
                            schools_score * 0.2 + 
                            hospitals_score * 0.15 + 
                            transport_score * 0.2 + 
                            crime_score * 0.2 + 
                            green_score * 0.25
                        )
                    elif heatmap_type == 'schools':
                        total_score = schools_score
                    elif heatmap_type == 'hospitals':
                        total_score = hospitals_score
                    elif heatmap_type == 'transport':
                        total_score = transport_score
                    elif heatmap_type == 'crime':
                        total_score = crime_score
                    elif heatmap_type == 'green':
                        total_score = green_score
                    else:
                        total_score = 0
                    
                    # Add point to heatmap
                    heatmap_points.append({
                        'lat': point_lat,
                        'lng': point_lng,
                        'weight': total_score / 100  # Normalize to 0-1
                    })
        
        return jsonify({
            'status': 'success',
            'data': {
                'center': {'lat': center_lat, 'lng': center_lng},
                'radius': radius,
                'type': heatmap_type,
                'points': heatmap_points
            }
        })
    
    except Exception as e:
        logger.error(f"Error generating heatmap data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Failed to generate heatmap data: {str(e)}"
        }), 500

def calculate_category_score(places, category):
    """Calculate score for a category based on number and quality of places"""
    if not places:
        return 0
    
    # Calculate base score based on number of places
    if category == 'school':
        base_score = min(len(places) * 15, 85)
    elif category == 'hospital':
        base_score = min(len(places) * 20, 90)
    elif category == 'transport':
        base_score = min(len(places) * 10, 80)
    else:
        base_score = min(len(places) * 10, 70)
    
    # Adjust score based on average distance
    avg_distance = sum(place.get('distance', 1000) for place in places) / len(places)
    distance_factor = max(0, 1 - (avg_distance / 2000))  # Normalize to 0-1
    
    # Calculate final score
    score = base_score * (0.7 + 0.3 * distance_factor)
    
    return min(score, 100)  # Cap at 100

def calculate_green_score(parks, green_areas):
    """Calculate score for green zones"""
    # Combine parks from Google Maps with green areas from OpenStreetMap
    num_green_spaces = len(parks) + len(green_areas)
    
    # Calculate base score
    base_score = min(num_green_spaces * 12, 85)
    
    # Adjust score based on average distance
    distances = []
    for place in parks:
        distances.append(place.get('distance', 1000))
    for area in green_areas:
        distances.append(area.get('distance', 1000))
    
    if distances:
        avg_distance = sum(distances) / len(distances)
        distance_factor = max(0, 1 - (avg_distance / 2000))  # Normalize to 0-1
        
        # Calculate final score
        score = base_score * (0.7 + 0.3 * distance_factor)
    else:
        score = 0
    
    return min(score, 100)  # Cap at 100

def calculate_development_score(location_details):
    """Calculate development score based on amenities and infrastructure"""
    # Use walkability score from OpenStreetMap if available
    walkability = location_details.get('walkability_score', 0)
    
    # Count amenities
    amenities = location_details.get('amenities', [])
    num_amenities = len(amenities)
    
    # Calculate base score
    base_score = min(walkability, 90)  # Walkability is already 0-100
    
    # Adjust based on number of amenities
    amenity_factor = min(num_amenities / 20, 1)  # Normalize to 0-1
    
    # Calculate final score
    score = base_score * 0.7 + amenity_factor * 30
    
    return min(score, 100)  # Cap at 100

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters"""
    import math
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    # Return distance in meters
    return c * r * 1000