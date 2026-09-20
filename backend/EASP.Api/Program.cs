using System.Text;
using EASP.Api.Data;
using EASP.Api.Middleware;
using EASP.Api.Models;
using EASP.Api.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

// ==========================================
// P0: Base Services
// ==========================================
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();

// Swagger configuration with JWT Bearer authentication support
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "EASP Security Platform API",
        Version = "v1",
        Description = "Enterprise AI Security Platform - Core Backend API (.NET 8)"
    });

    options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Name = "Authorization",
        Type = SecuritySchemeType.Http,
        Scheme = "Bearer",
        BearerFormat = "JWT",
        In = ParameterLocation.Header,
        Description = "Enter JWT Bearer token format: {your_token_here}"
    });

    options.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                {
                    Type = ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            Array.Empty<string>()
        }
    });
});

// ==========================================
// P1a: EF Core DbContext & Identity
// ==========================================
builder.Services.AddDbContext<AppDbContext>(opts =>
    opts.UseSqlServer(builder.Configuration.GetConnectionString("Default")));

builder.Services
    .AddIdentity<User, Role>(options =>
    {
        options.Password.RequiredLength = 8;
        options.Password.RequireNonAlphanumeric = false;
        options.Password.RequireUppercase = false;
        options.User.RequireUniqueEmail = true;
    })
    .AddEntityFrameworkStores<AppDbContext>()
    .AddDefaultTokenProviders();

// ==========================================
// P1b: JWT Authentication & Services (T-P01-011)
// ==========================================
builder.Services.AddScoped<IJwtTokenService, JwtTokenService>();

var jwtKey = builder.Configuration["Jwt:Key"] ?? "EASP_Super_Secret_JWT_Key_For_Development_Must_Be_Long_Enough_2026!";
var jwtIssuer = builder.Configuration["Jwt:Issuer"] ?? "EASP";
var jwtAudience = builder.Configuration["Jwt:Audience"] ?? "EASP-Client";

builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.RequireHttpsMetadata = false;
    options.SaveToken = true;
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidateAudience = true,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,
        ValidIssuer = jwtIssuer,
        ValidAudience = jwtAudience,
        IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey)),
        ClockSkew = TimeSpan.Zero
    };
});

builder.Services.AddAuthorization();

// ==========================================
// P3: Typed HttpClient for the DLP microservice (T-P03-023)
// ==========================================
builder.Services.AddHttpClient<IDlpClient, DlpClient>(client =>
{
    var baseUrl = builder.Configuration["DlpService:BaseUrl"] ?? "http://dlp-service:8001";
    if (!baseUrl.EndsWith("/")) baseUrl += "/";
    client.BaseAddress = new Uri(baseUrl);
    client.Timeout = TimeSpan.FromSeconds(5);
});

// ==========================================
// P2: CORS Configuration (T-P02-014)
// ==========================================
var allowedOrigins = builder.Configuration.GetSection("AllowedOrigins").Get<string[]>() 
    ?? new[] { "http://localhost:5173", "http://localhost:3000" };

builder.Services.AddCors(options =>
{
    options.AddPolicy("EaspCorsPolicy", policy =>
    {
        policy.WithOrigins(allowedOrigins)
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

// ==========================================
// P4: Token Mapping Service & TTL Cleanup Worker (T-P04-027)
// ==========================================
builder.Services.AddScoped<ITokenMappingService, TokenMappingService>();
builder.Services.AddHostedService<TokenMappingCleanupService>();

// ==========================================
// P6: Risk Engine Service (T-P06-033, T-P06-034, T-P06-035)
// ==========================================
builder.Services.AddScoped<IRiskEngineService, RiskEngineService>();

// P10: Typed HttpClient stub for FastAPI AI/Security Engine
// builder.Services.AddHttpClient<SecurityEngineService>(c =>
//     c.BaseAddress = new Uri(builder.Configuration["SecurityEngine:BaseUrl"]!));

// ==========================================
// Build WebApplication
// ==========================================
var app = builder.Build();

// ==========================================
// P2: Middleware Pipeline Order (T-P02-014, T-P02-016 & T-P02-017)
// 1. Global Exception Handling (catches all unhandled downstream errors)
// 2. Enterprise Security Headers (Helmet equivalent - T-P02-014)
// 3. Request Logging & Latency Tracking (T-P02-017)
// 4. CORS Allow-List (T-P02-014)
// 5. Swagger in Development
// 6. Https Redirection
// 7. Authentication (JWT Bearer)
// 8. Authorization (Role-based policies)
// 9. Route Endpoint Mapping
// ==========================================
app.UseMiddleware<GlobalExceptionMiddleware>();
app.UseMiddleware<SecurityHeadersMiddleware>();
app.UseMiddleware<RequestLoggingMiddleware>();
app.UseCors("EaspCorsPolicy");

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

if (!app.Environment.IsDevelopment())
{
    app.UseHttpsRedirection();
}

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

// ==========================================
// T-P01-010: Seed Default Roles on Startup
// ==========================================
using (var scope = app.Services.CreateScope())
{
    var services = scope.ServiceProvider;
    try
    {
        var roleManager = services.GetRequiredService<RoleManager<Role>>();
        await DbSeeder.SeedRolesAsync(roleManager);

        var dbContext = services.GetRequiredService<AppDbContext>();
        await DbSeeder.SeedDefaultPoliciesAsync(dbContext);
    }
    catch (Exception ex)
    {
        var logger = services.GetRequiredService<ILogger<Program>>();
        logger.LogError(ex, "An error occurred while seeding default roles or policies.");
    }
}

app.Run();
