using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Security.Claims;
using System.Text;
using System.Text.Json;
using EASP.API.Controllers;
using EASP.API.Data;
using EASP.API.Models;
using EASP.API.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.IdentityModel.Tokens;

const string jwtSecret = "batch-one-test-secret-not-for-deployment-1234567890";
const string secret = "sensitive-matched-value-123";
const string tokenId = "<REDACTED_TEST_abc123>";
await using var connection = new SqliteConnection("Data Source=:memory:");
await connection.OpenAsync();
var builder = WebApplication.CreateBuilder();
builder.WebHost.UseTestServer();
builder.Configuration.AddInMemoryCollection(new Dictionary<string, string?>
{
    ["Jwt:Secret"] = jwtSecret,
    ["EncryptionKey"] = new string('a', 64)
});
var logs = new CapturedLogs();
builder.Logging.ClearProviders();
builder.Logging.AddProvider(logs);
builder.Services.AddDbContext<AppDbContext>(o => o.UseSqlite(connection));
builder.Services.AddSingleton<JwtService>();
builder.Services.AddSingleton<RiskEngine>();
builder.Services.AddScoped<TokenService>();
builder.Services.AddScoped<PolicyEngine>();
builder.Services.AddScoped<AuditService>();
var upstream = new AiResponses(secret, tokenId);
builder.Services.AddScoped(sp => new AiServiceClient(new HttpClient(upstream, false)
    { BaseAddress = new Uri("http://test-ai") }, sp.GetRequiredService<ILogger<AiServiceClient>>()));
builder.Services.AddControllers().AddApplicationPart(typeof(AuthController).Assembly);
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme).AddJwtBearer(o =>
{
    o.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuerSigningKey = true,
        IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtSecret)),
        ValidateIssuer = false,
        ValidateAudience = false,
        ClockSkew = TimeSpan.Zero
    };
    o.Events = new JwtBearerEvents { OnTokenValidated = JwtService.ValidateCurrentUserAsync };
});
builder.Services.AddAuthorization();
await using var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();
await WithDb(async db => { await db.Database.EnsureCreatedAsync(); });
await app.StartAsync();
using var client = app.GetTestClient();
var passed = 0;

async Task WithDb(Func<AppDbContext, Task> action)
{
    using var scope = app.Services.CreateScope();
    await action(scope.ServiceProvider.GetRequiredService<AppDbContext>());
}
void Check(bool condition, string message)
{
    if (!condition) throw new Exception(message);
}
async Task Run(string name, Func<Task> test)
{
    await test();
    passed++;
    Console.WriteLine($"PASS: {name}");
}
async Task<JsonElement> Json(HttpResponseMessage response, HttpStatusCode expected = HttpStatusCode.OK)
{
    Check(response.StatusCode == expected, $"Expected {expected}, got {response.StatusCode}");
    var text = await response.Content.ReadAsStringAsync();
    return string.IsNullOrWhiteSpace(text) ? default : JsonSerializer.Deserialize<JsonElement>(text);
}
Task<HttpResponseMessage> Post(string route, object body) => client.PostAsJsonAsync("/api/v1/" + route, body);
string access = "", refresh = "";
int userId = 0;

