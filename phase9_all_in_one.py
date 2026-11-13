"""
EASP Phase 9 - mBERT social-engineering classifier - ALL IN ONE FILE

Put these next to this file, then just run it (VS Code: Run Python File):
    synthetic_calls/      (folder from the zip: train.jsonl, val.jsonl, test.jsonl, gold_unreviewed.jsonl ...)
    train_data.csv        (external BothBosu dialogues)
    test_data.csv

What it does, in order:
    1) builds the EASP-SE-Corpus with the 4 labels  -> data/processed/*.csv
    2) trains mBERT (mean pooling, warmup, early stopping)
    3) tunes one threshold per label on the validation set -> thresholds.json
    4) evaluates on TEST synthetic and TEST external (and on the gold set once you review it)

Useful options:
    python phase9_all_in_one.py --quick                 # tiny run, just to check that everything works
    python phase9_all_in_one.py --sources synthetic     # ablation: synthetic only (does the external data help?)
    python phase9_all_in_one.py --rebuild               # rebuild the CSVs from the raw files
    my_lines.csv (optional, next to this file): sentences YOU wrote - split=train goes to training,
                 split=test stays hidden and is used as an independent test (see my_lines_template.csv)
    python phase9_all_in_one.py --regenerate            # make NEW synthetic calls with exact labels (needs generate_dataset_v2.py next to this file), then rebuild
    python phase9_all_in_one.py --make_review_sheet 300 # sheet of external windows for you (and a friend) to label by hand
    python phase9_all_in_one.py --kappa data/processed/review_external.csv   # agreement between two reviewers

Needs: torch, transformers, pandas, numpy, scikit-learn.
Use a GPU (Colab / Kaggle). On CPU it will take hours - use --quick first.
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup

# every path is relative to this file, so it works from any working folder
BASE = Path(__file__).resolve().parent


def find_file(name, look_in):
    """Look for a file next to this script, then in any sub-folder (handles nested zip folders)."""
    for folder in look_in:
        if (folder / name).exists():
            return folder / name
    hits = [h for h in BASE.rglob(name) if "data" + os.sep + "processed" not in str(h)]
    if hits:
        return hits[0]
    raise FileNotFoundError(
        f"Could not find '{name}' anywhere under {BASE}\n"
        f"Put the files from synthetic_calls.zip (train.jsonl, val.jsonl, test.jsonl, gold_unreviewed.jsonl) "
        f"and train_data.csv / test_data.csv next to this script.")


def locate_synth_dir():
    """Prefer the v2 folder (labels by construction), then the old one, then search."""
    for folder in [BASE / "synthetic_calls_v2", BASE / "synthetic_calls", BASE]:
        if (folder / "train.jsonl").exists():
            return folder
    hits = [h for h in BASE.rglob("train.jsonl") if "processed" not in str(h)]
    return hits[0].parent if hits else None


SYNTH_DIR = locate_synth_dir()
EXT_TRAIN = find_file("train_data.csv", [BASE])
EXT_TEST = find_file("test_data.csv", [BASE])
OUT_DIR = BASE / "data" / "processed"
DATA_DIR = str(OUT_DIR)
WEIGHTS_PATH = str(BASE / "best_mbert_social_engineering.pt")
THRESHOLDS_PATH = str(BASE / "thresholds.json")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
LABELS = ["urgency", "authority_impersonation", "credential_request", "payment_request"]
CALLER_AUG = True                      # also train on the caller's lines alone (no other speaker)
MY_LINES = BASE / "my_lines.csv"       # sentences written by hand (optional)
WINDOW_WORDS = 80   # a window is ~80-160 words, so it fits in 256 tokens
MODEL_NAME = "bert-base-multilingual-cased"
MAX_LEN = 256
DEFAULT_THRESHOLDS = {l: 0.5 for l in LABELS}


# ===============================================================
# PART 1 - BUILD THE CORPUS
# Labels are proxy labels made from the CALLER's turns only; a benign call is all zeros.
# ===============================================================
# ---------------------------------------------------------------
# Patterns (applied to caller text only)
# ---------------------------------------------------------------
PATTERNS = {
    "urgency": [
        r"\b(urgent(ly)?|immediately|right now|right away|at once|asap|expires?|expired|suspended|final (notice|warning)|last (chance|warning)|before it'?s too late|cannot wait|can'?t wait)\b",
        r"\b(every minute counts|high[- ]priority|time[- ]sensitive|limited time|act (now|fast|quickly)|don'?t (wait|delay)|as soon as possible|running out of time)\b",
        r"\bwithin \d+ (minutes?|hours?|days?)\b",
        r"\bin \d+ minutes\b",
        r"(suspend|block|expire|cancel|court|lock|close|lose|lost|destroy)\w*[^.]{0,40}\b(today|tonight|now)\b",
        r"\b(confirm|pay|verify|act|send|provide|give|do (this|it))\b[^.]{0,15}\bnow\b",
        # Egyptian Arabic
        r"فورا|فوراً|بسرعة|حالا|حالاً|الإنذار الأخير|مينفعش يستنى|لازم يخلص|هيتلغي|قبل ما يتلغي|هيقفل|هيتقفل|آخر النهاردة",
        r"خلال \d+ دقيق",
        r"(دلوقتي|النهاردة)[^.]{0,20}(قبل|لازم)|(لازم|قبل)[^.]{0,20}(دلوقتي|النهاردة)",
    ],
    "authority_impersonation": [
        r"\b(this is|i'?m|i am|my name is|calling|speaking)\b[^.]{0,45}\bfrom\b[^.]{0,40}",
        r"\b(officer|inspector|detective|your (manager|boss|director)|the (ceo|director)|managing director|chairman)\b",
        r"\b(security (team|department)|fraud (department|team)|it (helpdesk|help desk|support|department)|help ?desk|tax authority|social security administration|customer service|technical support|compliance)\b",
        # Egyptian Arabic
        r"مديرك|المدير العام|رئيس مجلس|الدكتور سمير|أستاذ خالد|الإدارة الأمنية|مصلحة الضرائب|فريق الـ ?IT|الدعم الفني|خدمة العملاء|قسم الفواتير|البريد المصري|الشرطة|النيابة|الجمارك|الهيلب",
        r"(معاك|أنا|بنكلم|بنتصل)[^.]{0,30}(من|في) (ال)?(بنك|شركة|إدارة|مصلحة|فودافون|أورنج|اتصالات|أرامكس|بوسطة|DHL)",
    ],
    "credential_request": [
        r"\b(password|passcode|pin( code| number)?|otp|one[- ]time|verification code|security code|cvv|card (number|details)|bank card|credit card|debit card|log ?-?in|credentials|national id|social security( number)?|ssn|account (number|details)|bank account|date of birth|mother'?s maiden)\b",
        r"\b(confirm|verify|provide|give|share|tell|read|send)\b[^.]{0,25}\b(address|full name|birth)\b",
        r"\b(remote access|anydesk|teamviewer|download(ing)? (our|the) [a-z ]{0,20}(software|app|program))\b",
        # Egyptian Arabic
        r"الباسورد|الرقم السري|كلمة السر|كلمة المرور|الكود|الرمز|الأو تي بي|OTP|رقمك القومي|الرقم القومي|بيانات الكارت|رقم الكارت|بيانات الحساب|رقم الحساب|لوجين|اللوجين|CVV",
    ],
    "payment_request": [
        r"\b(pay(ing|ment)?|transfer|wire|deposit|fees?|fine|penalty|gift cards?|bitcoin|crypto|western union|cover (it|the)|charge|send (the )?(amount|money|\$?\d+))\b",
        # Egyptian Arabic
        r"ادفع|تدفع|رسوم|غرامة|الغرامة|اشحن|تغطي|سدد|مصاريف|إيداع",
        r"حو(ل|ّل|لي) (المبلغ|فلوس|الفلوس|مبلغ|\d)",
        r"ابعت(لي)? (المبلغ|فلوس|الفلوس|رصيد)",
    ],
}
COMPILED = {lab: [re.compile(p, re.IGNORECASE) for p in pats] for lab, pats in PATTERNS.items()}


def label_text(caller_text):
    """Return a dict of 0/1 for the 4 labels based on caller text."""
    out = {}
    for lab in LABELS:
        out[lab] = int(any(p.search(caller_text) for p in COMPILED[lab]))
    return out


# ---------------------------------------------------------------
# Turns -> windows
# ---------------------------------------------------------------
def make_windows(turns, is_scam):
    """turns = list of (speaker, text, tags). tags is a list (labels by construction) or None."""
    windows, cur_turns, cur_words = [], [], 0
    for spk, txt, tg in turns:
        cur_turns.append((spk, txt, tg))
        cur_words += len(txt.split())
        if cur_words >= WINDOW_WORDS:
            windows.append(cur_turns)
            cur_turns, cur_words = [], 0
    if cur_turns:
        # glue a tiny leftover to the previous window
        if windows and cur_words < WINDOW_WORDS // 2:
            windows[-1].extend(cur_turns)
        else:
            windows.append(cur_turns)

    rows = []
    for i, w in enumerate(windows):
        text = " ".join(t for _, t, _ in w)
        caller_turns = [(t, tg) for s, t, tg in w if s == "caller"]
        if not is_scam:
            labs = {l: 0 for l in LABELS}
        elif all(tg is not None for _, tg in caller_turns):
            # exact labels: the generator wrote down the tactic of every line
            labs = {l: int(any(l in tg for _, tg in caller_turns)) for l in LABELS}
        else:
            labs = label_text(" ".join(t for t, _ in caller_turns))   # keyword fallback
        rows.append({"window_idx": i, "text": text, **labs})
    return rows


def rows_for_call(call_id, source, language, attack_type, is_scam, turns):
    rows = make_windows(turns, is_scam)
    for r in rows:
        r.update(call_id=call_id, source=source, language=language,
                 attack_type=attack_type, is_scam=int(is_scam))
    return rows


# ---------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------
def load_synth(split_name, caller_only=False):
    rows = []
    for line in open(SYNTH_DIR / f"{split_name}.jsonl", encoding="utf-8"):
        c = json.loads(line)
        turns = [(d["speaker"], d["text"], d.get("tags")) for d in c["dialogue"]
                 if not caller_only or d["speaker"] == "caller"]
        call_id = c["id"] + ("_co" if caller_only else "")
        rows += rows_for_call(call_id, "synthetic", c["language"], c["attack_type"],
                              c["label"] == 1, turns)
    return pd.DataFrame(rows)


def load_my_lines(path):
    """Sentences written by hand. split=train -> training, split=test -> kept hidden for testing."""
    if not Path(path).exists():
        return None, None
    d = pd.read_csv(path).dropna(subset=["text"]).reset_index(drop=True)
    for l in LABELS:
        d[l] = pd.to_numeric(d[l], errors="coerce").fillna(0).astype(int) if l in d.columns else 0
    d["split"] = d["split"].astype(str).str.strip().str.lower()
    d["call_id"] = [f"user_{i:04d}" for i in range(len(d))]
    d["window_idx"] = 0
    d["source"] = "user_lines"
    d["attack_type"] = "user_line"
    d["is_scam"] = (d[LABELS].sum(axis=1) > 0).astype(int)
    if "language" not in d.columns:
        d["language"] = "unknown"
    keep = ["call_id", "source", "language", "attack_type", "is_scam", "window_idx", "text"] + LABELS
    train = d[d["split"] == "train"][keep]
    test = d[d["split"] == "test"][keep]
    return train, test


def parse_ext_dialogue(text):
    """'Innocent: ... Suspect: ...' -> [(caller/callee, text), ...]"""
    parts = re.split(r"(Innocent:|Suspect:)", text)
    turns = []
    for i in range(1, len(parts) - 1, 2):
        spk = "caller" if parts[i] == "Suspect:" else "callee"
        msg = parts[i + 1].strip()
        if msg:
            turns.append((spk, msg, None))
    return turns


def load_ext(csv_path, prefix):
    df = pd.read_csv(csv_path)
    rows = []
    for i, r in df.iterrows():
        turns = parse_ext_dialogue(str(r["dialogue"]))
        if not turns:
            continue
        rows += rows_for_call(f"{prefix}_{i:05d}", "external_bothbosu", "en",
                              str(r["type"]), r["labels"] == 1, turns)
    return pd.DataFrame(rows)


def load_gold():
    rows = []
    for line in open(SYNTH_DIR / "gold_unreviewed.jsonl", encoding="utf-8"):
        c = json.loads(line)
        caller_turns = [d for d in c["dialogue"] if d["speaker"] == "caller"]
        if c["label"] != 1:
            labs = {l: 0 for l in LABELS}
        elif all("tags" in d for d in caller_turns):
            labs = {l: int(any(l in d["tags"] for d in caller_turns)) for l in LABELS}
        else:
            labs = label_text(" ".join(d["text"] for d in caller_turns))
        row = {"call_id": c["id"], "language": c["language"], "attack_type": c["attack_type"],
               "is_scam": c["label"], "text": c["text"]}
        row.update({f"auto_{l}": labs[l] for l in LABELS})
        row.update({f"reviewed_{l}": "" for l in LABELS})
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------
def label_table(df, by):
    scam = df[df["is_scam"] == 1]
    return scam.groupby(by)[LABELS].mean().round(2)


def build_corpus():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if SYNTH_DIR is None:
        raise FileNotFoundError("No synthetic calls found. Put the synthetic_calls folder next to this file "
                                "or run with --regenerate (needs generate_dataset_v2.py).")
    first = json.loads(open(SYNTH_DIR / "train.jsonl", encoding="utf-8").readline())
    exact = "tags" in first["dialogue"][0]
    print(f"[+] synthetic data: {SYNTH_DIR.name} | labels by construction: {'YES' if exact else 'no (keyword rules)'}")

    synth_train = load_synth("train")
    if CALLER_AUG:     # same calls again with only the caller speaking (the model also sees that format)
        synth_train = pd.concat([synth_train, load_synth("train", caller_only=True)], ignore_index=True)
    synth_val = load_synth("val")
    test_synth = load_synth("test")

    ext_all = load_ext(EXT_TRAIN, "ext_train")
    ext_test = load_ext(EXT_TEST, "ext_test")

    # validation split for the external data: by call, not by window
    calls = ext_all.drop_duplicates("call_id")[["call_id", "is_scam"]]
    tr_ids, va_ids = train_test_split(calls["call_id"], test_size=0.1,
                                      random_state=42, stratify=calls["is_scam"])
    ext_train = ext_all[ext_all["call_id"].isin(tr_ids)]
    ext_val = ext_all[ext_all["call_id"].isin(va_ids)]

    train = pd.concat([synth_train, ext_train], ignore_index=True)
    val = pd.concat([synth_val, ext_val], ignore_index=True)

    mine_train, mine_test = load_my_lines(MY_LINES)
    if mine_train is not None and len(mine_train):
        train = pd.concat([train, mine_train], ignore_index=True)
        print(f"[+] my_lines.csv: {len(mine_train)} sentences added to training, {len(mine_test)} kept for testing")
    test_user_path = OUT_DIR / "test_user.csv"
    if mine_test is not None and len(mine_test):
        mine_test.to_csv(test_user_path, index=False, encoding="utf-8-sig")
    elif test_user_path.exists():
        test_user_path.unlink()

    train.to_csv(OUT_DIR / "train.csv", index=False, encoding="utf-8-sig")
    val.to_csv(OUT_DIR / "val.csv", index=False, encoding="utf-8-sig")
    test_synth.to_csv(OUT_DIR / "test_synth.csv", index=False, encoding="utf-8-sig")
    ext_test.to_csv(OUT_DIR / "test_ext.csv", index=False, encoding="utf-8-sig")
    load_gold().to_csv(OUT_DIR / "gold_review_4labels.csv", index=False, encoding="utf-8-sig")

    # ---- report ----
    lines = []
    for name, d in [("train", train), ("val", val), ("test_synth", test_synth), ("test_ext", ext_test)]:
        lines.append(f"== {name}: {d['call_id'].nunique()} calls, {len(d)} windows")
        lines.append(f"   scam windows: {int(d['is_scam'].sum())}")
        lines.append("   positives per label: " + ", ".join(f"{l}={int(d[l].sum())}" for l in LABELS))
    lines.append("\nShare of scam windows with each label, by source + attack type:")
    all_df = pd.concat([train, val, test_synth, ext_test])
    lines.append(label_table(all_df, ["source", "attack_type"]).to_string())
    lines.append("\nScam windows with NO label at all (rules found nothing):")
    scam = all_df[all_df["is_scam"] == 1]
    none_mask = scam[LABELS].sum(axis=1) == 0
    lines.append(f"   {int(none_mask.sum())} of {len(scam)} ({none_mask.mean():.1%})")
    report = "\n".join(lines)
    (OUT_DIR / "corpus_report.txt").write_text(report, encoding="utf-8")
    print(report)
    return None





# ===============================================================
# CHALLENGE SET - 40 short calls (EN + Egyptian Arabic) written to BREAK keyword shortcuts:
#   - scam calls whose tactics are said WITHOUT the usual trigger words
#   - benign calls that DO contain trigger words (bank, pin, transfer, today, ...)
# Labels follow the meaning of the call, not the words. They were written by an AI assistant,
# so please read them once and fix any label you disagree with.
# columns: language, text, urgency, authority_impersonation, credential_request, payment_request
# ===============================================================
CHALLENGE_ROWS = [
    # ---- English scams (tactics without the obvious keywords) ----
    ("en", "hi i work with the tax office and there is a problem with your file you need to sort this out before the end of the day or a case will be opened", 1, 1, 0, 0),
    ("en", "good afternoon i am calling on behalf of the head office you were charged twice by mistake we can only reverse it if you read me the little code the app just showed you", 0, 1, 1, 0),
    ("en", "you won a free holiday we just need a small amount for the booking you can settle it by buying a voucher at any shop and reading me the number on the back", 0, 0, 0, 1),
    ("en", "mom it's me my phone broke so i'm on a friend's phone i'm in trouble and i need money sent to this account right now please don't tell dad", 1, 0, 0, 1),
    ("en", "this is the it guys we are moving mailboxes tonight and yours needs a quick check so type what you use to get into your mailbox in the form i am sending", 1, 1, 1, 0),
    ("en", "i'm the new finance director the ceo asked me to arrange a confidential supplier invoice move the funds this afternoon and keep it between us", 1, 1, 0, 1),
    ("en", "our system picked your number for a cash prize but first we need a photo of the front and back of your card", 0, 0, 1, 0),
    ("en", "hello i'm with the electricity board your meter shows unpaid usage and the power goes off in thirty minutes unless you cover it by phone", 1, 1, 0, 1),
    ("en", "your account has a problem and i need to confirm it's really you so tell me the numbers you use to sign in and the answer to your security question", 0, 0, 1, 0),
    ("en", "agent smith from the investigation unit your bank account is being used for crime so move your savings to a safe account that we give you right away", 1, 1, 0, 1),
    ("en", "congratulations you qualify for a loan with no checks just send the first installment as a processing deposit today and we release the money", 1, 0, 0, 1),
    ("en", "hi i'm calling from microsoft your computer is sending us errors let me connect to it remotely so i can fix it please install the small program i tell you about", 0, 1, 1, 0),
    # ---- English benign (contain trigger words, but nothing suspicious is asked) ----
    ("en", "hi this is sara from the pharmacy your order is ready to collect any time today there is nothing to pay", 0, 0, 0, 0),
    ("en", "this is your bank's automated message your statement is ready online and we will never ask you for your pin or password", 0, 0, 0, 0),
    ("en", "calling from it support to let you know the wifi will be down tonight between two and three nothing for you to do", 0, 0, 0, 0),
    ("en", "hey it's omar can you transfer me the notes from yesterday's lecture i missed it thanks", 0, 0, 0, 0),
    ("en", "your delivery is arriving today between two and four the courier will call you from the gate and there are no fees due", 0, 0, 0, 0),
    ("en", "hello this is dr nour's clinic confirming your appointment today at four if you can't make it just reply and we'll move it", 0, 0, 0, 0),
    ("en", "this is a reminder from the library that your book is due next week you can renew it online any time", 0, 0, 0, 0),
    ("en", "hi this is customer service returning your call about the broken kettle we are sending a replacement and no payment or details are needed from you", 0, 0, 0, 0),
    # ---- Egyptian Arabic scams ----
    ("ar", "أهلا يا فندم معاك من قسم المتابعة بالبنك في عملية مشبوهة على حسابك ابعتلي الأرقام اللي وصلتك في رسالة عشان نوقفها", 0, 1, 1, 0),
    ("ar", "حضرتك كسبت جايزة معانا بس لازم تبعت خمسمية جنيه تمن التوصيل في خلال ساعة وإلا الجايزة هتروح لحد تاني", 1, 0, 0, 1),
    ("ar", "أنا الأستاذ هشام مدير الإدارة ومحتاج منك حاجة سريعة النهاردة قبل ما نخرج نزّل الفلوس في حساب المورد وسيبها سر بينا", 1, 1, 0, 1),
    ("ar", "مساء الخير انا من شركة الكهرباء فاتورتك فيها غلط لازم نصححها دلوقتي قولي رقم البطاقة والتاريخ اللي عليها", 1, 1, 1, 0),
    ("ar", "يا باشا ده أنا ابنك موبايلي باظ وواقع في مشكلة ومحتاج فلوس بسرعة حولها على الرقم ده ومتقولش لأبوي", 1, 0, 0, 1),
    ("ar", "معاك الدعم الفني جهازك فيه فيروس لازم نتحكم فيه من بعيد علشان نصلحه نزل البرنامج اللي هقولك عليه", 0, 1, 1, 0),
    ("ar", "تحب تشتغل من البيت وتكسب كويس بس محتاجين تدخل كل بياناتك الشخصية وصورة البطاقة على اللينك اللي هبعتهولك", 0, 0, 1, 0),
    ("ar", "حضرتك من النيابة العامة في قضية باسمك ومينفعش تقفل الخط ولازم تقولي رقمك القومي دلوقتي", 1, 1, 1, 0),
    ("ar", "تمام يا فندم احنا من فريق الأمان في تطبيق المحفظة حسابك هيتقفل النهاردة لو مدخلتش كلمة السر على الصفحة اللي بعتناها", 1, 1, 1, 0),
    ("ar", "ألو أنا مدير الفرع محتاج كارت شحن بألف جنيه ضروري وابعتلي الكود اللي عليه", 1, 1, 0, 1),
    ("ar", "مبروك اتسحب رقمك وكسبت عربية بس ادفع رسوم التسجيل النهاردة وهنوصلك العربية", 1, 0, 0, 1),
    ("ar", "لو عايز تسترد فلوسك المحجوزة ادخل على الموقع ده وحط رقم الكارت والرقم السري", 0, 0, 1, 0),
    # ---- Egyptian Arabic benign ----
    ("ar", "أهلا يا فندم معاك من البنك بنأكد معاد مقابلتك بكره الساعة اتناشر مفيش حاجة مطلوبة منك", 0, 0, 0, 0),
    ("ar", "حسابك على التطبيق اتحدث بنجاح ومتشاركش الباسورد أو الكود مع أي حد حتى لو قالك إنه من البنك", 0, 0, 0, 0),
    ("ar", "مصلحة الضرائب بتفكرك إن آخر ميعاد لتقديم الإقرار آخر الشهر ومفيش حاجة تدفعها دلوقتي", 0, 0, 0, 0),
    ("ar", "معاك الدعم الفني بنبلغك إن الإنترنت هيفصل الليلة من اتنين لتلاتة الصبح ومش مطلوب منك حاجة", 0, 0, 0, 0),
    ("ar", "طلبك وصل النهاردة والمندوب هيتصل بيك من قدام البيت والدفع كان أونلاين خلاص", 0, 0, 0, 0),
    ("ar", "ألو يا أحمد ابعتلي المحاضرة بتاعة امبارح مجتش النهاردة", 0, 0, 0, 0),
    ("ar", "أهلا بحضرتك من خدمة العملاء بنرد على شكواك والمنتج هيتبدل من غير أي رسوم ومش محتاجين منك بيانات", 0, 0, 0, 0),
    ("ar", "الدكتور بيأكد ميعادك النهاردة الساعة أربعة ولو مش هتيجي ابعتلنا رسالة", 0, 0, 0, 0),
]

# ===============================================================
# PART 2 - MODEL, TRAINING, EVALUATION
# ===============================================================
# ---------------------------------------------------------------
# Model
# ---------------------------------------------------------------
class SocialEngineeringmBERT(nn.Module):
    def __init__(self, model_name=MODEL_NAME, num_labels=4, dropout=0.3):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, num_labels)

    def forward(self, input_ids, attention_mask):
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        # mean pooling: average the token vectors, ignoring padding
        mask = attention_mask.unsqueeze(-1).float()
        summed = (out.last_hidden_state * mask).sum(dim=1)
        pooled = summed / mask.sum(dim=1).clamp(min=1e-9)
        return self.classifier(self.dropout(pooled))


# ---------------------------------------------------------------
# Data
# ---------------------------------------------------------------
class WindowDataset(Dataset):
    def __init__(self, df, tokenizer):
        self.texts = df["text"].astype(str).tolist()
        self.labels = df[LABELS].values.astype(np.float32)
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, i):
        enc = self.tokenizer(self.texts[i], max_length=MAX_LEN, padding="max_length",
                             truncation=True, return_tensors="pt")
        return {
            "input_ids": enc["input_ids"].flatten(),
            "attention_mask": enc["attention_mask"].flatten(),
            "labels": torch.tensor(self.labels[i]),
        }


def make_loader(df, tokenizer, batch_size, shuffle):
    return DataLoader(WindowDataset(df, tokenizer), batch_size=batch_size, shuffle=shuffle)


def get_pos_weight(df, cap=20.0):
    pos = df[LABELS].values.sum(axis=0)
    neg = len(df) - pos
    return torch.tensor(np.clip(neg / np.clip(pos, 1, None), 1.0, cap), dtype=torch.float32)


# ---------------------------------------------------------------
# Training
# ---------------------------------------------------------------
def get_probs(model, loader):
    model.eval()
    probs, targets = [], []
    with torch.no_grad():
        for b in loader:
            logits = model(b["input_ids"].to(DEVICE), b["attention_mask"].to(DEVICE))
            probs.append(torch.sigmoid(logits).cpu().numpy())
            targets.append(b["labels"].numpy())
    return np.vstack(probs), np.vstack(targets)


def train(model, train_loader, val_loader, pos_weight, epochs, lr, patience):
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, int(0.1 * total_steps), total_steps)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight.to(DEVICE))

    best_f1, bad_epochs = -1.0, 0
    for epoch in range(epochs):
        model.train()
        total = 0.0
        for step, b in enumerate(train_loader, 1):
            optimizer.zero_grad()
            logits = model(b["input_ids"].to(DEVICE), b["attention_mask"].to(DEVICE))
            loss = loss_fn(logits, b["labels"].to(DEVICE))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total += loss.item()
            if step % 100 == 0:
                print(f"   epoch {epoch + 1}: batch {step}/{len(train_loader)}  loss {total / step:.4f}", flush=True)

        val_probs, val_y = get_probs(model, val_loader)
        val_f1 = f1_score(val_y, val_probs >= 0.5, average="macro", zero_division=0)
        print(f"Epoch {epoch + 1}/{epochs}  train loss {total / len(train_loader):.4f}  val macro-F1 {val_f1:.4f}")

        if val_f1 > best_f1:
            best_f1, bad_epochs = val_f1, 0
            torch.save(model.state_dict(), WEIGHTS_PATH)
            print("   -> best so far, weights saved")
        else:
            bad_epochs += 1
            if bad_epochs >= patience:
                print("   early stop")
                break

    model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=DEVICE))
    return model


def tune_thresholds(probs, y):
    """One threshold per label, from the validation set only.
    When the model is very sure, many thresholds give the same F1, so we take the middle of all the
    thresholds that are about as good as the best one (more stable than the first or last of them)."""
    grid = np.arange(0.10, 0.91, 0.05)
    thresholds = {}
    for i, label in enumerate(LABELS):
        scores = np.array([f1_score(y[:, i], probs[:, i] >= t, zero_division=0) for t in grid])
        good = grid[scores >= scores.max() - 0.005]
        thresholds[label] = float(round(np.median(good), 2))
    return thresholds


# ---------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------
def report(name, probs, y, thresholds):
    t = np.array([thresholds[l] for l in LABELS])
    preds = (probs >= t).astype(int)
    print(f"\n===== {name} =====")
    print(classification_report(y, preds, target_names=LABELS, zero_division=0))
    lo, hi = macro_f1_ci(y.astype(int), preds)
    print(f"Macro F1 {f1_score(y, preds, average='macro', zero_division=0):.4f} "
          f"(95% CI {lo:.3f}-{hi:.3f}) | "
          f"Micro F1 {f1_score(y, preds, average='micro', zero_division=0):.4f}")


def macro_f1_ci(y, preds, n_boot=500, seed=0):
    """Bootstrap 95% interval for macro-F1 (shows how much to trust a number)."""
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        scores.append(f1_score(y[idx], preds[idx], average="macro", zero_division=0))
    return np.percentile(scores, [2.5, 97.5])


def one_line(name, y, preds):
    macro = f1_score(y, preds, average="macro", zero_division=0)
    micro = f1_score(y, preds, average="micro", zero_division=0)
    print(f"  {name:<42} macro-F1 {macro:.4f} | micro-F1 {micro:.4f}")


def fit_tfidf_baseline(train_df):
    """Simple word-count model. If mBERT cannot beat this, mBERT is not adding anything."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.multiclass import OneVsRestClassifier
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    X = vec.fit_transform(train_df["text"].astype(str))
    clf = OneVsRestClassifier(LogisticRegression(max_iter=1000, C=4))
    clf.fit(X, train_df[LABELS].values)
    return lambda df: clf.predict(vec.transform(df["text"].astype(str)))


