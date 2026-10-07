using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using EASP.API.Services;

namespace EASP.API.Controllers
{
    [ApiController]
    [Route("api/v1/security")]
    [Authorize]
    public class SecurityController : ControllerBase
    {
        private readonly AiServiceClient _ai;
        private readonly RiskEngine _risk;
        private readonly PolicyEngine _policy;
        private readonly TokenService _token;
        private readonly ILogger<SecurityController> _logger;

        public SecurityController(AiServiceClient ai, RiskEngine risk, PolicyEngine policy, TokenService token, ILogger<SecurityController> logger)
        {
            _ai = ai;
            _risk = risk;
            _policy = policy;
            _token = token;
            _logger = logger;
        }

        private int GetUserId() => int.Parse(User.FindFirst("userId")!.Value);
        private string GetUsername() => User.FindFirst("username")?.Value ?? "unknown";
        private string GetRole() => User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value ?? "Employee";
        private string GetIp() => HttpContext.Connection.RemoteIpAddress?.ToString() ?? "unknown";

        private static string ProtectMatchedText(string original, JsonElement dlpData, bool required = false)
        {
            if (dlpData.ValueKind != JsonValueKind.Object) return "[DLP OUTPUT UNAVAILABLE]";
            var hasMatches = (dlpData.TryGetProperty("has_sensitive_data", out var sensitive) && sensitive.ValueKind == JsonValueKind.True) ||
                (dlpData.TryGetProperty("entities", out var entities) && entities.ValueKind == JsonValueKind.Array && entities.GetArrayLength() > 0) ||
                (dlpData.TryGetProperty("mappings", out var mappings) && mappings.ValueKind == JsonValueKind.Array && mappings.GetArrayLength() > 0);
            if (!hasMatches && !required) return original;
            return dlpData.TryGetProperty("redacted_text", out var redacted) && redacted.ValueKind == JsonValueKind.String
                ? redacted.GetString()! : "[SENSITIVE CONTENT REDACTED]";
        }

        // POST /api/v1/security/scan-prompt
        [HttpPost("scan-prompt")]
        public async Task<IActionResult> ScanPrompt([FromBody] ScanPromptRequest req)
        {
            if (string.IsNullOrWhiteSpace(req.Prompt) || req.Prompt.Length < 1)
                return BadRequest(new { status = "error", error = "prompt is required" });

            try
            {
                var userId = GetUserId();
                var username = GetUsername();
                var role = GetRole();
                var ip = GetIp();

                // Step 1: DLP Scan
                var dlpResult = await _ai.ScanDlpAsync(req.Prompt, userId);
                if (!dlpResult.Success) return StatusCode(503, new { status = "error", error = "DLP analysis unavailable or invalid" });
                var dlpData = dlpResult.Data;

                // Step 2: Save token mappings
                if (dlpData.TryGetProperty("mappings", out var mappings) && mappings.ValueKind == JsonValueKind.Array)
                {
                    foreach (var m in mappings.EnumerateArray())
                    {
                        await _token.SaveTokenMappingAsync(
                            m.GetProperty("token_id").GetString()!,
                            m.GetProperty("entity_type").GetString()!,
                            m.GetProperty("original_value").GetString()!,
                            userId
                        );
                    }
                }

                // Step 3: NLP Social Engineering Classification
                var nlpResult = await _ai.ClassifyNlpAsync(req.Prompt);
                if (!nlpResult.Success) return StatusCode(503, new { status = "error", error = "NLP analysis unavailable or invalid" });
                var nlpData = nlpResult.Data;

                // Step 4: Risk Fusion
                var dlpScore = dlpData.TryGetProperty("sensitivity_score", out var ds) ? ds.GetDouble() : 0.0;
                var socialScore = nlpData.TryGetProperty("social_engineering_score", out var ss) ? ss.GetDouble() : 0.0;
                var riskAssessment = _risk.CalculateRisk(
                    voiceScore: 0.0,
                    socialScore: socialScore,
                    dlpScore: dlpScore,
                    isVoiceApplicable: false,
                    hasSocialError: !nlpResult.Success,
                    hasDlpError: !dlpResult.Success
                );

                // Step 5: Policy Decision
                var dlpFindings = PolicyEngine.ProjectDlpEntities(dlpData.TryGetProperty("entities", out var ent) ? ent : null);
                var policyDecision = await _policy.EvaluatePolicyAsync(
                    userId, username, role, ip,
                    riskAssessment.FusedRisk, riskAssessment.Level,
                    dlpFindings, riskAssessment.ContributingFactors,
                    "PROMPT_SCAN"
                );

                // Step 6: Final prompt
                var finalPrompt = policyDecision.Action switch
                {
                    "BLOCK" => "[BLOCKED BY EASP SECURITY POLICY: HIGH RISK CONTENT DETECTED]",
                    _ => ProtectMatchedText(req.Prompt, dlpData, policyDecision.RequireDlpRedaction || policyDecision.Action == "REDACT")
                };

                var hasSensitive = dlpData.TryGetProperty("has_sensitive_data", out var hs) && hs.GetBoolean();
                var tokensGenerated = mappings.ValueKind == JsonValueKind.Array ? mappings.GetArrayLength() : 0;
                var threats = nlpData.TryGetProperty("threats_detected", out var td) ? td : default;

                return Ok(new
                {
                    status = "success",
                    data = new
                    {
                        action = policyDecision.Action,
                        policyTriggered = policyDecision.PolicyName,
                        risk = new
                        {
                            scoringProfile = riskAssessment.ScoringProfile,
                            score = riskAssessment.FusedRisk,
                            level = riskAssessment.Level,
                            contributingFactors = riskAssessment.ContributingFactors
                        },
                        dlp = new
                        {
                            hasSensitiveData = hasSensitive,
                            entitiesDetected = dlpFindings,
                            tokensGenerated
                        },
                        socialEngineering = new
                        {
                            score = socialScore,
                            threatsDetected = threats.ValueKind != JsonValueKind.Undefined ? threats : default
                        },
                        processedPrompt = finalPrompt,
                        incidentId = policyDecision.IncidentId.HasValue ? $"INC-{policyDecision.IncidentId.Value:D4}" : null,
                        auditLogId = policyDecision.AuditLogId
                    }
                });
            }
            catch (Exception ex)
            {
                _logger.LogError("Prompt security scan failed ({ErrorType})", ex.GetType().Name);
                return StatusCode(500, new { status = "error", error = "Failed to process prompt security scan" });
            }
        }

