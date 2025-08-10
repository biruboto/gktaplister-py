import pygame

class Battle:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.active = False  # toggle when you want it to run
        self.timer = 0.0

    def start(self):
        """Begin the battle animation."""
        self.active = True
        self.timer = 0.0

    def stop(self):
        """Stop the battle animation."""
        self.active = False

    def update(self, dt):
        """Update battle state if active."""
        if not self.active:
            return
        self.timer += dt
        # TODO: Add sprite movement, collisions, etc.

    def draw(self, surface):
        """Draw battle elements if active."""
        if not self.active:
            return
        # For now, draw a placeholder rectangle
        rect = pygame.Rect(self.width//2 - 50, self.height//2 - 50, 100, 100)
        pygame.draw.rect(surface, (255, 0, 0), rect, 2)
