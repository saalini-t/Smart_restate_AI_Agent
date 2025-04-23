from datetime import datetime
from typing import List, Dict, Any, Optional

class EconomicIndicator:
    """Model for economic indicators like interest rates, inflation, GDP"""
    def __init__(self, 
                 indicator_type: str, 
                 value: float, 
                 date: datetime, 
                 country: str, 
                 forecast: Optional[float] = None,
                 source: str = "Trading Economics"):
        self.indicator_type = indicator_type
        self.value = value
        self.date = date
        self.country = country
        self.forecast = forecast
        self.source = source
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'indicator_type': self.indicator_type,
            'value': self.value,
            'date': self.date.isoformat(),
            'country': self.country,
            'forecast': self.forecast,
            'source': self.source
        }

class PropertyPrice:
    """Model for property price data and forecasts"""
    def __init__(self,
                 location: str,
                 price: float,
                 date: datetime,
                 property_type: str,
                 predicted_price: Optional[float] = None,
                 confidence: Optional[float] = None):
        self.location = location
        self.price = price
        self.date = date
        self.property_type = property_type
        self.predicted_price = predicted_price
        self.confidence = confidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'location': self.location,
            'price': self.price,
            'date': self.date.isoformat(),
            'property_type': self.property_type,
            'predicted_price': self.predicted_price,
            'confidence': self.confidence
        }

class LocationScore:
    """Model for location intelligence scoring"""
    def __init__(self,
                 location: str,
                 total_score: float,
                 schools_score: float,
                 hospitals_score: float,
                 transport_score: float,
                 crime_score: float,
                 green_zones_score: float,
                 development_score: float):
        self.location = location
        self.total_score = total_score
        self.schools_score = schools_score
        self.hospitals_score = hospitals_score
        self.transport_score = transport_score
        self.crime_score = crime_score
        self.green_zones_score = green_zones_score
        self.development_score = development_score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'location': self.location,
            'total_score': self.total_score,
            'schools_score': self.schools_score,
            'hospitals_score': self.hospitals_score,
            'transport_score': self.transport_score,
            'crime_score': self.crime_score,
            'green_zones_score': self.green_zones_score,
            'development_score': self.development_score
        }

class InvestmentRecommendation:
    """Model for investment timing recommendations"""
    def __init__(self,
                 location: str,
                 recommendation: str,
                 confidence: float,
                 price_forecast: List[Dict[str, Any]],
                 optimal_time: Optional[str] = None,
                 roi_estimate: Optional[float] = None):
        self.location = location
        self.recommendation = recommendation
        self.confidence = confidence
        self.price_forecast = price_forecast
        self.optimal_time = optimal_time
        self.roi_estimate = roi_estimate
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'location': self.location,
            'recommendation': self.recommendation,
            'confidence': self.confidence,
            'price_forecast': self.price_forecast,
            'optimal_time': self.optimal_time,
            'roi_estimate': self.roi_estimate
        }

class ConstructionPlan:
    """Model for construction planning information"""
    def __init__(self,
                 location: str,
                 optimal_start_date: str,
                 material_prices: Dict[str, float],
                 weather_forecast: List[Dict[str, Any]],
                 estimated_cost: float):
        self.location = location
        self.optimal_start_date = optimal_start_date
        self.material_prices = material_prices
        self.weather_forecast = weather_forecast
        self.estimated_cost = estimated_cost
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'location': self.location,
            'optimal_start_date': self.optimal_start_date,
            'material_prices': self.material_prices,
            'weather_forecast': self.weather_forecast,
            'estimated_cost': self.estimated_cost
        }