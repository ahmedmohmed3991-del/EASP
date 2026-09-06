"""
Environment and hardware verification script for EASP.
"""
import sys

def check_environment():
    print("=" * 60)
    print("EASP SYSTEM & ENVIRONMENT DIAGNOSTICS")
    print("=" * 60)
    print(f"Python Version: {sys.version}")
    
    # 1. Core ML/DS
    try:
        import numpy as np
        import pandas as pd
        import sklearn
        print(f"[OK] NumPy {np.__version__}")
        print(f"[OK] Pandas {pd.__version__}")
        print(f"[OK] Scikit-Learn {sklearn.__version__}")
    except ImportError as e:
        print(f"[FAIL] Core ML package missing: {e}")
        
    # 2. PyTorch & CUDA
    try:
        import torch
        import torchaudio
        print(f"[OK] PyTorch {torch.__version__}")
        print(f"[OK] TorchAudio {torchaudio.__version__}")
        cuda_avail = torch.cuda.is_available()
        print(f"[OK] CUDA Available: {cuda_avail}")
        if cuda_avail:
            print(f"     Device Name: {torch.cuda.get_device_name(0)}")
            print(f"     Device Capability: {torch.cuda.get_device_capability(0)}")
            print(f"     Allocated VRAM: {torch.cuda.memory_allocated(0)/(1024**2):.1f} MB")
    except ImportError as e:
        print(f"[FAIL] PyTorch package missing: {e}")

    # 3. Transformers & Datasets
    try:
        import transformers
        import datasets
        print(f"[OK] Transformers {transformers.__version__}")
        print(f"[OK] Datasets {datasets.__version__}")
    except ImportError as e:
        print(f"[FAIL] NLP package missing: {e}")

    # 4. Audio Processing
    try:
        import librosa
        import soundfile
        print(f"[OK] Librosa {librosa.__version__}")
        print(f"[OK] SoundFile {soundfile.__version__}")
    except ImportError as e:
        print(f"[FAIL] Audio package missing: {e}")

    # 5. Visualization
    try:
        import matplotlib
        import seaborn
        print(f"[OK] Matplotlib {matplotlib.__version__}")
        print(f"[OK] Seaborn {seaborn.__version__}")
    except ImportError as e:
        print(f"[FAIL] Visualization package missing: {e}")

    print("=" * 60)

if __name__ == "__main__":
    check_environment()
