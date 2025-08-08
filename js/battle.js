// Generate and Animate Starfield //
 const canvas = document.getElementById('starfield');
  const ctx = canvas.getContext('2d');

  let width, height, stars = [], layers = [], time = 0;
  let lastStarfieldTime = performance.now();

  function hexToRGBA(hex, alpha) {
    const bigint = parseInt(hex.replace("#", ""), 16);
    const r = (bigint >> 16) & 255;
    const g = (bigint >> 8) & 255;
    const b = bigint & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  function generateLayers() {
    return [
      { count: 50, zRange: [width * 0.95, width], color: '#ffffff', blur: true },
      { count: 75, zRange: [width * 0.7, width], color: '#88ccff' },
      { count: 100, zRange: [width * 0.4, width * 0.7], color: '#ffffff' },
      { count: 125, zRange: [width * 0.1, width * 0.4], color: '#ff99cc' }
    ];
  }

  function resizeCanvas() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    layers = generateLayers();
    initStars();
  }

  function initStars() {
    stars = [];
    layers.forEach(layer => {
      for (let i = 0; i < layer.count; i++) {
        stars.push({
          x: Math.random() * width,
          y: Math.random() * height,
          z: Math.random() * (layer.zRange[1] - layer.zRange[0]) + layer.zRange[0],
          o: Math.random(),
          color: layer.color,
          layer: layer
        });
      }
    });
  }

