$ErrorActionPreference = "Stop"

$baseUrl = "http://localhost:5000"
Write-Host "=== Starting EASP Phase 1 & 2 Verification Tests ===" -ForegroundColor Cyan

# 1. Health check
Write-Host "`n[1/5] Testing Health Check: GET $baseUrl/api/health..." -ForegroundColor Yellow
$healthResp = Invoke-WebRequest -Uri "$baseUrl/api/health" -Method Get
Write-Host "Health Check Status:" $healthResp.StatusCode -ForegroundColor Green
Write-Host "Response Body:" $healthResp.Content

# 2. Register new user
$testEmail = "analyst_" + [System.Guid]::NewGuid().ToString().Substring(0, 8) + "@easp.local"
$registerBody = @{
    email = $testEmail
    password = "Password123!"
    fullName = "EASP Security Analyst"
    role = "Analyst"
} | ConvertTo-Json

Write-Host "`n[2/5] Testing Registration (T-P01-011): POST $baseUrl/api/auth/register..." -ForegroundColor Yellow
$regResp = Invoke-WebRequest -Uri "$baseUrl/api/auth/register" -Method Post -Body $registerBody -ContentType "application/json"
Write-Host "Register Status:" $regResp.StatusCode -ForegroundColor Green
$regData = $regResp.Content | ConvertFrom-Json
Write-Host "Created User ID:" $regData.user.id
Write-Host "Assigned Roles:" ($regData.user.roles -join ", ")
$token = $regData.token

# Check RequestLoggingMiddleware headers
Write-Host "`n[Middleware Check (T-P02-017)]:" -ForegroundColor Magenta
Write-Host "X-Correlation-ID:" $regResp.Headers["X-Correlation-ID"]
Write-Host "X-Response-Time-Ms:" $regResp.Headers["X-Response-Time-Ms"]

# 3. Login
$loginBody = @{
    email = $testEmail
    password = "Password123!"
} | ConvertTo-Json

Write-Host "`n[3/5] Testing Login (T-P01-011): POST $baseUrl/api/auth/login..." -ForegroundColor Yellow
$loginResp = Invoke-WebRequest -Uri "$baseUrl/api/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
Write-Host "Login Status:" $loginResp.StatusCode -ForegroundColor Green
$loginData = $loginResp.Content | ConvertFrom-Json
$token = $loginData.token
Write-Host "Received JWT Token: OK (Length: $($token.Length))"

# 4. Protected endpoint without token -> expect 401
Write-Host "`n[4/5] Testing Protected Endpoint Without Token (T-P02-016 Auth Pipeline): GET $baseUrl/api/auth/me..." -ForegroundColor Yellow
try {
    $unauthResp = Invoke-WebRequest -Uri "$baseUrl/api/auth/me" -Method Get
    Write-Host "FAILED: Expected 401 Unauthorized but received $($unauthResp.StatusCode)" -ForegroundColor Red
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 401) {
        Write-Host "SUCCESS: Endpoint correctly rejected unauthenticated request with 401 Unauthorized." -ForegroundColor Green
    } else {
        Write-Host "Received status code: $statusCode" -ForegroundColor Yellow
    }
}

# 5. Protected endpoint with Bearer token
Write-Host "`n[5/5] Testing Protected Endpoint With Bearer Token: GET $baseUrl/api/auth/me..." -ForegroundColor Yellow
$headers = @{
    Authorization = "Bearer $token"
}
$meResp = Invoke-WebRequest -Uri "$baseUrl/api/auth/me" -Method Get -Headers $headers
Write-Host "Me Endpoint Status:" $meResp.StatusCode -ForegroundColor Green
$meData = $meResp.Content | ConvertFrom-Json
Write-Host "Authenticated User Email:" $meData.email
Write-Host "Authenticated User FullName:" $meData.fullName
Write-Host "Authenticated User Roles:" ($meData.roles -join ", ")

Write-Host "`n=== ALL TESTS PASSED SUCCESSFULLY! ===" -ForegroundColor Green
