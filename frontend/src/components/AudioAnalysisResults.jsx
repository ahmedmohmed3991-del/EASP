import Icon from './Icon';
import React from 'react';

export default function AudioAnalysisResults({ result }) {
  return (
        <div className="analysis-results">
          {/* Unified Policy & Risk Banner */}
          <div className="glass-card" style={{ borderLeft: `4px solid ${result.policyAction === 'BLOCK' ? 'var(--danger-color)' : result.policyAction === 'ESCALATE' ? 'var(--warning-color)' : 'var(--success-color)'}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                  Unified Security Verdict & Policy Decision
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.25rem' }}>
                  <span className={`pill-badge pill-${result.policyAction?.toLowerCase()}`} style={{ fontSize: '1.1rem', padding: '0.35rem 1rem' }}>
                    {result.policyAction}
                  </span>
                  <span style={{ fontSize: '1rem', fontWeight: 600 }}>
                    Threat Level: <span style={{ color: result.riskLevel === 'CRITICAL' ? 'var(--danger-color)' : result.riskLevel === 'HIGH' ? '#f87171' : result.riskLevel === 'MEDIUM' ? 'var(--warning-color)' : 'var(--success-color)' }}>{result.riskLevel}</span>
                  </span>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Fused Deepfake & Coercion Risk</span>
                <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
                  {(result.riskScore * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <strong>Policy Reason:</strong> {result.policyReason || 'Automated policy evaluation complete.'}
              {result.incidentId && (
                <div style={{ marginTop: '0.25rem' }}>
                  <strong>Incident Logged:</strong> <span style={{ fontFamily: 'monospace', color: 'var(--accent-primary)' }}>{result.incidentId}</span>
                </div>
              )}
            </div>
          </div>

          {/* Diagnostic Grid: Model 1, Model 2, and Model 3 */}
          <div className="analysis-grid">
            
            {/* MODEL 1: RawNet2 General AI Deepfake Analysis */}
            <div className="glass-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.05rem', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Icon name="shield" /> Model 1: RawNet2 Synthetics
                </h3>
                <span className="pill-badge pill-info" style={{ fontSize: '0.7rem' }}>ASVspoof</span>
              </div>
              
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>AI Spoof Probability:</span>
                  <span style={{ fontWeight: 600, color: (result.voiceAnalysis?.spoofScore || 0) > 0.5 ? 'var(--danger-color)' : 'var(--success-color)' }}>
                    {((result.voiceAnalysis?.spoofScore || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    width: `${Math.min(100, (result.voiceAnalysis?.spoofScore || 0) * 100)}%`,
                    height: '100%',
                    background: (result.voiceAnalysis?.spoofScore || 0) > 0.5 ? 'var(--danger-color)' : 'var(--success-color)',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>

              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <div>
                  <strong>Authenticity Verdict:</strong>{' '}
                  <span style={{ fontWeight: 600, color: result.voiceAnalysis?.isSynthetic ? 'var(--danger-color)' : 'var(--success-color)' }}>
                    {result.voiceAnalysis?.isSynthetic ? 'SYNTHETIC / AI DEEPFAKE' : 'REAL HUMAN VOICE'}
                  </span>
                </div>
                <div><strong>Inference Mode:</strong> {result.voiceAnalysis?.inferenceMode || 'DSP Acoustic Analysis'}</div>
                {result.voiceAnalysis?.spectralFeatures && (
                  <div style={{ marginTop: '0.5rem', padding: '0.6rem', background: 'rgba(0,0,0,0.25)', borderRadius: '6px', fontSize: '0.8rem', fontFamily: 'monospace' }}>
                    <div>Zero-Crossing Rate: {result.voiceAnalysis.spectralFeatures.zeroCrossingRate?.toFixed(4) || 'N/A'}</div>
                    <div>Spectral Smoothness Var: {result.voiceAnalysis.spectralFeatures.spectralVariance?.toFixed(6) || 'N/A'}</div>
                  </div>
                )}
              </div>
            </div>

            {/* MODEL 2: Acoustic Frequency & Gender Profiler (Doctor's Model) */}
            <div className="glass-card" style={{ borderTop: `3px solid ${result.acousticProfile?.pitch_in_range === false ? 'var(--danger-color)' : 'var(--accent-primary)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '1.05rem', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Icon name="voice" /> Model 2: Gender & Acoustic AI Risk
                </h3>
                <span className="pill-badge pill-accent" style={{ fontSize: '0.7rem' }}>
                  YIN F₀ Pitch
                </span>
              </div>

              {result.acousticProfile ? (
                <div>
                  {/* Target Frequency Mode Status Alert */}
                  {result.acousticProfile.target_mode && result.acousticProfile.target_mode !== 'auto' && (
                    <div style={{
                      padding: '0.65rem 0.85rem',
                      marginBottom: '0.85rem',
                      borderRadius: '6px',
                      background: result.acousticProfile.pitch_in_range === false ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                      border: `1px solid ${result.acousticProfile.pitch_in_range === false ? 'var(--danger-color)' : 'var(--success-color)'}`,
                      fontSize: '0.82rem'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong>
                          {result.acousticProfile.pitch_in_range === false
                            ? 'FREQUENCY & GENDER MISMATCH DETECTED'
                            : 'FREQUENCY PROFILE MATCHED'}
                        </strong>
                        <span style={{ fontWeight: 700, color: result.acousticProfile.pitch_in_range === false ? 'var(--danger-color)' : 'var(--success-color)' }}>
                          {result.acousticProfile.frequency_match_percentage}% Match
                        </span>
                      </div>
                      <div style={{ fontSize: '0.75rem', marginTop: '0.2rem', color: 'var(--text-secondary)' }}>
                        Target: <strong>{result.targetProfile?.name || result.acousticProfile.target_mode}</strong> [{result.targetProfile?.expected_pitch_range_hz?.[0]} - {result.targetProfile?.expected_pitch_range_hz?.[1]} Hz]
                        {result.acousticProfile.pitch_in_range === false && (
                          <span style={{ color: '#f87171', marginLeft: '0.4rem' }}>
                            (Deviation: {result.acousticProfile.pitch_deviation_hz} Hz outside bound)
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Gender Classification Header Card */}
                  <div style={{
                    padding: '0.75rem',
                    background: 'rgba(255,255,255,0.03)',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '0.85rem'
                  }}>
                    <div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Detected Voice Gender:</span>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.15rem' }}>
                        <Icon name="voice" />
                        <span>{result.acousticProfile.gender}</span>
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 400 }}>
                          ({result.acousticProfile.gender_ar || (result.acousticProfile.gender === 'Male' ? 'ذكر' : 'أنثى')})
                        </span>
                      </div>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <span className="pill-badge pill-info" style={{ fontSize: '0.75rem' }}>
                        {result.acousticProfile.gender_confidence ? `${result.acousticProfile.gender_confidence}% Confidence` : 'Acoustic F₀'}
                      </span>
                    </div>
                  </div>

                  {/* Target Frequency Match & AI Risk Bars */}
                  <div style={{ marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                    {/* Bar 1: Frequency Match % */}
                    {result.acousticProfile.target_mode && result.acousticProfile.target_mode !== 'auto' && (
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem', fontSize: '0.82rem' }}>
                          <span style={{ color: 'var(--text-secondary)' }}>Target Frequency Range Match:</span>
                          <span style={{ fontWeight: 600, color: result.acousticProfile.pitch_in_range ? 'var(--success-color)' : 'var(--danger-color)' }}>
                            {result.acousticProfile.frequency_match_percentage}%
                          </span>
                        </div>
                        <div style={{ width: '100%', height: '7px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{
                            width: `${Math.min(100, result.acousticProfile.frequency_match_percentage || 0)}%`,
                            height: '100%',
                            background: result.acousticProfile.pitch_in_range ? 'var(--success-color)' : 'var(--danger-color)',
                            transition: 'width 0.3s ease'
                          }} />
                        </div>
                      </div>
                    )}

                    {/* Bar 2: AI Deepfake Synthesis Risk */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem', fontSize: '0.82rem' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Acoustic AI Deepfake Risk:</span>
                        <span style={{ fontWeight: 600, color: (result.acousticProfile.ai_risk_score || 0) >= 0.45 ? 'var(--danger-color)' : 'var(--success-color)' }}>
                          {((result.acousticProfile.ai_risk_score || 0) * 100).toFixed(1)}% ({result.acousticProfile.is_ai_generated ? 'AI' : 'Real'})
                        </span>
                      </div>
                      <div style={{ width: '100%', height: '7px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{
                          width: `${Math.min(100, (result.acousticProfile.ai_risk_score || 0) * 100)}%`,
                          height: '100%',
                          background: (result.acousticProfile.ai_risk_score || 0) >= 0.45 ? 'var(--danger-color)' : 'var(--success-color)',
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                    </div>
                  </div>

                  {/* Pitch and Frequency Metrics */}
                  <div style={{
                    padding: '0.75rem',
                    background: 'rgba(0,0,0,0.3)',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color)',
                    fontSize: '0.82rem',
                    marginBottom: '0.75rem'
                  }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Measured Pitch (F₀):</span>
                        <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
                          {result.callerMeasurements?.pitch_mean_hz?.toFixed(1) || '0.0'} Hz
                        </div>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Acoustic Verdict:</span>
                        <div style={{
                          fontSize: '0.88rem',
                          fontWeight: 700,
                          color: result.acousticProfile.pitch_in_range === false || result.acousticProfile.is_ai_generated ? 'var(--danger-color)' : 'var(--success-color)'
                        }}>
                          {result.acousticProfile.verdict === 'FREQUENCY_MISMATCH_IMPERSONATION'
                            ? 'MISMATCH / SPOOF'
                            : result.acousticProfile.is_ai_generated
                            ? 'AI-GENERATED'
                            : 'AUTHENTIC HUMAN'}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '0.4rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                      <span>Impersonation Risk: <strong style={{ color: (result.acousticProfile.impersonation_risk_score || 0) > 0.5 ? 'var(--danger-color)' : 'var(--text-primary)' }}>{((result.acousticProfile.impersonation_risk_score || 0) * 100).toFixed(1)}%</strong></span>
                      <span>Pitch Variance (σ): <strong>{result.callerMeasurements?.pitch_std_hz?.toFixed(1) || '0.0'} Hz</strong></span>
                    </div>
                  </div>

                  {/* Explanation text */}
                  <div style={{
                    fontSize: '0.8rem',
                    color: result.acousticProfile.pitch_in_range === false || result.acousticProfile.is_ai_generated ? '#fca5a5' : 'var(--text-secondary)',
                    fontStyle: 'italic',
                    lineHeight: '1.3'
                  }}>
                    "{result.acousticProfile.explanation || 'Acoustic pitch and spectral analysis complete.'}"
                  </div>
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic' }}>
                  Acoustic frequency analysis data pending.
                </div>
              )}
            </div>

            {/* MODEL 3: Speech Transcription & Social Engineering */}
            <div className="glass-card">
              <h3 style={{ fontSize: '1.05rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Icon name="prompt" /> Model 3: Speech & Vishing NLP
              </h3>

              <div style={{ marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Faster-Whisper Automated Transcript:</span>
                <div style={{
                  marginTop: '0.25rem',
                  padding: '0.75rem',
                  background: 'rgba(0,0,0,0.3)',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.85rem',
                  fontStyle: result.transcript ? 'normal' : 'italic',
                  color: result.transcript ? 'var(--text-primary)' : 'var(--text-muted)',
                  maxHeight: '110px',
                  overflowY: 'auto'
                }}>
                  "{result.transcript || 'No recognizable speech detected in audio stream.'}"
                </div>
              </div>

              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span>Vishing / Coercion Threat Score:</span>
                  <span style={{ fontWeight: 600, color: (result.nlpAnalysis?.socialEngineeringScore || 0) > 0.5 ? 'var(--danger-color)' : 'var(--success-color)' }}>
                    {((result.nlpAnalysis?.socialEngineeringScore || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <strong>Detected TTP Indicators:</strong>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginTop: '0.35rem' }}>
                    {result.nlpAnalysis?.threatCategories && result.nlpAnalysis.threatCategories.length > 0 ? (
                      result.nlpAnalysis.threatCategories.map((c, i) => (
                        <span key={i} className="pill-badge pill-critical" style={{ fontSize: '0.75rem' }}>
                          {c}
                        </span>
                      ))
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>None detected</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
  );
}
