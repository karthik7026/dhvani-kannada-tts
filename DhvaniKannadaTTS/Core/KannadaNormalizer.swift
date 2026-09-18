import Foundation

/// Comprehensive Kannada Text Normalizer
/// Converts digits, symbols, currencies, percentages, and punctuation into phonetically natural spoken Kannada.
public struct KannadaNormalizer {
    
    // Kannada digits mapping
    private static let kannadaDigitsToAscii: [Character: Character] = [
        "೦": "0", "೧": "1", "೨": "2", "೩": "3", "೪": "4",
        "೫": "5", "೬": "6", "೭": "7", "೮": "8", "೯": "9"
    ]
    
    private static let onesWords: [Int: String] = [
        0: "ಸೊನ್ನೆ", 1: "ಒಂದು", 2: "ಎರಡು", 3: "ಮೂರು", 4: "ನಾಲ್ಕು",
        5: "ಐದು", 6: "ಆರು", 7: "ಏಳು", 8: "ಎಂಟು", 9: "ಒಂಬತ್ತು"
    ]
    
    private static let teensWords: [Int: String] = [
        10: "ಹತ್ತು", 11: "ಹನ್ನೊಂದು", 12: "ಹನ್ನೆರಡು", 13: "ಹದಿಮೂರು", 14: "ಹದಿನಾಲ್ಕು",
        15: "ಹದಿನೈದು", 16: "ಹದಿನಾರು", 17: "ಹದಿನೇಳು", 18: "ಹದಿನೆಂಟು", 19: "ಹತ್ತೊಂಬತ್ತು"
    ]
    
    private static let tensWordsBase: [Int: String] = [
        2: "ಇಪ್ಪತ್ತು", 3: "ಮೂವತ್ತು", 4: "ನಲವತ್ತು", 5: "ಐವತ್ತು",
        6: "ಅರವತ್ತು", 7: "ಎಪ್ಪತ್ತು", 8: "ಎಂಬತ್ತು", 9: "ತೊಂಬತ್ತು"
    ]
    
    private static let tensPrefix: [Int: String] = [
        2: "ಇಪ್ಪತ್ತ", 3: "ಮೂವತ್ತ", 4: "ನಲವತ್ತ", 5: "ಐವತ್ತ",
        6: "ಅರವತ್ತ", 7: "ಎಪ್ಪತ್ತ", 8: "ಎಂಬತ್ತ", 9: "ತೊಂಬತ್ತ"
    ]
    
    private static let sandhiOnes: [Int: String] = [
        1: "ೊಂದು", 2: "ೆರಡು", 3: "ಮೂರು", 4: "ನಾಲ್ಕು",
        5: "ೈದು", 6: "ಾರು", 7: "ೇಳು", 8: "ೆಂಟು", 9: "ೊಂಬತ್ತು"
    ]
    
    private static let hundredsExact: [Int: String] = [
        1: "ನೂರು", 2: "ಇನ್ನೂರು", 3: "ಮುನ್ನೂರು", 4: "ನಾನೂರು", 5: "ಐನೂರು",
        6: "ಆರುನೂರು", 7: "ಏಳುನೂರು", 8: "ಎಂಟುನೂರು", 9: "ಒಂಬೈನೂರು"
    ]
    
    private static let hundredsPrefix: [Int: String] = [
        1: "ನೂರ ", 2: "ಇನ್ನೂರ ", 3: "ಮುನ್ನೂರ ", 4: "ನಾನೂರಾ ", 5: "ಐನೂರ ",
        6: "ಆರುನೂರ ", 7: "ಏಳುನೂರ ", 8: "ಎಂಟುನೂರ ", 9: "ಒಂಬೈನೂರ "
    ]
    
