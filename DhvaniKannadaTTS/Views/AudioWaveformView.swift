import SwiftUI

/// Animated visual soundwave indicating active speech playback
public struct AudioWaveformView: View {
    let isPlaying: Bool
    let barCount: Int = 18
    
    @State private var animatedHeights: [CGFloat] = Array(repeating: 6, count: 18)
    @State private var timer: Timer?
    
    public init(isPlaying: Bool) {
        self.isPlaying = isPlaying
    }
    
    public var body: some View {
        HStack(spacing: 3) {
            ForEach(0..<barCount, id: \.self) { index in
                RoundedRectangle(cornerRadius: 2)
                    .fill(
                        LinearGradient(
                            colors: [Color.orange, Color.red, Color.purple],
                            startPoint: .bottom,
                            endPoint: .top
                        )
                    )
                    .frame(width: 3, height: isPlaying ? animatedHeights[index] : 4)
                    .animation(.easeInOut(duration: 0.25).repeatForever(autoreverses: true), value: animatedHeights[index])
            }
        }
        .frame(height: 28)
        .onAppear {
            if isPlaying {
                startAnimation()
            }
        }
        .onChange(of: isPlaying) { playing in
            if playing {
                startAnimation()
            } else {
                stopAnimation()
            }
        }
        .onDisappear {
            stopAnimation()
        }
    }
    
    private func startAnimation() {
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 0.15, repeats: true) { _ in
            withAnimation {
                self.animatedHeights = (0..<barCount).map { _ in
                    CGFloat.random(in: 4...28)
                }
            }
        }
    }
    
    private func stopAnimation() {
        timer?.invalidate()
        timer = nil
        withAnimation {
            animatedHeights = Array(repeating: 4, count: barCount)
        }
    }
}
