from flask import Blueprint, render_template, request, redirect, url_for, current_app
import os
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig, ResultReason, CancellationReason
import logging

app = Blueprint('app', __name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.form['data']
    # Process the data here
    return redirect(url_for('app.home'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filename = os.path.join(current_app.root_path, file.filename)
        file.save(filename)
        # Process the audio file here
        text, speaker = process_audio(filename)
        # Save the text log
        with open(os.path.join(current_app.root_path, 'log.txt'), 'a') as log_file:
            log_file.write(f'{filename}: {speaker} said {text}\n')
        return 'File uploaded and processed successfully'

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