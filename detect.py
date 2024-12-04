import argparse
import asyncio
import random
import cv2

from picamera2 import Picamera2, Preview, MappedArray
from picamera2.devices import Hailo
from bleak import BleakClient

# UUID for the UART RX characteristic
UART_RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dCCA9E"

# Address of your Raspberry Pi Pico
PICO_ADDRESS = "2C:CF:67:98:33:08"  # Replace with your Pico's address


def extract_detections(hailo_output, w, h, class_names, threshold=0.5):
    """Extract detections from the HailoRT-postprocess output."""
    results = []
    for class_id, detections in enumerate(hailo_output[0]):
        for detection in detections:
            score = detection[4]
            if score >= threshold:
                y0, x0, y1, x1 = detection[:4]
                bbox = (int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))
                results.append([class_names[class_id], bbox, score])
    return results


def draw_objects(request, detections):
    if detections:
        with MappedArray(request, "main") as m:
            for class_name, bbox, score in detections:
                x0, y0, x1, y1 = bbox
                label = f"{class_name} %{int(score * 100)}"
                cv2.rectangle(m.array, (x0, y0), (x1, y1), (0, 255, 0, 0), 2)
                cv2.putText(m.array, label, (x0 + 5, y0 + 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0, 0), 1, cv2.LINE_AA)


async def long_running_task(client):
    """Simulates a long-running asynchronous task with variable duration."""
    duration = random.choice([5])  # You can adjust the durations here
    await client.write_gatt_char(UART_RX_UUID, b'toggle\r\n')
    print("Sent 'toggle' command.")
    print(f"Long-running task started (duration: {duration} seconds)...")
    for i in range(1, duration + 1):
        await asyncio.sleep(1)
        print(f"Long-running task: {i} seconds")
    print("Long-running task done.")


async def capture_frame(picam2):
    """Asynchronously captures a frame from the camera."""
    return await asyncio.to_thread(picam2.capture_array, 'lores')


async def process_frame(hailo, frame, video_w, video_h, class_names, threshold):
    """Processes a frame using the Hailo model."""
    results = hailo.run(frame)
    return extract_detections(results, video_w, video_h, class_names, threshold)


async def main():
    parser = argparse.ArgumentParser(description="Detection Example")
    parser.add_argument("-m", "--model", help="Path for the HEF model.",
                        default="/usr/local/share/hailo-models/yolov8s_h8.hef")
    parser.add_argument("-l", "--labels", default="coco.txt",
                        help="Path to a text file containing labels.")
    parser.add_argument("-s", "--score_thresh", type=float, default=0.5,
                        help="Score threshold, must be a float between 0 and 1.")
    args = parser.parse_args()

    with Hailo(args.model) as hailo:
        model_h, model_w, _ = hailo.get_input_shape()
        video_w, video_h = 1280, 720

        with open(args.labels, 'r', encoding="utf-8") as f:
            class_names = f.read().splitlines()

        async with BleakClient(PICO_ADDRESS) as client:
            if not client.is_connected:
                print("Failed to connect to device!")
                return
            print(f"Connected to {PICO_ADDRESS}")

            with Picamera2() as picam2:
                main = {'size': (video_w, video_h), 'format': 'RGB888'}
                lores = {'size': (model_w, model_h), 'format': 'RGB888'}
                controls = {'FrameRate': 30}
                config = picam2.create_preview_configuration(main, sensor={'bit_depth': 10}, lores=lores, controls=controls)
                picam2.configure(config)
                picam2.start_preview(Preview.QT, x=0, y=0, width=video_w, height=video_h)
                picam2.start()

                detections = None
                picam2.pre_callback = lambda request: draw_objects(request, detections)

                task_running = asyncio.Event()
                task_running.set()

                while True:
                    try:
                        frame = await capture_frame(picam2)
                        detections = await process_frame(hailo, frame, video_w, video_h, class_names, args.score_thresh)

                        for class_name, _, _ in detections:
                            if class_name == "cup" and task_running.is_set():
                                task_running.clear()
                                asyncio.create_task(long_running_task(client)).add_done_callback(
                                    lambda task: task_running.set()
                                )
                    except Exception as e:
                        print(f"Error during processing or capture: {e}")


if __name__ == "__main__":
    asyncio.run(main())