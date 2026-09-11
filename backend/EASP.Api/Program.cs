var builder = WebApplication.CreateBuilder(args);

// ---- P0: base services ----
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// ---- P1: EF Core DbContext (User/Role) ----
// builder.Services.AddDbContext<AppDbContext>(opts =>
//     opts.UseSqlServer(builder.Configuration.GetConnectionString("Default")));

// ---- P1: Identity + JWT ----
// builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
//     .AddJwtBearer(opts => { /* token validation params */ });
// builder.Services.AddAuthorization();

// ---- P3: Typed HttpClient for the DLP microservice ----
// builder.Services.AddHttpClient<DlpClient>(c =>
//     c.BaseAddress = new Uri(builder.Configuration["DlpService:BaseUrl"]!));

// ---- P10: Typed HttpClient for the FastAPI AI/Security Engine service ----
// builder.Services.AddHttpClient<SecurityEngineService>(c =>
//     c.BaseAddress = new Uri(builder.Configuration["SecurityEngine:BaseUrl"]!));

// ---- P4: background TTL sweep for TokenMapping (Mongo TTL index equivalent) ----
// builder.Services.AddHostedService<TokenMappingCleanupService>();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

// ---- P2: middleware order matters — logging hook before auth ----
// app.UseMiddleware<RequestLoggingMiddleware>();

// app.UseAuthentication();
// app.UseAuthorization();

app.MapControllers();

app.Run();
