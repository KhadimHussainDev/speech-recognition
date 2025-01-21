from flask import Blueprint, render_template, request, jsonify, current_app
import threading
import time
import azure.cognitiveservices.speech as speechsdk
import json
import os
app = Blueprint('app', __name__)

# Global variables for recording
is_recording = False
recognition_thread = None
start_time = None
log_file_path = '/home/log.json'
log_dir = os.path.dirname(log_file_path)

# Ensure the directory exists
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/start_recognition', methods=['POST'])
def start_recognition():
    global is_recording, recognition_thread, start_time
    is_recording = True
    start_time = time.time()
    # Clear the log file
    with open(log_file_path, 'w') as log_file:
        json.dump([], log_file)
    app_context = current_app._get_current_object()
    recognition_thread = threading.Thread(target=recognize_speech, args=(app_context,))
    recognition_thread.start()
    return jsonify({'status': 'Recognition started'})

@app.route('/stop_recognition', methods=['POST'])
def stop_recognition():
    global is_recording, recognition_thread
    is_recording = False
    recognition_thread.join()
    # Read the log file
    with open(log_file_path, 'r') as log_file:
        log_data = json.load(log_file)
    print("Recognition stopped. Log:", log_data)  # Debugging statement
    return jsonify({'log': log_data})
results = []
def recognize_speech(app_context):
    global is_recording, log_file_path
    results.append("recognize_speech")

    with app_context.app_context():
        results.append("appcontext")

        # Create speech config
        speech_config = speechsdk.SpeechConfig(
            subscription=current_app.config['AZURE_SPEECH_KEY'],
            region=current_app.config['AZURE_SPEECH_REGION']
        )

        # Create audio config
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        # Store transcribed results
        conversation = []
        done = threading.Event()

        def handle_result(evt):
            results.append("handle_result")
            if evt.result.text:
                # For testing, assign alternating speaker IDs
                speaker_id = len(conversation) % 2 + 1
                speaker = f"Speaker {speaker_id}"
                offset_in_seconds = evt.result.offset / 10_000_000
                timestamp = time.strftime("%M:%S", time.gmtime(offset_in_seconds))
                result = {
                    'timestamp': timestamp,
                    'speaker': speaker,
                    'text': evt.result.text
                }
                print(result)
                conversation.append(result)
                results.append(result)
                # Append to the log file
                with open(log_file_path, 'r+') as log_file:
                    log_data = json.load(log_file)
                    log_data.append(result)
                    log_file.seek(0)
                    json.dump(log_data, log_file)
                print(f"[{timestamp}] {speaker}: {evt.result.text}")  # Debugging statement

        def stop_cb(evt):
            print('CLOSING on {}'.format(evt))
            done.set()

        # Connect callbacks
        speech_recognizer.recognized.connect(handle_result)
        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.canceled.connect(stop_cb)

        # Start recognition
        speech_recognizer.start_continuous_recognition()

        # Wait for the recognition to complete
        while is_recording:
            time.sleep(1)

        # Stop recognition
        speech_recognizer.stop_continuous_recognition_async()
        done.wait()

@app.route('/get_results', methods=['GET'])
def get_results():
    global results
    return jsonify(results)