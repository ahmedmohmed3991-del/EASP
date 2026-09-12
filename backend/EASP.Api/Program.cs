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
// P3 & P10: Typed HttpClients (Stubs for upcoming phases)
// ==========================================
// builder.Services.AddHttpClient<DlpClient>(c =>
//     c.BaseAddress = new Uri(builder.Configuration["DlpService:BaseUrl"]!));
// builder.Services.AddHttpClient<SecurityEngineService>(c =>
//     c.BaseAddress = new Uri(builder.Configuration["SecurityEngine:BaseUrl"]!));

// ==========================================
// Build WebApplication
// ==========================================
var app = builder.Build();

// ==========================================
// P2: Middleware Pipeline Order (T-P02-016 & T-P02-017)
// 1. Global Exception Handling (catches all unhandled downstream errors)
// 2. Request Logging & Latency Tracking
// 3. Swagger in Development
// 4. Https Redirection
// 5. Authentication (JWT Bearer)
// 6. Authorization (Role-based policies)
// 7. Route Endpoint Mapping
// ==========================================
app.UseMiddleware<GlobalExceptionMiddleware>();
app.UseMiddleware<RequestLoggingMiddleware>();

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
    }
    catch (Exception ex)
    {
        var logger = services.GetRequiredService<ILogger<Program>>();
        logger.LogError(ex, "An error occurred while seeding default roles.");
    }
}

app.Run();
