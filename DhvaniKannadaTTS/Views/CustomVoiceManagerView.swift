import SwiftUI
import UniformTypeIdentifiers
import AVFoundation

/// View for uploading reference audio files or recording voice samples to clone
public struct CustomVoiceManagerView: View {
    @ObservedObject var viewModel: TTSViewModel
    @Environment(\.dismiss) private var dismiss
    
    @StateObject private var recorder = AudioRecorder()
    @State private var voiceNameInput: String = ""
    @State private var isFileImporterPresented: Bool = false
    @State private var previewPlayer: AVAudioPlayer?
    @State private var isPreviewPlaying: Bool = false
    @State private var stagedAudioURL: URL?
    
    public var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Header Description Card
                    headerCard
                    
                    // Upload / Record Options Card
                    actionOptionsCard
                    
                    // Staged Audio Preview & Save Section
                    if let audioURL = stagedAudioURL {
                        stagedAudioCard(audioURL: audioURL)
                    }
                    
                    // Saved Cloned Voices List
                    savedVoicesSection
                }
                .padding(16)
            }
            .background(Color(UIColor.systemGroupedBackground))
            .navigationTitle("ಕಸ್ಟಮ್ ಧ್ವನಿ ಕ್ಲೋನಿಂಗ್")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("ಮುಕ್ತಾಯ") {
                        dismiss()
                    }
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.orange)
                }
            }
            .fileImporter(
                isPresented: $isFileImporterPresented,
                allowedContentTypes: [.audio, .wav, .mp3, .mpeg4Audio],
                allowsMultipleSelection: false
            ) { result in
                handleImportedFile(result: result)
            }
        }
    }
    
    // MARK: - Header Info Card
    private var headerCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "waveform.badge.mic")
                    .font(.system(size: 22))
                    .foregroundColor(.orange)
                Text("ಧ್ವನಿ ಮಾದರಿ ಅಪ್‌ಲೋಡ್ (Voice Clone Studio)")
                    .font(.system(size: 15, weight: .bold))
            }
            
            Text("ನೀವು ಯಾವುದೇ ಆಡಿಯೊ ಫೈಲ್ (WAV, MP3) ಅಪ್‌ಲೋಡ್ ಮಾಡಿದರೆ ಅಥವಾ ನಿಮ್ಮ ಧ್ವನಿಯನ್ನು ರೆಕಾರ್ಡ್ ಮಾಡಿದರೆ, ಸಿಸ್ಟಮ್ ಆ ಧ್ವನಿಯ ಸ್ವರೂಪ, ಪಿಚ್ ಮತ್ತು ಶೈಲಿಯಲ್ಲಿ ಕನ್ನಡ ಪಠ್ಯವನ್ನು ಓದುತ್ತದೆ.")
                .font(.system(size: 12))
                .foregroundColor(.secondary)
                .lineSpacing(3)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(UIColor.secondarySystemGroupedBackground))
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.04), radius: 6, x: 0, y: 2)
    }
    
    // MARK: - Action Options (Upload vs Record)
    private var actionOptionsCard: some View {
        VStack(spacing: 14) {
            Text("ಆಡಿಯೊ ಮಾದರಿ ಸೇರಿಸಿ (Add Audio Sample)")
                .font(.system(size: 14, weight: .bold))
                .frame(maxWidth: .infinity, alignment: .leading)
            
            HStack(spacing: 12) {
                // Upload File Button
                Button(action: {
                    isFileImporterPresented = true
                }) {
                    VStack(spacing: 8) {
                        Image(systemName: "arrow.up.doc.fill")
                            .font(.system(size: 26))
                            .foregroundColor(.orange)
                        Text("ಫೈಲ್ ಅಪ್‌ಲೋಡ್")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundColor(.primary)
                        Text("MP3, WAV, M4A")
                            .font(.system(size: 10))
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .background(Color(UIColor.secondarySystemGroupedBackground))
                    .cornerRadius(14)
                    .overlay(
                        RoundedRectangle(cornerRadius: 14)
                            .stroke(Color.orange.opacity(0.3), lineWidth: 1.5)
                    )
                }
                .buttonStyle(PlainButtonStyle())
                
                // Record Directly Button
                Button(action: {
                    if recorder.isRecording {
                        if let url = recorder.stopRecording() {
                            self.stagedAudioURL = url
                            self.voiceNameInput = "ರೆಕಾರ್ಡ್ ಮಾಡಿದ ಧ್ವನಿ \(Date().formatted(date: .omitted, time: .shortened))"
                        }
                    } else {
                        recorder.startRecording()
                    }
                }) {
                    VStack(spacing: 8) {
                        Image(systemName: recorder.isRecording ? "stop.circle.fill" : "mic.circle.fill")
                            .font(.system(size: 26))
                            .foregroundColor(recorder.isRecording ? .red : .purple)
                        Text(recorder.isRecording ? "ನಿಲ್ಲಿಸಿ (\(String(format: "%.1fs", recorder.recordedDuration)))" : "ಧ್ವನಿ ರೆಕಾರ್ಡ್")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundColor(.primary)
                        Text(recorder.isRecording ? "ರೆಕಾರ್ಡ್ ಆಗುತ್ತಿದೆ..." : "ಮೈಕ್ ಬಳಸಿ")
                            .font(.system(size: 10))
                            .foregroundColor(recorder.isRecording ? .red : .secondary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .background(recorder.isRecording ? Color.red.opacity(0.1) : Color(UIColor.secondarySystemGroupedBackground))
                    .cornerRadius(14)
                    .overlay(
                        RoundedRectangle(cornerRadius: 14)
                            .stroke(recorder.isRecording ? Color.red : Color.purple.opacity(0.3), lineWidth: 1.5)
                    )
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
    }
    
    // MARK: - Staged Audio Card
    private func stagedAudioCard(audioURL: URL) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
                Text("ಆಡಿಯೊ ಮಾದರಿ ಸಿದ್ಧವಾಗಿದೆ (Sample Ready)")
                    .font(.system(size: 13, weight: .bold))
                Spacer()
            }
            
            // Audio Preview Play Button
            HStack(spacing: 12) {
                Button(action: {
                    togglePreview(url: audioURL)
                }) {
                    HStack(spacing: 6) {
                        Image(systemName: isPreviewPlaying ? "pause.fill" : "play.fill")
                        Text(isPreviewPlaying ? "ನಿಲ್ಲಿಸಿ" : "ಮಾದರಿ ಕೇಳಿ")
                    }
                    .font(.system(size: 12, weight: .bold))
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(Color.orange.opacity(0.15))
                    .foregroundColor(.orange)
                    .cornerRadius(10)
                }
                
                Text(audioURL.lastPathComponent)
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundColor(.secondary)
                    .lineLimit(1)
            }
            
            // Name Input
            TextField("ಧ್ವನಿಯ ಹೆಸರು ನಮೂದಿಸಿ (Voice Name)...", text: $voiceNameInput)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .font(.system(size: 13))
            
            // Save Button
            Button(action: {
                saveStagedVoice(url: audioURL)
            }) {
                HStack {
                    Image(systemName: "plus.circle.fill")
                    Text("ಈ ಧ್ವನಿಯನ್ನು ಸೇರಿಸಿ & ಬಳಸಿ (Save & Activate)")
                }
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
                .background(Color.orange)
                .cornerRadius(10)
            }
            .disabled(voiceNameInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        }
        .padding(14)
        .background(Color(UIColor.secondarySystemGroupedBackground))
        .cornerRadius(14)
        .shadow(color: Color.black.opacity(0.04), radius: 6, x: 0, y: 2)
    }
    
    // MARK: - Saved Voices List
    private var savedVoicesSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("ಸಂಗ್ರಹಿಸಿದ ಕಸ್ಟಮ್ ಧ್ವನಿಗಳು (Saved Custom Voices)")
                .font(.system(size: 14, weight: .bold))
                .frame(maxWidth: .infinity, alignment: .leading)
            
            if viewModel.customVoices.isEmpty {
                VStack(spacing: 6) {
                    Image(systemName: "mic.slash")
                        .font(.system(size: 24))
                        .foregroundColor(.secondary)
                    Text("ಇನ್ನೂ ಯಾವುದೇ ಕಸ್ಟಮ್ ಧ್ವನಿ ಮಾದರಿಗಳನ್ನು ಸೇರಿಸಿಲ್ಲ.")
                        .font(.system(size: 12))
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 24)
                .background(Color(UIColor.secondarySystemGroupedBackground))
                .cornerRadius(14)
            } else {
                ForEach(viewModel.customVoices) { voice in
                    HStack(spacing: 12) {
                        Image(systemName: "person.crop.circle.badge.waveform")
                            .font(.system(size: 22))
                            .foregroundColor(.orange)
                        
                        VStack(alignment: .leading, spacing: 2) {
                            Text(voice.name)
                                .font(.system(size: 14, weight: .bold))
                            Text(voice.description)
                                .font(.system(size: 11))
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        // Select / Activate button
                        Button(action: {
                            viewModel.activateCustomVoice(voice)
                            dismiss()
                        }) {
                            Text(viewModel.activeCustomVoice?.id == voice.id ? "ಸಕ್ರಿಯ ✓" : "ಆಯ್ಕೆ ಮಾಡಿ")
                                .font(.system(size: 11, weight: .bold))
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .background(viewModel.activeCustomVoice?.id == voice.id ? Color.green : Color.orange.opacity(0.12))
                                .foregroundColor(viewModel.activeCustomVoice?.id == voice.id ? .white : .orange)
                                .cornerRadius(8)
                        }
                        
                        // Delete button
                        Button(action: {
                            viewModel.deleteCustomVoice(voice)
                        }) {
                            Image(systemName: "trash")
                                .font(.system(size: 13))
                                .foregroundColor(.red.opacity(0.8))
                        }
                    }
                    .padding(12)
                    .background(Color(UIColor.secondarySystemGroupedBackground))
                    .cornerRadius(12)
                }
            }
        }
    }
    
    // MARK: - Helpers
    private func handleImportedFile(result: Result<[URL], Error>) {
        switch result {
        case .success(let urls):
            guard let selectedURL = urls.first else { return }
            guard selectedURL.startAccessingSecurityScopedResource() else { return }
            defer { selectedURL.stopAccessingSecurityScopedResource() }
            
            let tempDir = FileManager.default.temporaryDirectory
            let targetURL = tempDir.appendingPathComponent("imported_\(UUID().uuidString)_\(selectedURL.lastPathComponent)")
            do {
                if FileManager.default.fileExists(atPath: targetURL.path) {
                    try FileManager.default.removeItem(at: targetURL)
                }
                try FileManager.default.copyItem(at: selectedURL, to: targetURL)
                self.stagedAudioURL = targetURL
                self.voiceNameInput = selectedURL.deletingPathExtension().lastPathComponent
            } catch {
                viewModel.showToast("ಫೈಲ್ ಲೋಡ್ ವಿಫಲ: \(error.localizedDescription)")
            }
        case .failure(let error):
            viewModel.showToast("ಅಪ್‌ಲೋಡ್ ದೋಷ: \(error.localizedDescription)")
        }
    }
    
    private func togglePreview(url: URL) {
        if isPreviewPlaying {
            previewPlayer?.stop()
            previewPlayer = nil
            isPreviewPlaying = false
        } else {
            do {
                try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
                try AVAudioSession.sharedInstance().setActive(true)
                previewPlayer = try AVAudioPlayer(contentsOf: url)
                previewPlayer?.play()
                isPreviewPlaying = true
            } catch {
                viewModel.showToast("ಪ್ಲೇಬ್ಯಾಕ್ ದೋಷ: \(error.localizedDescription)")
            }
        }
    }
    
    private func saveStagedVoice(url: URL) {
        guard let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else { return }
        let customVoicesDir = docs.appendingPathComponent("CustomVoices")
        try? FileManager.default.createDirectory(at: customVoicesDir, withIntermediateDirectories: true)
        
        let savedFileName = "\(UUID().uuidString)_\(url.lastPathComponent)"
        let destinationURL = customVoicesDir.appendingPathComponent(savedFileName)
        
        do {
            try FileManager.default.copyItem(at: url, to: destinationURL)
            let newProfile = CustomVoiceProfile(
                name: voiceNameInput,
                kannadaName: voiceNameInput,
                referenceAudioFileName: savedFileName,
                description: "ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ಆಡಿಯೊ ಮಾದರಿ (\(voiceNameInput))"
            )
            viewModel.addCustomVoice(newProfile)
            self.stagedAudioURL = nil
            self.voiceNameInput = ""
            viewModel.showToast("\"\(newProfile.name)\" ಧ್ವನಿಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಸೇರಿಸಲಾಗಿದೆ!")
        } catch {
            viewModel.showToast("ಉಳಿಸಲು ವಿಫಲವಾಗಿದೆ: \(error.localizedDescription)")
        }
    }
}
