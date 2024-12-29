# PhoneAsMic

Turn your phone into a virtual microphone for OBS streaming using WebSocket technology.

## Overview

PhoneAsMic is a web application that allows you to use your phone's microphone as an audio input source for OBS streaming software. It works by:
1. Capturing audio from your phone's browser
2. Streaming it via WebSocket to your PC
3. Creating a virtual audio device that OBS can recognize

## Features

- Real-time audio streaming via WebSocket
- Low-latency audio transmission
- Web-based interface for phone browsers
- Virtual audio device creation for Windows
- Compatible with OBS Studio
- Audio visualization and level monitoring
- Simple connection management
- Noise reduction and echo cancellation

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: HTML5, JavaScript (WebRTC)
- **Protocol**: WebSocket
- **Virtual Audio**: VB-Audio Virtual Cable (recommended)

## Prerequisites

1. Python 3.7+ installed on your PC
2. Windows 10/11
3. VB-Audio Virtual Cable installed ([Download Here](https://vb-audio.com/Cable/))
4. Phone with a modern web browser (Chrome/Firefox/Safari)
5. Both PC and phone on the same local network

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/phoneasmic.git
cd phoneasmic
```

2. Create and activate virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
.\venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Generate SSL certificates (required for HTTPS):
```bash
# Using the provided Python script
python src/generate_cert.py

# This will create two files:
# - cert.pem (certificate)
# - key.pem (private key)
```

5. Install VB-Audio Virtual Cable:
   - Download from: https://vb-audio.com/Cable/
   - Run the installer
   - Restart your computer if prompted

## Usage

1. Start the server:
```bash
# For HTTPS (recommended for phone browsers)
uvicorn src.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

2. On your phone:
   - Open your browser
   - Navigate to `https://<your-pc-ip>:8443`
   - Accept the security warning about self-signed certificate
   - Allow microphone permissions when prompted

3. In OBS:
   - Add a new Audio Input Capture
   - Select "CABLE Output (VB-Audio Virtual Cable)" as the Device
   - You should now see audio levels when speaking into your phone

## SSL Certificate Notes

The application requires HTTPS for accessing your phone's microphone. The provided `generate_cert.py` script creates self-signed certificates:

1. The script uses OpenSSL through Python to generate:
   - A new RSA private key (`key.pem`)
   - A self-signed certificate (`cert.pem`)

2. When accessing the web interface, your browser will show a security warning because the certificate is self-signed. This is normal and you can:
   - Click "Advanced" or similar
   - Choose "Proceed to site" or "Accept the risk and continue"

3. The certificates are valid for one year. To regenerate them:
```bash
python src/generate_cert.py
```

## Troubleshooting

1. **No audio in OBS?**
   - Check if VB-Audio Virtual Cable is properly installed
   - Verify the correct audio input is selected in OBS
   - Check the volume levels in Windows sound settings

2. **Can't access the website?**
   - Ensure your phone and PC are on the same network
   - Check if your PC's firewall is blocking the connection
   - Verify you're using the correct IP address

3. **Microphone not working?**
   - Make sure you're using HTTPS (required for microphone access)
   - Check if you've granted microphone permissions in your browser
   - Try refreshing the page

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FastAPI for the excellent WebSocket support
- VB-Audio for virtual audio device capabilities
- All contributors and users of this project

---

╔═════════════════════════════════════════════════════════════════╗
║                                                                 ║
║   ██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗ █████╗ ███████╗   ║
║   ██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝██╔══██╗██╔════╝   ║
║   ██████╔╝███████║██║   ██║██╔██╗ ██║█████╗  ███████║███████╗   ║
║   ██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║██╔══╝  ██╔══██║╚════██║   ║
║   ██║     ██║  ██║╚██████╔╝██║ ╚████║███████╗██║  ██║███████║   ║
║   ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚══════╝   ║
║                                                                 ║
╚═════════════════════════════════════════════════════════════════╝

All generated using Cursor - The AI-first Code Editor
"Turn your phone into a mic, let your voice be heard through the bytes."


