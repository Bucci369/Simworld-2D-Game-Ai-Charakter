import os

# Basic settings
TITLE = "Demo Welt"
FPS = 60  # Frames per second
# Größeres Fenster für mehr Sicht
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FULLSCREEN = False  # Auf True setzen für Vollbild
DEBUG_PANEL_WIDTH = 180  # Breite der Debug-Leiste (verkleinert von 260)
DEBUG_ENABLE_AUTO_SCAN = True  # PNGs automatisch auflisten

TILE_SIZE = 32
USE_SIMPLE_WORLD = True  # Wenn True: benutze prozedurale Welt aus Grass_Middle + Oak_Tree
USE_KENNEY_WORLD = True  # 🏘️ Wenn True: benutze hochwertige Kenney Sketch Town Assets
USE_ISOMETRIC_WORLD = True  # 🏘️ Wenn True: benutze KORREKTE isometrische Kenney Assets (ohne Lücken)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
MAP_PATH = os.path.join(ASSETS_DIR, '001', 'TiledMap Editor', 'sample map demo.tmx')

# Simple World Assets
GRASS_TILE_PATH = os.path.join(ASSETS_DIR, 'Tiles', 'Grass_Middle.png')
OAK_TREE_PATH = os.path.join(ASSETS_DIR, 'Outdoor decoration', 'Oak_Tree.png')
FARMLAND_TILE_PATH = os.path.join(ASSETS_DIR, 'Tiles', 'FarmLand_Tile.png')
WATER_TILE_PATH = os.path.join(ASSETS_DIR, 'Tiles', 'Water_Middle.png')
PATH_TILE_PATH = os.path.join(ASSETS_DIR, 'Tiles', 'Path_Middle.png')

# Simple World Konfiguration - ERWEITERT für mehr Abstand zwischen Tribes
SIMPLE_WORLD_WIDTH_TILES = 70    # Erweitert: 70x70 Tiles (2240x2240 Pixel) für mehr Platz
SIMPLE_WORLD_HEIGHT_TILES = 70   # Erweitert: 70x70 Tiles (2240x2240 Pixel) für mehr Platz
SIMPLE_WORLD_TREE_DENSITY = 0.12  # Höhere Dichte für größere Wälder
SIMPLE_WORLD_SEED = 42           # Für reproduzierbare Platzierung; None für Zufall
SIMPLE_WORLD_FARMLAND_PATCHES = 6  # Mehr Farmland-Patches für größere Welt
SIMPLE_WORLD_FARMLAND_RADIUS_RANGE = (3, 6)  # Größere Farmland-Patches
SIMPLE_WORLD_LAKE_RADII = (6, 4)  # Größerer See für erweiterte Welt
SIMPLE_WORLD_LAKE_CENTER_REL = (0.7, 0.3)  # versetzt, damit Pfad nicht durch muss
HOUSE_IMAGE_PATH = os.path.join(ASSETS_DIR, 'Outdoor decoration', 'House.png')

# Player Sprite Sheet Konfiguration
# Mapping: Richtung -> Zeilenindex im character-grid-sprite.png
# Passe diese Zahlen an, falls die Reihenfolge nicht stimmt.
PLAYER_SHEET_ROWS = {
	# Spezieller Wert: -1 bedeutet "left aus right spiegeln"
	'down': 0,
	'right': 1,
	'up': 2,
	'left': -1,
}

# Anzahl horizontaler Frames, die pro Bewegungsanimation genutzt werden (von links beginnend)
PLAYER_FRAMES_PER_DIRECTION = 4
