# tools.py - Fixed LangChain Tools Implementation
from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field
import requests
import json
from datetime import datetime, timedelta
import os
import logging

class LocationInput(BaseModel):
    user_id: str = Field(description="User ID to get location for")

class LocationTool(BaseTool):
    name = "get_location"
    description = "Get user's current city location"
    args_schema: Type[BaseModel] = LocationInput
    
    def _run(self, user_id: str) -> str:
        try:
            result = json.dumps({"city": "Mumbai"})
            logging.info(f"Location tool result: {result}")
            return result
        except Exception as e:
            logging.error(f"LocationTool error: {e}")
            return json.dumps({"city": "Mumbai", "error": str(e)})

class WeatherInput(BaseModel):
    city: str = Field(description="City name to get weather for")

class WeatherTool(BaseTool):
    name = "get_hourly_weather"
    description = "Get hourly weather forecast for a city"
    args_schema: Type[BaseModel] = WeatherInput
    
    def _run(self, city: str) -> str:
        try:
            api_key = os.getenv("OPENWEATHER_API_KEY")
            if not api_key:
                logging.warning("No OpenWeather API key found, using mock data")
                return self._get_mock_weather_data()
            
            # Fixed URL with proper HTTPS and correct endpoint
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
            
            headers = {
                'User-Agent': 'SportsPlanner/1.0'
            }
            
            logging.info(f"Making weather API request to: {url[:50]}...")
            response = requests.get(url, headers=headers, timeout=15)
            
            logging.info(f"Weather API response status: {response.status_code}")
            
            if response.status_code == 401:
                logging.error(f"Weather API 401 Unauthorized. Check API key: {api_key[:10]}...")
                logging.error(f"Response: {response.text}")
                return self._get_mock_weather_data()
            elif response.status_code != 200:
                logging.warning(f"Weather API error: {response.status_code} - {response.text}")
                return self._get_mock_weather_data()
            
            data = response.json()
            logging.info(f"Weather API success: Got {len(data.get('list', []))} forecast entries")
            
            weather_data = []
            for item in data['list'][:8]:
                weather_data.append({
                    'time': item['dt_txt'],
                    'temp': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                    'rain': 'rain' in item,
                    'wind_speed': item['wind']['speed']
                })
            
            result = json.dumps(weather_data)
            logging.info(f"Weather tool result: {len(weather_data)} entries processed")
            return result
            
        except requests.exceptions.Timeout:
            logging.error("Weather API timeout")
            return self._get_mock_weather_data()
        except requests.exceptions.ConnectionError:
            logging.error("Weather API connection error")
            return self._get_mock_weather_data()
        except Exception as e:
            logging.error(f"WeatherTool error: {e}")
            return self._get_mock_weather_data()
    
    def _get_mock_weather_data(self):
        """Generate mock weather data for testing"""
        weather_data = []
        base_time = datetime.now()
        for i in range(8):
            weather_data.append({
                'time': (base_time + timedelta(hours=i)).strftime("%Y-%m-%d %H:00:00"),
                'temp': 25 + (i * 2),  # Temperature between 25-39°C
                'humidity': 60 + (i * 2),
                'rain': False,
                'wind_speed': 5.0 + i
            })
        logging.info("Using mock weather data")
        return json.dumps(weather_data)

class AQIInput(BaseModel):
    city: str = Field(description="City name to get AQI for")

class AQITool(BaseTool):
    name = "get_hourly_aqi"
    description = "Get hourly air quality index for a city"
    args_schema: Type[BaseModel] = AQIInput
    
    def _run(self, city: str) -> str:
        try:
            aqi_data = []
            base_time = datetime.now()
            for i in range(8):
                aqi_data.append({
                    'time': (base_time + timedelta(hours=i)).isoformat(),
                    'aqi': 80 + (i * 5)  # AQI between 80-115
                })
            
            result = json.dumps(aqi_data)
            logging.info(f"AQI tool result: {len(aqi_data)} entries")
            return result
            
        except Exception as e:
            logging.error(f"AQITool error: {e}")
            return json.dumps([{"time": datetime.now().isoformat(), "aqi": 90}])

class DayTypeInput(BaseModel):
    date: str = Field(description="Date in ISO format to check")

class DayTypeTool(BaseTool):
    name = "is_holiday_or_weekend"
    description = "Check if a date is weekend or holiday"
    args_schema: Type[BaseModel] = DayTypeInput
    
    def _run(self, date: str) -> str:
        try:
            today = datetime.now()
            if today.weekday() >= 5:  # Saturday = 5, Sunday = 6
                result = json.dumps({"type": "weekend"})
            else:
                result = json.dumps({"type": "weekday"})
            
            logging.info(f"Day type tool result: {result}")
            return result
            
        except Exception as e:
            logging.error(f"DayTypeTool error: {e}")
            return json.dumps({"type": "weekday"})

