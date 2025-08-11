import pygame, json, os
from themes import Theme  # and RED/BLUE via launcher
from systems.starfield import Starfield
from systems.logos import build_logo_cache
from systems.ui import draw_taplist
from systems.battle import Battle
from pathlib import Path
from systems.fetch import is_url, fetch_text_conditional

BEERDB_FILE = "./json/beer-database.json"
FPS = 40

def load_json(path):
    with open(path, encoding="utf-8") as f:
        import json
        return json.load(f)
    
def load_beers(json_src: str):
    if is_url(json_src):
        local = fetch_text_conditional(json_src)  # cached local file
        return json.loads(Path(local).read_text(encoding="utf-8"))
    else:
        return json.loads(Path(json_src).read_text(encoding="utf-8"))

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

    logo_cache = build_logo_cache(beerdb, theme.logo_size, theme)
    starfield = Starfield(W, H, count=90)
    battle = Battle(W, H)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: running = False

        starfield.update(dt)
        battle.update(dt)
        battle.draw(screen)


        screen.fill(theme.bg_color)
        starfield.draw(screen)
        draw_taplist(
            screen, beers, logo_cache, theme, W, H,
            beer_font_path="./fonts/MagistralBold.otf",
            info_font_path="./fonts/Orbitron.otf"
        )
        pygame.display.flip()

    pygame.quit()
