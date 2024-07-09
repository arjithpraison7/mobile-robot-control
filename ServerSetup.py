import serial
from flask import Flask, jsonify, Response
import threading
import time
import cv2

app = Flask(__name__)

# Camera setup
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
camera.set(cv2.CAP_PROP_FPS, 30)

actual_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(camera.get(cv2.CAP_PROP_FPS))

# Serial setup
SERIAL_PORT = 'COM6'
BAUD_RATE = 9600
latest_value = "No data received yet"

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud rate.")
except serial.SerialException as e:
    print(f"Error opening serial port {SERIAL_PORT}: {e}")
    ser = None

def read_from_serial():
    global latest_value
    if ser:
        while True:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    print(f"Received: {line}")  # Debugging line
                    latest_value = line
            except Exception as e:
                print(f"Error reading from serial port: {e}")
                time.sleep(1)
    else:
        print("Serial port not available. Exiting read_from_serial.")
        while True:
            time.sleep(1)

if ser:
    thread = threading.Thread(target=read_from_serial)
    thread.daemon = True
    thread.start()

# Flask routes
@app.route('/')
def index():
    return f'Your Camera Resolution: {actual_width}x{actual_height}, Frame rate: {fps}'

@app.route('/video_feed')
def video_feed():
    def generate_frames():
        while True:
            success, frame = camera.read()
            if not success:
                break
            else:
                ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Flask route to handle data reception
@app.route('/receive_data', methods=['POST', 'GET'])
def receive_data():
    global received_data
    if request.method == 'POST':
        received_data = request.data.decode('utf-8')
        if ser and ser.is_open:
            ser.baudrate = 19200  # Change baud rate to 19200 for sending data
            ser.write((received_data.lower() + '\n').encode())
            print(f"Sent from Server: {received_data}")
            ser.baudrate = 9600  # Revert baud rate to 9600 for receiving sensor data
        return "Data received", 200
    elif request.method == 'GET':
        return received_data
        
# Flask route to handle handshake
@app.route('/handshake')
def handshake():
    return 'handshake successful'

@app.route('/data', methods=['GET'])
def get_data():
    if latest_value is not None:
        return latest_value
    else:
        return latest_value

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', use_reloader=False)
