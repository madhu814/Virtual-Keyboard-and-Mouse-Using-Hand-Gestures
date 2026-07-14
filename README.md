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
pip install opencv-python mediapipe pyautogui numpy
```

> On Windows, `pyautogui` may require additional modules such as `pillow` and `pygetwindow`.

## How to Run
1. Open a terminal in the project folder.
2. Run:

```bash
python main.py
```

3. Allow the webcam if prompted.
4. Move your hand in front of the camera.
5. Use the index finger to move the cursor.
6. Pinch with thumb and index finger to type or click.
7. Bring index and middle fingers close together and move vertically to scroll.

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
