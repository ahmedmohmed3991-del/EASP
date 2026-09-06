"""
Dataset Inspector & Summary Generator for EASP.
Scans all text and audio data directories, summarizes shapes, classes, and sample records,
and writes reports/dataset_inspection_report.md.
"""
import os
import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

def inspect_all_datasets():
    """Inspects all text and audio datasets."""
    records = []
    
    # 1. Prompt Injection Datasets
    pi_dir = DATA_DIR / "text_dlp" / "prompt_injection"
    if pi_dir.exists():
        for f in pi_dir.glob("*.parquet"):
            df = pd.read_parquet(f)
            records.append({
                "category": "Text DLP - Prompt Injection",
                "name": f.stem,
                "file": str(f.relative_to(BASE_DIR)),
                "rows": len(df),
                "columns": list(df.columns),
                "sample": df.head(2).to_dict(orient="records")
            })
            
    # 2. PII Dataset
    pii_dir = DATA_DIR / "text_dlp" / "pii_detection"
    if pii_dir.exists():
        for f in pii_dir.glob("*.parquet"):
            df = pd.read_parquet(f)
            records.append({
                "category": "Text DLP - PII Detection",
                "name": f.stem,
                "file": str(f.relative_to(BASE_DIR)),
                "rows": len(df),
                "columns": list(df.columns),
                "sample": df.head(2).to_dict(orient="records")
            })
            
    # 3. Social Engineering
    se_dir = DATA_DIR / "social_engineering"
    if se_dir.exists():
        for f in se_dir.glob("*.parquet"):
            df = pd.read_parquet(f)
            records.append({
                "category": "Social Engineering & Phishing",
                "name": f.stem,
                "file": str(f.relative_to(BASE_DIR)),
                "rows": len(df),
                "columns": list(df.columns),
                "sample": df.head(2).to_dict(orient="records")
            })

    # 4. Audio Deepfake - In the Wild
    audio_meta = DATA_DIR / "audio_deepfake" / "in_the_wild" / "meta.csv"
    if audio_meta.exists():
        df_audio = pd.read_csv(audio_meta)
        records.append({
            "category": "Voice Deepfake & Anti-Spoofing",
            "name": "in_the_wild_real_audio",
            "file": str(audio_meta.relative_to(BASE_DIR)),
            "rows": len(df_audio),
            "columns": list(df_audio.columns),
            "sample": df_audio.head(2).to_dict(orient="records")
        })

    # 5. Audio Deepfake - ASVspoof 2019 LA
    asv_train_proto = DATA_DIR / "audio_deepfake" / "asvspoof" / "LA" / "ASVspoof2019_LA_cm_protocols" / "ASVspoof2019.LA.cm.train.trn.txt"
    if asv_train_proto.exists():
        df_asv = pd.read_csv(asv_train_proto, sep=" ", names=["speaker_id", "audio_file", "env", "system_id", "key"])
        records.append({
            "category": "Voice Deepfake - ASVspoof 2019 LA",
            "name": "asvspoof_2019_la_train",
            "file": str(asv_train_proto.relative_to(BASE_DIR)),
            "rows": len(df_asv),
            "columns": list(df_asv.columns),
            "sample": df_asv.head(2).to_dict(orient="records")
        })

    # 6. Audio Deepfake - WaveFake
    wavefake_gen = DATA_DIR / "audio_deepfake" / "wavefake" / "generated_audio"
    if wavefake_gen.exists():
        vocoders = [d.name for d in wavefake_gen.iterdir() if d.is_dir()]
        total_wavs = sum(len(list(d.glob("*.wav"))) for d in wavefake_gen.iterdir() if d.is_dir())
        records.append({
            "category": "Voice Deepfake - WaveFake",
            "name": "wavefake_multi_vocoder",
            "file": str(wavefake_gen.relative_to(BASE_DIR)),
            "rows": total_wavs,
            "columns": ["vocoder_subdirectories: " + ", ".join(vocoders[:4]) + "..."],
            "sample": [{"vocoder_architectures": vocoders, "total_generated_wavs": total_wavs}]
        })
            
    return records

def generate_markdown_report(records):
    """Formats inspection records into a comprehensive Markdown report."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / "dataset_inspection_report.md"
    
    content = "# EASP Dataset Inspection & Exploration Report\n\n"
    content += "This report summarizes all downloaded real datasets, schemas, volume metrics, and sample records.\n\n"
    content += "## Summary Overview\n\n"
    content += "| Category | Dataset Identifier | File Path | Total Rows / Files | Columns |\n"
    content += "| :--- | :--- | :--- | :--- | :--- |\n"
    
    for r in records:
        content += f"| **{r['category']}** | `{r['name']}` | `{r['file']}` | **{r['rows']:,}** | `{', '.join(r['columns'])}` |\n"
        
    content += "\n---\n\n## Detailed Dataset Inspection & Sample Records\n\n"
    
    for r in records:
        content += f"### {r['name']} ({r['category']})\n\n"
        content += f"- **Path:** `{r['file']}`\n"
        content += f"- **Count:** `{r['rows']:,}` records/files\n"
        content += f"- **Columns:** {', '.join([f'`{c}`' for c in r['columns']])}\n\n"
        content += "#### Sample Records:\n\n```json\n"
        content += json.dumps(r['sample'], indent=2, ensure_ascii=False, default=str)
        content += "\n```\n\n"
        
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"[OK] Generated inspection report: {report_file}")
    return report_file

if __name__ == "__main__":
    records = inspect_all_datasets()
    generate_markdown_report(records)
