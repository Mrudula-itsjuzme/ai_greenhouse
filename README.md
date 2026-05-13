# AI Greenhouse

A smart plant-care desktop application for greenhouse monitoring, sensor analytics, chatbot support, and Arduino-based automation.

This project combines IoT, desktop UI design, and lightweight AI features to make plant monitoring more interactive and beginner-friendly.

---

## Project links and evidence

| Item | Link / Note |
|---|---|
| Repository | https://github.com/Mrudula-itsjuzme/ai_greenhouse |
| Paper / reference | No paper attached; applied IoT automation prototype |
| Demo video | Not uploaded yet |
| Deployment | Local desktop application; no hosted deployment |
| Dataset note | Uses live Arduino sensor readings for temperature, humidity, sunlight, and soil moisture |
| Result screenshots | Dashboard screenshots and wiring images should be added in a future `screenshots/` or `docs/` folder |

---

## Problem statement

Greenhouse plants need consistent monitoring of temperature, humidity, light, and soil moisture. Manual monitoring is easy to forget and hard to scale.

AI Greenhouse provides a desktop dashboard that reads sensor data, visualizes trends, sends alerts, and supports plant-care interactions through a chatbot-style assistant.

---

## Features

- real-time temperature, humidity, sunlight, and soil-moisture monitoring
- Arduino serial communication
- automated watering logic based on soil-moisture readings
- PyQt5 desktop interface
- chatbot support for plant-care questions
- sentiment analysis and voice input
- text-to-speech output
- sensor-history analytics and visualizations
- system-tray notifications
- chat-history export in TXT, CSV, and JSON formats
- image-upload support

---

## System overview

```text
Arduino Sensors
      ↓
Serial Communication
      ↓
Python Backend
      ↓
PyQt5 Dashboard
      ↓
Analytics + Alerts + Chatbot
      ↓
Automation Decisions
```

---

## Tech stack

- Python
- PyQt5
- Arduino
- Serial communication
- Matplotlib
- WordCloud
- TextBlob
- speech_recognition
- pyttsx3

---

## Quick start

```bash
git clone https://github.com/Mrudula-itsjuzme/ai_greenhouse.git
cd ai_greenhouse

pip install -r requirements.txt
python bot1.py
```

---

## Arduino setup

1. Upload the Arduino sketch used by the project.
2. Connect sensors for temperature, humidity, sunlight, and soil moisture.
3. Check the Arduino serial port.
4. Update the port configuration in the Python files, especially:

```text
bot1.py
python.py
```

Look for the `ARDUINO_PORT` setting and replace it with your local port.

---

## Repository structure

```text
ai_greenhouse/
├── bot1.py          # main desktop application entry point
├── python.py        # Arduino / sensor communication logic
├── requirements.txt # Python dependencies
└── README.md
```

---

## Why this project matters

This project is a practical IoT automation prototype. It shows how environmental sensing, desktop UI design, and automation logic can work together in a real plant-care workflow.

---

## Future improvements

- add screenshots of the dashboard
- add Arduino wiring diagrams
- move configuration into a `.env` or config file
- add database-backed sensor history
- add threshold customization from the UI
- package the app as an executable

---

## Author

Built by [Pedamallu Sai Mrudula](https://github.com/Mrudula-itsjuzme) as part of an applied AI, IoT, and automation portfolio.
