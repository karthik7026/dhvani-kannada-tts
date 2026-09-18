import Foundation
import AVFoundation

/// Profile definition for a Kannada voice
public struct VoiceProfile: Identifiable, Hashable {
    public let id: String
    public let name: String
    public let kannadaName: String
    public let gender: VoiceGender
    public let locale: String
    public let engineType: TTSEngineType
    public let description: String
    public let sampleSentence: String
    
    public init(
        id: String,
        name: String,
        kannadaName: String,
        gender: VoiceGender,
        locale: String = "kn-IN",
        engineType: TTSEngineType,
        description: String,
        sampleSentence: String = "ನಮಸ್ಕಾರ! ಕನ್ನಡ ಧ್ವನಿ ಸಂಶ್ಲೇಷಣೆಗೆ ಸುಸ್ವಾಗತ."
    ) {
        self.id = id
        self.name = name
        self.kannadaName = kannadaName
        self.gender = gender
        self.locale = locale
        self.engineType = engineType
        self.description = description
        self.sampleSentence = sampleSentence
    }
}

public struct VoiceCatalog {
    /// Default available voices for Dhvani Kannada TTS
    public static let defaultVoices: [VoiceProfile] = [
        VoiceProfile(
            id: "kn-IN-SapnaNeural",
            name: "Sapna (ಸ್ಪಪ್ನಾ)",
            kannadaName: "ಸ್ಪಪ್ನಾ",
            gender: .female,
            locale: "kn-IN",
            engineType: .neural,
            description: "ಸ್ಪಷ್ಟ ಮತ್ತು ಮಧುರವಾದ ಹೆಣ್ಣು ಧ್ವನಿ (HD Neural Female Voice)",
            sampleSentence: "ಕನ್ನಡ ನಾಡು ನುಡಿ ಅತ್ಯಂತ ಸುಂದರ ಮತ್ತು ಸಮೃದ್ಧವಾಗಿದೆ."
        ),
        VoiceProfile(
            id: "kn-IN-GaganNeural",
            name: "Gagan (ಗಗನ್)",
            kannadaName: "ಗಗನ್",
            gender: .male,
            locale: "kn-IN",
            engineType: .neural,
            description: "ಗಂಭೀರ ಮತ್ತು ಸ್ಪಷ್ಟವಾದ ಗಂಡು ಧ್ವನಿ (HD Neural Male Voice)",
            sampleSentence: "ಜ್ಞಾನಪೀಠ ಪ್ರಶಸ್ತಿ ಪುರಸ್ಕೃತ ಕನ್ನಡ ಸಾಹಿತ್ಯ ವಿಶ್ವಮಾನ್ಯವಾದುದು."
        ),
        VoiceProfile(
            id: "kn-IN-system-female",
            name: "Apple Kannada (Female)",
            kannadaName: "ಆ್ಯಪಲ್ ಕನ್ನಡ ಹೆಣ್ಣು",
            gender: .female,
            locale: "kn-IN",
            engineType: .native,
            description: "ಸಾಧನದಲ್ಲಿರುವ ಸ್ಥಳೀಯ ಹೆಣ್ಣು ಧ್ವನಿ (Offline On-Device)",
            sampleSentence: "ಇದು ಯಾವುದೇ ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕವಿಲ್ಲದೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ."
        ),
        VoiceProfile(
            id: "kn-IN-system-male",
            name: "Apple Kannada (Male)",
            kannadaName: "ಆ್ಯಪಲ್ ಕನ್ನಡ ಗಂಡು",
            gender: .male,
            locale: "kn-IN",
            engineType: .native,
            description: "ಸಾಧನದಲ್ಲಿರುವ ಸ್ಥಳೀಯ ಗಂಡು ಧ್ವನಿ (Offline On-Device)",
            sampleSentence: "ಕನ್ನಡ ಭಾಷೆಗೆ ೨೦೦೦ ವರ್ಷಗಳಿಗಿಂತ ಹೆಚ್ಚಿನ ಭವ್ಯ ಇತಿಹಾಸವಿದೆ."
        )
    ]
}
