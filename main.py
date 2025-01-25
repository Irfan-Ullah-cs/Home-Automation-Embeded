# Import libraries
import utime
import network
import urequests
import json
from machine import Pin, ADC
from hcsr04 import HCSR04
from dht import DHT22

# WiFi credentials
SSID = "Galaxy A06 0a23"
PASSWORD = "12345678"

# Server details
SERVER_URL = "http://192.168.152.113:8080/api"

# Pins
DHT_PIN = 21
LIGHT_SENSOR_PIN = 34
LED1_PIN = 13
LED2_PIN = 12
LED3_PIN = 27
TRIG_PIN = 32
ECHO_PIN = 33
MAX_BIN_HEIGHT = 100  

# Initialize sensors and pins
dht_sensor = DHT22(Pin(DHT_PIN))
light_sensor = ADC(Pin(LIGHT_SENSOR_PIN))
light_sensor.atten(ADC.ATTN_11DB)  # Configure ADC to read 0-3.3V

led1 = Pin(LED1_PIN, Pin.OUT)
led2 = Pin(LED2_PIN, Pin.OUT)
led3 = Pin(LED3_PIN, Pin.OUT)

ultrasonic_sensor = HCSR04(trigger_pin=TRIG_PIN, echo_pin=ECHO_PIN)

# Connect to WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        print("Connecting to WiFi...")
        utime.sleep(1)
    print("Connected to WiFi:", wlan.ifconfig())

# Get distance from ultrasonic sensor
def get_distance():
    try:
        distance = ultrasonic_sensor.distance_cm()
        
        # Calculate bin fill percentage
        if distance is not None and distance <= MAX_BIN_HEIGHT:
            fill_percentage = ((MAX_BIN_HEIGHT - distance) / MAX_BIN_HEIGHT) * 100
            return round(fill_percentage, 2)
        elif distance > MAX_BIN_HEIGHT:
            print("Error: Bin height exceeded maximum limit")
            return None
        else:
            return None
    except OSError as e:
        print("Ultrasonic sensor error:", e)
        return None

def send_sensor_data():
    try:
        # Read sensor values
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
        light_level = light_sensor.read()
        bin_level = get_distance()
        
        # Only send data if bin_level is valid
        if bin_level is not None and bin_level >= 0:
            # Get current timestamp
            current_time = utime.localtime()
            timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                current_time[0], current_time[1], current_time[2],
                current_time[3], current_time[4], current_time[5]
            )
            
            # Create JSON payload
            payload = {
                "timestamp": timestamp,
                "temperature": temperature,
                "humidity": humidity,
                "lightLevel": light_level,
                "binLevel": bin_level,
            }
            
            # Send HTTP POST request
            response = urequests.post(SERVER_URL + "/sensor-data", json=payload)
            print("Data sent successfully:", response.text)
            response.close()
        else:
            print("Invalid bin level. Data not sent.")
    except Exception as e:
        print("Error sending sensor data:", e)

# Update LED states based on server response
def update_led_states():
    try:
        response = urequests.get(SERVER_URL + "/led-states")
        if response.status_code == 200:
            led_states = response.json()
            for state in led_states:
                led_number = state["ledNumber"]
                is_on = state["on"]
                if led_number == 1:
                    led1.value(1 if is_on else 0)
                elif led_number == 2:
                    led2.value(1 if is_on else 0)
                elif led_number == 3:
                    led3.value(1 if is_on else 0)
        else:
            print("Failed to get LED states:", response.status_code)
        response.close()
    except Exception as e:
        print("Error updating LED states:", e)

# Main loop
def main():
    connect_wifi()
    while True:
        print("Sending sensor data...")
        send_sensor_data()
        update_led_states()
        utime.sleep(5)

if __name__ == "__main__":
    main()