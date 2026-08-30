from datasets import load_dataset
import soundfile as sf
import os

os.makedirs("sample_data", exist_ok=True)

print("Downloading small sample from ASVspoof2021 LA eval set...")
ds = load_dataset(
    "SpeechAntiSpoofingBenchmarks/ASVspoof2021_LA",
    split="eval",
    streaming=True
)

labels_file = open("sample_data/labels.txt", "w")

count = 0
max_samples = 20

for item in ds:
    if count >= max_samples:
        break
    audio = item["audio"]["array"]
    sr = item["audio"]["sampling_rate"]
    label = item["label"]  # bonafide or spoof

    filename = f"sample_{count:02d}.wav"
    filepath = os.path.join("sample_data", filename)
    sf.write(filepath, audio, sr)

    labels_file.write(f"{filename}\t{label}\n")
    print(f"[{count+1}/{max_samples}] Saved {filename} -> {label}")
    count += 1

labels_file.close()
print("Done! Files saved in sample_data/ folder")