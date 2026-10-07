using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using EASP.API.Data;
using EASP.API.Models;
using Microsoft.EntityFrameworkCore;

namespace EASP.API.Services
{
    public class TokenService
    {
        private readonly AppDbContext _db;
        private readonly AuditService _audit;
        private readonly byte[] _encryptionKey;
        private const int DefaultTtlHours = 24;

        public TokenService(AppDbContext db, AuditService audit, IConfiguration config)
        {
            _db = db;
            _audit = audit;
            var keyHex = config["EncryptionKey"] ?? "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
            _encryptionKey = Convert.FromHexString(keyHex);
        }

        /// <summary>Encrypt a plaintext value using AES-256-GCM</summary>
        private (string encrypted, string iv, string authTag) EncryptValue(string plaintext)
        {
            var nonce = new byte[12]; // 96-bit nonce for AES-GCM
            RandomNumberGenerator.Fill(nonce);

            var plaintextBytes = Encoding.UTF8.GetBytes(plaintext);
            var ciphertext = new byte[plaintextBytes.Length];
            var tag = new byte[16];

            using var aes = new AesGcm(_encryptionKey, 16);
            aes.Encrypt(nonce, plaintextBytes, ciphertext, tag);

            return (
                Convert.ToBase64String(ciphertext),
                Convert.ToBase64String(nonce),
                Convert.ToBase64String(tag)
            );
        }

        /// <summary>Decrypt AES-256-GCM encrypted value</summary>
        private string DecryptValue(string encryptedBase64, string ivBase64, string authTagBase64)
        {
            var ciphertext = Convert.FromBase64String(encryptedBase64);
            var nonce = Convert.FromBase64String(ivBase64);
            var tag = Convert.FromBase64String(authTagBase64);
            var plaintext = new byte[ciphertext.Length];

            using var aes = new AesGcm(_encryptionKey, 16);
            aes.Decrypt(nonce, ciphertext, tag, plaintext);

            return Encoding.UTF8.GetString(plaintext);
        }

        /// <summary>Save or refresh an encrypted token mapping</summary>
        public async Task<TokenMapping> SaveTokenMappingAsync(
            string tokenId, string entityType, string plaintextValue,
            int? userId, int ttlHours = DefaultTtlHours)
        {
            var (encrypted, iv, authTag) = EncryptValue(plaintextValue);
            var expiresAt = DateTime.UtcNow.AddHours(ttlHours);

            var existing = await _db.TokenMappings.FirstOrDefaultAsync(t => t.TokenId == tokenId);
            if (existing != null)
            {
                existing.EncryptedValue = encrypted;
                existing.Iv = iv;
                existing.AuthTag = authTag;
                existing.ExpiresAt = expiresAt;
                await _db.SaveChangesAsync();
                return existing;
            }

            var mapping = new TokenMapping
            {
                TokenId = tokenId,
                EntityType = entityType,
                EncryptedValue = encrypted,
                Iv = iv,
                AuthTag = authTag,
                UserId = userId,
                ExpiresAt = expiresAt
            };
            _db.TokenMappings.Add(mapping);
            await _db.SaveChangesAsync();
            return mapping;
        }

        /// <summary>Restore original sensitive value (strictly restricted to Analyst & Administrator)</summary>
        public async Task<RestoreResult> RestoreTokenAsync(string tokenId, int userId, string username, string userRole, string ipAddress)
        {
            // Fail-closed authorization
            if (!new[] { "Analyst", "Administrator" }.Contains(userRole))
            {
                await _audit.LogEventAsync(
                    "DLP_RESTORE", "BLOCK", userId, username, userRole, ipAddress,
                    0.85, "HIGH",
                    JsonSerializer.Serialize(new { tokenId, outcome = "DENIED", reason = "Insufficient permissions" }));

                return new RestoreResult { Success = false, StatusCode = 403, Error = $"Access forbidden: Role '{userRole}' is not authorized to restore sensitive values" };
            }

            var mapping = await _db.TokenMappings.FirstOrDefaultAsync(t => t.TokenId == tokenId);
            if (mapping == null)
                return new RestoreResult { Success = false, StatusCode = 404, Error = "Token mapping not found or has expired" };

            if (DateTime.UtcNow > mapping.ExpiresAt)
            {
                _db.TokenMappings.Remove(mapping);
                await _db.SaveChangesAsync();
                return new RestoreResult { Success = false, StatusCode = 410, Error = "Token mapping has expired and been purged" };
            }

            string originalValue;
            try
            {
                originalValue = DecryptValue(mapping.EncryptedValue, mapping.Iv, mapping.AuthTag);
            }
            catch
            {
                return new RestoreResult { Success = false, StatusCode = 500, Error = "Decryption failed: cryptographic integrity error" };
            }

            // Audit (NEVER log plaintext value)
            await _audit.LogEventAsync(
                "DLP_RESTORE", "ALLOW", userId, username, userRole, ipAddress,
                0.20, "LOW",
                JsonSerializer.Serialize(new { tokenId, entityType = mapping.EntityType, outcome = "AUTHORIZED_RESTORE" }));

            return new RestoreResult
            {
                Success = true,
                StatusCode = 200,
                TokenId = tokenId,
                EntityType = mapping.EntityType,
                OriginalValue = originalValue,
                ExpiresAt = mapping.ExpiresAt
            };
        }
    }

    public class RestoreResult
    {
        public bool Success { get; set; }
        public int StatusCode { get; set; }
        public string? Error { get; set; }
        public string? TokenId { get; set; }
        public string? EntityType { get; set; }
        public string? OriginalValue { get; set; }
        public DateTime? ExpiresAt { get; set; }
    }
}