def add_stt_noise(df, drop_p=0.05, seed=0):
    """Mimic speech-to-text output: no punctuation, lower case, a few missing words."""
    rng = random.Random(seed)
    out = df.copy()
    texts = []
    for t in df["text"].astype(str):
        t = re.sub(r"[^\w\s]", "", t.lower())
        words = [w for w in t.split() if rng.random() > drop_p]
        texts.append(" ".join(words) if words else t)
    out["text"] = texts
    return out


def export_errors(df, probs, y, thresholds, path):
    """Save the windows where the model disagrees with the label, so you can read them."""
    t = np.array([thresholds[l] for l in LABELS])
    preds = (probs >= t).astype(int)
    wrong = np.where((preds != y.astype(int)).any(axis=1))[0]
    out = df.iloc[wrong][["call_id", "text"]].reset_index(drop=True)
    for i, label in enumerate(LABELS):
        out[f"true_{label}"] = y[wrong, i].astype(int)
        out[f"pred_{label}"] = preds[wrong, i]
        out[f"p_{label}"] = probs[wrong, i].round(3)
    out.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[+] {len(out)} disagreements saved to {path}")


def evaluate_challenge(model, tokenizer, thresholds, batch_size, baseline):
    ch = pd.DataFrame(CHALLENGE_ROWS, columns=["language", "text"] + LABELS)
    ch["call_id"] = range(len(ch))
    ch.to_csv(OUT_DIR / "challenge_set.csv", index=False, encoding="utf-8-sig")
    probs, y = get_probs(model, make_loader(ch, tokenizer, batch_size, False))
    half = {l: 0.5 for l in LABELS}
    report("CHALLENGE - mBERT", probs, y, thresholds)

    # which calls did the model get wrong? (U=urgency A=authority C=credential P=payment)
    short = {"urgency": "U", "authority_impersonation": "A", "credential_request": "C", "payment_request": "P"}
    t = np.array([thresholds[l] for l in LABELS])
    pred = (probs >= t).astype(int)
    print("\nChallenge calls with a mistake (missed = real tactic not found, extra = tactic that is not there):")
    for i in range(len(ch)):
        if (pred[i] != y[i].astype(int)).any():
            missed = "".join(short[l] for k, l in enumerate(LABELS) if y[i][k] == 1 and pred[i][k] == 0)
            extra = "".join(short[l] for k, l in enumerate(LABELS) if y[i][k] == 0 and pred[i][k] == 1)
            print(f"  #{i:02d} missed={missed or '-':<4} extra={extra or '-':<4} | {ch['text'][i][:95]}")
    rules = np.array([[label_text(t)[l] for l in LABELS] for t in ch["text"]], dtype=float)
    report("CHALLENGE - keyword rules (the labeler itself)", rules, y, half)
    if baseline is not None:
        report("CHALLENGE - TF-IDF baseline", baseline(ch).astype(float), y, half)


