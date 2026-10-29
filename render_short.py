"""Render an original storyboard to a silent vertical MP4; no external media."""
import math, os, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from production import sample_plan, validate_plan

WIDTH, HEIGHT, FPS = 720, 1280, 15
def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap(draw, text, f, limit):
    words, lines, line = text.split(), [], ""
    for word in words:
        attempt = (line + " " + word).strip()
        if draw.textbbox((0,0), attempt, font=f)[2] > limit and line:
            lines.append(line)
            line = word
        else:
            line = attempt
    if line: lines.append(line)
    return lines

def make_frame(text, index, total, t):
    im = Image.new("RGB", (WIDTH, HEIGHT), "#09111e")
    d = ImageDraw.Draw(im)
    gold = "#e9c184"
    d.rectangle((45, 68, 675, 75), fill=gold)
    d.text((48, 110), "THE PRICE OF EVERYTHING", font=font(29), fill=gold)
    d.ellipse((130, 270, 590, 730), outline="#34435a", width=6)
    d.ellipse((170, 310, 550, 690), outline=gold, width=4)
    d.text((WIDTH//2, 495), "$", font=font(125), fill=gold, anchor="mm")
    f = font(45)
    lines = wrap(d, text, f, 620)
    y = 810 - (len(lines)-1)*30
    for line in lines:
        d.text((WIDTH//2, y), line, font=f, fill="#f7f4ed", anchor="mm")
        y += 65
    d.text((WIDTH//2, 1150), f"SCENE {index}/{total}  •  ORIGINAL EXPLAINER", font=font(19), fill=gold, anchor="mm")
    d.rectangle((45, 1200, 45+int(630*t), 1210), fill=gold)
    return im

def render(output: str):
    plan = sample_plan()
    errors = validate_plan(plan)
    if errors: raise ValueError(errors)
    output_path = Path(output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "frames.rgb"
        with raw.open("wb") as stream:
            for idx, scene in enumerate(plan.scenes, 1):
                frames = scene.seconds * FPS
                for i in range(frames):
                    stream.write(make_frame(scene.narration, idx, len(plan.scenes), i/max(frames-1,1)).tobytes())
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
                        "-r", str(FPS), "-i", str(raw), "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "28", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output_path)], check=True)
    return str(output_path)

if __name__ == "__main__":
    print(render(os.environ.get("OUTPUT_MP4", "/data/sample-short.mp4")))