function animateStarfield(now) {
  if (typeof now !== 'number') now = performance.now();
  const delta = (now - lastStarfieldTime) / 1000; // seconds
  lastStarfieldTime = now;

  // You can tweak these speeds to taste:
  const STAR_SPEED = 80;   // units per second (was 1 per frame, now 80 per sec for similar speed at 60fps)
  const DRIFT_SPEED_X = 0.001;
  const DRIFT_SPEED_Y = 0.0012;
  const DRIFT_AMOUNT = 0.01;

  const bgColor = getComputedStyle(document.body).getPropertyValue('--starfield-bg').trim();
  ctx.fillStyle = bgColor;
  ctx.fillRect(0, 0, width, height);

  // Use time as "seconds elapsed" instead of a frame count
  time += delta;

  const driftX = Math.sin(time * DRIFT_SPEED_X) * DRIFT_AMOUNT * width;
  const driftY = Math.cos(time * DRIFT_SPEED_Y) * DRIFT_AMOUNT * height;

  stars.forEach(star => {
    star.z -= STAR_SPEED * delta;
    if (star.z <= 0) {
      const zRange = star.layer.zRange;
      star.z = Math.random() * (zRange[1] - zRange[0]) + zRange[0];
      star.x = Math.random() * width;
      star.y = Math.random() * height;
    }

    const k = 128.0 / star.z;
    const centerX = width / 2 + Math.sin(time * DRIFT_SPEED_X) * width * 0.1;
    const centerY = height / 2 + Math.cos(time * 0.0013) * height * 0.1;
    const px = (star.x - centerX) * k + centerX;
    const py = (star.y - centerY) * k + centerY;

    const size = (1 - star.z / width) * 2;

    star.o += (Math.random() - 0.5) * 0.05;
    star.o = Math.max(0.1, Math.min(1, star.o));

    if (star.layer.blur) {
      ctx.shadowBlur = 5;
      ctx.shadowColor = star.color;
    } else {
      ctx.shadowBlur = 0;
    }

    ctx.beginPath();
    ctx.arc(px, py, size, 0, Math.PI * 2);
    ctx.fillStyle = hexToRGBA(star.color, star.o);
    ctx.fill();
  });

  requestAnimationFrame(animateStarfield);
}

  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();
  animateStarfield();

  // End Starfield //


  // This generates and animates the battle on top of the starfield //
   // Setup ship canvas and context
    const battleCanvas = document.getElementById('battleCanvas');
    const battleCtx = battleCanvas.getContext('2d');
    battleCtx.imageSmoothingEnabled = false;

    let battleWidth = battleCanvas.width = window.innerWidth;
    let battleHeight = battleCanvas.height = window.innerHeight;
    let lastBattleTime = performance.now();


    window.addEventListener('resize', () => {
      battleWidth = battleCanvas.width = window.innerWidth;
      battleHeight = battleCanvas.height = window.innerHeight;
      battleCtx.imageSmoothingEnabled = false;
    });

    // Ship sprite (custom shape)
    const sprite = [
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  [0,0,1,1,1,1,0,0,0,0,0,0,0,0,0],
  [0,0,0,1,1,0,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,1,1,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0],
  [0,0,1,1,1,1,1,1,1,1,1,1,1,0,0],
  [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0],
  [0,0,0,0,1,1,0,0,0,0,0,0,0,0,0],
  [0,0,0,1,1,0,0,0,0,0,0,0,0,0,0],
  [0,0,1,1,1,1,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
];

    const pixelSize = 2;
    const shipWidth = sprite[0].length * pixelSize;
    const shipHeight = sprite.length * pixelSize;

    const alienSprite = {
      frames: [
        [ // Frame 0
    ['#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#000000','#60c494','#60c494','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#000000','#60c494','#60c494','#60c494','#000000','#000000','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#60c494','#60c494','#000000','#60c494','#60c494','#68a22a','#68a22a','#68a22a','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#60c494','#60c494','#60c494','#000000','#60c494','#68a22a','#000000','#000000','#68a22a','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#60c494','#60c494','#68a22a','#60c494','#b9712f','#b9712f','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#68a22a','#68a22a','#68a22a','#68a22a','#b9712f','#b9712f','#68a22a','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#68a22a','#68a22a','#68a22a','#68a22a','#68a22a','#68a22a','#68a22a','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#68a22a','#68a22a','#68a22a','#68a22a','#b9712f','#b9712f','#68a22a','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#60c494','#60c494','#68a22a','#60c494','#b9712f','#b9712f','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#60c494','#60c494','#60c494','#000000','#60c494','#68a22a','#000000','#000000','#68a22a','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#60c494','#60c494','#000000','#60c494','#60c494','#68a22a','#68a22a','#68a22a','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#000000','#60c494','#60c494','#60c494','#000000','#000000','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#000000','#60c494','#60c494','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000']
  ],
  [ // Frame 1
    ['#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#000000','#60c494','#60c494','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#000000','#60c494','#60c494','#60c494','#68a22a','#68a22a','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#60c494','#60c494','#000000','#60c494','#60c494','#68a22a','#000000','#68a22a','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#60c494','#60c494','#68a22a','#60c494','#b9712f','#b9712f','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#68a22a','#68a22a','#68a22a','#68a22a','#b9712f','#b9712f','#68a22a','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#68a22a','#68a22a','#68a22a','#68a22a','#68a22a','#68a22a','#68a22a','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#68a22a','#68a22a','#68a22a','#68a22a','#b9712f','#b9712f','#68a22a','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#60c494','#60c494','#68a22a','#60c494','#b9712f','#b9712f','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#60c494','#60c494','#000000','#60c494','#60c494','#68a22a','#000000','#68a22a','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#000000','#60c494','#60c494','#60c494','#68a22a','#68a22a','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#000000','#60c494','#60c494','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000'],
    ['#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000','#000000']
  ]
    ],
  width: 15,
  height: 15,
  scale: 1,
  animationSpeed: 30  // how many frames to wait between switching
    };

const alien = {
  x: 0,
  y: 0,
  active: false,
  frameIndex: 0,
  frameTicker: 0,
  active: false
};

let lastAlienScale = -1;
let lastAlienFrameIndex = -1;

let bullets = [];
let bulletTimer = 0;
let nextBulletInterval = 20;

const shipCanvas = document.createElement('canvas');
const shipCtx = shipCanvas.getContext('2d');

shipCanvas.width = shipWidth;
shipCanvas.height = shipHeight;
shipCtx.imageSmoothingEnabled = false;

  const ship = {
  x: 0,
  y: 0,
  vx: 0,
  vy: 0,
  active: false,
  angle: 0,
  timer: 0,
  scale: 1,
  mode: 'normal' // can be 'normal', 'broken', or 'combat'
};

function renderShipToOffscreen() {
  shipCtx.clearRect(0, 0, shipWidth, shipHeight);
  for (let row = 0; row < sprite.length; row++) {
    for (let col = 0; col < sprite[row].length; col++) {
      if (sprite[row][col]) {
        shipCtx.fillStyle = 'white';
        shipCtx.fillRect(col * pixelSize, row * pixelSize, pixelSize, pixelSize);
      }
    }
  }
}
renderShipToOffscreen();

const alienCanvas = document.createElement('canvas');
const alienCtx = alienCanvas.getContext('2d');
alienCtx.imageSmoothingEnabled = false;

function renderAlienToOffscreen() {
  alienCtx.clearRect(0, 0, alienCanvas.width, alienCanvas.height);
  const scale = alien.scale || 1; // fallback to 1 if undefined
  const px = scale * pixelSize; // use same base pixelSize as ship
  const frame = alienSprite.frames[alien.frameIndex];

  // Resize canvas to match scaled sprite size
  alienCanvas.width = alienSprite.width * px;
  alienCanvas.height = alienSprite.height * px;

  alienCtx.clearRect(0, 0, alienCanvas.width, alienCanvas.height);

  for (let r = 0; r < frame.length; r++) {
    for (let c = 0; c < frame[r].length; c++) {
      const color = frame[r][c];
      if (color !== '#000000') {
        alienCtx.fillStyle = color;
        alienCtx.fillRect(c * px, r * px, px, px);
      }
    }
  }
}
    let particles = [];

function drawShip(x, y) {
  battleCtx.save();

  // Round position and scale to avoid subpixels
  const scale = ship.scale;
  const cx = Math.round(x + (shipWidth * scale) / 2);
  const cy = Math.round(y + (shipHeight * scale) / 2);

  battleCtx.setTransform(1, 0, 0, 1, 0, 0); // Reset transform
  battleCtx.imageSmoothingEnabled = false; // Always right before drawing!

  battleCtx.translate(cx, cy);
  battleCtx.rotate(ship.angle * Math.PI / 180);
  battleCtx.scale(scale, scale);

  battleCtx.drawImage(
    shipCanvas,
    -Math.round(shipWidth / 2),
    -Math.round(shipHeight / 2)
  );

  battleCtx.restore();
}

   function addThrust(x, y) {
  const angleRad = ship.angle * Math.PI / 180;
  const scale = ship.scale;

  // Rear center of ship (scaled)
  const rearOffsetX = -shipWidth * scale / 2;
  const rearOffsetY = 0;

  // Rotate rear point
  const rotatedX = Math.cos(angleRad) * rearOffsetX - Math.sin(angleRad) * rearOffsetY;
  const rotatedY = Math.sin(angleRad) * rearOffsetX + Math.cos(angleRad) * rearOffsetY;

  // Translate to screen coords (scaled)
  const cx = x + shipWidth * scale / 2;
  const cy = y + shipHeight * scale / 2;
  const thrustX = cx + rotatedX;
  const thrustY = cy + rotatedY;

  for (let i = 0; i < 4; i++) {
    const baseAngle = angleRad + Math.PI; // Directly opposite ship
    const spread = (Math.random() - 0.5) * 0.6; // Wider cone
    const thrustAngle = baseAngle + spread;
    const speed = 1.0 + Math.random() * 0.5;

    particles.push({
      x: thrustX,
      y: thrustY,
      vx: Math.cos(thrustAngle) * speed,
      vy: Math.sin(thrustAngle) * speed,
      radius: (3 + Math.random()) * scale,
      alpha: 1,
    });
  }
}

function drawAlien() {
  if (
    alien.active &&
    ship.active &&
    typeof alien.x === 'number' && !isNaN(alien.x) &&
    typeof alien.y === 'number' && !isNaN(alien.y)
  ) {
    battleCtx.save();
    const scale = alien.scale || 1;
    const alienW = alienSprite.width * scale;
    const alienH = alienSprite.height * scale;
    const cx = alien.x + alienW / 2;
    const cy = alien.y + alienH / 2;
    battleCtx.translate(cx, cy);
    battleCtx.rotate(alien.angle * Math.PI / 180);

    battleCtx.drawImage(
      alienCanvas,
      -alienW / 2,
      -alienH / 2,
      alienW,
      alienH
    );
    battleCtx.restore();
  }
}

function drawParticles() {
  particles.forEach(p => {
    const gradient = battleCtx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius * 1.8);
    gradient.addColorStop(0, `rgba(180, 220, 255, ${p.alpha})`); // bright center
    gradient.addColorStop(1, `rgba(0, 100, 255, 0)`);             // fade to deep blue

    battleCtx.fillStyle = gradient;
    battleCtx.beginPath();
    battleCtx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
    battleCtx.fill();
  });
}

