from dataclasses import dataclass

@dataclass
class Theme:
    name: str
    bg_color: tuple
    accent: tuple
    dim_white: tuple
    logo_size: int
    json_path: str
    text_brewery: tuple
    text_beer: tuple
    text_info: tuple

# Start with your current red setup
RED = Theme(
    name="red",
    bg_color=(14, 9, 9),
    accent=(218, 30, 55),
    dim_white=(180, 180, 180),
    logo_size=130,
    json_path="json/red-beers.json",
    text_brewery=(161, 29, 51),
    text_beer=(110, 20, 35),
    text_info=(221, 186, 186),
)

# Blue can point to its own JSON + colors (tweak later)
BLUE = Theme(
    name="blue",
    bg_color=(13, 13, 27),
    accent=(64, 180, 255),
    dim_white=(190, 200, 220),
    logo_size=130,
    json_path="json/blue-beers.json",
    text_brewery=(80, 140, 155),
    text_beer=(19, 75, 112),
    text_info=(206, 216, 235),
)
