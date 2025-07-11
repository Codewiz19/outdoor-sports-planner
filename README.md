**Outdoor Sports Planner Agent**

A comprehensive AI-powered system that automatically plans the best times to play outdoor sports (default: cricket) based on real-time location, weather, and air quality data. The system is designed to run inside a Docker container and can send daily recommendations via Telegram.

---

## 🔍 Project Overview

This repository contains three main modules:

1. **`tools.py`**: Implements LangChain tools for fetching location, weather, AQI, day type, selecting best time slots, generating motivational messages, and sending Telegram messages.
2. **`docker-main.py`**: Sets up logging, environment checks, and schedules daily notifications using a background thread with the `schedule` library.
3. **`agent.py`**: Defines the `OutdoorSportsPlannerAgent` class, which orchestrates the data retrieval, decision logic, and messaging (direct implementation and LangChain-based agent).

By combining these components, the system can autonomously determine the ideal time windows to play a sport, craft a user-friendly message, and dispatch it via Telegram at a scheduled time each day.

---

## ⚙️ Prerequisites

* Python 3.10+ (recommended)
* Docker (for containerized deployment)
* Environment variables:

  * `GROQ_API_KEY`: API key for Groq LLM
  * `OPENWEATHER_API_KEY`: API key for OpenWeather (optional — mock data is used if missing)
  * `TELEGRAM_BOT_TOKEN`: Token for Telegram Bot API (optional — messaging disabled if missing)
  * `TELEGRAM_CHAT_ID`: Target Telegram chat ID for notifications

---

## 🛠️ Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-org/outdoor-sports-planner.git
   cd outdoor-sports-planner
   ```

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file in the project root:

   ```dotenv
   GROQ_API_KEY=<your_groq_api_key>
   OPENWEATHER_API_KEY=<your_openweather_api_key>
   TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>
   TELEGRAM_CHAT_ID=<your_chat_id>
   ```

---

## 📝 Code Structure & Details

### 1. **`tools.py`**

* **`LocationTool`**: Returns the user’s current city. Defaults to mock data (`Mumbai`).
* **`WeatherTool`**: Fetches 8-hour hourly forecast from OpenWeather (metric units). Falls back to mock data if the API key is missing or on errors.
* **`AQITool`**: Generates mock 8-hour AQI data (values ranging 80–115).
* **`DayTypeTool`**: Determines if the current date is a weekday or weekend.
* **`BestTimeSelectorTool`**: Scores each hourly slot based on sport-specific criteria (temperature, rain, AQI, humidity, preferred time windows) and returns the top two slots.
* **`MotivationTool`**: Provides a motivational message if it’s a weekend.
* **`TelegramTool`**: Sends a text message to a specified Telegram chat via Bot API.

Each tool extends `langchain.tools.BaseTool`, defines an `args_schema`, and implements `_run(...)` that returns JSON-serializable strings.

### 2. **`docker-main.py`**

* **Logging Setup**: Creates `/app/logs` directory, configures file and console handlers, and logs initialization status.
* **Environment Check**: Verifies presence of required environment variables and logs missing ones (continues with mock data if any are absent).
* **Scheduling**: Uses the `schedule` library to run `daily_sports_notification()` every day at `06:00`.
* **Background Thread**: Launches the scheduler in a daemon thread so the container remains responsive.
* **Health Checks**: Periodically logs health status every hour and performs agent initialization checks every 6 hours.

Commands for manual testing:

```bash
# Inside the Docker container:
python -c "from docker-main import manual_recommendation; print(manual_recommendation('cricket'))"
```

### 3. **`agent.py`**

Defines the `OutdoorSportsPlannerAgent` class with two modes of operation:

1. **Direct Implementation (`generate_sports_recommendation_direct`)**

   * **Step 1**: Retrieve location via `LocationTool`.
   * **Step 2**: Fetch weather data via `WeatherTool`.
   * **Step 3**: Fetch AQI data via `AQITool`.
   * **Step 4**: Determine day type via `DayTypeTool`.
   * **Step 5**: Compute best time slots via `BestTimeSelectorTool`.
   * **Step 6**: Generate motivation if it’s a weekend via `MotivationTool`.
   * **Step 7**: Compose a user-friendly message with times, scores, and conditions.
   * **Step 8**: Send the message through Telegram via `TelegramTool`, if configured.

2. **LangChain ReAct Agent**

   * Built with `langchain_groq.ChatGroq` and React-style prompting.
   * Capable of reasoning through tool calls (for advanced flexibility).

Common design features:

* Comprehensive logging at each step for observability.
* Graceful error handling and fallback to mock data.
* JSON-based inputs and outputs for easy parsing.

---

## 🚀 Deployment with Docker

1. **Build Docker image:**

   ```bash
   docker build -t sports-planner-image .
   ```

2. **Run container:**

   ```bash
   docker run -d \
     --name sports-planner \
     --env-file .env \
     sports-planner-image
   ```

3. **Logs:**

   * **File logs:** `/app/logs/sports_planner.log`
   * **Console logs:** View via `docker logs -f sports-planner`

---

## 🎯 Usage Examples

* **Manual Recommendation:**

  ```bash
  docker exec sports-planner \
    python -c "from docker-main import manual_recommendation; print(manual_recommendation('cricket'))"
  ```

* **View Logs:**

  ```bash
  docker logs -f sports-planner
  ```

---

 

## 📄 License

[MIT License](./LICENSE)
