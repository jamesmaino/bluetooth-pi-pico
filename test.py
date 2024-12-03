from bleak import BleakClient
import asyncio
import time

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
        
        while True:
            # Send "toggle" every 2 seconds
            await client.write_gatt_char(UART_RX_UUID, b'toggle\r\n')
            print("Sent 'toggle' command.")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())