import pygame, random, sys

# Configurable
SCREEN_SIZE = (800, 480)   # adjust to Pi display size
STAR_COUNT = 2000          # crank this up to push GPU/CPU harder
STAR_SPEED = 200           # pixels per second

class Star:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.reset()

    def reset(self):
        self.x = random.random() * self.w
        self.y = random.random() * self.h
        self.vel = STAR_SPEED * (0.5 + random.random())  # vary a bit
        self.alpha = 128 + random.randint(0, 127)

    def update(self, dt):
        self.y += self.vel * dt
        if self.y > self.h:
            self.reset()
            self.y = 0

    def draw(self, surface):
        # Simple white dot with variable brightness
        color = (self.alpha, self.alpha, self.alpha)
        surface.set_at((int(self.x), int(self.y)), color)

def run():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    clock = pygame.time.Clock()

    stars = [Star(*SCREEN_SIZE) for _ in range(STAR_COUNT)]

    font = pygame.font.SysFont(None, 24)

    running = True
    while running:
        dt = clock.tick(0) / 1000.0  # "0" lets it run flat-out
        fps = clock.get_fps()

        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False

        # Update
        for s in stars:
            s.update(dt)

        # Draw
        screen.fill((0, 0, 0))
        for s in stars:
            s.draw(screen)

        # FPS overlay
        fps_surf = font.render(f"{fps:.1f} FPS", True, (0,255,0))
        screen.blit(fps_surf, (10, 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    run()
