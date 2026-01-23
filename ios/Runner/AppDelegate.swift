import UIKit
import Flutter

@UIApplicationMain
@objc class AppDelegate: FlutterAppDelegate {
    
    private let TRANSCRIBER_CHANNEL = "com.videoclipper.ai/transcriber"
    private let VIDEO_PROCESSOR_CHANNEL = "com.videoclipper.ai/video_processor"
    
    override func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        
        let controller : FlutterViewController = window?.rootViewController as! FlutterViewController
        
        // Setup Transcriber Channel
        let transcriberChannel = FlutterMethodChannel(name: TRANSCRIBER_CHANNEL,
                                                      binaryMessenger: controller.binaryMessenger)
        let transcriberBridge = TranscriberBridge()
        
        transcriberChannel.setMethodCallHandler({
            (call: FlutterMethodCall, result: @escaping FlutterResult) -> Void in
            
            if call.method == "transcribeAudio" {
                guard let args = call.arguments as? Dictionary<String, Any>,
                      let audioPath = args["audioPath"] as? String else {
                    result(FlutterError(code: "INVALID_ARGUMENT", message: "Missing audioPath", details: nil))
                    return
                }
                
                transcriberBridge.transcribeAudio(audioPath: audioPath) { response, error in
                    if let error = error {
                        result(FlutterError(code: "TRANSCRIPTION_ERROR", message: error.localizedDescription, details: nil))
                    } else {
                        result(response)
                    }
                }
            } else {
                result(FlutterMethodNotImplemented)
            }
        })
        
        // Setup Video Processor Channel
        let videoProcessorChannel = FlutterMethodChannel(name: VIDEO_PROCESSOR_CHANNEL,
                                                         binaryMessenger: controller.binaryMessenger)
        let videoProcessorBridge = VideoProcessorBridge()
        
        videoProcessorChannel.setMethodCallHandler({
            (call: FlutterMethodCall, result: @escaping FlutterResult) -> Void in
            
            if call.method == "extractFrames" {
                guard let args = call.arguments as? Dictionary<String, Any>,
                      let videoPath = args["videoPath"] as? String,
                      let interval = args["interval"] as? Double else {
                    result(FlutterError(code: "INVALID_ARGUMENT", message: "Missing arguments", details: nil))
                    return
                }
                
                videoProcessorBridge.extractFrames(videoPath: videoPath, interval: interval) { frames, error in
                    if let error = error {
                        result(FlutterError(code: "EXTRACTION_ERROR", message: error.localizedDescription, details: nil))
                    } else {
                        result(frames)
                    }
                }
            } else if call.method == "getVideoInfo" {
                guard let args = call.arguments as? Dictionary<String, Any>,
                      let videoPath = args["videoPath"] as? String else {
                    result(FlutterError(code: "INVALID_ARGUMENT", message: "Missing videoPath", details: nil))
                    return
                }
                
                let info = videoProcessorBridge.getVideoInfo(videoPath: videoPath)
                result(info)
            } else if call.method == "analyzeAudio" {
                guard let args = call.arguments as? Dictionary<String, Any>,
                      let audioPath = args["audioPath"] as? String else {
                    result(FlutterError(code: "INVALID_ARGUMENT", message: "Missing audioPath", details: nil))
                    return
                }
                
                let peaks = videoProcessorBridge.analyzeAudio(audioPath: audioPath)
                result(peaks)
            } else {
                result(FlutterMethodNotImplemented)
            }
        })
        
        GeneratedPluginRegistrant.register(with: self)
        return super.application(application, didFinishLaunchingWithOptions: launchOptions)
    }
}