await Run("AI contract validators preserve required fields, types and score boundaries", () =>
{
    const string valid = """
        {"voice_deepfake":{"success":true,"model_loaded":true,"spoof_score":0,"is_deepfake":false},
         "transcription":{"success":true,"transcript":""},
         "social_engineering":{"social_engineering_score":1,"threats_detected":[]},
         "dlp":{"sensitivity_score":0,"redacted_text":"","entities":[],"has_sensitive_data":false,
                "mappings":[{"token_id":"id","entity_type":"KEY","original_value":"value"}]}}
        """;
    Check(AiServiceClient.ValidAudio(JsonSerializer.Deserialize<JsonElement>(valid)), "Valid boundary values rejected");
    var root = System.Text.Json.Nodes.JsonNode.Parse(valid)!;
    foreach (var section in root.AsObject())
    {
        foreach (var field in section.Value!.AsObject())
        {
            var changed = System.Text.Json.Nodes.JsonNode.Parse(valid)!;
            changed[section.Key]!.AsObject().Remove(field.Key);
            Check(!AiServiceClient.ValidAudio(JsonSerializer.Deserialize<JsonElement>(changed.ToJsonString())), $"Missing {section.Key}.{field.Key} accepted");
            changed[section.Key]![field.Key] = null;
            Check(!AiServiceClient.ValidAudio(JsonSerializer.Deserialize<JsonElement>(changed.ToJsonString())), $"Null {section.Key}.{field.Key} accepted");
        }
    }
    foreach (var score in new[] { -0.01, 1.01 })
    {
        root["voice_deepfake"]!["spoof_score"] = score;
        Check(!AiServiceClient.ValidAudio(JsonSerializer.Deserialize<JsonElement>(root.ToJsonString())), "Out-of-range score accepted");
    }
    foreach (var value in new[] { "null", "[]", "false", "42", "{}" })
        Check(!AiServiceClient.ValidAudio(JsonSerializer.Deserialize<JsonElement>(value)), "Invalid root accepted");
    return Task.CompletedTask;
});

await Run("registration/login persist expiry and issue JWT with the assigned user ID", async () =>
{
    var body = await Json(await Post("auth/register", new { username = "batch1", email = "batch1@example.test", password = "Password123!" }), HttpStatusCode.Created);
    userId = body.GetProperty("user").GetProperty("id").GetInt32();
    access = body.GetProperty("token").GetString()!;
    var jwt = app.Services.GetRequiredService<JwtService>();
    Check(jwt.ValidateToken(access)?.FindFirst("userId")?.Value == userId.ToString(), "JWT user ID must be persisted ID");
    client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", access);
    await Json(await client.GetAsync("/api/v1/auth/me"));
    body = await Json(await Post("auth/login", new { email = "batch1@example.test", password = "Password123!" }));
    access = body.GetProperty("token").GetString()!;
    refresh = body.GetProperty("refreshToken").GetString()!;
    await WithDb(async db => Check((await db.Users.FindAsync(userId))!.RefreshTokenExpiresAt > DateTime.UtcNow, "Refresh expiry missing"));
});

await Run("refresh rejects missing, unknown, expired, legacy and disabled sessions", async () =>
{
    await Json(await Post("auth/refresh", new { refreshToken = "" }), HttpStatusCode.BadRequest);
    await Json(await Post("auth/refresh", new { refreshToken = "invalid" }), HttpStatusCode.Unauthorized);
    foreach (var expiry in new DateTime?[] { DateTime.UtcNow.AddMinutes(-1), null })
    {
        await WithDb(async db => { var u = (await db.Users.FindAsync(userId))!; u.RefreshTokenExpiresAt = expiry; await db.SaveChangesAsync(); });
        await Json(await Post("auth/refresh", new { refreshToken = refresh }), HttpStatusCode.Unauthorized);
    }
    await WithDb(async db => { var u = (await db.Users.FindAsync(userId))!; u.IsActive = false; u.RefreshTokenExpiresAt = DateTime.UtcNow.AddDays(1); await db.SaveChangesAsync(); });
    await Json(await Post("auth/refresh", new { refreshToken = refresh }), HttpStatusCode.Unauthorized);
    await Json(await client.GetAsync("/api/v1/auth/me"), HttpStatusCode.Unauthorized);
});

await Run("valid refresh rotates the stored token and uses the current role", async () =>
{
    await WithDb(async db => { var u = (await db.Users.FindAsync(userId))!; u.IsActive = true; u.Role = "Analyst"; await db.SaveChangesAsync(); });
    var body = await Json(await Post("auth/refresh", new { refreshToken = refresh }));
    await Json(await Post("auth/refresh", new { refreshToken = refresh }), HttpStatusCode.Unauthorized);
    refresh = body.GetProperty("refreshToken").GetString()!;
    access = body.GetProperty("token").GetString()!;
    Check(app.Services.GetRequiredService<JwtService>().ValidateToken(access)!.IsInRole("Analyst"), "Refresh used stale role");
    client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", access);
});

