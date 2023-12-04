// Node.js script for live audio transcription using Deepgram
require('dotenv').config(); 
const WebSocket = require('ws');
const { Readable } = require('stream');
const recorder = require('node-record-lpcm16'); // npm package for audio recording
const { spawn } = require('child_process');

class Transcriber {
    constructor(deepgramApiKey) {
        this.deepgramApiKey = deepgramApiKey;
        this.deepgramUrl = 'wss://api.deepgram.com/v1/listen?punctuate=true&encoding=linear16&sample_rate=16000';
        this.audioStream = null;
        this.ws = null;
    }

    startRecording() {
        const ffmpegArgs = [
            '-f', 'dshow',          // '-f dshow' for Windows, '-f avfoundation' for MacOS, '-f alsa' for Linux
            '-i', 'audio=Microphone (Realtek(R) Audio)', // Replace with your microphone device name
            '-ar', '16000',         // Sample rate
            '-ac', '1',             // Channels
            '-f', 's16le',          // Format (signed 16-bit little-endian)
            '-'                     // Output to stdout
        ];

        this.audioStream = spawn('ffmpeg', ffmpegArgs);

        this.audioStream.stderr.on('data', (data) => {
            console.error(`stderr: ${data}`);
        });

        this.audioStream.on('close', (code) => {
            console.log(`child process exited with code ${code}`);
        });

        // Pipe the audio stream to the WebSocket
        this.audioStream.stdout.on('data', (chunk) => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(chunk);
            }
        });

        return this.audioStream.stdout;
    }

    stopRecording() {
        if (this.audioStream) {
            this.audioStream.kill(); // Correct method to stop the audio stream
        }
    }

    async transcribe() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(this.deepgramUrl, {
                headers: { Authorization: `Token ${this.deepgramApiKey}` }
            });

            this.ws.on('open', () => {
                console.log('WebSocket connection established. Start speaking...');
                this.startRecording();
            });

            this.ws.on('message', (data) => {
                const response = JSON.parse(data);
                if (response.is_final) {
                    const transcript = response.channel.alternatives[0].transcript;
                    if (transcript.trim()) {
                        console.log('Transcript:', transcript);
                        this.stopRecording();
                        this.ws.close();
                        resolve(transcript);
                    }
                }
            });

            this.ws.on('error', (error) => {
                console.error('WebSocket error:', error);
                this.stopRecording();
                reject(error);
            });

            this.ws.on('close', () => {
                console.log('WebSocket connection closed.');
                this.stopRecording();
            });
        });
    }
}

function transcribeStream() {
    const deepgramApiKey = process.env.DEEPGRAM_API_KEY;
    if (!deepgramApiKey) {
        console.error('Please set the DEEPGRAM_API_KEY environment variable.');
        return;
    }

    const transcriber = new Transcriber(deepgramApiKey);
    transcriber.transcribe().then((transcript) => {
        console.log('Final Transcript:', transcript);
    }).catch((error) => {
        console.error('Error:', error);
    });
}

transcribeStream();
