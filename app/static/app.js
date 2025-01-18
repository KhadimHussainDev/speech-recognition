let mediaRecorder;
let audioChunks = [];

document.getElementById('startBtn').addEventListener('click', async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.start();

  mediaRecorder.addEventListener('dataavailable', event => {
    audioChunks.push(event.data);
  });

  mediaRecorder.addEventListener('stop', () => {
    const audioBlob = new Blob(audioChunks);
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.play();
    // Send audioBlob to the server for processing
  });
});

document.getElementById('endBtn').addEventListener('click', () => {
  mediaRecorder.stop();
});