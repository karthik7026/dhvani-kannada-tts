import SwiftUI

/// Voice selection, Gender switch, Engine tabs, and Custom Cloned Voice Manager
public struct VoiceSelectorView: View {
    @ObservedObject var viewModel: TTSViewModel
    
    public var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Engine Selector Segmented Control (HD Neural, Custom Clone, Native)
            VStack(alignment: .leading, spacing: 6) {
                Text("ಧ್ವನಿ ಎಂಜಿನ್ (Voice Engine)")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.secondary)
                
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(TTSEngineType.allCases) { engine in
                            Button(action: {
                                withAnimation(.spring()) {
                                    viewModel.selectEngine(engine)
                                }
                            }) {
                                HStack(spacing: 6) {
                                    Image(systemName: engineIcon(engine))
                                        .font(.system(size: 12, weight: .bold))
                                    
                                    VStack(alignment: .leading, spacing: 1) {
                                        Text(engineTitle(engine))
                                            .font(.system(size: 12, weight: .semibold))
                                        Text(engineSubtitle(engine))
                                            .font(.system(size: 9))
                                            .opacity(0.8)
                                    }
                                }
                                .padding(.vertical, 8)
                                .padding(.horizontal, 10)
                                .background(
                                    viewModel.selectedEngine == engine ?
                                    LinearGradient(colors: [Color.orange, Color.red], startPoint: .topLeading, endPoint: .bottomTrailing) :
                                    LinearGradient(colors: [Color(UIColor.tertiarySystemFill), Color(UIColor.tertiarySystemFill)], startPoint: .top, endPoint: .bottom)
                                )
                                .foregroundColor(viewModel.selectedEngine == engine ? .white : .primary)
                                .cornerRadius(12)
                                .shadow(color: viewModel.selectedEngine == engine ? Color.orange.opacity(0.3) : Color.clear, radius: 4, x: 0, y: 2)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                }
            }
            
            // If Custom Cloned Voice is active, show the Custom Voice Card
            if viewModel.selectedEngine == .customCloned {
                customVoiceActiveCard
            } else {
                // Standard Gender Selector Cards (Female & Male)
                VStack(alignment: .leading, spacing: 8) {
                    Text("ಧ್ವನಿ ಆಯ್ಕೆ (Voice Selection)")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(.secondary)
                    
                    HStack(spacing: 12) {
                        // Female Voice Card
                        VoiceGenderCard(
                            gender: .female,
                            title: "ಹೆಣ್ಣು ಧ್ವನಿ",
                            subtitle: viewModel.selectedEngine == .neural ? "Sapna (ಸ್ಪಪ್ನಾ)" : "ಆ್ಯಪಲ್ ಹೆಣ್ಣು",
                            icon: "person.crop.circle.fill.badge.checkmark",
                            accentColor: Color.pink,
                            isSelected: viewModel.selectedGender == .female
                        ) {
                            withAnimation(.spring()) {
                                viewModel.selectGender(.female)
                            }
                        }
                        
                        // Male Voice Card
                        VoiceGenderCard(
                            gender: .male,
                            title: "ಗಂಡು ಧ್ವನಿ",
                            subtitle: viewModel.selectedEngine == .neural ? "Gagan (ಗಗನ್)" : "ಆ್ಯಪಲ್ ಗಂಡು",
                            icon: "person.crop.circle.fill",
                            accentColor: Color.blue,
                            isSelected: viewModel.selectedGender == .male
                        ) {
                            withAnimation(.spring()) {
                                viewModel.selectGender(.male)
                            }
                        }
                    }
                }
            }
            
