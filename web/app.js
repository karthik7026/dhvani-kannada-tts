/**
 * Dhvani Kannada Text-to-Speech Studio Frontend Engine
 */

document.addEventListener("DOMContentLoaded", () => {
    // State
    const state = {
        gender: "female",
        voice: "kn-IN-SapnaNeural",
        pitch: 0,           // in Hz (-30 to +30)
        rate: 1.0,          // 0.5x to 1.8x
        volume: 100,        // 0 to 100%
        preset: "natural",
        energyMode: "ultra",// "ultra", "high", "standard"
        isTranslitOn: false,
        uploadedAudioFile: null,
        isPlaying: false,
        isLoading: false,
        currentAudioUrl: null,
        categories: [],
        samples: []
    };

    // DOM Elements
    const kannadaInput = document.getElementById("kannadaInput");
    const charCount = document.getElementById("charCount");
    const wordCount = document.getElementById("wordCount");
    const translitToggleBtn = document.getElementById("translitToggleBtn");
    const translitLabel = document.getElementById("translitLabel");
    const clearTextBtn = document.getElementById("clearTextBtn");
    const normalizedPreview = document.getElementById("normalizedPreview");

    const voiceCards = document.querySelectorAll(".voice-card");
    const voiceCloneUploader = document.getElementById("voiceCloneUploader");
    const audioFileInput = document.getElementById("audioFileInput");
    const uploadFileName = document.getElementById("uploadFileName");

    const presetChips = document.querySelectorAll(".chip");
    const pitchSlider = document.getElementById("pitchSlider");
    const pitchValue = document.getElementById("pitchValue");
    const rateSlider = document.getElementById("rateSlider");
    const rateValue = document.getElementById("rateValue");
    const volumeSlider = document.getElementById("volumeSlider");
    const volumeValue = document.getElementById("volumeValue");

    const audioPlayer = document.getElementById("audioPlayer");
    const playBtn = document.getElementById("playBtn");
    const playIcon = document.getElementById("playIcon");
    const pauseIcon = document.getElementById("pauseIcon");
    const loadingSpinner = document.getElementById("loadingSpinner");
    const stopBtn = document.getElementById("stopBtn");
    const downloadBtn = document.getElementById("downloadBtn");
    const statusText = document.getElementById("statusText");
    const activeVoiceInfo = document.getElementById("activeVoiceInfo");
    const audioScrubber = document.getElementById("audioScrubber");
    const currentTimeEl = document.getElementById("currentTime");
    const durationTimeEl = document.getElementById("durationTime");

    const waveformCanvas = document.getElementById("waveformCanvas");
    const canvasCtx = waveformCanvas.getContext("2d");

    const presetsModal = document.getElementById("presetsModal");
    const openPresetsBtn = document.getElementById("openPresetsBtn");
    const closePresetsBtn = document.getElementById("closePresetsBtn");
    const modalCategories = document.getElementById("modalCategories");
    const modalSamplesList = document.getElementById("modalSamplesList");
    const toast = document.getElementById("toast");

    // 1. Text Metrics & Live Normalization
    function updateTextMetrics() {
        const text = kannadaInput.value;
        charCount.textContent = `${text.length} ಅಕ್ಷರಗಳು`;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        wordCount.textContent = `${words} ಶಬ್ದಗಳು`;
        
        // Debounced normalization update
        clearTimeout(window._normTimeout);
        window._normTimeout = setTimeout(fetchNormalization, 300);
    }

    async function fetchNormalization() {
        const text = kannadaInput.value;
        if (!text.trim()) {
            normalizedPreview.textContent = "(ಖಾಲಿ)";
            return;
        }
        try {
            const res = await fetch("/api/normalize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text })
            });
            if (res.ok) {
                const data = await res.json();
                normalizedPreview.textContent = data.normalized_text;
            }
        } catch (e) {
            // Local client-side fallback normalization
            normalizedPreview.textContent = clientNormalize(text);
        }
    }

    function clientNormalize(text) {
        // Quick numeral expansion client fallback
        const knNums = { '0':'ಸೊನ್ನೆ', '1':'ಒಂದು', '2':'ಎರಡು', '3':'ಮೂರು', '4':'ನಾಲ್ಕು', '5':'ಐದು', '6':'ಆರು', '7':'ಏಳು', '8':'ಎಂಟು', '9':'ಒಂಬತ್ತು' };
        return text.replace(/[0-9]/g, d => knNums[d] || d).replace(/₹(\d+)/g, "$1 ರೂಪಾಯಿಗಳು");
    }

    kannadaInput.addEventListener("input", () => {
        updateTextMetrics();
    });

    clearTextBtn.addEventListener("click", () => {
        kannadaInput.value = "";
        updateTextMetrics();
    });

    // 2. English to Kannada Phonetic Typing (Transliteration)
    translitToggleBtn.addEventListener("click", () => {
        state.isTranslitOn = !state.isTranslitOn;
        translitToggleBtn.classList.toggle("active", state.isTranslitOn);
        translitLabel.textContent = state.isTranslitOn ? "En ➔ ಕ [ON]" : "En ➔ ಕ [OFF]";
        showToast(state.isTranslitOn ? "ಕನ್ನಡ ಲಿಪ್ಯಂತರಣ ಸಕ್ರಿಯವಾಗಿದೆ (Transliteration ON)" : "ಲಿಪ್ಯಂತರಣ ನಿಷ್ಕ್ರಿಯವಾಗಿದೆ (Transliteration OFF)");
    });

    // Simple phonetic mapper
    const translitMap = {
        'namaskara': 'ನಮಸ್ಕಾರ', 'kannada': 'ಕನ್ನಡ', 'shubhodaya': 'ಶುಭೋದಯ',
        'karnataka': 'ಕರ್ನಾಟಕ', 'hegiddeera': 'ಹೇಗಿದ್ದೀರ', 'dhanyavada': 'ಧನ್ಯವಾದ',
        'shubhadina': 'ಶುಭದಿನ', 'bharata': 'ಭಾರತ', 'desha': 'ದೇಶ'
    };

    kannadaInput.addEventListener("keyup", (e) => {
        if (!state.isTranslitOn) return;
        if (e.key === " " || e.key === "Enter") {
            const text = kannadaInput.value;
            const words = text.split(" ");
            const lastWord = words[words.length - 2]; // word before space
            if (lastWord && translitMap[lastWord.toLowerCase()]) {
                words[words.length - 2] = translitMap[lastWord.toLowerCase()];
                kannadaInput.value = words.join(" ");
                updateTextMetrics();
            }
        }
    });

    // 3. Voice Selection & Presets
    voiceCards.forEach(card => {
        card.addEventListener("click", () => {
            voiceCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            
            const gender = card.dataset.gender;
            const voice = card.dataset.voice;
            const preset = card.dataset.preset;

            state.gender = gender;
            state.voice = voice || "kn-IN-SapnaNeural";

            if (gender === "custom") {
                voiceCloneUploader.classList.remove("hidden");
                state.preset = "custom";
                updateStatusMeta("Custom Voice Clone", "ಕಸ್ಟಮ್ ಆಡಿಯೊ");
            } else {
                voiceCloneUploader.classList.add("hidden");
                if (preset === "podcast") {
                    applyPreset("podcast", -5, 1.12);
                } else if (gender === "female") {
                    applyPreset("natural", 0, 1.0);
                } else if (gender === "male") {
                    applyPreset("natural", -5, 1.0);
                }
            }
        });
    });

    // 4. File Upload for Voice Clone & Acoustic Analysis
    const refAudioPreviewCard = document.getElementById("refAudioPreviewCard");
    const refAudioPlayer = document.getElementById("refAudioPlayer");
    const refAudioMeta = document.getElementById("refAudioMeta");
    const analysisDetails = document.getElementById("analysisDetails");
    const directCloneBtn = document.getElementById("directCloneBtn");

    audioFileInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (file) {
            state.uploadedAudioFile = file;
            uploadFileName.textContent = `✓ ${file.name}`;
            
            // 1. Show audio preview player
            const fileUrl = URL.createObjectURL(file);
            refAudioPlayer.src = fileUrl;
            refAudioPreviewCard.classList.remove("hidden");
            directCloneBtn.disabled = false;
            
            // 2. Analyze acoustic profile
            analysisDetails.textContent = "ಧ್ವನಿ ಮಾದರಿಯನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...";
            try {
                const formData = new FormData();
                formData.append("reference_audio", file);
                const res = await fetch("/api/analyze_audio", {
                    method: "POST",
                    body: formData
                });
                if (res.ok) {
                    const data = await res.json();
                    refAudioMeta.textContent = `${data.duration_sec}s • ${data.pitch_hz} Hz`;
                    analysisDetails.textContent = `ವಿಶ್ಲೇಷಣೆ: ${data.gender === 'male' ? 'ಪುರುಷ' : 'ಮಹಿಳಾ'} ಧ್ವನಿ • ಪಿಚ್: ${data.pitch_hz} Hz • ರೆಸೋನೆನ್ಸ್: ${data.vocal_resonance}x`;
                    showToast(`"${file.name}" ವಿಶ್ಲೇಷಣೆ ಪೂರ್ಣಗೊಂಡಿದೆ!`);
                }
            } catch (err) {
                refAudioMeta.textContent = `${file.name}`;
                analysisDetails.textContent = "ಆಡಿಯೊ ಮಾದರಿ ಸಿದ್ಧವಾಗಿದೆ.";
            }
        }
    });

    directCloneBtn.addEventListener("click", () => {
        if (!state.uploadedAudioFile) {
            showToast("ದಯವಿಟ್ಟು ಮೊದಲು ಆಡಿಯೊ ಫೈಲ್ ಆಯ್ಕೆ ಮಾಡಿ");
            return;
        }
        synthesizeAndPlay();
    });

    // 5. Preset Chips
    presetChips.forEach(chip => {
        chip.addEventListener("click", () => {
            presetChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");

            const preset = chip.dataset.preset;
            const pitchStr = chip.dataset.pitch;
            const rateStr = chip.dataset.rate;

            const pitch = parseInt(pitchStr) || 0;
            const rate = parseFloat(rateStr) ? 1.0 + (parseFloat(rateStr) / 100) : 1.0;

            applyPreset(preset, pitch, rate);
        });
    });

    function applyPreset(presetKey, pitchVal, rateVal) {
        state.preset = presetKey;
        state.pitch = pitchVal;
        state.rate = rateVal;

        pitchSlider.value = pitchVal;
        pitchValue.textContent = `${pitchVal > 0 ? '+' : ''}${pitchVal} Hz`;

        rateSlider.value = rateVal.toFixed(2);
        rateValue.textContent = `${rateVal.toFixed(2)}x`;

        // Update active chip
        presetChips.forEach(c => {
            c.classList.toggle("active", c.dataset.preset === presetKey);
        });

        updateStatusMeta();
    }

    // Energy Chips Listener
    const energyChips = document.querySelectorAll(".energy-chip");
    energyChips.forEach(chip => {
        chip.addEventListener("click", () => {
            energyChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            state.energyMode = chip.dataset.energy;
            showToast(`ಎನರ್ಜಿ ಮೋಡ್: ${chip.textContent.trim()}`);
            updateStatusMeta();
        });
    });

    // 6. Sliders Event Listeners
    pitchSlider.addEventListener("input", () => {
        state.pitch = parseInt(pitchSlider.value);
        pitchValue.textContent = `${state.pitch > 0 ? '+' : ''}${state.pitch} Hz`;
        updateStatusMeta();
    });

    rateSlider.addEventListener("input", () => {
        state.rate = parseFloat(rateSlider.value);
        rateValue.textContent = `${state.rate.toFixed(2)}x`;
        updateStatusMeta();
    });

    volumeSlider.addEventListener("input", () => {
        state.volume = parseInt(volumeSlider.value);
        volumeValue.textContent = `${state.volume}%`;
        audioPlayer.volume = state.volume / 100;
    });

    function updateStatusMeta(customName, customPreset) {
        const voiceName = customName || (state.gender === "female" ? "Sapna (ಸ್ಪಪ್ನಾ)" : "Gagan (ಗಗನ್)");
        const presetName = customPreset || (state.preset === "podcast" ? "ಪಾಡ್‌ಕ್ಯಾಸ್ಟ್ ನಿರೂಪಕ" : "ಸ್ವಾಭಾವಿಕ");
        activeVoiceInfo.textContent = `${voiceName} • ${presetName} • ${state.pitch}Hz • ${state.rate.toFixed(2)}x`;
    }

    // 7. Synthesis & Playback
    playBtn.addEventListener("click", () => {
        if (state.isPlaying) {
            audioPlayer.pause();
            setPlaybackState("paused");
        } else if (audioPlayer.src && audioPlayer.currentTime > 0 && !audioPlayer.ended && audioPlayer.paused) {
            audioPlayer.play();
            setPlaybackState("playing");
        } else {
            synthesizeAndPlay();
        }
    });

    stopBtn.addEventListener("click", () => {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        setPlaybackState("stopped");
    });

    async function synthesizeAndPlay() {
        const text = kannadaInput.value.trim();
        if (!text) {
            showToast("ದಯವಿಟ್ಟು ಪಠ್ಯವನ್ನು ನಮೂದಿಸಿ");
            return;
        }

        setPlaybackState("loading");

        try {
            let res;
            if (state.gender === "custom" && state.uploadedAudioFile) {
                // Multi-part voice clone synthesis
                const formData = new FormData();
                formData.append("text", text);
                formData.append("pitch", (1.0 + state.pitch / 50).toString());
                formData.append("rate", state.rate.toString());
                formData.append("energy_level", state.energyMode);
                formData.append("reference_audio", state.uploadedAudioFile);

                const apiKeyInput = document.getElementById("cloningApiKey");
                if (apiKeyInput && apiKeyInput.value.trim()) {
                    formData.append("api_key", apiKeyInput.value.trim());
                }

                res = await fetch("/api/clone_voice", {
                    method: "POST",
                    body: formData
                });
            } else {
                // Standard Neural Synthesis
                const pitchStr = `${state.pitch >= 0 ? '+' : ''}${state.pitch}Hz`;
                const rateDelta = Math.round((state.rate - 1.0) * 100);
                const rateStr = `${rateDelta >= 0 ? '+' : ''}${rateDelta}%`;

                res = await fetch("/api/synthesize", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        text,
                        voice: state.voice,
                        pitch: pitchStr,
                        rate: rateStr,
                        energy_mode: state.energyMode,
                        volume: "+0%"
                    })
                });
            }

            if (!res.ok) {
                throw new Error("ಸಂಶ್ಲೇಷಣೆ ವಿಫಲವಾಗಿದೆ (Synthesis failed)");
            }

            const blob = await res.blob();
            if (state.currentAudioUrl) {
                URL.revokeObjectURL(state.currentAudioUrl);
            }
            state.currentAudioUrl = URL.createObjectURL(blob);
            audioPlayer.src = state.currentAudioUrl;
            audioPlayer.volume = state.volume / 100;
            audioPlayer.play();

            setPlaybackState("playing");
            showToast("ಧ್ವನಿ ಸಿದ್ಧವಾಗಿದೆ! ನುಡಿಸಲಾಗುತ್ತಿದೆ...");

        } catch (err) {
            console.error(err);
            setPlaybackState("stopped");
            showToast(`ದೋಷ: ${err.message}`);
        }
    }

    function setPlaybackState(status) {
        state.isPlaying = (status === "playing");
        state.isLoading = (status === "loading");

        playIcon.classList.toggle("hidden", state.isPlaying || state.isLoading);
        pauseIcon.classList.toggle("hidden", !state.isPlaying);
        loadingSpinner.classList.toggle("hidden", !state.isLoading);

        if (status === "playing") statusText.textContent = "ನುಡಿಸಲಾಗುತ್ತಿದೆ (Playing)";
        else if (status === "paused") statusText.textContent = "ವಿರಾಮಗೊಳಿಸಲಾಗಿದೆ (Paused)";
        else if (status === "loading") statusText.textContent = "ಧ್ವನಿ ತಯಾರಾಗುತ್ತಿದೆ...";
        else statusText.textContent = "ಸಿದ್ಧವಾಗಿದೆ (Ready)";
    }

    // Audio Progress & Scrubber
    audioPlayer.addEventListener("timeupdate", () => {
        if (!audioPlayer.duration) return;
        const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        audioScrubber.value = progress;
        currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
        durationTimeEl.textContent = formatTime(audioPlayer.duration);
    });

    audioPlayer.addEventListener("ended", () => {
        setPlaybackState("stopped");
        audioScrubber.value = 0;
        currentTimeEl.textContent = "0:00";
    });

    audioScrubber.addEventListener("input", () => {
        if (audioPlayer.duration) {
            audioPlayer.currentTime = (audioScrubber.value / 100) * audioPlayer.duration;
        }
    });

    function formatTime(secs) {
        if (isNaN(secs)) return "0:00";
        const m = Math.floor(secs / 60);
        const s = Math.floor(secs % 60);
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    // Download Audio MP3
    downloadBtn.addEventListener("click", () => {
        if (!state.currentAudioUrl) {
            showToast("ಮೊದಲು ಆಡಿಯೊ ಸಂಶ್ಲೇಷಿಸಿ ನಂತರ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ");
            return;
        }
        const a = document.createElement("a");
        a.href = state.currentAudioUrl;
        a.download = `dhvani_kannada_${Date.now()}.mp3`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        showToast("ಆಡಿಯೊ ಡೌನ್‌ಲೋಡ್ ಆಗಿದೆ!");
    });

    // 8. Waveform Animation (Canvas Visualizer)
    function drawVisualizer() {
        requestAnimationFrame(drawVisualizer);
        canvasCtx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);

        const bars = 16;
        const barWidth = 4;
        const spacing = 3;
        const startX = 6;

        for (let i = 0; i < bars; i++) {
            let height = 4;
            if (state.isPlaying) {
                height = Math.floor(Math.sin(Date.now() * 0.008 + i * 0.6) * 12 + 16);
            }
            const x = startX + i * (barWidth + spacing);
            const y = (waveformCanvas.height - height) / 2;

            const grad = canvasCtx.createLinearGradient(0, waveformCanvas.height, 0, 0);
            grad.addColorStop(0, "#f97316");
            grad.addColorStop(1, "#ec4899");

            canvasCtx.fillStyle = grad;
            canvasCtx.beginPath();
            canvasCtx.roundRect(x, y, barWidth, height, 2);
            canvasCtx.fill();
        }
    }
    drawVisualizer();

    // 9. Presets Modal & Samples Library
    const samplePresets = [
        {
            title: "ಪಾಡ್‌ಕ್ಯಾಸ್ಟ್ ವಿವರಣೆ (Geopolitics)",
            category: "ಸುದ್ದಿ & ವಾರ್ತೆಗಳು",
            text: "ಎಸ್‌ಸಿಒ ಸಮ್ಮೇಳನದಲ್ಲಿ ಭಾರತದ ಪಾತ್ರ ಅತ್ಯಂತ ಪ್ರಮುಖವಾಗಿದೆ. ಜಾಗತಿಕ ದಕ್ಷಿಣದ ದೇಶಗಳಿಗೆ ಭಾರತ ನೀಡಿದ ೧೦ ಅಂಶಗಳ ಕಾರ್ಯಸೂಚಿ ಇಡೀ ವಿಶ್ವದ ಗಮನ ಸೆಳೆದಿದೆ. ದೇಶದ ರಾಷ್ಟ್ರೀಯ ಭದ್ರತೆ ಮತ್ತು ಆರ್ಥಿಕ ಶಕ್ತಿ ಎರಡೂ ಅಷ್ಟೇ ಮುಖ್ಯ.",
            gender: "male",
            preset: "podcast"
        },
        {
            title: "ಶುಭೋದಯ ಮತ್ತು ಸ್ವಾಗತ",
            category: "ದೈನಂದಿನ ಸಂಭಾಷಣೆ",
            text: "ಶುಭೋದಯ! ಧ್ವನಿ ಕನ್ನಡ ಅಪ್ಲಿಕೇಶನ್‌ಗೆ ನಿಮಗೆ ಹೃತ್ಪೂರ್ವಕ ಸ್ವಾಗತ. ಇಂದು ನಿಮ್ಮ ದಿನ ಮಂಗಳಕರವಾಗಿರಲಿ.",
            gender: "female",
            preset: "natural"
        },
        {
            title: "ಹವಾಮಾನ ವರದಿ",
            category: "ಸುದ್ದಿ & ವಾರ್ತೆಗಳು",
            text: "ಕರ್ನಾಟಕ ರಾಜ್ಯದ ಹವಾಮಾನ ಇಲಾಖೆಯ ಪ್ರಕಾರ, ಕರಾವಳಿ ಮತ್ತು ಮಲೆನಾಡು ಭಾಗಗಳಲ್ಲಿ ಮುಂದಿನ ೨೪ ಗಂಟೆಗಳಲ್ಲಿ ಸಾಧಾರಣ ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆಯಿದೆ. ತಾಪಮಾನ ೨೮ ಡಿಗ್ರಿ ಸೆಲ್ಸಿಯಸ್ ಇರಲಿದೆ.",
            gender: "male",
            preset: "news"
        },
        {
            title: "ಕನ್ನಡ ನಾಡು ನುಡಿ",
            category: "ಸಾಹಿತ್ಯ & ಕವನಗಳು",
            text: "ಹೆಸರಾಯಿತು ಕರ್ನಾಟಕ, ಉಸಿರಾಗಲಿ ಕನ್ನಡ. ಸಿರಿಗನ್ನಡಂ ಗೆಲ್ಗೆ, ಸಿರಿಗನ್ನಡಂ ಬಾಳ್ಗೆ! ಎಲ್ಲಾದರು ಇರು ಎಂತಾದರು ಇರು ಎಂದೆಂದಿಗೂ ನೀ ಕನ್ನಡವಾಗಿರು.",
            gender: "female",
            preset: "softFemale"
        },
        {
            title: "ಜನಪ್ರಿಯ ಗಾದೆ ಮಾತುಗಳು",
            category: "ಜನಪ್ರಿಯ ಗಾದೆಗಳು",
            text: "ಹಾಸಿಗೆ ಇದ್ದಷ್ಟೇ ಕಾಲು ಚಾಚು. ಕೈ ಕೆಸರಾದರೆ ಬಾಯಿ ಮೊಸರು. ವಿದ್ಯೆಯೇ ಮನುಷ್ಯನ ನಿಜವಾದ ಆಭರಣ.",
            gender: "female",
            preset: "natural"
        },
        {
            title: "ಸಂಖ್ಯೆ ಮತ್ತು ಕರೆನ್ಸಿ ಉಚ್ಚಾರಣೆ",
            category: "ಸಂಖ್ಯೆ & ಕರೆನ್ಸಿ",
            text: "ನಮ್ಮ ಪುಸ್ತಕ ಮಳಿಗೆಯಲ್ಲಿ ಒಟ್ಟು ೧೨೫೦ ಪುಸ್ತಕಗಳಿವೆ. ಇದರ ಬೆಲೆ ₹೪೫೦ ಮಾತ್ರ. ನಿಮ್ಮ ಶೇಕಡಾ ೨೦% ರಿಯಾಯಿತಿ ಸಿಗಲಿದೆ.",
            gender: "male",
            preset: "natural"
        }
    ];

    function renderModalPresets() {
        const categories = [...new Set(samplePresets.map(s => s.category))];
        modalCategories.innerHTML = "";
        
        categories.forEach((cat, i) => {
            const btn = document.createElement("button");
            btn.className = `category-pill ${i === 0 ? 'active' : ''}`;
            btn.textContent = cat;
            btn.addEventListener("click", () => {
                document.querySelectorAll(".category-pill").forEach(p => p.classList.remove("active"));
                btn.classList.add("active");
                renderSamplesForCategory(cat);
            });
            modalCategories.appendChild(btn);
        });

        renderSamplesForCategory(categories[0]);
    }

    function renderSamplesForCategory(cat) {
        modalSamplesList.innerHTML = "";
        const filtered = samplePresets.filter(s => s.category === cat);
        filtered.forEach(item => {
            const div = document.createElement("div");
            div.className = "sample-item";
            div.innerHTML = `
                <div class="sample-title">${item.title}</div>
                <div class="sample-text">${item.text}</div>
            `;
            div.addEventListener("click", () => {
                kannadaInput.value = item.text;
                updateTextMetrics();
                
                // Select matching gender and preset
                const targetCard = Array.from(voiceCards).find(c => c.dataset.gender === item.gender);
                if (targetCard) targetCard.click();
                
                const targetChip = Array.from(presetChips).find(c => c.dataset.preset === item.preset);
                if (targetChip) targetChip.click();

                presetsModal.classList.add("hidden");
                showToast(`"${item.title}" ಲೋಡ್ ಆಗಿದೆ!`);
            });
            modalSamplesList.appendChild(div);
        });
    }

    openPresetsBtn.addEventListener("click", () => {
        renderModalPresets();
        presetsModal.classList.remove("hidden");
    });

    closePresetsBtn.addEventListener("click", () => {
        presetsModal.classList.add("hidden");
    });

    presetsModal.addEventListener("click", (e) => {
        if (e.target === presetsModal) presetsModal.classList.add("hidden");
    });

    // Toast Utility
    function showToast(msg) {
        toast.textContent = msg;
        toast.classList.remove("hidden");
        clearTimeout(window._toastTimer);
        window._toastTimer = setTimeout(() => {
            toast.classList.add("hidden");
        }, 2500);
    }

    // Initialize
    updateTextMetrics();
    updateStatusMeta();
});
