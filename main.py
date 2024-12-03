# Import necessary modules
from machine import Pin
import bluetooth
from ble_simple_peripheral import BLESimplePeripheral
import time

# Create a Bluetooth Low Energy (BLE) object
ble = bluetooth.BLE()
# Create an instance of the BLESimplePeripheral class with the BLE object
sp = BLESimplePeripheral(ble)

# Create a Pin object for the onboard LED, configure it as an output
led = Pin("LED", Pin.OUT)

# Initialize the LED state to 0 (off)
led_state = 0

# Define a callback function to handle received data
def on_rx(data):
    print("Data received: ", data)  # Print the received data
    global led_state  # Access the global variable led_state
    if data == b'toggle\r\n':  # Check if the received data is "toggle"
        led.value(not led_state)  # Toggle the LED state (on/off)
        led_state = 1 - led_state  # Update the LED state


# Set the debounce time to 0. Used for switch debouncing
debounce_time=0

# Create a Pin object for Pin 0, configure it as an input with a pull-up resistor
pin = Pin(0, Pin.IN, Pin.PULL_UP)

while True:
    if sp.is_connected():  # Check if a BLE connection is established
        sp.on_write(on_rx)  # Set the callback function for data reception
    
    # Check if the pin value is 0 and if debounce time has elapsed (more than 300 milliseconds)
    if ((pin.value() is 0) and (time.ticks_ms()-debounce_time) > 300):
        # Check if the BLE connection is established
        if sp.is_connected():
            # Create a message string
            msg="pushbutton pressed\n"
            # Send the message via BLE
            sp.send(msg)
        # Update the debounce time    
        debounce_time=time.ticks_ms()
