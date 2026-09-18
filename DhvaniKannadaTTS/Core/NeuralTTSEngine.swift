import Foundation
import AVFoundation

/// High-Definition Neural TTS Engine for Kannada (Gagan & Sapna voices)
/// Streams neural audio with precise pitch, rate, and prosody controls.
public final class NeuralTTSEngine: NSObject, TTSEngineProtocol, AVAudioPlayerDelegate {
    
    public weak var delegate: TTSEngineDelegate?
    public let engineType: TTSEngineType = .neural
    
    private var audioPlayer: AVAudioPlayer?
    private var fallbackEngine: NativeTTSEngine?
    private var currentTask: URLSessionDataTask?
    
    public override init() {
        super.init()
    }
    
    public var isSpeaking: Bool {
        audioPlayer?.isPlaying ?? false
    }
    
    public var isPaused: Bool {
        guard let player = audioPlayer else { return false }
        return !player.isPlaying && player.currentTime > 0
    }
    
    public func speak(
        text: String,
        gender: VoiceGender,
        pitch: Float,
        rate: Float,
        volume: Float,
        voiceId: String? = nil
    ) {
        stop()
        
        let normalizedText = KannadaNormalizer.normalize(text: text)
        guard !normalizedText.isEmpty else { return }
        
        // Convert pitch multiplier to SSML pitch string (+/-Hz or %)
        let ssmlPitch = calculateSSMLPitch(pitchMultiplier: pitch)
        let ssmlRate = calculateSSMLRate(rateMultiplier: rate)
        let ssmlVolume = calculateSSMLVolume(volumeMultiplier: volume)
        
        let voiceName = selectVoiceName(for: gender, voiceId: voiceId)
        
        delegate?.ttsEngineDidStartSpeaking()
        
        synthesizeNeuralAudio(
            text: normalizedText,
            voiceName: voiceName,
            pitch: ssmlPitch,
            rate: ssmlRate,
            volume: ssmlVolume
        ) { [weak self] result in
            guard let self = self else { return }
            DispatchQueue.main.async {
                switch result {
                case .success(let audioData):
                    self.playAudioData(audioData)
                case .failure(let error):
                    print("Neural TTS failed (\(error.localizedDescription)), falling back to On-Device Native Engine...")
                    self.useNativeFallback(
                        text: text,
                        gender: gender,
                        pitch: pitch,
                        rate: rate,
                        volume: volume,
                        voiceId: voiceId
                    )
                }
            }
        }
    }
    
    public func pause() {
        audioPlayer?.pause()
        delegate?.ttsEngineDidPauseSpeaking()
    }
    
    public func resume() {
        if let player = audioPlayer, !player.isPlaying {
            player.play()
            delegate?.ttsEngineDidContinueSpeaking()
        }
    }
    
    public func stop() {
        currentTask?.cancel()
        currentTask = nil
        if let player = audioPlayer, player.isPlaying {
            player.stop()
        }
        audioPlayer = nil
        fallbackEngine?.stop()
    }
    
    public func synthesizeToFile(
        text: String,
        gender: VoiceGender,
        pitch: Float,
        rate: Float,
        volume: Float,
        voiceId: String?,
        completion: @escaping (Result<URL, Error>) -> Void
    ) {
        let normalizedText = KannadaNormalizer.normalize(text: text)
        let voiceName = selectVoiceName(for: gender, voiceId: voiceId)
        let ssmlPitch = calculateSSMLPitch(pitchMultiplier: pitch)
        let ssmlRate = calculateSSMLRate(rateMultiplier: rate)
        let ssmlVolume = calculateSSMLVolume(volumeMultiplier: volume)
        
        synthesizeNeuralAudio(
            text: normalizedText,
            voiceName: voiceName,
            pitch: ssmlPitch,
            rate: ssmlRate,
            volume: ssmlVolume
        ) { result in
            switch result {
            case .success(let audioData):
                let tempDir = FileManager.default.temporaryDirectory
                let fileUrl = tempDir.appendingPathComponent("dhvani_neural_\(UUID().uuidString).mp3")
                do {
                    try audioData.write(to: fileUrl)
                    DispatchQueue.main.async {
                        completion(.success(fileUrl))
                    }
                } catch {
                    DispatchQueue.main.async {
                        completion(.failure(error))
                    }
                }
            case .failure(let error):
                // Fallback to Native file export
                let fallback = NativeTTSEngine()
                fallback.synthesizeToFile(
                    text: text,
                    gender: gender,
                    pitch: pitch,
                    rate: rate,
                    volume: volume,
                    voiceId: voiceId,
                    completion: completion
                )
            }
        }
    }
    
