import Foundation
import AVFoundation
import Combine

/// Native audio recorder to capture reference voice samples for voice cloning
public final class AudioRecorder: NSObject, ObservableObject, AVAudioRecorderDelegate {
    
    @Published public var isRecording: Bool = false
    @Published public var recordedDuration: TimeInterval = 0
    @Published public var audioPower: Float = -160.0
    @Published public var recordedAudioURL: URL?
    
    private var audioRecorder: AVAudioRecorder?
    private var timer: Timer?
    
    public override init() {
        super.init()
    }
    
    public func startRecording() {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .allowBluetooth])
            try session.setActive(true)
            
            let tempDir = FileManager.default.temporaryDirectory
            let fileName = "voice_sample_\(UUID().uuidString).wav"
            let fileURL = tempDir.appendingPathComponent(fileName)
            
            let settings: [String: Any] = [
                AVFormatIDKey: Int(kAudioFormatLinearPCM),
                AVSampleRateKey: 24000.0,
                AVNumberOfChannelsKey: 1,
                AVLinearPCMBitDepthKey: 16,
                AVLinearPCMIsBigEndianKey: false,
                AVLinearPCMIsFloatKey: false
            ]
            
            audioRecorder = try AVAudioRecorder(url: fileURL, settings: settings)
            audioRecorder?.delegate = self
            audioRecorder?.isMeteringEnabled = true
            audioRecorder?.record()
            
            isRecording = true
            recordedDuration = 0
            recordedAudioURL = nil
            
            timer?.invalidate()
            timer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
                guard let self = self, let recorder = self.audioRecorder else { return }
                recorder.updateMeters()
                self.recordedDuration = recorder.currentTime
                self.audioPower = recorder.averagePower(forChannel: 0)
            }
            
        } catch {
            print("Failed to start recording: \(error.localizedDescription)")
        }
    }
    
    public func stopRecording() -> URL? {
        timer?.invalidate()
        timer = nil
        isRecording = false
        
        audioRecorder?.stop()
        let url = audioRecorder?.url
        self.recordedAudioURL = url
        audioRecorder = nil
        return url
    }
    
    public func cancelRecording() {
        timer?.invalidate()
        timer = nil
        isRecording = false
        audioRecorder?.stop()
        if let url = audioRecorder?.url {
            try? FileManager.default.removeItem(at: url)
        }
        audioRecorder = nil
        recordedAudioURL = nil
    }
}
