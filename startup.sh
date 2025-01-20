#!/bin/bash

# Install PortAudio
apt-get update
apt-get install -y portaudio19-dev

# Start the application
gunicorn app:app