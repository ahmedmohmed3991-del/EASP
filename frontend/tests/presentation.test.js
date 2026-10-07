import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { buildSync } from 'esbuild';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

const require = createRequire(import.meta.url);
const compiled = buildSync({
  entryPoints: [fileURLToPath(new URL('../src/App.jsx', import.meta.url))],
  bundle: true, write: false, platform: 'node', format: 'cjs',
  external: ['react'], define: { 'import.meta.env': '{}' }
}).outputFiles[0].text;

function renderApp(role) {
  const module = { exports: {} };
  const storage = { getItem: key => key === 'easp_user' && role
    ? JSON.stringify({ role, email: 'presentation-test@example.test' }) : null };
  new Function('require', 'module', 'exports', 'localStorage', compiled)(require, module, module.exports, storage);
  return renderToStaticMarkup(React.createElement(module.exports.default));
}

test('login retains labelled credential fields, demo selection and submit control', () => {
  const html = renderApp();
  assert.match(html, /for="login-email"/);
  assert.match(html, /id="login-email"[^>]*type="email"/);
  assert.match(html, /for="login-password"/);
  assert.match(html, /id="login-password"[^>]*type="password"/);
  assert.match(html, /Sign In to EASP/);
  for (const label of ['Employee', 'Analyst (SOC)', 'Administrator']) assert.ok(html.includes(label));
});

test('employee workspace preserves restricted navigation and default prompt page', () => {
  const html = renderApp('Employee');
  for (const label of ['Prompt security', 'Voice intelligence', 'System health']) assert.ok(html.includes(label));
  for (const label of ['Incident desk', 'Audit trail', 'Policy rules', 'Security overview']) assert.ok(!html.includes(label));
  assert.match(html, /aria-current="page"/);
  assert.match(html, /aria-expanded="false" aria-controls="workspace-navigation"/);
  assert.match(html, /id="prompt-input"/);
});

test('analyst and administrator retain all existing workspace destinations', () => {
  for (const role of ['Analyst', 'Administrator']) {
    const html = renderApp(role);
    for (const label of ['Prompt security', 'Voice intelligence', 'System health', 'Incident desk', 'Audit trail', 'Policy rules', 'Security overview']) assert.ok(html.includes(label), `${role}: ${label}`);
    assert.match(html, /Log out/);
  }
});
