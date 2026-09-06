"""
Automated downloader for real audio deepfake datasets:
1. In-the-Wild (Zenodo)
2. WaveFake (Zenodo)
3. ASVspoof 2019 LA (Edinburgh DataShare)
"""
import os
import sys
import time
import requests
import zipfile
import tarfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
AUDIO_DIR = BASE_DIR / "data" / "audio_deepfake"

def download_file(url: str, dest_path: Path, desc: str):
    """Downloads a file with streaming chunks and progress logging."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")
    
    if dest_path.exists():
        print(f"[SKIP] {dest_path.name} already exists ({dest_path.stat().st_size / (1024**2):.1f} MB)")
        return dest_path

    print(f"\n[DOWNLOAD] Starting {desc}...")
    print(f"URL: {url}")
    print(f"Destination: {dest_path}")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(url, stream=True, headers=headers, timeout=60)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    start_time = time.time()
    last_print = 0
    
    with open(temp_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024): # 1 MB chunks
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                
                # Print progress every 1 second
                now = time.time()
                if now - last_print > 1.0 or downloaded == total_size:
                    last_print = now
                    elapsed = now - start_time
                    speed = (downloaded / (1024**2)) / max(elapsed, 0.001)
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100.0
                        print(f"  --> {pct:.1f}% | {downloaded/(1024**2):.1f} MB / {total_size/(1024**2):.1f} MB | {speed:.2f} MB/s", flush=True)
                    else:
                        print(f"  --> {downloaded/(1024**2):.1f} MB downloaded | {speed:.2f} MB/s", flush=True)
                        
    temp_path.rename(dest_path)
    print(f"[OK] Completed download: {dest_path.name} ({dest_path.stat().st_size / (1024**2):.1f} MB)")
    return dest_path

def extract_archive(archive_path: Path, target_dir: Path):
    """Extracts zip or tar archive into target directory."""
    print(f"\n[EXTRACT] Unpacking {archive_path.name} into {target_dir}...")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path, 'r') as z:
            z.extractall(target_dir)
    elif ".tar" in archive_path.name:
        with tarfile.open(archive_path, 'r:*') as t:
            t.extractall(target_dir)
            
    print(f"[OK] Finished extracting {archive_path.name}")

def download_in_the_wild():
    """Downloads & extracts the real In-the-Wild deepfake audio dataset."""
    in_the_wild_dir = AUDIO_DIR / "in_the_wild"
    
    # 1. meta.csv
    meta_url = "https://zenodo.org/records/8038573/files/meta.csv?download=1"
    download_file(meta_url, in_the_wild_dir / "meta.csv", "In-the-Wild Metadata CSV")
    
    # 2. release_in_the_wild.zip (~2.3 GB)
    zip_url = "https://zenodo.org/records/8038573/files/release_in_the_wild.zip?download=1"
    zip_file = download_file(zip_url, in_the_wild_dir / "release_in_the_wild.zip", "In-the-Wild Real Audio Dataset (~2.3 GB)")
    
    # Extract
    if not (in_the_wild_dir / "release_in_the_wild").exists():
        extract_archive(zip_file, in_the_wild_dir)

def download_wavefake_core():
    """Downloads WaveFake dataset archive (generated_audio.zip)."""
    wavefake_dir = AUDIO_DIR / "wavefake"
    
    # generated_audio.zip on Zenodo record 5642694
    wavefake_url = "https://zenodo.org/api/records/5642694/files/generated_audio.zip/content"
    wavefake_zip = download_file(wavefake_url, wavefake_dir / "generated_audio.zip", "WaveFake Deepfake Audio Dataset (generated_audio.zip)")
    if not (wavefake_dir / "generated_audio").exists():
        extract_archive(wavefake_zip, wavefake_dir)

def download_asvspoof():
    """Downloads ASVspoof 2019 Logical Access dataset (~15.2 GB)."""
    asv_dir = AUDIO_DIR / "asvspoof"
    asv_url = "https://datashare.ed.ac.uk/bitstream/handle/10283/3336/LA.zip?sequence=3&isAllowed=y"
    asv_zip = download_file(asv_url, asv_dir / "LA.zip", "ASVspoof 2019 LA Dataset (~15.2 GB)")
    if not (asv_dir / "LA").exists():
        extract_archive(asv_zip, asv_dir)

if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "in_the_wild"
    if task == "in_the_wild":
        download_in_the_wild()
    elif task == "wavefake":
        download_wavefake_core()
    elif task == "asvspoof":
        download_asvspoof()
    elif task == "all":
        download_in_the_wild()
        download_wavefake_core()
        download_asvspoof()
