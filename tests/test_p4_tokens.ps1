$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:5000"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Running Phase 4 Automated Tests (Tokens) " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Login to get JWT
Write-Host "`n[P4-01] Authenticating user to obtain JWT..." -ForegroundColor Yellow
$userEmail = "p4_test_$(Get-Random)@easp.local"
$regPayload = @{
    fullName = "Phase 4 Tester"
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

# 2. Tokenize sensitive data
Write-Host "`n[P4-02] Testing POST /api/tokens/tokenize..." -ForegroundColor Yellow
$tokenizePayload = @{
    originalValue = "ceo.confidential@easp-enterprise.com"
    tokenType = "EMAIL_ADDRESS"
    ttlMinutes = 15
} | ConvertTo-Json

$tokenizeRes = Invoke-RestMethod -Uri "$baseUrl/api/tokens/tokenize" -Method Post -Headers $headers -Body $tokenizePayload
Write-Host "  Token generated: $($tokenizeRes.token)" -ForegroundColor Green
Write-Host "  Token type: $($tokenizeRes.tokenType), TTL: $($tokenizeRes.ttlMinutes) mins" -ForegroundColor Gray

if (-not $tokenizeRes.token.StartsWith("TOK_EMAIL_ADDRESS_")) {
    throw "Surrogate token format invalid: $($tokenizeRes.token)"
}

$surrogateToken = $tokenizeRes.token

# 3. Detokenize sensitive data (valid)
Write-Host "`n[P4-03] Testing POST /api/tokens/detokenize (Active token)..." -ForegroundColor Yellow
$detokenizePayload = @{
    token = $surrogateToken
} | ConvertTo-Json

$detokenizeRes = Invoke-RestMethod -Uri "$baseUrl/api/tokens/detokenize" -Method Post -Headers $headers -Body $detokenizePayload
Write-Host "  Detokenized value: $($detokenizeRes.originalValue)" -ForegroundColor Green
Write-Host "  IsExpired: $($detokenizeRes.isExpired)" -ForegroundColor Gray

if ($detokenizeRes.originalValue -ne "ceo.confidential@easp-enterprise.com" -or $detokenizeRes.isExpired -ne $false) {
    throw "Detokenize failed to retrieve original sensitive value!"
}

# 4. Revoke token
Write-Host "`n[P4-04] Testing POST /api/tokens/revoke..." -ForegroundColor Yellow
$revokePayload = @{
    token = $surrogateToken
} | ConvertTo-Json

$revokeRes = Invoke-RestMethod -Uri "$baseUrl/api/tokens/revoke" -Method Post -Headers $headers -Body $revokePayload
Write-Host "  Revoke response: $($revokeRes.message)" -ForegroundColor Green

# 5. Detokenize after revocation (should return [EXPIRED_OR_REVOKED])
Write-Host "`n[P4-05] Testing POST /api/tokens/detokenize (Revoked token)..." -ForegroundColor Yellow
$revokedDetokRes = Invoke-RestMethod -Uri "$baseUrl/api/tokens/detokenize" -Method Post -Headers $headers -Body $detokenizePayload
Write-Host "  Detokenized value: $($revokedDetokRes.originalValue)" -ForegroundColor Green
Write-Host "  IsExpired: $($revokedDetokRes.isExpired)" -ForegroundColor Gray

if ($revokedDetokRes.originalValue -ne "[EXPIRED_OR_REVOKED]" -or $revokedDetokRes.isExpired -ne $true) {
    throw "Detokenize after revocation should return [EXPIRED_OR_REVOKED] with isExpired=true!"
}

# 6. Trigger sweep
Write-Host "`n[P4-06] Testing POST /api/tokens/sweep (Manual cleanup sweep)..." -ForegroundColor Yellow
$sweepRes = Invoke-RestMethod -Uri "$baseUrl/api/tokens/sweep" -Method Post -Headers $headers
Write-Host "  Sweep response: $($sweepRes.message) (Purged: $($sweepRes.purgedTokensCount))" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " ALL PHASE 4 TESTS PASSED SUCCESSFULLY! " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
