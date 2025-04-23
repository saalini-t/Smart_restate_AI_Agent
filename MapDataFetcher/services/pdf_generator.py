import logging
import io
import os
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from services.database import get_property_history, get_economic_indicators, get_location_score
from services.ml_models import forecast_market_direction, predict_property_prices

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_chart(data, title, xlabel, ylabel, filename):
    """Generate a chart using matplotlib and save to a temporary file"""
    plt.figure(figsize=(8, 4))
    
    # If data is a dictionary with 'dates' and 'values' keys
    if isinstance(data, dict) and 'dates' in data and 'values' in data:
        plt.plot(data['dates'], data['values'])
    # If data is a list of dictionaries with 'date' and 'value' keys
    elif isinstance(data, list) and all('date' in d and 'value' in d for d in data):
        dates = [d['date'] for d in data]
        values = [d['value'] for d in data]
        plt.plot(dates, values)
    # If data is a list of numeric values
    else:
        plt.plot(data)
    
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    
    # Save chart to a temporary file
    plt.savefig(filename)
    plt.close()
    return filename

def generate_dashboard_pdf(user_id, location='United States', include_economic_data=True, 
                          include_property_data=True, include_predictions=True, timeframe='1y'):
    """
    Generate a PDF report of dashboard data
    
    Args:
        user_id (str): User identifier
        location (str): Location for property data
        include_economic_data (bool): Whether to include economic indicators
        include_property_data (bool): Whether to include property data
        include_predictions (bool): Whether to include future predictions
        timeframe (str): Time period to cover (1m, 3m, 6m, 1y, 5y)
        
    Returns:
        bytes: PDF file data
    """
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    story = []
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        alignment=TA_LEFT,
        spaceAfter=6
    )
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.gray
    )
    
    # Add header
    story.append(Paragraph("Smart Estate Compass", title_style))
    story.append(Paragraph("Market Intelligence Dashboard Report", subtitle_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", date_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Add location info
    if location and location != 'United States':
        story.append(Paragraph(f"Location: {location}", styles['Heading3']))
    else:
        story.append(Paragraph(f"United States Market Overview", styles['Heading3']))
    story.append(Spacer(1, 0.25*inch))
    
    # Include economic data if requested
    if include_economic_data:
        story.append(Paragraph("Economic Indicators", subtitle_style))
        
        # Get economic data
        end_date = datetime.now()
        if timeframe == '1m':
            start_date = end_date.replace(month=end_date.month-1 if end_date.month > 1 else 12)
        elif timeframe == '3m':
            start_date = end_date.replace(month=end_date.month-3 if end_date.month > 3 else end_date.month+9)
        elif timeframe == '6m':
            start_date = end_date.replace(month=end_date.month-6 if end_date.month > 6 else end_date.month+6)
        elif timeframe == '5y':
            start_date = end_date.replace(year=end_date.year-5)
        else:  # Default to 1y
            start_date = end_date.replace(year=end_date.year-1)
        
        interest_rates = get_economic_indicators('interest-rate', start_date, end_date)
        inflation_data = get_economic_indicators('inflation-rate', start_date, end_date)
        gdp_data = get_economic_indicators('gdp-growth', start_date, end_date)
        
        # Create and add economic indicators table
        economic_data = [
            ["Indicator", "Current Value", "Change (1 Month)", "Trend"],
            ["Interest Rate", f"{interest_rates[-1].value:.2f}%" if interest_rates else "N/A", 
             f"{interest_rates[-1].value - interest_rates[-2].value:.2f}%" if len(interest_rates) > 1 else "N/A", 
             "↑" if len(interest_rates) > 1 and interest_rates[-1].value > interest_rates[-2].value else "↓"],
            ["Inflation Rate", f"{inflation_data[-1].value:.2f}%" if inflation_data else "N/A", 
             f"{inflation_data[-1].value - inflation_data[-2].value:.2f}%" if len(inflation_data) > 1 else "N/A", 
             "↑" if len(inflation_data) > 1 and inflation_data[-1].value > inflation_data[-2].value else "↓"],
            ["GDP Growth", f"{gdp_data[-1].value:.2f}%" if gdp_data else "N/A", 
             f"{gdp_data[-1].value - gdp_data[-2].value:.2f}%" if len(gdp_data) > 1 else "N/A", 
             "↑" if len(gdp_data) > 1 and gdp_data[-1].value > gdp_data[-2].value else "↓"]
        ]
        
        table = Table(economic_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 0.25*inch))
        
        # Generate market forecast if we have data
        if interest_rates and inflation_data and gdp_data:
            market_forecast = forecast_market_direction(interest_rates, inflation_data, gdp_data)
            story.append(Paragraph(f"Market Direction: {market_forecast.get('direction', 'stable').title()} (Confidence: {market_forecast.get('confidence', 0)*100:.0f}%)", styles['Normal']))
            story.append(Spacer(1, 0.25*inch))
    
    # Include property data if requested and location is specific
    if include_property_data and location and location != 'United States':
        story.append(Paragraph(f"Property Market in {location}", subtitle_style))
        
        # Get property price history
        property_history = get_property_history(location, period=timeframe)
        
        if property_history:
            # Calculate average price
            avg_price = sum(p.price for p in property_history) / len(property_history)
            # Calculate 3-month change
            recent_change = (property_history[-1].price - property_history[0].price) / property_history[0].price * 100 if len(property_history) > 1 else 0
            
            story.append(Paragraph(f"Average Property Price: ${avg_price:,.2f}", styles['Normal']))
            story.append(Paragraph(f"Recent Change: {recent_change:.2f}%", styles['Normal']))
            story.append(Spacer(1, 0.25*inch))
        
        # Add location intelligence score if available
        location_score = get_location_score(location)
        if location_score:
            story.append(Paragraph("Location Intelligence Score", subtitle_style))
            
            # Create and add location score table
            score_data = [
                ["Category", "Score (out of 100)"],
                ["Overall", f"{location_score.total_score:.1f}"],
                ["Schools", f"{location_score.schools_score:.1f}"],
                ["Healthcare", f"{location_score.hospitals_score:.1f}"],
                ["Transportation", f"{location_score.transport_score:.1f}"],
                ["Safety", f"{location_score.crime_score:.1f}"],
                ["Green Spaces", f"{location_score.green_zones_score:.1f}"],
                ["Development", f"{location_score.development_score:.1f}"]
            ]
            
            table = Table(score_data, colWidths=[2.5*inch, 2.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 0.25*inch))
    
    # Include predictions if requested
    if include_predictions and location and location != 'United States':
        story.append(Paragraph("Price Predictions", subtitle_style))
        
        # Predict property prices for residential and commercial
        residential_prediction = predict_property_prices(
            location=location,
            property_type='residential',
            area_sqft=2000,
            bedrooms=3,
            bathrooms=2,
            forecast_period='1y'
        )
        
        commercial_prediction = predict_property_prices(
            location=location,
            property_type='commercial',
            area_sqft=5000,
            forecast_period='1y'
        )
        
        # Add residential prediction
        if residential_prediction:
            story.append(Paragraph(f"Residential Property (2000 sq ft, 3bd/2ba):", styles['Normal']))
            story.append(Paragraph(f"Current Estimated Price: ${residential_prediction['current_price']:,.2f} (${residential_prediction['price_per_sqft']:.2f}/sq ft)", styles['Normal']))
            story.append(Paragraph(f"12-Month Growth Forecast: {(residential_prediction['forecast'][-1]['price'] - residential_prediction['current_price']) / residential_prediction['current_price'] * 100:.2f}%", styles['Normal']))
            story.append(Paragraph(f"Market Assessment: {residential_prediction['market_assessment']['assessment'].title()} ({residential_prediction['market_assessment']['percentage']}%)", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Add commercial prediction
        if commercial_prediction:
            story.append(Paragraph(f"Commercial Property (5000 sq ft):", styles['Normal']))
            story.append(Paragraph(f"Current Estimated Price: ${commercial_prediction['current_price']:,.2f} (${commercial_prediction['price_per_sqft']:.2f}/sq ft)", styles['Normal']))
            story.append(Paragraph(f"12-Month Growth Forecast: {(commercial_prediction['forecast'][-1]['price'] - commercial_prediction['current_price']) / commercial_prediction['current_price'] * 100:.2f}%", styles['Normal']))
            story.append(Paragraph(f"Market Assessment: {commercial_prediction['market_assessment']['assessment'].title()} ({commercial_prediction['market_assessment']['percentage']}%)", styles['Normal']))
        
        story.append(Spacer(1, 0.25*inch))
    
    # Add disclaimer
    story.append(Paragraph("DISCLAIMER: This report is for informational purposes only and should not be considered as financial advice. Market conditions can change rapidly, and all investment decisions should be made after consulting with a qualified financial advisor.", styles['Normal']))
    
    # Build the PDF
    doc.build(story)
    
    # Get the PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def generate_report_pdf(location, property_type, property_details=None, include_location_score=True, 
                       include_price_prediction=True, include_investment_analysis=True):
    """
    Generate a detailed PDF report for a specific property
    
    Args:
        location (str): Property location
        property_type (str): Type of property (residential, commercial, land)
        property_details (dict): Property details like address, sqft, etc.
        include_location_score (bool): Whether to include location intelligence
        include_price_prediction (bool): Whether to include price predictions
        include_investment_analysis (bool): Whether to include investment analysis
        
    Returns:
        bytes: PDF file data
    """
    buffer = io.BytesIO()
    
    # Default property details if not provided
    if not property_details:
        property_details = {
            'address': f"Sample Property in {location}",
            'area_sqft': 2000 if property_type == 'residential' else 5000,
            'bedrooms': 3 if property_type == 'residential' else None,
            'bathrooms': 2 if property_type == 'residential' else None,
            'year_built': 2010
        }
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    story = []
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        alignment=TA_LEFT,
        spaceAfter=6
    )
    
    # Add header
    story.append(Paragraph("Property Analysis Report", title_style))
    story.append(Paragraph(f"Generated by Smart Estate Compass on {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Add property details
    story.append(Paragraph("Property Details", subtitle_style))
    
    # Create property details table
    details_data = [
        ["Address", property_details.get('address', f"Property in {location}")],
        ["Location", location],
        ["Property Type", property_type.capitalize()],
        ["Area", f"{property_details.get('area_sqft', 'N/A'):,} sq ft"]
    ]
    
    if property_type == 'residential':
        details_data.extend([
            ["Bedrooms", str(property_details.get('bedrooms', 'N/A'))],
            ["Bathrooms", str(property_details.get('bathrooms', 'N/A'))]
        ])
    
    if property_details.get('year_built'):
        details_data.append(["Year Built", str(property_details.get('year_built'))])
    
    table = Table(details_data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 0.25*inch))
    
    # Add location intelligence if requested
    if include_location_score:
        story.append(Paragraph("Location Analysis", subtitle_style))
        
        # Get location score
        location_score = get_location_score(location)
        
        if location_score:
            # Create location score table
            score_data = [
                ["Category", "Score (out of 100)"],
                ["Overall", f"{location_score.total_score:.1f}"],
                ["Schools", f"{location_score.schools_score:.1f}"],
                ["Healthcare", f"{location_score.hospitals_score:.1f}"],
                ["Transportation", f"{location_score.transport_score:.1f}"],
                ["Safety", f"{location_score.crime_score:.1f}"],
                ["Green Spaces", f"{location_score.green_zones_score:.1f}"],
                ["Development", f"{location_score.development_score:.1f}"]
            ]
            
            table = Table(score_data, colWidths=[3*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            
            # Add location assessment
            if location_score.total_score >= 80:
                assessment = "Excellent location with outstanding amenities and infrastructure."
            elif location_score.total_score >= 70:
                assessment = "Very good location with solid amenities and infrastructure."
            elif location_score.total_score >= 60:
                assessment = "Good location with adequate amenities and infrastructure."
            elif location_score.total_score >= 50:
                assessment = "Average location with some amenities and infrastructure."
            else:
                assessment = "Below average location with limited amenities and infrastructure."
            
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(f"Assessment: {assessment}", styles['Normal']))
            story.append(Spacer(1, 0.25*inch))
    
    # Add price prediction if requested
    if include_price_prediction:
        story.append(Paragraph("Price Analysis & Forecast", subtitle_style))
        
        # Get property prediction
        price_prediction = predict_property_prices(
            location=location,
            property_type=property_type,
            area_sqft=property_details.get('area_sqft', 2000),
            bedrooms=property_details.get('bedrooms'),
            bathrooms=property_details.get('bathrooms'),
            year_built=property_details.get('year_built'),
            forecast_period='1y'
        )
        
        if price_prediction:
            # Add current valuation
            story.append(Paragraph(f"Current Estimated Value: ${price_prediction['current_price']:,.2f}", styles['Normal']))
            story.append(Paragraph(f"Price per Square Foot: ${price_prediction['price_per_sqft']:.2f}", styles['Normal']))
            story.append(Paragraph(f"Market Assessment: {price_prediction['market_assessment']['assessment'].title()} ({price_prediction['market_assessment']['percentage']}%)", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            # Add forecast table
            forecast_data = [["Month", "Predicted Price", "Change"]]
            prev_price = price_prediction['current_price']
            
            for forecast in price_prediction['forecast']:
                month = forecast['date']
                price = forecast['price']
                change = forecast['change_pct']
                forecast_data.append([month, f"${price:,.2f}", f"{change:.2f}%"])
                prev_price = price
            
            table = Table(forecast_data, colWidths=[1.5*inch, 2.5*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 0.25*inch))
    
    # Add investment analysis if requested
    if include_investment_analysis:
        story.append(Paragraph("Investment Analysis", subtitle_style))
        
        # Calculate basic ROI for different strategies
        if price_prediction:
            current_price = price_prediction['current_price']
            future_price = price_prediction['forecast'][-1]['price']
            appreciation = (future_price - current_price) / current_price * 100
            
            # Estimated monthly rent based on property type and value
            monthly_rent = current_price * 0.005 if property_type == 'residential' else current_price * 0.008
            monthly_expenses = monthly_rent * 0.3  # Estimated expenses as 30% of rent
            
            # ROI calculations
            flip_roi = appreciation - 6  # Account for transaction costs
            rental_roi = ((monthly_rent - monthly_expenses) * 12) / current_price * 100
            hold_long_term_roi = appreciation * 1.5  # Estimated 5-year appreciation
            
            # Create ROI table
            roi_data = [
                ["Investment Strategy", "Estimated Annual ROI", "Notes"],
                ["Flip (1 year)", f"{flip_roi:.2f}%", "Sell after market appreciation"],
                ["Rental Income", f"{rental_roi:.2f}%", f"Monthly income: ${monthly_rent - monthly_expenses:,.2f}"],
                ["Long-term Hold (5 years)", f"{hold_long_term_roi:.2f}%", "Based on projected appreciation"]
            ]
            
            table = Table(roi_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            
            # Investment recommendation based on ROI
            best_roi = max(flip_roi, rental_roi, hold_long_term_roi)
            if best_roi == flip_roi:
                recommendation = "Short-term flip"
            elif best_roi == rental_roi:
                recommendation = "Rental property"
            else:
                recommendation = "Long-term hold"
            
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(f"Recommended Strategy: {recommendation}", styles['Normal']))
            story.append(Spacer(1, 0.25*inch))
    
    # Add disclaimer
    story.append(Paragraph("DISCLAIMER: This report is for informational purposes only and should not be considered as financial advice. Property values can change based on numerous factors not accounted for in this analysis. All investment decisions should be made after consulting with a qualified real estate professional and financial advisor.", styles['Normal']))
    
    # Build the PDF
    doc.build(story)
    
    # Get the PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data