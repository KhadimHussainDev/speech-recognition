from flask import Blueprint, render_template, request, jsonify, current_app
import os
import wave
import sounddevice as sd
import numpy as np
import threading
import time
import azure.cognitiveservices.speech as speechsdk
import logging
from datetime import datetime, timedelta
from pydub import AudioSegment
from pydub.playback import play
import io

app = Blueprint('app', __name__)

# Global variables for recording
is_recording = False
frames = []
recording_thread = None
start_time = None
log = []

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global is_recording, frames, recording_thread, start_time, log
    is_recording = True
    frames = []
    log = []
    start_time = time.time()
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
    conversation = transcribe_audio(filename, current_app.config['AZURE_SPEECH_KEY'], current_app.config['AZURE_SPEECH_REGION'])
    return jsonify({'log': conversation})

def record_audio():
    global is_recording, frames
    frames = []
    def callback(indata, frame_count, time_info, status):
        if is_recording:
            frames.append(indata.copy())
    with sd.InputStream(samplerate=44100, channels=1, callback=callback):
        while is_recording:
            sd.sleep(100)

def save_audio(filename):
    global frames
    if not frames:
        print("No audio data to save.")
        return
    frames = np.concatenate(frames, axis=0)
    frames = (frames * 32767).astype(np.int16)  # Convert to 16-bit PCM format
    wf = wave.open(filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)  # 2 bytes for 16-bit PCM
    wf.setframerate(44100)
    wf.writeframes(frames.tobytes())
    wf.close()

def transcribe_audio(filename, subscription_key, region):
    """
    Transcribe audio file with speaker diarization using Azure Speech Services
    """
    # Create speech config
    speech_config = speechsdk.SpeechConfig(
        subscription=subscription_key,
        region=region
    )
    
    # Set properties for conversation transcription
    speech_config.set_property(
        speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
        "1000"
    )
    
    # Create audio config
    audio_config = speechsdk.audio.AudioConfig(filename=filename)
    
    # Create speech recognizer with conversation transcription
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    
    # Store transcribed results
    conversation = []
    done = threading.Event()

    def handle_result(evt):
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
            conversation.append(result)
            print(f"[{timestamp}] {speaker}: {evt.result.text}")

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
    done.wait()
    
    # Stop recognition
    speech_recognizer.stop_continuous_recognition_async()
    
    return conversation