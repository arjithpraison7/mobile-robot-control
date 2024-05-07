import json
import cv2
import serial
import time
from flask import Flask, Response

app = Flask(__name__)

camera = cv2.VideoCapture(0)  # Use the appropriate camera index

# Get the maximum resolution supported by the camera
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)  # Set width to 1920 pixels
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  # Set height to 1080 pixels

# Get the actual resolution being used
actual_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Get the frame rate
fps = int(camera.get(cv2.CAP_PROP_FPS))


def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Encode the frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            # Yield the frame as a response with appropriate content type
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return f'My name is Sneha. Your Camera Resolution: {actual_width}x{actual_height}, Frame rate: {fps}'

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/sensor_info')
def sensor_info():
    # Establish serial connection
    ser = serial.Serial('COM6', 9600) # Adjust 'COM3' to match your Arduino's port
    time.sleep(2) # Wait for the serial connection to initialize

    try:
        while True:
            # Read serial data
            if ser.in_waiting > 0:
                serial_data = ser.readline().decode().strip() # Read a line of serial data and decode it
                # print("Received:", serial_data) # Print the received data
    except KeyboardInterrupt:
        ser.close() # Close the serial connection when the program is interrupted

    return serial_data

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


