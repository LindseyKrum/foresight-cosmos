import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const CURRENT_YEAR = 2025;
const DYING_AGE    = 2;   // years since lastSeen before a signal "dies"

// ── Palette ────────────────────────────────────────────────────────────────
const C = {
  fresh:    new THREE.Color(0.68, 0.82, 1.0),   // cool blue-white
  aging:    new THREE.Color(0.94, 0.87, 0.55),  // warm yellow
  dying:    new THREE.Color(1.0,  0.47, 0.22),  // ember orange
  scenario: new THREE.Color(0.53, 0.95, 0.65),  // green
};

// ── Per-planet colors (19 macro-planets, ordered t001–t019) ────────────────
const PLANET_COLORS = {
  t001: new THREE.Color(0.27, 0.53, 1.00),  // electric blue    — AI Infrastructure
  t002: new THREE.Color(0.60, 0.27, 1.00),  // deep violet      — Cybersecurity & Data
  t003: new THREE.Color(0.27, 0.73, 0.95),  // steel blue       — AI in Business
  t004: new THREE.Color(1.00, 0.27, 0.67),  // hot magenta      — AI in Creativity
  t005: new THREE.Color(1.00, 0.42, 0.27),  // coral            — Creator Economy
  t006: new THREE.Color(1.00, 0.67, 0.13),  // amber            — Brand & Marketing
  t007: new THREE.Color(0.67, 0.90, 0.20),  // yellow-green     — Consumer Behavior
  t008: new THREE.Color(1.00, 0.65, 0.80),  // rose pink        — Fashion & Aesthetics
  t009: new THREE.Color(0.20, 1.00, 0.65),  // mint             — Health & Medicine
  t010: new THREE.Color(0.33, 0.87, 0.50),  // soft green       — Wellbeing
  t011: new THREE.Color(0.13, 0.90, 1.00),  // bright cyan      — Future of Work
  t012: new THREE.Color(0.13, 0.80, 0.38),  // emerald          — Climate & Sustainability
  t013: new THREE.Color(1.00, 0.33, 0.20),  // red-orange       — Geopolitics
  t014: new THREE.Color(1.00, 0.80, 0.20),  // gold             — Financial Markets
  t015: new THREE.Color(0.00, 0.93, 1.00),  // neon cyan        — Emerging Tech & Crypto
  t016: new THREE.Color(1.00, 0.55, 0.15),  // orange           — Food & Nutrition
  t017: new THREE.Color(0.40, 0.80, 1.00),  // sky blue         — Travel & Experience
  t018: new THREE.Color(0.80, 0.27, 1.00),  // vivid purple     — Gaming & Entertainment
  t019: new THREE.Color(0.85, 0.85, 1.00),  // silver-white     — Futures & Foresight
};

// ── Glow sprite factory ─────────────────────────────────────────────────────
function makeGlowTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0,   'rgba(255,255,255,1)');
  g.addColorStop(0.3, 'rgba(255,255,255,0.4)');
  g.addColorStop(1,   'rgba(0,0,0,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
}
const GLOW_TEX = makeGlowTexture();

