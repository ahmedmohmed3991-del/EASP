function safeEntities(entities) {
  return (Array.isArray(entities) ? entities : []).map(e => ({
    type: e.entity_type, entity_type: e.entity_type,
    category: e.category, confidence: e.confidence, severity: e.severity
  }));
}

function protectText(original, dlp, required = false) {
  if (!dlp) return '[DLP OUTPUT UNAVAILABLE]';
  if (!required && !dlp.has_sensitive_data && !dlp.entities?.length && !dlp.mappings?.length) return original;
  return typeof dlp.redacted_text === 'string' ? dlp.redacted_text : '[SENSITIVE CONTENT REDACTED]';
}
module.exports = { safeEntities, protectText };
