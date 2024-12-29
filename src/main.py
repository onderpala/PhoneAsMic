from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List
import numpy as np
import sounddevice as sd
import queue
import threading
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="PhoneAsMic")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Audio settings
SAMPLE_RATE = 44100
CHANNELS = 1
DTYPE = np.float32
BUFFER_SIZE = 2048  # Match with frontend's processor buffer size
QUEUE_SIZE = 32

# Audio queue for buffering
audio_queue = queue.Queue(maxsize=QUEUE_SIZE)

# Audio output stream
output_stream = None
is_streaming = False

def audio_callback(outdata, frames, time, status):
    """Callback for sounddevice output stream"""
    global is_streaming
    
    if status:
        logger.warning(f'Audio callback status: {status}')
    
    try:
        if not is_streaming:
            outdata.fill(0)
            return
            
        data = audio_queue.get_nowait()
        if len(data) < frames:
            # Pad with zeros if we don't have enough data
            padding = np.zeros((frames - len(data), CHANNELS), dtype=DTYPE)
            data = np.vstack([data, padding])
        outdata[:] = data[:frames].reshape(-1, CHANNELS)
    except queue.Empty:
        if is_streaming:
            logger.debug("Buffer underrun - no data available")
        outdata.fill(0)

def initialize_audio():
    """Initialize the audio output stream"""
    global output_stream, is_streaming
    try:
        # List available audio devices
        devices = sd.query_devices()
        logger.info("\n=== Available Audio Devices ===")
        virtual_cable_idx = None
        
        # First, look specifically for VB-Audio Virtual Cable
        for i, dev in enumerate(devices):
            # Log detailed device info
            logger.info(f"\nDevice {i}: {dev['name']}")
            logger.info(f"  Max Channels: Input={dev['max_input_channels']}, Output={dev['max_output_channels']}")
            logger.info(f"  Default Sample Rate: {dev['default_samplerate']}")
            
            # Look for CABLE Input device
            if 'cable input' in dev['name'].lower():
                if dev['max_output_channels'] > 0:
                    virtual_cable_idx = i
                    logger.info(f"\n>>> Found Virtual Cable at index {i}: {dev['name']}")
                    break

        if virtual_cable_idx is None:
            logger.error("\nNo Virtual Audio Cable found! Please install VB-Audio Virtual Cable")
            logger.error("Download from: https://vb-audio.com/Cable/")
            return False

        # Get the selected device
        device_info = devices[virtual_cable_idx]
        logger.info(f"\nInitializing Virtual Cable:")
        logger.info(f"  Device: {device_info['name']}")
        logger.info(f"  Sample Rate: {SAMPLE_RATE} Hz")
        logger.info(f"  Channels: {CHANNELS}")
        logger.info(f"  Buffer Size: {BUFFER_SIZE} samples")

        # Create the output stream
        output_stream = sd.OutputStream(
            device=virtual_cable_idx,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=BUFFER_SIZE,
            callback=audio_callback,
            finished_callback=lambda: logger.info("Audio stream finished")
        )
        
        # Test the stream
        try:
            output_stream.start()
            logger.info("  Stream Test: Success - Stream started")
            output_stream.stop()
            logger.info("  Stream Test: Success - Stream stopped")
        except sd.PortAudioError as e:
            logger.error(f"  Stream Test: Failed - {e}")
            return False

        logger.info(f"\nAudio output stream successfully initialized using: {device_info['name']}")
        return True
    except sd.PortAudioError as e:
        logger.error(f"\nError initializing audio: {e}")
        return False

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New client connected. Total connections: {len(self.active_connections)}")
        
        global is_streaming
        if not output_stream:
            if not initialize_audio():
                logger.error("Failed to initialize audio")
                return
        
        if not output_stream.active:
            output_stream.start()
            is_streaming = True
            logger.info("Audio stream started")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Remaining connections: {len(self.active_connections)}")
        
        global is_streaming
        if not self.active_connections and output_stream and output_stream.active:
            is_streaming = False
            output_stream.stop()
            logger.info("Audio stream stopped")

    async def process_audio(self, data: bytes):
        """Process incoming audio data and send it to the virtual audio device"""
        try:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(data, dtype=DTYPE)
            
            if audio_data.size > 0:
                # Log audio data statistics
                max_val = np.max(np.abs(audio_data))
                if max_val > 0:  # Only log when we have actual audio
                    logger.debug(f"Audio data - Size: {audio_data.size}, Max amplitude: {max_val:.3f}")
                
                # Normalize audio
                audio_data = np.clip(audio_data, -1.0, 1.0)
                
                # Reshape for stereo if needed
                if CHANNELS == 2:
                    audio_data = np.column_stack((audio_data, audio_data))
                
                # Put processed audio data in the queue
                try:
                    if audio_queue.qsize() < QUEUE_SIZE:
                        audio_queue.put_nowait(audio_data)
                        logger.debug(f"Queue status: {audio_queue.qsize()}/{QUEUE_SIZE}")
                    else:
                        # If queue is full, remove oldest item
                        try:
                            audio_queue.get_nowait()
                            audio_queue.put_nowait(audio_data)
                            logger.warning("Queue full, dropped oldest frame")
                        except queue.Empty:
                            pass
                except queue.Full:
                    logger.warning("Audio buffer full, dropping frame")
            else:
                logger.warning("Received empty audio data")
                    
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            import traceback
            logger.error(traceback.format_exc())

manager = ConnectionManager()

# Routes
@app.get("/")
async def get():
    with open("templates/index.html") as f:
        html_content = f.read()
    return HTMLResponse(html_content)

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_bytes()
            await manager.process_audio(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    global is_streaming
    if output_stream:
        is_streaming = False
        output_stream.stop()
        output_stream.close()
        logger.info("Audio stream closed") 