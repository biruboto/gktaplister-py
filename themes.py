from dataclasses import dataclass

@dataclass
class Theme:
    name: str
    bg_color: tuple
    accent: tuple
    dim_white: tuple
    logo_size: int
    json_path: str

# Start with your current red setup
RED = Theme(
    name="red",
    bg_color=(24, 2, 6),
    accent=(255, 36, 56),
    dim_white=(180, 180, 180),
    logo_size=130,
    json_path="./json/red-beers.json",
)

# Blue can point to its own JSON + colors (tweak later)
BLUE = Theme(
    name="blue",
    bg_color=(10, 16, 32),
    accent=(64, 180, 255),
    dim_white=(190, 200, 220),
    logo_size=130,
    json_path="./json/blue-beers.json",
)