def evaluate_split(model, df, tokenizer, thresholds, name, batch_size, errors_path=None):
    probs, y = get_probs(model, make_loader(df, tokenizer, batch_size, False))
    report(f"{name} (windows)", probs, y, thresholds)
    if errors_path:
        export_errors(df, probs, y, thresholds, errors_path)

    # call level: a call has a tactic if any window has it
    p_df = pd.DataFrame(probs, columns=LABELS)
    y_df = pd.DataFrame(y, columns=LABELS)
    p_df["call_id"] = y_df["call_id"] = df["call_id"].values
    call_p = p_df.groupby("call_id")[LABELS].max().values
    call_y = y_df.groupby("call_id")[LABELS].max().values
    report(f"{name} (calls)", call_p, call_y, thresholds)


def evaluate_gold(model, tokenizer, thresholds, path, batch_size):
    """Gold set after you reviewed it by hand (fill the reviewed_* columns)."""
    g = pd.read_csv(path)
    cols = [f"reviewed_{l}" for l in LABELS]
    g = g.dropna(subset=cols)
    if len(g) == 0:
        print("\n[gold] reviewed_* columns are empty - skipping")
        return
    for l in LABELS:
        g[l] = g[f"reviewed_{l}"].astype(int)
    probs, y = get_probs(model, make_loader(g, tokenizer, batch_size, False))
    report(f"GOLD ({len(g)} calls, hand reviewed)", probs, y, thresholds)
    # how good were the automatic labels compared with your review?
    auto = g[[f"auto_{l}" for l in LABELS]].values.astype(float)
    report("GOLD - automatic labels vs your review (label noise)", auto, y, {l: 0.5 for l in LABELS})


