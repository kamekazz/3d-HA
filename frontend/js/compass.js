// Scene directions match daylight.js: north = -Z, east = +X.
import { camera, controls, onFrame } from './scene.js';

export function initCompass() {
  const compass = document.getElementById('scene-compass');
  const rose = compass.querySelector('.compass-rose');
  const labels = [...compass.querySelectorAll('.compass-label')];
  let previousAngle;

  function update() {
    const angle = Math.atan2(camera.position.x - controls.target.x,
      camera.position.z - controls.target.z);
    if (angle === previousAngle) return;
    previousAngle = angle;
    rose.setAttribute('transform', `rotate(${angle * 180 / Math.PI} 44 44)`);
    // Move the cardinal labels with the rose, keeping the letters upright.
    labels.forEach((label, index) => {
      const bearing = angle + index * Math.PI / 2;
      label.setAttribute('x', 44 + Math.sin(bearing) * 31);
      label.setAttribute('y', 44 - Math.cos(bearing) * 31);
    });
  }

  controls.addEventListener('change', update);
  onFrame(update); // also follows programmatic camera flights
  update();
}
