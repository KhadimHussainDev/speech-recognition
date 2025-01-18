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
    recording_thread.join()
    filename = os.path.join(current_app.root_path, 'recording.wav')
    save_audio(filename)
    text, speaker = process_audio(filename)
    return jsonify({'transcript': text, 'speaker': speaker})

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
        speech_key = current_app.config['AZURE_SPEECH_KEY']
        service_region = current_app.config['AZURE_SPEECH_REGION']
        speech_config = SpeechConfig(subscription=speech_key, region=service_region)
        audio_config = AudioConfig(filename=filename)
        speech_recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        result = speech_recognizer.recognize_once()
        if result.reason == ResultReason.RecognizedSpeech:
            logging.info(f"Recognized: {result.text}")
            return result.text, "Speaker"  # Replace "Speaker" with actual speaker identification logic
        elif result.reason == ResultReason.NoMatch:
            logging.info("No speech could be recognized")
            return "No speech could be recognized", "Unknown"
        elif result.reason == ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logging.error(f"Speech Recognition canceled: {cancellation_details.reason}")
            if cancellation_details.reason == CancellationReason.Error:
                logging.error(f"Error details: {cancellation_details.error_details}")
            return "Speech Recognition canceled", "Unknown"
        else:
            logging.error(f"Unknown reason: {result.reason}")
            return "Unknown reason", "Unknown"
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        return str(e), "Unknown"