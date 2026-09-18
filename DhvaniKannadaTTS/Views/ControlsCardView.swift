import SwiftUI

/// Sliders for Pitch, Speech Rate, and Volume with live feedback
public struct ControlsCardView: View {
    @ObservedObject var viewModel: TTSViewModel
    @State private var isExpanded: Bool = true
    
    public var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            // Header with collapse and reset
            HStack {
                HStack(spacing: 6) {
                    Image(systemName: "slider.horizontal.3")
                        .foregroundColor(.orange)
                    Text("ಧ್ವನಿ ಹೊಂದಾಣಿಕೆಗಳು (Voice Controls)")
                        .font(.system(size: 15, weight: .bold))
                }
                
                Spacer()
                
                Button(action: {
                    withAnimation {
                        viewModel.resetToDefaults()
                    }
                }) {
                    Text("ಮರುಹೊಂದಿಸಿ")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(.orange)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.orange.opacity(0.1))
                        .cornerRadius(8)
                }
            }
            
            if isExpanded {
                VStack(spacing: 16) {
                    // 1. Pitch Slider
                    SliderRow(
                        title: "ಸ್ವರದ ಶ್ರುತಿ / Pitch",
                        icon: "waveform.path",
                        valueText: String(format: "%.2fx", viewModel.pitch),
                        value: $viewModel.pitch,
                        range: 0.5...1.8,
                        step: 0.05,
                        minLabel: "ಗಂಭೀರ (Deep)",
                        maxLabel: "ತೀಕ್ಷ್ಣ (High)"
                    )
                    
                    Divider()
                    
                    // 2. Speed / Rate Slider
                    SliderRow(
                        title: "ಓದುವ ವೇಗ / Speed",
                        icon: "gauge.with.needle",
                        valueText: String(format: "%.2fx", viewModel.speechRate),
                        value: $viewModel.speechRate,
                        range: 0.5...1.8,
                        step: 0.05,
                        minLabel: "ನಿಧಾನ (Slow)",
                        maxLabel: "ವೇಗ (Fast)"
                    )
                    
                    Divider()
                    
                    // 3. Volume Slider
                    SliderRow(
                        title: "ಧ್ವನಿ ಮಟ್ಟ / Volume",
                        icon: "speaker.wave.2.fill",
                        valueText: "\(Int(viewModel.volume * 100))%",
                        value: $viewModel.volume,
                        range: 0.0...1.0,
                        step: 0.05,
                        minLabel: "ಕಡಿಮೆ (0%)",
                        maxLabel: "ಗರಿಷ್ಠ (100%)"
                    )
                }
                .padding(.top, 4)
            }
        }
        .padding(16)
        .background(Color(UIColor.secondarySystemGroupedBackground))
        .cornerRadius(18)
        .shadow(color: Color.black.opacity(0.04), radius: 8, x: 0, y: 3)
    }
}

private struct SliderRow: View {
    let title: String
    let icon: String
    let valueText: String
    @Binding var value: Float
    let range: ClosedRange<Float>
    let step: Float
    let minLabel: String
    let maxLabel: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Image(systemName: icon)
                    .font(.system(size: 13))
                    .foregroundColor(.secondary)
                Text(title)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.primary)
                Spacer()
                Text(valueText)
                    .font(.system(size: 13, weight: .bold, design: .monospaced))
                    .foregroundColor(.orange)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.orange.opacity(0.12))
                    .cornerRadius(6)
            }
            
            Slider(value: $value, in: range, step: step)
                .accentColor(.orange)
            
            HStack {
                Text(minLabel)
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
                Spacer()
                Text(maxLabel)
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
            }
        }
    }
}
