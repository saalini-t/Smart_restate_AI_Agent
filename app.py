import os
import logging
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "smart-estate-compass-secret")

# Enable CORS for the React frontend
CORS(app)

# Import and register routes
from routes import economic_trends, property_price, location_intelligence, investment_timing, construction_planning
from routes import roi_calculator, alert_system, dashboard

# Initialize notification service if app is available
from services.notification import init_mail_app
init_mail_app(app)

# Register blueprints
app.register_blueprint(economic_trends.bp)
app.register_blueprint(property_price.bp)
app.register_blueprint(location_intelligence.bp)
app.register_blueprint(investment_timing.bp)
app.register_blueprint(construction_planning.bp)
app.register_blueprint(roi_calculator.bp)
app.register_blueprint(alert_system.bp)
app.register_blueprint(dashboard.bp)

# Web routes
@app.route('/')
def index():
    return render_template('index.html')

# API info route
@app.route('/api')
def api_info():
    return jsonify({
        'status': 'success',
        'message': 'Smart Estate Compass API is running',
        'endpoints': [
            '/api/economic-trends',
            '/api/property-price',
            '/api/location-intelligence',
            '/api/investment-timing',
            '/api/construction-planning',
            '/api/roi-calculator',
            '/api/alerts',
            '/api/dashboard'
        ]
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return {'status': 'error', 'message': 'Not found'}, 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Internal error: {error}")
    return {'status': 'error', 'message': 'Internal server error'}, 500