function addGlow(scene, pos, color, size, opacity) {
  const mat = new THREE.SpriteMaterial({
    map: GLOW_TEX,
    color: color.clone(),
    transparent: true,
    opacity,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const s = new THREE.Sprite(mat);
  s.scale.setScalar(size);
  s.position.copy(pos);
  scene.add(s);
  return s;
}

// ── Background star field ───────────────────────────────────────────────────
function buildStarfield(scene) {
  const N = 5000;
  const pos  = new Float32Array(N * 3);
  const col  = new Float32Array(N * 3);
  const size = new Float32Array(N);

  for (let i = 0; i < N; i++) {
    const r     = 350 + Math.random() * 500;
    const theta = Math.random() * Math.PI * 2;
    const phi   = Math.acos(2 * Math.random() - 1);
    pos[i*3]   = r * Math.sin(phi) * Math.cos(theta);
    pos[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
    pos[i*3+2] = r * Math.cos(phi);

    const warm = Math.random();
    col[i*3]   = 0.65 + warm * 0.35;
    col[i*3+1] = 0.65 + warm * 0.12;
    col[i*3+2] = 0.75 + (1 - warm) * 0.25;

    size[i] = 0.3 + Math.random() * 1.2;
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('aColor',   new THREE.BufferAttribute(col, 3));
  geo.setAttribute('aSize',    new THREE.BufferAttribute(size, 1));

  const mat = new THREE.ShaderMaterial({
    uniforms: { time: { value: 0 } },
    vertexShader: `
      attribute float aSize;
      attribute vec3 aColor;
      varying vec3 vColor;
      uniform float time;
      void main() {
        vColor = aColor;
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        float twinkle = 1.0 + 0.25 * sin(time * 1.5 + position.x * 0.3 + position.y * 0.2);
        gl_PointSize  = aSize * twinkle * (300.0 / -mv.z);
        gl_Position   = projectionMatrix * mv;
      }
    `,
    fragmentShader: `
      varying vec3 vColor;
      void main() {
        float d = length(gl_PointCoord - 0.5) * 2.0;
        float a = 1.0 - smoothstep(0.5, 1.0, d);
        gl_FragColor = vec4(vColor, a * 0.65);
      }
    `,
    transparent: true,
    depthWrite: false,
    vertexColors: true,
  });

  scene.add(new THREE.Points(geo, mat));
  return mat; // so we can update time uniform
}

// ── Layout helpers ──────────────────────────────────────────────────────────
function goldenSphere(n, radius) {
  // Fibonacci spiral on sphere for even distribution
  return Array.from({ length: n }, (_, i) => {
    const phi   = Math.acos(1 - (2 * (i + 0.5)) / n);
    const theta = Math.PI * (1 + Math.sqrt(5)) * i;
    return new THREE.Vector3(
      radius * Math.sin(phi) * Math.cos(theta),
      radius * Math.sin(phi) * Math.sin(theta),
      radius * Math.cos(phi)
    );
  });
}

// ── Signal color by age ─────────────────────────────────────────────────────
function signalColor(signal) {
  const age = CURRENT_YEAR - signal.lastSeen;
  if (age >= DYING_AGE)  return C.dying.clone();
  if (age === 1)         return C.aging.clone();
  return C.fresh.clone();
}

function signalOpacity(signal) {
  const age = CURRENT_YEAR - signal.lastSeen;
  if (age >= DYING_AGE) return 0.25 + signal.strength * 0.2;
  if (age === 1)        return 0.5  + signal.strength * 0.3;
  return                       0.7  + signal.strength * 0.3;
}

// ── Main ────────────────────────────────────────────────────────────────────
async function init() {
  const data    = await fetch('../data/cosmos.json').then(r => r.json());
  const isMobile = window.innerWidth <= 767;

  // Scene / renderer
  const scene    = new THREE.Scene();
  const camera   = new THREE.PerspectiveCamera(
    isMobile ? 65 : 55,   // wider FOV on mobile — fits more in frame
    innerWidth / innerHeight, 0.1, 2000
  );
  camera.position.set(0, 30, isMobile ? 185 : 150);

  const renderer = new THREE.WebGLRenderer({ antialias: !isMobile });
  renderer.setPixelRatio(Math.min(devicePixelRatio, isMobile ? 1.5 : 2));
  renderer.setSize(innerWidth, innerHeight);
  renderer.setClearColor(0x000008);
  document.getElementById('canvas-container').appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping    = true;
  controls.dampingFactor    = 0.06;
  controls.minDistance      = 3;
  controls.maxDistance      = 450;
  controls.autoRotate       = true;
  controls.autoRotateSpeed  = isMobile ? 0.06 : 0.10;
  controls.enablePan        = true;
  controls.panSpeed         = isMobile ? 0.5 : 0.8;
  controls.touches = {
    ONE:   THREE.TOUCH.ROTATE,
    TWO:   THREE.TOUCH.DOLLY_PAN,
  };

  // Mobile nav hint — tap instead of click
  if (isMobile) {
    const hints = document.querySelectorAll('.nav-hint-line');
    if (hints[0]) hints[0].textContent = 'Pinch to zoom · Drag to orbit';
    if (hints[1]) hints[1].textContent = 'Tap any object to explore';
  }

  // ── Camera fly-to animation state ──
  const DEFAULT_CAM_POS  = new THREE.Vector3(0, 30, 150);
  const DEFAULT_CAM_LOOK = new THREE.Vector3(0, 0, 0);

  const fly = {
    active:    false,
    t:         0,
    duration:  1.8,           // seconds
    fromPos:   new THREE.Vector3(),
    fromLook:  new THREE.Vector3(),
    toPos:     new THREE.Vector3(),
    toLook:    new THREE.Vector3(),
  };

  function flyTo(targetPos, lookAt, dur = 1.8) {
    fly.fromPos.copy(camera.position);
    fly.fromLook.copy(controls.target);
    fly.toPos.copy(targetPos);
    fly.toLook.copy(lookAt);
    fly.t        = 0;
    fly.duration = dur;
    fly.active   = true;
    controls.autoRotate = false;
    document.getElementById('reset-view').style.display = 'block';
  }

  function resetView() {
    flyTo(DEFAULT_CAM_POS, DEFAULT_CAM_LOOK, 1.6);
    controls.autoRotate = true;
    document.getElementById('reset-view').style.display = 'none';
  }

  document.getElementById('reset-view').addEventListener('click', resetView);
  window.addEventListener('keydown', e => { if (e.key === 'r' || e.key === 'R') resetView(); });

  // Fog for depth
  scene.fog = new THREE.FogExp2(0x000008, 0.0018);

  // Lighting
  scene.add(new THREE.AmbientLight(0x112233, 0.8));
  const sunLight = new THREE.PointLight(0xffd090, 3, 300);
  sunLight.position.set(0, 0, 0);
  scene.add(sunLight);

  const starMat = buildStarfield(scene);

  // ── Position trends ──
  const trendCount  = data.trends.length;
  const trendSphPos = goldenSphere(trendCount, 65);
  const trendPos    = {}; // id → Vector3
  data.trends.forEach((t, i) => { trendPos[t.id] = trendSphPos[i]; });

  // ── Position signals ── near their first connected trend, with orbital spread
  const signalPos = {}; // id → Vector3
  const rng = seededRandom(42);
  data.signals.forEach((sig, i) => {
    const primary = sig.connections[0];
    const base    = trendPos[primary] || new THREE.Vector3();
    const spread  = 16 + rng() * 12;
    const angle   = rng() * Math.PI * 2;
    const elev    = (rng() - 0.5) * spread * 0.8;
    const radius  = spread * (0.6 + rng() * 0.4);
    signalPos[sig.id] = new THREE.Vector3(
      base.x + Math.cos(angle) * radius,
      base.y + elev,
      base.z + Math.sin(angle) * radius
    );
  });

  // ── Draw connection lines ──
  const lineGroup = new THREE.Group();
  scene.add(lineGroup);

  data.signals.forEach(sig => {
    sig.connections.forEach((tid, connIdx) => {
      const from = signalPos[sig.id];
      const to   = trendPos[tid];
      if (!from || !to) return;

      const age       = CURRENT_YEAR - sig.lastSeen;
      const isPrimary = connIdx === 0;
      const isDying   = age >= DYING_AGE;
      const strength  = sig.strength ?? 0.6;   // 0–1

      // Colour: use the target planet's colour; dying signals go ember
      const planetCol = PLANET_COLORS[tid] ?? new THREE.Color(0.4, 0.5, 0.8);
      const lineCol   = isDying ? C.dying.clone().multiplyScalar(0.5) : planetCol.clone();

      // Opacity: scaled by signal strength, dimmer for secondaries and dying
      const baseOp = isDying   ? 0.06 + strength * 0.08
                   : isPrimary ? 0.15 + strength * 0.25   // 0.15–0.40
                               : 0.12 + strength * 0.20;  // cross-planet slightly dimmer

      const geo = new THREE.BufferGeometry().setFromPoints([from, to]);
      const mat = new THREE.LineDashedMaterial({
        color:       lineCol,
        transparent: true,
        opacity:     baseOp,
        dashSize:    isPrimary ? 1.4 : 0.5,
        gapSize:     isPrimary ? 0.9 : 0.5,
      });

      const line = new THREE.Line(geo, mat);
      line.computeLineDistances();
      lineGroup.add(line);
    });
  });

  // ── Tension arcs ──
  const tensionGroup = new THREE.Group();
  tensionGroup.visible = false;
  scene.add(tensionGroup);

  const tensionPairsSeen = new Set();
  data.signals.forEach(sig => {
    (sig.tensions || []).forEach(t => {
      const key = [sig.id, t.signal].sort().join('|');
      if (tensionPairsSeen.has(key)) return;
      tensionPairsSeen.add(key);
      const from = signalPos[sig.id];
      const to   = signalPos[t.signal];
      if (!from || !to) return;
      const geo = new THREE.BufferGeometry().setFromPoints([from, to]);
      const mat = new THREE.LineDashedMaterial({
        color:       new THREE.Color(1.0, 0.45, 0.20),
        transparent: true,
        opacity:     0.50,
        dashSize:    0.55,
        gapSize:     0.80,
      });
      const line = new THREE.Line(geo, mat);
      line.computeLineDistances();
      line.userData.label = t.label;
      tensionGroup.add(line);
    });
  });

  // ── Interactables ──
  const interactable = [];
  const objMeta      = new Map(); // mesh → { type, data }

  // ── Trend planets ──
  const dyingSignalMeshes = []; // for pulsing animation
  const signalMeshList    = []; // { mesh, sig } — for driver filter

  data.trends.forEach(trend => {
    const pos      = trendPos[trend.id];
    const size     = 2.8 + trend.mass * 1.8;
    const pCol     = (PLANET_COLORS[trend.id] ?? new THREE.Color(0.96, 0.78, 0.26)).clone();

    // Convergence-scaled glow
    const conv  = trend.convergenceScore ?? 0.33;
    const emInt = 0.18 + conv * 0.55;          // 0.18 (niche) → 0.73 (universal)
    const glowR = size * (4.0 + conv * 6.0);   // tighter for niche, expansive for universal
    const glowO = 0.12 + conv * 0.28;          // 0.12 → 0.40

    const geo  = new THREE.SphereGeometry(size, 40, 40);
    const mat  = new THREE.MeshStandardMaterial({
      color:             pCol.clone().multiplyScalar(0.55),
      emissive:          pCol.clone(),
      emissiveIntensity: emInt,
      roughness:         0.50,
      metalness:         0.20,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(pos);
    scene.add(mesh);
    interactable.push(mesh);
    objMeta.set(mesh, { type: 'trend', data: trend });

    // Atmosphere ring — tinted to planet colour, width scales with convergence
    const ringOuter = size + 1.2 + conv * 1.8;
    const ringGeo = new THREE.RingGeometry(size + 0.4, ringOuter, 64);
    const ringMat = new THREE.MeshBasicMaterial({
      color:      pCol.clone(),
      side:       THREE.DoubleSide,
      transparent: true,
      opacity:    0.06 + conv * 0.10,
      depthWrite: false,
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2 + (Math.random() - 0.5) * 0.6;
    ring.position.copy(pos);
    scene.add(ring);

    addGlow(scene, pos, pCol, glowR, glowO);

    // Scenarios as city-lights on surface
    const scenarios = data.scenarios.filter(s => s.trend === trend.id);
    scenarios.forEach((sc, si) => {
      const phi   = ((si + 0.5) / scenarios.length) * Math.PI * 0.9 + 0.2;
      const theta = (si / scenarios.length) * Math.PI * 2;
      const cp    = new THREE.Vector3(
        pos.x + (size + 0.25) * Math.sin(phi) * Math.cos(theta),
        pos.y + (size + 0.25) * Math.cos(phi),
        pos.z + (size + 0.25) * Math.sin(phi) * Math.sin(theta)
      );

      const cGeo  = new THREE.SphereGeometry(0.28, 8, 8);
      const cMat  = new THREE.MeshBasicMaterial({ color: C.scenario.clone() });
      const cMesh = new THREE.Mesh(cGeo, cMat);
      cMesh.position.copy(cp);
      scene.add(cMesh);
      interactable.push(cMesh);
      objMeta.set(cMesh, { type: 'scenario', data: sc });
      addGlow(scene, cp, C.scenario, 2.2, 0.45);
    });
  });

  // ── Signal stars ──
  data.signals.forEach(sig => {
    const pos  = signalPos[sig.id];
    const age  = CURRENT_YEAR - sig.lastSeen;
    const col  = signalColor(sig);
    const op   = signalOpacity(sig);
    const size = 0.35 + sig.strength * 0.75;

    // Merged signals get a size and glow boost
    const mergeBoost = sig.mergeCount ? 1 + (sig.mergeCount - 1) * 0.35 : 1;
    const drawSize   = size * mergeBoost;

    const geo  = new THREE.SphereGeometry(drawSize, 10, 10);
    const mat  = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: op });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(pos);
    mesh.userData.baseOp   = op;
    mesh.userData.drivers  = sig.drivers  || [];
    mesh.userData.tensions = sig.tensions || [];
    scene.add(mesh);
    interactable.push(mesh);
    objMeta.set(mesh, { type: 'signal', data: sig });
    signalMeshList.push({ mesh, sig });

    const glowOp   = age >= DYING_AGE ? 0.12 : (0.22 + sig.strength * 0.2) * mergeBoost;
    const glowSize = age >= DYING_AGE ? drawSize * 5 : drawSize * 6 + sig.strength * 3;
    addGlow(scene, pos, col, glowSize, glowOp);

    if (age >= DYING_AGE) {
      dyingSignalMeshes.push({ mesh, baseOp: op });
    }
  });

  // ── Raycaster / hover + tap ──
  const raycaster = new THREE.Raycaster();
  raycaster.params.Mesh.threshold = isMobile ? 1.2 : 0.5;  // bigger hit target on mobile
  const mouse     = new THREE.Vector2(-9999, -9999);
  let hoveredMesh = null;
  const tooltip   = document.getElementById('tooltip');
  const ttType    = document.getElementById('tooltip-type');
  const ttName    = document.getElementById('tooltip-name');

  window.addEventListener('mousemove', e => {
    mouse.x = (e.clientX / innerWidth)  *  2 - 1;
    mouse.y = (e.clientY / innerHeight) * -2 + 1;
    tooltip.style.left = (e.clientX + 16) + 'px';
    tooltip.style.top  = e.clientY + 'px';
  });

  // Mobile tap detection — fire on touchend if finger didn't move much
  if (isMobile) {
    let touchStartX = 0, touchStartY = 0;
    renderer.domElement.addEventListener('touchstart', e => {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    }, { passive: true });
    renderer.domElement.addEventListener('touchend', e => {
      const dx = e.changedTouches[0].clientX - touchStartX;
      const dy = e.changedTouches[0].clientY - touchStartY;
      if (Math.hypot(dx, dy) > 10) return; // was a drag, not a tap
      const cx = e.changedTouches[0].clientX;
      const cy = e.changedTouches[0].clientY;
      mouse.x = (cx / innerWidth)  *  2 - 1;
      mouse.y = (cy / innerHeight) * -2 + 1;
      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(interactable);
      if (!hits.length) return;
      const obj  = hits[0].object;
      const info = objMeta.get(obj);
      if (!info) return;
      const objPos = obj.position.clone();
      if (info.type === 'trend') {
        const sz = 2.8 + (info.data.mass ?? 1) * 1.8;
        flyTo(objPos.clone().add(new THREE.Vector3(0, sz * 2, sz * 6 + 18)), objPos);
      } else {
        flyTo(objPos.clone().add(new THREE.Vector3(0, 4, 14)), objPos);
      }
      openPanel(info, data);
    }, { passive: true });
    tooltip.style.display = 'none'; // no hover tooltip on mobile
  }

  window.addEventListener('click', () => {
    if (!hoveredMesh || !objMeta.has(hoveredMesh)) return;
    const info = objMeta.get(hoveredMesh);

    // Fly camera toward the clicked object before opening the panel
    const objPos = hoveredMesh.position.clone();
    if (info.type === 'trend') {
      // For planets: pull back to show the whole planet + its signal cluster
      const size    = 2.8 + (info.data.mass ?? 1) * 1.8;
      const offset  = camera.position.clone().sub(objPos).normalize().multiplyScalar(size * 6 + 18);
      flyTo(objPos.clone().add(offset), objPos);
    } else {
      // For signals / scenarios: zoom close
      const offset = camera.position.clone().sub(objPos).normalize().multiplyScalar(12);
      flyTo(objPos.clone().add(offset), objPos);
    }

    openPanel(info, data);
  });

  document.getElementById('panel-close').addEventListener('click', () => {
    document.getElementById('panel').classList.remove('open');
    history.replaceState(null, '', location.pathname + location.search.replace(/[?&][st]=\w+/, '').replace(/^&/, '?'));
    if (location.search === '?') history.replaceState(null, '', location.pathname);
  });

  // ── Planet legend ──
  const planetList = document.getElementById('planet-list');
  data.trends.forEach(trend => {
    const pc  = PLANET_COLORS[trend.id] ?? new THREE.Color(1,1,1);
    const hex = '#' + pc.getHexString();
    const item = document.createElement('div');
    item.className = 'planet-legend-item';
    item.innerHTML = `
      <div class="planet-legend-dot" style="background:${hex};box-shadow:0 0 5px ${hex}88;"></div>
      ${trend.name}`;
    item.addEventListener('click', () => {
      const pos  = trendPos[trend.id];
      if (!pos) return;
      const size   = 2.8 + trend.mass * 1.8;
      const offset = new THREE.Vector3(0, size * 2, size * 6 + 18);
      flyTo(pos.clone().add(offset), pos.clone());
      openPanel({ type: 'trend', data: trend }, data);
    });
    planetList.appendChild(item);
  });

  // On mobile: planet list starts collapsed, also close panel on planet click
  if (isMobile) {
    planetList.classList.add('hidden');
    planetList.querySelectorAll('.planet-legend-item').forEach(el => {
      el.addEventListener('click', () => { planetList.classList.add('hidden'); });
    });
  }

  document.getElementById('legend-toggle').addEventListener('click', () => {
    planetList.classList.toggle('hidden');
    // On mobile: close driver list when opening planet list
    if (isMobile && !planetList.classList.contains('hidden')) {
      document.getElementById('driver-list').classList.remove('visible');
    }
  });

  // ── Driver filters ──
  const DRIVERS = [
    { id: 'technological-acceleration',   label: 'Technological Acceleration', color: '#a78bfa' },
    { id: 'demographic-shift',            label: 'Demographic Shift',          color: '#fb923c' },
    { id: 'geopolitical-fragmentation',   label: 'Geopolitical Fragmentation', color: '#f87171' },
    { id: 'resource-environmental-pressure', label: 'Resource & Environmental Pressure', color: '#34d399' },
    { id: 'economic-realignment',         label: 'Economic Realignment',       color: '#f5c842' },
    { id: 'cultural-reorientation',       label: 'Cultural Reorientation',     color: '#ff85c2' },
    { id: 'governance-regulatory-change', label: 'Governance & Regulatory Change', color: '#7eb8f7' },
  ];

  let activeDriver = null;
  const driverList = document.getElementById('driver-list');

  DRIVERS.forEach(d => {
    const btn = document.createElement('button');
    btn.className = 'driver-btn';
    btn.dataset.driver = d.id;
    btn.textContent = d.label;
    btn.style.setProperty('--driver-color', d.color);
    btn.addEventListener('click', () => {
      const isActive = btn.classList.contains('active');
      driverList.querySelectorAll('.driver-btn').forEach(b => b.classList.remove('active'));
      if (isActive) {
        activeDriver = null;
        // Restore all signal meshes
        signalMeshList.forEach(({ mesh }) => {
          mesh.material.opacity = mesh.userData.baseOp;
        });
      } else {
        btn.classList.add('active');
        activeDriver = d.id;
        // Dim non-matching signals
        signalMeshList.forEach(({ mesh }) => {
          const matches = (mesh.userData.drivers || []).includes(activeDriver);
          mesh.material.opacity = matches ? mesh.userData.baseOp : 0.04;
        });
      }
    });
    driverList.appendChild(btn);
  });

  document.getElementById('driver-toggle').addEventListener('click', () => {
    driverList.classList.toggle('visible');
    // On mobile: close planet list when opening driver list
    if (isMobile && driverList.classList.contains('visible')) {
      planetList.classList.add('hidden');
    }
  });

  // ── Search ──
  const searchInput   = document.getElementById('search-input');
  const searchResults = document.getElementById('search-results');

  // Build flat search index: trends + signals
  const searchIndex = [
    ...data.trends.map(t  => ({ type: 'trend',  data: t,  text: `${t.name} ${t.description}`.toLowerCase() })),
    ...data.signals.map(s => ({ type: 'signal', data: s,  text: `${s.name} ${s.description}`.toLowerCase() })),
  ];

  function highlight(str, query) {
    const re = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return str.replace(re, '<mark>$1</mark>');
  }

  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim().toLowerCase();
    if (q.length < 2) { searchResults.style.display = 'none'; return; }

    const hits = searchIndex.filter(entry => entry.text.includes(q)).slice(0, 20);
    if (hits.length === 0) {
      searchResults.style.display = 'block';
      searchResults.innerHTML = `<div id="search-empty">No matches for "${q}"</div>`;
      return;
    }

    searchResults.style.display = 'block';
    searchResults.innerHTML = hits.map((entry, i) => `
      <div class="search-result-item" data-idx="${i}">
        <div class="search-result-type">${entry.type === 'trend' ? 'Trend Planet' : 'Weak Signal'}</div>
        <div class="search-result-name">${highlight(entry.data.name, searchInput.value.trim())}</div>
      </div>`).join('');

    searchResults.querySelectorAll('.search-result-item').forEach((el, i) => {
      el.addEventListener('click', () => {
        const entry = hits[i];
        searchInput.value = '';
        searchResults.style.display = 'none';

        if (entry.type === 'trend') {
          const pos  = trendPos[entry.data.id];
          if (!pos) return;
          const size = 2.8 + entry.data.mass * 1.8;
          flyTo(pos.clone().add(new THREE.Vector3(0, size * 2, size * 6 + 18)), pos.clone());
          openPanel({ type: 'trend', data: entry.data }, data);
        } else {
          const pos = signalPos[entry.data.id];
          if (!pos) return;
          const offset = new THREE.Vector3(0, 4, 14);
          flyTo(pos.clone().add(offset), pos.clone());
          openPanel({ type: 'signal', data: entry.data }, data);
        }
      });
    });
  });

  // Close search results when clicking outside
  document.addEventListener('click', e => {
    if (!document.getElementById('search-wrap').contains(e.target)) {
      searchResults.style.display = 'none';
    }
  });

  searchInput.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      searchInput.value = '';
      searchResults.style.display = 'none';
      searchInput.blur();
    }
  });

  // ── Filters ──
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const f = btn.dataset.filter;

      lineGroup.visible    = (f === 'all' || f === 'connections');
      tensionGroup.visible = (f === 'tensions');

      // Clear any active driver filter when switching main filters
      if (activeDriver) {
        activeDriver = null;
        driverList.querySelectorAll('.driver-btn').forEach(b => b.classList.remove('active'));
        signalMeshList.forEach(({ mesh }) => { mesh.material.opacity = mesh.userData.baseOp; });
      }

      interactable.forEach(m => {
        const info = objMeta.get(m);
        if (!info) return;
        m.visible = true;
        if (f === 'tensions') {
          if (info.type === 'signal') {
            const hasTension = m.userData.tensions?.length > 0;
            m.material.opacity = hasTension ? m.userData.baseOp : 0.04;
          }
        } else if (f === 'new') {
          // Highlight signals from 2025 reports; dim older ones
          if (info.type === 'signal') {
            const isNew = (info.data.lastSeen ?? 0) >= 2025;
            m.material.opacity = isNew ? m.userData.baseOp : 0.04;
          }
        } else if (f === 'weak') {
          // Highlight single-source signals (not yet corroborated)
          if (info.type === 'signal') {
            const isWeak = (info.data.sources?.length ?? 0) === 1;
            m.material.opacity = isWeak ? m.userData.baseOp : 0.04;
          }
        } else {
          if (info.type === 'signal') m.material.opacity = m.userData.baseOp;
          m.visible = f === 'all' || f === 'connections'
            || (f === 'signals' && info.type === 'signal')
            || (f === 'trends'  && (info.type === 'trend' || info.type === 'scenario'));
        }
      });
    });
  });

  // ── Meta UI ──
  document.getElementById('report-count').textContent =
    `${data.meta.reportCount} reports · ${data.meta.yearRange[0]}–${data.meta.yearRange[1]}`;

  // ── Resize ──
  window.addEventListener('resize', () => {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
  });

  // ── Render loop ──
  const clock   = new THREE.Clock();
  let elapsed   = 0;

  function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();   // call once per frame
    elapsed    += delta;
    const t     = elapsed;

    starMat.uniforms.time.value = t;

    // ── Camera fly animation ──
    if (fly.active) {
      fly.t = Math.min(1, fly.t + delta / fly.duration);
      const ease = 1 - Math.pow(1 - fly.t, 3);   // cubic ease-out
      camera.position.lerpVectors(fly.fromPos, fly.toPos, ease);
      controls.target.lerpVectors(fly.fromLook, fly.toLook, ease);
      if (fly.t >= 1) fly.active = false;
    }

    // Pulse dying signals
    dyingSignalMeshes.forEach(({ mesh, baseOp }, i) => {
      mesh.material.opacity = baseOp * (0.4 + 0.6 * (0.5 + 0.5 * Math.sin(t * 0.9 + i * 1.7)));
    });

    // Hover detection
    raycaster.setFromCamera(mouse, camera);
    const hits = raycaster.intersectObjects(interactable);

    if (hits.length > 0) {
      const obj  = hits[0].object;
      const info = objMeta.get(obj);
      if (info) {
        hoveredMesh = obj;
        ttType.textContent = info.type === 'signal' ? 'Weak Signal' : info.type === 'trend' ? 'Trend' : 'Scenario';
        ttName.textContent = info.data.name;
        tooltip.style.display = 'block';
        renderer.domElement.style.cursor = 'pointer';
      }
    } else {
      hoveredMesh = null;
      tooltip.style.display = 'none';
      renderer.domElement.style.cursor = 'grab';
    }

    controls.update();
    renderer.render(scene, camera);
  }

  animate();

  // ── Fade out loading ──
  const loading = document.getElementById('loading');
  loading.style.transition = 'opacity 0.8s';
  loading.style.opacity    = '0';
  setTimeout(() => { loading.style.display = 'none'; }, 900);

  // ── Deep link: auto-open signal or trend from URL params ──
  const qp       = new URLSearchParams(location.search);
  const deepSig  = qp.get('s');
  const deepTrnd = qp.get('t');
  if (deepSig || deepTrnd) {
    setTimeout(() => {
      if (deepSig) {
        const sig = data.signals.find(s => s.id === deepSig);
        if (sig) {
          openPanel({ type: 'signal', data: sig }, data);
          const pos = signalPos[deepSig];
          if (pos) flyTo(pos.clone().add(new THREE.Vector3(0, 4, 14)), pos);
        }
      } else if (deepTrnd) {
        const trend = data.trends.find(t => t.id === deepTrnd);
        if (trend) {
          openPanel({ type: 'trend', data: trend }, data);
          const pos = trendPos[deepTrnd];
          if (pos) {
            const size = 2.8 + trend.mass * 1.8;
            flyTo(pos.clone().add(new THREE.Vector3(0, size * 2, size * 6 + 18)), pos);
          }
        }
      }
    }, 600);
  }

  // ── What's New ──
  const LAST_VISIT_KEY = 'foresight_last_visit';
  const lastVisit      = localStorage.getItem(LAST_VISIT_KEY);
  const today          = new Date().toISOString().split('T')[0];
  const newSignals     = lastVisit
    ? data.signals.filter(s => s.addedDate && s.addedDate > lastVisit)
    : [];

  const updatesBtn    = document.getElementById('updates-btn');
  const updatesBadge  = document.getElementById('updates-badge');
  const updatesDrawer = document.getElementById('updates-drawer');
  const updatesBody   = document.getElementById('updates-body');

  if (newSignals.length > 0 && updatesBadge) {
    updatesBadge.textContent      = newSignals.length;
    updatesBadge.style.display    = 'inline-block';
  }

  function buildUpdatesContent() {
    const lastUpdated = data.meta?.generated || 'unknown';
    const [yr0, yr1]  = data.meta?.yearRange ?? [2024, 2025];
    let html = `
      <div class="updates-meta">
        Last updated <strong>${lastUpdated}</strong>
        <span class="updates-meta-sub">${data.signals.length} signals · ${data.meta?.reportCount ?? '—'} reports · ${yr0}–${yr1}</span>
      </div>`;

    if (newSignals.length > 0) {
      html += `<div class="updates-section-label">New since ${lastVisit}</div>`;
      const byTrend = {};
      newSignals.forEach(s => {
        const tid   = s.connections?.[0];
        const tname = (tid && data.trends.find(t => t.id === tid)?.name) || 'Other';
        if (!byTrend[tname]) byTrend[tname] = [];
        byTrend[tname].push(s);
      });
      Object.entries(byTrend).forEach(([trendName, sigs]) => {
        html += `<div class="updates-trend-group">
          <div class="updates-trend-name">${trendName}</div>
          ${sigs.map(s => `<div class="updates-signal-item" data-sid="${s.id}">★ ${s.name}</div>`).join('')}
        </div>`;
      });
    } else if (lastVisit) {
      html += `<div class="updates-empty">Up to date — no new signals since ${lastVisit}.</div>`;
    } else {
      html += `<div class="updates-empty">First visit — all ${data.signals.length} signals loaded.</div>`;
    }

    html += `
      <div class="updates-quick-btns">
        <button class="updates-quick-btn" data-filter="new">Show 2025 signals</button>
        <button class="updates-quick-btn" data-filter="weak">Show weak signals</button>
      </div>`;

    if (updatesBody) updatesBody.innerHTML = html;

    // Wire up signal-item clicks inside drawer
    updatesBody?.querySelectorAll('.updates-signal-item[data-sid]').forEach(el => {
      el.addEventListener('click', () => {
        const sig = data.signals.find(s => s.id === el.dataset.sid);
        if (!sig) return;
        closeUpdatesDrawer();
        openPanel({ type: 'signal', data: sig }, data);
        const pos = signalPos[sig.id];
        if (pos) flyTo(pos.clone().add(new THREE.Vector3(0, 4, 14)), pos);
      });
    });

    // Quick filter buttons inside drawer
    updatesBody?.querySelectorAll('.updates-quick-btn[data-filter]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelector(`.filter-btn[data-filter="${btn.dataset.filter}"]`)?.click();
        closeUpdatesDrawer();
      });
    });
  }

  function openUpdatesDrawer() {
    buildUpdatesContent();
    updatesDrawer?.classList.add('open');
    localStorage.setItem(LAST_VISIT_KEY, today);
    if (updatesBadge) updatesBadge.style.display = 'none';
  }

  function closeUpdatesDrawer() {
    updatesDrawer?.classList.remove('open');
  }

  updatesBtn?.addEventListener('click', e => { e.stopPropagation(); openUpdatesDrawer(); });
  document.getElementById('updates-close')?.addEventListener('click', closeUpdatesDrawer);
  document.addEventListener('click', e => {
    if (updatesDrawer?.classList.contains('open') &&
        !updatesDrawer.contains(e.target) &&
        e.target !== updatesBtn) {
      closeUpdatesDrawer();
    }
  });
}

