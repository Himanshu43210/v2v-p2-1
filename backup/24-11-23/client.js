// require('dotenv').config();
// const WebSocket = require('ws');
// const Deepgram = require('deepgram');
// const record = require('node-record-lpcm16');

// const DEEPGRAM_API_KEY = process.env.DEEPGRAM_API_KEY;
// const WEBSOCKET_URL = "ws://127.0.0.1:65432"; // Update this to your server's WebSocket URL

// const deepgram = new Deepgram(DEEPGRAM_API_KEY);

// async function main() {
//     const ws = new WebSocket(WEBSOCKET_URL);

//     ws.on('open', () => {
//         console.log('Connected to WebSocket server.');

//         // Start recording and sending audio
//         const recorder = record.start({
//             sampleRateHertz: 24000,
//             threshold: 0,
//             verbose: false,
//             recordProgram: 'rec', // Try also "arecord" or "sox"
//             silence: '10.0',
//         });

//         recorder.on('data', (data) => {
//             ws.send(data);
//         });

//         ws.on('message', (message) => {
//             console.log('Received:', message);
//         });

//         ws.on('close', () => {
//             console.log('WebSocket closed.');
//             record.stop();
//         });
//     });
// }

// main().catch(console.error);
require('dotenv').config();
const { Deepgram } = require('@deepgram/sdk');
const WebSocket = require('ws');

// Replace with your Deepgram API Key
const DEEPGRAM_API_KEY = process.env.DEEPGRAM_API_KEY;

// Initialize Deepgram SDK
const deepgram = new Deepgram(DEEPGRAM_API_KEY);

// Set up Deepgram live transcription
const deepgramLive = deepgram.transcription.live({
    punctuate: true,
    // additional options as needed
});

// Listen for the 'open' event
deepgramLive.addListener('open', () => {
    console.log('Connected to Deepgram.');
});

// Listen for the 'close' event
deepgramLive.addListener('close', () => {
    console.log('Deepgram connection closed.');
});

// Listen for the 'error' event
deepgramLive.addListener('error', (error) => {
    console.error('Error:', error);
});

// Listen for the 'transcriptReceived' event
deepgramLive.addListener('transcriptReceived', (transcription) => {
    console.log('Transcript:', transcription.data);
});

// Function to simulate sending audio data to Deepgram
// Replace this with your actual audio data source
function sendAudioData() {
    // Simulate sending audio data
    // In a real application, this should be the raw audio data
    const AUDIO_STREAM_DATA = '...'; // Replace with actual audio stream data
    deepgramLive.send(AUDIO_STREAM_DATA);
}

// Start sending audio data (simulate for this example)
setInterval(sendAudioData, 1000); // Adjust interval as needed for your audio data rate

// Close the connection after a certain time (for demonstration purposes)
setTimeout(() => {
    deepgramLive.finish();
}, 30000); // Adjust as needed
