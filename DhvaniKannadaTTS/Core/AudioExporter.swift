import Foundation
import SwiftUI
import AVFoundation

/// Helper for exporting and sharing synthesized Kannada audio clips
public final class AudioExporter {
    
    public static let shared = AudioExporter()
    
    private init() {}
    
    /// Generates and exports the audio file for the specified parameters
    public func exportAudio(
        text: String,
        engineType: TTSEngineType,
        gender: VoiceGender,
        pitch: Float,
        rate: Float,
        volume: Float,
        voiceId: String?,
        completion: @escaping (Result<URL, Error>) -> Void
    ) {
        let engine: TTSEngineProtocol = (engineType == .neural) ? NeuralTTSEngine() : NativeTTSEngine()
        
        engine.synthesizeToFile(
            text: text,
            gender: gender,
            pitch: pitch,
            rate: rate,
            volume: volume,
            voiceId: voiceId
        ) { result in
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
}
