# Virtual Keyboard and Mouse Control

A prototype application that uses a webcam and hand gestures to control the mouse cursor and type on a virtual keyboard.

## Features
- Camera-based hand tracking with MediaPipe
- Cursor movement mapped from index finger position
- Click and right-click gestures using thumb, index, and middle finger distance
- Virtual on-screen keyboard for typing with pinch gestures
- Optional scroll mode using index and middle finger together

## Requirements
- Python 3.8+ (recommended)
- Webcam
- Windows, macOS, or Linux

## Python Dependencies
Install dependencies with:

```bash
pip install -r requirements.txt
```

> On Windows, `pyautogui` may require additional modules such as `pillow` and `pygetwindow`.

## How to Run

### Local Python app
1. Open a terminal in the project folder.
2. Run:

```bash
python main.py
```

### Streamlit web showcase
1. Install requirements if you haven't already:

```bash
pip install -r requirements.txt
```

2. Start Streamlit:

```bash
streamlit run streamlit_app.py
```

3. Open the URL shown by Streamlit in your browser.

4. Use the "Open the browser demo in a new tab" link if embedded webcam access is restricted.

5. Allow the webcam if prompted.
6. Move your hand in front of the camera.
7. Use the index finger to move the cursor.
8. Pinch with thumb and index finger to type or click.
9. Bring index and middle fingers close together and move vertically to scroll.

### Browser demo web showcase
The `frontend/` folder contains a browser-based gesture demo using MediaPipe Hands. It is designed to run from a static web server or GitHub Pages.

- Open `frontend/index.html` in a browser.
- If the browser blocks camera access from a local file, serve the folder with a simple local host server:

```bash
cd frontend
python -m http.server 8000
```

Then open `http://localhost:8000`.

### Deploy to GitHub Pages
This repository includes a GitHub Actions workflow at `.github/workflows/deploy.yml` that publishes the contents of `frontend/` to GitHub Pages on every push to `main` or `master`.

1. Push your repository to GitHub.
2. In the repository settings, enable GitHub Pages and select the `gh-pages` branch.
3. The demo will be available at `https://<your-username>.github.io/<your-repository>/`.

> Note: The browser demo is a frontend showcase only and does not remotely control the system mouse from the web page.

## How It Works
- The app uses MediaPipe Hands to detect one hand and extract key landmarks.
- The index finger tip is mapped from camera coordinates to screen coordinates.
- A smoothing algorithm reduces jitter before moving the cursor with `pyautogui`.
- Pinch gestures are detected by measuring distances between thumb, index, and middle finger landmarks.
- A simple virtual keyboard is drawn on-screen using OpenCV.

## Notes
- `pyautogui.FAILSAFE` is disabled because the app moves the cursor automatically.
- If the cursor behaves erratically, adjust the smoothing parameters in `main.py`.
- This is a prototype and is best used as a local demo, not as production software.

## Files
- `main.py` — main application code

## GitHub Push Instructions
1. Initialize the repository:

```bash
git init
```

2. Add files:

```bash
git add .
```

3. Commit:

```bash
git commit -m "Add virtual keyboard and mouse gesture control prototype"
```

4. Add your GitHub remote (replace with your repo URL):

```bash
git remote add origin https://github.com/<your-username>/<your-repo>.git
```

5. Push to GitHub:

```bash
git branch -M main
 git push -u origin main
```
