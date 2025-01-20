let log = [];
let speakerNames = {};

document.getElementById('startBtn').addEventListener('click', () => {
  fetch('/start_recording', {
    method: 'POST'
  })
    .then(response => response.json())
    .then(data => {
      console.log(data.status);
      document.getElementById('startBtn').disabled = true;
      document.getElementById('endBtn').disabled = false;
    })
    .catch(error => {
      console.error('Error:', error);
    });
});

document.getElementById('endBtn').addEventListener('click', () => {
  fetch('/stop_recording', {
    method: 'POST'
  })
    .then(response => response.json())
    .then(data => {
      log = data.log;
      console.log('Log:', log);
      document.getElementById('startBtn').disabled = false;
      document.getElementById('endBtn').disabled = true;
      document.getElementById('downloadBtn').disabled = false;
    })
    .catch(error => {
      console.error('Error:', error);
    });
});

document.getElementById('downloadBtn').addEventListener('click', () => {
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
  a.download = 'transcript.txt';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
});