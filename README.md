# AI Greenhouse

Smart Plant Care Assistant - An intelligent desktop application for real-time greenhouse monitoring, analytics, and automation.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)

## Overview

**AI Greenhouse** is a desktop application designed to monitor and automate plant care. It integrates with Arduino sensors to track environmental conditions such as temperature, humidity, sunlight, and soil moisture. The application provides actionable insights, notifications, and interactive chatbot support.

## Features

- **Real-time Monitoring:** Tracking of temperature, humidity, sunlight, and soil moisture.
- **AI Chatbot:** Support for plant care queries, sentiment analysis, voice input, and Text-to-Speech (TTS).
- **Analytics:** Visualization of sensor history, interaction analytics, and wordclouds.
- **Notifications:** System tray alerts for critical plant care events.
- **Data Management:** Export chat history in TXT, CSV, or JSON formats and support for image uploads.
- **Automation:** Arduino integration for automated watering based on soil moisture levels.

## Architecture

- **Frontend:** PyQt5 desktop UI.
- **Backend:** Python with Arduino serial communication.
- **AI/ML Integration:** TextBlob, speech_recognition, pyttsx3, wordcloud, and matplotlib.

## Getting Started

### Prerequisites

- Python 3.8 or higher.
- Arduino board with compatible sensors.
- pip package manager.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Mrudula-itsjuzme/ai_greenhouse.git
   ```
2. Navigate to the project directory:
   ```bash
   cd ai_greenhouse
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Arduino Configuration

- Upload the provided Arduino sketch to the board.
- Connect the necessary sensors.
- Configure the `ARDUINO_PORT` in `bot1.py` and `python.py`.

## Usage

Start the application by running:
```bash
python bot1.py
```

## Contributing

Contributions are welcome. Please submit an issue or pull request for any bugs or feature enhancements.

## Acknowledgements

- Built with PyQt5, matplotlib, wordcloud, textblob, pyttsx3, and speech_recognition.
- Thanks to the Arduino community for sensor integration resources.
