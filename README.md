# ಧ್ವನಿ - Dhvani Kannada Text-to-Speech Studio (iOS & Web) 🎙️✨

**Dhvani Kannada TTS** is a cross-platform Kannada (`kn-IN` / ಕನ್ನಡ) speech synthesis suite with natural accent, precise pronunciation, male & female voices, **reference-audio voice cloning**, and customizable pitch, speed, and volume controls for both **iOS** and the **Web**.

---

## 🌐 1. Web Studio (ಕನ್ನಡ ವೆಬ್ ಸ್ಟುಡಿಯೋ)

Run the modern Kannada Text-to-Speech Studio in any desktop or mobile browser!

### 🚀 How to Run the Web Studio:

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the Web Studio server:
   ```bash
   python3 server.py
   ```
3. Open **`http://localhost:8000`** in your browser (Chrome, Safari, Firefox, Edge).

### 🌟 Web Studio Features:
- **👩‍💼 Sapna (Female)** & **👨‍💼 Gagan (Male)** Neural voices.
- **🎙️ Podcast Narrator (ನಿರೂಪಕ)**: Energetic, fast-paced presenter voice profile (matching our reference podcast audio).
- **🧬 Custom Voice Clone**: Upload any `.wav` or `.mp3` sample to synthesize Kannada in that exact voice.
- **🎛️ Pitch & Speed Sliders**: Adjust pitch ($-30\text{Hz}$ to $+30\text{Hz}$) and rate ($0.5\times$ to $1.8\times$) in real-time.
- **⌨️ Live Transliteration**: Type English (`namaskara`) to get Kannada (`ನಮಸ್ಕಾರ`).
- **🌊 Animated Sound Waveform**: Real-time visual equalizer canvas during speech.
- **📥 One-Click MP3 Download**: Export and save any generated speech to audio file.

---

## 📱 2. Native iOS App (ಆ್ಯಪಲ್ ಐಒಎಸ್ ಆ್ಯಪ್)

A native SwiftUI and AVFoundation app for iPhone and iPad.

### 🚀 How to Run in Xcode:
1. Open the project in **Xcode**:
   ```bash
   open "/Users/karthiku/Downloads/Text speech/DhvaniKannadaTTS.xcodeproj"
   ```
2. Select your **iOS Simulator** (iPhone 15/16 Pro) or your connected **iPhone/iPad**.
3. Press **`Cmd + R`** to run.

---

## 🧠 Smart Kannada Text Normalizer
Both Web and iOS include the built-in **Kannada Normalizer**:
- **Numbers to Spoken Kannada Words**:
  - `1250` or `೧೨೫೦` ➔ *"ಒಂದು ಸಾವಿರದ ಇನ್ನೂರ ಐವತ್ತು"*
  - `1947` ➔ *"ಒಂದು ಸಾವಿರದ ಒಂಬೈನೂರ ನಲವತ್ತೇಳು"*
- **Currency Symbols**:
  - `₹450` or `Rs. 450` ➔ *"ನಾನೂರ ಐವತ್ತು ರೂಪಾಯಿಗಳು"*
- **Percentages & Ordinals**:
  - `20%` ➔ *"ಇಪ್ಪತ್ತು ಪ್ರತಿಶತ"*
  - `1ನೇ` ➔ *"ಒಂದನೇ"*
- **Punctuation & Cadence**:
  - Automatic breath pauses on commas, full stops, and Indian danda (`।`).

---

## 📁 Project Structure

```
Text speech/
├── DhvaniKannadaTTS.xcodeproj/       # [iOS] Native Xcode Project
├── DhvaniKannadaTTS/                 # [iOS] SwiftUI & AVFoundation App
│
├── web/                              # [WEB] Modern Web Studio Frontend
│   ├── index.html                    # Web UI layout & audio visualizer
│   ├── styles.css                    # Glassmorphism styling & Kannada theme
│   └── app.js                        # Playback, visualizer & transliteration
├── server.py                         # [WEB BACKEND] FastAPI server
├── kannada_normalizer.py             # [CORE] Python Text Normalizer with Sandhi
├── requirements.txt                  # Python dependencies
│
└── README.md
```

---

## 📄 License
MIT License. Built for the Kannada developer and speaker community.
