from deepgram import Deepgram
import asyncio
import aiohttp

# DEEPGRAM_API_KEY = 'f81ff09854f9bb1535aa5909dd52ee7bff5c4e79'
DEEPGRAM_API_KEY='967c5ce3f89d5cbb8c74107737ba36b9e1a5ba20'
# URL = 'http://stream.live.vc.bbcmedia.co.uk/bbc_world_service'

URL = 'http://127.0.0.1:5500/index.html'

transcriptions = []  # A list to save all received transcriptions

async def main():
    deepgram = Deepgram(DEEPGRAM_API_KEY)
    
    try:
        deepgramLive = await deepgram.transcription.live({
            'smart_format': True,
            'interim_results': False,
            'language': 'en-US',
            'model': 'nova',
        })
    except Exception as e:
        print(f'Could not open socket: {e}')
        return
    
    deepgramLive.registerHandler(deepgramLive.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
    
    # def handle_transcript(transcript):
    #     print(transcript)
    #     transcriptions.append(transcript)

    def handle_transcript(transcript):
        channel = transcript.get('channel', {})
        alternatives = channel.get('alternatives', [{}])
        transcript_text = alternatives[0].get('transcript', '')
        print(transcript_text)
        transcriptions.append(transcript_text)

        
    deepgramLive.registerHandler(deepgramLive.event.TRANSCRIPT_RECEIVED, handle_transcript)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as resp:
            while True:
                chunk = await resp.content.readany()
                if not chunk:
                    break
                deepgramLive.send(chunk)
                
    await deepgramLive.finish()

    # Writing transcriptions to a file
    with open('transcriptions.txt', 'w') as f:
        for transcript in transcriptions:
            f.write(str(transcript) + '\n')


asyncio.run(main())