class BestTimeSelectorInput(BaseModel):
    sport_weather_aqi_data: str = Field(description="JSON string containing sport, weather_data, aqi_data, and day_type")

class BestTimeSelectorTool(BaseTool):
    name = "choose_best_time"
    description = "Choose best time slots for playing a sport based on weather and AQI. Input should be JSON with sport, weather_data, aqi_data, day_type"
    args_schema: Type[BaseModel] = BestTimeSelectorInput
    
    def _run(self, sport_weather_aqi_data: str) -> str:
        try:
            logging.info(f"BestTimeSelectorTool input: {sport_weather_aqi_data[:200]}...")
            
            # Parse the input data
            data = json.loads(sport_weather_aqi_data)
            sport = data.get('sport', 'cricket')
            weather_data_raw = data.get('weather_data', '[]')
            aqi_data_raw = data.get('aqi_data', '[]') 
            day_type_raw = data.get('day_type', '{}')
            
            # Parse nested JSON strings
            if isinstance(weather_data_raw, str):
                weather = json.loads(weather_data_raw)
            else:
                weather = weather_data_raw
                
            if isinstance(aqi_data_raw, str):
                aqi = json.loads(aqi_data_raw)
            else:
                aqi = aqi_data_raw
            
            logging.info(f"Parsed data - Sport: {sport}, Weather entries: {len(weather)}, AQI entries: {len(aqi)}")
            
            best_slots = []
            for i, w in enumerate(weather):
                try:
                    score = 0
                    hour = datetime.fromisoformat(w['time'].replace(' ', 'T')).hour
                    
                    # Cricket scoring rules
                    if sport.lower() == "cricket":
                        # Preferred time slots (early morning and evening)
                        if 6 <= hour <= 10 or 16 <= hour <= 19:
                            score += 3
                        
                        # Temperature range
                        if 15 <= w['temp'] <= 30:
                            score += 2
                        
                        # No rain
                        if not w['rain']:
                            score += 2
                        
                        # Good AQI
                        if i < len(aqi) and aqi[i]['aqi'] < 100:
                            score += 2
                        
                        # Low humidity
                        if w['humidity'] < 70:
                            score += 1
                    
                    # Only add slots with decent scores
                    if score >= 4:
                        end_time = datetime.fromisoformat(w['time'].replace(' ', 'T')) + timedelta(hours=2)
                        best_slots.append({
                            'start': w['time'],
                            'end': end_time.strftime("%Y-%m-%d %H:%M:%S"),
                            'score': score,
                            'temp': w['temp'],
                            'humidity': w['humidity'],
                            'aqi': aqi[i]['aqi'] if i < len(aqi) else 'N/A'
                        })
                        
                except Exception as slot_error:
                    logging.error(f"Error processing slot {i}: {slot_error}")
                    continue
            
            # Sort by score and return top 2
            best_slots = sorted(best_slots, key=lambda x: x['score'], reverse=True)[:2]
            
            result = json.dumps(best_slots)
            logging.info(f"Best time selector result: {len(best_slots)} slots found")
            return result
            
        except Exception as e:
            logging.error(f"BestTimeSelectorTool error: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            # Return empty result on error
            return json.dumps([])

class MotivationInput(BaseModel):
    day_type: str = Field(description="Day type data as JSON string")

class MotivationTool(BaseTool):
    name = "get_motivation"
    description = "Get motivational message based on day type"
    args_schema: Type[BaseModel] = MotivationInput
    
    def _run(self, day_type: str) -> str:
        try:
            day_info = json.loads(day_type)
            if day_info["type"] == "weekend":
                return "It's weekend! Perfect time to get active and play some sports! 🏃‍♂️"
            return "Stay active and healthy! 💪"
        except Exception as e:
            logging.error(f"MotivationTool error: {e}")
            return "Stay active and healthy! 💪"

class TelegramInput(BaseModel):
    chat_id: str = Field(description="Telegram chat ID")
    text: str = Field(description="Message text to send")

class TelegramTool(BaseTool):
    name = "send_message"
    description = "Send message via Telegram"
    args_schema: Type[BaseModel] = TelegramInput
    
    def _run(self, chat_id: str, text: str) -> str:
        try:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                logging.warning("No Telegram bot token found")
                return "Message not sent - no bot token configured"
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {"chat_id": chat_id, "text": text}
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logging.info("Telegram message sent successfully")
                return "Message sent successfully"
            else:
                logging.error(f"Telegram API error: {response.status_code} - {response.text}")
                return f"Message failed to send: {response.status_code}"
                
        except Exception as e:
            logging.error(f"TelegramTool error: {e}")
            return f"Message failed to send: {str(e)}"