import os, subprocess, urllib.request, time

OUT = "out"
os.makedirs(OUT, exist_ok=True)
VOICE = "hi-IN-MadhurNeural"
FONT = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"


def run(cmd):
    print(" ".join(cmd)[:200])
    subprocess.run(cmd, check=True)


def download(url, path, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
                f.write(r.read())
            if os.path.getsize(path) > 1000:
                return True
        except Exception as e:
            print("download failed", e)
        time.sleep(10)
    return False


def make_video(name, script, bg_url, w, h, max_secs=None):
    txt, mp3, vtt, bg = f"{name}.txt", f"{name}.mp3", f"{name}.vtt", f"{name}_bg.jpg"
    with open(txt, "w", encoding="utf-8") as f:
        f.write(script)
    run(["edge-tts", "--voice", VOICE, "--file", txt, "--write-media", mp3, "--write-subtitles", vtt])
    if not download(bg_url, bg):
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x101830:s={w}x{h}", "-frames:v", "1", bg])
    size = 56 if h > w else 30
    style = f"FontName=Noto Sans Devanagari,FontSize={size},Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Alignment=2,MarginV={150 if h > w else 40}"
    vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},subtitles={vtt}:fontsdir=/usr/share/fonts/truetype/noto:force_style='{style}'"
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", bg, "-i", mp3, "-vf", vf,
           "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "25",
           "-c:a", "aac", "-b:a", "128k", "-shortest"]
    if max_secs:
        cmd += ["-t", str(max_secs)]
    cmd += [f"{OUT}/{name}.mp4"]
    run(cmd)


make_video("short", os.environ["SHORT_SCRIPT"], os.environ["SHORT_BG_URL"], 1080, 1920, 59)
make_video("long", os.environ["LONG_SCRIPT"], os.environ["LONG_BG_URL"], 1920, 1080)

# thumbnail
thumb = "thumb_src.jpg"
if not download(os.environ["THUMB_URL"], thumb):
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x101830:s=1280x720", "-frames:v", "1", thumb])
base = f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720"
text = os.environ.get("THUMB_TEXT", "").strip()
done = False
if text:
    with open("thumb.txt", "w", encoding="utf-8") as f:
        f.write(text)
    try:
        run(["ffmpeg", "-y", "-i", thumb, "-vf",
             f"{base},drawtext=fontfile={FONT}:textfile=thumb.txt:fontsize=110:fontcolor=white:borderw=8:bordercolor=black:x=(w-text_w)/2:y=h-text_h-80",
             "-frames:v", "1", "-q:v", "3", f"{OUT}/thumbnail.jpg"])
        done = True
    except Exception as e:
        print("drawtext failed", e)
if not done:
    run(["ffmpeg", "-y", "-i", thumb, "-vf", base, "-frames:v", "-q:v", "3", f"{OUT}/thumbnail.jpg"])