# ---------------------------------------------------------------
# Production detector (same interface as v1, used by Phase 10)
# ---------------------------------------------------------------
class SocialEngineeringDetector:
    def __init__(self, model, tokenizer, thresholds=None, device=DEVICE):
        self.device = device
        self.tokenizer = tokenizer
        self.model = model.to(device).eval()
        self.thresholds = thresholds or DEFAULT_THRESHOLDS

    def _windows(self, text, size=120, step=60):
        # the STT text has no speaker tags, so we cut by words
        words = text.split()
        if len(words) <= size:
            return [text]
        return [" ".join(words[i:i + size]) for i in range(0, len(words) - size // 2, step)]

    def predict(self, text, thresholds=None):
        thresholds = thresholds or self.thresholds
        windows = self._windows(text)
        enc = self.tokenizer(windows, truncation=True, max_length=MAX_LEN,
                             padding=True, return_tensors="pt").to(self.device)
        with torch.no_grad():
            probs = torch.sigmoid(self.model(enc["input_ids"], enc["attention_mask"]))
        probs = probs.max(dim=0).values.cpu().numpy()   # max over windows

        results = {}
        for i, label in enumerate(LABELS):
            p = float(probs[i])
            results[label] = {"score": round(p, 4), "flagged": bool(p >= thresholds[label])}
        return {"text": text, "predictions": results,
                "overall_social_eng_score": round(float(probs.max()), 4)}


def build_social_engineering_detector(device=DEVICE):
    tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = SocialEngineeringmBERT()
    thresholds = DEFAULT_THRESHOLDS
    if os.path.exists(WEIGHTS_PATH):
        model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=device))
        print(f"[+] Loaded weights from '{WEIGHTS_PATH}'")
    else:
        print("[!] No fine-tuned weights found - using an untrained head")
    if os.path.exists(THRESHOLDS_PATH):
        thresholds = json.load(open(THRESHOLDS_PATH))
    return SocialEngineeringDetector(model, tok, thresholds, device), model, tok


