import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { buildSync } from 'esbuild';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { normalizeAudioAnalysis } from '../src/services/audioAnalysis.js';

const require = createRequire(import.meta.url);
function loadComponent(path) {
  const { outputFiles } = buildSync({
    entryPoints: [fileURLToPath(new URL(path, import.meta.url))],
    bundle: true, write: false, platform: 'node', format: 'cjs',
    external: ['react'], define: { 'import.meta.env': '{}' }
  });
  const module = { exports: {} };
  new Function('require', 'module', 'exports', outputFiles[0].text)(require, module, module.exports);
  return module.exports.default;
}
const Results = loadComponent('../src/components/AudioAnalysisResults.jsx');
const Page = loadComponent('../src/pages/VoiceDeepfakePage.jsx');
const raw = {
  action: 'ALLOW', risk: { score: 0, level: 'LOW' },
  voiceDeepfake: { spoofScore: 0, isDeepfake: false },
  socialEngineering: { score: 0, threatsDetected: [] },
  transcription: { transcript: '' }
};

test('audio mapping preserves zero, false and empty canonical values over legacy fields', () => {
  const result = normalizeAudioAnalysis({ ...raw,
    voiceAnalysis: { spoofScore: 1, isSynthetic: true },
    transcript: 'legacy', nlpAnalysis: { socialEngineeringScore: 1 }
  });
  assert.equal(result.riskScore, 0);
  assert.equal(result.voiceAnalysis.spoofScore, 0);
  assert.equal(result.voiceAnalysis.isSynthetic, false);
  assert.equal(result.transcript, '');
  assert.equal(result.nlpAnalysis.socialEngineeringScore, 0);
  assert.deepEqual(result.nlpAnalysis.threatCategories, []);
});

test('audio mapping retains legacy fields, profile details and policy identifiers', () => {
  const result = normalizeAudioAnalysis({ action: 'BLOCK', risk: { score: .9, level: 'HIGH' },
    policyReason: 'reason', incidentId: 'incident', auditLogId: 'audit',
    voiceAnalysis: { spoofScore: .8, isSynthetic: true, inferenceMode: 'legacy' },
    transcript: 'text', nlpAnalysis: { socialEngineeringScore: .5, threatCategories: ['threat'] },
    speakerFrequencyProfile: { evaluation: { gender: 'Male' }, caller_acoustic_measurements: { pitch_mean_hz: 100 }, target_profile: { name: 'target' } }
  });
  assert.equal(result.policyAction, 'BLOCK');
  assert.equal(result.policyReason, 'reason');
  assert.equal(result.incidentId, 'incident');
  assert.equal(result.auditLogId, 'audit');
  assert.equal(result.voiceAnalysis.inferenceMode, 'legacy');
  assert.equal(result.transcript, 'text');
  assert.equal(result.acousticProfile.gender, 'Male');
  assert.equal(result.callerMeasurements.pitch_mean_hz, 100);
  assert.equal(result.targetProfile.name, 'target');
});

test('results render empty transcript and missing acoustic profile without changing verdict', () => {
  const html = renderToStaticMarkup(React.createElement(Results, { result: normalizeAudioAnalysis(raw) }));
  assert.match(html, /No recognizable speech detected/);
  assert.match(html, /Acoustic frequency analysis data pending/);
  assert.match(html, /ALLOW/);
  assert.match(html, /0\.0%/);
});

test('upload control is keyboard reachable and submit is disabled without a file', () => {
  const html = renderToStaticMarkup(React.createElement(Page));
  assert.match(html, /role="button" tabindex="0" aria-disabled="false"/);
  assert.match(html, /type="submit"[^>]*disabled=""/);
  assert.match(html, /aria-busy="false"/);
});