        // POST /api/v1/security/analyze-call
        [HttpPost("analyze-call")]
        [RequestSizeLimit(26 * 1024 * 1024)]
        public async Task<IActionResult> AnalyzeCall(IFormFile audio, [FromForm] string? speakerProfileId = null)
        {
            if (audio == null || audio.Length == 0 || audio.Length > 25 * 1024 * 1024)
                return BadRequest(new { status = "error", error = "Audio file upload is required (field name: \"audio\")" });

            try
            {
                var userId = GetUserId();
                var username = GetUsername();
                var role = GetRole();
                var ip = GetIp();

                byte[] audioData;
                using (var ms = new MemoryStream())
                {
                    await audio.CopyToAsync(ms);
                    audioData = ms.ToArray();
                }

                // Step 1: Audio Pipeline
                var pipelineResult = await _ai.AnalyzeAudioPipelineAsync(audioData, audio.FileName ?? "call.wav", speakerProfileId);
                if (!pipelineResult.Success) return StatusCode(503, new { status = "error", error = "Audio analysis unavailable or invalid" });
                var pd = pipelineResult.Data;

                var vd = pd.TryGetProperty("voice_deepfake", out var v) ? v : default;
                var voiceScore = vd.ValueKind != JsonValueKind.Undefined && vd.TryGetProperty("spoof_score", out var vs) ? vs.GetDouble() : 0.15;
                var isDeepfake = vd.ValueKind != JsonValueKind.Undefined && vd.TryGetProperty("is_deepfake", out var isd) && isd.GetBoolean();
                var inferenceMode = vd.ValueKind != JsonValueKind.Undefined && vd.TryGetProperty("inference_engine", out var ie) ? ie.GetString() : "RawNet2 DSP Acoustic Analyzer";

                var tr = pd.TryGetProperty("transcription", out var t) ? t : default;
                var transcript = tr.ValueKind != JsonValueKind.Undefined && tr.TryGetProperty("transcript", out var trText) ? trText.GetString() ?? "" : "";

                var se = pd.TryGetProperty("social_engineering", out var s) ? s : default;
                var socialScore = se.ValueKind != JsonValueKind.Undefined && se.TryGetProperty("social_engineering_score", out var ses) ? ses.GetDouble() : 0.10;
                var threats = se.ValueKind != JsonValueKind.Undefined && se.TryGetProperty("threats_detected", out var td) ? td : default;

                var dlpData = pd.TryGetProperty("dlp", out var dlp) ? dlp : default;
                var dlpScore = dlpData.ValueKind != JsonValueKind.Undefined && dlpData.TryGetProperty("sensitivity_score", out var dlps) ? dlps.GetDouble() : 0.0;
                var safeEntities = PolicyEngine.ProjectDlpEntities(dlpData.ValueKind == JsonValueKind.Object && dlpData.TryGetProperty("entities", out var audioEntities) ? audioEntities : null);
                transcript = ProtectMatchedText(transcript, dlpData);

                // Step 2: Save DLP token mappings
                if (dlpData.ValueKind != JsonValueKind.Undefined && dlpData.TryGetProperty("mappings", out var mappings) && mappings.ValueKind == JsonValueKind.Array)
                {
                    foreach (var m in mappings.EnumerateArray())
                    {
                        await _token.SaveTokenMappingAsync(
                            m.GetProperty("token_id").GetString()!,
                            m.GetProperty("entity_type").GetString()!,
                            m.GetProperty("original_value").GetString()!,
                            userId
                        );
                    }
                }

                // Step 3: Risk Fusion
                var profile = pd.TryGetProperty("speaker_frequency_profile", out var profileData) ? profileData : (JsonElement?)null;
                var impersonation = profile.HasValue && profile.Value.TryGetProperty("evaluation", out var evaluation) &&
                    AiServiceClient.Score(evaluation, "impersonation_risk_score") ? evaluation.GetProperty("impersonation_risk_score").GetDouble() : 0.0;
                var riskAssessment = _risk.CalculateRisk(Math.Max(voiceScore, impersonation), socialScore, dlpScore);

                // Step 4: Policy Decision
                var policyDecision = await _policy.EvaluatePolicyAsync(
                    userId, username, role, ip,
                    riskAssessment.FusedRisk, riskAssessment.Level,
                    null, riskAssessment.ContributingFactors, "CALL_ANALYSIS");

                return Ok(new
                {
                    status = "success",
                    data = new
                    {
                        policyAction = policyDecision.Action,
                        riskLevel = riskAssessment.Level,
                        riskScore = riskAssessment.FusedRisk,
                        policyReason = $"Triggered policy {policyDecision.PolicyName} with fused risk {riskAssessment.FusedRisk:F2} ({riskAssessment.Level})",
                        incidentId = policyDecision.IncidentId.HasValue ? $"INC-{policyDecision.IncidentId.Value:D4}" : null,
                        transcript,
                        transcription = new { transcript, language = tr.TryGetProperty("language", out var language) ? language.GetString() : null, durationSeconds = tr.TryGetProperty("duration_seconds", out var duration) ? duration.GetDouble() : 0 },
                        socialEngineering = new { score = socialScore, threatsDetected = threats },
                        speakerFrequencyProfile = profile,
                        voiceAnalysis = new
                        {
                            spoofScore = voiceScore,
                            isSynthetic = isDeepfake,
                            inferenceMode = inferenceMode,
                            spectralFeatures = (object?)null
                        },
                        nlpAnalysis = new
                        {
                            socialEngineeringScore = socialScore,
                            threatCategories = threats
                        },
                        action = policyDecision.Action,
                        policyTriggered = policyDecision.PolicyName,
                        risk = new { scoringProfile = riskAssessment.ScoringProfile,
                            score = riskAssessment.FusedRisk, level = riskAssessment.Level, contributingFactors = riskAssessment.ContributingFactors },
                        voiceDeepfake = new { spoofScore = voiceScore, isDeepfake, inferenceEngine = inferenceMode },
                        dlp = new { sensitivityScore = dlpScore, entitiesDetected = safeEntities },
                        auditLogId = policyDecision.AuditLogId
                    }
                });
            }
            catch (Exception ex)
            {
                _logger.LogError("Call audio analysis failed ({ErrorType})", ex.GetType().Name);
                return StatusCode(500, new { status = "error", error = "Failed to analyze call audio" });
            }
        }

