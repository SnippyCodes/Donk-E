import json
import os
import re
import subprocess
import sys

DEMO_DIRECTOR_PATH = os.path.join("frontend", "src", "components", "DemoDirector.tsx")
OUTPUT_DIR = os.path.join("frontend", "public", "audio")

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(DEMO_DIRECTOR_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Extract DEMO_CHAPTERS array
match = re.search(r"export const DEMO_CHAPTERS: DemoChapter\[\] = \[(.*?)\]\s*(?:\r?\n)+\s*// ── VERIFIED", content, re.DOTALL)
if not match:
    print("Could not find DEMO_CHAPTERS block in DemoDirector.tsx")
    sys.exit(1)

block = match.group(1)

chapter_blocks = re.findall(r"\{\s*id:\s*(\d+).*?sentences:\s*\[(.*?)\]\s*,\s*voiceScript:\s*(?:'|\")?(.*?)(?:'|\")?\s*,\s*\}", block, re.DOTALL)

print(f"Found {len(chapter_blocks)} chapter blocks")

audio_items = []
for cid_str, sentences_str, voice_script in chapter_blocks:
    cid = int(cid_str)
    sentences = re.findall(r"(?:'|\")(.*?)(?:'|\")\s*(?:,|$)", sentences_str)
    cleaned_sentences = [s.replace("\\'", "'").replace('\\"', '"').strip() for s in sentences if s.strip()]
    cleaned_voice = voice_script.replace("\\'", "'").replace('\\"', '"').strip()

    # Full chapter audio item
    full_path = os.path.abspath(os.path.join(OUTPUT_DIR, f"ch_{cid}.wav"))
    audio_items.append({
        "cid": cid,
        "type": "chapter",
        "path": full_path,
        "text": cleaned_voice
    })

    # Sentence audio items
    for s_idx, sentence in enumerate(cleaned_sentences):
        s_path = os.path.abspath(os.path.join(OUTPUT_DIR, f"ch_{cid}_{s_idx}.wav"))
        audio_items.append({
            "cid": cid,
            "type": f"sentence_{s_idx}",
            "path": s_path,
            "text": sentence
        })

json_path = os.path.abspath("scripts/demo_audio_data.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(audio_items, f, indent=2, ensure_ascii=False)

print(f"Saved {len(audio_items)} audio tasks to {json_path}")

ps_code = f"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer

$voices = $synth.GetInstalledVoices()
foreach ($v in $voices) {{
    if ($v.VoiceInfo.Name -match "Zira|David|Aria|Mark|George") {{
        $synth.SelectVoice($v.VoiceInfo.Name)
        Write-Host "Using natural voice: $($v.VoiceInfo.Name)"
        break
    }}
}}
$synth.Rate = 0

$jsonContent = [System.IO.File]::ReadAllText('{json_path}', [System.Text.Encoding]::UTF8)
$items = ConvertFrom-Json $jsonContent

$count = 0
foreach ($item in $items) {{
    $synth.SetOutputToWaveFile($item.path)
    $synth.Speak($item.text)
    $count++
    if ($count % 5 -eq 0) {{
        Write-Host "Synthesized $count / $($items.Length) audio files..."
    }}
}}
$synth.Dispose()
Write-Host "Successfully generated all $count audio files!"
"""

ps_runner_path = os.path.abspath("scripts/run_tts.ps1")
with open(ps_runner_path, "w", encoding="utf-8") as f:
    f.write(ps_code)

print("Starting Windows SAPI TTS generation...")
res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_runner_path], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print("Stderr:", res.stderr)
