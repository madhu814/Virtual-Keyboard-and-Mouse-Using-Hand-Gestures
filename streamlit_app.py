import socket
import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).parent
FRONTEND_DIR = ROOT / "frontend"
STATIC_PORT = 8001


def start_static_server():
    handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = ThreadingHTTPServer(("localhost", STATIC_PORT), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("localhost", port)) == 0


st.set_page_config(page_title="Gesture Control Showcase", layout="wide")
st.title("Virtual Mouse Gesture Control — Streamlit Showcase")

st.write(
    "This page embeds the browser demo for camera-based hand tracking and gesture-controlled cursor movement. "
    "If the preview does not display your webcam, open the demo link in a new tab."
)

if not FRONTEND_DIR.exists():
    st.error("Missing `frontend/` directory. Make sure `frontend/index.html` is present in the repo.")
else:
    demo_url = f"http://localhost:{STATIC_PORT}/frontend/index.html"

    if not is_port_open(STATIC_PORT):
        start_static_server()
        st.success(f"Started static server on port {STATIC_PORT}.")

    st.markdown("### Live demo")
    st.markdown(f"[Open the browser demo in a new tab]({demo_url})")

    st.warning(
        "Some browsers may restrict webcam access inside an embedded iframe. "
        "If the preview does not show video, use the link above."
    )

    app_js = (FRONTEND_DIR / "app.js").read_text()

    demo_html = (
        "<div id=\"info\">Gesture demo — shows index position and pinch click</div>"
        "<div id=\"container\">"
        "<video id=\"video\" playsinline style=\"display:none\"></video>"
        "<canvas id=\"output\" width=\"1280\" height=\"720\"></canvas>"
        "</div>"
        "<style>"
        "html,body{height:100%;margin:0;background:#111;color:#eee;font-family:Arial}"
        "#container{display:flex;align-items:center;justify-content:center;height:100%}"
        "canvas{max-width:100%;height:auto;border:1px solid #222}"
        "#info{position:fixed;left:12px;top:12px;background:rgba(0,0,0,0.5);padding:8px;border-radius:6px}"
        "</style>"
        "<script src=\"https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js\"></script>"
        "<script src=\"https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js\"></script>"
        "<script>" + app_js + "</script>"
        ""
    )
    components.html(demo_html, height=760)

st.markdown("---")
st.header("How to use this showcase")
st.markdown(
    "1. Allow webcam access when the browser asks.\n"
    "2. Move your index finger to control the mouse cursor.\n"
    "3. Pinch thumb and index finger to click.\n"
    "4. Open the demo in a new tab if the embedded preview is blank."
)

st.markdown("---")
st.subheader("Python app")
st.write(
    "The local Python prototype lives in `main.py`. It uses MediaPipe for hand tracking and `pyautogui` to control the system cursor. "
    "This Streamlit page is only a presentation layer for the browser-based demo."
)
