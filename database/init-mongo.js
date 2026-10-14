// EASP MongoDB initialization script - Phase 0
// Runs automatically on first container start (via docker-entrypoint-initdb.d).
// Phase 0 only creates the application database and a placeholder collection
// to confirm persistence. No audit / append-only collections yet -
// that belongs to the later Audit Logging phase.

db = db.getSiblingDB('easp');

db.createCollection('_phase0_bootstrap');

db._phase0_bootstrap.insertOne({
  note: 'EASP Phase 0 database initialized.',
  phase: 'phase-0',
  createdAt: new Date()
});

print('[init-mongo] EASP Phase 0 database bootstrap complete.');
