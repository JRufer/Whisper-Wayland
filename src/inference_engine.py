from faster_whisper import WhisperModel
import numpy as np
import threading
import queue
import time
import os

class InferenceEngine(threading.Thread):
    def __init__(self, config, audio_queue, text_queue):
        super().__init__(daemon=True)
        self.config = config
        self.audio_queue = audio_queue
        self.text_queue = text_queue
        self.running = True
        self.recording = False
        self.buffer = bytearray()
        
        # Load model with robust fallback
        self.model = self._load_model()
        print("Model loaded.")

    def _load_model(self):
        model_size = self.config.get("model_size", "base")
        device = self.config.get("device", "auto")
        compute_type = self.config.get("compute_type", "default")
        
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "whisper-wayland")
        
        try:
            print(f"Attempting to load Whisper model '{model_size}' on '{device}'...")
            model = WhisperModel(
                model_size, 
                device=device, 
                compute_type=compute_type,
                download_root=cache_dir
            )
            
            # CRITICAL: Verify the model actually works. 
            # Often faster-whisper succeeds at creation but fails during first transcription if CUDA is broken.
            print("Verifying model operationality...")
            dummy_audio = np.zeros(16000, dtype=np.float32)
            list(model.transcribe(dummy_audio, beam_size=1, vad_filter=True))
            return model
            
        except Exception as e:
            if device != "cpu" or "libcublas" in str(e) or "cuda" in str(e).lower():
                print(f"CUDA/GPU Error detected: {e}")
                print("Forcing CPU fallback mode...")
                # Update config so we don't try GPU again next time
                self.config.set("device", "cpu")
                self.config.set("compute_type", "int8")
                self.config.save()
                
                return WhisperModel(
                    model_size, 
                    device="cpu", 
                    compute_type="int8",
                    download_root=cache_dir
                )
            else:
                raise e

    def set_recording(self, recording):
        self.recording = recording
        if not recording:
            # Flush on stop
            self.process_buffer(incremental=False)
            self.buffer.clear()

    def process_buffer(self, incremental=True):
        if not self.buffer:
            return

        # Convert bytearray to float32 numpy array
        audio_data = np.frombuffer(self.buffer, dtype=np.int16).astype(np.float32) / 32768.0
        
        try:
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=1,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=self.config.get("min_silence_duration_ms", 500),
                    threshold=self.config.get("vad_threshold", 0.5)
                )
            )
            
            full_text = ""
            for segment in segments:
                full_text += segment.text
            
            if full_text.strip():
                self.text_queue.put(full_text.strip())

        except Exception as e:
            print(f"Inference error: {e}")
            if "libcublas" in str(e) or "cuda" in str(e).lower():
                print("Critical GPU error during transcription. Attempting to switch to CPU...")
                # This is harder to do mid-flight, but we can try to re-init
                self.model = self._load_model()

    def run(self):
        last_proc_time = time.time()
        while self.running:
            try:
                # Collect audio from queue
                try:
                    while True:
                        chunk = self.audio_queue.get_nowait()
                        if self.recording:
                            self.buffer.extend(chunk)
                except queue.Empty:
                    pass

                # Process every 1s if recording to avoid overhead
                if self.recording and time.time() - last_proc_time > 1.0:
                    self.process_buffer(incremental=True)
                    last_proc_time = time.time()
                
                time.sleep(0.05)
            except Exception as e:
                print(f"Error in inference loop: {e}")

    def stop(self):
        self.running = False
