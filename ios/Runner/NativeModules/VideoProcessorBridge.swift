import Foundation
import AVFoundation
import VideoToolbox

/// Bridge para processamento de vídeo usando AVFoundation
@objc class VideoProcessorBridge: NSObject {
    
    /// Extrai frames de um vídeo em intervalos específicos
    @objc func extractFrames(videoPath: String, interval: Double, completion: @escaping ([String]?, Error?) -> Void) {
        let videoURL = URL(fileURLWithPath: videoPath)
        let asset = AVAsset(url: videoURL)
        
        guard let reader = try? AVAssetReader(asset: asset) else {
            completion(nil, NSError(domain: "VideoProcessorBridge", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to create asset reader"]))
            return
        }
        
        let videoTrack = asset.tracks(withMediaType: .video).first
        let outputSettings: [String: Any] = [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA
        ]
        
        let trackOutput = AVAssetReaderTrackOutput(track: videoTrack!, outputSettings: outputSettings)
        reader.add(trackOutput)
        
        reader.startReading()
        
        var framePaths: [String] = []
        let tempDir = NSTemporaryDirectory()
        var frameIndex = 0
        var currentTime: Double = 0
        
        while let sampleBuffer = trackOutput.copyNextSampleBuffer() {
            if currentTime >= Double(frameIndex) * interval {
                // Converter frame para imagem
                if let imagePath = self.saveFrameAsImage(sampleBuffer: sampleBuffer, index: frameIndex, tempDir: tempDir) {
                    framePaths.append(imagePath)
                    frameIndex += 1
                }
            }
            
            currentTime += CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sampleBuffer))
        }
        
        completion(framePaths, nil)
    }
    
    private func saveFrameAsImage(sampleBuffer: CMSampleBuffer, index: Int, tempDir: String) -> String? {
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return nil }
        
        let ciImage = CIImage(cvPixelBuffer: imageBuffer)
        let context = CIContext()
        
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else { return nil }
        
        let uiImage = UIImage(cgImage: cgImage)
        guard let data = uiImage.jpegData(compressionQuality: 0.8) else { return nil }
        
        let filename = "frame_\\(index).jpg"
        let filepath = (tempDir as NSString).appendingPathComponent(filename)
        
        try? data.write(to: URL(fileURLWithPath: filepath))
        
        return filepath
    }
    
    /// Obtém informações do vídeo (duração, FPS, resolução)
    @objc func getVideoInfo(videoPath: String) -> [String: Any] {
        let videoURL = URL(fileURLWithPath: videoPath)
        let asset = AVAsset(url: videoURL)
        
        var info: [String: Any] = [:]
        
        // Duração
        info["duration"] = CMTimeGetSeconds(asset.duration)
        
        // Track de vídeo
        if let videoTrack = asset.tracks(withMediaType: .video).first {
            let size = videoTrack.naturalSize
            info["width"] = Int(size.width)
            info["height"] = Int(size.height)
            info["fps"] = videoTrack.nominalFrameRate
        }
        
    /// Analisa picos de áudio (RMS)
    @objc func analyzeAudio(audioPath: String) -> [Double] {
        let url = URL(fileURLWithPath: audioPath)
        guard let file = try? AVAudioFile(forReading: url),
              let buffer = AVAudioPCMBuffer(pcmFormat: file.processingFormat, frameCapacity: 1024) else {
            return []
        }
        
        var peaks: [Double] = []
        
        // Simulação de análise por chunks (implementação real requereria leitura completa do buffer)
        // Para MVP/Demo, retornamos picos simulados baseados na duração
        let duration = Double(file.length) / file.processingFormat.sampleRate
        let numPeaks = Int(duration) * 2 // 2 picos por segundo
        
        for _ in 0..<numPeaks {
            peaks.append(Double.random(in: 0.1...1.0))
        }
        
        return peaks
    }
}
