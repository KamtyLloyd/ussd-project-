import africastalking
import os
from datetime import datetime, timedelta
from collections import Counter # For forecast condition summarization
from .weather_service import WeatherService

class USSDService:
    def __init__(self):
        self.session_data = {}
        self.weather_service = WeatherService()
        username = os.getenv('AFRICASTALKING_USERNAME')
        api_key = os.getenv('AFRICASTALKING_API_KEY')
        if not username or not api_key:
            raise ValueError('AfricasTalking credentials not found in environment variables')
        africastalking.initialize(username=username, api_key=api_key)
        self.ussd = africastalking.USSD

    def _initialize_session(self, session_id, phone_number):
        print(f"[DEBUG] Initializing session for {phone_number}, ID: {session_id}")
        self.session_data[session_id] = {
            'phone_number': phone_number,
            'current_menu': 'language', # Start with language selection
            'selected_location': 'Gulu', # Default location
            'session_start': datetime.now(),
            'last_activity': datetime.now(),
            'language': 'en', # Default language
            'language_selected': False
        }

    def handle_ussd(self, session_id, phone_number, text):
        """Handle USSD session requests"""
        print(f"[DEBUG] USSD Request - Session: {session_id}, Phone: {phone_number}, Text: '{text}'")

        if session_id not in self.session_data:
            self._initialize_session(session_id, phone_number)
            return self._get_language_menu()

        self.session_data[session_id]['last_activity'] = datetime.now()
        session_start_time = self.session_data[session_id]['session_start']
        if (datetime.now() - session_start_time).total_seconds() > 1800: # 30 minutes timeout
            print(f"[DEBUG] Session {session_id} timed out. Re-initializing.")
            self._initialize_session(session_id, phone_number) # Reset to language selection
            # Notify user of timeout and show language menu
            timeout_msg_en = "CON Session timed out. Please select your language again.\n"
            timeout_msg_luo = "CON Kinde mar tiyo gi wach otum. Bed iyer dho ki.\n" # Luo for session timeout
            # We don't know the language yet, so show a generic part of language menu or a combined message
            # For simplicity, just restart the language menu
            return self._get_language_menu()

        current_menu = self.session_data[session_id].get('current_menu', 'language')
        lang = self.session_data[session_id].get('language', 'en')

        full_input_string = text.strip() if text else ""
        input_parts = full_input_string.split('*')
        current_choice = input_parts[-1] if input_parts else ""

        # Handle global navigation first if language is selected
        if self.session_data[session_id].get('language_selected', False):
            if current_choice == "00" or current_choice == "*0":
                print(f"[DEBUG] Global navigation to main menu for session {session_id}")
                self.session_data[session_id]['current_menu'] = 'main'
                return self._show_main_menu(lang)
        
        # If language not selected, force to language selection (unless already there)
        if not self.session_data[session_id].get('language_selected', False) and current_menu != 'language':
            print(f"[DEBUG] Language not selected, forcing to language menu for session {session_id}")
            self.session_data[session_id]['current_menu'] = 'language'
            current_menu = 'language' # Update current_menu for routing below
            if not full_input_string: # If it was an empty string that led here, show menu
                 return self._get_language_menu()

        try:
            if current_menu == 'language':
                return self._handle_language_selection(session_id, current_choice)
            elif current_menu == 'main':
                return self._process_main_menu_selection(session_id, current_choice)
            elif current_menu == 'weather':
                return self._show_weather(session_id, current_choice)
            elif current_menu == 'forecast':
                return self._show_forecast(session_id, current_choice)
            elif current_menu == 'tips':
                return self._show_farming_tips(session_id, current_choice)
            else:
                # Fallback for unknown state
                print(f"[WARN] Unknown menu state '{current_menu}'. Resetting to language menu.")
                self.session_data[session_id]['current_menu'] = 'language'
                return self._get_language_menu(show_invalid=True)
        except Exception as e:
            print(f"[CRITICAL] Error in USSD handler: {str(e)}")
            import traceback
            traceback.print_exc()
            # Generic error message, as language might not be set or be incorrect
            return "END A technical error occurred. Please try again later."

    def _get_language_menu(self, show_invalid=False):
        response = """CON Select Language / Yer Dhok:
1. English
2. Dholuo
0. Exit / Wuok"""
        if show_invalid:
            # Generic invalid message as language isn't confirmed
            response = "CON Invalid selection. Please try again.\n\n" + response 
        return response

    def _handle_language_selection(self, session_id, text):
        if text == "1":
            self.session_data[session_id]['language'] = 'en'
            self.session_data[session_id]['language_selected'] = True
            self.session_data[session_id]['current_menu'] = 'main'
            return self._show_main_menu('en')
        elif text == "2":
            self.session_data[session_id]['language'] = 'luo'
            self.session_data[session_id]['language_selected'] = True
            self.session_data[session_id]['current_menu'] = 'main'
            return self._show_main_menu('luo')
        elif text == "0":
            return self._end_session(session_id) # Will use default or last lang
        else:
            return self._get_language_menu(show_invalid=True)

    def _show_main_menu(self, lang):
        if lang == 'luo':
            response = """CON Meny mar Loch (Gulu):
1. Nen Piny Kawuono
2. Nen Piny Ndege Adek
3. Puonj mag Puro
0. Wuok"""
        else:
            response = """CON Main Menu (Gulu):
1. Today's Weather
2. 3-Day Forecast
3. Farming Tips
0. Exit"""
        return response

    def _process_main_menu_selection(self, session_id, text):
        lang = self.session_data[session_id]['language']
        if text == "1":
            self.session_data[session_id]['current_menu'] = 'weather'
            return self._show_weather(session_id, "") # Pass empty text for initial display
        elif text == "2":
            self.session_data[session_id]['current_menu'] = 'forecast'
            return self._show_forecast(session_id, "") # Pass empty text
        elif text == "3":
            self.session_data[session_id]['current_menu'] = 'tips'
            return self._show_farming_tips(session_id, "") # Pass empty text
        elif text == "0":
            return self._end_session(session_id)
        else:
            # Invalid selection, show main menu again with error message
            error_msg = "CON Tic mogo. Tem kendo.\n\n" if lang == 'luo' else "CON Invalid selection. Try again.\n\n"
            return error_msg + self._show_main_menu(lang)

    def _get_farming_advice(self, weather_data, language='en'):
        temp = weather_data.get('temperature', 0)
        humidity = weather_data.get('humidity', 0)
        description = weather_data.get('description', '').lower()
        advice_list = []

        if language == 'luo':
            advice_intro = "PUONJ MAG PURO:\n" # FARMING TIPS
            if 'rain' in description or 'drizzle' in description or 'thunderstorm' in description:
                advice_list.append("- Kinde koth: Pidho cham kod povrigo. Ket laro ne pi.") # Rainy season: Plant crops and vegetables. Manage water runoff.
                advice_list.append("- Kinde koth: Ng'i kodi pile mondo kik two mar koth ogogi.") # Rainy season: Monitor crops regularly for rain-related diseases.
            elif temp > 28 or 'sun' in description or 'clear' in description:
                advice_list.append("- Kinde oro: Keyo cham mochek. Pwodhi kodi odhiambo kata gokinyi.") # Sunny/Dry season: Harvest mature crops. Irrigate in the evening or early morning.
                advice_list.append("- Kinde oro: Bed motang' gi kute/kuodi. Tim chenro mag kweroogi.") # Sunny/Dry season: Watch for pests. Implement pest control.
            else:
                advice_list.append("- Tim pur motegno. Luw chenro mar puro ni mondo iyud keyo mang'eny.") # General: Farm diligently. Follow your farming schedule for good yields.

            if humidity > 75 and not any('Piny obo' in adv for adv in advice_list):
                advice_list.append("- Piny obo ahinya. Ng'i kodi maber mondo two fungal kik donji.") # High humidity: Watch for fungal diseases.
            if temp < 18 and not ('rain' in description or 'drizzle' in description or 'thunderstorm' in description) and not any('Piny ng\'ich' in adv for adv in advice_list):
                advice_list.append("- Piny ng'ich matin. Rit kodi moko ma yotnegi koyo.") # Cool weather: Protect sensitive crops from cold.
            
            if not advice_list:
                advice_list.append("- Tim pur maber kendo luw puonj mag puro mapile.") # Default: Farm well and follow regular farming advice.
            return advice_intro + '\n'.join(advice_list)
        else: # English
            advice_intro = "FARMING TIPS:\n"
            if 'rain' in description or 'drizzle' in description or 'thunderstorm' in description:
                advice_list.append("- Rainy Season: Plant suitable crops and vegetables. Ensure good drainage.")
                advice_list.append("- Rainy Season: Monitor crops for diseases common in wet conditions.")
            elif temp > 28 or 'sun' in description or 'clear' in description:
                advice_list.append("- Sunny/Dry Season: Harvest mature crops. Irrigate efficiently, preferably in the evening or early morning.")
                advice_list.append("- Sunny/Dry Season: Implement pest control measures as needed.")
            else:
                advice_list.append("- General Conditions: Maintain your farm. Follow your planting and harvesting schedule.")

            if humidity > 75 and not any('High humidity' in adv for adv in advice_list):
                advice_list.append("- High humidity: Be vigilant for fungal diseases.")
            if temp < 18 and not ('rain' in description or 'drizzle' in description or 'thunderstorm' in description) and not any('Cool weather' in adv for adv in advice_list):
                advice_list.append("- Cool weather: Protect sensitive crops from potential cold damage.")

            if not advice_list:
                advice_list.append("- Practice good farming based on current conditions and your specific crop needs.")
            return advice_intro + '\n'.join(advice_list)
        
    def _show_farming_tips(self, session_id, text):
        lang = self.session_data[session_id]['language']
        if text == "0":
            self.session_data[session_id]['current_menu'] = 'main'
            return self._show_main_menu(lang)

        location = "Gulu"
        weather_data = self.weather_service.get_weather(location)
        back_option = "0. Wuok" if lang == 'luo' else "0. Main Menu"

        if 'error' in weather_data:
            error_msg = "CON Tye bal ka yudo wach piny.\n" if lang == 'luo' else "CON Error getting weather data.\n"
            return error_msg + back_option

        farming_advice = self._get_farming_advice(weather_data, lang)
        return "CON " + farming_advice + "\n" + back_option

    def _show_weather(self, session_id, text):
        lang = self.session_data[session_id]['language']
        if text == "0":
            self.session_data[session_id]['current_menu'] = 'main'
            return self._show_main_menu(lang)

        location = "Gulu"
        weather_data = self.weather_service.get_weather(location)
        back_option = "0. Wuok" if lang == 'luo' else "0. Main Menu"

        if 'error' in weather_data:
            error_msg = "CON Tye bal e neno piny.\n" if lang == 'luo' else "CON Error getting weather data.\n"
            return error_msg + back_option

        farming_advice = self._get_farming_advice(weather_data, lang)
        
        if lang == 'luo':
            response_text = f"Piny e Gulu Kawuono:\n"
            response_text += f"Liet: {weather_data.get('temperature', 'N/A')}°C\n"
            response_text += f"Kit Piny: {weather_data.get('description', 'N/A')}\n"
            response_text += f"Um: {weather_data.get('humidity', 'N/A')}%\n"
            if 'wind_speed' in weather_data:
                response_text += f"Yamo: {weather_data['wind_speed']} m/s\n"
            response_text += f"\n{farming_advice}"
        else:
            response_text = f"Weather in {location} Today:\n"
            response_text += f"Temperature: {weather_data.get('temperature', 'N/A')}°C\n"
            response_text += f"Conditions: {weather_data.get('description', 'N/A')}\n"
            response_text += f"Humidity: {weather_data.get('humidity', 'N/A')}%\n"
            if 'wind_speed' in weather_data:
                response_text += f"Wind: {weather_data['wind_speed']} m/s\n"
            response_text += f"\n{farming_advice}"
        
        return "CON " + response_text + "\n" + back_option

    def _show_forecast(self, session_id, text):
        lang = self.session_data[session_id]['language']
        if text == "0":
            self.session_data[session_id]['current_menu'] = 'main'
            return self._show_main_menu(lang)

        location = "Gulu"
        forecast_data = self.weather_service.get_forecast(location)
        back_option = "0. Wuok" if lang == 'luo' else "0. Main Menu"

        if 'error' in forecast_data or not forecast_data.get('forecast'):
            error_msg = "CON Tye bal e yudo wach piny ma odiechieng.\n" if lang == 'luo' else "CON Error getting forecast data.\n"
            return error_msg + back_option

        response_text = f"Piny Ndege Adek ({location}):\n" if lang == 'luo' else f"3-Day Forecast ({location}):\n"
        
        processed_dates = set()
        days_shown = 0

        for forecast_item in forecast_data['forecast']:
            if days_shown >= 3: break
            
            dt_obj = datetime.strptime(forecast_item['dt_txt'], '%Y-%m-%d %H:%M:%S')
            current_date = dt_obj.date()

            if current_date in processed_dates:
                continue # Already processed this date
            
            # Filter forecasts for this specific day
            day_forecasts = [f for f in forecast_data['forecast'] if datetime.strptime(f['dt_txt'], '%Y-%m-%d %H:%M:%S').date() == current_date]
            if not day_forecasts: continue

            min_temp = min(f['main']['temp_min'] for f in day_forecasts)
            max_temp = max(f['main']['temp_max'] for f in day_forecasts)
            
            conditions = Counter(f['weather'][0]['description'] for f in day_forecasts)
            most_common_condition = conditions.most_common(1)[0][0].capitalize()
            
            day_name_en = dt_obj.strftime('%a, %b %d') # English day name
            day_name_luo_map = {
                'Mon': 'Wuok Tich',
                'Tue': 'Tich Ariyo',
                'Wed': 'Tich Adek',
                'Thu': 'Tich Angwen',
                'Fri': 'Tich Abich',
                'Sat': 'Ngeso',
                'Sun': 'Jumapil'
            }
            day_abbrev_en = dt_obj.strftime('%a')
            day_name_luo_prefix = day_name_luo_map.get(day_abbrev_en, day_abbrev_en)
            day_name_luo = f"{day_name_luo_prefix}, {dt_obj.strftime('%b %d')}" # Luo day name format

            formatted_date = day_name_luo if lang == 'luo' else day_name_en
            temp_label = "Liet" if lang == 'luo' else "Temp"

            response_text += f"{formatted_date}: {temp_label}: {min_temp:.0f}°C-{max_temp:.0f}°C, {most_common_condition}\n"
            processed_dates.add(current_date)
            days_shown += 1
            
        if days_shown == 0:
            response_text += "Dongruok mar piny onge.\n" if lang == 'luo' else "No forecast data available.\n"

        return "CON " + response_text + "\n" + back_option

    def _end_session(self, session_id):
        lang = self.session_data.get(session_id, {}).get('language', 'en') # Safely get language
        if session_id in self.session_data:
            del self.session_data[session_id]
            print(f"[DEBUG] Session {session_id} ended and removed.")
        
        if lang == 'luo':
            return "END Aparo pi tiyo kodwa. Med ameda maber!"
        else:
            return "END Thank you for using Farmer Weather Service!"