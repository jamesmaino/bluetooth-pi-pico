from picamera2 import Picamera2, Preview
import time
import asyncio
from bleak import BleakClient
import libcamera

# UUID for the UART RX characteristic
UART_RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dCCA9E"

# Address of your Raspberry Pi Pico
PICO_ADDRESS = "2C:CF:67:98:33:08"

async def main():
    async with BleakClient(PICO_ADDRESS) as client:
        if not client.is_connected:
            print("Failed to connect to device!")
            return
        print(f"Connected to {PICO_ADDRESS}")


        main = {'size': (1280, 720), 'format': 'RGB888'}
        lores = {'size': (640, 640), 'format': 'RGB888'}
        controls = {'FrameRate': 30}
        sensor = {"bit_depth":10}

        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(main, lores=lores, sensor=sensor, controls=controls))
        picam2.set_controls({"AnalogueGain": 1.0})
        picam2.start_preview(Preview.QT)
        picam2.start()

        # Process each low resolution camera frame.
        count = 0
        while True:
            frame = picam2.capture_array('lores')
            count = count + 1
            if count % 120 == 0: 
                await client.write_gatt_char(UART_RX_UUID, b'toggle\r\n')
                await asyncio.sleep(2)
                print("Sent 'toggle' command.")
            


if __name__ == "__main__":
    asyncio.run(main())