// ── Panel ───────────────────────────────────────────────────────────────────
function openPanel({ type, data: obj }, cosmos) {
  document.getElementById('panel-type').textContent =
    type === 'signal' ? 'Weak Signal' : type === 'trend' ? 'Trend' : 'Scenario';
  document.getElementById('panel-title').textContent = obj.name;
  document.getElementById('panel-desc').textContent  = obj.description;

  // Report attribution line
  const noteEl = document.getElementById('panel-report-note');
  if (noteEl) {
    if (obj.sources?.length) {
      const orgs = [...new Set(obj.sources.map(s => s.org).filter(Boolean))];
      const years = [...new Set(obj.sources.map(s => s.year).filter(Boolean))].sort();
      const yearStr = years.length > 1 ? `${years[0]}–${years[years.length-1]}` : years[0];
      const orgStr = orgs.slice(0,3).join(', ') + (orgs.length > 3 ? ` +${orgs.length-3} more` : '');
      noteEl.textContent = `Extracted from ${orgStr}${yearStr ? ' · ' + yearStr : ''}`;
      noteEl.style.display = 'block';
    } else {
      noteEl.style.display = 'none';
    }
  }

  const dying    = document.getElementById('dying-notice-container');
  const recency  = document.getElementById('panel-recency-container');
  const ecology  = document.getElementById('panel-ecology-container');
  const sources  = document.getElementById('panel-sources-container');
  const conns    = document.getElementById('panel-connections-container');
  const scenarios = document.getElementById('panel-scenarios-container');
  [dying, recency, ecology, sources, conns, scenarios].forEach(el => { el.innerHTML = ''; });

  // Signal-specific
  if (type === 'signal') {
    const age = CURRENT_YEAR - obj.lastSeen;

    if (age >= DYING_AGE) {
      dying.innerHTML = `<div class="dying-notice">◌ Last cited ${obj.lastSeen} — fading from the signal field</div>`;
    }

    const pct   = Math.max(5, Math.min(100,
      ((obj.lastSeen - (CURRENT_YEAR - 6)) / 6) * 100
    ));
    const color = age >= DYING_AGE ? '#ff7a3c' : age === 1 ? '#f5c842' : '#b0c8ff';
    recency.innerHTML = `
      <div class="panel-section-label">Signal Recency</div>
      <div id="panel-recency" style="margin-bottom:20px;">
        <span class="recency-label">${obj.firstSeen}</span>
        <div class="recency-bar">
          <div class="recency-fill" style="width:${pct}%;background:${color};"></div>
        </div>
        <span class="recency-label">${obj.lastSeen}</span>
      </div>`;

    // Merged signal notice
    if (obj.mergeCount > 1) {
      dying.innerHTML += `<div style="font-size:11px;color:rgba(180,210,255,0.65);letter-spacing:0.06em;margin-bottom:16px;display:flex;align-items:center;gap:8px;">
        <span style="font-size:13px;">◈</span> Confirmed by ${obj.mergeCount} independent reports
      </div>`;
    }

    if (obj.connections?.length) {
      const linked = cosmos.trends.filter(t => obj.connections.includes(t.id));
      conns.innerHTML = `
        <div class="panel-section-label">Connected Trends</div>
        <div style="margin-bottom:20px;">
          ${linked.map(t => {
            const pc = PLANET_COLORS[t.id];
            const hex = pc ? '#' + pc.getHexString() : '#f5c842';
            return `<span class="connection-tag" style="border-color:${hex}44;color:${hex}cc;">◉ ${t.name}</span>`;
          }).join('')}
        </div>`;
    }

    // Drivers
    const DRIVER_META = {
      'technological-acceleration':       { label: 'Technological Acceleration', color: '#a78bfa' },
      'demographic-shift':                { label: 'Demographic Shift',          color: '#fb923c' },
      'geopolitical-fragmentation':       { label: 'Geopolitical Fragmentation', color: '#f87171' },
      'resource-environmental-pressure':  { label: 'Resource & Environmental Pressure', color: '#34d399' },
      'economic-realignment':             { label: 'Economic Realignment',       color: '#f5c842' },
      'cultural-reorientation':           { label: 'Cultural Reorientation',     color: '#ff85c2' },
      'governance-regulatory-change':     { label: 'Governance & Regulatory Change', color: '#7eb8f7' },
    };
    if (obj.drivers?.length) {
      ecology.innerHTML += `
        <div class="panel-section-label" style="margin-bottom:8px;">Underlying Driver</div>
        <div style="margin-bottom:20px;">
          ${obj.drivers.map(d => {
            const dm = DRIVER_META[d] || { label: d, color: '#888' };
            return `<span class="driver-tag" style="border-color:${dm.color}44;color:${dm.color};">${dm.label}</span>`;
          }).join('')}
        </div>`;
    }

    // Tensions
    if (obj.tensions?.length) {
      const sigMap = Object.fromEntries(cosmos.signals.map(s => [s.id, s]));
      ecology.innerHTML += `
        <div class="panel-section-label" style="margin-bottom:8px;">In Tension With</div>
        <div style="margin-bottom:20px;">
          ${obj.tensions.map(t => {
            const other = sigMap[t.signal];
            if (!other) return '';
            return `
              <div class="tension-item">
                <span class="tension-arrow">↔</span>
                <div class="tension-text">
                  <div class="tension-partner">${other.name}</div>
                  <div class="tension-label">${t.label}</div>
                </div>
              </div>`;
          }).join('')}
        </div>`;
    }
  }

  // Trend-specific
  if (type === 'trend') {
    // Convergence
    if (obj.convergenceScore !== undefined) {
      const conv  = obj.convergenceScore;
      const label = obj.convergenceLabel || '';
      const CONV_COLORS = { 'Universal': '#f5c842', 'Cross-sector': '#88ffaa', 'Emerging': '#7eb8f7', 'Niche': '#aaa' };
      const convColor = CONV_COLORS[label] || '#aaa';
      const ORG_TYPE_COLORS = {
        'Consultancy': '#7eb8f7', 'Financial': '#f5c842', 'Agency': '#ff85c2',
        'Research': '#88ffaa',   'Tech': '#a78bfa',       'Industry': '#fb923c',
        'Government': '#94a3b8', 'UN & IGO': '#34d399',   'Media': '#f87171',
      };
      const breakdown = obj.orgTypeBreakdown || {};
      const chips = Object.entries(breakdown)
        .sort((a, b) => b[1] - a[1])
        .map(([type, count]) => {
          const c = ORG_TYPE_COLORS[type] || '#aaa';
          return `<span class="org-type-chip" style="border-color:${c}44;color:${c};background:${c}11;">${type} <span style="opacity:0.6">${count}</span></span>`;
        }).join('');

      ecology.innerHTML = `
        <div style="margin-bottom:20px;">
          <div class="panel-section-label" style="margin-bottom:8px;">
            Cross-sector Convergence
            <span class="convergence-badge" style="border:1px solid ${convColor}55;color:${convColor};background:${convColor}11;">${label}</span>
          </div>
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
            <div style="flex:1;height:3px;background:rgba(255,255,255,0.07);border-radius:2px;overflow:hidden;">
              <div style="width:${Math.round(conv*100)}%;height:100%;background:${convColor};border-radius:2px;"></div>
            </div>
            <span style="font-size:10px;color:rgba(232,228,217,0.35);letter-spacing:0.08em;">${Math.round(conv*100)}%</span>
          </div>
          <div class="org-breakdown">${chips}</div>
        </div>`;
    }

    if (obj.signals?.length) {
      const sigs = cosmos.signals.filter(s => obj.signals.includes(s.id));
      conns.innerHTML = `
        <div class="panel-section-label">Signals (${sigs.length})</div>
        <div style="margin-bottom:20px;">
          ${sigs.map(s => {
            const a = CURRENT_YEAR - s.lastSeen;
            const c = a >= DYING_AGE ? '#ff7a3c' : a === 1 ? '#f5c842' : '#b0c8ff';
            return `<span class="connection-tag" style="border-color:${c}33;color:${c}cc;">★ ${s.name}</span>`;
          }).join('')}
        </div>`;
    }

    const scs = cosmos.scenarios.filter(s => s.trend === obj.id);
    if (scs.length) {
      scenarios.innerHTML = `
        <div class="panel-section-label">Scenarios</div>
        ${scs.map(s => `
          <div style="border:1px solid rgba(136,255,170,0.1);border-radius:6px;padding:14px;margin-bottom:10px;">
            <div style="font-size:13px;color:rgba(136,255,170,0.75);margin-bottom:6px;">⬡ ${s.name}</div>
            <div style="font-size:12px;line-height:1.7;color:rgba(232,228,217,0.5);">${s.description}</div>
          </div>`).join('')}`;
    }
  }

  // Scenario-specific
  if (type === 'scenario') {
    const parent = cosmos.trends.find(t => t.id === obj.trend);
    if (parent) {
      conns.innerHTML = `
        <div class="panel-section-label">Parent Trend</div>
        <div style="margin-bottom:20px;">
          <span class="connection-tag" style="border-color:rgba(245,200,66,0.25);color:rgba(245,200,66,0.7);">◉ ${parent.name}</span>
        </div>`;
    }
  }

  // Sources (all types)
  if (obj.sources?.length) {
    const ORG_TYPE_COLORS = {
      'Consultancy':  '#7eb8f7',
      'Financial':    '#f5c842',
      'Agency':       '#ff85c2',
      'Research':     '#88ffaa',
      'Tech':         '#a78bfa',
      'Industry':     '#fb923c',
      'Government':   '#94a3b8',
      'UN & IGO':     '#34d399',
      'Media':        '#f87171',
    };
    const ORG_BIAS = {
      'Consultancy': 'Solution-forward; identifies problems primarily as engagement opportunities. Tends to over-index on enterprise and B2B contexts.',
      'Financial':   'Frames everything through returns and risk management. Tends to smooth political disruption into "macro headwinds" and underweight systemic risk.',
      'Agency':      'Amplifies cultural novelty because novelty is their product. Tends toward optimistic consumer narratives and brand-centric framing.',
      'Research':    'Curatorial and pattern-matching. Can create self-fulfilling trend cycles; watch for recency bias and sampling toward English-language sources.',
      'Tech':        'Often self-serving toward platform or tool adoption. Frames adoption curves as destiny and underweights labor, regulatory, and equity concerns.',
      'Industry':    'Reporting from inside the sector. Strong domain depth; structural bias toward growth narratives that serve their own business case.',
      'Government':  'Risk-focused and compliance-driven. Slower-moving; tends to lag private-sector signals and under-represent commercial opportunity.',
      'UN & IGO':    'Equity and development lens. Highlights systemic failures the private sector underweights. Can be aspirational rather than predictive.',
      'Media':       'Audience-driven framing; tends toward the newsworthy, alarming, or culturally resonant. Watch for recency and novelty bias.',
    };

    sources.innerHTML = `
      <div class="panel-section-label">Sources (${obj.sources.length})</div>
      <div id="panel-sources">
        ${obj.sources.map(s => {
          const typeColor = ORG_TYPE_COLORS[s.orgType] || '#aaa';
          const bias      = ORG_BIAS[s.orgType] || '';
          // Clean up raw filename for display
          const reportDisplay = s.report
            .replace(/_CAIG$/i, '')   // strip batch suffix
            .replace(/_/g, ' ')       // underscores → spaces
            .trim();
          // Use stored URL if present, otherwise generate a Google search for the report
          const reportHref = s.url
            ? s.url
            : `https://www.google.com/search?q=${encodeURIComponent(`"${reportDisplay}" ${s.org || ''} report`)}`;

          return `
          <div class="source-item" style="flex-direction:column;align-items:flex-start;gap:6px;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;width:100%;gap:10px;">
              <div style="flex:1;min-width:0;">
                ${s.org ? `<div style="font-size:11px;color:rgba(232,228,217,0.75);margin-bottom:2px;">${s.org}</div>` : ''}
                <a href="${reportHref}" target="_blank" rel="noopener noreferrer"
                   style="font-size:10px;color:rgba(160,195,255,0.55);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block;text-decoration:none;transition:color 0.2s;"
                   onmouseover="this.style.color='rgba(160,195,255,0.9)'" onmouseout="this.style.color='rgba(160,195,255,0.55)'"
                   title="${s.url ? 'Open source report' : 'Search for this report'}"
                >${reportDisplay}</a>
              </div>
              <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">
                ${s.orgType ? `<span style="font-size:9px;letter-spacing:0.08em;text-transform:uppercase;color:${typeColor};opacity:0.85;border:1px solid ${typeColor}44;padding:2px 7px;border-radius:10px;">${s.orgType}</span>` : ''}
                <span class="source-year">${s.year}</span>
                <a class="source-link" href="${reportHref}" target="_blank" rel="noopener noreferrer" title="${s.url ? 'Open report' : 'Search for report'}">↗</a>
              </div>
            </div>
            ${bias ? `<div style="font-size:10px;color:rgba(232,228,217,0.28);line-height:1.55;font-style:italic;padding-left:1px;">${bias}</div>` : ''}
          </div>`;
        }).join('')}
      </div>`;
  }

  // ── Excerpt (appears just below description) ──
  const excerptEl = document.getElementById('panel-excerpt-container');
  if (excerptEl) {
    excerptEl.innerHTML = (type === 'signal' && obj.excerpt)
      ? `<blockquote class="panel-excerpt">“${obj.excerpt}”</blockquote>`
      : '';
  }

  // ── URL permalink ──
  if (type === 'signal') history.replaceState(null, '', `?s=${obj.id}`);
  else if (type === 'trend') history.replaceState(null, '', `?t=${obj.id}`);

  // ── Share button handler ──
  const shareBtn = document.getElementById('panel-share-btn');
  if (shareBtn) {
    shareBtn.onclick = () => {
      navigator.clipboard.writeText(location.href).catch(() => {});
      const toast = document.getElementById('copy-toast');
      if (toast) { toast.classList.add('show'); setTimeout(() => toast.classList.remove('show'), 2200); }
    };
  }

  document.getElementById('panel').classList.add('open');
}

// ── Seeded RNG (mulberry32) ─────────────────────────────────────────────────
function seededRandom(seed) {
  let s = seed;
  return () => {
    s |= 0; s = s + 0x6D2B79F5 | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = t + Math.imul(t ^ (t >>> 7), 61 | t) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

init().catch(console.error);