        [HttpGet("speaker-profiles")]
        public async Task<IActionResult> SpeakerProfiles()
        {
            var result = await _ai.GetSpeakerProfilesAsync();
            return result.Success ? Ok(new { status = "success", data = result.Data }) : StatusCode(503, new { status = "error", error = "AI service unavailable" });
        }

        // POST /api/v1/security/restore-token
        [HttpPost("restore-token")]
        public async Task<IActionResult> RestoreToken([FromBody] RestoreTokenRequest req)
        {
            if (string.IsNullOrWhiteSpace(req.TokenId))
                return BadRequest(new { status = "error", error = "tokenId is required" });

            var result = await _token.RestoreTokenAsync(
                req.TokenId, GetUserId(), GetUsername(), GetRole(), GetIp());

            if (!result.Success)
                return StatusCode(result.StatusCode, new { status = "error", error = result.Error });

            return Ok(new
            {
                status = "success",
                data = new { tokenId = result.TokenId, entityType = result.EntityType, originalValue = result.OriginalValue, expiresAt = result.ExpiresAt }
            });
        }

        // POST /api/v1/security/evaluate-risk
        [HttpPost("evaluate-risk")]
        public IActionResult EvaluateRisk([FromBody] EvaluateRiskRequest req)
        {
            if (new[] { req.VoiceScore, req.SocialScore, req.DlpScore }.Any(x => !double.IsFinite(x) || x < 0 || x > 1))
                return BadRequest(new { status = "error", error = "Scores must be in [0,1]" });
            var result = _risk.CalculateRisk(req.VoiceScore, req.SocialScore, req.DlpScore);
            return Ok(new { status = "success", data = result });
        }
    }

    public record ScanPromptRequest(string Prompt);
    public record RestoreTokenRequest(string TokenId);
    public record EvaluateRiskRequest(double VoiceScore = 0.0, double SocialScore = 0.0, double DlpScore = 0.0);
}
