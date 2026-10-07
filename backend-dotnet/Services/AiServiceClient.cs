using System.Text.Json;

namespace EASP.API.Services
{
    // Python owns inference. This client validates the contract and never fabricates a result.
    public class AiServiceClient
    {
        private readonly HttpClient _http;
        public AiServiceClient(HttpClient http, ILogger<AiServiceClient> logger) => _http = http;

        public static bool Score(JsonElement value, string name) =>
            value.ValueKind == JsonValueKind.Object && value.TryGetProperty(name, out var score) &&
            score.ValueKind == JsonValueKind.Number && score.TryGetDouble(out var number) &&
            double.IsFinite(number) && number >= 0 && number <= 1;
        private static bool Has(JsonElement value, string name, JsonValueKind kind) =>
            value.ValueKind == JsonValueKind.Object && value.TryGetProperty(name, out var field) && field.ValueKind == kind;
        private static bool HasBoolean(JsonElement value, string name) =>
            Has(value, name, JsonValueKind.True) || Has(value, name, JsonValueKind.False);

        private static bool ValidMapping(JsonElement mapping) =>
            Has(mapping, "token_id", JsonValueKind.String) &&
            Has(mapping, "entity_type", JsonValueKind.String) &&
            Has(mapping, "original_value", JsonValueKind.String);

        public static bool ValidDlp(JsonElement data) =>
            Score(data, "sensitivity_score") &&
            Has(data, "redacted_text", JsonValueKind.String) &&
            Has(data, "entities", JsonValueKind.Array) &&
            HasBoolean(data, "has_sensitive_data") &&
            Has(data, "mappings", JsonValueKind.Array) &&
            data.GetProperty("mappings").EnumerateArray().All(ValidMapping);

        public static bool ValidNlp(JsonElement data) =>
            Score(data, "social_engineering_score") && Has(data, "threats_detected", JsonValueKind.Array);

        private static bool ValidVoice(JsonElement voice) =>
            Has(voice, "success", JsonValueKind.True) &&
            Has(voice, "model_loaded", JsonValueKind.True) &&
            Score(voice, "spoof_score") && HasBoolean(voice, "is_deepfake");

        private static bool ValidTranscription(JsonElement transcription) =>
            Has(transcription, "success", JsonValueKind.True) &&
            Has(transcription, "transcript", JsonValueKind.String);

        public static bool ValidAudio(JsonElement data) =>
            Has(data, "voice_deepfake", JsonValueKind.Object) &&
            Has(data, "transcription", JsonValueKind.Object) &&
            ValidVoice(data.GetProperty("voice_deepfake")) &&
            ValidTranscription(data.GetProperty("transcription")) &&
            Has(data, "social_engineering", JsonValueKind.Object) && ValidNlp(data.GetProperty("social_engineering")) &&
            Has(data, "dlp", JsonValueKind.Object) && ValidDlp(data.GetProperty("dlp"));

        private async Task<AiServiceResult<JsonElement>> SendAsync(string path, HttpContent? content, Func<JsonElement, bool> valid)
        {
            try
            {
                using var request = new HttpRequestMessage(content == null ? HttpMethod.Get : HttpMethod.Post, path) { Content = content };
                using var response = await _http.SendAsync(request);
                if (!response.IsSuccessStatusCode) return new();
                var root = await response.Content.ReadFromJsonAsync<JsonElement>();
                if (!Has(root, "status", JsonValueKind.String) || root.GetProperty("status").GetString() != "success" ||
                    !root.TryGetProperty("data", out var data) || !valid(data)) return new();
                return new() { Success = true, Data = data.Clone() };
            }
            catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException or JsonException or InvalidOperationException)
            { return new(); }
        }
        public Task<AiServiceResult<JsonElement>> ScanDlpAsync(string prompt, int userId) =>
            SendAsync("/dlp/scan", JsonContent.Create(new { text = prompt, user_id = userId.ToString() }), ValidDlp);
        public Task<AiServiceResult<JsonElement>> ClassifyNlpAsync(string text) =>
            SendAsync("/nlp/classify", JsonContent.Create(new { text }), ValidNlp);
        public Task<AiServiceResult<JsonElement>> AnalyzeAudioPipelineAsync(byte[] audioData, string filename, string? speakerProfileId = null)
        {
            var form = new MultipartFormDataContent();
            form.Add(new ByteArrayContent(audioData), "file", filename);
            if (!string.IsNullOrWhiteSpace(speakerProfileId)) form.Add(new StringContent(speakerProfileId), "speaker_profile_id");
            return SendAsync("/audio/analyze", form, ValidAudio);
        }
        public Task<AiServiceResult<JsonElement>> GetSpeakerProfilesAsync() =>
            SendAsync("/audio/speaker-profiles", null, data => data.ValueKind == JsonValueKind.Array);
    }
    public class AiServiceResult<T>
    {
        public bool Success { get; set; }
        public T Data { get; set; } = default!;
    }
}
