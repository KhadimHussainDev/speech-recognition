document.getElementById('startBtn').addEventListener('click', () => {
  fetch('/start_recognition', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
      console.log(data.status);
      document.getElementById('startBtn').disabled = true;
      document.getElementById('endBtn').disabled = false;
      document.getElementById('downloadBtn').disabled = true;
    })
    .catch(error => {
      console.error('Error:', error);
    });
});

document.getElementById('endBtn').addEventListener('click', () => {
  fetch('/stop_recognition', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
      console.log(data.log);
      window.log = data.log; // Store the log data globally for download
      document.getElementById('startBtn').disabled = false;
      document.getElementById('endBtn').disabled = true;
      document.getElementById('downloadBtn').disabled = false;
    })
    .catch(error => {
      console.error('Error:', error);
    });
});

document.getElementById('downloadBtn').addEventListener('click', () => {
  const log = window.log || [];
  const speakerNames = {};
  const updatedLog = log.map(entry => {
    const nameMatch = entry.text.match(/.*my name is (\w+)/i);
    if (nameMatch) {
      speakerNames[entry.speaker] = nameMatch[1];
    }
    const speakerName = speakerNames[entry.speaker] || "Not Recognized";
    return `Start Time: ${entry.timestamp}\nVoice to text: ${entry.text}\nSpeaker: ${speakerName}\n`;
  }).join('\n');

  const blob = new Blob([updatedLog], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'transcription.txt';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
});