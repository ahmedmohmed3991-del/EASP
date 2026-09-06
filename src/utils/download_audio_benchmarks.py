"""
Audio Deepfake Datasets Downloader & Unpacker for EASP.
Downloads the real, full benchmark datasets directly from Zenodo and Edinburgh DataShare.
"""
import urllib.request
import zipfile
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
AUDIO_DIR = BASE_DIR / "data" / "audio_deepfake"

DOWNLOAD_LINKS = {
    "in_the_wild": {
        "name": "In-the-Wild Audio Deepfake Dataset (Full Release ~2.3 GB)",
        "zip_url": "https://zenodo.org/records/8038573/files/release_in_the_wild.zip?download=1",
        "meta_url": "https://zenodo.org/records/8038573/files/meta.csv?download=1",
        "target_dir": AUDIO_DIR / "in_the_wild"
    },
    "wavefake": {
        "name": "WaveFake Dataset (Multi-Architecture Vocoders)",
        "ljspeech": "https://zenodo.org/records/5642694/files/LJSpeech-1.1.tar.bz2?download=1",
        "melgan": "https://zenodo.org/records/5642694/files/ljspeech_melgan.zip?download=1",
        "hifi_gan": "https://zenodo.org/records/5642694/files/ljspeech_hifi_gan.zip?download=1",
        "target_dir": AUDIO_DIR / "wavefake"
    },
    "asvspoof": {
        "name": "ASVspoof 2019 Logical Access (LA.zip ~15.2 GB)",
        "zip_url": "https://datashare.ed.ac.uk/bitstream/handle/10283/3336/LA.zip?sequence=3&isAllowed=y",
        "target_dir": AUDIO_DIR / "asvspoof"
    }
}

def download_progress(count, block_size, total_size):
    if total_size > 0:
        percent = int(count * block_size * 100 / total_size)
        mb = count * block_size / (1024 * 1024)
        total_mb = total_size / (1024 * 1024)
        sys.stdout.write(f"\rDownloading: {percent}% [{mb:.1f} MB / {total_mb:.1f} MB]")
        sys.stdout.flush()

def download_in_the_wild():
    """Downloads the full real In-the-Wild audio dataset (~2.3 GB)."""
    target_dir = DOWNLOAD_LINKS["in_the_wild"]["target_dir"]
    target_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = target_dir / "release_in_the_wild.zip"
    meta_path = target_dir / "meta.csv"
    
    print(f"\n--- Downloading Real In-the-Wild Audio Dataset (~2.3 GB) ---")
    print(f"URL: {DOWNLOAD_LINKS['in_the_wild']['zip_url']}")
    
    if not meta_path.exists():
        print("Fetching meta.csv...")
        urllib.request.urlretrieve(DOWNLOAD_LINKS["in_the_wild"]["meta_url"], meta_path)
        
    if not zip_path.exists():
        print("Fetching release_in_the_wild.zip...")
        urllib.request.urlretrieve(DOWNLOAD_LINKS["in_the_wild"]["zip_url"], zip_path, reporthook=download_progress)
        print("\nExtracting archive...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        print("[OK] Real In-the-Wild dataset downloaded & extracted successfully!")

if __name__ == "__main__":
    download_in_the_wild()