# ===============================================================
# PART 3 - RUN EVERYTHING
# ===============================================================
def make_review_sheet(n):
    """A sheet of external windows to label by hand. Fill reviewed_* (you) and reviewed2_* (a friend)."""
    ext = pd.read_csv(OUT_DIR / "test_ext.csv")
    err_file = OUT_DIR / "errors_test_ext.csv"
    parts = []
    if err_file.exists():     # windows where the model and the keyword labels disagreed
        err = pd.read_csv(err_file)[["call_id", "text"]]
        hard = ext.merge(err, on=["call_id", "text"]).head(n // 3)
        parts.append(hard)
    rest = ext[~ext["text"].isin(pd.concat(parts)["text"])] if parts else ext
    parts.append(rest.sample(n - sum(len(x) for x in parts), random_state=7))
    sheet = pd.concat(parts, ignore_index=True).drop_duplicates("text")
    out = sheet[["call_id", "window_idx", "text"]].copy()
    for l in LABELS:
        out[f"auto_{l}"] = sheet[l].values
    for l in LABELS:
        out[f"reviewed_{l}"] = ""
    for l in LABELS:
        out[f"reviewed2_{l}"] = ""
    path = OUT_DIR / "review_external.csv"
    out.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[+] {len(out)} windows saved to {path}")
    print("    Fill reviewed_* with 0/1 (urgency, authority, credential, payment). "
          "Judge what the CALLER does in that text.")


def kappa_report(path):
    """How much two reviewers agree (Cohen's kappa), and which rows they disagree on."""
    from sklearn.metrics import cohen_kappa_score
    d = pd.read_csv(path)
    c1 = [f"reviewed_{l}" for l in LABELS]
    c2 = [f"reviewed2_{l}" for l in LABELS]
    d = d.dropna(subset=c1 + c2)
    if len(d) == 0:
        print("Both reviewer columns (reviewed_* and reviewed2_*) must be filled first.")
        return
    print(f"\nRows reviewed by both: {len(d)}")
    for l in LABELS:
        a, b = d[f"reviewed_{l}"].astype(int), d[f"reviewed2_{l}"].astype(int)
        print(f"  {l:<26} agreement {np.mean(a == b):.1%} | kappa {cohen_kappa_score(a, b):.3f}")
    diff = d[(d[c1].astype(int).values != d[c2].astype(int).values).any(axis=1)]
    out = Path(path).with_name(Path(path).stem + "_disagreements.csv")
    diff.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"[+] {len(diff)} rows with a disagreement saved to {out} - discuss them and agree on one answer")
    print("    (rule of thumb: kappa above 0.6 is good agreement, above 0.8 is very good)")


