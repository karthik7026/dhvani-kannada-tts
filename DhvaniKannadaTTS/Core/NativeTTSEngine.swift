import Foundation
import AVFoundation

/// Native on-device Kannada TTS Engine using Apple's AVFoundation
public final class NativeTTSEngine: NSObject, TTSEngineProtocol, AVSpeechSynthesizerDelegate {
    
    public weak var delegate: TTSEngineDelegate?
    public let engineType: TTSEngineType = .native
    
    private let synthesizer = AVSpeechSynthesizer()
    private var currentUtterance: AVSpeechUtterance?
    private var isAudioSessionConfigured = false
    
    public override init() {
        super.init()
        synthesizer.delegate = self
        setupAudioSession()
    }
    
    private func setupAudioSession() {
        guard !isAudioSessionConfigured else { return }
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playback, mode: .spokenAudio, options: [.duckOthers])
            try session.setActive(true, options: .notifyOthersOnDeactivation)
            isAudioSessionConfigured = true
        } catch {
            print("Failed to configure AVAudioSession: \(error.localizedDescription)")
        }
    }
    
    public var isSpeaking: Bool {
        synthesizer.isSpeaking
    }
    
    public var isPaused: Bool {
        synthesizer.isPaused
    }
    
    public func speak(
        text: String,
        gender: VoiceGender,
        pitch: Float,
        rate: Float,
        volume: Float,
        voiceId: String? = nil
    ) {
        if synthesizer.isSpeaking {
            synthesizer.stopSpeaking(at: .immediate)
        }
        
        setupAudioSession()
        
        // 1. Phonetically normalize Kannada text (numbers, currencies, etc.)
        let normalizedText = KannadaNormalizer.normalize(text: text)
        guard !normalizedText.isEmpty else { return }
        
        let utterance = AVSpeechUtterance(string: normalizedText)
        
        // 2. Select Kannada Voice (kn-IN)
        if let voice = findKannadaVoice(for: gender, preferredId: voiceId) {
            utterance.voice = voice
        } else {
            // Fallback to system default kn-IN voice
            utterance.voice = AVSpeechSynthesisVoice(language: "kn-IN") ?? AVSpeechSynthesisVoice(language: Locale.current.identifier)
        }
        
        // 3. Configure Pitch Multiplier (0.5 to 2.0)
        // If gender is male, adjust native baseline slightly lower if user has default pitch
        let adjustedPitch: Float
        if gender == .male && pitch == 1.0 {
            adjustedPitch = 0.85
        } else {
            adjustedPitch = pitch
        }
        utterance.pitchMultiplier = max(0.5, min(2.0, adjustedPitch))
        
        // 4. Configure Speech Rate
        // AVSpeechUtteranceDefaultSpeechRate is ~0.5. Scale user rate (0.5x - 2.0x)
        let baseRate = AVSpeechUtteranceDefaultSpeechRate
        let scaledRate = baseRate * rate
        utterance.rate = max(AVSpeechUtteranceMinimumSpeechRate, min(AVSpeechUtteranceMaximumSpeechRate, scaledRate))
        
        // 5. Volume
        utterance.volume = max(0.0, min(1.0, volume))
        
        utterance.preUtteranceDelay = 0.05
        utterance.postUtteranceDelay = 0.05
        
        self.currentUtterance = utterance
        synthesizer.speak(utterance)
    }
    
    public func pause() {
        if synthesizer.isSpeaking && !synthesizer.isPaused {
            synthesizer.pauseSpeaking(at: .word)
        }
    }
    
    public func resume() {
        if synthesizer.isPaused {
            synthesizer.continueSpeaking()
        }
    }
    
    public func stop() {
        if synthesizer.isSpeaking {
            synthesizer.stopSpeaking(at: .immediate)
        }
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
        guard !normalizedText.isEmpty else {
            completion(.failure(NSError(domain: "DhvaniTTS", code: -1, userInfo: [NSLocalizedDescriptionKey: "ಖಾಲಿ ಪಠ್ಯ (Text is empty)"])))
            return
        }
        
        let utterance = AVSpeechUtterance(string: normalizedText)
        utterance.voice = findKannadaVoice(for: gender, preferredId: voiceId) ?? AVSpeechSynthesisVoice(language: "kn-IN")
        utterance.pitchMultiplier = max(0.5, min(2.0, pitch))
        utterance.rate = max(AVSpeechUtteranceMinimumSpeechRate, min(AVSpeechUtteranceMaximumSpeechRate, AVSpeechUtteranceDefaultSpeechRate * rate))
        utterance.volume = max(0.0, min(1.0, volume))
        
        let tempDir = FileManager.default.temporaryDirectory
        let fileUrl = tempDir.appendingPathComponent("dhvani_kannada_\(UUID().uuidString).wav")
        
        var audioFile: AVAudioFile?
        
        synthesizer.write(utterance) { buffer in
            guard let pcmBuffer = buffer as? AVAudioPCMBuffer else { return }
            
            if pcmBuffer.frameLength == 0 {
                // Synthesis completed
                if audioFile != nil {
                    DispatchQueue.main.async {
                        completion(.success(fileUrl))
                    }
                }
                return
            }
            
            do {
                if audioFile == nil {
                    audioFile = try AVAudioFile(
                        forWriting: fileUrl,
                        settings: pcmBuffer.format.settings,
                        commonFormat: .pcmFormatFloat32,
                        interleaved: false
                    )
                }
                try audioFile?.write(from: pcmBuffer)
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
            }
        }
    }
    
    // MARK: - Voice Discovery
    private func findKannadaVoice(for gender: VoiceGender, preferredId: String?) -> AVSpeechSynthesisVoice? {
        let voices = AVSpeechSynthesisVoice.speechVoices().filter { $0.language == "kn-IN" }
        
        if let preferred = preferredId, let match = voices.first(where: { $0.identifier == preferred }) {
            return match
        }
        
        if #available(iOS 13.0, *) {
            if gender == .female {
                if let femaleVoice = voices.first(where: { $0.gender == .female }) {
                    return femaleVoice
                }
            } else {
                if let maleVoice = voices.first(where: { $0.gender == .male }) {
                    return maleVoice
                }
            }
        }
        
        return voices.first ?? AVSpeechSynthesisVoice(language: "kn-IN")
    }
    
    // MARK: - AVSpeechSynthesizerDelegate
    public func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didStart utterance: AVSpeechUtterance) {
        delegate?.ttsEngineDidStartSpeaking()
    }
    
    public func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        delegate?.ttsEngineDidFinishSpeaking()
    }
    
    public func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didPause utterance: AVSpeechUtterance) {
        delegate?.ttsEngineDidPauseSpeaking()
    }
    
    public func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didContinue utterance: AVSpeechUtterance) {
        delegate?.ttsEngineDidContinueSpeaking()
    }
    
    public func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        delegate?.ttsEngineDidCancelSpeaking()
    }
    
    public func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, willSpeakRangeOfSpeechString characterRange: NSRange, utterance: AVSpeechUtterance) {
        let text = utterance.speechString
        if let range = Range(characterRange, in: text) {
            let word = String(text[range])
            delegate?.ttsEngineDidSpeakRange(range: characterRange, word: word)
        }
    }
}
