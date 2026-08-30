import yaml
import torch
import numpy as np
import soundfile as sf
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score, roc_curve
from model import RawNet

with open('model_config_RawNet.yaml', 'r') as f:
    parser1 = yaml.load(f, Loader=yaml.FullLoader)

d_args = parser1['model']
device = 'cpu'
model = RawNet(d_args, device).to(device)
checkpoint = torch.load('rawnet2_asvspoof_LA.pth', map_location=device)
model.load_state_dict(checkpoint)
model.eval()

y_true = []
y_scores = []

with open('sample_data/labels.txt', 'r') as f:
    lines = f.readlines()

for line in lines:
    filename, label = line.strip().split('\t')
    label = int(label)

    audio, sr = sf.read(f'sample_data/{filename}')
    audio = audio.astype(np.float32)

    if len(audio) > 64600:
        audio = audio[:64600]
    else:
        audio = np.pad(audio, (0, 64600 - len(audio)))

    x = torch.from_numpy(audio).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(x)
        probs = torch.softmax(output, dim=1)
        bonafide_score = probs[0][0].item()

    y_true.append(label)
    y_scores.append(bonafide_score)
    print(f'{filename}: true={label}, model_score={bonafide_score:.4f}')

y_true = np.array(y_true)
y_scores = np.array(y_scores)
y_pred = (y_scores >= 0.5).astype(int)

print('\n=== RESULTS ===')
acc = accuracy_score(y_true, y_pred)
print(f'Accuracy: {acc:.4f}')

cm = confusion_matrix(y_true, y_pred)
print(f'Confusion Matrix:\n{cm}')

if len(np.unique(y_true)) > 1:
    auc = roc_auc_score(y_true, y_scores)
    print(f'ROC-AUC: {auc:.4f}')

    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    fnr = 1 - tpr
    eer_idx = np.nanargmin(np.abs(fnr - fpr))
    eer = fpr[eer_idx]
    print(f'EER: {eer:.4f}')
else:
    print('EER/ROC-AUC not computable: only one class present in this small sample.')