import SwiftUI

/// Text input editor card with Kannada transliteration and normalization preview
public struct TextEditorCardView: View {
    @ObservedObject var viewModel: TTSViewModel
    @FocusState private var isInputFocused: Bool
    @State private var showNormalizationPreview: Bool = false
    
    public var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header: Actions and Transliteration toggle
            HStack {
                Text("ಕನ್ನಡ ಪಠ್ಯ (Kannada Text)")
                    .font(.system(size: 15, weight: .bold))
                
                Spacer()
                
                // Transliteration Toggle Button
                Button(action: {
                    withAnimation {
                        viewModel.isTransliterationEnabled.toggle()
                        if viewModel.isTransliterationEnabled {
                            viewModel.showToast("ಇಂಗ್ಲಿಷ್ ಟೈಪಿಂಗ್ ಕನ್ನಡಕ್ಕೆ ಪರಿವರ್ತನೆಯಾಗುತ್ತದೆ (English -> ಕನ್ನಡ ON)")
                        }
                    }
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: viewModel.isTransliterationEnabled ? "keyboard.fill" : "keyboard")
                            .font(.system(size: 12))
                        Text(viewModel.isTransliterationEnabled ? "En ➔ ಕ [ON]" : "En ➔ ಕ [OFF]")
                            .font(.system(size: 11, weight: .bold))
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(viewModel.isTransliterationEnabled ? Color.green.opacity(0.18) : Color(UIColor.tertiarySystemFill))
                    .foregroundColor(viewModel.isTransliterationEnabled ? .green : .secondary)
                    .cornerRadius(8)
                }
                
                // Samples button
                Button(action: {
                    viewModel.showPresetsSheet = true
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: "book.pages.fill")
                            .font(.system(size: 12))
                        Text("ಮಾದರಿಗಳು")
                            .font(.system(size: 11, weight: .semibold))
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.orange.opacity(0.12))
                    .foregroundColor(.orange)
                    .cornerRadius(8)
                }
            }
            
            // Text Editor Box
            ZStack(alignment: .topLeading) {
                if viewModel.inputText.isEmpty {
                    Text("ಇಲ್ಲಿ ಕನ್ನಡದಲ್ಲಿ ಪಠ್ಯ ಬರೆಯಿರಿ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ 'namaskara' ಎಂದು ಟೈಪ್ ಮಾಡಿ...")
                        .font(.system(size: 15))
                        .foregroundColor(Color(UIColor.placeholderText))
                        .padding(.horizontal, 4)
                        .padding(.vertical, 8)
                }
                
                TextEditor(text: Binding(
                    get: { viewModel.inputText },
                    set: { viewModel.handleTypingText($0) }
                ))
                .font(.system(size: 16))
                .lineSpacing(4)
                .frame(minHeight: 120, maxHeight: 180)
                .focused($isInputFocused)
                .scrollContentBackground(.hidden)
                .background(Color.clear)
            }
            .padding(10)
            .background(Color(UIColor.tertiarySystemFill))
            .cornerRadius(12)
            
            // Footer: Word count, Clear button, Normalization preview toggle
            HStack {
                Text("\(viewModel.inputText.count) ಅಕ್ಷರಗಳು")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)
                
                if !viewModel.currentWord.isEmpty {
                    Text("• ಪ್ರಸ್ತುತ ಶಬ್ದ: ")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                    Text(viewModel.currentWord)
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(.orange)
                }
                
                Spacer()
                
                if !viewModel.inputText.isEmpty {
                    Button(action: {
                        viewModel.inputText = ""
                    }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.secondary)
                            .font(.system(size: 14))
                    }
                }
            }
            
            // Normalization Preview Disclosure
            VStack(alignment: .leading, spacing: 6) {
                Button(action: {
                    withAnimation(.spring()) {
                        showNormalizationPreview.toggle()
                    }
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: showNormalizationPreview ? "chevron.down" : "chevron.right")
                            .font(.system(size: 10, weight: .bold))
                        Text("ಉಚ್ಚಾರಣಾ ಪೂರ್ವವೀಕ್ಷಣೆ (Spoken Pronunciation Form)")
                            .font(.system(size: 11, weight: .semibold))
                        Spacer()
                    }
                    .foregroundColor(.secondary)
                }
                
                if showNormalizationPreview {
                    Text(viewModel.normalizedPreview.isEmpty ? "(ಖಾಲಿ)" : viewModel.normalizedPreview)
                        .font(.system(size: 12, design: .monospaced))
                        .foregroundColor(Color.primary.opacity(0.8))
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.orange.opacity(0.06))
                        .cornerRadius(8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.orange.opacity(0.2), lineWidth: 1)
                        )
                }
            }
        }
        .padding(16)
        .background(Color(UIColor.secondarySystemGroupedBackground))
        .cornerRadius(18)
        .shadow(color: Color.black.opacity(0.04), radius: 8, x: 0, y: 3)
    }
}
