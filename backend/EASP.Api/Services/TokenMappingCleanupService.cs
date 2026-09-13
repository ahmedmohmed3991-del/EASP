namespace EASP.Api.Services;

/// <summary>
/// T-P04-027: Background service performing periodic TTL sweeps on expired TokenMappings.
/// Direct .NET equivalent of MongoDB TTL collection index expiration.
/// </summary>
public class TokenMappingCleanupService : BackgroundService
{
    private readonly IServiceScopeFactory _scopeFactory;
    private readonly ILogger<TokenMappingCleanupService> _logger;
    private readonly TimeSpan _sweepInterval = TimeSpan.FromSeconds(60);

    public TokenMappingCleanupService(IServiceScopeFactory scopeFactory, ILogger<TokenMappingCleanupService> logger)
    {
        _scopeFactory = scopeFactory;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("TokenMappingCleanupService background TTL worker started.");

        using var timer = new PeriodicTimer(_sweepInterval);

        while (!stoppingToken.IsCancellationRequested && await timer.WaitForNextTickAsync(stoppingToken))
        {
            try
            {
                using var scope = _scopeFactory.CreateScope();
                var tokenService = scope.ServiceProvider.GetRequiredService<ITokenMappingService>();
                var purgedCount = await tokenService.SweepExpiredTokensAsync(stoppingToken);

                if (purgedCount > 0)
                {
                    _logger.LogInformation("Background TTL Worker: Purged {Count} expired token mappings.", purgedCount);
                }
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error occurred while executing TokenMapping TTL sweep.");
            }
        }

        _logger.LogInformation("TokenMappingCleanupService background TTL worker stopped.");
    }
}
