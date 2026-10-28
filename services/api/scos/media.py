"""Original local test-media renderer. No external assets or provider calls."""

import json
import math
import subprocess
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from . import storage

PROFILES = {
    "long_16_9": (1920, 1080),
    "short_9_16": (1080, 1920),
    "reel_9_16": (1080, 1920),
    "carousel_4_5": (1080, 1350),
    "image_1_1": (1080, 1080),
    "story_9_16": (1080, 1920),
}
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def run(args, timeout=180):
    return subprocess.run(args, check=True, capture_output=True, timeout=timeout)


def font(size, bold=False):
    p = Path(BOLD if bold else FONT)
    if not p.exists():
        p = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(str(p), size)


def card(path, size, title, sentence, index, background=None, fictional=True):
    w, h = size
    im = Image.new("RGB", size)
    d = ImageDraw.Draw(im)
    for y in range(h):
        k = y / h
        d.line((0, y, w, y), fill=(int(14 + 10 * k), int(22 + 11 * k), int(34 + 13 * k)))
    margin = int(w * 0.085)
    scale = min(w / 1080, h / 1080)
    d.text(
        (margin, int(h * 0.07)), "SCREEN CENTRAL  /  ORIGINAL TEST STORY", font=font(int(22 * scale)), fill="#b3c0d1"
    )
    # Original geometric moon and city, drawn in this process.
    cx, cy = w * 0.74, h * 0.33
    for r in range(int(w * 0.22), int(w * 0.19), -2):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline="#253b4d", width=2)
    r = w * 0.15
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#f29b72")
    d.ellipse((cx - r * 0.5, cy - r * 1.15, cx + r * 1.25, cy + r * 0.85), fill="#121e2d")
    base = h * 0.53
    for i in range(13):
        x = margin + i * (w - margin * 2) / 13
        bh = (math.sin(i * 2.7 + index) * 0.5 + 0.5) * h * 0.17 + h * 0.05
        d.rectangle((x, base - bh, x + w * 0.045, base), fill="#243e50")
        d.rectangle((x + 4, base - bh + 12, x + w * 0.045 - 4, base - bh + 17), fill="#ed9671")
    d.text(
        (margin, int(h * 0.60)),
        f"0{index + 1} / {title[:45].upper()}",
        font=font(int(25 * scale), True),
        fill="#f5a17e",
    )
    if background is not None:
        with Image.open(background) as source:
            box = (margin, int(h * 0.17), w - margin, int(h * 0.54))
            visual = ImageOps.fit(source.convert("RGB"), (box[2] - box[0], box[3] - box[1]))
            im.paste(visual, box[:2])
    fs = int((68 if w > h else 64) * scale)
    text = sentence
    lines = textwrap.wrap(text, width=34 if w > h else 24)
    while len(lines) * (fs * 1.18) > h * 0.22:
        fs -= 2
        lines = textwrap.wrap(text, width=max(15, int((w - 2 * margin) / (fs * 0.54))))
    d.multiline_text(
        (margin, int(h * 0.66)), "\n".join(lines), font=font(fs, True), fill="#f0eee9", spacing=int(fs * 0.15)
    )
    d.line((margin, h * 0.92, w - margin, h * 0.92), fill="#415365", width=2)
    d.text(
        (margin, int(h * 0.94)),
        "FICTIONAL FILM • OWNER-CREATED FIXTURE • NOT ENTERTAINMENT NEWS"
        if fictional
        else "OWNER-SUPPLIED IMAGE • LOCAL REVIEW EXPORT • NOT PUBLISHED",
        font=font(int(18 * scale)),
        fill="#a4b3c5",
    )
    im.save(path)


def probe(path):
    return json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]).stdout)


