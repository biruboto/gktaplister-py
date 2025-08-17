# battlefield_js_port.py
# Port of your HTML starfield + battle to Pygame, now with CRISP pixel-art rendering.
# - Nearest-neighbor scaling (pygame.transform.scale)
# - Quantized angles and rotation cache for sharp, stable rotations

import math, random, pygame

# ---------- helpers ----------
def clamp(v, lo, hi): return lo if v < lo else hi if v > hi else v
def hex_to_rgb(hexs: str):
    hexs = hexs.lstrip("#")
    return int(hexs[0:2], 16), int(hexs[2:4], 16), int(hexs[4:6], 16)

# ---------- STARFIELD (layers, drift, opacity jitter) ----------
class JSStarfield:
    def __init__(self, w, h, bg_color=(0,0,0)):
        self.w, self.h = w, h
        self.bg = bg_color
        self.time = 0.0
        self.layers = self._gen_layers()
        self.stars = self._init_stars()
        # Speeds/amounts taken from your JS:
        self.STAR_SPEED = 80.0        # px/sec
        self.DRIFT_SPEED_X = 0.001
        self.DRIFT_SPEED_Y = 0.0012
        self.DRIFT_AMOUNT  = 0.01

    def _gen_layers(self):
        w = self.w
        return [
            {"count":50,  "zmin":w*0.95, "zmax":w*1.0,  "color":hex_to_rgb("#ffffff"), "blur":True},
            {"count":75,  "zmin":w*0.7,  "zmax":w*1.0,  "color":hex_to_rgb("#88ccff"), "blur":False},
            {"count":100, "zmin":w*0.4,  "zmax":w*0.7,  "color":hex_to_rgb("#ffffff"), "blur":False},
            {"count":125, "zmin":w*0.1,  "zmax":w*0.4,  "color":hex_to_rgb("#ff99cc"), "blur":False},
        ]

    def _init_stars(self):
        stars = []
        for L in self.layers:
            for _ in range(L["count"]):
                z = random.random() * (L["zmax"] - L["zmin"]) + L["zmin"]
                stars.append({
                    "x": random.random() * self.w,
                    "y": random.random() * self.h,
                    "z": z,
                    "o": random.random(),   # opacity jitter 0..1 (clamped in update)
                    "col": L["color"],
                    "blur": L["blur"],
                    "layer": L,
                })
        return stars

    def resize(self, w, h):
        self.w, self.h = w, h
        self.layers = self._gen_layers()
        self.stars  = self._init_stars()

    def update(self, dt):
        self.time += dt
        for s in self.stars:
            s["z"] -= self.STAR_SPEED * dt
            if s["z"] <= 0:
                L = s["layer"]
                s["z"] = random.random() * (L["zmax"] - L["zmin"]) + L["zmin"]
                s["x"] = random.random() * self.w
                s["y"] = random.random() * self.h

            # opacity jitter towards [0.1, 1.0]
            s["o"] += (random.random() - 0.5) * 0.05
            s["o"] = clamp(s["o"], 0.1, 1.0)

    def draw(self, screen):
        screen.fill(self.bg)
        # drifting projection center
        centerX = self.w/2 + math.sin(self.time * self.DRIFT_SPEED_X) * self.w * 0.1
        centerY = self.h/2 + math.cos(self.time * 0.0013          ) * self.h * 0.1

        for s in self.stars:
            # perspective projection
            k  = 128.0 / s["z"]
            px = (s["x"] - centerX) * k + centerX
            py = (s["y"] - centerY) * k + centerY
            size = max(1, int((1.0 - s["z"]/self.w) * 2))

            r, g, b = s["col"]
            a = int(255 * s["o"])

            # shadowBlur approximation: faint halo for "blur" stars
            if s["blur"]:
                pygame.draw.circle(screen, (r, g, b, int(a * 0.4)), (int(px), int(py)), max(2, int(size*3)), 0)
            pygame.draw.circle(screen, (r, g, b, a), (int(px), int(py)), size, 0)

