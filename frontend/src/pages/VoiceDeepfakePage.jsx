import Icon from '../components/Icon';
import React, { useState } from 'react';
import AudioAnalysisResults from '../components/AudioAnalysisResults';
import { normalizeAudioAnalysis } from '../services/audioAnalysis';
import { securityApi } from '../services/apiClient';

export default function VoiceDeepfakePage({ currentUser }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [genderFilter, setGenderFilter] = useState('auto');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select an audio file (.wav, .mp3, or .flac) to inspect.');
      return;
    }

    if (loading) return;
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('audio', selectedFile);
      if (genderFilter !== 'auto') {
        formData.append('speakerProfileId', genderFilter);
      }

      const res = await securityApi.analyzeCall(formData);
      const raw = res.data || {};
      setResult(normalizeAudioAnalysis(raw));
    } catch (err) {
      setError(err.message || 'Audio analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-pane">
      <div className="glass-card">
        <div className="card-title-row">
          <h2 className="card-title">
            <span className="badge-platform">AUDIO AI</span>
            Analyze an audio recording
          </h2>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            RawNet2 ASVspoof + Acoustic Frequency Profiler (Male/Female & AI/Real) + Faster-Whisper + mBERT
          </span>
        </div>

        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
          Inspect inbound calls through two complementary models: <strong>Model 1 (RawNet2)</strong> evaluates synthetic vocoder artifacts, while <strong>Model 2 (Acoustic Profiler)</strong> measures fundamental frequency (F₀ pitch) to classify the voice as <strong>Male or Female</strong> and calculate the risk of being <strong>AI-generated vs Real Human</strong>.
        </p>

        <form className="audio-form" aria-busy={loading} onSubmit={handleAnalyze}>
          {/* Gender Filter Option */}
          <div className="audio-mode">
            <div>
              <label htmlFor="gender-mode-select" style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Icon name="voice" /> Acoustic Frequency Mode:
              </label>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Identifies gender (Male 85-165 Hz / Female 165-260 Hz) and assesses AI synthesis vs human vocal dynamics.
              </span>
            </div>

            <select
              id="gender-mode-select"
              disabled={loading}
              value={genderFilter}
              onChange={(e) => setGenderFilter(e.target.value)}
            >
              <option value="auto">Auto-Detect (Male / Female)</option>
              <option value="male">Target: Male Voice (ذكر)</option>
              <option value="female">Target: Female Voice (أنثى)</option>
            </select>
          </div>

          {/* Audio Upload Box */}
          <div className="upload-area">
            <input
              type="file"
              disabled={loading}
              id="audio-file-input"
              accept="audio/*,.wav,.mp3,.flac"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <label htmlFor="audio-file-input"
              role="button"
              tabIndex={loading ? -1 : 0}
              aria-disabled={loading}
              onKeyDown={(event) => {
                if (!loading && (event.key === 'Enter' || event.key === ' ')) {
                  event.preventDefault();
                  document.getElementById('audio-file-input').click();
                }
              }}
              style={{ cursor: 'pointer', display: 'block' }}>
              <div className="upload-icon"><Icon name="upload" /></div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                {selectedFile ? selectedFile.name : 'Select an audio recording (.wav, .mp3, .flac)'}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Recommended: 16 kHz Mono PCM WAV or standard customer service / VoIP call recording
              </div>
            </label>
          </div>

          <div className="audio-actions">
            <button
              type="submit"
              className="btn-primary"
              disabled={loading || !selectedFile}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              {loading ? (
                <>
                  <span className="spinner" />
                  <span>Evaluating Acoustic Models & Risk...</span>
                </>
              ) : (
                <>
                  <Icon name="search" />
                  <span>Analyze Audio (Gender & AI Risk)</span>
                </>
              )}
            </button>
            {selectedFile && (
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                File size: {(selectedFile.size / 1024).toFixed(1)} KB
              </span>
            )}
          </div>
        </form>
        {loading && <div className="analysis-processing" role="status"><span className="spinner" aria-hidden="true" /><span>Analyzing your recording. Results will appear when processing is complete.</span></div>}

        {error && (
          <div className="alert-error" role="alert">
            {error}
          </div>
        )}
      </div>

      {result && <AudioAnalysisResults result={result} />}
    </div>
  );
}
