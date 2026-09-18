import Foundation

/// Custom voice profile created from an uploaded or recorded reference audio
public struct CustomVoiceProfile: Identifiable, Codable, Hashable {
    public let id: String
    public var name: String
    public var kannadaName: String
    public var referenceAudioFileName: String
    public var durationSeconds: Double
    public var dateCreated: Date
    public var description: String
    
    public init(
        id: String = UUID().uuidString,
        name: String,
        kannadaName: String,
        referenceAudioFileName: String,
        durationSeconds: Double = 0.0,
        dateCreated: Date = Date(),
        description: String = "ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ಆಡಿಯೊ ಮಾದರಿಯ ಧ್ವನಿ (Custom Cloned Voice)"
    ) {
        self.id = id
        self.name = name
        self.kannadaName = kannadaName
        self.referenceAudioFileName = referenceAudioFileName
        self.durationSeconds = durationSeconds
        self.dateCreated = dateCreated
        self.description = description
    }
    
    /// Returns the local file URL for the reference audio stored in Documents directory
    public var localAudioURL: URL? {
        guard let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else {
            return nil
        }
        return docs.appendingPathComponent("CustomVoices/\(referenceAudioFileName)")
    }
}
