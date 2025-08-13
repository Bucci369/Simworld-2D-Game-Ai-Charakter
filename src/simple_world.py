import random
import os
import math
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
from asset_manager import asset_manager

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

        # 🚀 PERFORMANCE: Asset-Manager für gecachte Tiles
        print("🎯 Loading world assets with caching...")
        self.grass_tile = asset_manager.load_scaled_image('Tiles/Grass_Middle.png', (TILE_SIZE, TILE_SIZE))
        self.oak_tree = asset_manager.load_image('Outdoor decoration/Oak_Tree.png')
        self.farmland_tile = asset_manager.load_scaled_image('Tiles/FarmLand_Tile.png', (TILE_SIZE, TILE_SIZE))
        self.water_tile = asset_manager.load_scaled_image('Tiles/Water_Middle.png', (TILE_SIZE, TILE_SIZE))
        self.path_tile = asset_manager.load_scaled_image('Tiles/Path_Middle.png', (TILE_SIZE, TILE_SIZE))

        # 🚀 PERFORMANCE: Pre-render Background komplett für bessere FPS
        print("🎯 Pre-rendering world background...")
        self.background = self._create_optimized_background()

        # ALTE Logik entfernt - wird jetzt in _create_optimized_background() gemacht
        center_x = tiles_x // 2
        center_y = tiles_y // 2
        
        # Weg rund um den See (wird teilweise überschrieben)
        lake_rx_tiles, lake_ry_tiles = SIMPLE_WORLD_LAKE_RADII
        lake_cx = int(SIMPLE_WORLD_LAKE_CENTER_REL[0] * tiles_x)
        lake_cy = int(SIMPLE_WORLD_LAKE_CENTER_REL[1] * tiles_y)
        
        # Hauptweg: Von Westen nach Osten durch die Mitte, um den See herum
        for tx in range(tiles_x):
            # Weg um den See herum führen
            if tx < lake_cx - lake_rx_tiles - 2:
                # Links vom See - gerader Weg
                self.overlay[center_y][tx] = 'path'
            elif tx > lake_cx + lake_rx_tiles + 2:
                # Rechts vom See - gerader Weg
                self.overlay[center_y][tx] = 'path'
            else:
                # Am See vorbei - Weg nach Norden um den See
                path_y = max(2, lake_cy - lake_ry_tiles - 3)
                if 0 <= path_y < tiles_y:
                    self.overlay[path_y][tx] = 'path'
        
        # Verbindungsweg von Hauptweg nach Süden um den See
        for tx in range(max(0, lake_cx - lake_rx_tiles - 2), min(tiles_x, lake_cx + lake_rx_tiles + 3)):
            path_y = min(tiles_y - 3, lake_cy + lake_ry_tiles + 3)
            if 0 <= path_y < tiles_y:
                self.overlay[path_y][tx] = 'path'
        
        # Vertikale Verbindungswege
        # Westlicher Verbindungsweg
        west_x = max(2, lake_cx - lake_rx_tiles - 6)
        for ty in range(tiles_y):
            if 0 <= west_x < tiles_x:
                self.overlay[ty][west_x] = 'path'
                
        # Östlicher Verbindungsweg  
        east_x = min(tiles_x - 3, lake_cx + lake_rx_tiles + 6)
        for ty in range(tiles_y):
            if 0 <= east_x < tiles_x:
                self.overlay[ty][east_x] = 'path'
        
        # Weg um den See herum (Seepromenade)
        for angle in range(0, 360, 6):  # Alle 6 Grad ein Punkt
            rad = math.radians(angle)
            # Etwas größerer Radius als der See für den Weg
            path_x = int(lake_cx + (lake_rx_tiles + 2) * math.cos(rad))
            path_y = int(lake_cy + (lake_ry_tiles + 2) * math.sin(rad))
            if 0 <= path_x < tiles_x and 0 <= path_y < tiles_y:
                self.overlay[path_y][path_x] = 'path'

        # Lake (ellipse) - nur der See
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
        
                # 🌲 WALDGEBIETE: Normale Waldgebiete für 50x50 Welt - KOMPAKT UM SPIELER
        forest_areas = [
            # Nordwest-Wald (oben links)
            {'center': (self.width * 0.2, self.height * 0.2), 'radius': 120, 'density': 0.3},
            # Nordost-Wald (oben rechts) 
            {'center': (self.width * 0.8, self.height * 0.2), 'radius': 100, 'density': 0.25},
            # Südwest-Wald (unten links)
            {'center': (self.width * 0.2, self.height * 0.8), 'radius': 140, 'density': 0.35},
            # Südost-Wald (unten rechts)
            {'center': (self.width * 0.8, self.height * 0.8), 'radius': 110, 'density': 0.3},
            # Zentral-West (links)
            {'center': (self.width * 0.15, self.height * 0.5), 'radius': 80, 'density': 0.25},
            # Zentral-Ost (rechts)
            {'center': (self.width * 0.85, self.height * 0.5), 'radius': 90, 'density': 0.3},
            # Nord-Zentral (oben mitte)
            {'center': (self.width * 0.5, self.height * 0.15), 'radius': 80, 'density': 0.3},
            # Zentral-Süd-Wald (unten mitte)
            {'center': (self.width * 0.5, self.height * 0.85), 'radius': 90, 'density': 0.35},
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
                
                # Prüfe Abstand zu anderen Bäumen - REDUZIERTER Abstand für dichtere Wälder
                min_distance = 25  # Reduziert von 30 auf 25 Pixel für dichtere Wälder
                too_close = False
                for existing_x, existing_y in self.trees:
                    distance_to_existing = ((tx - existing_x)**2 + (ty - existing_y)**2) ** 0.5
                    if distance_to_existing < min_distance:
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

    def _load_mountain_asset(self):
        """Lade Berg-Asset oder erstelle Platzhalter"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        mountain_paths = [
            'assets/Outdoor decoration/stone.png',
            'assets/Tiles/stone.png', 
            'assets/stein.png'
        ]
        
        for path in mountain_paths:
            full_path = os.path.join(base_dir, path)
            if os.path.exists(full_path):
                try:
                    sprite = pygame.image.load(full_path).convert_alpha()
                    return pygame.transform.scale(sprite, (TILE_SIZE, TILE_SIZE))
                except Exception:
                    continue
        
        # Fallback: Erstelle grauen Berg-Tile
        mountain_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        mountain_tile.fill((80, 80, 90))  # Dunkelgrau für Berge
        # Berg-Textur hinzufügen
        for y in range(0, TILE_SIZE, 4):
            for x in range(0, TILE_SIZE, 4):
                if random.random() < 0.3:
                    pygame.draw.rect(mountain_tile, (60, 60, 70), (x, y, 2, 2))
        return mountain_tile
    
    def _load_stone_asset(self):
        """Lade Stein-Asset oder erstelle Platzhalter"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        stone_paths = [
            'assets/Outdoor decoration/stone_deco.png',
            'assets/stone_deco.png'
        ]
        
        for path in stone_paths:
            full_path = os.path.join(base_dir, path)
            if os.path.exists(full_path):
                try:
                    sprite = pygame.image.load(full_path).convert_alpha()
                    return pygame.transform.scale(sprite, (TILE_SIZE, TILE_SIZE))
                except Exception:
                    continue
                    
        # Fallback: Erstelle steinigen Tile
        stone_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        stone_tile.fill((120, 120, 100))  # Heller als Berge
        # Stein-Textur
        for y in range(0, TILE_SIZE, 3):
            for x in range(0, TILE_SIZE, 3):
                if random.random() < 0.4:
                    pygame.draw.rect(stone_tile, (100, 100, 80), (x, y, 2, 2))
        return stone_tile

    def _create_mountain_ranges(self, tiles_x, tiles_y):
        """Erstelle kompakte Bergketten in 50x50 Welt"""
        
        # 🏔️ NORDWEST-BERGKETTE (oben links) - kompakter
        nw_center_x = int(tiles_x * 0.15)
        nw_center_y = int(tiles_y * 0.1)
        self._create_mountain_cluster(nw_center_x, nw_center_y, 8, tiles_x, tiles_y)
        
        # 🏔️ NORDOST-BERGKETTE (oben rechts) - kompakter
        ne_center_x = int(tiles_x * 0.85)
        ne_center_y = int(tiles_y * 0.15)
        self._create_mountain_cluster(ne_center_x, ne_center_y, 6, tiles_x, tiles_y)
        
        # 🏔️ SÜDWEST-BERGKETTE (unten links) - klein
        sw_center_x = int(tiles_x * 0.1)
        sw_center_y = int(tiles_y * 0.9)
        self._create_mountain_cluster(sw_center_x, sw_center_y, 5, tiles_x, tiles_y)
        
        # 🏔️ SÜDOST-BERGKETTE (unten rechts) - klein
        se_center_x = int(tiles_x * 0.9)
        se_center_y = int(tiles_y * 0.85)
        self._create_mountain_cluster(se_center_x, se_center_y, 6, tiles_x, tiles_y)
        
        print(f"🏔️ Kompakte Bergketten erstellt: 4 Bereiche für 50x50 Welt")

    def _create_mountain_cluster(self, center_x, center_y, size, tiles_x, tiles_y):
        """Erstelle einen Berg-Cluster um einen Mittelpunkt"""
        for ty in range(max(0, center_y - size), min(tiles_y, center_y + size)):
            for tx in range(max(0, center_x - size), min(tiles_x, center_x + size)):
                distance = ((tx - center_x) ** 2 + (ty - center_y) ** 2) ** 0.5
                
                if distance <= size:
                    # Berg-Wahrscheinlichkeit basierend auf Entfernung vom Zentrum
                    mountain_chance = max(0, 1.0 - (distance / size))
                    mountain_chance = mountain_chance ** 2  # Quadratisch für natürlichere Form
                    
                    if random.random() < mountain_chance:
                        if mountain_chance > 0.7:
                            self.overlay[ty][tx] = 'mountain'  # Hohe Berge
                        elif mountain_chance > 0.3:
                            self.overlay[ty][tx] = 'stone'  # Steinige Hügel
                        # Sonst bleibt es Gras für sanfte Übergänge

    def _create_winding_river(self, tiles_x, tiles_y):
        """Erstelle einen kompakten schlängelnden Fluss in 50x50 Welt"""
        
        # 🌊 FLUSS-PARAMETER - kompakter für 50x50 Welt
        # Startpunkt: Links mitte
        start_x = int(tiles_x * 0.1)
        start_y = int(tiles_y * 0.3)
        
        # Endpunkt: Rechts mitte 
        end_x = int(tiles_x * 0.9)
        end_y = int(tiles_y * 0.7)
        
        # Erstelle Fluss-Pfad mit Schlängelung
        river_points = []
        steps = 40  # Weniger Punkte für kompakte Welt
        
        for i in range(steps + 1):
            t = i / steps  # 0.0 bis 1.0
            
            # Grundlinie von Start zu Ende
            base_x = start_x + (end_x - start_x) * t
            base_y = start_y + (end_y - start_y) * t
            
            # Schlängelung hinzufügen (weniger stark für kompakte Welt)
            amplitude = 6  # Reduziert für 50x50 Welt
            wavelength = 3  # Weniger Windungen
            
            offset_x = amplitude * random.uniform(-0.5, 0.5) * math.sin(t * wavelength * math.pi)
            offset_y = amplitude * random.uniform(-0.3, 0.3) * math.cos(t * wavelength * math.pi)
            
            river_x = int(base_x + offset_x)
            river_y = int(base_y + offset_y)
            
            # Grenzen prüfen
            river_x = max(0, min(tiles_x - 1, river_x))
            river_y = max(0, min(tiles_y - 1, river_y))
            
            river_points.append((river_x, river_y))
        
        # Fluss-Tiles platzieren
        river_width = 1  # Schmaler für kompakte Welt
        
        for i, (rx, ry) in enumerate(river_points):
            # Haupt-Fluss-Tile
            if self.overlay[ry][rx] != 'mountain':  # Nicht über Berge
                self.overlay[ry][rx] = 'water'
            
            # Fluss-Breite hinzufügen
            for dy in range(-river_width, river_width + 1):
                for dx in range(-river_width, river_width + 1):
                    tx = rx + dx
                    ty = ry + dy
                    
                    if 0 <= tx < tiles_x and 0 <= ty < tiles_y:
                        distance = (dx**2 + dy**2)**0.5
                        if distance <= river_width:
                            if self.overlay[ty][tx] != 'mountain':  # Berge blockieren Fluss
                                # Wahrscheinlichkeit basierend auf Entfernung von Flussmitte
                                water_chance = max(0, 1.0 - (distance / river_width)) if river_width > 0 else 1.0
                                if random.random() < water_chance * 0.8:  # 80% Chance für Wasser
                                    self.overlay[ty][tx] = 'water'
        
        print(f"🌊 Kompakter Fluss erstellt: {len(river_points)} Punkte von ({start_x},{start_y}) nach ({end_x},{end_y})")

        # 🌊 KLEINE BÄCHE von Bergen (weniger für kompakte Welt)
        self._create_mountain_streams(tiles_x, tiles_y)

    def _create_mountain_streams(self, tiles_x, tiles_y):
        """Erstelle kleine Bäche die von Bergen zum Hauptfluss fließen"""
        
        # Finde Berg-Bereiche und erstelle Bäche
        mountain_areas = []
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                if self.overlay[ty][tx] == 'mountain':
                    mountain_areas.append((tx, ty))
        
        # Erstelle 3-4 kleine Bäche von Bergen
        stream_count = 4
        for i in range(stream_count):
            if not mountain_areas:
                break
                
            # Wähle zufälligen Berg als Startpunkt
            start_mountain = random.choice(mountain_areas)
            mx, my = start_mountain
            
            # Erstelle kurzen Bach (10-15 Tiles lang)
            stream_length = random.randint(8, 12)
            
            current_x, current_y = mx, my
            for step in range(stream_length):
                # Bewege Richtung Hauptfluss (leicht zufällig)
                direction_x = random.choice([-1, 0, 1])
                direction_y = random.choice([-1, 0, 1])
                
                current_x += direction_x
                current_y += direction_y
                
                # Grenzen prüfen
                current_x = max(0, min(tiles_x - 1, current_x))
                current_y = max(0, min(tiles_y - 1, current_y))
                
                # Bach-Tile platzieren (nur wenn nicht Berg)
                if self.overlay[current_y][current_x] != 'mountain':
                    if random.random() < 0.6:  # 60% Chance für Wasser-Tile
                        self.overlay[current_y][current_x] = 'water'
        
        print(f"🏞️ {stream_count} Berg-Bäche erstellt")
