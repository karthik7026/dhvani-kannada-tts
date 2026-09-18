import Foundation

/// Category of Kannada sample texts
public enum PresetCategory: String, CaseIterable, Identifiable {
    case conversation = "ದೈನಂದಿನ ಸಂಭಾಷಣೆ"
    case news = "ಸುದ್ದಿ & ವಾರ್ತೆಗಳು"
    case literature = "ಸಾಹಿತ್ಯ & ಕವನಗಳು"
    case proverbs = "ಜನಪ್ರಿಯ ಗಾದೆಗಳು"
    case tongueTwisters = "ನಾಲಗೆ ತಿರುವು & ಒತ್ತಕ್ಷರಗಳು"
    case numberTests = "ಸಂಖ್ಯೆ & ರೂಪಾಯಿ ಪರೀಕ್ಷೆ"
    
    public var id: String { rawValue }
    
    public var iconName: String {
        switch self {
        case .conversation: return "bubble.left.and.bubble.right.fill"
        case .news: return "newspaper.fill"
        case .literature: return "book.fill"
        case .proverbs: return "quote.bubble.fill"
        case .tongueTwisters: return "waveform.badge.magnifyingglass"
        case .numberTests: return "numbers.rectangle.fill"
        }
    }
}

/// Model for a preset Kannada sample text
public struct KannadaSampleText: Identifiable {
    public let id = UUID()
    public let title: String
    public let category: PresetCategory
    public let text: String
    public let suggestedGender: VoiceGender
    public let suggestedPitch: PitchPreset
    
    public init(
        title: String,
        category: PresetCategory,
        text: String,
        suggestedGender: VoiceGender = .female,
        suggestedPitch: PitchPreset = .natural
    ) {
        self.title = title
        self.category = category
        self.text = text
        self.suggestedGender = suggestedGender
        self.suggestedPitch = suggestedPitch
    }
}

