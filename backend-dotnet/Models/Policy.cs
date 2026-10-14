using System.ComponentModel.DataAnnotations;

namespace EASP.API.Models
{
    public class Policy
    {
        [Key]
        public int Id { get; set; }

        [Required, MaxLength(200)]
        public string Name { get; set; } = string.Empty;

        [Required]
        public string Description { get; set; } = string.Empty;

        [MaxLength(20)]
        public string TargetRole { get; set; } = "All";
        // All | Employee | Analyst | Administrator

        public double MinRiskScore { get; set; } = 0.0;
        public double MaxRiskScore { get; set; } = 1.0;

        [Required, MaxLength(20)]
        public string Action { get; set; } = string.Empty;
        // ALLOW | REDACT | ESCALATE | BLOCK

        public bool RequireDlpRedaction { get; set; } = true;

        public int Priority { get; set; } = 100; // Lower = higher priority

        public bool IsActive { get; set; } = true;

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    }
}
