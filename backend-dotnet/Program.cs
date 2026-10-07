using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using System.Text;
using System.Threading.RateLimiting;
using EASP.API.Data;
using EASP.API.Services;

var builder = WebApplication.CreateBuilder(args);

// ══════════════════════════════════════════
// 1. Database — SQL Server + EF Core
// ══════════════════════════════════════════
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

// ══════════════════════════════════════════
// 2. Authentication — JWT Bearer
// ══════════════════════════════════════════
var jwtSecret = builder.Configuration["Jwt:Secret"]
    ?? throw new InvalidOperationException("Jwt:Secret is not configured");

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtSecret)),
            ValidateIssuer = false,
            ValidateAudience = false,
            ClockSkew = TimeSpan.Zero
        };
        options.Events = new JwtBearerEvents
        {
            OnTokenValidated = JwtService.ValidateCurrentUserAsync
        };
    });

builder.Services.AddAuthorization();

// ══════════════════════════════════════════
// 3. CORS — Allow frontend origins
// ══════════════════════════════════════════
var allowedOrigins = builder.Configuration.GetSection("AllowedOrigins").Get<string[]>()
    ?? new[] { "http://localhost:5173", "http://localhost:3000" };

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins(allowedOrigins)
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

// ══════════════════════════════════════════
// 4. Rate Limiting (built-in .NET 8)
// ══════════════════════════════════════════
builder.Services.AddRateLimiter(options =>
{
    options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(ctx =>
        RateLimitPartition.GetFixedWindowLimiter(
            ctx.Connection.RemoteIpAddress?.ToString() ?? "anonymous",
            _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit = 100,
                Window = TimeSpan.FromMinutes(1),
                QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
                QueueLimit = 0
            }));
    options.RejectionStatusCode = 429;
});

// ══════════════════════════════════════════
// 5. Application Services
// ══════════════════════════════════════════
builder.Services.AddScoped<AuditService>();
builder.Services.AddScoped<TokenService>();
builder.Services.AddScoped<PolicyEngine>();
builder.Services.AddSingleton<RiskEngine>();
builder.Services.AddSingleton<JwtService>();

// AI Service HTTP Client
var aiServiceUrl = builder.Configuration["AiServiceUrl"] ?? "http://localhost:8000";
builder.Services.AddHttpClient<AiServiceClient>(client =>
{
    client.BaseAddress = new Uri(aiServiceUrl);
    var serviceToken = builder.Configuration["AI_SERVICE_TOKEN"];
    if (!string.IsNullOrEmpty(serviceToken)) client.DefaultRequestHeaders.Add("X-Service-Token", serviceToken);
    client.Timeout = TimeSpan.FromSeconds(120);
});

// ══════════════════════════════════════════
// 6. Controllers + Swagger/OpenAPI
// ══════════════════════════════════════════
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new() { Title = "EASP API", Version = "v1", Description = "Enterprise AI Security Platform — .NET 8 + SQL Server" });
    c.AddSecurityDefinition("Bearer", new Microsoft.OpenApi.Models.OpenApiSecurityScheme
    {
        Name = "Authorization",
        Type = Microsoft.OpenApi.Models.SecuritySchemeType.Http,
        Scheme = "Bearer",
        BearerFormat = "JWT",
        In = Microsoft.OpenApi.Models.ParameterLocation.Header,
        Description = "Enter: Bearer {your JWT token}"
    });
    c.AddSecurityRequirement(new Microsoft.OpenApi.Models.OpenApiSecurityRequirement
    {
        {
            new Microsoft.OpenApi.Models.OpenApiSecurityScheme
            {
                Reference = new Microsoft.OpenApi.Models.OpenApiReference
                    { Type = Microsoft.OpenApi.Models.ReferenceType.SecurityScheme, Id = "Bearer" }
            },
            Array.Empty<string>()
        }
    });
});

// ══════════════════════════════════════════
// BUILD APPLICATION
// ══════════════════════════════════════════
var app = builder.Build();

// Auto-migrate DB and seed default data on startup
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    try
    {
        Console.WriteLine("[EASP] Running database migration...");
        await SeedData.SeedAsync(db);
        Console.WriteLine("[EASP] ✅ Database ready.");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"[EASP] ⚠️ Migration/Seed error: {ex.Message}");
    }
}

// Security headers (basic)
app.Use(async (ctx, next) =>
{
    ctx.Response.Headers["X-Content-Type-Options"] = "nosniff";
    ctx.Response.Headers["X-Frame-Options"] = "DENY";
    ctx.Response.Headers["X-XSS-Protection"] = "1; mode=block";
    await next();
});

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(c => c.SwaggerEndpoint("/swagger/v1/swagger.json", "EASP API v1"));
}

app.UseRateLimiter();
app.UseCors();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

// Root endpoint
app.MapGet("/", () => new
{
    service = "easp-backend-dotnet",
    status = "running",
    version = "1.0.0",
    message = "EASP Enterprise AI Security Platform Backend is active (.NET 8 + SQL Server).",
    architecture = "Two-Branch Defense: Voice Anti-Spoofing & Reversible Generative AI DLP",
    swagger = "/swagger"
});

Console.WriteLine("[EASP Backend] Starting on port 5000...");
app.Run("http://0.0.0.0:5000");
