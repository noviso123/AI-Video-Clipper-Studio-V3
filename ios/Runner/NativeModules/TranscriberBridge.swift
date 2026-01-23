import Foundation
import Speech

/// Bridge para Speech Framework nativo do iOS
@objc class TranscriberBridge: NSObject {
    
    private let speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "pt-BR"))
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    
    /// Transcreve arquivo de áudio
    @objc func transcribeAudio(audioPath: String, completion: @escaping ([String: Any]?, Error?) -> Void) {
        // Verificar permissões
        SFSpeechRecognizer.requestAuthorization { status in
            guard status == .authorized else {
                completion(nil, NSError(domain: "TranscriberBridge", code: 1, userInfo: [NSLocalizedDescriptionKey: "Speech recognition not authorized"]))
                return
            }
            
            self.performTranscription(audioPath: audioPath, completion: completion)
        }
    }
    
    private func performTranscription(audioPath: String, completion: @escaping ([String: Any]?, Error?) -> Void) {
        guard let speechRecognizer = speechRecognizer, speechRecognizer.isAvailable else {
            completion(nil, NSError(domain: "TranscriberBridge", code: 2, userInfo: [NSLocalizedDescriptionKey: "Speech recognizer not available"]))
            return
        }
        
        let audioURL = URL(fileURLWithPath: audioPath)
        let recognitionRequest = SFSpeechURLRecognitionRequest(url: audioURL)
        
        recognitionTask = speechRecognizer.recognitionTask(with: recognitionRequest) { result, error in
            if let error = error {
                completion(nil, error)
                return
            }
            
            guard let result = result else { return }
            
            if result.isFinal {
                // Converter para formato JSON
                var segments: [[String: Any]] = []
                
                for segment in result.bestTranscription.segments {
                    segments.append([
                        "text": segment.substring,
                        "startTime": segment.timestamp,
                        "duration": segment.duration,
                        "confidence": segment.confidence
                    ])
                }
                
                let response: [String: Any] = [
                    "text": result.bestTranscription.formattedString,
                    "segments": segments
                ]
                
                completion(response, nil)
            }
        }
    }
    
    /// Cancela transcrição em andamento
    @objc func cancelTranscription() {
        recognitionTask?.cancel()
        recognitionTask = nil
        recognitionRequest = nil
    }
}