# ---------- BATTLE (ship/alien/bullets/exhaust) ----------
class JSBattle:
    def __init__(self, w, h):
        self.w, self.h = w, h

        # Ship sprite (15x15), 1 = white pixel
        self.pixel_size = 2
        self.sprite = [
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
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        ]
        self.ship_w = len(self.sprite[0]) * self.pixel_size
        self.ship_h = len(self.sprite)    * self.pixel_size

        # prerender ship to offscreen (white pixels)
        self.ship_base = pygame.Surface((self.ship_w, self.ship_h), pygame.SRCALPHA).convert_alpha()
        for r, row in enumerate(self.sprite):
            for c, v in enumerate(row):
                if v:
                    pygame.draw.rect(self.ship_base, (255,255,255,255),
                                     (c*self.pixel_size, r*self.pixel_size, self.pixel_size, self.pixel_size))

        self.ship = {
            "x":0.0, "y":0.0, "vx":0.0, "vy":0.0,
            "active":False, "angle":0.0, "timer":0.0,
            "scale":1.0, "mode":"normal"   # 'normal' | 'broken' | 'combat'
        }

        # Alien frames (2 frames; colors preserved)
        self.alien_frames = self._build_alien_frames()
        self.alien = {"active":False, "x":-9999, "y":-9999, "vx":0.0, "vy":0.0,
                      "angle":0.0, "scale":1, "frame":0, "ticker":0.0}
        self.alien_animation_speed = 30.0  # frames (scaled by 60)

        # Combat toys
        self.bullets = []
        self.bullet_timer = 0.0
        self.next_bullet_interval = 20    # frames (scaled by 60)
        self.particles = []

        # ---------- CRISP RENDERING CACHES ----------
        self.ship_scaled = {}           # {scale_int: Surface} nearest-neighbor
        self.ship_rot_cache = {}        # {(scale_int, ang_deg): Surface}
        self.alien_scaled = {}          # {(scale_int, frame): Surface}
        self.alien_rot_cache = {}       # {(scale_int, frame, ang_deg): Surface}
        self.ANGLE_STEP_DEFAULT = 3   # used for normal/combat (good perf)
        self.ANGLE_STEP_BROKEN  = 1   # smoother spin when broken

    # ---- crisp helpers ----
    def _quant_angle(self, ang):
        # Use the finer step when the ship is in 'broken' mode
        step = self.ANGLE_STEP_BROKEN if self.ship.get("mode") == "broken" else self.ANGLE_STEP_DEFAULT
        return int(round(ang / step)) * step


    def _get_ship_surface_crisp(self, scale, angle_deg):
        s = max(1, int(round(scale)))
        if s not in self.ship_scaled:
            self.ship_scaled[s] = pygame.transform.scale(
                self.ship_base, (self.ship_w * s, self.ship_h * s)
            )
        ang = self._quant_angle(angle_deg) % 360
        key = (s, ang)
        surf = self.ship_rot_cache.get(key)
        if surf is None:
            surf = pygame.transform.rotate(self.ship_scaled[s], -ang)
            self.ship_rot_cache[key] = surf
        return surf

    def _get_alien_surface_crisp(self, scale, frame, angle_deg):
        s = max(1, int(round(scale)))
        key_scaled = (s, frame)
        base = self.alien_scaled.get(key_scaled)
        if base is None:
            # Build nearest-neighbor scaled frame
            px = max(1, int(s * self.pixel_size))
            fr = self.alien_frames[frame]
            w = len(fr[0]) * px; h = len(fr) * px
            base = pygame.Surface((w, h), pygame.SRCALPHA).convert_alpha()
            for r, row in enumerate(fr):
                for c, hexcol in enumerate(row):
                    if hexcol != "#000000":
                        pygame.draw.rect(base, (*hex_to_rgb(hexcol), 255), (c*px, r*px, px, px))
            self.alien_scaled[key_scaled] = base

        ang = self._quant_angle(angle_deg) % 360
        key_rot = (s, frame, ang)
        rot = self.alien_rot_cache.get(key_rot)
        if rot is None:
            rot = pygame.transform.rotate(base, -ang)
            self.alien_rot_cache[key_rot] = rot
        return rot

    # ---- alien frames from JS ----
    def _build_alien_frames(self):
        f0 = [
 ['#000000']*15,
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
 ['#000000']*15]
        f1 = [
 ['#000000']*15,
 ['#000000']*15,
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
 ['#000000']*15,
 ['#000000']*15]
        return [f0, f1]

    # ---- exhaust particles ----
    def _add_thrust(self):
        angle_rad = math.radians(self.ship["angle"])
        scale     = self.ship["scale"]
        rear_off_x = -(self.ship_w * scale) / 2
        rear_off_y = 0
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)

        rx = cos_a*rear_off_x - sin_a*rear_off_y
        ry = sin_a*rear_off_x + cos_a*rear_off_y

        cx = self.ship["x"] + (self.ship_w * scale) / 2
        cy = self.ship["y"] + (self.ship_h * scale) / 2
        tx, ty = cx + rx, cy + ry

        for _ in range(4):
            base = angle_rad + math.pi
            spread = (random.random() - 0.5) * 0.6
            ang = base + spread
            spd = 1.0 + random.random() * 0.5
            self.particles.append({"x":tx, "y":ty, "vx":math.cos(ang)*spd, "vy":math.sin(ang)*spd,
                                   "r":(3.0 + random.random())*scale, "a":1.0})

    def _update_particles(self, dt):
        decay = math.pow(0.9, dt*60.0)  # matches JS frame-scaling
        fade  = 0.1 * dt * 60.0
        keep = []
        for p in self.particles:
            p["x"] += p["vx"] * dt; p["y"] += p["vy"] * dt
            p["r"] *= decay
            p["a"] -= fade
            if p["a"] > 0: keep.append(p)
        self.particles = keep

    def _draw_particles(self, screen):
        # radial gradient approximation: core + halo
        for p in self.particles:
            x, y = int(p["x"]), int(p["y"])
            a = clamp(p["a"], 0.0, 1.0)
            r_core = max(1, int(p["r"]))
            r_halo = max(r_core+1, int(p["r"]*1.8))
            pygame.draw.circle(screen, (180,220,255, int(200*a)), (x,y), r_core, 0)
            pygame.draw.circle(screen, (0,100,255,  int( 80*a)), (x,y), r_halo, 0)

    # ---- bullets ----
    def _fire_bullet_pair(self):
        if not self.ship["active"] or self.ship["mode"] != "combat": return
        scale = self.ship["scale"]
        angle = math.radians(self.ship["angle"])
        guns  = [(6,4), (6,11)]
        center_col = len(self.sprite[0]) / 2
        center_row = len(self.sprite)    / 2
        for gc, gr in guns:
            relX = (gc - center_col) * self.pixel_size * scale
            relY = (gr - center_row) * self.pixel_size * scale
            rx =  math.cos(angle)*relX - math.sin(angle)*relY
            ry =  math.sin(angle)*relX + math.cos(angle)*relY
            cx = self.ship["x"] + (self.ship_w * scale) / 2
            cy = self.ship["y"] + (self.ship_h * scale) / 2
            bulletX, bulletY = cx + rx, cy + ry
            speed = 1000.0
            self.bullets.append({"x":bulletX, "y":bulletY,
                                 "vx":math.cos(angle)*speed + self.ship["vx"],
                                 "vy":math.sin(angle)*speed + self.ship["vy"],
                                 "r":1.0*scale, "life":240.0})

    # ---- activation / spawn ----
    def _maybe_activate_ship(self):
        if self.ship["active"]: return
        if random.random() < 0.002:   # activation gate
            self.ship["active"] = True
            r = random.random()
            self.ship["mode"]  = "broken" if r < 0.1 else ("combat" if r < 0.4 else "normal")
            self.ship["scale"] = float(random.randint(1,4))

            # edge spawn
            margin = 100
            e = random.randint(0,3)
            if   e == 0: sx, sy = random.random()*self.w, -margin
            elif e == 1: sx, sy = self.w+margin,          random.random()*self.h
            elif e == 2: sx, sy = random.random()*self.w, self.h+margin
            else:        sx, sy = -margin,                random.random()*self.h
            self.ship["x"], self.ship["y"] = sx, sy

            # target near center
            cx, cy = self.w/2, self.h/2
            spread = min(self.w, self.h)*0.25
            tx = cx + (random.random()-0.5)*spread
            ty = cy + (random.random()-0.5)*spread

            # velocity toward target
            w = self.ship_w * self.ship["scale"]; h = self.ship_h * self.ship["scale"]
            dx = tx - (self.ship["x"] + w/2); dy = ty - (self.ship["y"] + h/2)
            dist = math.hypot(dx, dy) or 1.0
            base_speed = (0.8 + random.random()*0.8)*60.0 if self.ship["mode"]=="broken" else (2 + random.random()*6)*60.0
            self.ship["vx"] = dx/dist*base_speed
            self.ship["vy"] = dy/dist*base_speed
            self.ship["angle"] = math.degrees(math.atan2(self.ship["vy"], self.ship["vx"]))
            self.ship["timer"] = 0.0

            # alien setup
            if self.ship["mode"] == "combat":
                self.alien.update({"active":True, "scale":int(self.ship["scale"]), "frame":0, "ticker":0.0})
            else:
                self.alien.update({"active":False, "x":-9999, "y":-9999, "frame":0})

    # ---- public update/draw ----
    def update(self, dt):
        self._maybe_activate_ship()

        # inactive: just particles
        if not self.ship["active"]:
            self._update_particles(dt)
            return

        # early deactivation
        buffer = 100
        time_limit = 50.0 if self.ship["mode"]=="broken" else (25.0 if self.ship["mode"]=="combat" else 20.0)
        if (self.ship["x"] < -buffer or self.ship["x"] > self.w + buffer or
            self.ship["y"] < -buffer or self.ship["y"] > self.h + buffer or
            self.ship["timer"] > time_limit):
            self.ship["active"] = False
            self.alien.update({"active":False, "x":-9999, "y":-9999, "frame":0})
            self._update_particles(dt)
            return

        # motion/timer
        self.ship["x"] += self.ship["vx"] * dt
        self.ship["y"] += self.ship["vy"] * dt
        self.ship["timer"] += dt

        # combat goodies
        if self.ship["mode"] == "combat":
            self.bullet_timer += dt * 60.0
            if self.bullet_timer >= self.next_bullet_interval:
                self._fire_bullet_pair()
                self.bullet_timer = 0.0
                self.next_bullet_interval = 5 + int(random.random()*50)  # 5..54 frames

            # alien position 200px ahead + perpendicular bob
            forward = 200.0
            ang = math.radians(self.ship["angle"])
            ship_cx = self.ship["x"] + (self.ship_w * self.ship["scale"])/2
            ship_cy = self.ship["y"] + (self.ship_h * self.ship["scale"])/2
            ax = ship_cx + math.cos(ang)*forward
            ay = ship_cy + math.sin(ang)*forward
            bob_amp, bob_freq = 50.0, 2.0
            bob = math.sin(self.ship["timer"]*bob_freq)*bob_amp
            ax += math.cos(ang + math.pi/2)*bob
            ay += math.sin(ang + math.pi/2)*bob
            self.alien["x"] = ax; self.alien["y"] = ay
            self.alien["vx"] = self.ship["vx"]; self.alien["vy"] = self.ship["vy"]
            self.alien["angle"] = self.ship["angle"]
            self.alien["scale"] = int(self.ship["scale"])

            self.alien["ticker"] += dt * 60.0
            if self.alien["ticker"] >= self.alien_animation_speed:
                self.alien["ticker"] = 0.0
                self.alien["frame"]  = (self.alien["frame"] + 1) % len(self.alien_frames)

        if self.ship["mode"] != "broken":
            self._add_thrust()

        # bullets
        keep = []
        for b in self.bullets:
            b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
            b["life"] -= dt * 60.0
            if b["life"] > 0:
                keep.append(b)
        self.bullets = keep

        self._update_particles(dt)

        # broken spin speed (0.5 deg/frame @60)
        if self.ship["mode"] == "broken":
            self.ship["angle"] += 0.5 * dt * 60.0

    def draw(self, screen):
        # bullets
        for b in self.bullets:
            pygame.draw.circle(screen, (255,255,255,255), (int(b["x"]), int(b["y"])), max(1, int(b["r"])), 0)
        # particles
        self._draw_particles(screen)

        # ship (CRISP)
        if self.ship["active"]:
            surf = self._get_ship_surface_crisp(self.ship["scale"], self.ship["angle"])
            rect = surf.get_rect(center=(
                int(self.ship["x"] + (self.ship_w * self.ship["scale"]) / 2),
                int(self.ship["y"] + (self.ship_h * self.ship["scale"]) / 2)
            ))
            screen.blit(surf, rect)

        # alien (CRISP)
        if self.alien["active"] or self.ship["mode"] == "combat":
            a_rot = self._get_alien_surface_crisp(self.alien["scale"], self.alien["frame"], self.alien["angle"])
            rect = a_rot.get_rect(center=(int(self.alien["x"]), int(self.alien["y"])))
            screen.blit(a_rot, rect)

