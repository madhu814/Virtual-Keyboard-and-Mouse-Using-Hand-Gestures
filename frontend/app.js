const videoElement = document.getElementById('video');
const canvasElement = document.getElementById('output');
const cursorElement = document.getElementById('cursor');
const infoElement = document.getElementById('info');
const statusElement = document.getElementById('status');
const ctx = canvasElement ? canvasElement.getContext('2d') : null;

let smoothedX = window.innerWidth / 2;
let smoothedY = window.innerHeight / 2;
let lastPinch = false;

function setStatus(message) {
  if (statusElement) {
    statusElement.textContent = message;
  }
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function moveCursorTo(x, y) {
  if (!cursorElement) return;
  const targetX = clamp(x, 0, window.innerWidth);
  const targetY = clamp(y, 0, window.innerHeight);
  smoothedX = smoothedX * 0.7 + targetX * 0.3;
  smoothedY = smoothedY * 0.7 + targetY * 0.3;
  cursorElement.style.left = `${smoothedX}px`;
  cursorElement.style.top = `${smoothedY}px`;
}

function onResults(results) {
  if (!ctx || !canvasElement) return;

  ctx.save();
  ctx.clearRect(0, 0, canvasElement.width, canvasElement.height);
  ctx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

  if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
    const lm = results.multiHandLandmarks[0];
    const index = lm[8];
    const thumb = lm[4];

    const rect = canvasElement.getBoundingClientRect();
    const x = rect.left + index.x * rect.width;
    const y = rect.top + index.y * rect.height;

    const dist = Math.hypot(index.x - thumb.x, index.y - thumb.y);
    const isPinch = dist < 0.05;

    moveCursorTo(x, y);
    if (cursorElement) {
      cursorElement.classList.toggle('cursor-active', isPinch);
    }

    if (isPinch && !lastPinch) {
      const target = document.elementFromPoint(smoothedX, smoothedY);
      if (target) {
        target.click?.();
        if (infoElement) {
          infoElement.textContent = 'Pinch detected — click triggered';
        }
      }
    }

    lastPinch = isPinch;

    ctx.beginPath();
    ctx.fillStyle = isPinch ? 'red' : 'lime';
    ctx.arc(index.x * canvasElement.width, index.y * canvasElement.height, 16, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#fff';
    ctx.font = '18px Arial';
    ctx.fillText(isPinch ? 'Pinch (click)' : 'Index', index.x * canvasElement.width + 20, index.y * canvasElement.height - 10);

    ctx.strokeStyle = 'rgba(255,255,255,0.6)';
    ctx.lineWidth = 2;
    for (let i = 0; i < lm.length; i++) {
      const lx = lm[i].x * canvasElement.width;
      const ly = lm[i].y * canvasElement.height;
      ctx.beginPath();
      ctx.arc(lx, ly, 4, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,255,255,0.9)';
      ctx.fill();
    }
  } else {
    lastPinch = false;
    if (cursorElement) {
      cursorElement.classList.remove('cursor-active');
    }
    if (infoElement) {
      infoElement.textContent = 'Gesture demo — your hand moves a browser cursor';
    }
  }

  ctx.restore();
}

if (!window.Hands || !window.Camera) {
  setStatus('MediaPipe failed to load. Check your internet connection or refresh the page.');
} else {
  const hands = new window.Hands({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
  });

  hands.setOptions({
    maxNumHands: 1,
    modelComplexity: 1,
    minDetectionConfidence: 0.7,
    minTrackingConfidence: 0.7
  });

  hands.onResults(onResults);

  const camera = new window.Camera(videoElement, {
    onFrame: async () => {
      await hands.send({image: videoElement});
    },
    width: 1280,
    height: 720
  });

  camera.start().catch((error) => {
    console.error(error);
    setStatus('Camera access was blocked or unavailable. Please allow webcam access and refresh the page.');
  });
}

function resizeCanvas() {
  if (!canvasElement) return;
  const ratio = canvasElement.width / canvasElement.height;
  const maxW = Math.min(window.innerWidth - 20, 1280);
  canvasElement.style.width = `${maxW}px`;
  canvasElement.style.height = `${Math.round(maxW / ratio)}px`;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();
