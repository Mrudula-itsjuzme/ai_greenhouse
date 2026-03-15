import sys
import os
import json
import csv
import serial
import time
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
    QTextEdit, QLineEdit, QLabel, QHBoxLayout, QFileDialog, QComboBox,
    QScrollArea, QFrame, QSizePolicy, QSystemTrayIcon, QMenu, QColorDialog)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor
import speech_recognition as sr
import pyttsx3
from textblob import TextBlob
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import numpy as np

# Arduino Constants
ARDUINO_PORT = os.getenv("ARDUINO_PORT", "/dev/cu.usbserial-1130")  # Override with ARDUINO_PORT env var
BAUD_RATE = 9600

# Plant Thresholds
TEMP_MIN = 18
TEMP_MAX = 30
HUMIDITY_MIN = 40
HUMIDITY_MAX = 70
SUNLIGHT_MIN = 500
SUNLIGHT_MAX = 1500
SOIL_MOISTURE_THRESHOLD = 40

class ArduinoThread(QThread):
    sensor_data = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.ser = None
    
    def run(self):
        try:
            self.ser = serial.Serial(ARDUINO_PORT, BAUD_RATE)
            time.sleep(2)  # Wait for Arduino to initialize
            
            while self.running:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8').strip()
                    try:
                        temp, humidity, sunlight, soil_moisture = map(float, data.split(','))
                        sensor_dict = {
                            'temperature': temp,
                            'humidity': humidity,
                            'sunlight': sunlight,
                            'soil_moisture': soil_moisture
                        }
                        self.sensor_data.emit(sensor_dict)
                    except ValueError:
                        self.error.emit("Error parsing sensor data")
                time.sleep(0.1)
                
        except serial.SerialException as e:
            self.error.emit(f"Arduino connection error: {str(e)}")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
    
    def stop(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()

class SpeechThread(QThread):
    finished = pyqtSignal(str)
    
    def run(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            audio = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(audio)
                self.finished.emit(text)
            except:
                self.finished.emit("")

class ChatbotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.chat_history = []
        self.notification_enabled = False
        self.tts_engine = pyttsx3.init()
        self.speech_thread = None
        self.interaction_count = 0
        self.setup_tray()
        self.load_faqs()
        self.init_ui()
        self.show_welcome_screen()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))  # Replace with your icon
        self.tray_menu = QMenu()
        self.tray_menu.addAction("Show", self.show)
        self.tray_menu.addAction("Exit", self.close)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        
    def start_arduino_monitoring(self):
        self.arduino_thread = ArduinoThread()
        self.arduino_thread.sensor_data.connect(self.update_sensor_display)
        self.arduino_thread.error.connect(self.handle_arduino_error)
        self.arduino_thread.start()

    def update_sensor_display(self, sensor_data):
        # Store sensor data
        self.sensor_history.append({
            'timestamp': datetime.now(),
            'data': sensor_data
        })
        
        # Update display
        status_text = f"""
        <div style='background-color: #f1f8e9; padding: 10px; border-radius: 10px; margin: 5px;'>
            <h3>Current Readings:</h3>
            <p>Temperature: {sensor_data['temperature']:.1f}°C</p>
            <p>Humidity: {sensor_data['humidity']:.1f}%</p>
            <p>Sunlight: {sensor_data['sunlight']:.0f} lux</p>
            <p>Soil Moisture: {sensor_data['soil_moisture']:.1f}%</p>
        </div>
        """
        self.sensor_display.setHtml(status_text)
        
        # Get and display suggestions
        suggestions = self.get_suggestions(sensor_data)
        if suggestions:
            suggestion_text = "<div style='color: #2e7d32;'><b>Suggestions:</b><ul>"
            for suggestion in suggestions:
                suggestion_text += f"<li>{suggestion}</li>"
            suggestion_text += "</ul></div>"
            self.chat_display.append(suggestion_text)
            
            # Show notification if enabled
            if self.notification_enabled:
                self.tray_icon.showMessage(
                    "Plant Care Alert",
                    suggestions[0],  # Show first suggestion as notification
                    QSystemTrayIcon.Information,
                    2000
                )

    def get_suggestions(self, sensor_data):
        suggestions = []
        temp = sensor_data['temperature']
        humidity = sensor_data['humidity']
        sunlight = sensor_data['sunlight']
        soil_moisture = sensor_data['soil_moisture']
        
        if temp < TEMP_MIN:
            suggestions.append("🌡 Increase temperature to maintain optimal growth conditions.")
        elif temp > TEMP_MAX:
            suggestions.append("🌡 Decrease temperature to prevent overheating.")
        
        if humidity < HUMIDITY_MIN:
            suggestions.append("💧 Increase humidity levels, such as by misting the plant.")
        elif humidity > HUMIDITY_MAX:
            suggestions.append("💧 Reduce humidity to prevent fungal issues.")
        
        if sunlight < SUNLIGHT_MIN:
            suggestions.append("☀ Move the plant to a brighter location.")
        elif sunlight > SUNLIGHT_MAX:
            suggestions.append("☀ Move the plant to a shaded area to avoid sunburn.")
        
        if soil_moisture < SOIL_MOISTURE_THRESHOLD:
            suggestions.append("💦 Water the plant to maintain healthy soil moisture.")
            # Activate pump
            if self.arduino_thread and self.arduino_thread.ser:
                self.arduino_thread.ser.write(b'PUMP_ON\n')
                QTimer.singleShot(10000, lambda: self.arduino_thread.ser.write(b'PUMP_OFF\n'))
        
        return suggestions

    def handle_arduino_error(self, error_message):
        self.chat_display.append(f"<div style='color: red;'><b>Error:</b> {error_message}</div>")


    def init_ui(self):
        self.setWindowTitle('Enhanced Greenhouse Assistant')
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f5f0;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        main_layout = QVBoxLayout()

        # Welcome header
        self.header = QLabel("🌿 Welcome to Greenhouse Assistant", self)
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("""
            font-size: 24px;
            color: #2e7d32;
            padding: 20px;
            background-color: white;
            border-radius: 15px;
            margin: 10px;
        """)
        main_layout.addWidget(self.header)

        # Control buttons layout
        controls_layout = QHBoxLayout()
        
        # Notification toggle
        self.notification_btn = self.create_button("🔔 Notifications")
        self.notification_btn.clicked.connect(self.toggle_notifications)
        controls_layout.addWidget(self.notification_btn)
        
        # Voice input
        self.voice_btn = self.create_button("🎤 Voice")
        self.voice_btn.clicked.connect(self.start_voice_input)
        controls_layout.addWidget(self.voice_btn)
        
        # Text-to-speech
        self.tts_btn = self.create_button("🔊 TTS")
        self.tts_btn.clicked.connect(self.toggle_tts)
        controls_layout.addWidget(self.tts_btn)
        
        main_layout.addLayout(controls_layout)

        # Quick access FAQs
        self.create_faq_buttons(main_layout)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                border: 2px solid #a5d6a7;
                border-radius: 15px;
                padding: 15px;
                background-color: white;
                font-size: 14px;
            }
        """)
        main_layout.addWidget(self.chat_display)

        # Input area
        input_layout = QHBoxLayout()
        
        # File upload button
        self.upload_btn = self.create_button("📎")
        self.upload_btn.clicked.connect(self.upload_file)
        input_layout.addWidget(self.upload_btn)
        
        # Text input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #a5d6a7;
                border-radius: 15px;
                font-size: 14px;
                margin: 10px 0;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        # Emoji picker
        self.emoji_btn = self.create_button("😊")
        self.emoji_btn.clicked.connect(self.show_emoji_picker)
        input_layout.addWidget(self.emoji_btn)
        
        # Send button
        self.send_button = self.create_button("Send 📤")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        main_layout.addLayout(input_layout)

        # Bottom buttons layout
        bottom_layout = QHBoxLayout()
        
        # Save history
        self.save_btn = self.create_button("💾 Save History")
        self.save_btn.clicked.connect(self.save_history)
        bottom_layout.addWidget(self.save_btn)
        
        # Generate WordCloud
        self.wordcloud_btn = self.create_button("☁ WordCloud")
        self.wordcloud_btn.clicked.connect(self.generate_wordcloud)
        bottom_layout.addWidget(self.wordcloud_btn)
        
        # Show Graph
        self.graph_btn = self.create_button("📊 Show Graph")
        self.graph_btn.clicked.connect(self.show_interaction_graph)
        bottom_layout.addWidget(self.graph_btn)
        
        # Theme selector
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Light", "Dark", "Nature", "Custom"])
        self.theme_selector.currentTextChanged.connect(self.change_theme)
        self.theme_selector.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #a5d6a7;
                border-radius: 10px;
                background: white;
            }
        """)
        bottom_layout.addWidget(self.theme_selector)
        
        main_layout.addLayout(bottom_layout)
        
        self.setLayout(main_layout)
        
        # Right panel for sensor readings
        right_panel = QVBoxLayout()
        
        # Sensor display
        self.sensor_display = QTextEdit()
        self.sensor_display.setReadOnly(True)
        self.sensor_display.setStyleSheet("""
            QTextEdit {
                border: 2px solid #a5d6a7;
                border-radius: 15px;
                padding: 15px;
                background-color: white;
                font-size: 14px;
                max-height: 300px;
            }
        """)
        right_panel.addWidget(self.sensor_display)
        
        # Add sensor history graph
        self.sensor_graph = QLabel()
        self.sensor_graph.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 2px solid #a5d6a7;
                border-radius: 15px;
                padding: 15px;
            }
        """)
        right_panel.addWidget(self.sensor_graph)
        
        # Update sensor graph periodically
        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.update_sensor_graph)
        self.sensor_timer.start(60000)  # Update every minute
        
        # Add panels to main layout
        main_layout.addLayout(left_panel, 2)  # 2/3 of width
        main_layout.addLayout(right_panel, 1)  # 1/3 of width
        
        self.setLayout(main_layout)
        
    def closeEvent(self, event):
        if self.arduino_thread:
            self.arduino_thread.stop()
        event.accept()

    def update_sensor_graph(self):
        if len(self.sensor_history) > 1:
            plt.figure(figsize=(8, 6))
            
            times = [record['timestamp'] for record in self.sensor_history[-60:]]  # Last 60 readings
            temps = [record['data']['temperature'] for record in self.sensor_history[-60:]]
            humidity = [record['data']['humidity'] for record in self.sensor_history[-60:]]
            moisture = [record['data']['soil_moisture'] for record in self.sensor_history[-60:]]
            
            plt.plot(times, temps, label='Temperature (°C)', color='red')
            plt.plot(times, humidity, label='Humidity (%)', color='blue')
            plt.plot(times, moisture, label='Soil Moisture (%)', color='green')
            
            plt.title('Sensor History')
            plt.xlabel('Time')
            plt.ylabel('Value')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save and display the graph
            plt.savefig('sensor_history.png')
            self.sensor_graph.setPixmap(QPixmap('sensor_history.png').scaled(
                self.sensor_graph.width(),
                self.sensor_graph.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
            plt.close()

    def create_button(self, text):
        button = QPushButton(text)
        button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 15px;
                min-width: 100px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        return button

    def create_faq_buttons(self, layout):
        faq_scroll = QScrollArea()
        faq_widget = QWidget()
        faq_layout = QHBoxLayout()
        
        for question in self.faqs.keys():
            btn = QPushButton(question)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e8f5e9;
                    color: #2e7d32;
                    border: 1px solid #a5d6a7;
                    padding: 8px;
                    border-radius: 10px;
                    margin: 0 5px;
                }
                QPushButton:hover {
                    background-color: #c8e6c9;
                }
            """)
            btn.clicked.connect(lambda checked, q=question: self.input_field.setText(q))
            faq_layout.addWidget(btn)
        
        faq_widget.setLayout(faq_layout)
        faq_scroll.setWidget(faq_widget)
        faq_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        faq_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        faq_scroll.setMaximumHeight(50)
        faq_scroll.setWidgetResizable(True)
        layout.addWidget(faq_scroll)

    def show_welcome_screen(self):
        welcome_text = """
        <div style='text-align: center; padding: 20px;'>
            <h1 style='color: #2e7d32;'>🌿 Welcome to Greenhouse Assistant!</h1>
            <p>I'm here to help you with all your plant care needs.</p>
            <p>Features available:</p>
            <ul style='list-style-type: none;'>
                <li>💬 Chat with AI about plant care</li>
                <li>🎤 Voice input support</li>
                <li>📊 Interaction analytics</li>
                <li>💾 Save chat history</li>
                <li>🔔 Notifications</li>
                <li>🌈 Customizable themes</li>
            </ul>
        </div>
        """
        self.chat_display.setHtml(welcome_text)

    def send_message(self):
        message = self.input_field.text().strip()
        if message:
            # Add timestamp and analyze sentiment
            timestamp = datetime.now().strftime("%H:%M:%S")
            sentiment = TextBlob(message).sentiment.polarity
            emoji = "😊" if sentiment > 0 else "😐" if sentiment == 0 else "😔"
            
            # Format and display user message
            user_message = f'<div style="text-align: right; margin: 10px;">'
            user_message += f'<span style="background-color: #e8f5e9; padding: 8px; border-radius: 10px;">'
            user_message += f'<b>{timestamp} You:</b> {message} {emoji}</span></div>'
            self.chat_display.append(user_message)
            
            # Store message in history
            self.chat_history.append({
                "role": "user",
                "message": message,
                "timestamp": timestamp,
                "sentiment": sentiment
            })
            
            # Clear input and update interaction count
            self.input_field.clear()
            self.interaction_count += 1
            
            # Simulate bot response (replace with actual AI response)
            QTimer.singleShot(1000, lambda: self.bot_response(message))

    def bot_response(self, user_message):
        # Simple response simulation - replace with actual AI processing
        responses = {
            "hello": "Hello! How can I help you with your plants today? 🌱",
            "help": "I can help you with plant care, watering schedules, and more! What would you like to know? 🌿",
        }
        
        response = responses.get(user_message.lower(), 
            "I'm here to help with your plant care needs! Feel free to ask anything specific. 🌺")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        bot_message = f'<div style="text-align: left; margin: 10px;">'
        bot_message += f'<span style="background-color: #f1f8e9; padding: 8px; border-radius: 10px;">'
        bot_message += f'<b>{timestamp} Bot:</b> {response}</span></div>'
        
        self.chat_display.append(bot_message)
        
        # Store in history
        self.chat_history.append({
            "role": "bot",
            "message": response,
            "timestamp": timestamp
        })
        
        # Show notification if enabled
        if self.notification_enabled:
            self.tray_icon.showMessage(
                "New Message",
                "The bot has responded to your message!",
                QSystemTrayIcon.Information,
                2000
            )

    def toggle_notifications(self):
        self.notification_enabled = not self.notification_enabled
        self.notification_btn.setStyleSheet(
    "QPushButton {"
    "background-color: " + ('#45a049' if self.notification_enabled else '#4caf50') + ";"
    "color: white;"
    "border: none;"
    "padding: 12px;"
    "border-radius: 15px;"
    "}"
)


    def start_voice_input(self):
        if not self.speech_thread:
            self.speech_thread = SpeechThread()
            self.speech_thread.finished.connect(self.on_speech_recognized)
            self.voice_btn.setStyleSheet("background-color: #ff4444;")
            self.speech_thread.start()

    def on_speech_recognized(self, text):
        if text:
            self.input_field.setText(text)
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 15px;
            }
        """)
        self.speech_thread = None

    def toggle_tts(self):
        # Get last bot message and speak it
        for msg in reversed(self.chat_history):
            if msg["role"] == "bot":
                self.tts_engine.say(msg["message"])
                self.tts_engine.runAndWait()
                break

    def upload_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Upload File", "", 
            "Images (.png *.jpg);;All Files (.*)"
        )
        if file_name:
            # Handle file upload - implement your logic here
            self.chat_display.append(f"<i>File uploaded: {os.path.basename(file_name)}</i>")

    def show_emoji_picker(self):
        # Simple emoji picker - extend with more emojis
        emojis = ["😊", "🌱", "🌿", "🌺", "🌸", "🌼", "👍", "❤"]
        emoji_menu = QMenu(self)
        for emoji in emojis:
            emoji_menu.addAction(emoji, lambda e=emoji: self.input_field.insert(e))
        emoji_menu.exec_(self.emoji_btn.mapToGlobal(self.emoji_btn.rect().bottomLeft()))

    def save_history(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Chat History",
            "",
            "Text Files (.txt);;CSV Files (.csv);;JSON Files (*.json)",
            options=options
        )
        
        if file_name:
            if file_name.endswith('.txt'):
                with open(file_name, 'w', encoding='utf-8') as f:
                    for msg in self.chat_history:
                        f.write(f"[{msg['timestamp']}] {msg['role']}: {msg['message']}\n")
            
            elif file_name.endswith('.csv'):
                with open(file_name, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['timestamp', 'role', 'message', 'sentiment'])
                    writer.writeheader()
                    writer.writerows(self.chat_history)
            
            elif file_name.endswith('.json'):
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(self.chat_history, f, indent=2)

    def generate_wordcloud(self):
        # Combine all messages into one text
        text = ' '.join(msg['message'] for msg in self.chat_history)
        if text.strip():
            wordcloud = WordCloud(
                width=800, 
                height=400,
                background_color='white',
                colormap='Greens'
            ).generate(text)
            
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            
            # Save and show the wordcloud
            plt.savefig('wordcloud.png')
            self.chat_display.append(
                '<div style="text-align: center;">'
                '<img src="wordcloud.png" width="600"/>'
                '</div>'
            )

    def show_interaction_graph(self):
        # Create interaction data
        interactions = [msg for msg in self.chat_history if msg['role'] == 'user']
        if interactions:
            dates = [datetime.strptime(msg['timestamp'], '%H:%M:%S').strftime('%H:%M')
                    for msg in interactions]
            counts = range(1, len(interactions) + 1)
            
            plt.figure(figsize=(10, 5))
            plt.plot(dates, counts, marker='o', color='#4caf50')
            plt.title('Interaction History')
            plt.xlabel('Time')
            plt.ylabel('Number of Interactions')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save and show the graph
            plt.savefig('interactions.png')
            self.chat_display.append(
                '<div style="text-align: center;">'
                '<img src="interactions.png" width="600"/>'
                '</div>'
            )

    def change_theme(self, theme_name):
        themes = {
            "Light": {
                "background": "#ffffff",
                "text": "#000000",
                "chat_bg": "#f0f5f0",
                "accent": "#4caf50"
            },
            "Dark": {
                "background": "#2c2c2c",
                "text": "#ffffff",
                "chat_bg": "#3c3c3c",
                "accent": "#6abf6e"
            },
            "Nature": {
                "background": "#e8f5e9",
                "text": "#1b5e20",
                "chat_bg": "#c8e6c9",
                "accent": "#388e3c"
            }
        }
        
        if theme_name == "Custom":
            color = QColorDialog.getColor()
            if color.isValid():
                custom_theme = {
                    "background": color.name(),
                    "text": "#000000" if color.lightness() > 128 else "#ffffff",
                    "chat_bg": color.lighter().name(),
                    "accent": color.darker().name()
                }
                self.apply_theme(custom_theme)
        else:
            self.apply_theme(themes.get(theme_name, themes["Light"]))

    def apply_theme(self, theme):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['background']};
                color: {theme['text']};
            }}
            QTextEdit {{
                background-color: {theme['chat_bg']};
                border-color: {theme['accent']};
            }}
            QPushButton {{
                background-color: {theme['accent']};
                color: white;
            }}
            QLineEdit {{
                background-color: {theme['chat_bg']};
                border-color: {theme['accent']};
            }}
        """)

    def load_faqs(self):
        self.faqs = {
            "How do I water my plants?": 
                "Check soil moisture before watering. Water thoroughly until it drains from bottom.",
            "What's the ideal temperature?": 
                "Most plants prefer 65-75°F (18-24°C) during day, slightly cooler at night.",
            "How to control pests naturally?": 
                "Use neem oil, introduce beneficial insects, or try companion planting.",
            "Best soil mix?": 
                "A good general mix is equal parts peat moss, perlite, and compost.",
            "Plant looking unhealthy?":
                "Check water, light, nutrients, and look for signs of pests or disease."
        }

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look across platforms
    
    # Set application-wide font
    font = QFont('Segoe UI', 10)
    app.setFont(font)
    
    window = ChatbotApp()
    window.show()
    
    sys.exit(app.exec_())