namespace EASP.API.Services
{
    /// <summary>
    /// Multi-Modal Risk Engine: Fuses voice deepfake score, social engineering score,
    /// and DLP sensitivity score into a unified risk assessment.
    /// Legacy .NET scoring profile; thresholds intentionally preserved pending calibration decision.
    /// </summary>
    public class RiskEngine
    {
        // Weights for each modality (must sum to ~1.0)
        private const double VoiceWeight = 0.45;
        private const double SocialWeight = 0.35;
        private const double DlpWeight = 0.20;

        // Thresholds
        private const double LowThreshold = 0.35;
        private const double HighThreshold = 0.60;

        public RiskAssessment CalculateRisk(
            double voiceScore = 0.0,
            double socialScore = 0.0,
            double dlpScore = 0.0,
            bool isVoiceApplicable = true,
            bool hasSocialError = false,
            bool hasDlpError = false,
            bool hasVoiceError = false)
        {
            var contributingFactors = new Dictionary<string, double>
            {
                ["voiceRisk"] = voiceScore,
                ["socialRisk"] = socialScore,
                ["dlpSensitivity"] = dlpScore
            };

            double fusedRisk;

            if (isVoiceApplicable)
            {
                // Full multi-modal fusion (Voice + Social + DLP)
                fusedRisk = (voiceScore * VoiceWeight) +
                            (socialScore * SocialWeight) +
                            (dlpScore * DlpWeight);
            }
            else
            {
                // Text-only (Social + DLP), re-weighted
                fusedRisk = (socialScore * 0.60) + (dlpScore * 0.40);
            }

            // Clamp to [0, 1]
            fusedRisk = Math.Max(0.0, Math.Min(1.0, fusedRisk));

            // Apply error penalties
            if (hasVoiceError) fusedRisk = Math.Min(1.0, fusedRisk + 0.10);
            if (hasSocialError) fusedRisk = Math.Min(1.0, fusedRisk + 0.05);
            if (hasDlpError) fusedRisk = Math.Min(1.0, fusedRisk + 0.05);

            var level = fusedRisk < LowThreshold ? "LOW" :
                        fusedRisk < HighThreshold ? "MEDIUM" : "HIGH";

            return new RiskAssessment
            {
                FusedRisk = Math.Round(fusedRisk, 4),
                Level = level,
                ContributingFactors = contributingFactors
            };
        }
    }

    public class RiskAssessment
    {
        public string ScoringProfile => "dotnet-legacy-v1";
        public double FusedRisk { get; set; }
        public string Level { get; set; } = "LOW";
        public Dictionary<string, double> ContributingFactors { get; set; } = new();
    }
}
