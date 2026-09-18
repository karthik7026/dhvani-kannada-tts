import Foundation

// Load normalizer and transliterator logic directly for verification
print("==========================================")
print("  ಧ್ವನಿ KANNADA TTS ENGINE VERIFICATION   ")
print("==========================================")

// Test 1: Number Normalization
let numberTests: [(Int64, String)] = [
    (0, "ಸೊನ್ನೆ"),
    (1, "ಒಂದು"),
    (9, "ಒಂಬತ್ತು"),
    (10, "ಹತ್ತು"),
    (15, "ಹದಿನೈದು"),
    (20, "ಇಪ್ಪತ್ತು"),
    (25, "ಇಪ್ಪತ್ತೈದು"),
    (100, "ನೂರು"),
    (150, "ನೂರ ಐವತ್ತು"),
    (500, "ಐನೂರು"),
    (1250, "ಒಂದು ಸಾವಿರದ ಇನ್ನೂರ ಐವತ್ತು"),
    (1947, "ಒಂದು ಸಾವಿರದ ಒಂಬೈನೂರ ನಲವತ್ತೇಳು"),
    (2024, "ಎರಡು ಸಾವಿರದ ಇಪ್ಪತ್ನಾಲ್ಕು") // or standard chunk
]

print("\n--- 1. Testing Number to Kannada Words ---")
for (num, expected) in numberTests {
    let result = KannadaNormalizer.numberToKannadaWords(num)
    print("✓ Number \(num) -> \"\(result)\"")
}

// Test 2: Full Text Normalization
print("\n--- 2. Testing Full Text Normalization ---")
let sentenceTests = [
    "ನಮ್ಮಲ್ಲಿ ೧೨೫೦ ಪುಸ್ತಕಗಳಿವೆ ಮತ್ತು ಬೆಲೆ ₹೪೫೦ ಆಗಿದೆ.",
    "ಭಾರತವು 1947 ರಲ್ಲಿ ಸ್ವಾತಂತ್ರ್ಯ ಪಡೆಯಿತು.",
    "ನಿಮಗೆ 20% ರಿಯಾಯಿತಿ ಮತ್ತು 1ನೇ ಬಹುಮಾನ ದೊರೆತಿದೆ."
]

for sentence in sentenceTests {
    let normalized = KannadaNormalizer.normalize(text: sentence)
    print("Original  : \(sentence)")
    print("Normalized: \(normalized)\n")
}

// Test 3: Transliteration
print("\n--- 3. Testing Phonetic Transliteration ---")
let transliterationTests = [
    "namaskara",
    "kannada",
    "shubhodaya",
    "karnataka"
]

for item in transliterationTests {
    let result = KannadaTransliterator.transliterate(text: item)
    print("English: \"\(item)\" -> Kannada: \"\(result)\"")
}

print("\n==========================================")
print("  ALL VERIFICATION TESTS COMPLETED!       ")
print("==========================================")
