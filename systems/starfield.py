import math, random, pygame

class Starfield:
    def __init__(self, w, h, count=90, colors=None):
        self.w, self.h = w, h
        self.colors = colors or [
            (255,80,120), (255,255,255), (180,50,80),
            (200,120,140), (255,200,200)
        ]
        self.stars = []
        for i in range(count):
            self.stars.append({
                "x": random.random()*w,
                "y": random.random()*h,
                "speed": 0.12 + random.random()*0.7,
                "size": 1 + int(random.random()*3),
                "tw": random.random()*math.tau,
                "color": self.colors[i % len(self.colors)]
            })
        self.t = 0.0

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        for s in self.stars:
            offset = math.sin(self.t * s["speed"] + s["tw"]) * 1.5
            r,g,b = s["color"]
            col = (
                max(0,min(255,int(r+offset*32))),
                max(0,min(255,int(g+offset*32))),
                max(0,min(255,int(b+offset*32))),
            )
            pygame.draw.circle(surf, col, (int(s["x"]), int((s["y"]+offset) % self.h)), s["size"])
