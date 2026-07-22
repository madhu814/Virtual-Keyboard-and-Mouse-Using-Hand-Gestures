Gesture demo frontend

This is a minimal browser demo that uses MediaPipe Hands to visualize the index finger position and a pinch (thumb+index) as a click.

Run locally (recommended):

1. From the repository root, start a simple HTTP server (required for camera access in many browsers):

```powershell
python -m http.server 8000
```

2. Open http://localhost:8000/frontend/index.html in your browser.

Notes:
- The demo is purely visual and does not control system mouse or keyboard.
- For a live demo embedded with the Python app you'd need a backend bridge; this demo is for showcasing recognition and interaction in-browser.
