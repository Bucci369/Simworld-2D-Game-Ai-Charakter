import os
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, MAP_PATH, TITLE, USE_SIMPLE_WORLD, FULLSCREEN, DEBUG_PANEL_WIDTH, TILE_SIZE
from map_loader import TiledMap, Camera
from simple_world import SimpleWorld
from player import Player
from time_system import GameTime
from farming_system import FarmingSystem
from farm_ui import FarmUI
from inventory import Inventory
from hunger_system import HungerSystem
from tree_system import TreeSystem
from pygame import KMOD_SHIFT

# Debug Panel (lazy import of assets)
class DebugPanel:
    def __init__(self, screen_height):
        import pygame
        self.visible = True  # Standardmäßig sichtbar
        self.width = DEBUG_PANEL_WIDTH
        self.surface = pygame.Surface((self.width, screen_height), pygame.SRCALPHA)
        self.font = pygame.font.SysFont('Arial', 14)
        self.assets = []  # list of dict(name, image, thumb)
        self.selected = None
        self.scroll = 0
        self.entry_h = 48
        self.current_frame = 0  # Welcher Frame des Sprite-Sheets gerade angezeigt wird
        if True:  # auto scan
            self.scan_assets()

    def toggle(self):
        self.visible = not self.visible

    def is_mouse_over(self, mx, my, screen_width):
        if not self.visible:
            return False
        return mx >= screen_width - self.width

    def scan_assets(self, max_files=120):
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
        self.assets = []
        for root, _, files in os.walk(base_dir):
            for f in files:
                if len(self.assets) >= max_files:
                    break
                if not f.lower().endswith('.png'):
                    continue
                path = os.path.join(root, f)
                try:
                    full_img = pygame.image.load(path).convert_alpha()
                    w, h = full_img.get_size()
                    
                    frames = []
                    
                    # Intelligente Sprite-Sheet Erkennung basierend auf Dateiname und Struktur
                    is_likely_sheet = self._is_likely_sprite_sheet(f, w, h)
                    
                    if not is_likely_sheet:
                        # Definitiv kein Sprite-Sheet, als einzelnes Bild behandeln
                        frames.append(full_img)
                    elif w > h and w % h == 0 and w // h >= 2:
                        # Horizontales Sprite-Sheet (nur wenn wahrscheinlich ein Sheet)
                        frame_count = w // h
                        frame_width = h
                        
                        # Prüfe ob es sich wirklich um verschiedene Frames handelt
                        first_frame = pygame.Surface((frame_width, h), pygame.SRCALPHA)
                        first_frame.blit(full_img, (0, 0), (0, 0, frame_width, h))
                        
                        if frame_count >= 2:
                            second_frame = pygame.Surface((frame_width, h), pygame.SRCALPHA)
                            second_frame.blit(full_img, (0, 0), (frame_width, 0, frame_width, h))
                            
                            frames_different = self._frames_are_different(first_frame, second_frame)
                            
                            if frames_different:
                                # Echtes Sprite-Sheet: Alle Frames extrahieren
                                for i in range(min(4, frame_count)):
                                    frame = pygame.Surface((frame_width, h), pygame.SRCALPHA)
                                    frame.blit(full_img, (0, 0), (i * frame_width, 0, frame_width, h))
                                    frames.append(frame)
                            else:
                                # Gleiche Frames: Behandle als einzelnes Bild
                                frames.append(full_img)
                        else:
                            frames.append(full_img)
                            
                    elif h > w and h % w == 0 and h // w >= 2:
                        # Vertikales Sprite-Sheet (nur wenn wahrscheinlich ein Sheet)
                        frame_count = h // w
                        frame_height = w
                        
                        first_frame = pygame.Surface((w, frame_height), pygame.SRCALPHA)
                        first_frame.blit(full_img, (0, 0), (0, 0, w, frame_height))
                        
                        if frame_count >= 2:
                            second_frame = pygame.Surface((w, frame_height), pygame.SRCALPHA)
                            second_frame.blit(full_img, (0, 0), (0, frame_height, w, frame_height))
                            
                            frames_different = self._frames_are_different(first_frame, second_frame)
                            
                            if frames_different:
                                # Echtes Sprite-Sheet: Alle Frames extrahieren
                                for i in range(min(4, frame_count)):
                                    frame = pygame.Surface((w, frame_height), pygame.SRCALPHA)
                                    frame.blit(full_img, (0, 0), (0, i * frame_height, w, frame_height))
                                    frames.append(frame)
                            else:
                                frames.append(full_img)
                        else:
                            frames.append(full_img)
                            
                    elif is_likely_sheet and min(w, h) >= 32:
                        # Erweiterte Grid-Erkennung für Asset-Sammlungen
                        best_grid = None
                        best_score = 0
                        
                        # Teste verschiedene Grid-Größen systematisch - suche vollständige Items
                        for rows in range(2, 20):  # Bis zu 20 Reihen für kleine Items
                            for cols in range(2, 20):  # Bis zu 20 Spalten für kleine Items
                                if w % cols == 0 and h % rows == 0:
                                    frame_w = w // cols
                                    frame_h = h // rows
                                    
                                    # Kleinere Items erlauben, aber nicht zu klein
                                    if frame_w >= 12 and frame_h >= 12 and frame_w <= 64 and frame_h <= 64:
                                        total_frames = rows * cols
                                        
                                        # Teste die ersten paar Items auf Unterschiede
                                        different_count = 0
                                        comparisons = 0
                                        
                                        # Teste nur die ersten paar Items statt das ganze Grid
                                        test_positions = [
                                            (0, 0), (1, 0), (0, 1), (1, 1),
                                            (2, 0) if cols > 2 else None,
                                            (0, 2) if rows > 2 else None,
                                            (2, 1) if cols > 2 and rows > 1 else None
                                        ]
                                        test_positions = [p for p in test_positions if p is not None]
                                        
                                        frame1 = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                                        frame1.blit(full_img, (0, 0), (0, 0, frame_w, frame_h))
                                        
                                        for test_col, test_row in test_positions[1:]:  # Skip first position
                                            if test_col < cols and test_row < rows:
                                                frame2 = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                                                frame2.blit(full_img, (0, 0), (test_col * frame_w, test_row * frame_h, frame_w, frame_h))
                                                
                                                comparisons += 1
                                                if self._frames_are_different(frame1, frame2, threshold=0.03):
                                                    different_count += 1
                                        
                                        # Bewerte das Grid: mehr unterschiedliche Items = besser, aber bevorzuge kleinere, gleichmäßige Frames
                                        if comparisons > 0 and different_count >= comparisons * 0.6:  # 60% müssen unterschiedlich sein
                                            # Score basiert auf Item-Gleichmäßigkeit und Anzahl unterschiedlicher Items
                                            size_score = 1.0 / (abs(frame_w - frame_h) + 1)  # Bevorzuge quadratische Items
                                            diff_score = different_count / comparisons
                                            total_score = size_score * diff_score * different_count
                                            
                                            if total_score > best_score:
                                                best_score = total_score
                                                best_grid = (rows, cols, frame_w, frame_h)
                        
                        if best_grid:
                            rows, cols, frame_w, frame_h = best_grid
                            # Extrahiere alle Grid-Elemente
                            for row in range(rows):
                                for col in range(cols):
                                    frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                                    frame.blit(full_img, (0, 0), (col * frame_w, row * frame_h, frame_w, frame_h))
                                    frames.append(frame)
                            print(f"Optimales Grid für {f}: {rows}x{cols} = {len(frames)} Items (Größe: {frame_w}x{frame_h})")
                        else:
                            # Fallback: Als einzelnes Bild behandeln
                            frames.append(full_img)
                            print(f"Kein passendes Grid für {f}, als einzelnes Bild behandelt")
                    else:
                        # Einzelnes Bild (Standard)
                        frames.append(full_img)
                    
                    # Wenn keine Frames erkannt wurden, nimm das ganze Bild
                    if not frames:
                        frames.append(full_img)
                    
                    # Erstelle Thumbnails für alle Frames
                    thumbs = []
                    for frame in frames:
                        fw, fh = frame.get_size()
                        scale = min(40/max(1,fw), 40/max(1,fh), 1)
                        thumb = pygame.transform.smoothscale(frame, (int(fw*scale), int(fh*scale))) if scale != 1 else frame
                        thumbs.append(thumb)
                    
                    self.assets.append({
                        'name': f, 
                        'frames': frames,  # Alle Frames
                        'thumbs': thumbs   # Alle Thumbnails
                    })
                    
                except Exception:
                    continue
            if len(self.assets) >= max_files:
                break

    def _frames_are_different(self, frame1, frame2, threshold=0.05):
        """Prüft ob zwei Frames signifikant unterschiedlich sind"""
        try:
            # Konvertiere zu Arrays für Vergleich
            arr1 = pygame.surfarray.array3d(frame1)
            arr2 = pygame.surfarray.array3d(frame2)
            
            # Berechne den Unterschied
            if arr1.shape != arr2.shape:
                return True
                
            # Berechne prozentuale Unterschiede
            diff = abs(arr1.astype(float) - arr2.astype(float))
            total_diff = diff.sum()
            max_possible_diff = arr1.size * 255
            
            difference_ratio = total_diff / max_possible_diff
            return difference_ratio > threshold
            
        except Exception:
            # Falls Vergleich fehlschlägt, nimm an dass sie unterschiedlich sind
            return True
    
    def _is_likely_sprite_sheet(self, filename, w, h):
        """Prüft anhand von Dateiname und Dimensionen ob es ein Sprite-Sheet ist"""
        filename_lower = filename.lower()
        
        # Dateinamen die definitiv Sprite-Sheets sind
        sprite_indicators = [
            'sheet', 'sprite', 'animation', 'anim', 'frames', 'walk', 'run', 
            'idle', 'attack', 'death', 'actions', 'character', 'player'
        ]
        
        # Dateinamen die definitiv KEINE Sprite-Sheets sind
        single_indicators = [
            'tree', 'baum', 'house', 'haus', 'chest', 'kiste', 'rock', 'stein',
            'fence', 'zaun', 'bridge', 'brücke', 'decor', 'decoration', 'prop',
            'static', 'building', 'gebäude', 'item', 'object', 'obj'
        ]
        
        # Dateinamen die Asset-Sammlungen/Tilesets sind (sollten aufgeteilt werden)
        tileset_indicators = [
            'farm', 'tileset', 'tiles', 'collection', 'sammlung', 'set', 'pack',
            'outdoor', 'indoor', 'props', 'items', 'objects', 'vegetation', 'food'
        ]
        
        # Prüfe auf eindeutige Indikatoren
        for indicator in sprite_indicators:
            if indicator in filename_lower:
                return True
                
        for indicator in single_indicators:
            if indicator in filename_lower:
                return False
        
        # Prüfe auf Tileset/Asset-Sammlungen
        for indicator in tileset_indicators:
            if indicator in filename_lower:
                return True  # Diese sollten aufgeteilt werden
        
        # Dimensionsbasierte Heuristiken
        aspect_ratio = max(w, h) / min(w, h)
        
        # Sehr breite oder hohe Bilder sind wahrscheinlich Sprite-Sheets
        if aspect_ratio >= 4:
            return True
            
        # Perfekte 2er, 3er oder 4er Teilungen könnten Sprite-Sheets sein
        if w > h and w % h == 0:
            frames = w // h
            if frames in [2, 3, 4, 8]:
                return True
                
        if h > w and h % w == 0:
            frames = h // w
            if frames in [2, 3, 4, 8]:
                return True
        
        # 2x2 Grids bei quadratischen Bildern
        if abs(w - h) <= min(w, h) * 0.1:  # Fast quadratisch
            if w % 2 == 0 and h % 2 == 0 and min(w, h) >= 64:
                return True
        
        return False

    def handle_event(self, event, screen_width):
        # Tastatur-Events für Frame-Auswahl (auch wenn Panel nicht sichtbar ist)
        if event.type == pygame.KEYDOWN:
            if event.key >= pygame.K_1 and event.key <= pygame.K_9:
                frame_num = event.key - pygame.K_1  # 0-8
                if self.selected is not None and 0 <= self.selected < len(self.assets):
                    asset = self.assets[self.selected]
                    if frame_num < len(asset['frames']):
                        self.current_frame = frame_num
                        print(f"Frame {frame_num + 1} ausgewählt für {asset['name']}")
            elif event.key == pygame.K_0:
                # Taste 0 für Frame 10
                frame_num = 9  # Frame 10 (Index 9)
                if self.selected is not None and 0 <= self.selected < len(self.assets):
                    asset = self.assets[self.selected]
                    if frame_num < len(asset['frames']):
                        self.current_frame = frame_num
                        print(f"Frame {frame_num + 1} ausgewählt für {asset['name']}")
            elif event.key == pygame.K_LEFT:
                # Vorheriger Frame
                if self.selected is not None and 0 <= self.selected < len(self.assets):
                    asset = self.assets[self.selected]
                    if len(asset['frames']) > 1:
                        self.current_frame = (self.current_frame - 1) % len(asset['frames'])
                        print(f"Frame {self.current_frame + 1}/{len(asset['frames'])} für {asset['name']}")
            elif event.key == pygame.K_RIGHT:
                # Nächster Frame
                if self.selected is not None and 0 <= self.selected < len(self.assets):
                    asset = self.assets[self.selected]
                    if len(asset['frames']) > 1:
                        self.current_frame = (self.current_frame + 1) % len(asset['frames'])
                        print(f"Frame {self.current_frame + 1}/{len(asset['frames'])} für {asset['name']}")
        
        if not self.visible:
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if self.is_mouse_over(mx, my, screen_width):
                if event.button == 1:  # Linksklick
                    # Berücksichtige das Info-Panel bei der Mausposition
                    info_panel_height = 12 * 16 + 10  # 12 Zeilen * 16px + 10px Abstand
                    panel_relative_y = my  # Y-Position relativ zum Panel
                    
                    # Prüfe ob Klick im Asset-Bereich ist (unterhalb des Info-Panels)
                    if panel_relative_y >= info_panel_height:
                        asset_relative_y = panel_relative_y - info_panel_height + self.scroll
                        idx = asset_relative_y // self.entry_h
                        if 0 <= idx < len(self.assets):
                            self.selected = idx
                            self.current_frame = 0  # Reset frame bei neuer Auswahl
                            print(f"Asset ausgewählt: {self.assets[idx]['name']}")

    def get_selected(self):
        if self.selected is None:
            return None
        if 0 <= self.selected < len(self.assets):
            asset = self.assets[self.selected].copy()
            # Füge den aktuellen Frame als 'image' hinzu für Rückwärtskompatibilität
            frame_idx = getattr(self, 'current_frame', 0)
            if frame_idx >= len(asset['frames']):
                frame_idx = 0
            asset['image'] = asset['frames'][frame_idx]
            return asset
        return None

    def draw(self, screen):
        if not self.visible:
            return
        h = self.surface.get_height()
        self.surface.fill((20,20,24,230))
        start_y = -self.scroll
        mx, my = pygame.mouse.get_pos()
        left = screen.get_width() - self.width
        
        # Info-Text oben
        info_lines = [
            "=== WORLD EDITOR ===",
            "Shift+Click: Platzieren",
            "Ctrl+Shift+Click: 5x5 Raster",
            "Alt+Shift+Click: Zufall x5",
            "",
            "1-9,0: Frame wählen (1-10)",
            "←→: Frame vor/zurück",
            "↑↓: Scrollen",
            "PgUp/PgDn: Schnell scrollen", 
            "S: Speichern",
            "C: Alles löschen", 
            "R: Assets neu laden",
            "Tab/F1: Panel toggle",
            "=================="
        ]
        
        info_y = 5
        for line in info_lines:
            info_surf = self.font.render(line, True, (200,255,200))
            self.surface.blit(info_surf, (5, info_y))
            info_y += 16
        
        start_y += len(info_lines) * 16 + 10
        
        for i, a in enumerate(self.assets):
            y = start_y + i*self.entry_h
            if y > h or y + self.entry_h < 0:
                continue
            rect = pygame.Rect(0, y, self.width, self.entry_h)
            over = left <= mx < left+self.width and 0 <= my - y < self.entry_h
            bg = (60,60,70) if over else (45,45,55)
            if i == self.selected:
                bg = (bg[0]+30, bg[1]+30, bg[2]+30)
            pygame.draw.rect(self.surface, bg, rect)
            
            # Zeige aktuellen Frame oder ersten Thumbnail
            thumb_to_show = a['thumbs'][0]  # Default: erster Frame
            if i == self.selected and hasattr(self, 'current_frame') and self.current_frame < len(a['thumbs']):
                thumb_to_show = a['thumbs'][self.current_frame]
            
            self.surface.blit(thumb_to_show, (6, y + (self.entry_h - thumb_to_show.get_height())//2))
            
            # Zeige Frame-Info bei ausgewähltem Asset
            name_text = a['name'][:18]  # Kürzer für mehr Platz
            if i == self.selected and len(a['frames']) > 1:
                frame_num = getattr(self, 'current_frame', 0) + 1
                total_frames = len(a['frames'])
                name_text += f" ({frame_num}/{total_frames})"
            
            name_surf = self.font.render(name_text[:40], True, (230,230,230))  # Mehr Platz
            self.surface.blit(name_surf, (54, y + (self.entry_h - name_surf.get_height())//2))
        pygame.draw.rect(self.surface, (90,90,110), (0,0,self.width,h), 1)
        screen.blit(self.surface, (screen.get_width()-self.width, 0))

    def place_into_world(self, world, world_pos):
        sel = self.get_selected()
        if not sel:
            return False
        
        # Verwende den aktuellen Frame
        frame_idx = getattr(self, 'current_frame', 0)
        if frame_idx >= len(sel['frames']):
            frame_idx = 0
        img = sel['frames'][frame_idx]
        
        wx, wy = world_pos
        px = int(wx - img.get_width()/2)
        py = int(wy - img.get_height())
        
        # Verschiedene Platzierungsmodi
        mods = pygame.key.get_mods()
        if mods & pygame.KMOD_CTRL:
            # Ctrl+Shift+Click: Mehrfache Platzierung in einem Raster
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if hasattr(world, 'add_dynamic_object'):
                        world.add_dynamic_object(img, px + dx * img.get_width(), py + dy * img.get_height(), sel['name'])
            return True
        elif mods & pygame.KMOD_ALT:
            # Alt+Shift+Click: Zufällige Platzierung in der Umgebung
            import random
            for _ in range(5):
                rand_x = px + random.randint(-100, 100)
                rand_y = py + random.randint(-100, 100)
                if hasattr(world, 'add_dynamic_object'):
                    world.add_dynamic_object(img, rand_x, rand_y, sel['name'])
            return True
        else:
            # Normal: Einzelne Platzierung
            if hasattr(world, 'add_dynamic_object'):
                return world.add_dynamic_object(img, px, py, sel['name'])
        return False


def load_player_sprite():
    # Versuche Player-Sheet zu laden, sonst gelbes Platzhalterquadrat
    base_dir = os.path.dirname(os.path.dirname(__file__))
    candidate = os.path.join(base_dir, 'assets', 'Player', 'character-grid-sprite.png')
    if os.path.exists(candidate):
        try:
            img = pygame.image.load(candidate).convert_alpha()
            surf = pygame.Surface((32, 32), pygame.SRCALPHA)
            surf.blit(img, (0, 0), (0, 0, 32, 32))
            return surf
        except Exception:
            pass
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)
    surf.fill((255, 255, 0))
    return surf

class Game:
    def __init__(self):
        pygame.init()
        flags = 0
        if FULLSCREEN:
            flags |= pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Zeit-System initialisieren
        self.game_time = GameTime()

        if USE_SIMPLE_WORLD:
            self.world = SimpleWorld()
            self.camera = Camera(self.world.width, self.world.height, SCREEN_WIDTH, SCREEN_HEIGHT)
            self.map = None
            spawn_pos = self.world.find_safe_spawn()
            spawn_x, spawn_y = spawn_pos
        else:
            self.map = TiledMap(MAP_PATH)
            self.camera = Camera(self.map.width, self.map.height, SCREEN_WIDTH, SCREEN_HEIGHT)
            self.world = None
            spawn_x, spawn_y = 100, 100

        self.all_sprites = pygame.sprite.Group()
        self.player = Player((spawn_x, spawn_y), world=self.world if USE_SIMPLE_WORLD else None)
        self.player.image = load_player_sprite()
        self.all_sprites.add(self.player)
        self.camera.update(self.player.rect)
        self.debug_panel = DebugPanel(SCREEN_HEIGHT)
        
        # Farming-System initialisieren
        self.farming_system = FarmingSystem(self.world if USE_SIMPLE_WORLD else None)
        
        # Farm-UI initialisieren
        self.farm_ui = FarmUI()
        
        # Inventar-System initialisieren
        self.inventory = Inventory()
        
        # Hunger-System initialisieren
        self.hunger_system = HungerSystem()
        
        # Tree-System initialisieren
        self.tree_system = TreeSystem(self.world if USE_SIMPLE_WORLD else None)
        
        # Versuche gespeicherte Welt zu laden
        self.auto_load_world()
        
        # Beispiel-Tiere platzieren
        self._place_demo_animals()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                    
            elif event.type == pygame.KEYDOWN:
                print(f"Taste gedrückt: {pygame.key.name(event.key)}")  # Debug-Ausgabe
                
                # Alle Tastatur-Events hier behandeln
                if event.key >= pygame.K_1 and event.key <= pygame.K_9:
                    # Frame-Auswahl für Debug Panel (1-9)
                    self.debug_panel.handle_event(event, self.screen.get_width())
                elif event.key == pygame.K_0:
                    # Frame 10 (Taste 0)
                    self.debug_panel.handle_event(event, self.screen.get_width())
                elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    # Frame navigation mit Pfeiltasten
                    self.debug_panel.handle_event(event, self.screen.get_width())
                elif event.key == pygame.K_F1 or event.key == pygame.K_TAB:
                    self.debug_panel.toggle()
                    print("Debug Panel umgeschaltet!")
                elif event.key == pygame.K_r:
                    self.debug_panel.scan_assets()
                    print("Assets neu geladen!")
                elif event.key == pygame.K_UP and self.debug_panel.visible:
                    # Pfeil hoch: Nach oben scrollen
                    self.debug_panel.scroll = max(0, self.debug_panel.scroll - self.debug_panel.entry_h)
                elif event.key == pygame.K_DOWN and self.debug_panel.visible:
                    # Pfeil runter: Nach unten scrollen
                    info_panel_height = 12 * 16 + 10
                    available_height = self.debug_panel.surface.get_height() - info_panel_height
                    max_scroll = max(0, len(self.debug_panel.assets)*self.debug_panel.entry_h - available_height)
                    self.debug_panel.scroll = min(max_scroll, self.debug_panel.scroll + self.debug_panel.entry_h)
                elif event.key == pygame.K_PAGEUP and self.debug_panel.visible:
                    # Page Up: Schneller nach oben
                    self.debug_panel.scroll = max(0, self.debug_panel.scroll - self.debug_panel.entry_h * 5)
                elif event.key == pygame.K_PAGEDOWN and self.debug_panel.visible:
                    # Page Down: Schneller nach unten
                    info_panel_height = 12 * 16 + 10
                    available_height = self.debug_panel.surface.get_height() - info_panel_height
                    max_scroll = max(0, len(self.debug_panel.assets)*self.debug_panel.entry_h - available_height)
                    self.debug_panel.scroll = min(max_scroll, self.debug_panel.scroll + self.debug_panel.entry_h * 5)
                elif event.key == pygame.K_s and USE_SIMPLE_WORLD:
                    # S = Speichern
                    if self.save_world():
                        print("Welt gespeichert!")
                # Zeit-Steuerung
                elif event.key == pygame.K_p:
                    # P = Zeit pausieren/fortsetzen
                    if self.game_time.paused:
                        self.game_time.resume()
                        print("Zeit fortgesetzt")
                    else:
                        self.game_time.pause()
                        print("Zeit pausiert")
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    # + = Zeit beschleunigen
                    new_speed = min(10.0, self.game_time.time_speed + 0.5)
                    self.game_time.set_time_speed(new_speed)
                    print(f"Zeitgeschwindigkeit: {new_speed:.1f}x")
                elif event.key == pygame.K_MINUS:
                    # - = Zeit verlangsamen
                    new_speed = max(0.1, self.game_time.time_speed - 0.5)
                    self.game_time.set_time_speed(new_speed)
                    print(f"Zeitgeschwindigkeit: {new_speed:.1f}x")
                elif event.key == pygame.K_t and pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    # Shift+T = Zeit vorspulen (1 Stunde)
                    self.game_time.advance_time(hours=1)
                    print(f"Zeit vorspulen: {self.game_time.get_time_string()}")
                elif event.key == pygame.K_t and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    # Ctrl+T = Schnell vorspulen (6 Stunden) - um Sonnenposition zu sehen
                    self.game_time.advance_time(hours=6)
                    print(f"Schnell vorspulen: {self.game_time.get_time_string()}")
                elif event.key == pygame.K_t:
                    # T = Zeit auf normal zurücksetzen
                    self.game_time.set_time_speed(1.0)
                    print("Zeitgeschwindigkeit zurückgesetzt")
                # Schnelle Sonnen-Demo Tasten
                elif event.key == pygame.K_m:
                    # M = Morgen (6:00)
                    self.game_time.set_time(6, 0)
                    print("Zeit gesetzt auf: Morgen 06:00")
                elif event.key == pygame.K_n:
                    # N = Mittag (12:00)
                    self.game_time.set_time(12, 0)
                    print("Zeit gesetzt auf: Mittag 12:00")
                elif event.key == pygame.K_i:
                    # I = Inventar öffnen/schließen
                    self.inventory.toggle_visibility()
                elif event.key == pygame.K_e:
                    # E = Essen (erste essbare Item im Inventar) oder Abend (wenn Shift gedrückt)
                    if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                        # Shift+E = Abend (18:00)
                        self.game_time.set_time(18, 0)
                        print("Zeit gesetzt auf: Abend 18:00")
                    else:
                        # E = Essen
                        # Suche nach essbaren Items im Inventar
                        eaten = False
                        for slot in self.inventory.slots:
                            if not slot.is_empty() and self.hunger_system.is_food_item(slot.item_type):
                                if self.hunger_system.eat_item(slot.item_type, self.inventory):
                                    print(f"🍴 {slot.item_type} gegessen!")
                                    eaten = True
                                    break
                        if not eaten:
                            print("Keine essbaren Items im Inventar!")
                elif event.key == pygame.K_SPACE:
                    # SPACE = Zeitraffer-Modus (5x Geschwindigkeit für Sonnen-Demo)
                    if self.game_time.time_speed == 5.0:
                        self.game_time.set_time_speed(1.0)
                        print("Zeitraffer aus")
                    else:
                        self.game_time.set_time_speed(5.0)
                        print("Zeitraffer an (5x Geschwindigkeit)")
                
                # Alte Farming-Steuerung entfernt - jetzt UI-basiert!
                # W = Gießen (behalten für Schnellzugriff)
                elif event.key == pygame.K_w:
                    # W = Gießen (Schnellzugriff)
                    world_pos = self.player.rect.center
                    tile_x = int(world_pos[0] // TILE_SIZE)
                    tile_y = int(world_pos[1] // TILE_SIZE)
                    if self.farming_system.water_crop_at_tile(tile_x, tile_y):
                        print("Pflanze gegossen!")
                elif event.key == pygame.K_h:
                    # H = Hilfe für Zeit-Steuerung anzeigen
                    self.show_time_help()
                elif event.key == pygame.K_c and USE_SIMPLE_WORLD:
                    # C = Clear (alle platzierten Objekte löschen)
                    if hasattr(self.world, 'clear_dynamic_objects'):
                        self.world.clear_dynamic_objects()
                        print("Alle platzierten Objekte gelöscht!")
                # Tier-Interaktion (behalten)
                elif event.key == pygame.K_f:
                    # F = Tier füttern
                    world_pos = self.player.rect.center
                    if self.farming_system.interact_with_animal(world_pos, "feed"):
                        print("Tier gefüttert!")
                    else:
                        print("Kein Tier in der Nähe")
                # Spezielle Simple World Navigation
                elif USE_SIMPLE_WORLD:
                    if event.key == pygame.K_l:
                        pos = self._find_feature_center('water')
                        if pos:
                            self.player.rect.center = pos
                            self.player.stop()
                    elif event.key == pygame.K_p:
                        pos = self._find_path_cross()
                        if pos:
                            self.player.rect.center = pos
                            self.player.stop()
                    elif event.key == pygame.K_f:
                        pos = self._find_feature_center('farm')
                        if pos:
                            self.player.rect.center = pos
                            self.player.stop()
            elif event.type == pygame.MOUSEMOTION:
                # Zeit-UI Hover-Effekt 
                self.game_time.handle_mouse_event(event)
            elif event.type == pygame.MOUSEWHEEL:
                # Mausrad-Events separat behandeln
                if self.debug_panel.visible:
                    mx, my = pygame.mouse.get_pos()
                    if self.debug_panel.is_mouse_over(mx, my, self.screen.get_width()):
                        if event.y > 0:  # Nach oben scrollen
                            self.debug_panel.scroll = max(0, self.debug_panel.scroll - self.debug_panel.entry_h)
                        elif event.y < 0:  # Nach unten scrollen
                            info_panel_height = 12 * 16 + 10  # Info-Panel Höhe
                            available_height = self.debug_panel.surface.get_height() - info_panel_height
                            max_scroll = max(0, len(self.debug_panel.assets)*self.debug_panel.entry_h - available_height)
                            self.debug_panel.scroll = min(max_scroll, self.debug_panel.scroll + self.debug_panel.entry_h)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Zeit-UI Klicks zuerst prüfen
                if self.game_time.handle_mouse_event(event):
                    continue  # Event wurde von Zeit-UI verarbeitet
                # Inventar Klicks prüfen (mit Hunger-System)
                elif self.inventory.handle_mouse_event(event, self.hunger_system):
                    continue  # Event wurde von Inventar verarbeitet
                # Farm-UI Klicks prüfen
                elif self.farm_ui.handle_mouse_event(event, self.camera):
                    continue  # Event wurde von Farm-UI verarbeitet
                # Klick auf Panel? -> Panel Event
                elif self.debug_panel.visible and self.debug_panel.is_mouse_over(*event.pos, self.screen.get_width()):
                    self.debug_panel.handle_event(event, self.screen.get_width())
                else:
                    # Alle anderen Klicks
                    mouse_screen = pygame.Vector2(event.pos)
                    world_x = mouse_screen.x + self.camera.camera.left
                    world_y = mouse_screen.y + self.camera.camera.top
                    mods = pygame.key.get_mods()
                    
                    # Prüfe zuerst Baum-Klicks
                    if self.tree_system.handle_click((world_x, world_y), self.player.rect.center, self.inventory):
                        # Baum wurde geklickt - keine weitere Aktion
                        continue
                    elif (mods & pygame.KMOD_SHIFT) and USE_SIMPLE_WORLD and self.world:
                        # Debug Panel Platzierung
                        if not self.debug_panel.place_into_world(self.world, (world_x, world_y)):
                            self.player.set_target((world_x, world_y))
                    else:
                        # Normale Spieler-Bewegung
                        self.player.set_target((world_x, world_y))
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # Farm-UI Mouse-Up Events
                self.farm_ui.handle_mouse_event(event, self.camera)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.player.stop()

    def _find_feature_center(self, code):
        if not USE_SIMPLE_WORLD or not self.world:
            return None
        for ty, row in enumerate(self.world.overlay):
            for tx, c in enumerate(row):
                if c == code:
                    return (tx * 32 + 16, ty * 32 + 16)
        return None

    def _find_path_cross(self):
        if not USE_SIMPLE_WORLD or not self.world:
            return None
        cx = self.world.area_width_tiles // 2
        cy = self.world.area_height_tiles // 2
        return (cx * 32 + 16, cy * 32 + 16)

    def update(self, dt):
        # Zeit-System updaten
        self.game_time.update()
        
        # Hunger-System updaten
        self.hunger_system.update(self.game_time)
        
        # Farming-System updaten
        self.farming_system.update(dt, self.game_time)
        
        # Tree-System updaten
        self.tree_system.update(dt)
        
        # Farm-Tiles an Farming-System weitergeben
        self.farming_system.set_farm_tiles(self.farm_ui.get_farm_tiles())
        
        # Farm-Aktionen vom UI verarbeiten
        mouse_pos = pygame.mouse.get_pos()
        if not self.farm_ui.ui_rect.collidepoint(mouse_pos):
            # Nur wenn Maus nicht über UI ist
            action_data = None
            if pygame.mouse.get_pressed()[0]:  # Linke Maustaste gedrückt
                if self.farm_ui.mode == "plant_crops":
                    world_pos = self.camera.screen_to_world(mouse_pos)
                    action_data = {'action': 'plant', 'pos': world_pos, 'crop': 'carrot'}
                elif self.farm_ui.mode == "harvest":
                    world_pos = self.camera.screen_to_world(mouse_pos)
                    action_data = {'action': 'harvest', 'pos': world_pos}
                elif self.farm_ui.mode == "water":
                    world_pos = self.camera.screen_to_world(mouse_pos)
                    action_data = {'action': 'water', 'pos': world_pos}
            
            if action_data:
                self.farming_system.handle_farm_action(action_data, self.inventory)
        
        self.all_sprites.update(dt)
        self.camera.update(self.player.rect)

    def save_world(self):
        """Speichert die aktuelle Welt mit allen platzierten Objekten"""
        if not USE_SIMPLE_WORLD or not hasattr(self.world, 'dynamic_objects'):
            return False
        
        import json
        save_data = {
            'dynamic_objects': [],
            'player_pos': [self.player.rect.centerx, self.player.rect.centery]
        }
        
        # Alle dynamischen Objekte speichern
        for obj in self.world.dynamic_objects:
            save_data['dynamic_objects'].append({
                'image_name': obj.get('image_name', 'unknown.png'),
                'x': obj['x'],
                'y': obj['y']
            })
        
        # In Datei speichern
        save_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saved_world.json')
        
        # Zeit auch speichern
        self.game_time.save_time(save_path)
        
        with open(save_path, 'w') as f:
            json.dump(save_data, f, indent=2)
        return True

    def load_world(self):
        """Lädt eine gespeicherte Welt"""
        save_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saved_world.json')
        if not os.path.exists(save_path):
            return False
        
        try:
            import json
            with open(save_path, 'r') as f:
                save_data = json.load(f)
            
            # Welt neu erstellen wenn im Simple World Modus
            if USE_SIMPLE_WORLD and hasattr(self.world, 'load_dynamic_objects'):
                self.world.load_dynamic_objects(save_data['dynamic_objects'])
                
                # Player Position wiederherstellen
                if 'player_pos' in save_data:
                    self.player.rect.center = save_data['player_pos']
                
                # Zeit wiederherstellen
                save_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saved_world.json')
                self.game_time.load_time(save_path)
                
                return True
        except Exception as e:
            print(f"Fehler beim Laden: {e}")
            return False
        
        return False

    def auto_load_world(self):
        """Lädt automatisch beim Start eine gespeicherte Welt"""
        save_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saved_world.json')
        if os.path.exists(save_path) and USE_SIMPLE_WORLD:
            if self.load_world():
                print("Gespeicherte Welt automatisch geladen!")

    def draw(self):
        self.screen.fill((30, 30, 40))
        
        # Basis-Szene zeichnen
        if USE_SIMPLE_WORLD:
            self.world.render(self.screen, self.camera.camera)
        else:
            self.map.render(self.screen, self.camera.camera)
            
        # Farm-Tiles als Bodentextur zeichnen (nach Basis-Welt, vor Sprites)
        self.farm_ui.draw_farm_tiles(self.screen, self.camera)
        
        # Bäume zeichnen (vor Spieler für korrektes Layering)
        self.tree_system.draw(self.screen, self.camera.camera)
            
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply_to_point(sprite.rect.topleft))
            
        # Farming-Elemente mit korrekten Assets zeichnen
        self.farm_ui.draw_crops(self.screen, self.camera, self.farming_system.crops)
        
        # Tiere zeichnen (nach Sprites)
        self.farming_system.draw_animals(self.screen, self.camera)
        
        # Lichtsystem anwenden
        self.apply_lighting()
        
        # Farm-UI zeichnen (nach Licht, aber vor anderen UIs)
        mouse_pos = pygame.mouse.get_pos()
        self.farm_ui.draw(self.screen, self.camera, mouse_pos)
        
        # UI
        self.debug_panel.draw(self.screen)
        
        # Inventar zeichnen (über allem anderen)
        self.inventory.draw(self.screen)
        
        # Hunger-UI zeichnen (links oben)
        self.hunger_system.draw_hunger_ui(self.screen, 10, 200)
        if self.hunger_system.is_hungry:
            self.hunger_system.draw_eating_hint(self.screen, 10, 280)
        
        # Zeit-UI zeichnen als elegantes, klickbares Spielelement (oben mittig)
        time_x = (SCREEN_WIDTH - 400) // 2  # Zentriert oben (400 = neue UI Breite)
        self.game_time.draw_time_ui(self.screen, time_x, 10)
        
        # Zeit-Steuerungshinweise (falls Zeit nicht normal läuft)
        if self.game_time.paused or self.game_time.time_speed != 1.0:
            info_y = 140
            if self.game_time.paused:
                pause_text = self.game_time.small_font.render("ZEIT PAUSIERT - Drücke P zum Fortsetzen", True, (255, 255, 0))
                text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, info_y))
                
                # Hintergrund für bessere Lesbarkeit
                bg_rect = text_rect.inflate(20, 10)
                pygame.draw.rect(self.screen, (0, 0, 0, 128), bg_rect)
                pygame.draw.rect(self.screen, (255, 255, 0), bg_rect, 2)
                
                self.screen.blit(pause_text, text_rect)
            elif self.game_time.time_speed != 1.0:
                speed_text = self.game_time.small_font.render(f"ZEITRAFFER: {self.game_time.time_speed:.1f}x - Drücke T für Normal", True, (0, 255, 255))
                text_rect = speed_text.get_rect(center=(SCREEN_WIDTH // 2, info_y))
                
                # Hintergrund für bessere Lesbarkeit
                bg_rect = text_rect.inflate(20, 10)
                pygame.draw.rect(self.screen, (0, 0, 0, 128), bg_rect)
                pygame.draw.rect(self.screen, (0, 255, 255), bg_rect, 2)
                
                self.screen.blit(speed_text, text_rect)
        
        pygame.display.flip()
        
    def show_time_help(self):
        """Zeige Hilfe für Zeit-Steuerung in der Konsole"""
        print("\n" + "="*50)
        print("⏰ ZEIT-STEUERUNG HILFE")
        print("="*50)
        print("⏸  P           = Zeit pausieren/fortsetzen")
        print("⚡ SPACE       = Zeitraffer (5x ein/aus)")
        print("➕ +           = Zeit beschleunigen")
        print("➖ -           = Zeit verlangsamen")
        print("🔄 T           = Normale Geschwindigkeit")
        print("⏩ Shift+T     = 1 Stunde vorspulen")
        print("⏩ Ctrl+T      = 6 Stunden vorspulen")
        print("🌅 M           = Springe zu Morgen (6:00)")
        print("☀️ N           = Springe zu Mittag (12:00)")
        print("🌆 E           = Springe zu Abend (18:00)")
        print("❓ H           = Diese Hilfe anzeigen")
        print("="*50)
        print("💡 Tipp: Beobachte die Sonne im Zeit-UI!")
        print("="*50 + "\n")
        
    def apply_lighting(self):
        """Wende das Lichtsystem auf die Szene an"""
        # Schatten-Overlay erstellen und anwenden
        shadow_overlay = self.game_time.get_shadow_overlay(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # IMMER das Licht-Overlay anwenden, damit Tag/Nacht sichtbar wird
        self.screen.blit(shadow_overlay, (0, 0), special_flags=pygame.BLEND_MULT)
    
    def _place_demo_animals(self):
        """Platziert Demo-Tiere in der Welt"""
        if not USE_SIMPLE_WORLD or not self.world:
            return
            
        # Tiere in der Nähe des Spawns platzieren
        spawn_x, spawn_y = self.world.find_safe_spawn()
        
        # Eine Kuh
        cow_pos = (spawn_x + 100, spawn_y + 50)
        self.farming_system.place_animal("cow", cow_pos)
        
        # Ein Schwein
        pig_pos = (spawn_x - 80, spawn_y + 100)
        self.farming_system.place_animal("pig", pig_pos)
        
        # Ein Huhn
        chicken_pos = (spawn_x + 50, spawn_y - 70)
        self.farming_system.place_animal("chicken", chicken_pos)
        
        # Ein Schaf
        sheep_pos = (spawn_x - 50, spawn_y - 50)
        self.farming_system.place_animal("sheep", sheep_pos)
        
        print("Demo-Tiere platziert: Kuh, Schwein, Huhn, Schaf")
        print("Steuerung:")
        print("1/2 = Weizen/Karotte pflanzen (auf Farmland)")
        print("W = Gießen, H = Ernten")
        print("F = Tier füttern, C = Von Tier sammeln")

if __name__ == '__main__':
    Game().run()
