using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace EASP.API.Models
{
    public class Incident
    {
        [Key]
        public int Id { get; set; }

        [Required, MaxLength(500)]
        public string Title { get; set; } = string.Empty;

        [Required, MaxLength(10)]
        public string Severity { get; set; } = "MEDIUM";
        // LOW | MEDIUM | HIGH | CRITICAL

        [Required, MaxLength(20)]
        public string Status { get; set; } = "OPEN";
        // OPEN | INVESTIGATING | RESOLVED | DISMISSED

        [Required, MaxLength(20)]
        public string Source { get; set; } = string.Empty;
        // PROMPT_SCAN | CALL_ANALYSIS | MANUAL_ALERT

        public int? UserId { get; set; }
        public User? User { get; set; }

        [MaxLength(100)]
        public string Username { get; set; } = "anonymous";

        public double RiskScore { get; set; }

        [Required, MaxLength(10)]
        public string RiskLevel { get; set; } = "LOW";
        // LOW | MEDIUM | HIGH

        // Contributing factors stored as individual columns
        public double VoiceRisk { get; set; } = 0.0;
        public double SocialRisk { get; set; } = 0.0;
        public double DlpSensitivity { get; set; } = 0.0;

        [Required, MaxLength(20)]
        public string ActionTaken { get; set; } = string.Empty;
        // ALLOW | REDACT | ESCALATE | BLOCK

        public int? AuditLogId { get; set; }

        // Notes stored as JSON string
        public string NotesJson { get; set; } = "[]";

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        public DateTime? ResolvedAt { get; set; }
    }
}
