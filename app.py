from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
from services.weather_service import WeatherService
from services.ussd_service import USSDService

# Load environment variables
load_dotenv()

app = Flask(__name__)
weather_service = WeatherService()
ussd_service = USSDService()

# Web routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/weather', methods=['GET'])
def get_weather():
    location = request.args.get('location')
    if not location:
        return jsonify({'error': 'Location is required'}), 400
    
    weather_data = weather_service.get_weather(location)
    return jsonify(weather_data)

@app.route('/api/forecast', methods=['GET'])
def get_forecast():
    location = request.args.get('location')
    if not location:
        return jsonify({'error': 'Location is required'}), 400
    
    forecast_data = weather_service.get_forecast(location)
    return jsonify(forecast_data)

# USSD routes
@app.route('/ussd', methods=['POST'])
def ussd_callback():
    try:
        session_id = request.values.get("sessionId", "")
        service_code = request.values.get("serviceCode", "")
        phone_number = request.values.get("phoneNumber", "")
        text = request.values.get("text", "")
        
        # Process the USSD request
        response = ussd_service.handle_ussd(session_id, phone_number, text)
        return response
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error processing USSD request: {str(e)}")
        return "CON An error occurred. Please try again later."

if __name__ == '__main__':
    app.run(debug=True)


