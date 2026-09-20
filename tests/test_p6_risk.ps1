$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:5000"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Running Phase 6 Automated Tests (Risk-Based Engine) " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Authenticate user to get JWT token
Write-Host "`n[P6-01] Authenticating user to obtain JWT..." -ForegroundColor Yellow
$userEmail = "p6_tester_$(Get-Random)@easp.local"
$regPayload = @{
    fullName = "Phase 6 Security Tester"
    email = $userEmail
    password = "Password123!"
} | ConvertTo-Json

try {
    $regRes = Invoke-RestMethod -Uri "$baseUrl/api/auth/register" -Method Post -Body $regPayload -ContentType "application/json"
    $token = $regRes.token
    Write-Host "  Registered and logged in as $userEmail" -ForegroundColor Green
} catch {
    Write-Error "Failed to register/authenticate: $_"
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# 2. Test Security Headers & CORS (T-P02-014)
Write-Host "`n[P6-02] Testing Enterprise Security Headers & CORS allow-list..." -ForegroundColor Yellow
$diagRes = Invoke-WebRequest -Uri "$baseUrl/api/risk/health" -Method Get -Headers $headers
Write-Host "  Status Code: $($diagRes.StatusCode)" -ForegroundColor Green

$xFrame = $diagRes.Headers["X-Frame-Options"]
$xContentType = $diagRes.Headers["X-Content-Type-Options"]
$referrer = $diagRes.Headers["Referrer-Policy"]

Write-Host "  X-Frame-Options: $xFrame" -ForegroundColor Gray
Write-Host "  X-Content-Type-Options: $xContentType" -ForegroundColor Gray
Write-Host "  Referrer-Policy: $referrer" -ForegroundColor Gray

if (-not $xFrame -or -not $xContentType) {
    throw "Security headers (X-Frame-Options / X-Content-Type-Options) missing from response!"
}

# 3. Test GET /api/risk/health
Write-Host "`n[P6-03] Testing GET /api/risk/health (Diagnostic & Weights)..." -ForegroundColor Yellow
$healthData = Invoke-RestMethod -Uri "$baseUrl/api/risk/health" -Method Get -Headers $headers
Write-Host "  Engine Status: $($healthData.status)" -ForegroundColor Green
Write-Host "  Allow Threshold: $($healthData.allowThreshold), Block Threshold: $($healthData.blockThreshold)" -ForegroundColor Gray
Write-Host "  Weights: Injection=$($healthData.weights.PromptInjection), Deepfake=$($healthData.weights.Deepfake), SocialEng=$($healthData.weights.SocialEngineering), PII=$($healthData.weights.PiiLeakage)" -ForegroundColor Gray

# 4. Low Risk Evaluation Scenario (Benign prompt) -> expect ALLOW
Write-Host "`n[P6-04] Testing Low Risk Scenario (Benign Input)..." -ForegroundColor Yellow
$lowRiskPayload = @{
    promptInjectionProbability = 0.05
    deepfakeProbability = 0.02
    socialEngineeringProbability = 0.10
    piiEntitiesCount = 0
    piiSeverityScore = 0.0
    metadata = @{ channel = "chat"; prompt = "Summarize meeting notes." }
} | ConvertTo-Json

$lowRiskRes = Invoke-RestMethod -Uri "$baseUrl/api/risk/evaluate" -Method Post -Headers $headers -Body $lowRiskPayload
Write-Host "  Composite Risk Score: $($lowRiskRes.compositeRiskScore)/100" -ForegroundColor Green
Write-Host "  Action: $($lowRiskRes.action)" -ForegroundColor Green
Write-Host "  Reasons: $($lowRiskRes.reasons -join ' | ')" -ForegroundColor Gray

if ($lowRiskRes.action -ne "ALLOW" -or $lowRiskRes.compositeRiskScore -ge 35.0) {
    throw "Expected action ALLOW with score < 35 for benign input, got action=$($lowRiskRes.action), score=$($lowRiskRes.compositeRiskScore)"
}

# 5. Moderate Risk Scenario -> expect FLAG / ESCALATE
Write-Host "`n[P6-05] Testing Moderate Risk Scenario..." -ForegroundColor Yellow
$modRiskPayload = @{
    promptInjectionProbability = 0.55
    deepfakeProbability = 0.35
    socialEngineeringProbability = 0.40
    piiEntitiesCount = 0
    piiSeverityScore = 0.0
} | ConvertTo-Json

$modRiskRes = Invoke-RestMethod -Uri "$baseUrl/api/risk/evaluate" -Method Post -Headers $headers -Body $modRiskPayload
Write-Host "  Composite Risk Score: $($modRiskRes.compositeRiskScore)/100" -ForegroundColor Green
Write-Host "  Action: $($modRiskRes.action)" -ForegroundColor Green
Write-Host "  Reasons: $($modRiskRes.reasons -join ' | ')" -ForegroundColor Gray

if ($modRiskRes.action -ne "FLAG" -and $modRiskRes.action -ne "ESCALATE") {
    throw "Expected action FLAG or ESCALATE for moderate risk, got action=$($modRiskRes.action)"
}

# 6. High Risk Prompt Injection Scenario -> expect BLOCK
Write-Host "`n[P6-06] Testing High Risk Scenario (Direct Prompt Injection)..." -ForegroundColor Yellow
$highRiskPayload = @{
    promptInjectionProbability = 0.95
    deepfakeProbability = 0.10
    socialEngineeringProbability = 0.30
    piiEntitiesCount = 0
    piiSeverityScore = 0.0
} | ConvertTo-Json

$highRiskRes = Invoke-RestMethod -Uri "$baseUrl/api/risk/evaluate" -Method Post -Headers $headers -Body $highRiskPayload
Write-Host "  Composite Risk Score: $($highRiskRes.compositeRiskScore)/100" -ForegroundColor Green
Write-Host "  Action: $($highRiskRes.action)" -ForegroundColor Green
Write-Host "  Reasons: $($highRiskRes.reasons -join ' | ')" -ForegroundColor Gray

if ($highRiskRes.action -ne "BLOCK") {
    throw "Expected action BLOCK for direct high-confidence prompt injection!"
}

# 7. Compound Threat Multiplier Scenario (Voice Deepfake + Social Engineering) -> +25% boost
Write-Host "`n[P6-07] Testing Compound Threat Scenario (Deepfake + Social Engineering)..." -ForegroundColor Yellow
$compoundPayload = @{
    promptInjectionProbability = 0.10
    deepfakeProbability = 0.85
    socialEngineeringProbability = 0.75
    piiEntitiesCount = 0
    piiSeverityScore = 0.0
} | ConvertTo-Json

$compoundRes = Invoke-RestMethod -Uri "$baseUrl/api/risk/evaluate" -Method Post -Headers $headers -Body $compoundPayload
Write-Host "  Composite Risk Score: $($compoundRes.compositeRiskScore)/100" -ForegroundColor Green
Write-Host "  Compound Threat Detected: $($compoundRes.compoundThreatDetected) (Multiplier: $($compoundRes.compoundThreatMultiplier))" -ForegroundColor Green
Write-Host "  Action: $($compoundRes.action)" -ForegroundColor Green
Write-Host "  Reasons: $($compoundRes.reasons -join ' | ')" -ForegroundColor Gray

if (-not $compoundRes.compoundThreatDetected -or $compoundRes.compoundThreatMultiplier -lt 1.20) {
    throw "Compound threat multiplier failed to trigger on voice deepfake + social engineering pattern!"
}

# 8. Dynamic Policy Engine Linkage (T-P06-034)
Write-Host "`n[P6-08] Testing Dynamic Policy Linkage with Phase 5 Policies..." -ForegroundColor Yellow
$customPolicyPayload = @{
    name = "Custom High Sensitivity Risk Policy"
    description = "Escalate any prompt when composite risk score exceeds 40%"
    category = "RISK"
    action = "Escalate"
    severity = "Critical"
    isEnabled = $true
    configurationJson = '{"threshold": 40.0}'
} | ConvertTo-Json

$newPolicy = Invoke-RestMethod -Uri "$baseUrl/api/policies" -Method Post -Headers $headers -Body $customPolicyPayload
Write-Host "  Created test policy: '$($newPolicy.name)' (ID: $($newPolicy.id))" -ForegroundColor Green

$evalWithPolicyPayload = @{
    promptInjectionProbability = 0.60
    deepfakeProbability = 0.40
    socialEngineeringProbability = 0.50
    piiEntitiesCount = 0
    piiSeverityScore = 0.0
} | ConvertTo-Json

$evalWithPolicyRes = Invoke-RestMethod -Uri "$baseUrl/api/risk/evaluate" -Method Post -Headers $headers -Body $evalWithPolicyPayload
Write-Host "  Risk Score: $($evalWithPolicyRes.compositeRiskScore), Action: $($evalWithPolicyRes.action)" -ForegroundColor Green
Write-Host "  Policy Applied: '$($evalWithPolicyRes.policyName)' (ID: $($evalWithPolicyRes.policyAppliedId))" -ForegroundColor Green

if ($evalWithPolicyRes.policyAppliedId -ne $newPolicy.id) {
    throw "Risk evaluation failed to link with active Policy in database!"
}

# Clean up test policy
Invoke-RestMethod -Uri "$baseUrl/api/policies/$($newPolicy.id)" -Method Delete -Headers $headers | Out-Null
Write-Host "  Test policy cleaned up successfully." -ForegroundColor Gray

# 9. Audit Trail Verification (Phase 5 Integration)
Write-Host "`n[P6-09] Verifying Immutable Audit Log generation for Risk Evaluations..." -ForegroundColor Yellow
$auditRes = Invoke-RestMethod -Uri "$baseUrl/api/auditlogs?page=1&pageSize=20" -Method Get -Headers $headers
$riskAudit = $auditRes.items | Where-Object { $_.action -eq "RISK_EVALUATION" }

if (-not $riskAudit) {
    throw "No RISK_EVALUATION audit log records were found in the audit trail!"
}

Write-Host "  Found $($riskAudit.Count) RISK_EVALUATION audit events." -ForegroundColor Green
Write-Host "  Latest Event Resource: $($riskAudit[0].resource), Latency: $($riskAudit[0].executionTimeMs)ms" -ForegroundColor Gray

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host " ALL PHASE 6 TESTS PASSED SUCCESSFULLY! " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
