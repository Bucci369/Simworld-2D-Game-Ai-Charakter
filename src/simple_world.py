import random
import os
import pygame
from settings import (
    GRASS_TILE_PATH,
    OAK_TREE_PATH,
    TILE_SIZE,
    SIMPLE_WORLD_WIDTH_TILES,
    SIMPLE_WORLD_HEIGHT_TILES,
    SIMPLE_WORLD_TREE_DENSITY,
    SIMPLE_WORLD_SEED,
    FARMLAND_TILE_PATH,
    WATER_TILE_PATH,
    PATH_TILE_PATH,
    SIMPLE_WORLD_FARMLAND_PATCHES,
    SIMPLE_WORLD_FARMLAND_RADIUS_RANGE,
    SIMPLE_WORLD_LAKE_RADII,
    SIMPLE_WORLD_LAKE_CENTER_REL,
    HOUSE_IMAGE_PATH,
)

class SimpleWorld:
    def __init__(self, area_width_tiles=None, area_height_tiles=None, tree_density=None, seed=None):
        # Defaults
        self.area_width_tiles = area_width_tiles or SIMPLE_WORLD_WIDTH_TILES
        self.area_height_tiles = area_height_tiles or SIMPLE_WORLD_HEIGHT_TILES
        density = tree_density if tree_density is not None else SIMPLE_WORLD_TREE_DENSITY
        use_seed = SIMPLE_WORLD_SEED if seed is None else seed
        if use_seed is not None:
            random.seed(use_seed)

        # Dimensions
        self.width = self.area_width_tiles * TILE_SIZE
        self.height = self.area_height_tiles * TILE_SIZE

        # Assets
        self.grass_tile = pygame.image.load(GRASS_TILE_PATH).convert_alpha()
        self.oak_tree = pygame.image.load(OAK_TREE_PATH).convert_alpha()
        self.farmland_tile = pygame.image.load(FARMLAND_TILE_PATH).convert_alpha()
        self.water_tile = pygame.image.load(WATER_TILE_PATH).convert_alpha()
        self.path_tile = pygame.image.load(PATH_TILE_PATH).convert_alpha()

        # Hilfsfunktionen zum Zuschneiden & Skalieren, damit keine Lücken entstehen
        def trim_and_scale(surf: pygame.Surface) -> pygame.Surface:
            mask = pygame.mask.from_surface(surf)
            if mask.count() == 0:
                return pygame.transform.scale(surf, (TILE_SIZE, TILE_SIZE))
            bbox = mask.get_bounding_rects()
            # get_bounding_rects kann mehrere zurückgeben; nimm union
            if bbox:
                if len(bbox) > 1:
                    # vereinige
                    min_l = min(r.left for r in bbox)
                    min_t = min(r.top for r in bbox)
                    max_r = max(r.right for r in bbox)
                    max_b = max(r.bottom for r in bbox)
                    rect = pygame.Rect(min_l, min_t, max_r - min_l, max_b - min_t)
                else:
                    rect = bbox[0]
                trimmed = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                trimmed.blit(surf, (0, 0), rect)
            else:
                trimmed = surf
            if trimmed.get_width() != TILE_SIZE or trimmed.get_height() != TILE_SIZE:
                trimmed = pygame.transform.smoothscale(trimmed, (TILE_SIZE, TILE_SIZE))
            return trimmed

        # Nur Overlay-Tiles trimmen & skalieren (Grass wird gekachelt mit eigener Größe; Baum unverändert)
        self.farmland_tile = trim_and_scale(self.farmland_tile)
        self.water_tile = trim_and_scale(self.water_tile)
        self.path_tile = trim_and_scale(self.path_tile)

        # Background (grass)
        self.background = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        grass_w, grass_h = self.grass_tile.get_width(), self.grass_tile.get_height()
        for y in range(0, self.height, grass_h):
            for x in range(0, self.width, grass_w):
                self.background.blit(self.grass_tile, (x, y))

        # Overlay grid
        tiles_x = self.area_width_tiles
        tiles_y = self.area_height_tiles
        self.overlay = [[None for _ in range(tiles_x)] for _ in range(tiles_y)]

        # Paths (cross) zuerst zeichnen
        center_x = tiles_x // 2
        center_y = tiles_y // 2
        for tx in range(tiles_x):
            self.overlay[center_y][tx] = 'path'
        for ty in range(tiles_y):
            self.overlay[ty][center_x] = 'path'

        # Lake (ellipse) danach – überschreibt Pfad im Inneren, so dass kein Weg hindurch geht
        lake_rx_tiles, lake_ry_tiles = SIMPLE_WORLD_LAKE_RADII
        lake_cx = int(SIMPLE_WORLD_LAKE_CENTER_REL[0] * tiles_x)
        lake_cy = int(SIMPLE_WORLD_LAKE_CENTER_REL[1] * tiles_y)
        for ty in range(tiles_y):
            dy = (ty - lake_cy) / lake_ry_tiles if lake_ry_tiles else 0
            for tx in range(tiles_x):
                dx = (tx - lake_cx) / lake_rx_tiles if lake_rx_tiles else 0
                if dx*dx + dy*dy <= 1.0:
                    self.overlay[ty][tx] = 'water'

        # Farmland patches
        patch_count = SIMPLE_WORLD_FARMLAND_PATCHES
        min_r, max_r = SIMPLE_WORLD_FARMLAND_RADIUS_RANGE
        attempts = patch_count * 4
        placed = 0
        while placed < patch_count and attempts > 0:
            attempts -= 1
            r = random.randint(min_r, max_r)
            cx = random.randint(r, tiles_x - r - 1)
            cy = random.randint(r, tiles_y - r - 1)
            if self.overlay[cy][cx] == 'water':
                continue
            changed = False
            for ty in range(cy - r, cy + r + 1):
                for tx in range(cx - r, cx + r + 1):
                    if (tx - cx)**2 + (ty - cy)**2 <= r*r:
                        if self.overlay[ty][tx] is None:
                            self.overlay[ty][tx] = 'farm'
                            changed = True
            if changed:
                placed += 1

        # Blit overlay onto background
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                code = self.overlay[ty][tx]
                if code is None:
                    continue
                px = tx * TILE_SIZE
                py = ty * TILE_SIZE
                if code == 'water':
                    self.background.blit(self.water_tile, (px, py))
                elif code == 'path':
                    self.background.blit(self.path_tile, (px, py))
                elif code == 'farm':
                    self.background.blit(self.farmland_tile, (px, py))

        # House platzieren (ein Haus nahe des Pfadkreuzes, nicht auf Wasser)
        self.house_image = None
        try:
            if HOUSE_IMAGE_PATH and os.path.exists(HOUSE_IMAGE_PATH):
                self.house_image = pygame.image.load(HOUSE_IMAGE_PATH).convert_alpha()
        except Exception:
            self.house_image = None
        self.structures = []
        if self.house_image:
            hx_tiles = center_x + 5
            hy_tiles = center_y - 2
            if 0 <= hx_tiles < tiles_x and 0 <= hy_tiles < tiles_y and self.overlay[hy_tiles][hx_tiles] != 'water':
                self.structures.append((hx_tiles * TILE_SIZE, (hy_tiles+1) * TILE_SIZE - self.house_image.get_height()))

        # Optional: simple outlines (lake + farmland) for better contrast
        outline_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        water_color = (30, 90, 160, 90)
        farm_color = (200, 170, 60, 80)
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                code = self.overlay[ty][tx]
                if code in ('water', 'farm'):
                    # Check any neighbor different -> outline
                    neighbors = [(tx+1,ty),(tx-1,ty),(tx,ty+1),(tx,ty-1)]
                    for nx, ny in neighbors:
                        if 0 <= nx < tiles_x and 0 <= ny < tiles_y:
                            if self.overlay[ny][nx] != code:
                                color = water_color if code=='water' else farm_color
                                pygame.draw.rect(outline_surface, color, (tx*TILE_SIZE, ty*TILE_SIZE, TILE_SIZE, TILE_SIZE), 2)
                                break
        self.background.blit(outline_surface, (0,0))

        # Trees avoid features
        wanted_trees = int(self.area_width_tiles * self.area_height_tiles * density)
        self.trees = []
        max_attempts = wanted_trees * 5
        attempts = 0
        while len(self.trees) < wanted_trees and attempts < max_attempts:
            attempts += 1
            tx = random.randint(0, self.width - self.oak_tree.get_width())
            ty = random.randint(0, self.height - self.oak_tree.get_height())
            tile_x = tx // TILE_SIZE
            tile_y = ty // TILE_SIZE
            if 0 <= tile_x < self.area_width_tiles and 0 <= tile_y < self.area_height_tiles:
                code = self.overlay[tile_y][tile_x]
                if code in ('water', 'path', 'farm'):
                    continue
            self.trees.append((tx, ty))
        self.trees.sort(key=lambda p: p[1])  # painter's order
        
        # Load decorative sprites
        self._load_decoration_sprites()
        
        # Generate decorative objects on grass areas
        self._generate_decorations()
        
        # Vom Debug Panel platzierte dynamische Objekte
        self.dynamic_objects = []  # (image, x, y)

    def render(self, surface: pygame.Surface, camera_rect: pygame.Rect):
        surface.blit(self.background, (-camera_rect.left, -camera_rect.top))
        view_rect = camera_rect
        
        # Draw decorations first (on ground level)
        if hasattr(self, 'decorations'):
            for decoration in self.decorations:
                dx, dy = decoration['x'], decoration['y']
                sprite = decoration['sprite']
                rect = pygame.Rect(dx, dy, sprite.get_width(), sprite.get_height())
                if rect.colliderect(view_rect):
                    surface.blit(sprite, (dx - camera_rect.left, dy - camera_rect.top))
        
        # Strukturen (Haus) vor Bäumen oder nach Bedarf sortieren
        if self.structures:
            for (sx, sy) in self.structures:
                if self.house_image:
                    rect = pygame.Rect(sx, sy, self.house_image.get_width(), self.house_image.get_height())
                    if rect.colliderect(view_rect):
                        surface.blit(self.house_image, (sx - camera_rect.left, sy - camera_rect.top))
        # Dynamische Objekte (sortiert nach y für Zeichnungsreihenfolge)
        for obj in sorted(self.dynamic_objects, key=lambda e: e['y']):
            img, ox, oy = obj['image'], obj['x'], obj['y']
            rect = pygame.Rect(ox, oy, img.get_width(), img.get_height())
            if rect.colliderect(view_rect):
                surface.blit(img, (ox - camera_rect.left, oy - camera_rect.top))
        for (x, y) in self.trees:
            tree_rect = pygame.Rect(x, y, self.oak_tree.get_width(), self.oak_tree.get_height())
            if tree_rect.colliderect(view_rect):
                surface.blit(self.oak_tree, (x - camera_rect.left, y - camera_rect.top))

    # --- Collision Helpers ---
    def is_blocked_rect(self, rect: pygame.Rect) -> bool:
        """Block nur wenn Mittelpunkt des Spielers auf Wasser liegt.
        Dadurch kann man bis an den Rand laufen ohne komplett zu stoppen."""
        tx = rect.centerx // TILE_SIZE
        ty = rect.centery // TILE_SIZE
        if 0 <= ty < self.area_height_tiles and 0 <= tx < self.area_width_tiles:
            return self.overlay[ty][tx] == 'water'
        return False

    # --- Spawn Helper ---
    def find_safe_spawn(self) -> tuple[int,int]:
        cx = self.area_width_tiles // 2
        cy = self.area_height_tiles // 2
        # Bevorzugt Kreuzung (jetzt path)
        if self.overlay[cy][cx] != 'water':
            return (cx * TILE_SIZE + TILE_SIZE//2, cy * TILE_SIZE + TILE_SIZE//2)
        # Spiral Suche nach erstem Nicht-Wasser
        max_r = max(self.area_width_tiles, self.area_height_tiles)
        for r in range(1, max_r):
            for dx in range(-r, r+1):
                for dy in (-r, r):
                    tx, ty = cx+dx, cy+dy
                    if 0 <= tx < self.area_width_tiles and 0 <= ty < self.area_height_tiles and self.overlay[ty][tx] != 'water':
                        return (tx*TILE_SIZE + TILE_SIZE//2, ty*TILE_SIZE + TILE_SIZE//2)
            for dy in range(-r+1, r):
                for dx in (-r, r):
                    tx, ty = cx+dx, cy+dy
                    if 0 <= tx < self.area_width_tiles and 0 <= ty < self.area_height_tiles and self.overlay[ty][tx] != 'water':
                        return (tx*TILE_SIZE + TILE_SIZE//2, ty*TILE_SIZE + TILE_SIZE//2)
        # Fallback 0,0
        return (TILE_SIZE//2, TILE_SIZE//2)

    # --- Dynamische Objekte hinzufügen ---
    def add_dynamic_object(self, image: pygame.Surface, x: int, y: int, image_name: str = "unknown.png") -> bool:
        """Fügt ein Objekt hinzu (untere Mitte an Position ausgerichtet). Verhindert Platzierung auf Wasser."""
        tile_x = (x + image.get_width()//2) // TILE_SIZE
        tile_y = (y + image.get_height() - 1) // TILE_SIZE
        if 0 <= tile_x < self.area_width_tiles and 0 <= tile_y < self.area_height_tiles:
            if self.overlay[tile_y][tile_x] == 'water':
                return False
        # Speichere auch den Bildnamen für Speicher/Laden
        obj_data = {
            'image': image,
            'x': x,
            'y': y,
            'image_name': image_name
        }
        self.dynamic_objects.append(obj_data)
        return True

    def clear_dynamic_objects(self):
        """Entfernt alle platzierten dynamischen Objekte"""
        self.dynamic_objects.clear()

    def load_dynamic_objects(self, objects_data):
        """Lädt dynamische Objekte aus gespeicherten Daten"""
        self.dynamic_objects.clear()
        
        # Asset-Cache für bereits geladene Bilder
        asset_cache = {}
        
        for obj_data in objects_data:
            image_name = obj_data.get('image_name', 'unknown.png')
            x = obj_data['x']
            y = obj_data['y']
            
            # Lade Bild falls noch nicht im Cache
            if image_name not in asset_cache:
                # Suche Bild in assets Ordner
                base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
                image_path = None
                
                # Durchsuche alle Unterordner nach dem Bild
                for root, dirs, files in os.walk(base_dir):
                    if image_name in files:
                        image_path = os.path.join(root, image_name)
                        break
                
                if image_path and os.path.exists(image_path):
                    try:
                        loaded_image = pygame.image.load(image_path).convert_alpha()
                        asset_cache[image_name] = loaded_image
                    except:
                        print(f"Konnte Bild nicht laden: {image_name}")
                        continue
                else:
                    print(f"Bild nicht gefunden: {image_name}")
                    continue
            
            # Füge Objekt hinzu
            image = asset_cache[image_name]
            obj_data = {
                'image': image,
                'x': x,
                'y': y,
                'image_name': image_name
            }
            self.dynamic_objects.append(obj_data)
            
    def _load_decoration_sprites(self):
        """Load decorative sprites (pilz, blume, stone, gold)"""
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'Outdoor decoration')
        
        self.decoration_sprites = {}
        
        # List of decorations to load
        decoration_files = ['pilz.png', 'blume.png', 'blume1.png', 'stone.png', 'gold.png']
        
        for filename in decoration_files:
            filepath = os.path.join(base_dir, filename)
            if os.path.exists(filepath):
                try:
                    sprite = pygame.image.load(filepath).convert_alpha()
                    
                    # Stone und Gold größer machen
                    if filename in ['stone.png', 'gold.png']:
                        original_size = sprite.get_size()
                        scale_factor = 2.5  # 2.5x größer
                        new_width = int(original_size[0] * scale_factor)
                        new_height = int(original_size[1] * scale_factor)
                        sprite = pygame.transform.scale(sprite, (new_width, new_height))
                        print(f"🔍 {filename} skaliert: {original_size} → {(new_width, new_height)}")
                    
                    self.decoration_sprites[filename] = sprite
                    print(f"✅ Loaded decoration: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")
            else:
                print(f"⚠️ Decoration file not found: {filename}")
                
    def _generate_decorations(self):
        """Generate decorative objects on grass areas"""
        if not hasattr(self, 'decoration_sprites'):
            return
            
        self.decorations = []
        
        # Distribution settings
        decoration_densities = {
            'pilz.png': 0.003,    # Pilze seltener
            'blume.png': 0.006,   # Blumen häufiger  
            'blume1.png': 0.006,  # Blumen häufiger
            'stone.png': 0.004,   # Steine mittel
            'gold.png': 0.001     # Gold sehr selten
        }
        
        for decoration_name, density in decoration_densities.items():
            if decoration_name not in self.decoration_sprites:
                continue
                
            sprite = self.decoration_sprites[decoration_name]
            wanted_count = int(self.area_width_tiles * self.area_height_tiles * density)
            
            max_attempts = wanted_count * 10
            attempts = 0
            placed = 0
            
            while placed < wanted_count and attempts < max_attempts:
                attempts += 1
                
                # Random position
                x = random.randint(0, self.width - sprite.get_width())
                y = random.randint(0, self.height - sprite.get_height())
                
                # Check if position is on grass (not water, path, farm)
                tile_x = x // TILE_SIZE
                tile_y = y // TILE_SIZE
                
                if 0 <= tile_x < self.area_width_tiles and 0 <= tile_y < self.area_height_tiles:
                    code = self.overlay[tile_y][tile_x]
                    
                    # Only place on grass (None) areas
                    if code is None:
                        # Check distance from trees (avoid placing too close)
                        too_close_to_tree = False
                        for tree_x, tree_y in self.trees:
                            distance = ((x - tree_x) ** 2 + (y - tree_y) ** 2) ** 0.5
                            if distance < 32:  # Min 32px distance from trees
                                too_close_to_tree = True
                                break
                                
                        if not too_close_to_tree:
                            self.decorations.append({
                                'sprite': sprite,
                                'x': x,
                                'y': y,
                                'name': decoration_name
                            })
                            placed += 1
                            
            print(f"🌿 Placed {placed} {decoration_name} decorations")
