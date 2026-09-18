import SwiftUI

/// Preset Kannada sample texts categorized sheet
public struct PresetLibraryView: View {
    @ObservedObject var viewModel: TTSViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var selectedCategory: PresetCategory = .conversation
    
    public var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Category Pills
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(PresetCategory.allCases) { category in
                            Button(action: {
                                withAnimation {
                                    selectedCategory = category
                                }
                            }) {
                                HStack(spacing: 6) {
                                    Image(systemName: category.iconName)
                                        .font(.system(size: 12))
                                    Text(category.rawValue)
                                        .font(.system(size: 13, weight: .medium))
                                }
                                .padding(.horizontal, 12)
                                .padding(.vertical, 8)
                                .background(
                                    selectedCategory == category ?
                                    Color.orange :
                                    Color(UIColor.secondarySystemGroupedBackground)
                                )
                                .foregroundColor(selectedCategory == category ? .white : .primary)
                                .cornerRadius(16)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                }
                .background(Color(UIColor.systemGroupedBackground))
                
                // Samples List
                List {
                    let filtered = PresetLibrary.samples.filter { $0.category == selectedCategory }
                    
                    ForEach(filtered) { sample in
                        Button(action: {
                            viewModel.applySampleText(sample)
                        }) {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Text(sample.title)
                                        .font(.system(size: 15, weight: .bold))
                                        .foregroundColor(.primary)
                                    Spacer()
                                    HStack(spacing: 4) {
                                        Image(systemName: sample.suggestedGender == .female ? "person.crop.circle.fill.badge.checkmark" : "person.crop.circle.fill")
                                            .font(.system(size: 11))
                                        Text(sample.suggestedGender.shortName)
                                            .font(.system(size: 11, weight: .semibold))
                                    }
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(sample.suggestedGender == .female ? Color.pink.opacity(0.12) : Color.blue.opacity(0.12))
                                    .foregroundColor(sample.suggestedGender == .female ? .pink : .blue)
                                    .cornerRadius(6)
                                }
                                
                                Text(sample.text)
                                    .font(.system(size: 14))
                                    .foregroundColor(.secondary)
                                    .lineLimit(3)
                                
                                HStack {
                                    Label(sample.suggestedPitch.title, systemImage: "waveform")
                                        .font(.system(size: 11))
                                        .foregroundColor(.orange)
                                    Spacer()
                                    Text("ಆಯ್ಕೆ ಮಾಡಿ ➔")
                                        .font(.system(size: 11, weight: .semibold))
                                        .foregroundColor(.orange)
                                }
                                .padding(.top, 2)
                            }
                            .padding(.vertical, 6)
                        }
                    }
                }
                .listStyle(InsetGroupedListStyle())
            }
            .navigationTitle("ಕನ್ನಡ ಮಾದರಿ ಪಠ್ಯಗಳು")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("ಮುಚ್ಚಿ (Close)") {
                        dismiss()
                    }
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.orange)
                }
            }
        }
    }
}