    /// Normalizes raw input text for optimal Kannada speech synthesis.
    public static func normalize(text: String) -> String {
        var processed = text
        
        // 1. Convert Kannada numerals (೦-೯) to standard ASCII digits for uniform processing
        for (knDigit, asciiDigit) in kannadaDigitsToAscii {
            processed = processed.replacingOccurrences(of: String(knDigit), with: String(asciiDigit))
        }
        
        // 2. Normalize Currency (₹500 / Rs. 500 / Rs 500 -> 500 ರೂಪಾಯಿಗಳು)
        processed = normalizeCurrency(processed)
        
        // 3. Normalize Percentages (50% -> 50 ಪ್ರತಿಶತ)
        processed = normalizePercentages(processed)
        
        // 4. Normalize Ordinals (1ನೇ / 1st -> ಒಂದನೇ)
        processed = normalizeOrdinals(processed)
        
        // 5. Normalize standalone and embedded numbers to Kannada words
        processed = normalizeNumbers(processed)
        
        // 6. Normalize punctuation for natural pauses
        processed = normalizePunctuation(processed)
        
        return processed
    }
    
    // MARK: - Currency Normalization
    private static func normalizeCurrency(_ text: String) -> String {
        var result = text
        
        // Match ₹500 or ₹ 500
        let regexPatterns = [
            "(?:₹|Rs\\.?|ರೂ\\.?)\\s*(\\d+)(?:\\.(\\d{1,2}))?": { (amount: String, paise: String?) -> String in
                guard let num = Int64(amount) else { return amount }
                let amountText = numberToKannadaWords(num) + " ರೂಪಾಯಿ"
                if let p = paise, let paiseNum = Int64(p), paiseNum > 0 {
                    let paiseText = numberToKannadaWords(paiseNum) + " ಪೈಸೆ"
                    return amountText + " " + paiseText
                }
                return amountText + "ಗಳು"
            }
        ]
        
        for (pattern, formatter) in regexPatterns {
            if let regex = try? NSRegularExpression(pattern: pattern, options: [.caseInsensitive]) {
                let matches = regex.matches(in: result, options: [], range: NSRange(location: 0, length: result.utf16.count))
                for match in matches.reversed() {
                    guard let amountRange = Range(match.range(at: 1), in: result) else { continue }
                    let amountStr = String(result[amountRange])
                    
                    var paiseStr: String? = nil
                    if match.numberOfRanges > 2, match.range(at: 2).location != NSNotFound,
                       let pRange = Range(match.range(at: 2), in: result) {
                        paiseStr = String(result[pRange])
                    }
                    
                    let replacement = formatter(amountStr, paiseStr)
                    if let fullRange = Range(match.range, in: result) {
                        result.replaceSubrange(fullRange, with: replacement)
                    }
                }
            }
        }
        
        return result
    }
    
    // MARK: - Percentages
    private static func normalizePercentages(_ text: String) -> String {
        var result = text
        let pattern = "(\\d+)%"
        if let regex = try? NSRegularExpression(pattern: pattern, options: []) {
            let matches = regex.matches(in: result, options: [], range: NSRange(location: 0, length: result.utf16.count))
            for match in matches.reversed() {
                guard let numRange = Range(match.range(at: 1), in: result),
                      let num = Int64(result[numRange]),
                      let fullRange = Range(match.range, in: result) else { continue }
                
                let word = numberToKannadaWords(num) + " ಪ್ರತಿಶತ"
                result.replaceSubrange(fullRange, with: word)
            }
        }
        return result
    }
    
    // MARK: - Ordinals
    private static func normalizeOrdinals(_ text: String) -> String {
        var result = text
        let pattern = "(\\d+)\\s*(?:ನೇ|ನೆ|st|nd|rd|th)"
        if let regex = try? NSRegularExpression(pattern: pattern, options: [.caseInsensitive]) {
            let matches = regex.matches(in: result, options: [], range: NSRange(location: 0, length: result.utf16.count))
            for match in matches.reversed() {
                guard let numRange = Range(match.range(at: 1), in: result),
                      let num = Int64(result[numRange]),
                      let fullRange = Range(match.range, in: result) else { continue }
                
                let baseWord = numberToKannadaWords(num)
                let ordinalWord: String
                if baseWord.hasSuffix("ು") {
                    ordinalWord = String(baseWord.dropLast()) + "ನೇ"
                } else {
                    ordinalWord = baseWord + "ನೇ"
                }
                result.replaceSubrange(fullRange, with: ordinalWord)
            }
        }
        return result
    }
    
