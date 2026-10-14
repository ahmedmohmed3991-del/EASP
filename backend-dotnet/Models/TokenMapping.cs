using System.ComponentModel.DataAnnotations;
using System.Security.Cryptography;
using System.Text;

namespace EASP.API.Models
{
    public class TokenMapping
    {
        [Key]
        public int Id { get; set; }

        [Required, MaxLength(200)]
        public string TokenId { get; set; } = string.Empty;

        [MaxLength(100)]
        public string EntityType { get; set; } = string.Empty;

        [Required]
        public string EncryptedValue { get; set; } = string.Empty; // Base64

        [Required, MaxLength(32)]
        public string Iv { get; set; } = string.Empty; // Base64

        [Required, MaxLength(32)]
        public string AuthTag { get; set; } = string.Empty; // Base64

        public int? UserId { get; set; }
        public User? User { get; set; }

        public DateTime ExpiresAt { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    }
}
