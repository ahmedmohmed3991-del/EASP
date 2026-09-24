import API from './api';

/**
 * ============================================================================
 * VERIFIED against the real backend (EASP-feature-p01-010-scaffold-folders,
 * backend/EASP.Api, .NET 8 / ASP.NET Core Identity + EF Core).
 * ============================================================================
 *
 * GET /api/AuditLogs  (AuditLogsController, [Authorize] — any authenticated
 * role, no role restriction found server-side)
 *   Query params: userId, action, from, to, page, pageSize
 *   Response: { items: AuditLogDto[], totalCount, page, pageSize }
 *   AuditLogDto: { id, timestamp, correlationId, userId, userEmail, action,
 *                  resource, ipAddress, statusCode, executionTimeMs,
 *                  detailsJson }
 *
 * There is no separate "incidents" table or endpoint. Every security
 * decision (risk fusion, AI text/voice analysis) is written into this same
 * AuditLogs table by RiskEngineService / SecurityEngineService, tagged with
 * one of the INCIDENT_ACTIONS below, with the decision details serialized
 * into `detailsJson`. "Incidents" here is a filtered, parsed view of the
 * audit log — not a separate invented endpoint.
 *
 * There is NO evaluation-results / metrics endpoint or table anywhere in
 * this backend (confirmed: no controller, no DbSet, nothing registered in
 * Program.cs). This lines up with the roadmap — Phase 13 (final measurement)
 * hasn't been implemented yet. getEvaluationResults() below does not call
 * anything; it returns null so the UI shows "No measured data available"
 * (T-P11-054) rather than fabricating an endpoint that doesn't exist.
 * ============================================================================
 */

const AUDIT_LOGS_ENDPOINT = '/api/AuditLogs';

// Action values written by RiskEngineService.cs / SecurityEngineService.cs
// that represent an actual security decision (as opposed to e.g. AUTH_LOGIN).
const INCIDENT_ACTIONS = ['RISK_EVALUATION', 'AI_TEXT_ANALYSIS', 'AI_VOICE_ANALYSIS'];

/**
 * Fetches a page of raw audit log entries.
 * Returns null on any failure (network, auth) so callers can render the
 * "No measured data available" / empty-state fallback instead of crashing.
 */
export async function getAuditLogs(params = {}) {
  try {
    const response = await API.get(AUDIT_LOGS_ENDPOINT, { params });
    // Response is the PagedResult<AuditLogDto> shape: { items, totalCount, page, pageSize }
    return response.data;
  } catch (err) {
    return null;
  }
}

function parseDetails(detailsJson) {
  if (!detailsJson) return null;
  try {
    return JSON.parse(detailsJson);
  } catch {
    return null;
  }
}

/**
 * Derives "incidents" (detected events) from the audit log, since the
 * backend does not persist them separately. Each entry's `detailsJson` is
 * parsed defensively — its shape differs between RiskEngineService (rich:
 * compositeRiskScore, action, reasons, policyName) and SecurityEngineService
 * (sparse: just { decision }) — so several fields will legitimately come
 * back as null/undefined for some rows. Those render via MeasuredValue as
 * "No measured data available" rather than being guessed at.
 *
 * @param {object} [options]
 * @param {string} [options.userId] - if provided, scopes the query to one
 *   user's own audit entries (server-side filter via the existing `userId`
 *   query param). This is a UI convenience, not a security boundary: the
 *   backend does not enforce that a caller may only request their own
 *   userId, so this filtering is trivially bypassable and does not replace
 *   the server-side authorization that Phase 11's review task (T-P11-051)
 *   still needs to add.
 */
export async function getIncidents({ userId } = {}) {
  const params = { pageSize: 100 };
  if (userId) params.userId = userId;

  const page = await getAuditLogs(params);
  if (!page || !Array.isArray(page.items)) return null;

  return page.items
    .filter((log) => INCIDENT_ACTIONS.includes(log.action))
    .map((log) => {
      const details = parseDetails(log.detailsJson);
      return {
        id: log.id,
        timestamp: log.timestamp,
        userId: log.userId,
        userEmail: log.userEmail,
        detectedEvent: log.action,
        // Only present for RISK_EVALUATION entries; AI_TEXT_ANALYSIS /
        // AI_VOICE_ANALYSIS entries do not include it.
        riskScore: details?.compositeRiskScore ?? null,
        // RiskEngineService serializes this as `action`; SecurityEngineService
        // serializes it as `decision` — both mean the same thing (the
        // enforced ALLOW/FLAG/ESCALATE/BLOCK outcome).
        policyAction: details?.action ?? details?.decision ?? null,
        // Only RISK_EVALUATION entries carry explainability reasons; the
        // AI analysis entries carry no per-model output in the audit trail.
        reasons: Array.isArray(details?.reasons) ? details.reasons.join('; ') : null,
      };
    });
}

/**
 * No evaluation-results endpoint exists in this backend. Intentionally does
 * not call the network — see the file header comment. Returns null so
 * callers render "No measured data available".
 */
export async function getEvaluationResults() {
  return null;
}
