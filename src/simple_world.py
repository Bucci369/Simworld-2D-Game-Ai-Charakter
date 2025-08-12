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
        
        # Portal erstellen (2D-Darstellung da portal.glb 3D ist)
        self.portal_image = self._create_portal_sprite()
        
        self.structures = []
        if self.house_image:
            hx_tiles = center_x + 5
            hy_tiles = center_y - 2
            if 0 <= hx_tiles < tiles_x and 0 <= hy_tiles < tiles_y and self.overlay[hy_tiles][hx_tiles] != 'water':
                self.structures.append(('house', hx_tiles * TILE_SIZE, (hy_tiles+1) * TILE_SIZE - self.house_image.get_height()))
        
        # Portal südlich des Sees platzieren
        if self.portal_image:
            # Finde Südrand des Sees
            portal_x = lake_cx
            portal_y = lake_cy + lake_ry_tiles + 1  # 1 Tile südlich des Sees
            if 0 <= portal_x < tiles_x and 0 <= portal_y < tiles_y and self.overlay[portal_y][portal_x] != 'water':
                self.structures.append(('portal', portal_x * TILE_SIZE, (portal_y+1) * TILE_SIZE - self.portal_image.get_height()))

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

        # 🌲 NEUE WALDGEBIETE: Erstelle dichte Waldgebiete für besseres Gameplay
        self._generate_forest_areas(density)
        
        # Load decorative sprites
        self._load_decoration_sprites()
        
        # Generate decorative objects on grass areas
        self._generate_decorations()
        
        # Vom Debug Panel platzierte dynamische Objekte
        self.dynamic_objects = []  # (image, x, y)
    
    def _create_portal_sprite(self):
        """Erstelle ein 2D Portal-Sprite (da portal.glb 3D ist)"""
        # Erstelle ein animiertes Portal-Sprite
        portal_size = 64
        portal = pygame.Surface((portal_size, portal_size), pygame.SRCALPHA)
        
        # Äußerer Ring (lila/blau)
        pygame.draw.circle(portal, (100, 50, 200), (portal_size//2, portal_size//2), portal_size//2 - 2, 6)
        pygame.draw.circle(portal, (150, 100, 255), (portal_size//2, portal_size//2), portal_size//2 - 8, 4)
        
        # Innerer Bereich (dunkel mit Sternen-Effekt)
        pygame.draw.circle(portal, (20, 10, 50), (portal_size//2, portal_size//2), portal_size//2 - 12)
        
        # Glitzer-Effekte (kleine weiße Punkte)
        import random
        random.seed(42)  # Für konsistente Darstellung
        for _ in range(8):
            x = random.randint(portal_size//4, 3*portal_size//4)
            y = random.randint(portal_size//4, 3*portal_size//4)
            pygame.draw.circle(portal, (255, 255, 255), (x, y), 2)
        
        # Zentrum (hell leuchtend)
        pygame.draw.circle(portal, (200, 150, 255), (portal_size//2, portal_size//2), 8)
        pygame.draw.circle(portal, (255, 255, 255), (portal_size//2, portal_size//2), 4)
        
        return portal

    def _generate_forest_areas(self, base_density):
        """Erstelle 3-4 dichte Waldgebiete in der Welt"""
        self.trees = []
        
        # 🌲 WALDGEBIETE: Definiere 6-8 Waldgebiete für größere Welt
        forest_areas = [
            # Nordwest-Wald (oben links)
            {'center': (self.width * 0.15, self.height * 0.15), 'radius': 200, 'density': 0.3},
            # Nordost-Wald (oben rechts) 
            {'center': (self.width * 0.85, self.height * 0.15), 'radius': 180, 'density': 0.25},
            # Südwest-Wald (unten links) - größer, da Spieler hier spawnt
            {'center': (self.width * 0.2, self.height * 0.8), 'radius': 250, 'density': 0.35},
            # Südost-Wald (unten rechts)
            {'center': (self.width * 0.8, self.height * 0.85), 'radius': 220, 'density': 0.3},
            # Zentral-Wald (Mitte)
            {'center': (self.width * 0.5, self.height * 0.3), 'radius': 160, 'density': 0.25},
            # West-Wald (links mitte)
            {'center': (self.width * 0.1, self.height * 0.5), 'radius': 140, 'density': 0.2},
            # Ost-Wald (rechts mitte)  
            {'center': (self.width * 0.9, self.height * 0.6), 'radius': 160, 'density': 0.25},
            # Süd-Zentral-Wald (unten mitte)
            {'center': (self.width * 0.6, self.height * 0.7), 'radius': 130, 'density': 0.2},
        ]
        
        print(f"🌲 Erstelle {len(forest_areas)} Waldgebiete...")
        
        for forest in forest_areas:
            center_x, center_y = forest['center']
            radius = forest['radius']
            density = forest['density']
            
            # Berechne Anzahl Bäume für dieses Waldgebiet
            area_size = 3.14159 * radius * radius  # Kreisfläche
            trees_in_forest = int(area_size / (TILE_SIZE * TILE_SIZE) * density)
            
            print(f"  🌳 Waldgebiet bei ({int(center_x)}, {int(center_y)}) - Radius: {radius}, Bäume: {trees_in_forest}")
            
            attempts = 0
            trees_placed = 0
            max_attempts = trees_in_forest * 10
            
            while trees_placed < trees_in_forest and attempts < max_attempts:
                attempts += 1
                
                # Zufällige Position im Kreis
                angle = random.uniform(0, 2 * 3.14159)
                distance = random.uniform(0, radius)
                
                tx = int(center_x + distance * random.uniform(-1, 1))
                ty = int(center_y + distance * random.uniform(-1, 1))
                
                # Prüfe Grenzen
                if (tx < 0 or ty < 0 or 
                    tx > self.width - self.oak_tree.get_width() or 
                    ty > self.height - self.oak_tree.get_height()):
                    continue
                
                # Prüfe Überlappung mit Features
                tile_x = tx // TILE_SIZE
                tile_y = ty // TILE_SIZE
                if 0 <= tile_x < self.area_width_tiles and 0 <= tile_y < self.area_height_tiles:
                    code = self.overlay[tile_y][tile_x]
                    if code in ('water', 'path', 'farm'):
                        continue
                
                # Prüfe Abstand zu anderen Bäumen (mindestens 30 Pixel)
                too_close = False
                for existing_x, existing_y in self.trees:
                    distance_to_existing = ((tx - existing_x)**2 + (ty - existing_y)**2) ** 0.5
                    if distance_to_existing < 30:
                        too_close = True
                        break
                
                if not too_close:
                    self.trees.append((tx, ty))
                    trees_placed += 1
        
        # Zusätzlich verstreute Einzelbäume für Sammler
        scattered_trees = int(self.area_width_tiles * self.area_height_tiles * base_density * 0.3)
        print(f"🌿 Zusätzlich {scattered_trees} verstreute Bäume...")
        
        attempts = 0
        max_attempts = scattered_trees * 5
        while len(self.trees) - sum(int(area['radius']**2 * 3.14159 / (TILE_SIZE**2) * area['density']) for area in forest_areas) < scattered_trees and attempts < max_attempts:
            attempts += 1
            tx = random.randint(0, self.width - self.oak_tree.get_width())
            ty = random.randint(0, self.height - self.oak_tree.get_height())
            tile_x = tx // TILE_SIZE
            tile_y = ty // TILE_SIZE
            if 0 <= tile_x < self.area_width_tiles and 0 <= tile_y < self.area_height_tiles:
                code = self.overlay[tile_y][tile_x]
                if code in ('water', 'path', 'farm'):
                    continue
            
            # Prüfe Abstand zu anderen Bäumen
            too_close = False
            for existing_x, existing_y in self.trees:
                distance_to_existing = ((tx - existing_x)**2 + (ty - existing_y)**2) ** 0.5
                if distance_to_existing < 25:
                    too_close = True
                    break
                    
            if not too_close:
                self.trees.append((tx, ty))

        self.trees.sort(key=lambda p: p[1])  # painter's order
        print(f"🌲 Insgesamt {len(self.trees)} Bäume in der Welt platziert!")
        
        # Load decorative sprites
        self._load_decoration_sprites()
        
        # Generate decorative objects on grass areas
        self._generate_decorations()
        
        # Vom Debug Panel platzierte dynamische Objekte
        self.dynamic_objects = []  # (image, x, y)
        
        # Drag & Drop System
        self.selected_object = None  # Aktuell ausgewähltes Objekt
        self.dragging = False        # Gerade am Ziehen
        self.drag_offset = (0, 0)    # Offset zwischen Maus und Objektmitte

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
        
        # Strukturen (Haus, Portal) vor Bäumen oder nach Bedarf sortieren
        if self.structures:
            for structure in self.structures:
                structure_type, sx, sy = structure
                if structure_type == 'house' and self.house_image:
                    rect = pygame.Rect(sx, sy, self.house_image.get_width(), self.house_image.get_height())
                    if rect.colliderect(view_rect):
                        surface.blit(self.house_image, (sx - camera_rect.left, sy - camera_rect.top))
                elif structure_type == 'portal' and self.portal_image:
                    rect = pygame.Rect(sx, sy, self.portal_image.get_width(), self.portal_image.get_height())
                    if rect.colliderect(view_rect):
                        surface.blit(self.portal_image, (sx - camera_rect.left, sy - camera_rect.top))
        # Dynamische Objekte (sortiert nach y für Zeichnungsreihenfolge)
        # Bereinige alte/ungültige Objekte (Memory Leak Fix)
        if len(self.dynamic_objects) > 100:  # Begrenze auf max 100 Objekte
            self.dynamic_objects = self.dynamic_objects[-50:]  # Behalte nur die letzten 50
        
        for i, obj in enumerate(sorted(self.dynamic_objects, key=lambda e: e['y'])):
            img, ox, oy = obj['image'], obj['x'], obj['y']
            rect = pygame.Rect(ox, oy, img.get_width(), img.get_height())
            if rect.colliderect(view_rect):
                surface.blit(img, (ox - camera_rect.left, oy - camera_rect.top))
                
                # Zeige Auswahl-Rahmen für ausgewähltes/gezogenes Objekt
                if self.selected_object and self.selected_object[1] == i:
                    # Zeichne Auswahl-Rahmen
                    screen_rect = pygame.Rect(ox - camera_rect.left - 2, oy - camera_rect.top - 2, 
                                            img.get_width() + 4, img.get_height() + 4)
                    if self.dragging:
                        pygame.draw.rect(surface, (255, 255, 0), screen_rect, 3)  # Gelb beim Ziehen
                    else:
                        pygame.draw.rect(surface, (0, 255, 0), screen_rect, 2)    # Grün bei Auswahl
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
        
        # Asset-Cache für bereits geladene Bilder (mit Memory Management)
        if not hasattr(self, '_asset_cache'):
            self._asset_cache = {}
        
        for obj_data in objects_data:
            image_name = obj_data.get('image_name', 'unknown.png')
            x = obj_data['x']
            y = obj_data['y']
            
            # Lade Bild falls noch nicht im Cache
            if image_name not in self._asset_cache:
                # Cache-Größe begrenzen (max 50 Assets)
                if len(self._asset_cache) > 50:
                    # Entferne älteste Einträge
                    keys_to_remove = list(self._asset_cache.keys())[:10]
                    for key in keys_to_remove:
                        del self._asset_cache[key]
                
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
                        self._asset_cache[image_name] = loaded_image
                    except:
                        print(f"Konnte Bild nicht laden: {image_name}")
                        continue
                else:
                    print(f"Bild nicht gefunden: {image_name}")
                    continue
            
            # Füge Objekt hinzu
            image = self._asset_cache[image_name]
            obj_data = {
                'image': image,
                'x': x,
                'y': y,
                'image_name': image_name
            }
            self.dynamic_objects.append(obj_data)
    
    def cleanup_cache(self):
        """Bereinigt den Asset-Cache"""
        if hasattr(self, '_asset_cache'):
            self._asset_cache.clear()
    
    def get_object_at_position(self, world_pos):
        """Findet das oberste Objekt an einer Weltposition"""
        x, y = world_pos
        
        # Prüfe dynamic_objects (von hinten nach vorne für oberste Ebene)
        for i in range(len(self.dynamic_objects) - 1, -1, -1):
            obj = self.dynamic_objects[i]
            obj_rect = pygame.Rect(obj['x'], obj['y'], obj['image'].get_width(), obj['image'].get_height())
            if obj_rect.collidepoint(x, y):
                return ('dynamic', i, obj)
        
        return None
    
    def start_drag(self, world_pos):
        """Startet Drag & Drop für Objekt an Position"""
        object_info = self.get_object_at_position(world_pos)
        if object_info:
            obj_type, obj_index, obj_data = object_info
            self.selected_object = object_info
            self.dragging = True
            # Berechne Offset zwischen Mausposition und Objektmitte
            obj_center_x = obj_data['x'] + obj_data['image'].get_width() // 2
            obj_center_y = obj_data['y'] + obj_data['image'].get_height() // 2
            self.drag_offset = (world_pos[0] - obj_center_x, world_pos[1] - obj_center_y)
            return True
        return False
    
    def update_drag(self, world_pos):
        """Aktualisiert Position des gezogenen Objekts"""
        if self.dragging and self.selected_object:
            obj_type, obj_index, obj_data = self.selected_object
            if obj_type == 'dynamic':
                # Neue Position mit Offset
                new_center_x = world_pos[0] - self.drag_offset[0]
                new_center_y = world_pos[1] - self.drag_offset[1]
                
                # Konvertiere zu Objekt-Ursprung (oben links)
                new_x = new_center_x - obj_data['image'].get_width() // 2
                new_y = new_center_y - obj_data['image'].get_height() // 2
                
                # Aktualisiere Objektposition
                self.dynamic_objects[obj_index]['x'] = new_x
                self.dynamic_objects[obj_index]['y'] = new_y
    
    def end_drag(self):
        """Beendet Drag & Drop"""
        self.dragging = False
        self.selected_object = None
        self.drag_offset = (0, 0)
    
    def delete_selected_object(self):
        """Löscht das aktuell ausgewählte Objekt"""
        if self.selected_object:
            obj_type, obj_index, obj_data = self.selected_object
            if obj_type == 'dynamic':
                del self.dynamic_objects[obj_index]
                print(f"🗑️ Objekt {obj_data.get('image_name', 'unknown')} gelöscht")
            self.selected_object = None
            return True
        return False
            
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
