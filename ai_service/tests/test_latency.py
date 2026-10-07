"""
EASP Latency Benchmarking Harness - Phase 13 (T-P13-064 / T-P13-065)
Measures wall-clock latency per pipeline stage and end-to-end against the <= 3.0s target.
Matches methodology from EASP_fixed.ipynb Cell 11.
"""

import time
import numpy as np
from dlp.engine import DLPEngine
from social_engineering.detector import SocialEngineeringDetector
from voice_deepfake.detector import RawNet2VoiceDetector
from audio.processor import AudioProcessor
from audio.transcriber import SpeechTranscriber


def benchmark_latency(num_iterations: int = 10):
    print(f"=== Running EASP Latency Benchmark Harness ({num_iterations} iterations) ===")

    dlp = DLPEngine()
    processor = AudioProcessor(target_sr=16000)
    voice_detector = RawNet2VoiceDetector()
    transcriber = SpeechTranscriber(model_size="base")
    social_detector = SocialEngineeringDetector()

    # Synthetic 4-second audio waveform (64,000 samples at 16 kHz)
    t = np.linspace(0, 4.0, 64000)
    dummy_waveform = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

    sample_prompt = (
        "URGENT: This is executive IT support. Please verify your credentials: "
        "sk-proj-1234567890abcdef1234567890abcdef1234567890abcdef and approve the wire transfer."
    )

    stage_latencies = {
        "DLP_Scan": [],
        "Audio_Preprocessing": [],
        "RawNet2_Voice_Deepfake": [],
        "Whisper_Transcription": [],
        "mBERT_Social_Engineering": [],
        "End_to_End_Total": []
    }

    for _ in range(num_iterations):
        e2e_start = time.perf_counter()

        # 1. DLP Scan
        t0 = time.perf_counter()
        _ = dlp.scan_and_redact(sample_prompt)
        stage_latencies["DLP_Scan"].append((time.perf_counter() - t0) * 1000)

        # 2. Audio Preprocessing
        t0 = time.perf_counter()
        trimmed = processor.trim_silence(dummy_waveform)
        stage_latencies["Audio_Preprocessing"].append((time.perf_counter() - t0) * 1000)

        # 3. RawNet2
        t0 = time.perf_counter()
        _ = voice_detector.analyze_audio(trimmed, sample_rate=16000)
        stage_latencies["RawNet2_Voice_Deepfake"].append((time.perf_counter() - t0) * 1000)

        # 4. Faster-Whisper
        t0 = time.perf_counter()
        _ = transcriber.transcribe(trimmed)
        stage_latencies["Whisper_Transcription"].append((time.perf_counter() - t0) * 1000)

        # 5. mBERT Social Engineering
        t0 = time.perf_counter()
        _ = social_detector.analyze_text(sample_prompt)
        stage_latencies["mBERT_Social_Engineering"].append((time.perf_counter() - t0) * 1000)

        # End to End total
        e2e_duration = (time.perf_counter() - e2e_start) * 1000
        stage_latencies["End_to_End_Total"].append(e2e_duration)

    print("\n--- Measured Latency Results (Wall-Clock) ---")
    print(f"{'Pipeline Stage':<30} | {'Avg Latency (ms)':<18} | {'Min (ms)':<10} | {'Max (ms)':<10}")
    print("-" * 75)

    for stage, times in stage_latencies.items():
        avg_t = np.mean(times)
        min_t = np.min(times)
        max_t = np.max(times)
        print(f"{stage:<30} | {avg_t:>14.2f} ms | {min_t:>8.2f} ms | {max_t:>8.2f} ms")

    total_avg_s = np.mean(stage_latencies["End_to_End_Total"]) / 1000.0
    print("-" * 75)
    print(f"Total Pipeline Average Latency: {total_avg_s:.3f} s")
    target_s = 3.0
    status = "MET (PASS)" if total_avg_s <= target_s else "EXCEEDED (FAIL)"
    print(f"Graduation Requirement Target: <= {target_s}s -> Status: {status}\n")

    assert total_avg_s <= target_s, f"Latency target exceeded: {total_avg_s}s > {target_s}s"


if __name__ == "__main__":
    benchmark_latency(num_iterations=5)
