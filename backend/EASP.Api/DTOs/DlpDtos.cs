using System.ComponentModel.DataAnnotations;

namespace EASP.Api.DTOs;

public class DlpAnalyzeRequest
{
    [Required]
    public string Text { get; set; } = string.Empty;

    public List<string>? TargetEntities { get; set; }

    public string Language { get; set; } = "en";
}

public class DlpEntityMatch
{
    public string EntityType { get; set; } = string.Empty;
    public string Value { get; set; } = string.Empty;
    public int StartIndex { get; set; }
    public int EndIndex { get; set; }
    public double Confidence { get; set; }
}

public class DlpAnalyzeResponse
{
    public bool HasSensitiveData { get; set; }
    public List<DlpEntityMatch> DetectedEntities { get; set; } = new();
    public string MaskedText { get; set; } = string.Empty;
    public long ProcessingTimeMs { get; set; }
    public string SourceEngine { get; set; } = "DlpService"; // "DlpMicroservice" or "InternalFallbackScanner"
}

public class DlpAnonymizeRequest
{
    [Required]
    public string Text { get; set; } = string.Empty;

    public string MaskChar { get; set; } = "*";
}

public class DlpAnonymizeResponse
{
    public string OriginalText { get; set; } = string.Empty;
    public string AnonymizedText { get; set; } = string.Empty;
    public int EntitiesRedactedCount { get; set; }
}
