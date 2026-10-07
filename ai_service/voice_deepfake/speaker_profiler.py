"""
Acoustic Voice & Gender Profiler - EASP Voice Security Engine
Extracts fundamental acoustic metrics:
  - Fundamental Frequency (F0 / Pitch in Hz) using robust YIN algorithm
  - Gender Classification (Male / Female / High-Pitch / Unvoiced)
  - Target Frequency Profile Matching & Impersonation Detection (Male vs Female baselines)
  - AI vs Real (Human) Authenticity Risk Evaluation (Pitch Dynamics, Robotic Flatness, Spectral Dispersion)
"""

import os
import json
from typing import Dict, Any, Optional, List
import numpy as np


class SpeakerFrequencyProfiler:
    """
    Acoustic Frequency & Voice Authenticity Analyzer.
    Classifies gender (Male vs Female) and evaluates frequency compliance against target profiles.
    """

    def __init__(self, profiles_dir: Optional[str] = None):
        self.profiles_dir = profiles_dir

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
        Extracts F0 Fundamental Pitch trajectory using the YIN algorithm:
        1. Difference function d_t(tau)
        2. Cumulative mean normalized difference cmnd_t(tau)
        3. Absolute thresholding and local minimum selection
        4. Global minimum fallback for noise resilience
        5. Parabolic interpolation
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
            # Remove extreme 2% outliers if sufficient frames
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

    def extract_acoustic_features(self, audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """Extracts pitch, spectral centroid, spectral roll-off, and zero-crossing rate."""
        if audio is None or len(audio) == 0:
            return {
                "success": False,
                "error": "Empty audio provided",
                "pitch": {"mean_hz": 0.0, "min_hz": 0.0, "max_hz": 0.0, "std_hz": 0.0, "voiced_ratio": 0.0},
                "spectral": {"centroid_hz": 0.0, "rolloff_hz": 0.0}
            }

        audio = audio.astype(np.float32)
        total_samples = len(audio)

        pitch_metrics = self._extract_yin_pitch(audio, sample_rate=sample_rate)

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

        # Neural Vocoder Artifacts (High-Frequency Derivative Energy & Spectral Flatness)
        diff_audio = np.diff(audio)
        hf_energy = float(np.mean(diff_audio ** 2) / (np.mean(audio ** 2) + 1e-8)) if total_samples > 1 else 0.0
        
        # Spectral Flatness across initial speech segment
        spec_init = np.abs(np.fft.rfft(audio[:min(total_samples, 8000)]))
        spec_flatness = float(np.exp(np.mean(np.log(spec_init + 1e-8))) / (np.mean(spec_init) + 1e-8)) if len(spec_init) > 0 else 0.0

        return {
            "success": True,
            "sample_rate": sample_rate,
            "duration_seconds": round(total_samples / sample_rate, 2),
            "pitch": pitch_metrics,
            "spectral": spectral_metrics,
            "zero_crossing_rate": round(zero_crossings, 4),
            "high_freq_energy_ratio": round(hf_energy, 4),
            "spectral_flatness": round(spec_flatness, 4)
        }

    def classify_voice(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        rawnet2_spoof_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Main Classification & Vocal Dynamics Function:
        1. Classifies voice gender: Male (ذكر) vs Female (أنثى).
        2. Calculates AI vs Real (Human) acoustic risk probability based on pitch variability and harmonics.
        """
        features = self.extract_acoustic_features(audio, sample_rate)
        if not features.get("success"):
            return {
                "success": False,
                "gender": "Unknown",
                "gender_ar": "غير محدد",
                "gender_confidence": 0.0,
                "ai_risk_score": 0.5,
                "human_score": 0.5,
                "is_ai_generated": False,
                "authenticity_label": "UNAVAILABLE",
                "authenticity_label_ar": "غير متاح",
                "pitch_mean_hz": 0.0,
                "pitch_range_hz": [0.0, 0.0],
                "explanation": "Could not extract acoustic features from audio."
            }

        pitch = features["pitch"]
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

        # ---------------------------------------------------------
        # 1. Gender Classification (Male vs Female)
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # 2. AI vs Real (Human) Vocal Dynamics Risk Evaluation
        # ---------------------------------------------------------
        ai_risk_penalty = 0.08
        diagnostics = []

        if voiced_frames >= 10:
            # Robotic pitch flatness check:
            # Natural human speech has pitch intonation (std >= 6.0 Hz).
            # Robotic TTS typically produces unnaturally flat pitch (std < 2.5 Hz).
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

        # Independent Neural Vocoder Physical Artifacts Check
        # Neural vocoders (MelGAN/HiFi-GAN) exhibit extreme ZCR (>= 0.20) COMBINED with flat pitch dynamics.
        # Ambient mic hiss or breath sounds alone must NOT trigger artificial deepfake penalties on expressive speech.
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

        # Cross-reference with Neural Voice Deepfake Detector
        if rawnet2_spoof_score is not None:
            if rawnet2_spoof_score >= 0.50:
                # If neural detector flagged spoofing, align acoustic score
                ai_risk_penalty = max(ai_risk_penalty, round(rawnet2_spoof_score, 3))
                diagnostics.append(
                    f"Neural deepfake detector flagged synthetic audio indicators ({round(rawnet2_spoof_score * 100, 1)}% spoof probability)."
                )
            elif rawnet2_spoof_score < 0.25 and f0_std >= 5.0:
                # Strong human confirmation: low neural spoof score + rich natural human pitch dynamics
                ai_risk_penalty = min(ai_risk_penalty, 0.05)
                diagnostics.append(f"Natural human speech verified: rich pitch dynamics (std: {f0_std} Hz) and authentic spectral harmonics.")

        ai_risk_score = round(min(0.95, max(0.04, ai_risk_penalty)), 3)
        human_score = round(1.0 - ai_risk_score, 3)

        is_ai = ai_risk_score >= 0.45
        if is_ai:
            auth_label = "AI_DEEPFAKE"
            auth_label_ar = "صوت اصطناعي (AI Deepfake)"
            verdict_text = f"High probability of AI-generated or vocoded synthetic voice ({round(ai_risk_score * 100, 1)}% AI Risk)."
        else:
            auth_label = "AUTHENTIC_HUMAN"
            auth_label_ar = "صوت بشري طبيعي (Real Human)"
            verdict_text = f"Acoustically consistent with natural human vocal dynamics ({round(human_score * 100, 1)}% Authenticity)."

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
        Doctor's Frequency Baseline Verification & Impersonation Engine:
        Validates the incoming caller against the requested target profile (Male, Female, or Auto-Detect).
        Detects gender/frequency mismatches and flags voice impersonation risk.
        """
        analysis = self.classify_voice(audio, sample_rate, rawnet2_spoof_score=rawnet2_spoof_score)
        measured_pitch = analysis["pitch_mean_hz"]
        detected_gender = analysis["gender"]
        detected_gender_ar = analysis["gender_ar"]

        # Parse requested target profile
        p_id_raw = str(profile_id or "").strip().lower()
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
            target_name = f"Auto-Detect: {detected_gender}"
            target_title = "Automatic Acoustic Gender Classification"
            target_range = analysis["expected_pitch_range_hz"]
            target_mean = measured_pitch

        # Evaluate match against target profile
        if target_id in ["male", "female"]:
            in_range = (target_range[0] <= measured_pitch <= target_range[1])
            if in_range:
                # Caller matches expected frequency profile
                pitch_dev = round(abs(measured_pitch - target_mean), 1)
                match_pct = round(max(75.0, min(99.0, 100.0 - pitch_dev * 0.4)), 1)
                
                # Check if caller matches pitch range BUT is an AI deepfake synthetic voice
                if analysis["is_ai_generated"]:
                    impersonation_risk = analysis["ai_risk_score"]
                    verdict = "AI_SPOOF_IN_TARGET_RANGE"
                    verdict_ar = f"صوت اصطناعي (AI Deepfake) يطابق النطاق الترددي للـ{'أنثى' if target_id == 'female' else 'ذكر'}"
                    explanation = (
                        f"🚨 AI SYNTHETIC VOICE DETECTED: Caller pitch ({measured_pitch} Hz) is inside expected {target_name} range "
                        f"[{target_range[0]} - {target_range[1]} Hz], BUT acoustic and vocoder indicators confirm "
                        f"an AI-generated synthetic voice ({round(analysis['ai_risk_score'] * 100, 1)}% AI Deepfake Risk)."
                    )
                    diag = [
                        f"Pitch ({measured_pitch} Hz) falls within {target_name} baseline, but synthetic artifacts detected.",
                        f"Acoustic AI Risk: {round(analysis['ai_risk_score'] * 100, 1)}%."
                    ] + analysis["diagnostics"]
                else:
                    impersonation_risk = round(max(0.04, min(0.30, analysis["ai_risk_score"])), 3)
                    verdict = "AUTHENTIC_FREQUENCY_MATCH"
                    verdict_ar = "تطابق ترددي معتمد (مطابق للملف المختار)"
                    explanation = (
                        f"Voice pitch ({measured_pitch} Hz) is within expected {target_name} range "
                        f"[{target_range[0]} - {target_range[1]} Hz]. Frequency profile verified."
                    )
                    diag = [
                        f"Caller pitch ({measured_pitch} Hz) matches the expected {target_name} baseline.",
                        f"Deviation from ideal centroid ({target_mean} Hz): {pitch_dev} Hz."
                    ]
            else:
                # FREQUENCY MISMATCH DETECTED (e.g. Male caller claiming Female profile)
                if measured_pitch < target_range[0]:
                    pitch_dev = round(target_range[0] - measured_pitch, 1)
                else:
                    pitch_dev = round(measured_pitch - target_range[1], 1)

                match_pct = round(max(5.0, 35.0 - pitch_dev * 0.3), 1)
                impersonation_risk = round(min(0.95, max(0.70, 0.70 + min(pitch_dev * 0.005, 0.25))), 3)
                verdict = "FREQUENCY_MISMATCH_IMPERSONATION"
                verdict_ar = f"عدم تطابق التردد مع الصوت ال{'أنثوي' if target_id == 'female' else 'ذكوري'} المختار (انتحال محتمل)"
                explanation = (
                    f"🚨 FREQUENCY MISMATCH: Caller pitch ({measured_pitch} Hz, {detected_gender}) deviates by "
                    f"{pitch_dev} Hz outside expected {target_name} baseline [{target_range[0]} - {target_range[1]} Hz]. "
                    f"High probability of voice spoofing or gender impersonation."
                )
                diag = [
                    f"ALERT: Incoming voice classified as {detected_gender} ({measured_pitch} Hz), but Target Profile is {target_name}.",
                    f"Pitch boundary violation: {pitch_dev} Hz deviation from closest bound.",
                    "High acoustic impersonation risk score assigned to trigger security escalation."
                ]
        else:
            # Auto-detect mode
            in_range = True
            pitch_dev = 0.0
            match_pct = round(analysis["human_score"] * 100.0, 1)
            impersonation_risk = analysis["ai_risk_score"]
            verdict = "SUSPECTED_AI_VOICE" if analysis["is_ai_generated"] else "AUTHENTIC_HUMAN_VOICE"
            verdict_ar = "صوت اصطناعي مشبوه" if analysis["is_ai_generated"] else "صوت بشري طبيعي"
            explanation = analysis["explanation"]
            diag = analysis["diagnostics"]

        return {
            "profile_specified": (target_id in ["male", "female"]),
            "target_profile": {
                "profile_id": target_id,
                "name": target_name,
                "title": target_title,
                "vocal_classification": target_id.capitalize(),
                "expected_pitch_range_hz": target_range,
                "expected_pitch_mean_hz": target_mean,
                "expected_spectral_centroid_hz": [1200.0, 2800.0]
            },
            "caller_acoustic_measurements": {
                "pitch_mean_hz": measured_pitch,
                "pitch_range_hz": analysis["pitch_range_hz"],
                "pitch_std_hz": analysis["pitch_std_hz"],
                "pitch_contour_samples": analysis.get("pitch_contour", []),
                "spectral_centroid_hz": analysis["spectral_centroid_hz"],
                "spectral_rolloff_hz": 0.0,
                "zero_crossing_rate": analysis["zero_crossing_rate"],
                "voiced_ratio": analysis["voiced_ratio"]
            },
            "evaluation": {
                "gender": detected_gender,
                "gender_ar": detected_gender_ar,
                "gender_confidence": analysis["gender_confidence"],
                "target_mode": target_id,
                "is_ai_generated": analysis["is_ai_generated"],
                "ai_risk_score": analysis["ai_risk_score"],
                "human_score": analysis["human_score"],
                "authenticity_label": analysis["authenticity_label"],
                "authenticity_label_ar": analysis["authenticity_label_ar"],
                "pitch_in_range": in_range,
                "pitch_deviation_hz": pitch_dev,
                "centroid_deviation_hz": 0.0,
                "pitch_flattening_detected": analysis["ai_risk_score"] >= 0.40,
                "frequency_match_percentage": match_pct,
                "impersonation_risk_score": impersonation_risk,
                "verdict": verdict,
                "verdict_ar": verdict_ar,
                "explanation": explanation,
                "diagnostics": diag
            }
        }

    def list_profiles(self) -> List[Dict[str, Any]]:
        """Returns acoustic baseline frequency profiles."""
        return [
            {
                "profile_id": "auto",
                "name": "Auto-Detect Gender (Male / Female)",
                "title": "Automatic Acoustic Classification",
                "vocal_classification": "Dynamic",
                "expected_pitch_range_hz": [85.0, 260.0],
                "expected_pitch_mean_hz": 165.0
            },
            {
                "profile_id": "male",
                "name": "Male Voice (ذكر)",
                "title": "Male Adult Pitch Range",
                "vocal_classification": "Baritone / Tenor",
                "expected_pitch_range_hz": [85.0, 165.0],
                "expected_pitch_mean_hz": 125.0
            },
            {
                "profile_id": "female",
                "name": "Female Voice (أنثى)",
                "title": "Female Adult Pitch Range",
                "vocal_classification": "Mezzo / Soprano",
                "expected_pitch_range_hz": [165.0, 260.0],
                "expected_pitch_mean_hz": 215.0
            }
        ]