await Run("prompt entities, processed output, encrypted storage and policy audit stay within boundaries", async () =>
{
    await WithDb(async db => { db.Policies.Add(new Policy { Name = "Test policy", Action = "ALLOW", MinRiskScore = 0, MaxRiskScore = 1, IsActive = true, TargetRole = "All" }); await db.SaveChangesAsync(); });
    var body = await Json(await Post("security/scan-prompt", new { prompt = secret }));
    Check(!body.GetRawText().Contains(secret), "Prompt response leaked matched plaintext");
    var entity = body.GetProperty("data").GetProperty("dlp").GetProperty("entitiesDetected")[0];
    Check(entity.GetProperty("entity_type").GetString() == "TEST", "Safe metadata lost");
    await WithDb(async db =>
    {
        Check(!(await db.TokenMappings.SingleAsync()).EncryptedValue.Contains(secret), "Stored token is plaintext");
        Check(!(await db.AuditLogs.ToListAsync()).Any(a => a.Details.Contains(secret)), "Audit leaked matched plaintext");
    });
    Check(!string.Join("\n", logs.Messages).Contains(secret), "Application log leaked plaintext");
});

await Run("policy audit sanitizes raw findings even when called without the controller", async () =>
{
    using var scope = app.Services.CreateScope();
    await scope.ServiceProvider.GetRequiredService<PolicyEngine>().EvaluatePolicyAsync(userId, "batch1", "Analyst", "test",
        0, "LOW", upstream.Entities(), new(), "PROMPT_SCAN");
    await WithDb(async db => Check(!(await db.AuditLogs.ToListAsync()).Any(a => a.Details.Contains(secret)), "Direct policy call leaked plaintext"));
});

await Run("audio responses redact transcript and project metadata", async () =>
{
    using var form = new MultipartFormDataContent();
    form.Add(new ByteArrayContent(new byte[] { 1, 2, 3 }), "audio", "test.wav");
    var body = await Json(await client.PostAsync("/api/v1/security/analyze-call", form));
    Check(!body.GetRawText().Contains(secret), "Audio response leaked matched plaintext");
    Check(body.GetProperty("data").GetProperty("transcript").GetString() == tokenId, "Transcript was not redacted");
});

await Run("missing redacted output never falls back to the original secret", async () =>
{
    upstream.OmitRedactedText = true;
    try
    {
        var body = await Json(await Post("security/scan-prompt", new { prompt = secret }), HttpStatusCode.ServiceUnavailable);
        Check(!body.GetRawText().Contains(secret), "Missing redaction leaked original prompt");
    }
    finally { upstream.OmitRedactedText = false; }
});

await Run("restoration honors current role/account, mapping expiry, and valid analyst access", async () =>
{
    var body = await Json(await Post("security/restore-token", new { tokenId }));
    Check(body.GetProperty("data").GetProperty("originalValue").GetString() == secret, "Authorized restore failed");
    await WithDb(async db => { var u = (await db.Users.FindAsync(userId))!; u.Role = "Employee"; await db.SaveChangesAsync(); });
    await Json(await Post("security/restore-token", new { tokenId }), HttpStatusCode.Forbidden);
    await WithDb(async db => { var u = (await db.Users.FindAsync(userId))!; u.Role = "Analyst"; u.IsActive = false; await db.SaveChangesAsync(); });
    await Json(await Post("security/restore-token", new { tokenId }), HttpStatusCode.Unauthorized);
    await WithDb(async db =>
    {
        (await db.Users.FindAsync(userId))!.IsActive = true;
        (await db.TokenMappings.SingleAsync()).ExpiresAt = DateTime.UtcNow.AddMinutes(-1);
        await db.SaveChangesAsync();
    });
    await Json(await Post("security/restore-token", new { tokenId }), HttpStatusCode.Gone);
    Check(!string.Join("\n", logs.Messages).Contains(secret), "Restore log leaked plaintext");
});

