import Foundation
import Combine

public protocol TTSEngineDelegate: AnyObject {
    func ttsEngineDidStartSpeaking()
    func ttsEngineDidFinishSpeaking()
    func ttsEngineDidPauseSpeaking()
    func ttsEngineDidContinueSpeaking()
    func ttsEngineDidCancelSpeaking()
    func ttsEngineDidSpeakRange(range: NSRange, word: String)
    func ttsEngineDidFail(error: Error)
}

public protocol TTSEngineProtocol: AnyObject {
    var delegate: TTSEngineDelegate? { get set }
    var engineType: TTSEngineType { get }
    var isSpeaking: Bool { get }
    var isPaused: Bool { get }
    
    func speak(
        text: String,
        gender: VoiceGender,
        pitch: Float,
        rate: Float,
        volume: Float,
        voiceId: String?
    )
    
    func pause()
    func resume()
    func stop()
    
    func synthesizeToFile(
        text: String,
        gender: VoiceGender,
        pitch: Float,
        rate: Float,
        volume: Float,
        voiceId: String?,
        completion: @escaping (Result<URL, Error>) -> Void
    )
}
