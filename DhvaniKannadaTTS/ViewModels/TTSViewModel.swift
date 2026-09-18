import Foundation
import SwiftUI
import Combine
import AVFoundation

@MainActor
public final class TTSViewModel: ObservableObject, TTSEngineDelegate {
    
    // MARK: - Published Properties
    @Published public var inputText: String = "ನಮಸ್ಕಾರ! ಧ್ವನಿ ಕನ್ನಡ ಅಪ್ಲಿಕೇಶನ್‌ಗೆ ಸುಸ್ವಾಗತ. ನೀವು ಟೈಪ್ ಮಾಡಿದ ಯಾವುದೇ ಕನ್ನಡ ಪಠ್ಯವನ್ನು ಇಲ್ಲಿ ನೈಸರ್ಗಿಕ ಧ್ವನಿಯಲ್ಲಿ ಕೇಳಬಹುದು."
    @Published public var normalizedPreview: String = ""
    
    @Published public var selectedGender: VoiceGender = .female
    @Published public var selectedEngine: TTSEngineType = .neural
    @Published public var selectedVoice: VoiceProfile
    @Published public var selectedPreset: PitchPreset = .natural
    
    // Custom Voice Cloning
    @Published public var customVoices: [CustomVoiceProfile] = []
    @Published public var activeCustomVoice: CustomVoiceProfile?
    @Published public var showCustomVoiceManager: Bool = false
    
    // Controls
    @Published public var pitch: Float = 1.0          // 0.5x to 2.0x (1.0 = standard)
    @Published public var speechRate: Float = 1.0     // 0.5x to 2.0x (1.0 = standard)
    @Published public var volume: Float = 1.0         // 0.0 to 1.0
    
    // Transliteration Toggle
    @Published public var isTransliterationEnabled: Bool = false
    @Published public var transliteratedBuffer: String = ""
    
    // Playback States
    @Published public var playbackState: PlaybackState = .idle
    @Published public var currentWord: String = ""
    @Published public var currentWordRange: NSRange?
    
    // Sheets & Dialogs
    @Published public var showPresetsSheet: Bool = false
    @Published public var showShareSheet: Bool = false
    @Published public var exportedAudioURL: URL?
    @Published public var isExporting: Bool = false
    @Published public var toastMessage: String?
    
    // MARK: - Private Engine Instances
    private var nativeEngine = NativeTTSEngine()
    private var neuralEngine = NeuralTTSEngine()
    private var voiceCloningEngine = VoiceCloningEngine()
    
    private var cancellables = Set<AnyCancellable>()
    private let customVoicesKey = "SavedCustomVoicesProfiles_v1"
    
    public init() {
        let initialVoice = VoiceCatalog.defaultVoices.first(where: { $0.id == "kn-IN-SapnaNeural" }) ?? VoiceCatalog.defaultVoices[0]
        self.selectedVoice = initialVoice
        
        self.nativeEngine.delegate = self
        self.neuralEngine.delegate = self
        self.voiceCloningEngine.delegate = self
        
        loadSavedCustomVoices()
        updateNormalizedPreview()
        
        // Observe text changes for normalization preview
        $inputText
            .debounce(for: .milliseconds(300), scheduler: RunLoop.main)
            .sink { [weak self] _ in
                self?.updateNormalizedPreview()
            }
            .store(in: &cancellables)
    }
    
    // MARK: - Engine Selection
    private var activeEngine: TTSEngineProtocol {
        switch selectedEngine {
        case .native: return nativeEngine
        case .neural: return neuralEngine
        case .customCloned:
            voiceCloningEngine.activeReferenceAudioURL = activeCustomVoice?.localAudioURL
            return voiceCloningEngine
        }
    }
    
    // MARK: - Actions
    public func togglePlayback() {
        switch playbackState {
        case .playing:
            pause()
        case .paused:
            resume()
        case .idle, .stopped, .error:
            speak()
        case .loading:
            stop()
        }
    }
    
    public func speak() {
        guard !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            showToast("ದಯವಿಟ್ಟು ಪಠ್ಯವನ್ನು ನಮೂದಿಸಿ (Please enter text)")
            return
        }
        
        if selectedEngine == .customCloned && activeCustomVoice == nil {
            showToast("ದಯವಿಟ್ಟು ಆಡಿಯೊ ಮಾದರಿಯನ್ನು ಆಯ್ಕೆಮಾಡಿ")
            showCustomVoiceManager = true
            return
        }
        
        playbackState = .loading
        currentWord = ""
        currentWordRange = nil
        