await Run("unknown/deleted account access tokens are rejected", async () =>
{
    var unknown = new User { Id = 999, Username = "missing", Email = "missing@example.test", Role = "Administrator" };
    var token = app.Services.GetRequiredService<JwtService>().GenerateTokens(unknown).accessToken;
    client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
    await Json(await Post("security/restore-token", new { tokenId }), HttpStatusCode.Unauthorized);
});

await Run("SQL Server migration adds nullable expiry without touching existing data", () =>
{
    using var db = new AppDbContext(new DbContextOptionsBuilder<AppDbContext>()
        .UseSqlServer("Server=unused;Database=unused;Integrated Security=true").Options);
    var script = db.GetService<IMigrator>().GenerateScript("20260920091010_InitialCreate", "20261003000000_AddRefreshTokenExpiry");
    Check(script.Contains("ADD [RefreshTokenExpiresAt] datetime2 NULL"), "Expected additive expiry migration");
    Check(!script.Contains("DROP TABLE"), "Unexpected destructive migration");
    return Task.CompletedTask;
});

await Run("missing policy blocks, redaction beats ALLOW, explicit ALLOW stays allowed", async () =>
{
    using var scope = app.Services.CreateScope();
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    var engine = scope.ServiceProvider.GetRequiredService<PolicyEngine>();
    db.Policies.RemoveRange(await db.Policies.ToListAsync()); await db.SaveChangesAsync();
    async Task<PolicyDecision> Evaluate() => await engine.EvaluatePolicyAsync(userId, "batch1", "Analyst", "test", 0, "LOW", null, new(), "PROMPT_SCAN");
    Check((await Evaluate()).Action == "BLOCK", "Missing policy allowed");
    var rule = new Policy { Name = "explicit", Action = "ALLOW", RequireDlpRedaction = true, MinRiskScore = 0, MaxRiskScore = 1, TargetRole = "All", IsActive = true };
    db.Policies.Add(rule); await db.SaveChangesAsync();
    Check((await Evaluate()).Action == "REDACT", "Redaction requirement ignored");
    rule.RequireDlpRedaction = false; await db.SaveChangesAsync();
    Check((await Evaluate()).Action == "ALLOW", "Explicit policy not preserved");
});

await Run("AI outages and missing results fail; audio filenames never fabricate success; speaker profile forwards", async () =>
{
    client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", access);
    foreach (var missing in new[] { false, true })
    {
        upstream.Fail = !missing; upstream.MissingResult = missing;
        await Json(await Post("security/scan-prompt", new { prompt = secret }), HttpStatusCode.ServiceUnavailable);
        using var form = new MultipartFormDataContent();
        form.Add(new ByteArrayContent(new byte[] { 1 }), "audio", "fake_spoof.wav");
        await Json(await client.PostAsync("/api/v1/security/analyze-call", form), HttpStatusCode.ServiceUnavailable);
    }
    upstream.Fail = upstream.MissingResult = false;
    using var valid = new MultipartFormDataContent();
    valid.Add(new ByteArrayContent(new byte[] { 1 }), "audio", "real.wav");
    valid.Add(new StringContent("female"), "speakerProfileId");
    var result = await Json(await client.PostAsync("/api/v1/security/analyze-call", valid));
    Check(upstream.LastMultipart!.Contains("speaker_profile_id") && upstream.LastMultipart.Contains("female"), "Profile not forwarded");
    foreach (var field in new[] { "action", "risk", "transcription", "socialEngineering", "voiceDeepfake", "dlp" })
        Check(result.GetProperty("data").TryGetProperty(field, out _), "Missing canonical field " + field);
});