function updateParticles(delta) {
  particles.forEach(p => {
    p.x += p.vx * delta;
    p.y += p.vy * delta;
    p.radius *= Math.pow(0.9, delta * 60); // decay matches old logic at 60fps
    p.alpha -= 0.1 * delta * 60; // fade speed matches old logic at 60fps
  });
  particles = particles.filter(p => p.alpha > 0);
}

function fireBullet() {

  if (!ship.active || ship.mode !== "combat") return;

  const scale = ship.scale;
  const angleRad = ship.angle * Math.PI / 180;

  // GUN POSITIONS (sprite col, row)
  const guns = [
    { col: 6, row: 4 },   // Left gun (adjust as needed)
    { col: 6, row: 11 }   // Right gun (adjust as needed)
  ];

  // Loop for both guns
  guns.forEach(gun => {
    // Sprite center (for rotation)
    const centerCol = sprite[0].length / 2;
    const centerRow = sprite.length / 2;

    // Gun position relative to sprite center
    const relX = (gun.col - centerCol) * pixelSize * scale;
    const relY = (gun.row - centerRow) * pixelSize * scale;

    // Rotate gun position
    const rotatedX = Math.cos(angleRad) * relX - Math.sin(angleRad) * relY;
    const rotatedY = Math.sin(angleRad) * relX + Math.cos(angleRad) * relY;

    // Ship center in screen coordinates
    const cx = ship.x + (shipWidth * scale) / 2;
    const cy = ship.y + (shipHeight * scale) / 2;

    // Final gun position on screen
    const bulletX = cx + rotatedX;
    const bulletY = cy + rotatedY;

    // Bullet speed (in direction of ship)
    const bulletSpeed = 1000;

    bullets.push({
      x: bulletX,
      y: bulletY,
     vx: Math.cos(angleRad) * bulletSpeed + ship.vx,
vy: Math.sin(angleRad) * bulletSpeed + ship.vy,

      radius: 1 * scale, // Small bullets
      life: 240
    });
  });
}

