from flask import Blueprint, render_template, request, jsonify, current_app
import os
import wave
import pyaudio
import threading
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig, ResultReason, CancellationReason
import logging

app = Blueprint('app', __name__)

# Global variables for recording
is_recording = False
frames = []
recording_thread = None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global is_recording, frames, recording_thread
    is_recording = True
    frames = []
    recording_thread = threading.Thread(target=record_audio)
    recording_thread.start()
    return jsonify({'status': 'Recording started'})

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global is_recording, recording_thread
    is_recording = False
    if recording_thread:
        recording_thread.join()
    filename = os.path.join(current_app.root_path, 'recording.wav')
    save_audio(filename)
    try:
        log_file = process_audio(filename)
        # Read the contents of the log file to send back to the client
        if os.path.exists(log_file):
            with open(log_file, 'r') as file:
                log_content = file.read()
            return jsonify({
                'status': 'Recording stopped',
                'log_file': log_file,
                'log_content': log_content
            })
        else:
            return jsonify({
                'status': 'Error',
                'message': 'Log file not created'
            })
    except Exception as e:
        return jsonify({
            'status': 'Error',
            'message': str(e)
        })
    
def record_audio():
    global is_recording, frames
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    while is_recording:
        data = stream.read(1024)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    p.terminate()

def save_audio(filename):
    global frames
    p = pyaudio.PyAudio()
    wf = wave.open(filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(44100)
    wf.writeframes(b''.join(frames))
    wf.close()

def process_audio(filename):
    try:
        from datetime import datetime
        
        speech_key = current_app.config['AZURE_SPEECH_KEY']
        service_region = current_app.config['AZURE_SPEECH_REGION']
        speech_config = SpeechConfig(subscription=speech_key, region=service_region)
        audio_config = AudioConfig(filename=filename)
        speech_recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Enable continuous recognition
        results = []
        done = threading.Event()

        def recognized_callback(evt):
            if evt.result.reason == ResultReason.RecognizedSpeech:
                text = evt.result.text
                timestamp = datetime.now().strftime("%H:%M:%S")

                # Simple speaker identification logic
                speaker = "Not recognized"
                if "my name is" in text.lower():
                    name_start = text.lower().find("my name is") + len("my name is")
                    name_end = text.find(".") if "." in text else len(text)
                    speaker = text[name_start:name_end].strip().title()

                results.append({
                    "timestamp": timestamp,
                    "text": text,
                    "speaker": speaker
                })

        def stop_cb(evt):
            print('CLOSING on {}'.format(evt))
            done.set()

        # Connect callbacks
        speech_recognizer.recognized.connect(recognized_callback)
        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.canceled.connect(stop_cb)

        # Start continuous recognition
        speech_recognizer.start_continuous_recognition()
        
        # Wait for recognition to finish (or timeout)
        done.wait(timeout=30)  # 30 second timeout, adjust as needed

        # Stop continuous recognition
        speech_recognizer.stop_continuous_recognition()

        # Generate log
        log = ""
        for entry in results:
            log += f"Start Time: {entry['timestamp']}\n"
            log += f"Voice to text: {entry['text']}\n"
            log += f"Speaker: {entry['speaker']}\n\n"

        # Save log to a text file
        log_file = os.path.join(current_app.root_path, 'session_log.txt')
        with open(log_file, 'w') as file:
            file.write(log)

        return log_file

    except Exception as e:
        logging.error(f"Exception in process_audio: {str(e)}")
        raise Exception(f"Speech recognition failed: {str(e)}")