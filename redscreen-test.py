import time

import pygame


def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
    print("driver:", pygame.display.get_driver(), "size:", screen.get_size(), flush=True)
    screen.fill((255, 0, 0))
    pygame.display.flip()
    time.sleep(5)
    pygame.quit()


if __name__ == "__main__":
    main()