# ---------- COMBINED ----------
class ArcadeBattlefield:
    def __init__(self, w, h, bg_color=(0,0,0)):
        self.starfield = JSStarfield(w, h, bg_color)
        self.battle    = JSBattle(w, h)

    def resize(self, w, h):
        self.starfield.resize(w, h)
        self.battle.w, self.battle.h = w, h

    def update(self, dt):
        self.starfield.update(dt)
        self.battle.update(dt)

    def draw(self, screen):
        self.starfield.draw(screen)
        self.battle.draw(screen)

# ---------- Standalone runner ----------
if __name__ == "__main__":
    import argparse
    pygame.init()
    parser = argparse.ArgumentParser()
    parser.add_argument("--fullscreen", action="store_true", help="Fullscreen")
    parser.add_argument("--size", default="800x480", help="WxH if windowed")
    parser.add_argument("--bg", default="red", choices=["red","blue","black"], help="Background")
    parser.add_argument("--force", choices=["normal","broken","combat"], help="Force immediate ship spawn")
    parser.add_argument("--angle-step", type=int, default=3, help="Angle quantization (degrees) for crisp cache")
    args = parser.parse_args()

    if args.fullscreen:
        screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN | pygame.DOUBLEBUF, vsync=1)
    else:
        W, H = map(int, args.size.lower().split("x"))
        screen = pygame.display.set_mode((W, H), pygame.DOUBLEBUF, vsync=1)

    W, H = screen.get_size()
    pygame.mouse.set_visible(False)
    pygame.event.set_blocked([pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP])

    bg_map = {"red":(24,2,6), "blue":(10,16,32), "black":(0,0,0)}
    field = ArcadeBattlefield(W, H, bg_color=bg_map[args.bg])
    # expose angle-step on the crisp caches
    field.battle.ANGLE_STEP = max(1, int(args.angle_step))

    # cheat: force immediate action
    def force_spawn(battle, mode):
        if not mode: return
        b = battle
        b.ship["active"] = True
        b.ship["mode"]   = mode
        b.ship["scale"]  = float(random.randint(1,4))
        if mode == "combat":
            b.alien.update({"active":True, "scale":int(b.ship["scale"]), "frame":0, "ticker":0.0})
        else:
            b.alien.update({"active":False, "x":-9999, "y":-9999, "frame":0})
        # Edge spawn → target center (same as normal path)
        margin = 100
        e = random.randint(0,3)
        if   e == 0: sx, sy = random.random()*b.w, -margin
        elif e == 1: sx, sy = b.w+margin,          random.random()*b.h
        elif e == 2: sx, sy = random.random()*b.w, b.h+margin
        else:        sx, sy = -margin,             random.random()*b.h
        b.ship["x"], b.ship["y"] = sx, sy
        cx, cy = b.w/2, b.h/2
        spread = min(b.w, b.h)*0.25
        tx = cx + (random.random()-0.5)*spread
        ty = cy + (random.random()-0.5)*spread
        w = b.ship_w*b.ship["scale"]; h = b.ship_h*b.ship["scale"]
        dx = tx - (b.ship["x"] + w/2); dy = ty - (b.ship["y"] + h/2)
        dist = math.hypot(dx,dy) or 1.0
        base_speed = (0.8 + random.random()*0.8)*60.0 if mode=="broken" else (2 + random.random()*6)*60.0
        b.ship["vx"] = dx/dist*base_speed; b.ship["vy"] = dy/dist*base_speed
        b.ship["angle"] = math.degrees(math.atan2(b.ship["vy"], b.ship["vx"]))
        b.ship["timer"] = 0.0

    force_spawn(field.battle, args.force)

    clock = pygame.time.Clock()
    font  = pygame.font.SysFont(None, 24)
    running = True
    while running:
        dt = clock.tick(0) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q): running = False
                elif e.key == pygame.K_c: force_spawn(field.battle, "combat")
                elif e.key == pygame.K_b: force_spawn(field.battle, "broken")
                elif e.key == pygame.K_n: force_spawn(field.battle, "normal")

        field.update(dt)
        field.draw(screen)

        fps = font.render(f"{clock.get_fps():.1f} FPS", True, (0,255,0))
        screen.blit(fps, (10, 10))
        pygame.display.flip()

    pygame.quit()