        activeEngine.speak(
            text: inputText,
            gender: selectedGender,
            pitch: pitch,
            rate: speechRate,
            volume: volume,
            voiceId: selectedVoice.id
        )
    }
    
    public func pause() {
        activeEngine.pause()
        playbackState = .paused
    }
    
    public func resume() {
        activeEngine.resume()
        playbackState = .playing
    }
    
    public func stop() {
        activeEngine.stop()
        playbackState = .stopped
        currentWord = ""
        currentWordRange = nil
    }
    
    public func selectGender(_ gender: VoiceGender) {
        self.selectedGender = gender
        if let match = VoiceCatalog.defaultVoices.first(where: { $0.gender == gender && $0.engineType == selectedEngine }) {
            self.selectedVoice = match
        }
    }
    
    public func selectEngine(_ engine: TTSEngineType) {
        self.selectedEngine = engine
        if engine == .customCloned {
            if activeCustomVoice == nil && !customVoices.isEmpty {
                activeCustomVoice = customVoices.first
            }
            if activeCustomVoice == nil {
                showCustomVoiceManager = true
            }
        } else {
            if let match = VoiceCatalog.defaultVoices.first(where: { $0.gender == selectedGender && $0.engineType == engine }) {
                self.selectedVoice = match
            }
        }
    }
    
    // MARK: - Custom Voice Management
    public func addCustomVoice(_ profile: CustomVoiceProfile) {
        customVoices.append(profile)
        saveCustomVoices()
        activateCustomVoice(profile)
    }
    
    public func activateCustomVoice(_ profile: CustomVoiceProfile) {
        self.activeCustomVoice = profile
        self.selectedEngine = .customCloned
        self.voiceCloningEngine.activeReferenceAudioURL = profile.localAudioURL
        showToast("\"\(profile.name)\" ಸಕ್ರಿಯಗೊಳಿಸಲಾಗಿದೆ")
    }
    
    public func deleteCustomVoice(_ profile: CustomVoiceProfile) {
        if let url = profile.localAudioURL {
            try? FileManager.default.removeItem(at: url)
        }
        customVoices.removeAll(where: { $0.id == profile.id })
        if activeCustomVoice?.id == profile.id {
            activeCustomVoice = customVoices.first
            if activeCustomVoice == nil {
                selectedEngine = .neural
            }
        }
        saveCustomVoices()
    }
    
    private func saveCustomVoices() {
        if let data = try? JSONEncoder().encode(customVoices) {
            UserDefaults.standard.set(data, forKey: customVoicesKey)
        }
    }
    
    private func loadSavedCustomVoices() {
        if let data = UserDefaults.standard.data(forKey: customVoicesKey),
           let list = try? JSONDecoder().decode([CustomVoiceProfile].self, from: data) {
            self.customVoices = list
            self.activeCustomVoice = list.first
        }
    }
    
    public func applyPreset(_ preset: PitchPreset) {
        self.selectedPreset = preset
        self.selectedGender = preset.defaultGender
        self.pitch = preset.nativePitch
        self.speechRate = preset.speechRate
        
        if selectedEngine != .customCloned {
            if let match = VoiceCatalog.defaultVoices.first(where: { $0.gender == selectedGender && $0.engineType == selectedEngine }) {
                self.selectedVoice = match
            }
        }
        
        showToast("\(preset.title) ಪ್ರೊಫೈಲ್ ಆಯ್ಕೆಯಾಗಿದೆ")
    }
    
    public func applySampleText(_ sample: KannadaSampleText) {
        self.inputText = sample.text
        self.selectedGender = sample.suggestedGender
        applyPreset(sample.suggestedPitch)
        showPresetsSheet = false
        showToast("\"\(sample.title)\" ಲೋಡ್ ಆಗಿದೆ")
    }
    
    public func handleTypingText(_ newText: String) {
        if isTransliterationEnabled {
            self.inputText = KannadaTransliterator.transliterate(text: newText)
        } else {
            self.inputText = newText
        }
    }
    
    public func resetToDefaults() {
        self.pitch = 1.0
        self.speechRate = 1.0
        self.volume = 1.0
        self.selectedPreset = .natural
        showToast("ಸೆಟ್ಟಿಂಗ್‌ಗಳನ್ನು ಮರುಹೊಂದಿಸಲಾಗಿದೆ (Reset to defaults)")
    }
    
    public func updateNormalizedPreview() {
        self.normalizedPreview = KannadaNormalizer.normalize(text: inputText)
    }
    
    public func exportAudio() {
        guard !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            showToast("ರಫ್ತು ಮಾಡಲು ಪಠ್ಯ ಖಾಲಿಯಾಗಿದೆ")
            return
        }
        
        isExporting = true
        showToast("ಆಡಿಯೊ ಸಿದ್ಧವಾಗುತ್ತಿದೆ...")
        
        AudioExporter.shared.exportAudio(
            text: inputText,
            engineType: selectedEngine,
            gender: selectedGender,
            pitch: pitch,
            rate: speechRate,
            volume: volume,
            voiceId: selectedVoice.id
        ) { [weak self] result in
            guard let self = self else { return }
            self.isExporting = false
            switch result {
            case .success(let url):
                self.exportedAudioURL = url
                self.showShareSheet = true
            case .failure(let error):
                self.showToast("ಆಡಿಯೊ ರಫ್ತು ವಿಫಲವಾಗಿದೆ: \(error.localizedDescription)")
            }
        }
    }
    
    public func showToast(_ msg: String) {
        self.toastMessage = msg
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) { [weak self] in
            if self?.toastMessage == msg {
                self?.toastMessage = nil
            }
        }
    }
    
    // MARK: - TTSEngineDelegate
    public func ttsEngineDidStartSpeaking() {
        self.playbackState = .playing
    }
    
    public func ttsEngineDidFinishSpeaking() {
        self.playbackState = .idle
        self.currentWord = ""
        self.currentWordRange = nil
    }
    
    public func ttsEngineDidPauseSpeaking() {
        self.playbackState = .paused
    }
    
    public func ttsEngineDidContinueSpeaking() {
        self.playbackState = .playing
    }
    
    public func ttsEngineDidCancelSpeaking() {
        self.playbackState = .stopped
        self.currentWord = ""
        self.currentWordRange = nil
    }
    
    public func ttsEngineDidSpeakRange(range: NSRange, word: String) {
        self.currentWordRange = range
        self.currentWord = word
    }
    
    public func ttsEngineDidFail(error: Error) {
        self.playbackState = .error(error.localizedDescription)
        self.showToast("ದೋಷ: \(error.localizedDescription)")
    }
}
