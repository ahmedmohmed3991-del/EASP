using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using EASP.API.Data;
using EASP.API.Models;
using Microsoft.EntityFrameworkCore;

namespace EASP.API.Services
{
    public class ChainVerificationResult
    {
        public bool Valid { get; set; }
        public int TotalRecords { get; set; }
        public string? HeadHash { get; set; }
        public string? Message { get; set; }
        public string? BrokenReason { get; set; }
    }

    public class AuditService
    {
        private static readonly string GenesisHash = new string('0', 64);
        private readonly AppDbContext _db;
        private static readonly SemaphoreSlim _lock = new SemaphoreSlim(1, 1);

        public AuditService(AppDbContext db)
        {
            _db = db;
        }

        /// <summary>Compute SHA-256 hash of audit record fields for tamper detection</summary>
        public static string ComputeHash(string previousHash, DateTime timestamp, string eventType,
            string username, string actionTaken, double riskScore, string details)
        {
            long unixSeconds = new DateTimeOffset(DateTime.SpecifyKind(timestamp, DateTimeKind.Utc)).ToUnixTimeSeconds();
            var content = string.Join("|", new[]
            {
                previousHash,
                unixSeconds.ToString(),
                eventType,
                username ?? "anonymous",
                actionTaken,
                riskScore.ToString("F4")
            });

            var bytes = Encoding.UTF8.GetBytes(content);
            var hash = SHA256.HashData(bytes);
            return Convert.ToHexString(hash).ToLowerInvariant();
        }

        public static string ComputeEntryHash(AuditLog entry)
        {
            if (entry.HashVersion == 1) return ComputeHash(entry.PreviousHash, entry.Timestamp,
                entry.EventType, entry.Username, entry.ActionTaken, entry.RiskScore, entry.Details);
            if (entry.HashVersion != 2) throw new InvalidOperationException("Unsupported audit hash version");
            var payload = JsonSerializer.Serialize(new {
                entry.HashVersion, entry.PreviousHash,
                Timestamp = DateTime.SpecifyKind(entry.Timestamp, DateTimeKind.Utc).ToString("O"),
                entry.EventType, entry.UserId, entry.Username, entry.UserRole, entry.IpAddress,
                entry.ActionTaken, entry.RiskScore, entry.RiskLevel, entry.Details
            });
            return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(payload))).ToLowerInvariant();
        }

        /// <summary>Append a new immutable audit record to the SHA-256 hash chain</summary>
        public async Task<AuditLog> LogEventAsync(
            string eventType,
            string actionTaken,
            int? userId = null,
            string username = "anonymous",
            string userRole = "None",
            string ipAddress = "unknown",
            double riskScore = 0.0,
            string riskLevel = "N/A",
            string details = "{}")
        {
            await _lock.WaitAsync();
            try
            {
                // SQL application lock serializes the read-head/append across API processes.
                await using var transaction = _db.Database.IsSqlServer() ? await _db.Database.BeginTransactionAsync() : null;
                if (transaction != null)
                    await _db.Database.ExecuteSqlRawAsync(@"DECLARE @result int;
                        EXEC @result = sp_getapplock @Resource=N'EASP:AuditLedger', @LockMode='Exclusive',
                            @LockOwner='Transaction', @LockTimeout=10000;
                        IF @result < 0 THROW 51000, 'Audit writer lock unavailable', 1;");
                var lastEntry = await _db.AuditLogs
                    .OrderByDescending(a => a.Id)
                    .FirstOrDefaultAsync();

                var previousHash = lastEntry?.Hash ?? GenesisHash;
                var timestamp = DateTime.UtcNow;


                var log = new AuditLog
                {
                    HashVersion = 2,
                    Timestamp = timestamp,
                    EventType = eventType,
                    UserId = userId,
                    Username = username,
                    UserRole = userRole,
                    IpAddress = ipAddress,
                    ActionTaken = actionTaken,
                    RiskScore = riskScore,
                    RiskLevel = riskLevel,
                    Details = details,
                    PreviousHash = previousHash,
                    Hash = string.Empty
                };

                log.Hash = ComputeEntryHash(log);
                _db.AuditLogs.Add(log);
                await _db.SaveChangesAsync();
                if (transaction != null) await transaction.CommitAsync();
                return log;
            }
            finally
            {
                _lock.Release();
            }
        }

        /// <summary>Verify integrity of entire SHA-256 hash chain</summary>
        public async Task<ChainVerificationResult> VerifyChainAsync()
        {
            var entries = await _db.AuditLogs
                .OrderBy(a => a.Id)
                .ToListAsync();

            if (entries.Count == 0)
            {
                return new ChainVerificationResult
                {
                    Valid = true,
                    TotalRecords = 0,
                    HeadHash = GenesisHash,
                    Message = "Genesis state: No audit records found."
                };
            }

            var expectedPreviousHash = GenesisHash;

            for (int i = 0; i < entries.Count; i++)
            {
                var entry = entries[i];

                if (entry.PreviousHash != expectedPreviousHash)
                {
                    return new ChainVerificationResult
                    {
                        Valid = false,
                        TotalRecords = entries.Count,
                        HeadHash = entries[^1].Hash,
                        BrokenReason = $"Previous hash mismatch at record {i} (Id: {entry.Id})"
                    };
                }

                if (entry.HashVersion is not (1 or 2) || (i > 0 && entries[i - 1].HashVersion == 2 && entry.HashVersion == 1))
                    return new ChainVerificationResult { Valid = false, BrokenReason = "Invalid audit hash version transition" };
                var recalculated = ComputeEntryHash(entry);

                if (recalculated != entry.Hash)
                {
                    return new ChainVerificationResult
                    {
                        Valid = false,
                        TotalRecords = entries.Count,
                        HeadHash = entries[^1].Hash,
                        BrokenReason = $"Hash mismatch at record {i} (Id: {entry.Id})"
                    };
                }

                expectedPreviousHash = entry.Hash;
            }

            return new ChainVerificationResult
            {
                Valid = true,
                TotalRecords = entries.Count,
                HeadHash = entries[^1].Hash,
                Message = $"Chain verified successfully across {entries.Count} immutable records"
            };
        }
    }
}
