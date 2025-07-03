# Farmer Weather Information System (FWIS)

A dual-platform system that provides farmers with daily weather forecasts and agricultural insights through both web interface and USSD technology.

## Features

- Web-based weather information system
- USSD-based weather information access
- Location-based weather forecasting
- Agricultural insights based on weather conditions
- Multi-language support
- Offline-capable USSD access

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a .env file with the following variables:
```
OPENWEATHERMAP_API_KEY=your_api_key
AFRICASTALKING_USERNAME=your_username
AFRICASTALKING_API_KEY=your_api_key
```

3. Run the application:
```bash
python app.py
```

## Project Structure

- `app/` - Main application code
  - `web/` - Web application components
  - `ussd/` - USSD application components
  - `services/` - External service integrations
  - `utils/` - Utility functions
- `tests/` - Test files
- `static/` - Static assets
- `templates/` - HTML templates

## API Keys Required

- OpenWeatherMap API Key
- Africa's Talking API Key

## License

MIT License
