import asyncio
import time
import signal
import logging
from bleak import BleakClient
from ai_camera import IMX500Detector

# Configuration (consider moving to a separate config file)
PICO_ADDRESS = "2C:CF:67:98:33:08"
TARGET_LABEL = "cup"
DETECTION_THRESHOLD = 0.2
DEBOUNCE_DELAY = 0.5  # seconds
CONNECTION_TIMEOUT = 10.0  # seconds

# UUIDs for UART characteristics
UART_TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Global flag for graceful exit
is_running = True

def signal_handler(sig, frame):
    global is_running
    logger.info("Exiting...")
    is_running = False

signal.signal(signal.SIGINT, signal_handler)

# Initialize the AI camera
camera = IMX500Detector()  # Or IMX500Detector(framerate=5) if you want to set framerate
camera.start(show_preview=False)

async def connect_and_run():
    while is_running:
        try:
            async with BleakClient(PICO_ADDRESS, timeout=CONNECTION_TIMEOUT) as client:
                logger.info(f"Connected to {PICO_ADDRESS}")
                await client.start_notify(UART_TX_UUID, notification_handler)
                await run_detection_loop(client) # Call the detection loop here

        except Exception as e:
            logger.error(f"Connection error: {e}")
            if is_running:
                logger.info("Attempting to reconnect in 5 seconds...")
            await asyncio.sleep(5)

async def run_detection_loop(client):
    """Main detection loop (runs while connected)"""
    last_toggle_time = 0  # Initialize last_toggle_time here in the loop
    while is_running and client.is_connected:
        try:
            detections = camera.get_detections()
            labels = camera.get_labels()

            for detection in detections:
                if labels[int(detection.category)] == TARGET_LABEL and detection.conf > DETECTION_THRESHOLD:
                    logger.info(f"{TARGET_LABEL} detected with {detection.conf:.2f} confidence!")
                    if time.time() - last_toggle_time > DEBOUNCE_DELAY:
                        asyncio.create_task(asyncio.shield(send_toggle_command(client)))  # Don't await here
                        last_toggle_time = time.time()

            await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in detection loop: {e}")
            break # Exit the inner loop to trigger reconnection


async def send_toggle_command(client):
    try:
        await client.write_gatt_char(UART_RX_UUID, b'toggle\r\n')
        logger.info("Sent toggle command to Pico")
    except Exception as e:
        logger.error(f"Error sending command: {e}")


async def notification_handler(sender, data):
    message = data.decode('utf-8')
    logger.info(f"Received message from Pico: {message}")



if __name__ == "__main__":
    try:
        asyncio.run(connect_and_run())
    finally:
        camera.stop()
        logger.info("Camera stopped.")