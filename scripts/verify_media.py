import json
from pathlib import Path
import subprocess
from scos.db import connect, all_rows, clean
from scos import storage
from scos.config import RUNTIME

reports = []
with connect() as c:
    exports = all_rows(c, "SELECT * FROM exports ORDER BY created_at")
    assert exports, "No rendered media. Create a fixture and render it through the UI first."
    for ex in exports:
        data = storage.read(ex["object_key"], ex["sha256"])
        result = {
            "id": str(ex["id"]),
            "format": ex["format"],
            "sha256": ex["sha256"],
            "byte_size": len(data),
            "hash_verified": True,
        }
        if ex["format"] in ("long_16_9", "short_9_16", "reel_9_16"):
            p = RUNTIME / ex["object_key"]
            probe = json.loads(
                subprocess.run(
                    ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(p)],
                    capture_output=True,
                    check=True,
                ).stdout
            )
            v = next(s for s in probe["streams"] if s["codec_type"] == "video")
            assert (v["width"], v["height"]) == (ex["width"], ex["height"])
            assert v["codec_name"] == "h264"
            assert any(s["codec_type"] == "audio" for s in probe["streams"])
            subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "null", "-"], capture_output=True, check=True)
            result["probe"] = probe
        else:
            import zipfile
            import io
            from PIL import Image

            with zipfile.ZipFile(io.BytesIO(data)) as z:
                assert len(z.namelist()) >= 3
                for name in z.namelist():
                    with Image.open(io.BytesIO(z.read(name))) as im:
                        assert im.size == (ex["width"], ex["height"])
                result["slides"] = z.namelist()
        reports.append(result)
root = Path(__file__).resolve().parents[1]
(root / "artifacts").mkdir(exist_ok=True)
(root / "artifacts/media-verification.json").write_text(json.dumps(clean(reports), indent=2))
print(f"{len(reports)} actual exports independently hash-verified and decoded/probed.")
