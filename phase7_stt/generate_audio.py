from gtts import gTTS

sentences = [
    "The weather is really nice today",
    "I have a meeting scheduled for tomorrow morning",
    "Can you send me the report by the end of the day",
    "She is studying computer science at the university",
    "We should grab coffee sometime this week",
    "The train arrives at the station in ten minutes",
    "My favorite season is autumn because of the colors",
    "He forgot his keys at the office again",
]

for i, text in enumerate(sentences):
    tts = gTTS(text=text, lang='en')
    tts.save(f"gen_{i}.mp3")
    print(f"[{i}] Saved: gen_{i}.mp3  ->  \"{text}\"")

print("\nDone! Generated", len(sentences), "files.")