    // MARK: - Private Helpers
    private func selectVoiceName(for gender: VoiceGender, voiceId: String?) -> String {
        if let id = voiceId, id.contains("Neural") {
            return id
        }
        switch gender {
        case .female: return "kn-IN-SapnaNeural"
        case .male: return "kn-IN-GaganNeural"
        }
    }
    
    private func calculateSSMLPitch(pitchMultiplier: Float) -> String {
        // pitchMultiplier: 0.5 to 2.0 (1.0 = 0Hz)
        let deltaHz = Int((pitchMultiplier - 1.0) * 35.0)
        return deltaHz >= 0 ? "+\(deltaHz)Hz" : "\(deltaHz)Hz"
    }
    
    private func calculateSSMLRate(rateMultiplier: Float) -> String {
        // rateMultiplier: 0.5 to 2.0 (1.0 = 0%)
        let deltaPercent = Int((rateMultiplier - 1.0) * 100.0)
        return deltaPercent >= 0 ? "+\(deltaPercent)%" : "\(deltaPercent)%"
    }
    
    private func calculateSSMLVolume(volumeMultiplier: Float) -> String {
        let deltaPercent = Int((volumeMultiplier - 1.0) * 50.0)
        return deltaPercent >= 0 ? "+\(deltaPercent)%" : "\(deltaPercent)%"
    }
    
    private func buildSSML(text: String, voiceName: String, pitch: String, rate: String, volume: String) -> String {
        let escapedText = text
            .replacingOccurrences(of: "&", with: "&amp;")
            .replacingOccurrences(of: "<", with: "&lt;")
            .replacingOccurrences(of: ">", with: "&gt;")
        
        return """
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='kn-IN'>
            <voice name='\(voiceName)'>
                <prosody pitch='\(pitch)' rate='\(rate)' volume='\(volume)'>
                    \(escapedText)
                </prosody>
            </voice>
        </speak>
        """
    }
    
    private func synthesizeNeuralAudio(
        text: String,
        voiceName: String,
        pitch: String,
        rate: String,
        volume: String,
        completion: @escaping (Result<Data, Error>) -> Void
    ) {
        let ssml = buildSSML(text: text, voiceName: voiceName, pitch: pitch, rate: rate, volume: volume)
        
        guard let url = URL(string: "https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?trustedclienttoken=6A5AA1D4EAFF4E9FB37E23D68491D6F4") else {
            completion(.failure(NSError(domain: "DhvaniTTS", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid synthesis endpoint"])))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/ssml+xml", forHTTPHeaderField: "Content-Type")
        request.setValue("audio-24khz-48kbitrate-mono-mp3", forHTTPHeaderField: "X-Output-Format")
        request.setValue("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36", forHTTPHeaderField: "User-Agent")
        request.httpBody = ssml.data(using: .utf8)
        
        currentTask = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            guard let data = data, !data.isEmpty else {
                completion(.failure(NSError(domain: "DhvaniTTS", code: -2, userInfo: [NSLocalizedDescriptionKey: "Empty neural audio response"])))
                return
            }
            completion(.success(data))
        }
        currentTask?.resume()
    }
    
    private func playAudioData(_ data: Data) {
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio, options: [.duckOthers])
            try AVAudioSession.sharedInstance().setActive(true)
            
            audioPlayer = try AVAudioPlayer(data: data)
            audioPlayer?.delegate = self
            audioPlayer?.prepareToPlay()
            audioPlayer?.play()
        } catch {
            delegate?.ttsEngineDidFail(error: error)
        }
    }
    
    private func useNativeFallback(
        text: String,
        gender: VoiceGender,
        pitch: Float,
        rate: Float,
        volume: Float,
        voiceId: String?
    ) {
        fallbackEngine = NativeTTSEngine()
        fallbackEngine?.delegate = self.delegate
        fallbackEngine?.speak(
            text: text,
            gender: gender,
            pitch: pitch,
            rate: rate,
            volume: volume,
            voiceId: voiceId
        )
    }
    
    // MARK: - AVAudioPlayerDelegate
    public func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        delegate?.ttsEngineDidFinishSpeaking()
    }
    
    public func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: Error?) {
        if let error = error {
            delegate?.ttsEngineDidFail(error: error)
        }
    }
}
