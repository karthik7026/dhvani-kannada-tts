import Foundation

/// Fast phonetic English (Baraha/ITRANS scheme) to Kannada Script Transliterator
public struct KannadaTransliterator {
    
    // Independent Vowels
    private static let independentVowels: [(String, String)] = [
        ("aa", "ಆ"), ("AA", "ಆ"), ("A", "ಆ"),
        ("ai", "ಐ"), ("au", "ಔ"), ("ou", "ಔ"),
        ("ee", "ಈ"), ("ii", "ಈ"), ("II", "ಈ"), ("I", "ಈ"),
        ("oo", "ಊ"), ("uu", "ಊ"), ("UU", "ಊ"), ("U", "ಊ"),
        ("Ru", "ಋ"), ("RU", "ೠ"),
        ("a", "ಅ"), ("i", "ಇ"), ("u", "ಉ"),
        ("e", "ಎ"), ("E", "ಏ"), ("ee", "ಏ"),
        ("o", "ಒ"), ("O", "ಓ"), ("oo", "ಓ"),
        ("am", "ಅಂ"), ("ah", "ಅಃ")
    ]
    
    // Dependent Vowel Signs (Matras)
    private static let dependentVowels: [(String, String)] = [
        ("aa", "ಾ"), ("AA", "ಾ"), ("A", "ಾ"),
        ("ai", "ೈ"), ("au", "ೌ"), ("ou", "ೌ"),
        ("ee", "ೀ"), ("ii", "ೀ"), ("II", "ೀ"), ("I", "ೀ"),
        ("oo", "ೂ"), ("uu", "ೂ"), ("UU", "ೂ"), ("U", "ೂ"),
        ("Ru", "ೃ"),
        ("a", ""), // Inherent 'a' vowel
        ("i", "ಿ"), ("u", "ು"),
        ("e", "ೆ"), ("E", "ೇ"),
        ("o", "ೊ"), ("O", "ೋ")
    ]
    
    // Consonant Mappings
    private static let consonants: [(String, String)] = [
        ("kh", "ಖ"), ("k", "ಕ"),
        ("gh", "ಘ"), ("g", "ಗ"),
        ("ng", "ಙ"),
        ("chh", "ಛ"), ("ch", "ಚ"),
        ("jh", "ಝ"), ("j", "ಜ"),
        ("ny", "ಞ"),
        ("Th", "ಠ"), ("T", "ಟ"),
        ("Dh", "ಢ"), ("D", "ಡ"),
        ("N", "ಣ"),
        ("th", "ಥ"), ("t", "ತ"),
        ("dh", "ಧ"), ("d", "ದ"),
        ("n", "ನ"),
        ("ph", "ಫ"), ("f", "ಫ"), ("p", "ಪ"),
        ("bh", "ಭ"), ("b", "ಬ"),
        ("m", "ಮ"),
        ("y", "ಯ"),
        ("r", "ರ"),
        ("l", "ಲ"),
        ("v", "ವ"), ("w", "ವ"),
        ("sh", "ಶ"), ("Sh", "ಷ"), ("s", "ಸ"),
        ("h", "ಹ"),
        ("L", "ಳ"), ("zh", "ೞ")
    ]
    
    private static let virama = "್"
    
    /// Transliterates English phonetic word into Kannada script
    public static func transliterate(text: String) -> String {
        var output = ""
        let words = text.components(separatedBy: " ")
        
        for (idx, word) in words.enumerated() {
            if idx > 0 { output += " " }
            output += transliterateWord(word)
        }
        
        return output
    }
    
    private static func transliterateWord(_ input: String) -> String {
        var result = ""
        var index = input.startIndex
        
        while index < input.endIndex {
            // Check for special punctuation/digits
            let char = input[index]
            if !char.isLetter {
                result.append(char)
                index = input.index(after: index)
                continue
            }
            
            // 1. Try to match a consonant
            var matchedConsonant: (key: String, char: String)? = nil
            for (key, val) in consonants {
                if input[index...].hasPrefix(key) {
                    matchedConsonant = (key, val)
                    break
                }
            }
            
            if let cons = matchedConsonant {
                // Advance past consonant key
                let afterConsIndex = input.index(index, offsetBy: cons.key.count)
                
                // Check if followed by vowel
                var matchedVowel: (key: String, sign: String)? = nil
                if afterConsIndex < input.endIndex {
                    for (vKey, vSign) in dependentVowels {
                        if input[afterConsIndex...].hasPrefix(vKey) {
                            matchedVowel = (vKey, vSign)
                            break
                        }
                    }
                }
                
                if let vowel = matchedVowel {
                    result += cons.char + vowel.sign
                    index = input.index(afterConsIndex, offsetBy: vowel.key.count)
                } else {
                    // No vowel follows, add virama (halant)
                    result += cons.char + virama
                    index = afterConsIndex
                }
            } else {
                // 2. Try to match an independent vowel
                var matchedIndVowel: (key: String, char: String)? = nil
                for (vKey, vChar) in independentVowels {
                    if input[index...].hasPrefix(vKey) {
                        matchedIndVowel = (vKey, vChar)
                        break
                    }
                }
                
                if let indVowel = matchedIndVowel {
                    result += indVowel.char
                    index = input.index(index, offsetBy: indVowel.key.count)
                } else {
                    // Fallback
                    result.append(input[index])
                    index = input.index(after: index)
                }
            }
        }
        
        // Clean up trailing viramas if needed
        return result
    }
}
