import Foundation

/// Voice Gender representation
public enum VoiceGender: String, CaseIterable, Identifiable, Codable {
    case female = "female"
    case male = "male"
    
    public var id: String { rawValue }
    
    public var displayName: String {
        switch self {
        case .female: return "ಹೆಣ್ಣು ಧ್ವನಿ (Female)"
        case .male: return "ಗಂಡು ಧ್ವನಿ (Male)"
        }
    }
    
    public var shortName: String {
        switch self {
        case .female: return "ಹೆಣ್ಣು"
        case .male: return "ಗಂಡು"
        }
    }
    
    public var iconName: String {
        switch self {
        case .female: return "person.crop.circle.fill.badge.checkmark"
        case .male: return "person.crop.circle.fill"
        }
    }
}

/// Available TTS Engines
public enum TTSEngineType: String, CaseIterable, Identifiable, Codable {
    case neural = "neural"             // High-Definition Neural (Online HD Voices)
    case customCloned = "customCloned" // Voice Cloning from Uploaded Reference Audio
    case native = "native"             // Apple AVFoundation (Offline, On-Device)
    
    public var id: String { rawValue }
    
    public var title: String {
        switch self {
        case .neural: return "ಹೆಚ್.ಡಿ ನ್ಯೂರಲ್ (HD Neural Studio)"
        case .customCloned: return "ಕ್ಲೋನ್ ಮಾಡಿದ ಧ್ವನಿ (Custom Voice Clone)"
        case .native: return "ಆನ್‌ಲೈನ್‌ ಅಲ್ಲದ (On-Device Offline)"
        }
    }
    
    public var subtitle: String {
        switch self {
        case .neural: return "ಅತ್ಯುತ್ತಮ ಉಚ್ಚಾರಣೆ ಮತ್ತು ನೈಸರ್ಗಿಕ ಧ್ವನಿ"
        case .customCloned: return "ನೀವು ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ಆಡಿಯೊದ ಧ್ವನಿ ಹೋಲಿಕೆ"
        case .native: return "ವೇಗದ ಮತ್ತು ಇಂಟರ್ನೆಟ್ ಇಲ್ಲದೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ"
        }
    }
}

/// Pitch & Voice Presets for Kannada
public enum PitchPreset: String, CaseIterable, Identifiable, Codable {
    case natural = "natural"
    case energeticNarrator = "energetic_narrator"
    case deepMale = "deep_male"
    case softFemale = "soft_female"
    case child = "child"
    case newsAnchor = "news_anchor"
    
    public var id: String { rawValue }
    
    public var title: String {
        switch self {
        case .natural: return "ಸ್ವಾಭಾವಿಕ (Natural)"
        case .energeticNarrator: return "ಪಾಡ್‌ಕ್ಯಾಸ್ಟ್ ನಿರೂಪಕ (Podcast Narrator)"
        case .deepMale: return "ಗಂಭೀರ ಗಂಡು (Deep Male)"
        case .softFemale: return "ಮೃದು ಹೆಣ್ಣು (Soft Female)"
        case .child: return "ಮಕ್ಕಳ ಧ್ವನಿ (Child)"
        case .newsAnchor: return "ವಾರ್ತಾವಾಚಕ (News Anchor)"
        }
    }
    
    public var defaultGender: VoiceGender {
        switch self {
        case .natural: return .female
        case .energeticNarrator: return .male
        case .deepMale: return .male
        case .softFemale: return .female
        case .child: return .female
        case .newsAnchor: return .male
        }
    }
    
    /// Native pitch multiplier (0.5 to 2.0, default 1.0)
    public var nativePitch: Float {
        switch self {
        case .natural: return 1.0
        case .energeticNarrator: return 0.92
        case .deepMale: return 0.75
        case .softFemale: return 1.2
        case .child: return 1.55
        case .newsAnchor: return 0.88
        }
    }
    
    /// Neural pitch string (e.g., "+0Hz", "-15Hz", "+25Hz")
    public var neuralPitch: String {
        switch self {
        case .natural: return "+0Hz"
        case .energeticNarrator: return "-5Hz"
        case .deepMale: return "-18Hz"
        case .softFemale: return "+12Hz"
        case .child: return "+35Hz"
        case .newsAnchor: return "-8Hz"
        }
    }
    
    public var speechRate: Float {
        switch self {
        case .natural: return 0.50
        case .energeticNarrator: return 0.56  // ~1.12x fast-paced presenter speed
        case .deepMale: return 0.48
        case .softFemale: return 0.50
        case .child: return 0.55
        case .newsAnchor: return 0.52
        }
    }
}

/// Playback States
public enum PlaybackState: Equatable {
    case idle
    case loading
    case playing
    case paused
    case stopped
    case error(String)
}

/// Highlighted word range during real-time speech synthesis
public struct SpokenWordRange: Equatable {
    public let range: NSRange
    public let word: String
    
    public init(range: NSRange, word: String) {
        self.range = range
        self.word = word
    }
}