function maybeActivateShip() {

  if (!ship.active) {
    ship.active = true;
    // (choose a mode)
    const rand = Math.random();
    if (rand < 0.1) {
    ship.mode = 'broken';
    } else if (rand < 0.4) {
    ship.mode = 'combat';
    } else {
    ship.mode = 'normal';
    }

    ship.scale = Math.floor(Math.random() * 4) + 1;

    // Setup alien for combat mode
    if (ship.mode === 'combat') {
      alien.scale = ship.scale;
      alien.frameIndex = 0;
      alien.frameTicker = 0;
      renderAlienToOffscreen();
      alien.active = true;
    } else {
      alien.active = false;
      alien.frameIndex = 0;
      alienCtx.clearRect(0, 0, alienCanvas.width, alienCanvas.height);
      alien.x = -9999;
      alien.y = -9999;
    }

    const w = shipWidth * ship.scale;
    const h = shipHeight * ship.scale;
    const margin = 100; // How far off-screen to start

// --- TRUE RANDOMIZED EDGE SPAWN ---
// Pick an edge: 0=top, 1=right, 2=bottom, 3=left
const edge = Math.floor(Math.random() * 4);
let spawnX, spawnY;

if (edge === 0) { // Top
  spawnX = Math.random() * battleWidth;
  spawnY = -margin; // ship is just above the screen
} else if (edge === 1) { // Right
  spawnX = battleWidth + margin; // just right of screen
  spawnY = Math.random() * battleHeight;
} else if (edge === 2) { // Bottom
  spawnX = Math.random() * battleWidth;
  spawnY = battleHeight + margin; // just below the screen
} else { // Left
  spawnX = -margin; // just left of screen
  spawnY = Math.random() * battleHeight;
}

ship.x = spawnX;
ship.y = spawnY;

    // --- Target zone near center (tweak spread as needed) ---
    const centerX = battleWidth / 2;
    const centerY = battleHeight / 2;
    const spread = Math.min(battleWidth, battleHeight) * 0.25;
    const targetX = centerX + (Math.random() - 0.5) * spread;
    const targetY = centerY + (Math.random() - 0.5) * spread;

    // --- Calculate velocity toward target ---
    const dx = targetX - (ship.x + w / 2);
    const dy = targetY - (ship.y + h / 2);
    const dist = Math.sqrt(dx * dx + dy * dy);

    const baseSpeed = ship.mode === 'broken'
  ? (0.8 + Math.random() * 0.8) * 60
  : (2 + Math.random() * 6) * 60;

    ship.vx = (dx / dist) * baseSpeed;
    ship.vy = (dy / dist) * baseSpeed;

    ship.angle = Math.atan2(ship.vy, ship.vx) * 180 / Math.PI;
    ship.timer = 0;
  }
}

