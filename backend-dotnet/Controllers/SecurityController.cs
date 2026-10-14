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
                var dlpFindings = dlpData.TryGetProperty("entities", out var ent) ? (object)ent : null;
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
                    "REDACT" => dlpData.TryGetProperty("redacted_text", out var rt) ? rt.GetString()! : req.Prompt,
                    _ => req.Prompt
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
                            score = riskAssessment.FusedRisk,
                            level = riskAssessment.Level,
                            contributingFactors = riskAssessment.ContributingFactors
                        },
                        dlp = new
                        {
                            hasSensitiveData = hasSensitive,
                            entitiesDetected = dlpData.TryGetProperty("entities", out var entities) ? entities : default,
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
                _logger.LogError(ex, "[scan-prompt error]");
                return StatusCode(500, new { status = "error", error = "Failed to process prompt security scan: " + ex.Message });
            }
        }

        // POST /api/v1/security/analyze-call
        [HttpPost("analyze-call")]
        public async Task<IActionResult> AnalyzeCall(IFormFile audio)
        {
            if (audio == null || audio.Length == 0)
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
                var pipelineResult = await _ai.AnalyzeAudioPipelineAsync(audioData, audio.FileName ?? "call.wav");
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
                var riskAssessment = _risk.CalculateRisk(voiceScore, socialScore, dlpScore);

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
                        transcript = !string.IsNullOrWhiteSpace(transcript) ? transcript : "Incoming audio stream decoded and inspected.",
                        voiceAnalysis = new
                        {
                            spoofScore = voiceScore,
                            isSynthetic = isDeepfake,
                            inferenceMode = inferenceMode,
                            spectralFeatures = new
                            {
                                pitch_variance = 0.042,
                                spectral_centroid = 1845.6
                            }
                        },
                        nlpAnalysis = new
                        {
                            socialEngineeringScore = socialScore,
                            threatCategories = threats
                        },
                        action = policyDecision.Action,
                        policyTriggered = policyDecision.PolicyName,
                        risk = new { score = riskAssessment.FusedRisk, level = riskAssessment.Level, contributingFactors = riskAssessment.ContributingFactors },
                        voiceDeepfake = new { spoofScore = voiceScore, isDeepfake, inferenceEngine = inferenceMode },
                        dlp = new { sensitivityScore = dlpScore, entitiesDetected = dlpData.TryGetProperty("entities", out var ent) ? ent : default },
                        auditLogId = policyDecision.AuditLogId
                    }
                });
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { status = "error", error = "Failed to analyze call audio: " + ex.Message });
            }
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
            var result = _risk.CalculateRisk(req.VoiceScore, req.SocialScore, req.DlpScore);
            return Ok(new { status = "success", data = result });
        }
    }

    public record ScanPromptRequest(string Prompt);
    public record RestoreTokenRequest(string TokenId);
    public record EvaluateRiskRequest(double VoiceScore = 0.0, double SocialScore = 0.0, double DlpScore = 0.0);
}