await Run("mixed legacy/v2 ledger verifies and all new security fields are tamper evident", async () =>
{
    await using var isolated = new SqliteConnection("Data Source=:memory:"); await isolated.OpenAsync();
    await using var db = new AppDbContext(new DbContextOptionsBuilder<AppDbContext>().UseSqlite(isolated).Options);
    await db.Database.EnsureCreatedAsync();
    var legacy = new AuditLog { Timestamp = DateTime.UtcNow, PreviousHash = new string('0', 64), EventType = "DLP_SCAN", Username = "legacy" };
    legacy.Hash = AuditService.ComputeEntryHash(legacy); db.AuditLogs.Add(legacy); await db.SaveChangesAsync();
    var audit = new AuditService(db);
    var current = await audit.LogEventAsync("DLP_SCAN", "INFO", details: "{\"safe\":true}");
    Check((await audit.VerifyChainAsync()).Valid, "Mixed history failed verification");
    foreach (var field in new[] { "UserRole", "IpAddress", "RiskLevel", "Details" })
    {
        var property = typeof(AuditLog).GetProperty(field)!;
        var old = property.GetValue(current); property.SetValue(current, "tampered"); await db.SaveChangesAsync();
        Check(!(await audit.VerifyChainAsync()).Valid, "Tampering not detected for " + field);
        property.SetValue(current, old); await db.SaveChangesAsync();
    }
    current.HashVersion = 1; await db.SaveChangesAsync();
    Check(!(await audit.VerifyChainAsync()).Valid, "Hash downgrade accepted");
});

Console.WriteLine($"{passed}/{passed} Batch 1 checks passed. No external database or AI service used.");

sealed class AiResponses(string secret, string tokenId) : HttpMessageHandler
{
    public bool OmitRedactedText { get; set; }
    public object[] Entities() => new object[] { new { entity_type = "TEST", category = "CREDENTIAL", severity = "HIGH", confidence = 0.99,
        start = 0, end = secret.Length, text = secret, original_value = secret, nested = new { value = secret } } };
    public string? LastMultipart { get; private set; }
    public bool Fail { get; set; }
    public bool MissingResult { get; set; }
    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        LastMultipart = request.Content == null ? null : await request.Content.ReadAsStringAsync(cancellationToken);
        if (Fail) return new HttpResponseMessage(HttpStatusCode.ServiceUnavailable);
        if (MissingResult) return new HttpResponseMessage(HttpStatusCode.OK) { Content = JsonContent.Create(new { status = "success", data = new { } }) };
        var dlp = new Dictionary<string, object?>
        {
            ["entities"] = Entities(), ["has_sensitive_data"] = true, ["sensitivity_score"] = 0.8,
            ["mappings"] = new[] { new { token_id = tokenId, entity_type = "TEST", original_value = secret } }
        };
        if (!OmitRedactedText) dlp["redacted_text"] = tokenId;
        object nlp = new { social_engineering_score = 0.0, threats_detected = Array.Empty<string>() };
        object data = request.RequestUri!.AbsolutePath switch
        {
            "/nlp/classify" => nlp,
            "/audio/analyze" => new { voice_deepfake = new { success = true, model_loaded = true, spoof_score = 0.1, is_deepfake = false },
                transcription = new { success = true, transcript = secret }, social_engineering = nlp, dlp },
            _ => dlp
        };
        return new HttpResponseMessage(HttpStatusCode.OK) { Content = JsonContent.Create(new { status = "success", data }) };
    }
}

sealed class CapturedLogs : ILoggerProvider
{
    public List<string> Messages { get; } = new();
    public ILogger CreateLogger(string categoryName) => new Capture(Messages);
    public void Dispose() { }
    private sealed class Capture(List<string> messages) : ILogger
    {
        public IDisposable? BeginScope<TState>(TState state) where TState : notnull => null;
        public bool IsEnabled(LogLevel logLevel) => true;
        public void Log<TState>(LogLevel level, EventId id, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
        { lock (messages) messages.Add(formatter(state, exception) + exception?.ToString()); }
    }
}
