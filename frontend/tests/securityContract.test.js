import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateSecurityResponse } from '../src/services/securityContract.js';

test('valid zero scores are accepted; missing result fields never imply ALLOW/LOW', () => {
  const response = { status: 'success', data: { action: 'ALLOW', risk: { score: 0, level: 'LOW' },
    dlp: { entitiesDetected: [] }, socialEngineering: { score: 0, threatsDetected: [] },
    voiceDeepfake: { spoofScore: 0, isDeepfake: false }, transcription: { transcript: '' } } };
  assert.equal(validateSecurityResponse(response, true), response);
  for (const field of ['action', 'risk', 'dlp', 'socialEngineering', 'voiceDeepfake', 'transcription']) {
    const incomplete = structuredClone(response); delete incomplete.data[field];
    assert.throws(() => validateSecurityResponse(incomplete, true));
  }
  assert.throws(() => validateSecurityResponse({ status: 'success', data: {} }, false));
});
