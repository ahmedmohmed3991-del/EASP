$ErrorActionPreference = "Stop"

$baseUrl = "http://localhost:5000"
Write-Host "=== Starting EASP Phase 3 (T-P03-023: DlpClient) Verification Tests ===" -ForegroundColor Cyan

# 1. Login to get token
$loginEmail = "analyst.dlp@easp.local"
$regBody = @{
    email = $loginEmail
    password = "Password123!"
    fullName = "DLP Analyst"
    role = "Analyst"
} | ConvertTo-Json

Write-Host "`n[1/3] Registering / Logging in DLP test user..." -ForegroundColor Yellow
$token = ""
try {
    $regResp = Invoke-WebRequest -Uri "$baseUrl/api/auth/register" -Method Post -Body $regBody -ContentType "application/json"
    $token = ($regResp.Content | ConvertFrom-Json).token
} catch {
    $loginBody = @{ email = $loginEmail; password = "Password123!" } | ConvertTo-Json
    $loginResp = Invoke-WebRequest -Uri "$baseUrl/api/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    $token = ($loginResp.Content | ConvertFrom-Json).token
}

Write-Host "Obtained JWT Token: OK" -ForegroundColor Green
$headers = @{
    Authorization = "Bearer $token"
}

# 2. Test DLP Analyze Endpoint
$sampleText = "Please contact me at john.doe@company.com or phone 202-555-0199. Server IP is 10.0.0.45 and card is 4111222233334444."
$analyzeBody = @{
    text = $sampleText
} | ConvertTo-Json

Write-Host "`n[2/3] Testing POST $baseUrl/api/dlp/analyze..." -ForegroundColor Yellow
$analyzeResp = Invoke-WebRequest -Uri "$baseUrl/api/dlp/analyze" -Method Post -Headers $headers -Body $analyzeBody -ContentType "application/json"
Write-Host "DLP Analyze Status:" $analyzeResp.StatusCode -ForegroundColor Green

$analyzeData = $analyzeResp.Content | ConvertFrom-Json
Write-Host "Has Sensitive Data:" $analyzeData.hasSensitiveData
Write-Host "Source Engine:" $analyzeData.sourceEngine
Write-Host "Detected Entities Count:" $analyzeData.detectedEntities.Count
foreach ($e in $analyzeData.detectedEntities) {
    Write-Host " - [$($e.entityType)] Value: $($e.value) (Confidence: $($e.confidence))" -ForegroundColor Magenta
}
Write-Host "`nMasked Output Text:" -ForegroundColor Yellow
Write-Host $analyzeData.maskedText -ForegroundColor White

if (-not $analyzeData.hasSensitiveData) {
    throw "Expected hasSensitiveData to be true!"
}

# 3. Test DLP Anonymize Endpoint
$anonymizeBody = @{
    text = "Secret email: admin@classified.mil with direct line 800-555-1234"
} | ConvertTo-Json

Write-Host "`n[3/3] Testing POST $baseUrl/api/dlp/anonymize..." -ForegroundColor Yellow
$anonResp = Invoke-WebRequest -Uri "$baseUrl/api/dlp/anonymize" -Method Post -Headers $headers -Body $anonymizeBody -ContentType "application/json"
Write-Host "DLP Anonymize Status:" $anonResp.StatusCode -ForegroundColor Green

$anonData = $anonResp.Content | ConvertFrom-Json
Write-Host "Original Text: " $anonData.originalText
Write-Host "Anonymized Text:" $anonData.anonymizedText
Write-Host "Entities Redacted Count:" $anonData.entitiesRedactedCount

Write-Host "`n=== PHASE 3 (T-P03-023) TESTS PASSED SUCCESSFULLY! ===" -ForegroundColor Green
