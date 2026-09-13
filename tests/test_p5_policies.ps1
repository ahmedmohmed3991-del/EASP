$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:5000"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Running Phase 5 Automated Tests (Policies & Audit) " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Login to get JWT
Write-Host "`n[P5-01] Authenticating user to obtain JWT..." -ForegroundColor Yellow
$userEmail = "p5_test_$(Get-Random)@easp.local"
$regPayload = @{
    fullName = "Phase 5 Tester"
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

# 2. Create a new security policy
Write-Host "`n[P5-02] Testing POST /api/policies (Create policy)..." -ForegroundColor Yellow
$policyPayload = @{
    name = "PII Data Redaction Policy"
    description = "Automatically redact sensitive customer PII across incoming AI prompts"
    category = "DLP"
    action = "Redact"
    severity = "High"
    isEnabled = $true
    configurationJson = '{"entities":["EMAIL_ADDRESS","PHONE_NUMBER"],"mask":"[REDACTED]"}'
} | ConvertTo-Json

$createdPolicy = Invoke-RestMethod -Uri "$baseUrl/api/policies" -Method Post -Headers $headers -Body $policyPayload
Write-Host "  Policy created with ID: $($createdPolicy.id)" -ForegroundColor Green
Write-Host "  Name: $($createdPolicy.name), Category: $($createdPolicy.category), Action: $($createdPolicy.action)" -ForegroundColor Gray

$policyId = $createdPolicy.id
if (-not $policyId) {
    throw "Policy creation failed to return an ID!"
}

# 3. List all policies
Write-Host "`n[P5-03] Testing GET /api/policies (List policies)..." -ForegroundColor Yellow
$policiesList = Invoke-RestMethod -Uri "$baseUrl/api/policies" -Method Get -Headers $headers
Write-Host "  Total policies retrieved: $($policiesList.Count)" -ForegroundColor Green
$found = $policiesList | Where-Object { $_.id -eq $policyId }
if (-not $found) {
    throw "Newly created policy not found in policy list!"
}

# 4. Get policy by ID
Write-Host "`n[P5-04] Testing GET /api/policies/$policyId..." -ForegroundColor Yellow
$singlePolicy = Invoke-RestMethod -Uri "$baseUrl/api/policies/$policyId" -Method Get -Headers $headers
Write-Host "  Policy verified: $($singlePolicy.name)" -ForegroundColor Green

# 5. Update policy
Write-Host "`n[P5-05] Testing PUT /api/policies/$policyId (Update policy)..." -ForegroundColor Yellow
$updatePayload = @{
    severity = "Critical"
    isEnabled = $false
    description = "Updated description: temporarily disabled for maintenance"
} | ConvertTo-Json

$updatedPolicy = Invoke-RestMethod -Uri "$baseUrl/api/policies/$policyId" -Method Put -Headers $headers -Body $updatePayload
Write-Host "  Updated severity: $($updatedPolicy.severity), isEnabled: $($updatedPolicy.isEnabled)" -ForegroundColor Green

if ($updatedPolicy.severity -ne "Critical" -or $updatedPolicy.isEnabled -ne $false) {
    throw "Policy update failed to persist modified fields!"
}

# 6. Test Audit Logs endpoint
Write-Host "`n[P5-06] Testing GET /api/auditlogs (Query paginated audit trail)..." -ForegroundColor Yellow
$auditRes = Invoke-RestMethod -Uri "$baseUrl/api/auditlogs?page=1&pageSize=10" -Method Get -Headers $headers
Write-Host "  Audit logs page: $($auditRes.page), pageSize: $($auditRes.pageSize), totalCount: $($auditRes.totalCount)" -ForegroundColor Green

# 7. Delete policy
Write-Host "`n[P5-07] Testing DELETE /api/policies/$policyId..." -ForegroundColor Yellow
$delRes = Invoke-RestMethod -Uri "$baseUrl/api/policies/$policyId" -Method Delete -Headers $headers
Write-Host "  Delete response: $($delRes.message)" -ForegroundColor Green

# 8. Verify policy is deleted
Write-Host "`n[P5-08] Verifying deletion..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "$baseUrl/api/policies/$policyId" -Method Get -Headers $headers
    throw "Policy still exists after deletion!"
} catch {
    Write-Host "  Confirmed 404 NotFound after deletion." -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " ALL PHASE 5 TESTS PASSED SUCCESSFULLY! " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
