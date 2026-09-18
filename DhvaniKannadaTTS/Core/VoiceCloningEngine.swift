import Foundation
import AVFoundation

/// Engine that performs Kannada speech synthesis matching an uploaded reference voice sample
public final class VoiceCloningEngine: NSObject, TTSEngineProtocol, AVAudioPlayerDelegate {
    
    public weak var delegate: TTSEngineDelegate?
    public let engineType: TTSEngineType = .customCloned
    
    private var audioPlayer: AVAudioPlayer?
    private var neuralFallback = NeuralTTSEngine()
    private var currentTask: URLSessionDataTask?
    
    public var customVoiceServerURL: String = "http://localhost:8000/api/clone_voice"
    public var activeReferenceAudioURL: URL?
    
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
        
        guard let refAudioURL = activeReferenceAudioURL, FileManager.default.fileExists(atPath: refAudioURL.path) else {
            print("No reference audio uploaded! Falling back to HD Neural...")
            neuralFallback.delegate = self.delegate
            neuralFallback.speak(text: text, gender: gender, pitch: pitch, rate: rate, volume: volume, voiceId: voiceId)
            return
        }
        
        delegate?.ttsEngineDidStartSpeaking()
        
        cloneVoiceSynthesis(
            text: normalizedText,
            referenceAudioURL: refAudioURL,
            pitch: pitch,
            rate: rate,
            volume: volume
        ) { [weak self] result in
            guard let self = self else { return }
            DispatchQueue.main.async {
                switch result {
                case .success(let audioData):
                    self.playAudioData(audioData)
                case .failure(let error):
                    print("Voice cloning endpoint unavailable (\(error.localizedDescription)). Using HD Neural fallback with matching acoustic pitch...")
                    self.neuralFallback.delegate = self.delegate
                    self.neuralFallback.speak(text: text, gender: gender, pitch: pitch, rate: rate, volume: volume, voiceId: voiceId)
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
        neuralFallback.stop()
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
        guard let refAudioURL = activeReferenceAudioURL, FileManager.default.fileExists(atPath: refAudioURL.path) else {
            neuralFallback.synthesizeToFile(text: text, gender: gender, pitch: pitch, rate: rate, volume: volume, voiceId: voiceId, completion: completion)
            return
        }
        
        cloneVoiceSynthesis(
            text: normalizedText,
            referenceAudioURL: refAudioURL,
            pitch: pitch,
            rate: rate,
            volume: volume
        ) { result in
            switch result {
            case .success(let data):
                let tempDir = FileManager.default.temporaryDirectory
                let fileURL = tempDir.appendingPathComponent("cloned_kannada_\(UUID().uuidString).wav")
                do {
                    try data.write(to: fileURL)
                    DispatchQueue.main.async {
                        completion(.success(fileURL))
                    }
                } catch {
                    DispatchQueue.main.async {
                        completion(.failure(error))
                    }
                }
            case .failure(let error):
                print("Clone endpoint failed, exporting via Neural engine...")
                self.neuralFallback.synthesizeToFile(text: text, gender: gender, pitch: pitch, rate: rate, volume: volume, voiceId: voiceId, completion: completion)
            }
        }
    }
    
    // MARK: - Multipart Upload to Voice Cloning Synthesizer
    private func cloneVoiceSynthesis(
        text: String,
        referenceAudioURL: URL,
        pitch: Float,
        rate: Float,
        volume: Float,
        completion: @escaping (Result<Data, Error>) -> Void
    ) {
        guard let serverURL = URL(string: customVoiceServerURL) else {
            completion(.failure(NSError(domain: "DhvaniTTS", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid Voice Clone Server URL"])))
            return
        }
        
        guard let audioData = try? Data(contentsOf: referenceAudioURL) else {
            completion(.failure(NSError(domain: "DhvaniTTS", code: -2, userInfo: [NSLocalizedDescriptionKey: "Unable to read reference audio data"])))
            return
        }
        
        let boundary = "Boundary-\(UUID().uuidString)"
        var request = URLRequest(url: serverURL)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30
        
        var body = Data()
        
        // Text parameter
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"text\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(text)\r\n".data(using: .utf8)!)
        
        // Pitch parameter
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"pitch\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(pitch)\r\n".data(using: .utf8)!)
        
        // Rate parameter
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"rate\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(rate)\r\n".data(using: .utf8)!)
        
        // Language parameter
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"language\"\r\n\r\n".data(using: .utf8)!)
        body.append("kn\r\n".data(using: .utf8)!)
        
        // Reference Audio File
        let fileName = referenceAudioURL.lastPathComponent
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"reference_audio\"; filename=\"\(fileName)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/wav\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n".data(using: .utf8)!)
        
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = body
        
        currentTask = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            guard let data = data, !data.isEmpty else {
                completion(.failure(NSError(domain: "DhvaniTTS", code: -3, userInfo: [NSLocalizedDescriptionKey: "Empty cloned audio received"])))
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