def regenerate_synthetic():
    """Run generate_dataset_v2.py to make new calls whose labels are exact."""
    gen = BASE / "generate_dataset_v2.py"
    if not gen.exists():
        raise SystemExit("Put generate_dataset_v2.py next to this file first.")
    out = BASE / "synthetic_calls_v2"
    subprocess.run([sys.executable, str(gen), "--n", "4000", "--gold", "400", "--out", str(out)], check=True)


def use_llm_labels(df, llm):
    """Swap the keyword labels for the LLM labels. Windows the LLM has not labelled yet are dropped."""
    out = df.merge(llm, on=["call_id", "window_idx"], how="inner", suffixes=("_rule", ""))
    out["is_scam"] = (out[LABELS].sum(axis=1) > 0).astype(int)
    return out


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="synthetic,external_bothbosu,user_lines",
                    help="comma list of training sources")
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--patience", type=int, default=2)
    ap.add_argument("--batch_size", type=int, default=16 if torch.cuda.is_available() else 8)
    ap.add_argument("--gold", default=str(OUT_DIR / "gold_review_4labels.csv"))
    ap.add_argument("--max_len", type=int, default=256, help="tokens per window (128 is faster on CPU)")
    ap.add_argument("--rebuild", action="store_true", help="rebuild the CSVs from the raw files")
    ap.add_argument("--quick", action="store_true", help="tiny run to check the pipeline")
    ap.add_argument("--use_llm_labels", action="store_true",
                    help="use data/processed/llm_labels.csv (made by llm_relabel.py) instead of the keyword labels")
    ap.add_argument("--regenerate", action="store_true",
                    help="make new synthetic calls with exact labels (generate_dataset_v2.py), then rebuild")
    ap.add_argument("--make_review_sheet", type=int, default=0, metavar="N",
                    help="write N external windows to data/processed/review_external.csv for hand labeling")
    ap.add_argument("--tune_only", action="store_true",
                    help="load saved weights, re-tune thresholds on the validation set, save thresholds.json, stop")
    ap.add_argument("--seed", type=int, default=42, help="random seed (same seed = same training)")
    ap.add_argument("--thr", type=float, default=None,
                    help="use this one threshold for all 4 labels (for testing, not saved)")
    ap.add_argument("--challenge_only", action="store_true",
                    help="fast: load saved weights and evaluate only on the 40 challenge calls")
    ap.add_argument("--gold_only", action="store_true",
                    help="fast: load saved weights + thresholds.json and evaluate only on the --gold file")
    ap.add_argument("--kappa", default=None, metavar="CSV",
                    help="agreement between two reviewers (columns reviewed_* and reviewed2_*)")
    ap.add_argument("--save_dir", default=None, help="folder for the weights and thresholds.json (default: next to this file)")
    ap.add_argument("--allow_cpu", action="store_true", help="train on the CPU even though it is very slow")
    ap.add_argument("--no_caller_aug", action="store_true",
                    help="do not add the caller-only copies of the synthetic training calls")
    ap.add_argument("--my_lines", default=None, help="csv of sentences you wrote (default: my_lines.csv next to this file)")
    ap.add_argument("--errors", action="store_true", help="save model-vs-label disagreements to a CSV")
    ap.add_argument("--eval_only", action="store_true",
                    help="skip training: load the saved .pt, tune thresholds, evaluate")
    args = ap.parse_args()
    global MAX_LEN, SYNTH_DIR, CALLER_AUG, MY_LINES, WEIGHTS_PATH, THRESHOLDS_PATH
    MAX_LEN = args.max_len
    if args.save_dir:     # e.g. a Google Drive folder, so the weights survive if Colab disconnects
        Path(args.save_dir).mkdir(parents=True, exist_ok=True)
        WEIGHTS_PATH = str(Path(args.save_dir) / "best_mbert_social_engineering.pt")
        THRESHOLDS_PATH = str(Path(args.save_dir) / "thresholds.json")
    CALLER_AUG = not args.no_caller_aug
    if args.my_lines:
        MY_LINES = Path(args.my_lines)

    # tools that do not train anything
    if args.kappa:
        kappa_report(args.kappa)
        return
    if args.make_review_sheet:
        make_review_sheet(args.make_review_sheet)
        return
    if args.tune_only:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = SocialEngineeringmBERT().to(DEVICE)
        model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=DEVICE))
        val_df = pd.read_csv(f"{DATA_DIR}/val.csv")
        val_probs, val_y = get_probs(model, make_loader(val_df, tokenizer, args.batch_size, False))
        thresholds = tune_thresholds(val_probs, val_y)
        json.dump(thresholds, open(THRESHOLDS_PATH, "w"), indent=2)
        print("[+] new thresholds saved to", THRESHOLDS_PATH, ":", thresholds)
        return
    if args.gold_only or args.challenge_only:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = SocialEngineeringmBERT().to(DEVICE)
        model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=DEVICE))
        thresholds = json.load(open(THRESHOLDS_PATH)) if os.path.exists(THRESHOLDS_PATH) else DEFAULT_THRESHOLDS
        if args.thr is not None:
            thresholds = {l: args.thr for l in LABELS}
        print("[+] thresholds:", thresholds)
        if args.gold_only:
            evaluate_gold(model, tokenizer, thresholds, args.gold, args.batch_size)
        if args.challenge_only:
            evaluate_challenge(model, tokenizer, thresholds, args.batch_size, None)
        return
    if args.regenerate:
        regenerate_synthetic()
        SYNTH_DIR = locate_synth_dir()
        args.rebuild = True
    print(f"[+] device: {DEVICE}")
    set_seed(args.seed)
    if DEVICE.type == "cpu" and not (args.quick or args.eval_only or args.allow_cpu):
        raise SystemExit("[!] No GPU found, so training would take many hours.\n"
                         "    Colab: Runtime > Change runtime type > T4 GPU, then run again.\n"
                         "    (To train on the CPU anyway, add --allow_cpu.)")

    # 1) build the corpus (only if it is not there yet)
    if args.rebuild or not (OUT_DIR / "train.csv").exists():
        print("[*] Building corpus...")
        build_corpus()
    else:
        print("[+] Using existing data/processed/*.csv (use --rebuild to remake them)")

    sources = args.sources.split(",")
    train_df = pd.read_csv(f"{DATA_DIR}/train.csv")
    val_df = pd.read_csv(f"{DATA_DIR}/val.csv")
    train_df = train_df[train_df["source"].isin(sources)]
    val_df = val_df[val_df["source"].isin(sources)]
    test_synth = pd.read_csv(f"{DATA_DIR}/test_synth.csv")
    test_ext = pd.read_csv(f"{DATA_DIR}/test_ext.csv")

    if args.use_llm_labels:
        llm_path = OUT_DIR / "llm_labels.csv"
        llm = pd.read_csv(llm_path)
        train_df, val_df = use_llm_labels(train_df, llm), use_llm_labels(val_df, llm)
        test_synth, test_ext = use_llm_labels(test_synth, llm), use_llm_labels(test_ext, llm)
        print(f"[+] using LLM labels: train {len(train_df)} | val {len(val_df)} | "
              f"test synthetic {len(test_synth)} | test external {len(test_ext)} windows")
        print("[!] weights/thresholds files are overwritten - copy the old .pt first if you want to keep it")

    if args.quick:
        train_df = train_df.sample(300, random_state=1)
        val_df = val_df.sample(100, random_state=1)
        test_synth = test_synth.sample(150, random_state=1)
        test_ext = test_ext.sample(200, random_state=1)
        args.epochs = 1
    print(f"[+] train {len(train_df)} windows | val {len(val_df)} | sources: {sources}")

    # 2) train
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = SocialEngineeringmBERT().to(DEVICE)
    train_loader = make_loader(train_df, tokenizer, args.batch_size, True)
    val_loader = make_loader(val_df, tokenizer, args.batch_size, False)
    if args.eval_only:
        print(f"[+] --eval_only: loading saved weights from {WEIGHTS_PATH} (no training)")
        model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=DEVICE))
    else:
        model = train(model, train_loader, val_loader, get_pos_weight(train_df),
                      args.epochs, args.lr, args.patience)

    # 3) thresholds from the validation set
    val_probs, val_y = get_probs(model, val_loader)
    thresholds = tune_thresholds(val_probs, val_y)
    json.dump(thresholds, open(THRESHOLDS_PATH, "w"), indent=2)
    print("[+] tuned thresholds:", thresholds)
    if args.thr is not None:
        thresholds = {l: args.thr for l in LABELS}
        print(f"[+] --thr: using {args.thr} for all labels in this run (thresholds.json keeps the tuned values)")

    # 4) test sets are only used here, once
    err_path = OUT_DIR / "errors_test_ext.csv" if args.errors else None
    evaluate_split(model, test_synth, tokenizer, thresholds, "TEST synthetic", args.batch_size)
    evaluate_split(model, test_ext, tokenizer, thresholds, "TEST external (BothBosu)",
                   args.batch_size, errors_path=err_path)

    user_test = OUT_DIR / "test_user.csv"
    if user_test.exists():
        evaluate_split(model, pd.read_csv(user_test), tokenizer, thresholds,
                       "TEST your own sentences (never used in training)", args.batch_size)

    # 5) sanity checks: is mBERT really better than a simple model, and is it robust?
    baseline = fit_tfidf_baseline(train_df)
    print("\n===== BASELINE: TF-IDF + logistic regression (windows) =====")
    for name, df in [("TEST synthetic", test_synth), ("TEST external", test_ext)]:
        one_line(name, df[LABELS].values.astype(int), baseline(df))

    print("\n===== ROBUSTNESS: same test sets with speech-to-text style noise =====")
    evaluate_split(model, add_stt_noise(test_synth), tokenizer, thresholds,
                   "TEST synthetic [STT noise]", args.batch_size)
    evaluate_split(model, add_stt_noise(test_ext), tokenizer, thresholds,
                   "TEST external [STT noise]", args.batch_size)

    evaluate_challenge(model, tokenizer, thresholds, args.batch_size, baseline)

    if os.path.exists(args.gold):
        evaluate_gold(model, tokenizer, thresholds, args.gold, args.batch_size)


if __name__ == "__main__":
    main()
