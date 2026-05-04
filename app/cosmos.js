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
  const data = await fetch('../data/cosmos.json').then(r => r.json());

  // Scene / renderer
  const scene    = new THREE.Scene();
  const camera   = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.1, 2000);
  camera.position.set(0, 30, 150);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(innerWidth, innerHeight);
  renderer.setClearColor(0x000008);
  document.getElementById('canvas-container').appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping    = true;
  controls.dampingFactor    = 0.06;
  controls.minDistance      = 25;
  controls.maxDistance      = 450;
  controls.autoRotate       = true;
  controls.autoRotateSpeed  = 0.12;

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

  // ── Interactables ──
  const interactable = [];
  const objMeta      = new Map(); // mesh → { type, data }

  // ── Trend planets ──
  const dyingSignalMeshes = []; // for pulsing animation

  data.trends.forEach(trend => {
    const pos      = trendPos[trend.id];
    const size     = 2.8 + trend.mass * 1.8;
    const pCol     = (PLANET_COLORS[trend.id] ?? new THREE.Color(0.96, 0.78, 0.26)).clone();

    const geo  = new THREE.SphereGeometry(size, 40, 40);
    const mat  = new THREE.MeshStandardMaterial({
      color:             pCol.clone().multiplyScalar(0.55),
      emissive:          pCol.clone(),
      emissiveIntensity: 0.30,
      roughness:         0.50,
      metalness:         0.20,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(pos);
    scene.add(mesh);
    interactable.push(mesh);
    objMeta.set(mesh, { type: 'trend', data: trend });

    // Atmosphere ring — tinted to planet colour
    const ringGeo = new THREE.RingGeometry(size + 0.4, size + 1.6, 64);
    const ringMat = new THREE.MeshBasicMaterial({
      color:      pCol.clone(),
      side:       THREE.DoubleSide,
      transparent: true,
      opacity:    0.10,
      depthWrite: false,
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2 + (Math.random() - 0.5) * 0.6;
    ring.position.copy(pos);
    scene.add(ring);

    addGlow(scene, pos, pCol, size * 5.5, 0.22);

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

    const geo  = new THREE.SphereGeometry(size, 10, 10);
    const mat  = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: op });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(pos);
    scene.add(mesh);
    interactable.push(mesh);
    objMeta.set(mesh, { type: 'signal', data: sig });

    const glowOp   = age >= DYING_AGE ? 0.12 : 0.22 + sig.strength * 0.2;
    const glowSize = age >= DYING_AGE ? size * 5 : size * 6 + sig.strength * 3;
    addGlow(scene, pos, col, glowSize, glowOp);

    if (age >= DYING_AGE) {
      dyingSignalMeshes.push({ mesh, baseOp: op });
    }
  });

  // ── Raycaster / hover ──
  const raycaster = new THREE.Raycaster();
  raycaster.params.Mesh.threshold = 0.5;
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

  window.addEventListener('click', () => {
    if (hoveredMesh && objMeta.has(hoveredMesh)) {
      openPanel(objMeta.get(hoveredMesh), data);
      controls.autoRotate = false;
    }
  });

  document.getElementById('panel-close').addEventListener('click', () => {
    document.getElementById('panel').classList.remove('open');
    controls.autoRotate = true;
  });

  // ── Filters ──
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const f = btn.dataset.filter;
      lineGroup.visible = (f === 'all' || f === 'connections');
      interactable.forEach(m => {
        const info = objMeta.get(m);
        if (!info) return;
        m.visible = f === 'all' || f === 'connections'
          || (f === 'signals' && info.type === 'signal')
          || (f === 'trends'  && (info.type === 'trend' || info.type === 'scenario'));
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
  const clock = new THREE.Clock();

  function animate() {
    requestAnimationFrame(animate);
    const t = clock.getElapsedTime();

    starMat.uniforms.time.value = t;

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
}

// ── Panel ───────────────────────────────────────────────────────────────────
function openPanel({ type, data: obj }, cosmos) {
  document.getElementById('panel-type').textContent =
    type === 'signal' ? 'Weak Signal' : type === 'trend' ? 'Trend' : 'Scenario';
  document.getElementById('panel-title').textContent = obj.name;
  document.getElementById('panel-desc').textContent  = obj.description;

  const dying     = document.getElementById('dying-notice-container');
  const recency   = document.getElementById('panel-recency-container');
  const sources   = document.getElementById('panel-sources-container');
  const conns     = document.getElementById('panel-connections-container');
  const scenarios = document.getElementById('panel-scenarios-container');
  [dying, recency, sources, conns, scenarios].forEach(el => { el.innerHTML = ''; });

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
  }

  // Trend-specific
  if (type === 'trend') {
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
    sources.innerHTML = `
      <div class="panel-section-label">Sources</div>
      <div id="panel-sources">
        ${obj.sources.map(s => `
          <div class="source-item">
            <span class="source-name">${s.report}</span>
            <span class="source-year">${s.year}</span>
            ${s.url ? `<a class="source-link" href="${s.url}" target="_blank">↗</a>` : ''}
          </div>`).join('')}
      </div>`;
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
