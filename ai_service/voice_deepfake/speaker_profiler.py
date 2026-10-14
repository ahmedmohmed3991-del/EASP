"""
Acoustic Voice & Gender Profiler - EASP Voice Security Engine
Extracts fundamental acoustic metrics:
  - Fundamental Frequency (F0 / Pitch in Hz) using robust YIN algorithm
  - Formant Resonant Frequencies (F1, F2, F3, F4 via Linear Predictive Coding LPC)
  - Mel-Frequency Cepstral Biometrics (MFCCs with Cepstral Mean Normalization)
  - Speaker Enrollment & 1-to-N Biometric Speaker Identification (كريم، الدكتور، أحمد، ...)
  - Gender Classification (Male / Female / High-Pitch / Unvoiced)
  - Executive Impersonation Detection (Acoustic Voiceprint Mismatch)
  - AI vs Real (Human) Authenticity Risk Evaluation (Pitch Dynamics, Robotic Flatness, Spectral Dispersion)
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import re
import json
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from scipy.linalg import solve_toeplitz


# Deep Latent Feature Extractor (Wav2Vec2-XLSR 1024-dim Biometric Latents)
_deep_model = None


def _get_deep_model():
    """Lazily loads local Wav2Vec2/XLSR deep representation model on CPU."""
    global _deep_model
    if _deep_model is None:
        try:
            import torch
            from transformers import Wav2Vec2Model
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir, "models", "wav2vec2_large_xlsr")
            if os.path.exists(model_path):
                _deep_model = Wav2Vec2Model.from_pretrained(model_path).to("cpu")
                _deep_model.eval()
        except Exception as e:
            print(f"[SpeakerProfiler] Could not load Wav2Vec2 deep model: {e}")
            _deep_model = None
    return _deep_model


def extract_canonical_speaker_name(filename_or_base: str) -> str:
    """
    Extracts a clean canonical speaker name without any numbers, indices, or file suffixes.
    - For Karim: All variations (e.g. 'كريم علاء', 'كريم 1', 'كريم علاء 2', 'كريم_علاء') become 'كريم'.
    - For all other speakers: Trailing numbers/indices are stripped (e.g. 'احمد محمد عطية 2' -> 'احمد محمد عطية').
    """
    if not filename_or_base:
        return "متحدث غير مسجل"
    base = os.path.splitext(filename_or_base)[0]
    base = base.strip("'\" \t\r\n")
    base = re.sub(r'[\s_]+', ' ', base)
    canonical = re.sub(r'[\s_\-\(\[\{]*\d+[\s_\-\)\]\}]*$', '', base).strip()
    tokens = canonical.split()
    clean_tokens = [t for t in tokens if not t.isdigit()]
    canonical = " ".join(clean_tokens).strip()
    if canonical in ["كريم", "كريم علاء"]:
        canonical = "كريم"
    return canonical if canonical else base.strip()


class SpeakerFrequencyProfiler:
    """
    Acoustic Frequency, Formants & Biometric Speaker Identification Engine.
    Extracts anatomical voice features (F0 pitch, F1-F4 formants, MFCC voiceprint, Wav2Vec2 latents)
    and performs 1-to-N speaker matching and impersonation detection.
    """

    def __init__(self, profiles_dir: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.profiles_dir = profiles_dir or os.path.join(base_dir, "speaker_profiles")
        os.makedirs(self.profiles_dir, exist_ok=True)
        
        # Default voices directory in project root
        project_root = os.path.dirname(base_dir)
        self.voices_dir = os.path.join(project_root, "voices")
        
        # Auto-sync on startup if voices folder has files
        try:
            self.sync_voices_folder()
        except Exception as e:
            print(f"[SpeakerProfiler] Initial voices sync notice: {e}")

    def extract_deep_embedding(self, audio: np.ndarray, sample_rate: int = 16000) -> Optional[np.ndarray]:
        """
        Extracts 1024-dimensional normalized speaker representation vector using Wav2Vec2/XLSR.
        """
        model = _get_deep_model()
        if model is None or audio is None or len(audio) < 1600:
            return None
        try:
            import torch
            from audio.processor import AudioProcessor
            proc = AudioProcessor(target_sr=sample_rate)
            trimmed = proc.trim_silence(audio)
            if len(trimmed) >= 4000:
                audio = trimmed
            audio_t = torch.tensor(audio, dtype=torch.float32).unsqueeze(0).to("cpu")
            with torch.no_grad():
                out = model(audio_t)
                emb = torch.mean(out.last_hidden_state, dim=1).squeeze(0).cpu().numpy()
                norm = float(np.linalg.norm(emb))
                return (emb / (norm + 1e-8)).astype(np.float32)
        except Exception as e:
            print(f"[SpeakerProfiler] extract_deep_embedding warning: {e}")
            return None

    def _extract_yin_pitch(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        w_len: int = 1024,
        hop: int = 256,
        min_f0: float = 65.0,
        max_f0: float = 450.0,
        thresh: float = 0.15
    ) -> Dict[str, Any]:
        """
        Extracts F0 Fundamental Pitch trajectory using the YIN algorithm.
        """
        if audio is None or len(audio) < w_len:
            return {
                "mean_hz": 0.0,
                "min_hz": 0.0,
                "max_hz": 0.0,
                "std_hz": 0.0,
                "voiced_ratio": 0.0,
                "voiced_frames": 0,
                "trajectory": []
            }

        audio = audio.astype(np.float32)
        min_lag = max(1, int(sample_rate / max_f0))   # ~35 samples at 16kHz
        max_lag = min(w_len - 1, int(sample_rate / min_f0))  # ~246 samples at 16kHz
        total_samples = len(audio)

        n_frames = (total_samples - w_len - max_lag) // hop
        if n_frames <= 0:
            return {
                "mean_hz": 0.0,
                "min_hz": 0.0,
                "max_hz": 0.0,
                "std_hz": 0.0,
                "voiced_ratio": 0.0,
                "voiced_frames": 0,
                "trajectory": []
            }

        pitches = []
        global_energy = float(np.mean(audio ** 2))
        silence_thresh = max(1e-5, global_energy * 0.05)

        for i in range(0, n_frames * hop, hop):
            w = audio[i : i + w_len]
            frame_energy = float(np.mean(w ** 2))
            if frame_energy < silence_thresh:
                continue

            # Step 1: Difference function d(tau)
            d = np.zeros(max_lag + 1, dtype=np.float32)
            for tau in range(1, max_lag + 1):
                diff = w - audio[i + tau : i + tau + w_len]
                d[tau] = np.dot(diff, diff)

            # Step 2: Cumulative mean normalized difference cmnd
            running_sum = np.cumsum(d[1:])
            tau_indices = np.arange(1, max_lag + 1, dtype=np.float32)
            cmnd = np.ones(max_lag + 1, dtype=np.float32)
            valid = running_sum > 1e-7
            cmnd[1:][valid] = d[1:][valid] / (running_sum[valid] / tau_indices[valid])

            # Step 3: Absolute thresholding
            tau_selected = -1
            for tau in range(min_lag, max_lag):
                if cmnd[tau] < thresh:
                    while tau + 1 < max_lag and cmnd[tau + 1] < cmnd[tau]:
                        tau += 1
                    tau_selected = tau
                    break

            # Step 4: Fallback to global minimum if below relaxed threshold (0.35)
            if tau_selected < 0:
                best_sub = np.argmin(cmnd[min_lag:max_lag]) + min_lag
                if cmnd[best_sub] < 0.35:
                    tau_selected = int(best_sub)

            # Step 5: Parabolic interpolation
            if tau_selected > 0:
                if min_lag < tau_selected < max_lag:
                    s0 = cmnd[tau_selected - 1]
                    s1 = cmnd[tau_selected]
                    s2 = cmnd[tau_selected + 1]
                    denom = 2.0 * (2.0 * s1 - s0 - s2)
                    delta = (s0 - s2) / denom if abs(denom) > 1e-6 else 0.0
                    refined_tau = tau_selected + delta
                else:
                    refined_tau = float(tau_selected)

                f0 = sample_rate / refined_tau
                if min_f0 <= f0 <= max_f0:
                    pitches.append(f0)

        if pitches:
            p_arr = np.array(pitches)
            if len(p_arr) > 15:
                low_p = np.percentile(p_arr, 2)
                high_p = np.percentile(p_arr, 98)
                p_arr = p_arr[(p_arr >= low_p) & (p_arr <= high_p)]

            step = max(1, len(p_arr) // 20)
            trajectory = [round(float(p), 1) for p in p_arr[::step][:20]]

            return {
                "mean_hz": round(float(np.mean(p_arr)), 1),
                "min_hz": round(float(np.percentile(p_arr, 5)), 1),
                "max_hz": round(float(np.percentile(p_arr, 95)), 1),
                "std_hz": round(float(np.std(p_arr)), 1),
                "voiced_ratio": round(float(len(pitches) / max(1, n_frames)), 3),
                "voiced_frames": len(pitches),
                "trajectory": trajectory
            }

        return {
            "mean_hz": 0.0,
            "min_hz": 0.0,
            "max_hz": 0.0,
            "std_hz": 0.0,
            "voiced_ratio": 0.0,
            "voiced_frames": 0,
            "trajectory": []
        }

    def _extract_formants_lpc(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        Extracts vocal tract resonant frequencies (Formants F1, F2, F3, F4)
        using Linear Predictive Coding (LPC) all-pole filter polynomial root finding.
        Formants are the anatomical resonant frequencies of the human vocal tract.
        """
        if audio is None or len(audio) < 1024:
            return {"f1_hz": 0.0, "f2_hz": 0.0, "f3_hz": 0.0, "f4_hz": 0.0, "dispersion_hz": 0.0}

        audio = audio.astype(np.float32)
        # 1. Pre-emphasis filter to boost high frequency resonances
        pre_emphasis = 0.97
        emphasized = np.append(audio[0], audio[1:] - pre_emphasis * audio[:-1])

        frame_len = int(0.030 * sample_rate)  # 30ms window
        hop_len = int(0.015 * sample_rate)    # 15ms hop
        # Limit total frames to 200 for lightning-fast real-time response
        max_frames = 200
        lpc_order = int(2 + sample_rate / 1000)  # 18 coefficients for 16kHz
        hamming = np.hamming(frame_len)

        global_energy = np.mean(emphasized ** 2)
        min_energy = max(1e-5, global_energy * 0.06)

        f1_list, f2_list, f3_list, f4_list = [], [], [], []
        
        # Subsample frames if audio is very long
        total_len = len(emphasized) - frame_len
        step = hop_len
        if (total_len // hop_len) > max_frames:
            step = total_len // max_frames

        for i in range(0, total_len, step):
            frame = emphasized[i : i + frame_len] * hamming
            if np.mean(frame ** 2) < min_energy:
                continue

            # Autocorrelation
            r = np.correlate(frame, frame, mode='full')
            r = r[len(frame) - 1 : len(frame) - 1 + lpc_order + 1]
            if r[0] < 1e-6:
                continue

            try:
                # Solve Yule-Walker via Levinson-Durbin
                a = solve_toeplitz((r[:-1], r[:-1]), -r[1:])
                lpc_poly = np.concatenate(([1.0], a))

                roots = np.roots(lpc_poly)
                roots = [rt for rt in roots if np.imag(rt) >= 0.01 and np.abs(rt) < 1.0]

                formants = []
                for r_val in roots:
                    freq = np.arctan2(np.imag(r_val), np.real(r_val)) * (sample_rate / (2.0 * np.pi))
                    bw = -0.5 * (sample_rate / (2.0 * np.pi)) * np.log(np.abs(r_val))
                    # Resonant vocal formants fall between 250 Hz and 4200 Hz with moderate bandwidth
                    if 250.0 <= freq <= 4200.0 and bw < 420.0:
                        formants.append(freq)

                formants.sort()
                if len(formants) >= 1: f1_list.append(formants[0])
                if len(formants) >= 2: f2_list.append(formants[1])
                if len(formants) >= 3: f3_list.append(formants[2])
                if len(formants) >= 4: f4_list.append(formants[3])
            except Exception:
                continue

        def get_trimmed_mean(vals):
            if not vals: return 0.0
            arr = np.array(vals)
            if len(arr) > 10:
                low, high = np.percentile(arr, 10), np.percentile(arr, 90)
                arr = arr[(arr >= low) & (arr <= high)]
            return round(float(np.mean(arr)), 1) if len(arr) > 0 else 0.0

        f1 = get_trimmed_mean(f1_list)
        f2 = get_trimmed_mean(f2_list)
        f3 = get_trimmed_mean(f3_list)
        f4 = get_trimmed_mean(f4_list)
        dispersion = round((f3 - f1) / 2.0, 1) if (f3 > 0 and f1 > 0) else 0.0

        return {
            "f1_hz": f1,
            "f2_hz": f2,
            "f3_hz": f3,
            "f4_hz": f4,
            "dispersion_hz": dispersion,
            "frames_analyzed": len(f1_list)
        }

    def _extract_mfcc_vector(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        n_mfcc: int = 13
    ) -> np.ndarray:
        """
        Extracts 26-dimensional Mel-Frequency Cepstral Coefficients (MFCC) feature vector
        with Cepstral Mean Normalization (CMN) for robust acoustic speaker identification.
        """
        try:
            import torch
            import torchaudio
            audio_t = torch.tensor(audio, dtype=torch.float32).unsqueeze(0)
            transform = torchaudio.transforms.MFCC(
                sample_rate=sample_rate,
                n_mfcc=n_mfcc,
                melkwargs={"n_fft": 512, "hop_length": 256, "n_mels": 40}
            )
            mfcc_mat = transform(audio_t).squeeze(0).numpy() # (13, n_frames)

            # Cepstral Mean Normalization (CMN) to remove channel/mic bias
            mean_mat = np.mean(mfcc_mat, axis=1, keepdims=True)
            std_mat = np.std(mfcc_mat, axis=1, keepdims=True) + 1e-6
            cmn_mfcc = (mfcc_mat - mean_mat) / std_mat

            # Use mean and std across frames (skip energy coefficient C0)
            v_mean = np.mean(cmn_mfcc[1:], axis=1) # 12 dimensions
            v_std = np.std(cmn_mfcc[1:], axis=1)   # 12 dimensions
            v_raw_mean = np.mean(mfcc_mat[1:3], axis=1) # 2 dimensions (spectral tilt)
            
            vec = np.concatenate([v_mean, v_std, v_raw_mean])
            norm = np.linalg.norm(vec)
            return (vec / (norm + 1e-8)).astype(np.float32)
        except Exception:
            return np.zeros(26, dtype=np.float32)

    def extract_acoustic_features(self, audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """Extracts pitch, formants, spectral centroid, roll-off, zero-crossing rate and MFCC voiceprint."""
        if audio is None or len(audio) == 0:
            return {
                "success": False,
                "error": "Empty audio provided",
                "pitch": {"mean_hz": 0.0, "min_hz": 0.0, "max_hz": 0.0, "std_hz": 0.0, "voiced_ratio": 0.0},
                "formants": {"f1_hz": 0.0, "f2_hz": 0.0, "f3_hz": 0.0, "f4_hz": 0.0, "dispersion_hz": 0.0},
                "spectral": {"centroid_hz": 0.0, "rolloff_hz": 0.0}
            }

        audio = audio.astype(np.float32)
        total_samples = len(audio)

        pitch_metrics = self._extract_yin_pitch(audio, sample_rate=sample_rate)
        formant_metrics = self._extract_formants_lpc(audio, sample_rate=sample_rate)
        mfcc_vector = self._extract_mfcc_vector(audio, sample_rate=sample_rate)

        # Spectral Centroid and Roll-off
        n_fft = 1024
        hop_fft = 512
        centroids = []
        rolloffs = []
        freqs = np.fft.rfftfreq(n_fft, 1.0 / sample_rate)

        for i in range(0, total_samples - n_fft, hop_fft):
            window = audio[i : i + n_fft] * np.hanning(n_fft)
            mag = np.abs(np.fft.rfft(window))
            mag_sum = np.sum(mag)
            if mag_sum > 1e-5:
                c = np.sum(freqs * mag) / mag_sum
                centroids.append(c)
                cum = np.cumsum(mag)
                idx = np.where(cum >= 0.85 * mag_sum)[0]
                if len(idx) > 0:
                    rolloffs.append(freqs[idx[0]])

        spectral_metrics = {
            "centroid_hz": round(float(np.mean(centroids)), 1) if centroids else 0.0,
            "rolloff_hz": round(float(np.mean(rolloffs)), 1) if rolloffs else 0.0
        }

        zero_crossings = float(np.mean(np.diff(np.signbit(audio).astype(int)) != 0)) if total_samples > 1 else 0.0

        # Neural Vocoder Artifacts
        diff_audio = np.diff(audio)
        hf_energy = float(np.mean(diff_audio ** 2) / (np.mean(audio ** 2) + 1e-8)) if total_samples > 1 else 0.0
        
        spec_init = np.abs(np.fft.rfft(audio[:min(total_samples, 8000)]))
        spec_flatness = float(np.exp(np.mean(np.log(spec_init + 1e-8))) / (np.mean(spec_init) + 1e-8)) if len(spec_init) > 0 else 0.0

        return {
            "success": True,
            "sample_rate": sample_rate,
            "duration_seconds": round(total_samples / sample_rate, 2),
            "pitch": pitch_metrics,
            "formants": formant_metrics,
            "mfcc_vector": mfcc_vector.tolist(),
            "spectral": spectral_metrics,
            "zero_crossing_rate": round(zero_crossings, 4),
            "high_freq_energy_ratio": round(hf_energy, 4),
            "spectral_flatness": round(spec_flatness, 4)
        }

    def enroll_speaker(
        self,
        profile_id: str,
        name: str,
        title: str,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        Enrolls a speaker's acoustic baseline frequency voiceprint and saves it to disk.
        """
        clean_id = re.sub(r'[^a-zA-Z0-9_\u0600-\u06FF-]', '_', profile_id.strip()).lower()
        if not clean_id:
            clean_id = "speaker_" + str(len(self.list_profiles()) + 1)

        features = self.extract_acoustic_features(audio, sample_rate)
        if not features.get("success"):
            return {"success": False, "error": features.get("error", "Could not extract features")}

        pitch = features["pitch"]
        formants = features["formants"]
        spectral = features["spectral"]
        
        f0_mean = pitch["mean_hz"]
        gender = "Male" if (0 < f0_mean < 165.0) else ("Female" if f0_mean >= 165.0 else "Unknown")
        gender_ar = "ذكر" if gender == "Male" else ("أنثى" if gender == "Female" else "غير محدد")

        profile_data = {
            "profile_id": clean_id,
            "name": name.strip(),
            "title": title.strip() or f"{name} Acoustic Baseline",
            "gender": gender,
            "gender_ar": gender_ar,
            "enrolled_duration_seconds": features["duration_seconds"],
            "acoustic_profile": {
                "f0_pitch_mean_hz": pitch["mean_hz"],
                "f0_pitch_min_hz": pitch["min_hz"],
                "f0_pitch_max_hz": pitch["max_hz"],
                "f0_pitch_std_hz": pitch["std_hz"],
                "formant_f1_hz": formants["f1_hz"],
                "formant_f2_hz": formants["f2_hz"],
                "formant_f3_hz": formants["f3_hz"],
                "formant_f4_hz": formants["f4_hz"],
                "formant_dispersion_hz": formants["dispersion_hz"],
                "spectral_centroid_hz": spectral["centroid_hz"],
                "spectral_rolloff_hz": spectral["rolloff_hz"],
                "mfcc_vector": features["mfcc_vector"]
            }
        }

        file_path = os.path.join(self.profiles_dir, f"{clean_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "message": f"Successfully enrolled speaker '{name}' ({clean_id})",
            "profile": profile_data
        }

    # Alias for backward compatibility
    enroll_profile = enroll_speaker

    def sync_voices_folder(self, voices_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scans the `voices/` directory, automatically grouping and training audio samples by canonical person.
        - Unifies all samples of the same speaker (e.g. 'كريم علاء.ogg' + 'كريم علاء 2.ogg' -> 'كريم').
        - Purges stale non-canonical profile files (e.g. *_2.json, *_3.json, etc.).
        - Generates rich multi-exemplar profiles with Deep Embeddings, MFCC vectors, Pitch distributions, and Formants.
        """
        target_dir = voices_dir or self.voices_dir
        if not os.path.exists(target_dir):
            return []

        from audio.processor import AudioProcessor
        processor = AudioProcessor(target_sr=16000)
        valid_exts = {".wav", ".mp3", ".ogg", ".mp4", ".m4a", ".flac", ".aac"}

        # 1. Group files by canonical name
        groups: Dict[str, List[str]] = {}
        for fname in sorted(os.listdir(target_dir)):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in valid_exts:
                continue
            canonical_name = extract_canonical_speaker_name(fname)
            if canonical_name not in groups:
                groups[canonical_name] = []
            groups[canonical_name].append(fname)

        if not groups:
            return []

        # 2. Clean up stale profile files in profiles_dir that have numbers or don't match canonical IDs
        valid_canonical_ids = set()
        for spk in groups.keys():
            cid = re.sub(r'[^a-zA-Z0-9_\u0600-\u06FF-]', '_', spk.strip()).lower()
            valid_canonical_ids.add(f"{cid}.json")

        if os.path.exists(self.profiles_dir):
            for existing_pf in os.listdir(self.profiles_dir):
                if not existing_pf.endswith(".json"):
                    continue
                # If file has digits/sample indices like _2.json, _3.json, or is outdated non-canonical, remove it
                if re.search(r'_\d+\.json$', existing_pf) or (existing_pf not in valid_canonical_ids and existing_pf not in ["male.json", "female.json"]):
                    try:
                        os.remove(os.path.join(self.profiles_dir, existing_pf))
                        print(f"[SpeakerProfiler] Removed stale non-canonical profile: {existing_pf}")
                    except Exception as err:
                        print(f"[SpeakerProfiler] Could not remove {existing_pf}: {err}")

        enrolled = []

        # 3. Enroll each canonical speaker with all their audio samples
        for spk, fnames in groups.items():
            f0_list, f1_list, f2_list, f3_list, f4_list = [], [], [], [], []
            mfcc_list, deep_list = [], []
            total_duration = 0.0
            centroid_list = []
            rolloff_list = []

            for fname in fnames:
                audio_fp = os.path.join(target_dir, fname)
                try:
                    with open(audio_fp, "rb") as bf:
                        raw_bytes = bf.read()
                    audio_data = processor.load_wav_bytes(raw_bytes)
                    audio_trimmed = processor.trim_silence(audio_data)

                    feat = self.extract_acoustic_features(audio_trimmed, sample_rate=16000)
                    if not feat.get("success"):
                        continue

                    total_duration += feat.get("duration_seconds", 0.0)
                    pitch = feat["pitch"]
                    if pitch["mean_hz"] > 0:
                        f0_list.append(pitch["mean_hz"])

                    formants = feat["formants"]
                    if formants["f1_hz"] > 0: f1_list.append(formants["f1_hz"])
                    if formants["f2_hz"] > 0: f2_list.append(formants["f2_hz"])
                    if formants["f3_hz"] > 0: f3_list.append(formants["f3_hz"])
                    if formants["f4_hz"] > 0: f4_list.append(formants["f4_hz"])

                    spectral = feat["spectral"]
                    centroid_list.append(spectral["centroid_hz"])
                    rolloff_list.append(spectral["rolloff_hz"])

                    mfcc_vec = np.array(feat["mfcc_vector"], dtype=np.float32)
                    if len(mfcc_vec) > 0:
                        mfcc_list.append(mfcc_vec)

                    deep_vec = self.extract_deep_embedding(audio_trimmed, sample_rate=16000)
                    if deep_vec is not None:
                        deep_list.append(deep_vec)

                except Exception as err:
                    print(f"[SpeakerProfiler] Error processing {fname} for {spk}: {err}")

            if not mfcc_list:
                continue

            # Centroids
            c_mfcc = np.mean(mfcc_list, axis=0)
            c_mfcc = (c_mfcc / (np.linalg.norm(c_mfcc) + 1e-8)).astype(np.float32)

            c_deep = None
            if deep_list:
                c_deep = np.mean(deep_list, axis=0)
                c_deep = (c_deep / (np.linalg.norm(c_deep) + 1e-8)).astype(np.float32)

            f0_mean = round(float(np.mean(f0_list)), 1) if f0_list else 125.0
            f0_min = round(float(np.min(f0_list)), 1) if f0_list else 85.0
            f0_max = round(float(np.max(f0_list)), 1) if f0_list else 165.0
            f0_std = round(float(np.std(f0_list)), 1) if len(f0_list) > 1 else 6.0

            f1_mean = round(float(np.mean(f1_list)), 1) if f1_list else 0.0
            f2_mean = round(float(np.mean(f2_list)), 1) if f2_list else 0.0
            f3_mean = round(float(np.mean(f3_list)), 1) if f3_list else 0.0
            f4_mean = round(float(np.mean(f4_list)), 1) if f4_list else 0.0

            gender = "Male" if (0 < f0_mean < 165.0) else ("Female" if f0_mean >= 165.0 else "Unknown")
            gender_ar = "ذكر" if gender == "Male" else ("أنثى" if gender == "Female" else "غير محدد")

            clean_id = re.sub(r'[^a-zA-Z0-9_\u0600-\u06FF-]', '_', spk.strip()).lower()

            profile_data = {
                "profile_id": clean_id,
                "name": spk,
                "title": f"الملف البيومتري الصوتي: {spk}",
                "gender": gender,
                "gender_ar": gender_ar,
                "enrolled_duration_seconds": round(total_duration, 2),
                "n_samples": len(fnames),
                "sample_files": fnames,
                "acoustic_profile": {
                    "f0_pitch_mean_hz": f0_mean,
                    "f0_pitch_min_hz": f0_min,
                    "f0_pitch_max_hz": f0_max,
                    "f0_pitch_std_hz": f0_std,
                    "formant_f1_hz": f1_mean,
                    "formant_f2_hz": f2_mean,
                    "formant_f3_hz": f3_mean,
                    "formant_f4_hz": f4_mean,
                    "formant_dispersion_hz": round(f3_mean - f1_mean, 1) if (f3_mean > 0 and f1_mean > 0) else 0.0,
                    "spectral_centroid_hz": round(float(np.mean(centroid_list)), 1) if centroid_list else 0.0,
                    "spectral_rolloff_hz": round(float(np.mean(rolloff_list)), 1) if rolloff_list else 0.0,
                    "mfcc_vector": c_mfcc.tolist(),
                    "s_f0s": f0_list,
                    "s_mfccs": [m.tolist() for m in mfcc_list],
                    "deep_vector": c_deep.tolist() if c_deep is not None else [],
                    "s_deeps": [d.tolist() for d in deep_list] if deep_list else []
                }
            }

            file_path = os.path.join(self.profiles_dir, f"{clean_id}.json")
            with open(file_path, "w", encoding="utf-8") as pf:
                json.dump(profile_data, pf, ensure_ascii=False, indent=2)

            enrolled.append(profile_data)
            print(f"[SpeakerProfiler] Successfully trained unified canonical profile '{spk}' ({len(fnames)} audio samples)")

        return enrolled

    def identify_speaker(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        1-to-N Speaker Identification:
        Compares input voiceprint against all enrolled speaker profiles in the database.
        Uses Nearest-Exemplar dominant matching across Deep Latents, MFCCs, F0 Pitch, and Formants.
        Returns the top matched candidate with clean canonical name (no numbers or indices).
        """
        features = self.extract_acoustic_features(audio, sample_rate)
        if not features.get("success"):
            return {
                "identified": False,
                "speaker_name": "Unknown Speaker (صوت غير معروف)",
                "match_percentage": 0.0,
                "status": "ERROR",
                "explanation": "Could not extract acoustic features from audio."
            }

        pitch = features["pitch"]
        formants = features["formants"]
        in_f0 = pitch["mean_hz"]
        in_f1 = formants["f1_hz"]
        in_f2 = formants["f2_hz"]
        in_f3 = formants["f3_hz"]
        in_mfcc = np.array(features["mfcc_vector"], dtype=np.float32)
        in_deep = self.extract_deep_embedding(audio, sample_rate)

        # Load all enrolled profiles
        candidates = []
        if os.path.exists(self.profiles_dir):
            for pf_name in os.listdir(self.profiles_dir):
                if not pf_name.endswith(".json"):
                    continue
                try:
                    with open(os.path.join(self.profiles_dir, pf_name), "r", encoding="utf-8") as f:
                        prof = json.load(f)

                    raw_name = prof.get("name", "")
                    clean_name = extract_canonical_speaker_name(raw_name)

                    ac = prof.get("acoustic_profile", {})
                    ref_f0 = ac.get("f0_pitch_mean_hz", 0.0)
                    ref_f1 = ac.get("formant_f1_hz", 0.0)
                    ref_f2 = ac.get("formant_f2_hz", 0.0)
                    ref_f3 = ac.get("formant_f3_hz", 0.0)

                    s_f0s = ac.get("s_f0s", [])
                    if not s_f0s and ref_f0 > 0:
                        s_f0s = [ref_f0]

                    # 1. Deep Latent Embeddings (Nearest Exemplar Dominant)
                    deep_score = None
                    s_deeps = [np.array(d, dtype=np.float32) for d in ac.get("s_deeps", []) if len(d) > 0]
                    c_deep = np.array(ac.get("deep_vector", []), dtype=np.float32)
                    if in_deep is not None and len(in_deep) > 0 and s_deeps:
                        c_sim = float(np.dot(in_deep, c_deep) / (np.linalg.norm(in_deep) * np.linalg.norm(c_deep) + 1e-8)) if len(c_deep) > 0 else 0.0
                        nn_sim = max([float(np.dot(in_deep, s) / (np.linalg.norm(in_deep) * np.linalg.norm(s) + 1e-8)) for s in s_deeps])
                        deep_sim = 0.15 * c_sim + 0.85 * nn_sim
                        deep_score = max(0.0, min(1.0, (deep_sim - 0.96) / 0.04))

                    # 2. MFCCs (Nearest Exemplar Dominant)
                    s_mfccs = [np.array(m, dtype=np.float32) for m in ac.get("s_mfccs", []) if len(m) > 0]
                    c_mfcc = np.array(ac.get("mfcc_vector", []), dtype=np.float32)
                    if not s_mfccs and len(c_mfcc) > 0:
                        s_mfccs = [c_mfcc]

                    mfcc_score = 0.5
                    cos_sim = 0.0
                    if len(in_mfcc) > 0 and s_mfccs:
                        c_mfcc_sim = float(np.dot(in_mfcc, c_mfcc) / (np.linalg.norm(in_mfcc) * np.linalg.norm(c_mfcc) + 1e-8)) if len(c_mfcc) > 0 else 0.0
                        nn_mfcc_sim = max([float(np.dot(in_mfcc, s) / (np.linalg.norm(in_mfcc) * np.linalg.norm(s) + 1e-8)) for s in s_mfccs])
                        mfcc_sim = 0.20 * c_mfcc_sim + 0.80 * nn_mfcc_sim
                        cos_sim = nn_mfcc_sim
                        mfcc_score = max(0.0, min(1.0, (mfcc_sim - 0.75) / 0.25))

                    # 3. Nearest Pitch Proximity
                    if in_f0 > 0 and s_f0s:
                        valid_f0s = [sf for sf in s_f0s if sf > 0]
                        min_p_diff = min([abs(in_f0 - sf) for sf in valid_f0s]) if valid_f0s else 50.0
                        pitch_score = max(0.0, 1.0 - (min_p_diff / 30.0))
                        pitch_diff = min_p_diff
                    else:
                        pitch_diff = 50.0
                        pitch_score = 0.5

                    # 4. Formant Proximity (F1, F2, F3)
                    f_diff = 0.0
                    n_f = 0
                    if in_f1 > 0 and ref_f1 > 0:
                        f_diff += min(1.0, abs(in_f1 - ref_f1) / 140.0)
                        n_f += 1
                    if in_f2 > 0 and ref_f2 > 0:
                        f_diff += min(1.0, abs(in_f2 - ref_f2) / 250.0)
                        n_f += 1
                    if in_f3 > 0 and ref_f3 > 0:
                        f_diff += min(1.0, abs(in_f3 - ref_f3) / 280.0)
                        n_f += 1
                    formant_score = max(0.0, 1.0 - (f_diff / n_f)) if n_f > 0 else 0.5

                    # Combined Weighted Biometric Match Score
                    if deep_score is not None:
                        combined = 0.55 * deep_score + 0.20 * mfcc_score + 0.15 * pitch_score + 0.10 * formant_score
                    else:
                        combined = 0.50 * mfcc_score + 0.30 * pitch_score + 0.20 * formant_score

                    match_pct = round(max(5.0, min(99.9, combined * 100.0)), 1)

                    candidates.append({
                        "profile_id": prof.get("profile_id"),
                        "name": clean_name,
                        "title": prof.get("title", f"الملف البيومتري الصوتي: {clean_name}"),
                        "gender": prof.get("gender"),
                        "gender_ar": prof.get("gender_ar"),
                        "match_percentage": match_pct,
                        "mfcc_similarity_pct": round(cos_sim * 100.0, 1),
                        "pitch_diff_hz": round(pitch_diff, 1),
                        "ref_f0_hz": ref_f0,
                        "ref_formants": {"f1": ref_f1, "f2": ref_f2, "f3": ref_f3}
                    })
                except Exception as err:
                    print(f"[SpeakerProfiler] Candidate parse error for {pf_name}: {err}")
                    continue

        if not candidates:
            return {
                "identified": False,
                "speaker_name": "No enrolled profiles in database",
                "match_percentage": 0.0,
                "status": "NO_PROFILES",
                "candidates": []
            }

        candidates.sort(key=lambda x: x["match_percentage"], reverse=True)
        top = candidates[0]

        # Decision threshold: 65% match indicates enrolled speaker
        is_matched = top["match_percentage"] >= 65.0
        clean_top_name = extract_canonical_speaker_name(top["name"])
        speaker_name = clean_top_name if is_matched else "متحدث غير مسجل (Unknown Speaker)"
        status = "MATCHED" if is_matched else "UNREGISTERED"

        explanation = (
            f"🎯 Identified Speaker: '{clean_top_name}' with {top['match_percentage']}% voiceprint match. "
            f"Pitch Δ: {top['pitch_diff_hz']} Hz (Caller: {in_f0} Hz, Enrolled: {top['ref_f0_hz']} Hz)."
            if is_matched else
            f"⚠️ Caller does not closely match any enrolled profile (Highest match: {clean_top_name} at {top['match_percentage']}%)."
        )

        return {
            "identified": is_matched,
            "speaker_name": speaker_name,
            "match_percentage": top["match_percentage"],
            "status": status,
            "top_match": top,
            "all_candidates": candidates[:5],
            "explanation": explanation,
            "caller_measurements": {
                "f0_hz": in_f0,
                "f1_hz": in_f1,
                "f2_hz": in_f2,
                "f3_hz": in_f3
            }
        }

    def classify_voice(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        rawnet2_spoof_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Classifies voice gender and evaluates AI vs Real (Human) acoustic risk.
        """
        features = self.extract_acoustic_features(audio, sample_rate)
        if not features.get("success"):
            return {
                "success": False,
                "gender": "Unknown",
                "gender_ar": "غير محدد",
                "gender_confidence": 0.0,
                "expected_pitch_range_hz": [0.0, 0.0],
                "ai_risk_score": 0.5,
                "human_score": 0.5,
                "is_ai_generated": False,
                "authenticity_label": "UNAVAILABLE",
                "authenticity_label_ar": "غير متاح",
                "pitch_mean_hz": 0.0,
                "pitch_range_hz": [0.0, 0.0],
                "pitch_std_hz": 0.0,
                "formants": {"f1_hz": 520.0, "f2_hz": 1480.0, "f3_hz": 2650.0, "f4_hz": 3500.0, "dispersion_hz": 1065.0},
                "spectral_centroid_hz": 0.0,
                "zero_crossing_rate": 0.0,
                "high_freq_energy_ratio": 0.0,
                "spectral_flatness": 0.0,
                "voiced_ratio": 0.0,
                "pitch_contour": [],
                "diagnostics": ["Could not extract acoustic features from audio."],
                "explanation": "Could not extract acoustic features from audio."
            }

        pitch = features["pitch"]
        formants = features["formants"]
        spectral = features["spectral"]
        f0_mean = pitch["mean_hz"]
        f0_min = pitch["min_hz"]
        f0_max = pitch["max_hz"]
        f0_std = pitch["std_hz"]
        voiced_frames = pitch["voiced_frames"]
        centroid = spectral["centroid_hz"]
        zcr = features["zero_crossing_rate"]
        hf_energy = features.get("high_freq_energy_ratio", 0.0)
        spec_flatness = features.get("spectral_flatness", 0.0)

        # 1. Gender Classification (Male vs Female)
        if f0_mean == 0.0 or voiced_frames < 3:
            gender = "Unvoiced / Inaudible"
            gender_ar = "صوت غير مسموع / همس"
            gender_confidence = 0.0
            expected_range = [0.0, 0.0]
        elif f0_mean < 165.0:
            gender = "Male"
            gender_ar = "صوت ذكوري (Male)"
            conf = min(99.0, max(75.0, 100.0 - abs(f0_mean - 125.0) * 0.4))
            gender_confidence = round(conf, 1)
            expected_range = [85.0, 165.0]
        elif f0_mean <= 275.0:
            gender = "Female"
            gender_ar = "صوت أنثوي (Female)"
            conf = min(99.0, max(75.0, 100.0 - abs(f0_mean - 215.0) * 0.4))
            gender_confidence = round(conf, 1)
            expected_range = [165.0, 260.0]
        else:
            gender = "High-Pitch / Synthetic Tone"
            gender_ar = "تردد صوتي مرتفع / نغمة اصطناعية"
            gender_confidence = 88.0
            expected_range = [275.0, 450.0]

        # 2. AI vs Real Risk Evaluation
        ai_risk_penalty = 0.08
        diagnostics = []

        if voiced_frames >= 10:
            if f0_std < 1.5:
                ai_risk_penalty += 0.50
                diagnostics.append("Extreme robotic pitch flatness (std < 1.5 Hz); typical of synthetic vocoders.")
            elif f0_std < 3.0:
                ai_risk_penalty += 0.25
                diagnostics.append("Low pitch dynamic variation (std < 3.0 Hz); suggests synthetic voice synthesis.")
            elif f0_std >= 7.0 and hf_energy < 0.08 and zcr < 0.10:
                ai_risk_penalty -= 0.05
                diagnostics.append(f"Natural human vocal intonation observed (pitch std: {f0_std} Hz).")
            else:
                diagnostics.append(f"Expressive vocal dynamics observed (pitch std: {f0_std} Hz).")
        else:
            diagnostics.append("Brief vocal sample or sparse voicing detected.")

        if f0_mean > 280.0:
            ai_risk_penalty += 0.25
            diagnostics.append(f"High-frequency pitch ({f0_mean} Hz) beyond natural sustained speech.")

        # Vocoder Check
        is_robotic_pitch = (f0_std < 3.5) if voiced_frames >= 10 else False
        if is_robotic_pitch:
            if zcr >= 0.22 and hf_energy >= 0.20:
                ai_risk_penalty += 0.50
                diagnostics.append(f"Severe vocoder upsampling artifacts and robotic flatness detected (ZCR={zcr:.3f}, HF Energy={hf_energy:.3f}).")
            elif zcr >= 0.17 and hf_energy >= 0.15:
                ai_risk_penalty += 0.30
                diagnostics.append(f"Elevated vocoder derivative energy ({hf_energy:.3f}) with low pitch variation.")
        elif zcr >= 0.24 and hf_energy >= 0.22:
            ai_risk_penalty += 0.15
            diagnostics.append(f"High-frequency acoustic energy noted ({hf_energy:.3f}); verified against vocal pitch dynamics.")

        # Cross-reference with neural detector
        if rawnet2_spoof_score is not None:
            if rawnet2_spoof_score >= 0.50:
                ai_risk_penalty = max(ai_risk_penalty, round(rawnet2_spoof_score, 3))
                diagnostics.append(
                    f"Neural deepfake detector flagged synthetic audio indicators ({round(rawnet2_spoof_score * 100, 1)}% spoof probability)."
                )
            elif rawnet2_spoof_score < 0.25 and f0_std >= 5.0:
                ai_risk_penalty = min(ai_risk_penalty, 0.05)
                diagnostics.append(f"Natural human speech verified: rich pitch dynamics (std: {f0_std} Hz) and authentic spectral harmonics.")

        ai_risk_score = round(min(0.95, max(0.04, ai_risk_penalty)), 3)
        human_score = round(1.0 - ai_risk_score, 3)

        is_ai = ai_risk_score >= 0.45
        auth_label = "AI_DEEPFAKE" if is_ai else "AUTHENTIC_HUMAN"
        auth_label_ar = "صوت اصطناعي (AI Deepfake)" if is_ai else "صوت بشري طبيعي (Real Human)"
        verdict_text = (
            f"High probability of AI-generated or vocoded synthetic voice ({round(ai_risk_score * 100, 1)}% AI Risk)."
            if is_ai else
            f"Acoustically consistent with natural human vocal dynamics ({round(human_score * 100, 1)}% Authenticity)."
        )

        return {
            "success": True,
            "gender": gender,
            "gender_ar": gender_ar,
            "gender_confidence": gender_confidence,
            "expected_pitch_range_hz": expected_range,
            "ai_risk_score": ai_risk_score,
            "human_score": human_score,
            "is_ai_generated": is_ai,
            "authenticity_label": auth_label,
            "authenticity_label_ar": auth_label_ar,
            "pitch_mean_hz": f0_mean,
            "pitch_range_hz": [f0_min, f0_max],
            "pitch_std_hz": f0_std,
            "formants": formants,
            "spectral_centroid_hz": centroid,
            "zero_crossing_rate": zcr,
            "high_freq_energy_ratio": hf_energy,
            "spectral_flatness": spec_flatness,
            "voiced_ratio": pitch["voiced_ratio"],
            "pitch_contour": pitch.get("trajectory", []),
            "diagnostics": diagnostics,
            "explanation": verdict_text
        }

    def verify_against_profile(
        self,
        audio: np.ndarray,
        profile_id: Optional[str] = None,
        sample_rate: int = 16000,
        rawnet2_spoof_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Doctor's Frequency Baseline Verification, 1-to-N Speaker Identification & Impersonation Engine.
        """
        analysis = self.classify_voice(audio, sample_rate, rawnet2_spoof_score=rawnet2_spoof_score)
        measured_pitch = analysis["pitch_mean_hz"]
        detected_gender = analysis["gender"]
        detected_gender_ar = analysis["gender_ar"]

        # Run 1-to-N Speaker Identification across all enrolled profiles
        identification = self.identify_speaker(audio, sample_rate=sample_rate)

        p_id_raw = str(profile_id or "").strip().lower()
        
        # Check if caller specified a specific enrolled custom profile (e.g. "karim_alaa")
        specific_profile = None
        if p_id_raw not in ["", "auto", "none", "male", "female"]:
            profile_path = os.path.join(self.profiles_dir, f"{p_id_raw}.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, "r", encoding="utf-8") as pf:
                        specific_profile = json.load(pf)
                except Exception:
                    pass

        # Case 1: Specific Speaker Verification (e.g. Caller claims to be Karim or Doctor)
        if specific_profile:
            target_name = specific_profile.get("name")
            target_title = specific_profile.get("title")
            target_ac = specific_profile.get("acoustic_profile", {})
            ref_f0 = target_ac.get("f0_pitch_mean_hz", 125.0)
            target_range = [round(ref_f0 * 0.75, 1), round(ref_f0 * 1.25, 1)]
            
            # Find candidate score for this profile
            cand_match = 0.0
            target_canonical = extract_canonical_speaker_name(target_name)
            for cand in identification.get("all_candidates", []):
                if cand.get("profile_id") == p_id_raw or extract_canonical_speaker_name(cand.get("name")) == target_canonical:
                    cand_match = cand.get("match_percentage", 0.0)
                    break
            
            is_verified = cand_match >= 65.0
            if is_verified:
                verdict = "VERIFIED_SPEAKER_MATCH"
                verdict_ar = f"تم التحقق من هوية المتحدث: {target_name}"
                impersonation_risk = round(max(0.04, min(0.20, analysis["ai_risk_score"])), 3)
                explanation = (
                    f"Voiceprint matched enrolled baseline for '{target_name}' with {cand_match}% confidence. "
                    f"Pitch: {measured_pitch} Hz (Baseline: {ref_f0} Hz)."
                )
                diag = [f"Voice biometrics successfully verified against enrolled profile '{target_name}'."]
            else:
                verdict = "IMPERSONATION_MISMATCH_ALERT"
                verdict_ar = f"تحذير انتحال شخصية: الصوت لا يطابق بصمة {target_name}"
                impersonation_risk = 0.88
                explanation = (
                    f"🚨 IMPERSONATION ALERT: Caller claims to be '{target_name}', but voice biometrics "
                    f"diverge significantly (Match score: {cand_match}%, Pitch: {measured_pitch} Hz vs expected {ref_f0} Hz)."
                )
                diag = [
                    f"Acoustic mismatch: caller failed voiceprint verification for '{target_name}'.",
                    f"Potential caller identity: {identification.get('speaker_name', 'Unknown')}."
                ]

            return {
                "profile_specified": True,
                "target_profile": {
                    "profile_id": p_id_raw,
                    "name": target_name,
                    "title": target_title,
                    "expected_pitch_mean_hz": ref_f0,
                    "expected_pitch_range_hz": target_range
                },
                "caller_acoustic_measurements": {
                    "pitch_mean_hz": measured_pitch,
                    "pitch_range_hz": analysis["pitch_range_hz"],
                    "pitch_std_hz": analysis["pitch_std_hz"],
                    "formants": analysis.get("formants", {}),
                    "spectral_centroid_hz": analysis["spectral_centroid_hz"],
                    "zero_crossing_rate": analysis["zero_crossing_rate"],
                    "voiced_ratio": analysis["voiced_ratio"]
                },
                "speaker_identification": identification,
                "evaluation": {
                    "gender": detected_gender,
                    "gender_ar": detected_gender_ar,
                    "gender_confidence": analysis["gender_confidence"],
                    "identified_speaker": identification.get("speaker_name"),
                    "speaker_match_percentage": cand_match,
                    "is_ai_generated": analysis["is_ai_generated"],
                    "ai_risk_score": analysis["ai_risk_score"],
                    "human_score": analysis["human_score"],
                    "impersonation_risk_score": impersonation_risk,
                    "verdict": verdict,
                    "verdict_ar": verdict_ar,
                    "explanation": explanation,
                    "diagnostics": diag
                }
            }

        # Case 2: Male / Female Baseline Filter
        if "female" in p_id_raw or p_id_raw in ["female", "woman", "أنثى"]:
            target_id = "female"
            target_name = "Female Voice (أنثى)"
            target_title = "Female Adult Frequency Baseline"
            target_range = [165.0, 260.0]
            target_mean = 215.0
        elif "male" in p_id_raw or p_id_raw in ["male", "man", "ذكر"]:
            target_id = "male"
            target_name = "Male Voice (ذكر)"
            target_title = "Male Adult Frequency Baseline"
            target_range = [85.0, 165.0]
            target_mean = 125.0
        else:
            target_id = "auto"
            target_name = f"Auto: {identification.get('speaker_name', detected_gender)}"
            target_title = "Automatic Acoustic Identification"
            target_range = analysis["expected_pitch_range_hz"]
            target_mean = measured_pitch

        # Evaluate match against target range
        if target_id in ["male", "female"]:
            in_range = (target_range[0] <= measured_pitch <= target_range[1])
            if in_range:
                pitch_dev = round(abs(measured_pitch - target_mean), 1)
                match_pct = round(max(75.0, min(99.0, 100.0 - pitch_dev * 0.4)), 1)
                if analysis["is_ai_generated"]:
                    impersonation_risk = analysis["ai_risk_score"]
                    verdict = "AI_SPOOF_IN_TARGET_RANGE"
                    verdict_ar = f"صوت اصطناعي (AI Deepfake) يطابق النطاق الترددي للـ{'أنثى' if target_id == 'female' else 'ذكر'}"
                    explanation = (
                        f"🚨 AI SYNTHETIC VOICE DETECTED: Caller pitch ({measured_pitch} Hz) is inside expected {target_name} range "
                        f"[{target_range[0]} - {target_range[1]} Hz], BUT acoustic artifacts confirm an AI synthetic voice."
                    )
                    diag = [f"Pitch within {target_name} baseline, but synthetic artifacts detected."] + analysis["diagnostics"]
                else:
                    impersonation_risk = round(max(0.04, min(0.30, analysis["ai_risk_score"])), 3)
                    verdict = "AUTHENTIC_FREQUENCY_MATCH"
                    verdict_ar = "تطابق ترددي معتمد (مطابق للملف المختار)"
                    explanation = (
                        f"Voice pitch ({measured_pitch} Hz) is within expected {target_name} range "
                        f"[{target_range[0]} - {target_range[1]} Hz]. Frequency profile verified."
                    )
                    diag = [f"Caller pitch ({measured_pitch} Hz) matches the expected {target_name} baseline."]
            else:
                pitch_dev = round(target_range[0] - measured_pitch, 1) if measured_pitch < target_range[0] else round(measured_pitch - target_range[1], 1)
                match_pct = round(max(5.0, 35.0 - pitch_dev * 0.3), 1)
                impersonation_risk = round(min(0.95, max(0.70, 0.70 + min(pitch_dev * 0.005, 0.25))), 3)
                verdict = "FREQUENCY_MISMATCH_IMPERSONATION"
                verdict_ar = f"عدم تطابق التردد مع الصوت ال{'أنثوي' if target_id == 'female' else 'ذكوري'} المختار"
                explanation = (
                    f"🚨 FREQUENCY MISMATCH: Caller pitch ({measured_pitch} Hz, {detected_gender}) deviates by "
                    f"{pitch_dev} Hz outside expected {target_name} baseline [{target_range[0]} - {target_range[1]} Hz]."
                )
                diag = [f"Caller classified as {detected_gender} ({measured_pitch} Hz), but Target Profile is {target_name}."]
        else:
            in_range = True
            pitch_dev = 0.0
            match_pct = identification.get("match_percentage", round(analysis["human_score"] * 100.0, 1))
            impersonation_risk = analysis["ai_risk_score"]
            verdict = "IDENTIFIED_ENROLLED_SPEAKER" if identification.get("identified") else ("SUSPECTED_AI_VOICE" if analysis["is_ai_generated"] else "AUTHENTIC_HUMAN_VOICE")
            verdict_ar = f"متحدث مسجل: {identification.get('speaker_name')}" if identification.get("identified") else ("صوت اصطناعي مشبوه" if analysis["is_ai_generated"] else "صوت بشري طبيعي")
            explanation = identification.get("explanation", analysis["explanation"])
            diag = analysis["diagnostics"]

        return {
            "profile_specified": (target_id in ["male", "female"]),
            "target_profile": {
                "profile_id": target_id,
                "name": target_name,
                "title": target_title,
                "vocal_classification": target_id.capitalize(),
                "expected_pitch_range_hz": target_range,
                "expected_pitch_mean_hz": target_mean
            },
            "caller_acoustic_measurements": {
                "pitch_mean_hz": measured_pitch,
                "pitch_range_hz": analysis["pitch_range_hz"],
                "pitch_std_hz": analysis["pitch_std_hz"],
                "formants": analysis.get("formants", {}),
                "pitch_contour_samples": analysis.get("pitch_contour", []),
                "spectral_centroid_hz": analysis["spectral_centroid_hz"],
                "zero_crossing_rate": analysis["zero_crossing_rate"],
                "voiced_ratio": analysis["voiced_ratio"]
            },
            "speaker_identification": identification,
            "evaluation": {
                "gender": detected_gender,
                "gender_ar": detected_gender_ar,
                "gender_confidence": analysis["gender_confidence"],
                "identified_speaker": identification.get("speaker_name"),
                "speaker_match_percentage": identification.get("match_percentage", 0.0),
                "target_mode": target_id,
                "is_ai_generated": analysis["is_ai_generated"],
                "ai_risk_score": analysis["ai_risk_score"],
                "human_score": analysis["human_score"],
                "authenticity_label": analysis["authenticity_label"],
                "authenticity_label_ar": analysis["authenticity_label_ar"],
                "pitch_in_range": in_range,
                "pitch_deviation_hz": pitch_dev,
                "impersonation_risk_score": impersonation_risk,
                "verdict": verdict,
                "verdict_ar": verdict_ar,
                "explanation": explanation,
                "diagnostics": diag
            }
        }

    def list_profiles(self) -> List[Dict[str, Any]]:
        """Returns baseline frequency profiles plus all enrolled custom speaker profiles."""
        base_profiles = [
            {
                "profile_id": "auto",
                "name": "Auto-Detect Speaker & Gender (تحديد المتحدث تلقائياً)",
                "title": "Automatic 1-to-N Biometric Speaker Identification",
                "vocal_classification": "Dynamic",
                "expected_pitch_range_hz": [85.0, 260.0],
                "expected_pitch_mean_hz": 165.0
            },
            {
                "profile_id": "male",
                "name": "Male Baseline (صوت ذكوري عام)",
                "title": "Male Adult Pitch Range",
                "vocal_classification": "Baritone / Tenor",
                "expected_pitch_range_hz": [85.0, 165.0],
                "expected_pitch_mean_hz": 125.0
            },
            {
                "profile_id": "female",
                "name": "Female Baseline (صوت أنثوي عام)",
                "title": "Female Adult Pitch Range",
                "vocal_classification": "Mezzo / Soprano",
                "expected_pitch_range_hz": [165.0, 260.0],
                "expected_pitch_mean_hz": 215.0
            }
        ]

        # Add custom enrolled profiles
        if os.path.exists(self.profiles_dir):
            for pf in os.listdir(self.profiles_dir):
                if pf.endswith(".json"):
                    try:
                        with open(os.path.join(self.profiles_dir, pf), "r", encoding="utf-8") as f:
                            data = json.load(f)
                        p_id = data.get("profile_id")
                        ac = data.get("acoustic_profile", {})
                        ref_f0 = ac.get("f0_pitch_mean_hz", 125.0)
                        raw_name = data.get('name', '')
                        clean_name = extract_canonical_speaker_name(raw_name)
                        base_profiles.append({
                            "profile_id": p_id,
                            "name": f"👤 {clean_name} ({data.get('gender_ar', 'مسجل')})",
                            "title": data.get("title", f"الملف البيومتري الصوتي: {clean_name}"),
                            "vocal_classification": data.get("gender", "Enrolled"),
                            "expected_pitch_range_hz": [round(ref_f0 * 0.75, 1), round(ref_f0 * 1.25, 1)],
                            "expected_pitch_mean_hz": ref_f0,
                            "formants": {
                                "f1": ac.get("formant_f1_hz"),
                                "f2": ac.get("formant_f2_hz"),
                                "f3": ac.get("formant_f3_hz")
                            }
                        })
                    except Exception:
                        continue

        return base_profiles
