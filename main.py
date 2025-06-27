# docker-main.py - Fixed version with proper logging setup
import schedule
import time
from threading import Thread
from agent import OutdoorSportsPlannerAgent
import os
import logging

def setup_logging():
    """Setup logging with proper directory creation"""
    # Ensure logs directory exists
    logs_dir = '/app/logs'
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create log file path
    log_file = os.path.join(logs_dir, 'sports_planner.log')
    
    # Setup logging with error handling
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, mode='a'),
                logging.StreamHandler()
            ]
        )
        logging.info(f"Logging initialized successfully. Log file: {log_file}")
    except Exception as e:
        # Fallback to console only if file logging fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        logging.warning(f"Could not setup file logging: {e}. Using console only.")

def setup_environment():
    """Check environment variables"""
    required_vars = [
        "GROQ_API_KEY",
        "OPENWEATHER_API_KEY", 
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logging.error(f"Missing environment variables: {missing_vars}")
        logging.info("The application will run with mock data for missing services")
        return False
    
    logging.info("All environment variables loaded successfully")
    return True

def daily_sports_notification():
    """Run daily sports notification"""
    try:
        logging.info("Running daily sports notification...")
        agent = OutdoorSportsPlannerAgent()
        result = agent.run_daily_recommendation()
        logging.info(f"Daily notification completed: {result[:100]}...")
    except Exception as e:
        logging.error(f"Error in daily notification: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")

def run_scheduler():
    """Run the scheduled tasks"""
    schedule.every().day.at("06:00").do(daily_sports_notification)
    logging.info("Scheduler started - daily notifications at 06:00")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logging.error(f"Error in scheduler: {e}")
            time.sleep(60)

def manual_recommendation(sport="cricket"):
    """Run manual recommendation for testing"""
    try:
        logging.info(f"Running manual recommendation for {sport}...")
        agent = OutdoorSportsPlannerAgent()
        result = agent.run_custom_sport_recommendation(sport)
        logging.info(f"Manual recommendation result: {result}")
        return result
    except Exception as e:
        logging.error(f"Error in manual recommendation: {e}")
        return f"Error: {str(e)}"

def main():
    """Main function"""
    # Setup logging first
    setup_logging()
    
    # Check environment (but don't exit if missing - use mock data)
    env_status = setup_environment()
    
    # Initialize agent
    try:
        agent = OutdoorSportsPlannerAgent()
        logging.info("OutdoorSportsPlannerAgent initialized successfully")
        
        # Test the agent immediately
        logging.info("Running initial test recommendation...")
        test_result = agent.run_daily_recommendation()
        logging.info(f"Test recommendation completed: {test_result[:100]}...")
        
    except Exception as e:
        logging.error(f"Failed to initialize agent: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return
    
    # Start scheduler in background thread
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Docker mode - run continuously
    logging.info("🏃‍♂️ OutdoorSportsPlannerAgent is running in Docker mode!")
    logging.info("📅 Daily notifications scheduled at 06:00")
    logging.info("🔧 For manual recommendations, use: docker exec <container> python -c \"from docker-main import manual_recommendation; print(manual_recommendation('cricket'))\"")
    
    # Keep the container running with health checks
    try:
        health_check_counter = 0
        while True:
            time.sleep(3600)  # Sleep for 1 hour
            health_check_counter += 1
            logging.info(f"Health check #{health_check_counter} - container is running")
            
            # Run a mini health check every 6 hours
            if health_check_counter % 6 == 0:
                try:
                    logging.info("Running periodic health check...")
                    agent = OutdoorSportsPlannerAgent()
                    logging.info("Health check passed - agent can be initialized")
                except Exception as e:
                    logging.warning(f"Health check warning: {e}")
                    
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully...")
    except Exception as e:
        logging.error(f"Unexpected error in main loop: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()