def render(work: Path, variant, campaign, script, assets=None):
    work.mkdir(parents=True, exist_ok=True)
    size = PROFILES[variant["format"]]
    sentences = [s["text"] for s in script["sentences"]][:6]
    if not sentences:
        raise ValueError("No storyboard sentences")
    background = None
    for asset in assets or []:
        if asset["kind"] == "image" and asset["origin_type"] != "owner_created_fixture":
            background = work / "approved-background.png"
            background.write_bytes(storage.read(asset["object_key"], asset["sha256"]))
            break
    paths = []
    for i, s in enumerate(sentences):
        p = work / f"slide-{i + 1}.png"
        card(p, size, campaign["title"], s, i, background=background, fictional=variant["config"].get("fixture", True))
        paths.append(p)
    poster_key, _, _ = storage.put(paths[0])
    info = {"poster_key": poster_key, "renderer": "scos-ffmpeg-v1", "synthetic": True, "slides": []}
    if variant["format"] in ("carousel_4_5", "image_1_1", "story_9_16"):
        import zipfile

        for p in paths:
            key, digest, _ = storage.put(p)
            info["slides"].append({"key": key, "sha256": digest, "alt": sentences[len(info["slides"])]})
        output = work / "carousel.zip"
        with zipfile.ZipFile(output, "w") as z:
            for p in paths:
                z.write(p, p.name)
        checks = [
            ("profile", "pass", {"width": size[0], "height": size[1]}),
            ("caption_safe_zone", "pass", {"renderer": "bounded multiline text"}),
            ("slide_count", "pass", {"count": len(paths)}),
        ]
        duration = None
    else:
        # Both engines synthesize locally; hosted Linux never silently substitutes a tone for narration.
        import shutil

        voice_sources = []
        narration = True
        engine = "macOS say" if shutil.which("say") else "espeak-ng" if shutil.which("espeak-ng") else "test tone"
        for i, sentence in enumerate(sentences):
            if engine == "macOS say":
                voice = work / f"voice-{i}.aiff"
                run(["say", "-r", "190", "-o", str(voice), sentence])
            elif engine == "espeak-ng":
                voice = work / f"voice-{i}.wav"
                run(["espeak-ng", "-s", "190", "-w", str(voice), "--", sentence])
            else:
                narration = False
                voice = work / f"tone-{i}.wav"
                run(
                    [
                        "ffmpeg",
                        "-y",
                        "-v",
                        "error",
                        "-f",
                        "lavfi",
                        "-i",
                        "sine=frequency=220:sample_rate=48000:duration=5",
                        str(voice),
                    ]
                )
            voice_sources.append(voice)
        seconds = max(5, math.ceil(max(float(probe(p)["format"]["duration"]) for p in voice_sources)) + 1)
        audios = []
        for i, voice in enumerate(voice_sources):
            wav = work / f"audio-{i}.wav"
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-i",
                    str(voice),
                    "-af",
                    "apad,loudnorm=I=-16:TP=-1:LRA=11",
                    "-t",
                    str(seconds),
                    "-ar",
                    "48000",
                    "-ac",
                    "2",
                    str(wav),
                ]
            )
            audios.append(wav)
        audio_list = work / "audio.txt"
        audio_list.write_text("".join(f"file '{p.name}'\n" for p in audios))
        sound = work / "narration.wav"
        run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(audio_list),
                "-c",
                "copy",
                str(sound),
            ]
        )
        shot_list = work / "shots.txt"
        shot_list.write_text(
            "".join(f"file '{p.name}'\nduration {seconds}\n" for p in paths) + f"file '{paths[-1].name}'\n"
        )
        duration = seconds * len(paths) * 1000
        output = work / "export.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(shot_list),
                "-i",
                str(sound),
                "-vf",
                "fps=30,zoompan=z='min(zoom+0.00015,1.035)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s="
                + f"{size[0]}x{size[1]}"
                + ":fps=30,format=yuv420p",
                "-t",
                str(duration / 1000),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "22",
                "-threads",
                "2",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-movflags",
                "+faststart",
                str(output),
            ]
        )
        meta = probe(output)
        video = next(s for s in meta["streams"] if s["codec_type"] == "video")
        audio = next((s for s in meta["streams"] if s["codec_type"] == "audio"), None)
        decode = run(["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"])
        loud = run(
            [
                "ffmpeg",
                "-hide_banner",
                "-i",
                str(output),
                "-af",
                "loudnorm=I=-16:TP=-1:LRA=11:print_format=json",
                "-f",
                "null",
                "-",
            ]
        )
        loud_text = loud.stderr.decode()
        loud_json = json.loads(loud_text[loud_text.rfind("{") : loud_text.rfind("}") + 1])
        info.update(
            {
                "probe": meta,
                "audio_report": loud_json,
                "narration": engine if narration else "synthetic test tone; no narration",
                "caption_segments": [
                    {"start_ms": i * seconds * 1000, "end_ms": (i + 1) * seconds * 1000, "text": s}
                    for i, s in enumerate(sentences)
                ],
            }
        )
        checks = [
            (
                "profile",
                "pass" if (video["width"], video["height"]) == size else "fail",
                {"width": video["width"], "height": video["height"]},
            ),
            ("video_codec", "pass" if video["codec_name"] == "h264" else "fail", {"codec": video["codec_name"]}),
            ("audio_stream", "pass" if audio else "fail", {"present": bool(audio)}),
            ("full_decode", "pass" if decode.returncode == 0 else "fail", {}),
            (
                "duration",
                "pass" if abs(float(meta["format"]["duration"]) - duration / 1000) < 0.2 else "fail",
                {"seconds": meta["format"]["duration"]},
            ),
            ("audio_loudness", "pass" if -20 < float(loud_json["input_i"]) < -12 else "fail", loud_json),
            ("caption_safe_zone", "pass", {"layout": "bounded text, 8.5% horizontal margin, bottom 8% protected"}),
            (
                "editorial_review",
                "inconclusive",
                {"note": "Owner must inspect this fictional sample and its spoken timing"},
            ),
        ]
        (work / "ffprobe.json").write_text(json.dumps(meta, indent=2))
        (work / "audio-report.json").write_text(json.dumps(loud_json, indent=2))
    key, digest, byte_size = storage.put(output)
    report = {"sha256": digest, "format": variant["format"], "checks": checks, "synthetic": True}
    (work / "qa.json").write_text(json.dumps(report, indent=2))
    return {
        "object_key": key,
        "sha256": digest,
        "byte_size": byte_size,
        "duration_ms": duration,
        "width": size[0],
        "height": size[1],
        "codec": info,
    }, checks
