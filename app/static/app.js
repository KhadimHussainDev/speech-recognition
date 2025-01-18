let transcript = '';
let speaker = '';

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
      console.log('Transcript:', data.transcript);
      console.log('Speaker:', data.speaker);
      transcript = data.transcript;
      speaker = data.speaker;
      document.getElementById('startBtn').disabled = false;
      document.getElementById('endBtn').disabled = true;
      document.getElementById('downloadBtn').disabled = false;
    })
    .catch(error => {
      console.error('Error:', error);
    });
});

document.getElementById('downloadBtn').addEventListener('click', () => {
  const text = `Speaker: ${speaker}\nTranscript: ${transcript}`;
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'transcript.txt';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
});