function battleAnimate(now) {
  if (typeof now !== 'number') now = performance.now();
  let delta = (now - lastBattleTime) / 1000; // seconds since last frame
  lastBattleTime = now;

  battleCtx.clearRect(0, 0, battleWidth, battleHeight);

  if (!ship.active && Math.random() < 0.002) {
    maybeActivateShip();
  }

  // --- EARLY SHIP INACTIVE CHECK ---
  if (!ship.active) {
    alien.active = false;
    alien.x = -9999;
    alien.y = -9999;
    alien.frameIndex = 0;
    alienCtx.clearRect(0, 0, alienCanvas.width, alienCanvas.height);

    drawParticles();
    updateParticles(delta);
    requestAnimationFrame(battleAnimate);
    return;
  }

  // --- EARLY DEACTIVATION CHECK ---
  const buffer = 100;
  const timeLimit = ship.mode === 'broken'
  ? 50.0   // 3000/60
  : ship.mode === 'combat'
    ? 25.0  // 1500/60
    : 20.0; // 1200/60

  if (
    ship.x < -buffer || ship.x > battleWidth + buffer ||
    ship.y < -buffer || ship.y > battleHeight + buffer ||
    ship.timer > timeLimit
  ) {
    ship.active = false;
    alien.active = false;
    alien.x = -9999;
    alien.y = -9999;
    alien.frameIndex = 0;
    alienCtx.clearRect(0, 0, alienCanvas.width, alienCanvas.height);
  }

  // --- EARLY RETURN IF SHIP IS INACTIVE ---
  if (!ship.active) {
    drawParticles();
    updateParticles(delta);
    requestAnimationFrame(battleAnimate);
    return;
  }

  // --- SHIP AND ALIEN MOTION ---
  ship.x += ship.vx * delta;
  ship.y += ship.vy * delta;
  ship.timer += delta;

  if (ship.mode === 'combat') {
    bulletTimer += delta * 60; // keeps previous logic compatible (frame rate scaling)
    if (bulletTimer >= nextBulletInterval) {
      fireBullet();
      bulletTimer = 0;
      nextBulletInterval = 5 + Math.floor(Math.random() * 50); // random between 12 and 28
    }

    const forwardOffset = 200;
    const angleRad = ship.angle * Math.PI / 180;

    alien.scale = ship.scale;

    const alienW = alienSprite.width * alien.scale;
    const alienH = alienSprite.height * alien.scale;

    const shipCenterX = ship.x + (shipWidth * ship.scale) / 2;
    const shipCenterY = ship.y + (shipHeight * ship.scale) / 2;

    // Alien's main position (in front of the ship)
    let alienX = shipCenterX + Math.cos(angleRad) * forwardOffset;
    let alienY = shipCenterY + Math.sin(angleRad) * forwardOffset;

    // --- BOBBING LOGIC ---
    const bobAmplitude = 50;
    const bobFrequency = 2.0;
    const bobOffset = Math.sin(ship.timer * bobFrequency) * bobAmplitude;
    const perpAngle = angleRad + Math.PI / 2;
    alienX += Math.cos(perpAngle) * bobOffset;
    alienY += Math.sin(perpAngle) * bobOffset;

    // Center the alien sprite on alienX/alienY
    alien.x = alienX - alienW / 2;
    alien.y = alienY - alienH / 2;

    alien.vx = ship.vx;
    alien.vy = ship.vy;
    alien.angle = ship.angle;

    if (
      alien.frameIndex !== lastAlienFrameIndex ||
      alien.scale !== lastAlienScale
    ) {
      renderAlienToOffscreen();
      lastAlienFrameIndex = alien.frameIndex;
      lastAlienScale = alien.scale;
    }

    // 👾 Animate alien sprite frames
    alien.frameTicker += delta * 60; // scale frameTicker as well
    if (alien.frameTicker >= alienSprite.animationSpeed) {
      alien.frameTicker = 0;
      alien.frameIndex = (alien.frameIndex + 1) % alienSprite.frames.length;
    }

    if (alien.active) {
      drawAlien();
    }
  }

  if (ship.mode !== 'broken') {
    addThrust(ship.x, ship.y);
  }

  bullets = bullets.filter(bullet => {
    bullet.x += bullet.vx * delta;
    bullet.y += bullet.vy * delta;
    bullet.life -= delta * 60; // old logic was in frames; scale for 60fps
    return (
     /*  bullet.x > 0 && bullet.x < battleWidth &&
      bullet.y > 0 && bullet.y < battleHeight && */
      bullet.life > 0
    );
  });

  bullets.forEach(bullet => {
    battleCtx.save();
    battleCtx.globalAlpha = 1.0;
    battleCtx.beginPath();
    battleCtx.arc(bullet.x, bullet.y, bullet.radius, 0, Math.PI * 2);
    battleCtx.fillStyle = '#FFFFFF';
    //battleCtx.shadowColor = '#6db6d8'; // comment out if you want to remove glow!
    //battleCtx.shadowBlur = 12; // comment out for no glow
    battleCtx.fill();
    battleCtx.restore();
  });

  drawParticles();
  updateParticles(delta);

  if (ship.mode === 'broken') {
    ship.angle += 0.5 * delta * 60; // matches original spin speed at 60fps
  }

  drawShip(ship.x, ship.y);

  requestAnimationFrame(battleAnimate);
}

battleAnimate();

// End Battle