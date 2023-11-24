require('dotenv').config();
const WebSocket = require('ws');
// const Deepgram = require('deepgram');
const { Deepgram } = require("@deepgram/sdk");


const DEEPGRAM_API_KEY = process.env.DEEPGRAM_API_KEY;
const deepgram = new Deepgram(DEEPGRAM_API_KEY);

async function transcribe() {
    const deepgramUrl = `wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000`;

    const ws = new WebSocket(deepgramUrl, {
        headers: { Authorization: `Token ${DEEPGRAM_API_KEY}` },
    });

    ws.on('open', () => {
        console.log('Connected to Deepgram.');
    });

    ws.on('message', (data) => {
        const response = JSON.parse(data);
        if (response.is_final) {
            const transcript = response.channel.alternatives[0].transcript;
            console.log('Transcript:', transcript);
        }
    });

    ws.on('close', () => {
        console.log('Deepgram connection closed.');
    });

    // Handle sending audio data to Deepgram here...
}

transcribe().catch(console.error);