public struct PresetLibrary {
    public static let samples: [KannadaSampleText] = [
        // Daily Conversation
        KannadaSampleText(
            title: "ಪಾಡ್‌ಕ್ಯಾಸ್ಟ್ ವಿವರಣೆ (Geopolitics)",
            category: .news,
            text: "ಎಸ್‌ಸಿಒ ಸಮ್ಮೇಳನದಲ್ಲಿ ಭಾರತದ ಪಾತ್ರ ಅತ್ಯಂತ ಪ್ರಮುಖವಾಗಿದೆ. ಜಾಗತಿಕ ದಕ್ಷಿಣದ ದೇಶಗಳಿಗೆ ಭಾರತ ನೀಡಿದ ೧೦ ಅಂಶಗಳ ಕಾರ್ಯಸೂಚಿ ಇಡೀ ವಿಶ್ವದ ಗಮನ ಸೆಳೆದಿದೆ. ದೇಶದ ರಾಷ್ಟ್ರೀಯ ಭದ್ರತೆ ಮತ್ತು ಆರ್ಥಿಕ ಶಕ್ತಿ ಎರಡೂ ಅಷ್ಟೇ ಮುಖ್ಯ.",
            suggestedGender: .male,
            suggestedPitch: .energeticNarrator
        ),
        KannadaSampleText(
            title: "ಶುಭೋದಯ ಮತ್ತು ಸ್ವಾಗತ",
            category: .conversation,
            text: "ಶುಭೋದಯ! ಧ್ವನಿ ಕನ್ನಡ ಅಪ್ಲಿಕೇಶನ್‌ಗೆ ನಿಮಗೆ ಹೃತ್ಪೂರ್ವಕ ಸ್ವಾಗತ. ಇಂದು ನಿಮ್ಮ ದಿನ ಮಂಗಳಕರವಾಗಿರಲಿ.",
            suggestedGender: .female,
            suggestedPitch: .natural
        ),
        KannadaSampleText(
            title: "ಸ್ನೇಹಿತರ ಮಾತುಕತೆ",
            category: .conversation,
            text: "ನಮಸ್ಕಾರ ಸ್ನೇಹಿತರೆ, ನೀವು ಹೇಗಿದ್ದೀರಿ? ಬಹಳ ದಿನಗಳ ನಂತರ ನಿಮ್ಮನ್ನು ಭೇಟಿಯಾಗುತ್ತಿರುವುದು ತುಂಬಾ ಸಂತೋಷ ತಂದಿದೆ.",
            suggestedGender: .male,
            suggestedPitch: .natural
        ),
        
        // News & Announcements
        KannadaSampleText(
            title: "ಹವಾಮಾನ ವರದಿ",
            category: .news,
            text: "ಕರ್ನಾಟಕ ರಾಜ್ಯದ ಹವಾಮಾನ ಇಲಾಖೆಯ ಪ್ರಕಾರ, ಕರಾವಳಿ ಮತ್ತು ಮಲೆನಾಡು ಭಾಗಗಳಲ್ಲಿ ಮುಂದಿನ ೨೪ ಗಂಟೆಗಳಲ್ಲಿ ಸಾಧಾರಣ ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆಯಿದೆ. ತಾಪಮಾನ ೨೮ ಡಿಗ್ರಿ ಸೆಲ್ಸಿಯಸ್ ಇರಲಿದೆ.",
            suggestedGender: .male,
            suggestedPitch: .newsAnchor
        ),
        KannadaSampleText(
            title: "ರೈಲ್ವೆ ಪ್ರಕಟಣೆ",
            category: .news,
            text: "ಪ್ರಯಾಣಿಕರ ಗಮನಕ್ಕೆ, ಬೆಂಗಳೂರಿನಿಂದ ಮೈಸೂರಿಗೆ ತೆರಳುವ ಚಾಮುಂಡಿ ಎಕ್ಸ್‌ಪ್ರೆಸ್ ರೈಲು ನಿಲ್ದಾಣದ ಒಂದನೇ ಪ್ಲಾಟ್‌ಫಾರ್ಮ್‌ಗೆ ಸರಿಯಾದ ಸಮಯಕ್ಕೆ ಆಗಮಿಸುತ್ತಿದೆ.",
            suggestedGender: .female,
            suggestedPitch: .natural
        ),
        
        // Literature & Poetry
        KannadaSampleText(
            title: "ಕನ್ನಡ ನಾಡು ನುಡಿ",
            category: .literature,
            text: "ಹೆಸರಾಯಿತು ಕರ್ನಾಟಕ, ಉಸಿರಾಗಲಿ ಕನ್ನಡ. ಸಿರಿಗನ್ನಡಂ ಗೆಲ್ಗೆ, ಸಿರಿಗನ್ನಡಂ ಬಾಳ್ಗೆ! ಎಲ್ಲಾದರು ಇರು ಎಂತಾದರು ಇರು ಎಂದೆಂದಿಗೂ ನೀ ಕನ್ನಡವಾಗಿರು.",
            suggestedGender: .female,
            suggestedPitch: .softFemale
        ),
        KannadaSampleText(
            title: "ಕುವೆಂಪು ಅವರ ವಾಣಿ",
            category: .literature,
            text: "ಸರ್ವರಿಗೂ ಸಮಪಾಲು, ಸರ್ವರಿಗೂ ಸಮಬಾಳು. ಮನುಜ ಮತ, ವಿಶ್ವಪಥ, ಸರ್ವೋದಯ, ಸಮನ್ವಯ, ಪೂರ್ಣದೃಷ್ಟಿ ನಮ್ಮ ಧ್ಯೇಯವಾಗಲಿ.",
            suggestedGender: .male,
            suggestedPitch: .deepMale
        ),
        
        // Proverbs
        KannadaSampleText(
            title: "ಜನಪ್ರಿಯ ಗಾದೆ ಮಾತುಗಳು",
            category: .proverbs,
            text: "ಹಾಸಿಗೆ ಇದ್ದಷ್ಟೇ ಕಾಲು ಚಾಚು. ಕೈ ಕೆಸರಾದರೆ ಬಾಯಿ ಮೊಸರು. ವಿದ್ಯೆಯೇ ಮನುಷ್ಯನ ನಿಜವಾದ ಆಭರಣ.",
            suggestedGender: .female,
            suggestedPitch: .natural
        ),
        KannadaSampleText(
            title: "ಜ್ಞಾನದ ಮಾತುಗಳು",
            category: .proverbs,
            text: "ಮಾತು ಬಲ್ಲವನಿಗೆ ಜಗಳವಿಲ್ಲ, ಊಟ ಬಲ್ಲವನಿಗೆ ರೋಗವಿಲ್ಲ. ಉಪ್ಪಿಗಿಂತ ರುಚಿಯಿಲ್ಲ, ತಾಯಿಗಿಂತ ಬಂಧುವಿಲ್ಲ.",
            suggestedGender: .male,
            suggestedPitch: .deepMale
        ),
        
        // Tongue Twisters & Ottakshara Tests
        KannadaSampleText(
            title: "ಒತ್ತಕ್ಷರಗಳ ಪರೀಕ್ಷೆ",
            category: .tongueTwisters,
            text: "ಕಾಗೆ ಕಾಗದ ಕಚ್ಚಿತು, ಕಾಗದ ಕರಕರ ಹರಿಯಿತು. ಕೆಂಪು ಕುಂಕುಮ, ಕಪ್ಪು ಕುಂಕುಮ, ಚುಕ್ಕಿ ಕುಂಕುಮ.",
            suggestedGender: .female,
            suggestedPitch: .child
        ),
        KannadaSampleText(
            title: "ಸಂಕೀರ್ಣ ಶಬ್ದಗಳು",
            category: .tongueTwisters,
            text: "ರಾಷ್ಟ್ರೀಯ ಪರೀಕ್ಷಾ ಮಂಡಳಿಯು ಸಾಂಸ್ಕೃತಿಕ ಕಾರ್ಯಕ್ರಮದ ಸ್ಪರ್ಧೆಗಳನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಆಯೋಜಿಸಿದೆ.",
            suggestedGender: .female,
            suggestedPitch: .natural
        ),
        
        // Numbers & Currency
        KannadaSampleText(
            title: "ಸಂಖ್ಯೆ ಮತ್ತು ಕರೆನ್ಸಿ ಉಚ್ಚಾರಣೆ",
            category: .numberTests,
            text: "ನಮ್ಮ ಪುಸ್ತಕ ಮಳಿಗೆಯಲ್ಲಿ ಒಟ್ಟು ೧೨೫೦ ಪುಸ್ತಕಗಳಿವೆ. ಇದರ ಬೆಲೆ ₹೪೫೦ ಮಾತ್ರ. ನಿಮ್ಮ ಶೇಕಡಾ ೨೦% ರಿಯಾಯಿತಿ ಸಿಗಲಿದೆ.",
            suggestedGender: .male,
            suggestedPitch: .natural
        ),
        KannadaSampleText(
            title: "ದಿನಾಂಕ ಮತ್ತು ವರ್ಷ",
            category: .numberTests,
            text: "ಭಾರತ ದೇಶವು 1947 ನೇ ಇಸವಿ ಆಗಸ್ಟ್ 15 ರಂದು ಸ್ವಾತಂತ್ರ್ಯ ಪಡೆಯಿತು. ಕರ್ನಾಟಕ ರಾಜ್ಯೋತ್ಸವವನ್ನು ಪ್ರತಿ ವರ್ಷ ನವೆಂಬರ್ 1 ರಂದು ಆಚರಿಸಲಾಗುತ್ತದೆ.",
            suggestedGender: .female,
            suggestedPitch: .natural
        )
    ]
}
