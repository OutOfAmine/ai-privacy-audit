"""Render scene.html to demo.mp4 + demo.gif, frame by frame with a fake clock.

    pip install playwright && playwright install chromium
    python demo/render.py <path-to-ffmpeg>
"""
import functools, http.server, pathlib, shutil, subprocess, sys, tempfile, threading
from playwright.sync_api import sync_playwright

FPS = 30
HERE = pathlib.Path(__file__).parent
FFMPEG = sys.argv[1] if len(sys.argv) > 1 else "ffmpeg"

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()

frames = pathlib.Path(tempfile.mkdtemp())
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1.5)
    # Fake clock before load: framer-motion captures requestAnimationFrame at import time.
    page.clock.install(time=0)
    page.goto(f"http://127.0.0.1:{server.server_port}/scene.html?render")
    while not page.evaluate("!!window.__start"):  # wait_for_function polls via rAF, frozen under the fake clock
        page.clock.run_for(16)
    page.clock.pause_at((page.evaluate("Date.now()") + 100) / 1000)  # seconds
    page.evaluate("window.__start()")
    while not page.evaluate("window.__duration"):
        page.clock.run_for(1)
    total = page.evaluate("window.__duration")
    for i in range(int(total / 1000 * FPS)):
        page.screenshot(path=str(frames / f"{i:05d}.png"))
        page.clock.run_for(round(1000 / FPS))
    browser.close()
server.shutdown()

src = ["-framerate", str(FPS), "-i", str(frames / "%05d.png")]
subprocess.run([FFMPEG, "-y", *src, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "slow",
                "-movflags", "+faststart", str(HERE / "demo.mp4")], check=True)
subprocess.run([FFMPEG, "-y", *src, "-vf",
                "fps=8,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle",
                str(HERE / "demo.gif")], check=True)
shutil.rmtree(frames)
