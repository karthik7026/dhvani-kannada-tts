import SwiftUI

/// Main Studio Screen for Dhvani Kannada TTS
public struct MainTTSView: View {
    @StateObject private var viewModel = TTSViewModel()
    
    public init() {}
    
    public var body: some View {
        ZStack(alignment: .bottom) {
            // Background
            Color(UIColor.systemGroupedBackground)
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // Header Bar
                headerBar
                
                // Scrollable Content
                ScrollView {
                    VStack(spacing: 16) {
                        // Text Editor Card
                        TextEditorCardView(viewModel: viewModel)
                        
                        // Voice Selector Card (Gender, Engine, Pitch Presets)
                        VoiceSelectorView(viewModel: viewModel)
                        
                        // Controls Card (Pitch, Speed, Volume)
                        ControlsCardView(viewModel: viewModel)
                        
                        // Bottom Padding for floating bar
                        Spacer()
                            .frame(height: 100)
                    }
                    .padding(.horizontal, 16)
                    .padding(.top, 12)
                }
            }
            
            // Sticky Floating Player Control Bar
            floatingPlayerBar
                .padding(.horizontal, 16)
                .padding(.bottom, 12)
            
            // Toast Notification
            if let message = viewModel.toastMessage {
                toastView(message: message)
                    .transition(.move(edge: .top).combined(with: .opacity))
                    .padding(.top, 50)
            }
        }
        .sheet(isPresented: $viewModel.showPresetsSheet) {
            PresetLibraryView(viewModel: viewModel)
        }
        .sheet(isPresented: $viewModel.showCustomVoiceManager) {
            CustomVoiceManagerView(viewModel: viewModel)
        }
        .sheet(isPresented: $viewModel.showShareSheet) {
            if let url = viewModel.exportedAudioURL {
                ShareSheet(activityItems: [url])
            }
        }
    }
    
    // MARK: - Header Bar
    private var headerBar: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 6) {
                    Text("ಧ್ವನಿ")
                        .font(.system(size: 24, weight: .black))
                        .foregroundColor(.orange)
                    Text("• DHVANI")
                        .font(.system(size: 16, weight: .bold, design: .rounded))
                        .foregroundColor(.primary)
                }
                Text("ಕನ್ನಡ ಧ್ವನಿ ಸಂಶ್ಲೇಷಣೆ (Kannada Text-to-Speech)")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            // Quick preset samples button in header
            Button(action: {
                viewModel.showPresetsSheet = true
            }) {
                HStack(spacing: 4) {
                    Image(systemName: "sparkles")
                        .foregroundColor(.orange)
                    Text("ಮಾದರಿಗಳು")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(.primary)
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(Color(UIColor.secondarySystemGroupedBackground))
                .cornerRadius(12)
                .shadow(color: Color.black.opacity(0.04), radius: 4, x: 0, y: 2)
            }
        }
        .padding(.horizontal, 16)
        .padding(.top, 12)
        .padding(.bottom, 8)
        .background(Color(UIColor.systemGroupedBackground))
    }
    
    // MARK: - Floating Player Bar
    private var floatingPlayerBar: some View {
        HStack(spacing: 12) {
            // Waveform animation
            AudioWaveformView(isPlaying: viewModel.playbackState == .playing)
                .frame(width: 60)
            
            // Current status label
            VStack(alignment: .leading, spacing: 2) {
                Text(statusText)
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.primary)
                Text("\(viewModel.selectedGender.shortName) • \(viewModel.selectedPreset.title)")
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            // Stop button
            if viewModel.playbackState == .playing || viewModel.playbackState == .paused {
                Button(action: {
                    viewModel.stop()
                }) {
                    Image(systemName: "stop.fill")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(.red)
                        .frame(width: 38, height: 38)
                        .background(Color.red.opacity(0.12))
                        .clipShape(Circle())
                }
            }
            
            // Export / Share Audio button
            Button(action: {
                viewModel.exportAudio()
            }) {
                Group {
                    if viewModel.isExporting {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .orange))
                    } else {
                        Image(systemName: "square.and.arrow.up")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundColor(.orange)
                    }
                }
                .frame(width: 38, height: 38)
                .background(Color.orange.opacity(0.12))
                .clipShape(Circle())
            }
            .disabled(viewModel.isExporting)
            
            // Main Play/Pause Button
            Button(action: {
                withAnimation {
                    viewModel.togglePlayback()
                }
            }) {
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [Color.orange, Color.red],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 48, height: 48)
                        .shadow(color: Color.orange.opacity(0.4), radius: 6, x: 0, y: 3)
                    
                    if viewModel.playbackState == .loading {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    } else {
                        Image(systemName: playButtonIcon)
                            .font(.system(size: 18, weight: .bold))
                            .foregroundColor(.white)
                            .offset(x: viewModel.playbackState == .playing ? 0 : 1)
                    }
                }
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(
            Color(UIColor.secondarySystemGroupedBackground)
                .overlay(
                    RoundedRectangle(cornerRadius: 24)
                        .stroke(Color.orange.opacity(0.2), lineWidth: 1)
                )
        )
        .cornerRadius(24)
        .shadow(color: Color.black.opacity(0.12), radius: 12, x: 0, y: 4)
    }
    
    private var playButtonIcon: String {
        switch viewModel.playbackState {
        case .playing: return "pause.fill"
        case .paused: return "play.fill"
        case .loading: return ""
        case .idle, .stopped, .error: return "play.fill"
        }
    }
    
    private var statusText: String {
        switch viewModel.playbackState {
        case .idle: return "ಸಿದ್ಧವಾಗಿದೆ (Ready)"
        case .loading: return "ಧ್ವನಿ ತಯಾರಾಗುತ್ತಿದೆ..."
        case .playing: return "ಓದಲಾಗುತ್ತಿದೆ (Speaking)"
        case .paused: return "ವಿರಾಮಗೊಳಿಸಲಾಗಿದೆ (Paused)"
        case .stopped: return "ನಿಲ್ಲಿಸಲಾಗಿದೆ (Stopped)"
        case .error: return "ದೋಷ (Error)"
        }
    }
    
    // MARK: - Toast View
    private func toastView(message: String) -> some View {
        VStack {
            HStack(spacing: 8) {
                Image(systemName: "info.circle.fill")
                    .foregroundColor(.orange)
                Text(message)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.primary)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(Color(UIColor.secondarySystemGroupedBackground))
            .cornerRadius(20)
            .shadow(color: Color.black.opacity(0.15), radius: 10, x: 0, y: 4)
            Spacer()
        }
    }
}

#Preview {
    MainTTSView()
}