    // MARK: - Numbers to Words
    private static func normalizeNumbers(_ text: String) -> String {
        var result = text
        let pattern = "\\b\\d+\\b"
        if let regex = try? NSRegularExpression(pattern: pattern, options: []) {
            let matches = regex.matches(in: result, options: [], range: NSRange(location: 0, length: result.utf16.count))
            for match in matches.reversed() {
                guard let matchRange = Range(match.range, in: result),
                      let num = Int64(result[matchRange]) else { continue }
                let word = numberToKannadaWords(num)
                result.replaceSubrange(matchRange, with: word)
            }
        }
        return result
    }
    
    // MARK: - Punctuation Normalization
    private static func normalizePunctuation(_ text: String) -> String {
        var result = text
        // Replace Indian danda '।' with full stop
        result = result.replacingOccurrences(of: "।", with: ".")
        // Replace multiple dots with a single ellipsis
        result = result.replacingOccurrences(of: "\\.{2,}", with: "...", options: .regularExpression)
        // Clean whitespace
        result = result.replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression)
        return result.trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    // MARK: - Number to Kannada Words Algorithm
    public static func numberToKannadaWords(_ n: Int64) -> String {
        if n < 0 {
            return "ಋಣ " + numberToKannadaWords(-n)
        }
        if n == 0 {
            return onesWords[0] ?? "ಸೊನ್ನೆ"
        }
        
        return convertChunk(n)
    }
    
    private static func convertChunk(_ n: Int64) -> String {
        if n == 0 { return "" }
        
        // Under 10
        if n < 10 {
            return onesWords[Int(n)] ?? ""
        }
        
        // 10 to 19
        if n < 20 {
            return teensWords[Int(n)] ?? ""
        }
        
        // 20 to 99
        if n < 100 {
            let tens = Int(n / 10)
            let rem = Int(n % 10)
            if rem == 0 {
                return tensWordsBase[tens] ?? ""
            } else {
                let prefix = tensPrefix[tens] ?? ""
                let sandhi = sandhiOnes[rem] ?? (onesWords[rem] ?? "")
                return prefix + sandhi
            }
        }
        
        // 100 to 999
        if n < 1000 {
            let hundred = Int(n / 100)
            let rem = n % 100
            if rem == 0 {
                return hundredsExact[hundred] ?? ""
            } else {
                let prefix = hundredsPrefix[hundred] ?? ""
                return prefix + convertChunk(rem)
            }
        }
        
        // 1,000 to 99,999 (Thousands)
        if n < 100_000 {
            let thousands = n / 1000
            let rem = n % 1000
            if rem == 0 {
                if thousands == 1 {
                    return "ಒಂದು ಸಾವಿರ"
                }
                return convertChunk(thousands) + " ಸಾವಿರ"
            } else {
                if thousands == 1 {
                    return "ಒಂದು ಸಾವಿರದ " + convertChunk(rem)
                }
                return convertChunk(thousands) + " ಸಾವಿರದ " + convertChunk(rem)
            }
        }
        
        // 1,00,000 to 99,99,999 (Lakhs)
        if n < 10_000_000 {
            let lakhs = n / 100_000
            let rem = n % 100_000
            if rem == 0 {
                if lakhs == 1 {
                    return "ಒಂದು ಲಕ್ಷ"
                }
                return convertChunk(lakhs) + " ಲಕ್ಷ"
            } else {
                if lakhs == 1 {
                    return "ಒಂದು ಲಕ್ಷದ " + convertChunk(rem)
                }
                return convertChunk(lakhs) + " ಲಕ್ಷದ " + convertChunk(rem)
            }
        }
        
        // Crores
        let crores = n / 10_000_000
        let rem = n % 10_000_000
        if rem == 0 {
            if crores == 1 {
                return "ಒಂದು ಕೋಟಿ"
            }
            return convertChunk(crores) + " ಕೋಟಿ"
        } else {
            if crores == 1 {
                return "ಒಂದು ಕೋಟಿಯ " + convertChunk(rem)
            }
            return convertChunk(crores) + " ಕೋಟಿಯ " + convertChunk(rem)
        }
    }
}
