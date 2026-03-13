import serial
import time

# Update with the correct port (check in Arduino IDE -> Tools -> Port)
arduino_port = "/dev/cu.usbserial-1130"  # Change this as needed
baud_rate = 9600  # Must match the baud rate in the Arduino sketch

# Thresholds for Spider Plant
TEMP_MIN = 18      # Minimum temperature in °C
TEMP_MAX = 30      # Maximum temperature in °C
HUMIDITY_MIN = 40  # Minimum humidity in %
HUMIDITY_MAX = 70  # Maximum humidity in %
SUNLIGHT_MIN = 500 # Minimum sunlight in lux
SUNLIGHT_MAX = 1500 # Maximum sunlight in lux
SOIL_MOISTURE_THRESHOLD = 40  # Minimum soil moisture in %

def get_suggestions(temp, humidity, sunlight, soil_moisture):
    suggestions = []
    if temp < TEMP_MIN:
        suggestions.append("Increase temperature to maintain optimal growth conditions.")
    elif temp > TEMP_MAX:
        suggestions.append("Decrease temperature to prevent overheating.")
    
    if humidity < HUMIDITY_MIN:
        suggestions.append("Increase humidity levels, such as by misting the plant.")
    elif humidity > HUMIDITY_MAX:
        suggestions.append("Reduce humidity to prevent fungal issues.")
    
    if sunlight < SUNLIGHT_MIN:
        suggestions.append("Move the plant to a brighter location.")
    elif sunlight > SUNLIGHT_MAX:
        suggestions.append("Move the plant to a shaded area to avoid sunburn.")
    
    if soil_moisture < SOIL_MOISTURE_THRESHOLD:
        suggestions.append("Water the plant to maintain healthy soil moisture.")
    
    return suggestions

try:
    # Open the serial connection
    ser = serial.Serial(arduino_port, baud_rate)
    print("Connected to Arduino on", arduino_port)
    time.sleep(2)  # Wait for Arduino to initialize

    while True:
        # Check if Arduino has sent data
        if ser.in_waiting > 0:
            # Read and decode data from Arduino
            data = ser.readline().decode('utf-8').strip()

            # Parse the data (assumes format: "Temp,Humidity,Light,Moisture")
            try:
                temp, humidity, sunlight, soil_moisture = map(float, data.split(','))
                
                print("\n--- Sensor Readings ---")
                print(f"Temperature: {temp:.2f} °C")
                print(f"Humidity: {humidity:.2f} %")
                print(f"Sunlight: {sunlight:.2f} lux")
                print(f"Soil Moisture: {soil_moisture:.2f} %")

                # Get and display suggestions
                suggestions = get_suggestions(temp, humidity, sunlight, soil_moisture)
                if suggestions:
                    print("\n--- Suggestions ---")
                    for suggestion in suggestions:
                        print(f"- {suggestion}")
                else:
                    print("\nAll conditions are optimal for the plant.")

                # Control pump based on soil moisture
                if soil_moisture < SOIL_MOISTURE_THRESHOLD:
                    print("\nActivating pump to water the plant...")
                    ser.write(b'PUMP_ON\n')  # Command to turn on pump
                    time.sleep(10)  # Watering duration
                    ser.write(b'PUMP_OFF\n')  # Command to turn off pump
                    print("Pump turned off.")
                
                print("\n---------------------------\n")

            except ValueError:
                print("Error: Could not parse data. Check Arduino code and serial communication.")
                
except serial.SerialException:
    print(f"Error: Could not open port {arduino_port}. Make sure Arduino is connected.")
except KeyboardInterrupt:
    print("\nProgram terminated by user.")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()