            // Quick Pitch Presets Pills
            VStack(alignment: .leading, spacing: 8) {
                Text("ಸ್ವರದ ಶೈಲಿ & ಮಾದರಿಗಳು (Voice Pitch Presets)")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.secondary)
                
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(PitchPreset.allCases) { preset in
                            Button(action: {
                                withAnimation(.spring()) {
                                    viewModel.applyPreset(preset)
                                }
                            }) {
                                HStack(spacing: 6) {
                                    Circle()
                                        .fill(presetColor(preset))
                                        .frame(width: 8, height: 8)
                                    Text(preset.title)
                                        .font(.system(size: 13, weight: .medium))
                                }
                                .padding(.horizontal, 12)
                                .padding(.vertical, 7)
                                .background(
                                    viewModel.selectedPreset == preset ?
                                    Color.orange.opacity(0.18) :
                                    Color(UIColor.tertiarySystemFill)
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 16)
                                        .stroke(viewModel.selectedPreset == preset ? Color.orange : Color.clear, lineWidth: 1.5)
                                )
                                .cornerRadius(16)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                }
            }
        }
        .padding(16)
        .background(Color(UIColor.secondarySystemGroupedBackground))
        .cornerRadius(18)
        .shadow(color: Color.black.opacity(0.04), radius: 8, x: 0, y: 3)
    }
    
    // MARK: - Custom Voice Active Banner
    private var customVoiceActiveCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Image(systemName: "waveform.badge.mic")
                    .foregroundColor(.orange)
                    .font(.system(size: 16))
                Text("ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ಆಡಿಯೊ ಮಾದರಿ")
                    .font(.system(size: 13, weight: .bold))
                Spacer()
                
                Button(action: {
                    viewModel.showCustomVoiceManager = true
                }) {
                    Text("ಆಡಿಯೊ ಬದಲಿಸಿ / ಸೇರಿಸಿ ➔")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(.orange)
                }
            }
            
            if let active = viewModel.activeCustomVoice {
                HStack(spacing: 10) {
                    Circle()
                        .fill(Color.orange.opacity(0.2))
                        .frame(width: 36, height: 36)
                        .overlay(
                            Image(systemName: "person.crop.circle.fill")
                                .foregroundColor(.orange)
                        )
                    
                    VStack(alignment: .leading, spacing: 2) {
                        Text(active.name)
                            .font(.system(size: 14, weight: .bold))
                        Text("ಉಲ್ಲೇಖಿತ ಆಡಿಯೊ ಫೈಲ್: \(active.referenceAudioFileName)")
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundColor(.secondary)
                            .lineLimit(1)
                    }
                    Spacer()
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                }
                .padding(10)
                .background(Color(UIColor.tertiarySystemFill))
                .cornerRadius(10)
            } else {
                Button(action: {
                    viewModel.showCustomVoiceManager = true
                }) {
                    HStack {
                        Image(systemName: "plus.circle.fill")
                        Text("ಆಡಿಯೊ ಫೈಲ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ (Upload Audio Sample)")
                    }
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(Color.orange)
                    .cornerRadius(10)
                }
            }
        }
        .padding(12)
        .background(Color.orange.opacity(0.06))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.orange.opacity(0.25), lineWidth: 1)
        )
    }
    
    private func engineIcon(_ engine: TTSEngineType) -> String {
        switch engine {
        case .neural: return "sparkles"
        case .customCloned: return "waveform.badge.mic"
        case .native: return "iphone.gen3"
        }
    }
    
    private func engineTitle(_ engine: TTSEngineType) -> String {
        switch engine {
        case .neural: return "HD Neural"
        case .customCloned: return "Voice Clone"
        case .native: return "Offline"
        }
    }
    
    private func engineSubtitle(_ engine: TTSEngineType) -> String {
        switch engine {
        case .neural: return "ಸ್ಪಪ್ನಾ / ಗಗನ್"
        case .customCloned: return "ಕಸ್ಟಮ್ ಆಡಿಯೊ"
        case .native: return "ಆ್ಯಪಲ್ ಕನ್ನಡ"
        }
    }
    
    private func presetColor(_ preset: PitchPreset) -> Color {
        switch preset {
        case .natural: return .green
        case .energeticNarrator: return .orange
        case .deepMale: return .blue
        case .softFemale: return .pink
        case .child: return .purple
        case .newsAnchor: return .red
        }
    }
}

private struct VoiceGenderCard: View {
    let gender: VoiceGender
    let title: String
    let subtitle: String
    let icon: String
    let accentColor: Color
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Image(systemName: icon)
                        .font(.system(size: 22))
                        .foregroundColor(isSelected ? accentColor : .secondary)
                    Spacer()
                    if isSelected {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(accentColor)
                            .font(.system(size: 16))
                    }
                }
                
                Text(title)
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(.primary)
                
                Text(subtitle)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.secondary)
            }
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                isSelected ?
                accentColor.opacity(0.12) :
                Color(UIColor.tertiarySystemFill)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 14)
                    .stroke(isSelected ? accentColor : Color.clear, lineWidth: 2)
            )
            .cornerRadius(14)
        }
        .buttonStyle(PlainButtonStyle())
    }
}
