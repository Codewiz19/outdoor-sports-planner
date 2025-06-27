# agent.py - Fixed Main Agent Implementation
from langchain_groq import ChatGroq
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from tools import (LocationTool, WeatherTool, AQITool, DayTypeTool, 
                  BestTimeSelectorTool, MotivationTool, TelegramTool)
import os
import json
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()


class OutdoorSportsPlannerAgent:
    def __init__(self):
        try:
            self.llm = ChatGroq(
                temperature=0.7,
                groq_api_key=os.getenv("GROQ_API_KEY"),
                model_name="llama3-70b-8192"
            )
            
            self.tools = [
                LocationTool(),
                WeatherTool(), 
                AQITool(),
                DayTypeTool(),
                BestTimeSelectorTool(),
                MotivationTool(),
                TelegramTool()
            ]
            
            # Create react agent prompt
            template = """You are an outdoor sports planning agent. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

            prompt = PromptTemplate.from_template(template)
            
            # Create the agent
            agent = create_react_agent(self.llm, self.tools, prompt)
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=agent, 
                tools=self.tools, 
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=10
            )
            
            self.default_sport = "cricket"
            self.user_id = "user123"
            self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
            
            logging.info("Agent initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing agent: {e}")
            raise
    
    def generate_sports_recommendation_direct(self, sport=None):
        """Direct method without LLM for reliability"""
        if sport is None:
            sport = self.default_sport
            
        try:
            logging.info(f"Generating recommendation for sport: {sport}")
            
            # Step 1: Get location
            location_tool = LocationTool()
            location_result = location_tool._run(self.user_id)
            location_data = json.loads(location_result)
            city = location_data["city"]
            logging.info(f"Location: {city}")
            
            # Step 2: Get weather
            weather_tool = WeatherTool()
            weather_result = weather_tool._run(city)
            logging.info(f"Weather data retrieved: {len(json.loads(weather_result))} entries")
            
            # Step 3: Get AQI
            aqi_tool = AQITool()
            aqi_result = aqi_tool._run(city)
            logging.info(f"AQI data retrieved: {len(json.loads(aqi_result))} entries")
            
            # Step 4: Check day type
            day_tool = DayTypeTool()
            day_result = day_tool._run(datetime.now().isoformat())
            logging.info(f"Day type: {day_result}")
            
            # Step 5: Find best times - Fix the parameter passing
            selector_tool = BestTimeSelectorTool()
            
            # Create the combined data structure that the tool expects
            combined_data = {
                'sport': sport,
                'weather_data': weather_result,  # This is already a JSON string
                'aqi_data': aqi_result,          # This is already a JSON string
                'day_type': day_result           # This is already a JSON string
            }
            
            # Convert to JSON string as expected by the tool
            combined_data_json = json.dumps(combined_data)
            best_times_result = selector_tool._run(combined_data_json)
            best_times = json.loads(best_times_result)
            logging.info(f"Best times found: {len(best_times)} slots")
            
            # Step 6: Get motivation if weekend
            day_data = json.loads(day_result)
            motivation = ""
            if day_data["type"] != "weekday":
                motivation_tool = MotivationTool()
                motivation = motivation_tool._run(day_result)
                logging.info(f"Motivation message: {motivation}")
            
            # Step 7: Format message
            if not best_times:
                message = f"⚠️ Weather/AQI not suitable for playing {sport} today in {city}. Consider indoor alternatives."
                logging.info("No suitable time slots found")
            else:
                weather_data = json.loads(weather_result)
                aqi_data = json.loads(aqi_result)
                
                message = f"🏏 Best time for {sport} today in {city}:\n"
                for slot in best_times[:2]:
                    start_time = datetime.fromisoformat(slot['start'].replace(' ', 'T')).strftime("%H:%M")
                    end_time = datetime.fromisoformat(slot['end']).strftime("%H:%M")
                    message += f"- {start_time}-{end_time} (score: {slot['score']})\n"
                
                avg_temp = sum(w['temp'] for w in weather_data) / len(weather_data)
                avg_aqi = sum(a['aqi'] for a in aqi_data) / len(aqi_data)
                message += f"Conditions: {avg_temp:.1f}°C, AQI {avg_aqi:.0f}"
                
                if motivation:
                    message += f"\n\n🎉 {motivation}"
                
                logging.info(f"Generated message: {message[:100]}...")
            
            # Step 8: Send message
            if self.chat_id:
                try:
                    telegram_tool = TelegramTool()
                    telegram_result = telegram_tool._run(self.chat_id, message)
                    logging.info(f"Telegram message sent: {telegram_result}")
                except Exception as e:
                    logging.error(f"Failed to send Telegram message: {e}")
            else:
                logging.warning("No Telegram chat ID configured")
            
            return message
            
        except Exception as e:
            error_msg = f"Error generating recommendation: {str(e)}"
            logging.error(error_msg)
            logging.error(f"Error type: {type(e).__name__}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return error_msg
    
    def run_daily_recommendation(self):
        """Run daily recommendation for default sport"""
        return self.generate_sports_recommendation_direct()
    
    def run_custom_sport_recommendation(self, sport):
        """Run recommendation for specific sport"""
        return self.generate_sports_recommendation_direct(sport)