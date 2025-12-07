import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js';

const DATA_URL = './assets/data.json';

const canvas = document.getElementById('scene');
const selectEl = document.getElementById('cameraSelect');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const resetBtn = document.getElementById('resetBtn');
const statusEl = document.getElementById('status');
const imgA = document.getElementById('imgA');
const imgB = document.getElementById('imgB');
const pointSizeEl = document.getElementById('pointSize');
const durationEl = document.getElementById('duration');
const togglePointsEl = document.getElementById('togglePoints');
const opacityEl = document.getElementById('imgOpacity');
const fovEl = document.getElementById('fovRange');

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0d1117);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.01, 5000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

let pointCloud = null;
let data = null;
let activeImg = 'A';
let currentIdx = 0;

const transition = {
  active: false,
  start: 0,
  duration: 1500,
  fromPos: new THREE.Vector3(),
  toPos: new THREE.Vector3(),
  fromQuat: new THREE.Quaternion(),
  toQuat: new THREE.Quaternion(),
  nextImage: null,
};

async function init() {
  try {
    resize();
    bindUI();
    await loadData();
    populateSelect();
    if (data.point_cloud_path) buildPointCloud(data.point_cloud_path);
    buildCameraHelpers(data.cameras);
    jumpTo(0);
    animate();
  } catch (err) {
    console.error(err);
    if (statusEl) statusEl.textContent = 'Error: ' + err.message;
  }
}

function resize() {
  const w = window.innerWidth;
  const h = window.innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}
window.addEventListener('resize', resize);

async function loadData() {
  const res = await fetch(DATA_URL);
  if (!res.ok) throw new Error(`Failed to load ${DATA_URL}`);
  data = await res.json();
  if (statusEl) statusEl.textContent = `Loaded ${data.cameras.length} cameras`;
}

function buildPointCloud(plyPath) {
  const loader = new PLYLoader();
  loader.load(plyPath, (geometry) => {
    geometry.computeVertexNormals();
    const material = new THREE.PointsMaterial({
      size: parseFloat(pointSizeEl.value || 0.05),
      vertexColors: geometry.hasAttribute('color'),
      opacity: 0.8,
      transparent: true,
      sizeAttenuation: true,
    });
    pointCloud = new THREE.Points(geometry, material);
    scene.add(pointCloud);
  });
}

function buildCameraHelpers(cameras) {
  cameras.forEach((cam) => {
    const geometry = new THREE.ConeGeometry(0.05, 0.1, 4);
    const material = new THREE.MeshBasicMaterial({ color: 0xff0000 });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(...cam.position);
    mesh.quaternion.set(...cam.quaternion);
    mesh.rotateX(-Math.PI / 2); // point along -Z
    scene.add(mesh);
  });
}

function populateSelect() {
  selectEl.innerHTML = '';
  data.cameras.forEach((cam, idx) => {
    const opt = document.createElement('option');
    opt.value = idx;
    opt.textContent = `Cam ${idx}: ${cam.filename}`;
    selectEl.appendChild(opt);
  });
}

function setImage(imgName) {
  const next = activeImg === 'A' ? imgB : imgA;
  const current = activeImg === 'A' ? imgA : imgB;
  if (imgName) {
    const cleanName = imgName.split('/').pop();
    next.src = `./assets/images/${cleanName}`;
    next.classList.add('active');
    current.classList.remove('active');
    activeImg = activeImg === 'A' ? 'B' : 'A';
  }
}

function jumpTo(idx) {
  if (!data || !data.cameras[idx]) return;
  currentIdx = idx;
  const cam = data.cameras[idx];
  camera.position.set(...cam.position);
  camera.quaternion.set(...cam.quaternion);
  setImage(cam.filename);
  selectEl.value = String(idx);
  const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
  controls.target.copy(camera.position).add(forward);
  controls.update();
}

function startTransition(nextIdx) {
  if (nextIdx < 0 || nextIdx >= data.cameras.length) return;
  const targetCam = data.cameras[nextIdx];
  transition.active = true;
  transition.start = performance.now();
  transition.duration = (parseFloat(durationEl.value) || 1.5) * 1000;
  transition.fromPos.copy(camera.position);
  transition.toPos.set(...targetCam.position);
  transition.fromQuat.copy(camera.quaternion);
  transition.toQuat.set(...targetCam.quaternion);
  transition.nextImage = targetCam.filename;
  imgA.classList.remove('active');
  imgB.classList.remove('active');
  currentIdx = nextIdx;
  selectEl.value = String(nextIdx);
}

function animate() {
  requestAnimationFrame(animate);
  if (transition.active) {
    const now = performance.now();
    let t = (now - transition.start) / transition.duration;
    if (t >= 1) {
      t = 1;
      transition.active = false;
      camera.position.copy(transition.toPos);
      camera.quaternion.copy(transition.toQuat);
      setImage(transition.nextImage);
    } else {
      camera.position.lerpVectors(transition.fromPos, transition.toPos, t);
      THREE.Quaternion.slerp(transition.fromQuat, transition.toQuat, camera.quaternion, t);
    }
  }
  controls.update();
  renderer.render(scene, camera);
}

function bindUI() {
  prevBtn.addEventListener('click', () => {
    const nextIdx = (currentIdx - 1 + data.cameras.length) % data.cameras.length;
    startTransition(nextIdx);
  });
  nextBtn.addEventListener('click', () => {
    const cam = data.cameras[currentIdx];
    if (cam.neighbors && cam.neighbors.length > 0) {
      startTransition(cam.neighbors[0]);
    } else {
      const nextIdx = (currentIdx + 1) % data.cameras.length;
      startTransition(nextIdx);
    }
  });
  resetBtn.addEventListener('click', () => jumpTo(0));
  selectEl.addEventListener('change', (e) => startTransition(Number(e.target.value)));
  pointSizeEl.addEventListener('input', () => {
    if (pointCloud) pointCloud.material.size = parseFloat(pointSizeEl.value);
  });
  togglePointsEl.addEventListener('change', () => {
    if (pointCloud) pointCloud.visible = togglePointsEl.checked;
  });
  if (opacityEl) {
    opacityEl.addEventListener('input', () => {
      const val = opacityEl.value;
      imgA.style.opacity = val;
      imgB.style.opacity = val;
      document.querySelectorAll('.bg.active').forEach((el) => (el.style.opacity = val));
    });
  }
  if (fovEl) {
    fovEl.addEventListener('input', () => {
      camera.fov = parseFloat(fovEl.value);
      camera.updateProjectionMatrix();
    });
  }
}

init();
