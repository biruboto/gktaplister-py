# main.py
import pygame, json
from themes import Theme  # and RED/BLUE via launcher
from systems.starfield import Starfield
from systems.logos import build_logo_cache
from systems.ui import draw_taplist

BEERDB_FILE = "./json/beer-database.json"
FPS = 40

def load_json(path):
    with open(path, encoding="utf-8") as f:
        import json
        return json.load(f)

def merge_taplist_with_db(taplist, beerdb):
    db_by_id = {b['id']: b for b in beerdb}
    out = []
    for beer in taplist["beers"]:
        b = db_by_id.get(beer["id"])
        if b:
            b = b.copy()
            b['soldOut'] = beer.get('soldOut', False)
            out.append(b)
    return out

def run(theme):
    pygame.init()
    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    W, H = screen.get_size()
    clock = pygame.time.Clock()

    taplist = load_json(theme.json_path)
    beerdb = load_json(BEERDB_FILE)
    beers = merge_taplist_with_db(taplist, beerdb)

    logo_cache = build_logo_cache(beerdb, theme.logo_size)
    starfield = Starfield(W, H, count=90)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: running = False

        starfield.update(dt)

        screen.fill(theme.bg_color)
        starfield.draw(screen)
        draw_taplist(
            screen, beers, logo_cache, theme, W, H,
            beer_font_path="./fonts/MagistralBold.otf",
            info_font_path="./fonts/Orbitron.otf"
        )
        pygame.display.flip()

    pygame.quit()
