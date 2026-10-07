using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Text.Json;

namespace EASP.API.Models
{
    public class AuditLog
    {
        [Key]
        public int Id { get; set; }
        public int HashVersion { get; set; } = 1;

        public DateTime Timestamp { get; set; } = DateTime.UtcNow;

        [Required, MaxLength(50)]
        public string EventType { get; set; } = string.Empty;
        // AUTH_LOGIN | AUTH_REGISTER | AUTH_FAILURE | DLP_SCAN | DLP_REDACT | DLP_RESTORE
        // VOICE_DEEPFAKE_ANALYSIS | SOCIAL_ENGINEERING_ANALYSIS | RISK_EVALUATION
        // POLICY_DECISION | INCIDENT_CREATED | INCIDENT_UPDATED

        public int? UserId { get; set; }
        public User? User { get; set; }

        [MaxLength(100)]
        public string Username { get; set; } = "anonymous";

        [MaxLength(30)]
        public string UserRole { get; set; } = "None";

        [MaxLength(50)]
        public string IpAddress { get; set; } = "unknown";

        [Required, MaxLength(20)]
        public string ActionTaken { get; set; } = "INFO";
        // ALLOW | REDACT | ESCALATE | BLOCK | INFO | ALERT

        public double RiskScore { get; set; } = 0.0;

        [MaxLength(10)]
        public string RiskLevel { get; set; } = "N/A";
        // LOW | MEDIUM | HIGH | N/A

        // JSON serialized details object
        public string Details { get; set; } = "{}";

        [Required, MaxLength(64)]
        public string PreviousHash { get; set; } = string.Empty;

        [Required, MaxLength(64)]
        public string Hash { get; set; } = string.Empty;
    }
}
