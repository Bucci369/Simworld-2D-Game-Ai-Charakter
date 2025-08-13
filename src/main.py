import os
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, MAP_PATH, TITLE, USE_SIMPLE_WORLD, USE_KENNEY_WORLD, USE_ISOMETRIC_WORLD, FULLSCREEN, DEBUG_PANEL_WIDTH, TILE_SIZE
from map_loader import TiledMap, Camera
from simple_world_optimized import SimpleWorldOptimized
# from kenney_world import KenneyWorld  # Deaktiviert - Datei existiert nicht
# from isometric_world import IsometricWorld  # Deaktiviert - Datei existiert nicht
from player import Player
from time_system import GameTime
from farming_system import FarmingSystem
from farm_ui import FarmUI
from inventory import Inventory
from hunger_system import HungerSystem
from tree_system import TreeSystem
from mining_system import MiningSystem
from npc_system_simple import NPCSystem2D
from simple_tribe_ai import SimpleTribeSystem  # Neues vereinfachtes System
from storage_system import StorageSystem
from house_system import HouseSystem
from chat_system import ChatSystem
from pygame import KMOD_SHIFT

# Debug Panel (lazy import of assets)
class DebugPanel:
    def __init__(self, screen_height):
        import pygame
        self.visible = True  # Standardmäßig sichtbar
        self.width = DEBUG_PANEL_WIDTH
        self.surface = pygame.Surface((self.width, screen_height), pygame.SRCALPHA)
        self.font = pygame.font.SysFont('Arial', 12)  # Verkleinert von 14
        self.assets = []  # list of dict(name, image, thumb)
        self.selected = None
        self.scroll = 0
        self.entry_h = 35  # Verkleinert von 48
        self.current_frame = 0  # Welcher Frame des Sprite-Sheets gerade angezeigt wird
        # 🚀 PERFORMANCE: Debug Panel Asset-Scanning komplett deaktiviert
        # Asset-Scanning war der größte Performance-Killer beim Start
        
        # Single Asset Loading System
        self.current_single_asset = None
        self.single_asset_mode = True  # Neuer Modus: Ein Asset zur Zeit

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
                        scale = min(28/max(1,fw), 28/max(1,fh), 1)  # Verkleinert von 40
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
    
    def load_single_asset(self, asset_path):
        """Lädt ein einzelnes Asset für die Platzierung"""
        try:
            if not os.path.exists(asset_path):
                print(f"❌ Asset nicht gefunden: {asset_path}")
                return False
            
            full_img = pygame.image.load(asset_path).convert_alpha()
            filename = os.path.basename(asset_path)
            
            # Erstelle Thumbnail
            w, h = full_img.get_size()
            scale = min(28/max(1,w), 28/max(1,h), 1)  # Verkleinert von 40
            thumb = pygame.transform.smoothscale(full_img, (int(w*scale), int(h*scale))) if scale != 1 else full_img
            
            self.current_single_asset = {
                'name': filename,
                'frames': [full_img],  # Einfach als einzelner Frame
                'thumbs': [thumb],
                'image': full_img
            }
            
            print(f"✅ Asset geladen: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Laden von {asset_path}: {e}")
            return False
    
    def get_selected(self):
        """Gibt das aktuell geladene Asset zurück"""
        if self.single_asset_mode and self.current_single_asset:
            return self.current_single_asset
        elif not self.single_asset_mode and self.selected is not None:
            # Alter Modus (falls wieder aktiviert)
            if 0 <= self.selected < len(self.assets):
                asset = self.assets[self.selected].copy()
                frame_idx = getattr(self, 'current_frame', 0)
                if frame_idx >= len(asset['frames']):
                    frame_idx = 0
                asset['image'] = asset['frames'][frame_idx]
                return asset
        return None

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

    # get_selected wurde bereits oben neu definiert

    def draw(self, screen):
        if not self.visible:
            return
        h = self.surface.get_height()
        self.surface.fill((20,20,24,230))
        start_y = -self.scroll
        mx, my = pygame.mouse.get_pos()
        left = screen.get_width() - self.width
        
        # Info-Text oben (für Single Asset Modus, verkürzt)
        if self.single_asset_mode:
            info_lines = [
                "=== ASSET MODE ===",
                "L: Asset laden",
                "Shift+Klick: Platzieren",
                "V: Edit-Modus",
                "Edit: Klick&Drag, Del",
                "",
                "S: Speichern",
                "Tab: Panel toggle",
                "=================="
            ]
        else:
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
            info_y += 14  # Verkleinert von 16
        
        start_y += len(info_lines) * 14 + 10  # Angepasst an neue Zeilenhöhe
        
        # Single Asset Anzeige
        if self.single_asset_mode and self.current_single_asset:
            # Zeige aktuell geladenes Asset
            y = start_y
            rect = pygame.Rect(0, y, self.width, self.entry_h)
            bg = (60, 100, 60)  # Grüner Hintergrund für geladenes Asset
            pygame.draw.rect(self.surface, bg, rect)
            
            # Asset Thumbnail
            thumb = self.current_single_asset['thumbs'][0]
            self.surface.blit(thumb, (6, y + (self.entry_h - thumb.get_height())//2))
            
            # Asset Name
            name_text = self.current_single_asset['name'][:35]
            name_surf = self.font.render(name_text, True, (255, 255, 255))
            self.surface.blit(name_surf, (54, y + (self.entry_h - name_surf.get_height())//2))
        elif self.single_asset_mode:
            # Kein Asset geladen - zeige Hinweis
            y = start_y
            hint_text = "Kein Asset geladen"
            hint_surf = self.font.render(hint_text, True, (200, 200, 200))
            self.surface.blit(hint_surf, (10, y))
        
        # Alter Modus (falls aktiviert)
        if not self.single_asset_mode:
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
        
        # 🚀 SMOOTH RENDERING: VSYNC für konsistente Framerate
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags, vsync=1)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 🚀 PERFORMANCE: Frame-Zeit Tracking für konsistente Bewegung
        self.frame_time = 0.0
        self.target_fps = FPS
        
        # Zeit-System initialisieren
        self.game_time = GameTime()

        if USE_SIMPLE_WORLD:
            if USE_ISOMETRIC_WORLD:
                # 🏘️ ISOMETRIC WORLD: Fallback auf optimierte SimpleWorld
                self.world = SimpleWorldOptimized()  # Fallback da IsometricWorld nicht verfügbar
                print(f"🏘️ ISOMETRIC WORLD (Fallback auf SimpleWorldOptimized): {self.world.width}x{self.world.height} pixels")
            elif USE_KENNEY_WORLD:
                # 🏘️ KENNEY WORLD: Fallback auf optimierte SimpleWorld
                self.world = SimpleWorldOptimized()  # Fallback da KenneyWorld nicht verfügbar
                print(f"🏘️ KENNEY WORLD (Fallback auf SimpleWorldOptimized): {self.world.width}x{self.world.height} pixels")
            else:
                # 🚀 PERFORMANCE: Verwende optimierte SimpleWorld  
                self.world = SimpleWorldOptimized()  # Optimiert: Asset-Caching + Pre-Rendering
                print(f"🚀 OPTIMIZED SimpleWorld created: {self.world.width}x{self.world.height} pixels")
                
            self.camera = Camera(self.world.width, self.world.height, SCREEN_WIDTH, SCREEN_HEIGHT)
            self.map = None
            spawn_x, spawn_y = self.world.find_safe_spawn()
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
        
        # Mining-System initialisieren
        self.mining_system = MiningSystem(self.world if USE_SIMPLE_WORLD else None)
        
        # 📦 Storage-System initialisieren (Lager für jedes Volk)
        self.storage_system = StorageSystem()
        
        # 🏠 House-System initialisieren (Häuser und Stadtplanung)
        self.house_system = HouseSystem()
        
        # 💬 Chat-System initialisieren (Spieler-Befehle an Anführer)
        self.chat_system = ChatSystem(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # NPC-System initialisieren (einfaches 2D-System)
        self.npc_system = NPCSystem2D(self.world if USE_SIMPLE_WORLD else None)
        
        # 🧠 Hierarchisches KI-Stamm-System initialisieren
        try:
            from hierarchical_tribe_system import SimpleTribeSystem
            self.tribe_system = SimpleTribeSystem()
            self.use_ai_tribess = True
            print("🏛️ Hierarchisches AI System geladen (Agenten-basiert)")
        except ImportError:
            print("⚠️ Hierarchisches System nicht verfügbar, verwende altes System")
            from simple_tribe_ai import SimpleTribeSystem
            self.tribe_system = SimpleTribeSystem()
            self.use_ai_tribess = True
            print("🏠 Einfaches Tribe AI System geladen (Fallback)")
        
        # Immer 2D-NPCs verwenden (Performance-optimiert)
        self.use_3d_npcs = False
        self.use_ai_tribes = True  # Verwende KI-Stamm statt einfacher NPCs
        
        # 🏘️ SPAWN-POSITIONEN: Erweiterte Verteilung in 70x70 Welt für mehr Abstand
        # Spieler spawnt in der Mitte der Welt (1120, 1120 bei 2240x2240)
        player_x, player_y = spawn_x, spawn_y
        tribe_spawn_pos = (player_x, player_y)
        
        if self.use_ai_tribess:
            # 🏘️ ERSTES VOLK (ROT): Beim Spieler (Mitte der Welt)
            storage_pos_red = (tribe_spawn_pos[0], tribe_spawn_pos[1])
            self.storage_system.create_storage(storage_pos_red, "red")
            self.house_system.create_city_planner("red", storage_pos_red)
            
            # 🏘️ ZWEITES VOLK (BLAU): Weiter entfernt für größere Welt
            # Erweiterte Verteilung in 70x70 Welt mit mehr Abstand
            blue_spawn_x = player_x + 500  # 500 Pixel rechts vom Spieler (mehr Abstand)
            blue_spawn_y = player_y - 400  # 400 Pixel nach oben vom Spieler (mehr Abstand)
            blue_tribe_spawn_pos = (blue_spawn_x, blue_spawn_y)
            
            storage_pos_blue = (blue_spawn_x, blue_spawn_y)
            self.storage_system.create_storage(storage_pos_blue, "blue")
            self.house_system.create_city_planner("blue", storage_pos_blue)
            
            # HIERARCHISCHES SYSTEM RICHTIG VERBINDEN
            if hasattr(self.tribe_system, 'create_growth_oriented_tribe_near_player'):
                # Verbinde mit echten Game-Systemen
                self.tribe_system.game_house_system = self.house_system
                # WICHTIG: Verbinde auch die Welt-Ressourcen für echtes Sammeln/Bauen
                self.tribe_system.game_world_resources = {
                    'trees': self.tree_system,
                    'mining': getattr(self, 'mining_system', None),
                    'storage': self.storage_system
                }
                
                # Verwende hierarchisches System für BEIDE Völker
                player_pos = (self.player.rect.centerx, self.player.rect.centery)
                
                # ROTES VOLK (bei Spieler) - erweiterte Reichweite (VERDOPPELT FÜR PERFORMANCE TEST)
                volk_red = self.tribe_system.create_growth_oriented_tribe_near_player("red", player_pos, distance=200.0, num_workers=20)
                
                # BLAUES VOLK (weiter entfernt) - erweiterte Reichweite (VERDOPPELT FÜR PERFORMANCE TEST)
                volk_blue = self.tribe_system.create_growth_oriented_tribe_near_player("blue", blue_tribe_spawn_pos, distance=200.0, num_workers=20)
                
                # WICHTIG: Aktiviere kontinuierliche Updates
                self.hierarchical_active = True
                print("🏛️ Hierarchisches System AKTIV - 2 Völker bauen Städte!")
                print(f"🔴 Rotes Volk bei Spieler: {storage_pos_red}")
                print(f"🔵 Blaues Volk oben rechts: {storage_pos_blue}")
            else:
                # Fallback für beide Völker (VERDOPPELT FÜR PERFORMANCE TEST)
                self.tribe_system.create_tribe("red", tribe_spawn_pos, num_workers=20)
                self.tribe_system.create_tribe("blue", blue_tribe_spawn_pos, num_workers=20)
                print("👥 Fallback System aktiv - 2 Völker erstellt")
        
        # Versuche gespeicherte Welt zu laden
        self.auto_load_world()
        
        # Beispiel-Tiere platzieren
        self._place_demo_animals()
        
        # Memory Management Timer
        self._memory_cleanup_timer = 0.0
        self._memory_cleanup_interval = 60.0  # Alle 60 Sekunden aufräumen
        
        # Drag & Drop State
        self.edit_mode = False  # Toggle für Edit-Modus
        
        # Asset Loading State
        self.asset_input_mode = False
        self.asset_input_text = ""

    def run(self):
        """🚀 SMOOTH GAME LOOP: Optimiert für konsistente Performance"""
        while self.running:
            # 🚀 PERFORMANCE: Frame-Zeit mit Begrenzung für Stabilität
            frame_ms = self.clock.tick(self.target_fps)
            dt = min(frame_ms / 1000.0, 1.0/30.0)  # Max 30 FPS minimum (verhindert riesige dt-Sprünge)
            
            self.frame_time = dt
            
            self.handle_events()
            self.update(dt)
            self.draw()
            
        pygame.quit()

    def _get_tribe_leader(self, tribe_color: str):
        """Hole den Anführer eines Stammes"""
        try:
            if hasattr(self, 'tribe_system') and self.tribe_system and hasattr(self.tribe_system, 'tribes'):
                tribe = self.tribe_system.tribes.get(tribe_color, [])
                for npc in tribe:
                    if hasattr(npc, 'is_leader') and npc.is_leader:
                        return npc
        except Exception as e:
            print(f"❌ Fehler beim Suchen des Anführers: {e}")
        return None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                    
            elif event.type == pygame.KEYDOWN:
                print(f"Taste gedrückt: {pygame.key.name(event.key)}")  # Debug-Ausgabe
                
                # Chat-System hat Priorität bei Input
                try:
                    command = self.chat_system.handle_input(event)
                    if command:
                        # Bestimme welcher Anführer angesprochen werden soll
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_SHIFT:
                            # Shift+Chat = Sprich mit blauem Anführer
                            leader = self._get_tribe_leader('blue')
                            tribe_name = "Blaues Volk"
                        elif mods & pygame.KMOD_CTRL:
                            # Ctrl+Chat = Sprich mit beiden Anführern
                            leaders = [self._get_tribe_leader('red'), self._get_tribe_leader('blue')]
                            tribe_name = "Beide Völker"
                        else:
                            # Standard = Sprich mit rotem Anführer
                            leader = self._get_tribe_leader('red')
                            tribe_name = "Rotes Volk"
                        
                        # Befehle senden
                        if mods & pygame.KMOD_CTRL:
                            # An beide Anführer senden
                            from chat_system import CommandParser
                            parser = CommandParser()
                            parsed = parser.parse_command(command.command_text)
                            
                            for i, leader in enumerate(leaders):
                                if leader:
                                    leader.receive_player_command(parsed)
                                    color = "🔴" if i == 0 else "🔵"
                                    self.chat_system.add_leader_response(f"{color} {tribe_name}: Befehl erhalten: {parsed['description']}")
                        else:
                            # An einen Anführer senden
                            if leader:
                                from chat_system import CommandParser
                                parser = CommandParser()
                                parsed = parser.parse_command(command.command_text)
                                leader.receive_player_command(parsed)
                                color = "🔴" if tribe_name == "Rotes Volk" else "🔵"
                                self.chat_system.add_leader_response(f"{color} {tribe_name}: Befehl erhalten: {parsed['description']}")
                        continue  # Skip andere Input-Handling wenn Chat aktiv
                except Exception as e:
                    print(f"❌ Chat-System Fehler: {e}")
                    # Fortfahren ohne Chat-Input
                
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
                    # Asset-Scanning deaktiviert für Performance
                    # self.debug_panel.scan_assets()
                    print("Asset-Scanning deaktiviert für Performance!")
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
                elif event.key == pygame.K_t and pygame.key.get_pressed()[pygame.K_LALT]:
                    # Alt+T = Teleportiere AI Members zum Player
                    if self.tribe_system:
                        player_x = self.player.x
                        player_y = self.player.y
                        
                        # Unterschiedliche Teleport-Methoden für verschiedene AI Systeme
                        if hasattr(self.tribe_system, 'teleport_nearby_to_player'):
                            # Hybrid/Scalable AI System - teleportiere nahegelegene Charaktere
                            self.tribe_system.teleport_nearby_to_player(player_x, player_y, radius=500)
                            if hasattr(self.tribe_system, 'leaders'):
                                print(f"🚁 AI Charaktere zu dir teleportiert! ({len(self.tribe_system.leaders)} Leaders + {len(self.tribe_system.workers)} Workers)")
                            else:
                                print("🚁 Nahegelegene AI Charaktere zu dir teleportiert!")
                        else:
                            # Normal AI System
                            self.tribe_system.teleport_members_to_player(player_x, player_y)
                            print("🚁 AI Tribe Members zu dir teleportiert!")
                elif event.key == pygame.K_t:
                    # T = Zeit auf normal zurücksetzen
                    self.game_time.set_time_speed(1.0)
                    print("Zeitgeschwindigkeit zurückgesetzt")
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
                                    print(f"� {slot.item_type} gegessen!")
                                    eaten = True
                                    break
                        if not eaten:
                            print("Keine essbaren Items im Inventar!")
                # Schnelle Sonnen-Demo Tasten
                elif event.key == pygame.K_m:
                    # M = Morgen (6:00)
                    self.game_time.set_time(6, 0)
                    print("Zeit gesetzt auf: Morgen 06:00")
                elif event.key == pygame.K_n:
                    # N = Mittag (12:00)
                    self.game_time.set_time(12, 0)
                    print("Zeit gesetzt auf: Mittag 12:00")
                elif event.key == pygame.K_k:
                    # K = KI-Statistiken anzeigen
                    if self.use_ai_tribess:
                        if hasattr(self.tribe_system, 'get_stats'):
                            # Hybrid/Scalable AI System
                            stats = self.tribe_system.get_stats()
                            print(f"🧠 Hybrid AI Stats: {stats}")
                        else:
                            # Normal AI System
                            stats = self.tribe_system.get_ai_stats()
                            print(f"🧠 KI-Stats: {stats}")
                
                elif event.key == pygame.K_r:
                    # [R] - Ressourcen-Debug: Zeige alle gesammelten Ressourcen
                    if hasattr(self.tribe_system, 'members'):
                        print("📊 RESSOURCEN-ÜBERSICHT:")
                        for color in ['red', 'blue', 'green']:
                            tribe_members = [m for m in self.tribe_system.members if m.tribe_color == color]
                            total_wood = sum(m.memory.resources_collected['wood'] for m in tribe_members)
                            total_stone = sum(m.memory.resources_collected['stone'] for m in tribe_members)
                            print(f"  🔴🔵🟢 {color.upper()} Volk: {total_wood} Holz, {total_stone} Stein ({len(tribe_members)} Mitglieder)")
                
                elif event.key == pygame.K_b:
                    # [B] - Baufortschritt-Debug  
                    if hasattr(self.tribe_system, 'world_state'):
                        print("🏠 BAUFORTSCHRITT:")
                        for color in ['red', 'blue', 'green']:
                            house_key = f'house_progress_{color}'
                            progress = self.tribe_system.world_state.get(house_key, 0.0)
                            completed = self.tribe_system.world_state.get(f'house_completed_{color}', False)
                            status = "✅ FERTIG" if completed else f"{progress:.1%}"
                            house_type = {"red": "Holzhaus", "blue": "Haus", "green": "Steinburg"}[color]
                            print(f"  🔴🔵🟢 {color.upper()} {house_type}: {status}")
                
                elif event.key == pygame.K_o:
                    # [O] - Boost Ressourcen sammeln (zum Testen)
                    if hasattr(self.tribe_system, 'volks'):
                        print("⚡ HIERARCHISCHES SYSTEM: Ressourcen-Boost!")
                        for volk in self.tribe_system.volks.values():
                            volk.update_resource('wood', 25)
                            volk.update_resource('stone', 15)
                            volk.update_resource('gold', 10)
                        print("💰 Alle Völker haben Ressourcen erhalten!")
                    elif hasattr(self.tribe_system, 'members'):
                        print("⚡ ALTES SYSTEM: RESSOURCEN-BOOST AKTIVIERT!")
                        import random
                        for member in self.tribe_system.members[:20]:  # Erste 20 NPCs
                            member.memory.resources_collected['wood'] += random.randint(5, 15)
                            member.memory.resources_collected['stone'] += random.randint(3, 10)
                        print("🪓 +Holz und ⛏️ +Stein für 20 NPCs hinzugefügt!")
                elif event.key == pygame.K_x:
                    # [X] - Simuliere Bedrohung (nur hierarchisches System)
                    if hasattr(self.tribe_system, 'simulate_threat'):
                        print("🚨 SIMULIERE BEDROHUNG!")
                        self.tribe_system.simulate_threat("red", threat_level=0.9)
                        print("⚔️ Kriegsherr sollte Kampfmodus aktivieren!")
                elif event.key == pygame.K_c and not USE_SIMPLE_WORLD:
                    # C = Chat öffnen/schließen (nur wenn nicht Simple World für Clear)
                    self.chat_system.toggle_chat()
                elif event.key == pygame.K_c and USE_SIMPLE_WORLD and pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    # Shift+C = Clear (alle platzierten Objekte löschen) in Simple World
                    if hasattr(self.world, 'clear_dynamic_objects'):
                        self.world.clear_dynamic_objects()
                        print("Alle platzierten Objekte gelöscht!")
                elif event.key == pygame.K_c and not pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    # C = Chat öffnen/schließen
                    self.chat_system.toggle_chat()
                elif event.key == pygame.K_v:
                    # V = Edit-Modus toggle (für Drag & Drop)
                    self.edit_mode = not self.edit_mode
                    if USE_SIMPLE_WORLD and hasattr(self.world, 'end_drag'):
                        self.world.end_drag()  # Beende aktuelles Dragging
                    print(f"🎨 Edit-Modus: {'AN' if self.edit_mode else 'AUS'}")
                elif event.key == pygame.K_DELETE and self.edit_mode:
                    # DELETE = Ausgewähltes Objekt löschen (nur im Edit-Modus)
                    if USE_SIMPLE_WORLD and hasattr(self.world, 'delete_selected_object'):
                        self.world.delete_selected_object()
                elif event.key == pygame.K_l:
                    # L = Asset laden (Input-Modus aktivieren)
                    self.asset_input_mode = True
                    self.asset_input_text = ""
                    print("📝 Asset-Eingabe aktiviert - tippe Pfad und drücke Enter")
                    print("Beispiele: assets/Outdoor decoration/House.png")
                elif self.asset_input_mode:
                    # Asset-Input-Modus
                    if event.key == pygame.K_RETURN:
                        # Enter = Asset laden
                        if self.asset_input_text.strip():
                            asset_path = self.asset_input_text.strip()
                            # Absoluter Pfad vom Game-Ordner aus
                            full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), asset_path)
                            if self.debug_panel.load_single_asset(full_path):
                                print(f"✅ Asset '{asset_path}' erfolgreich geladen!")
                            else:
                                print(f"❌ Konnte Asset '{asset_path}' nicht laden!")
                        self.asset_input_mode = False
                        self.asset_input_text = ""
                    elif event.key == pygame.K_ESCAPE:
                        # Escape = Input abbrechen
                        self.asset_input_mode = False
                        self.asset_input_text = ""
                        print("Asset-Eingabe abgebrochen")
                    elif event.key == pygame.K_BACKSPACE:
                        # Backspace = Zeichen löschen
                        self.asset_input_text = self.asset_input_text[:-1]
                        print(f"📝 {self.asset_input_text}")
                    else:
                        # Normales Zeichen hinzufügen
                        if event.unicode and event.unicode.isprintable():
                            self.asset_input_text += event.unicode
                            print(f"📝 {self.asset_input_text}")
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
                
                # Drag & Drop Update (nur im Edit-Modus)
                if self.edit_mode and USE_SIMPLE_WORLD and hasattr(self.world, 'dragging'):
                    if self.world.dragging:
                        world_pos = self.camera.screen_to_world(event.pos)
                        self.world.update_drag(world_pos)
            elif event.type == pygame.MOUSEWHEEL:
                # Mausrad-Events für Debug Panel
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
                    world_pos = self.camera.screen_to_world(event.pos)
                    world_x, world_y = world_pos
                    mods = pygame.key.get_mods()
                    
                    # Prüfe zuerst Baum-Klicks
                    if self.tree_system.handle_click((world_x, world_y), self.player.rect.center, self.inventory):
                        # Baum wurde geklickt - keine weitere Aktion
                        continue
                    
                    # Prüfe Mining-Klicks (Stone/Gold)
                    if self.mining_system.handle_click((world_x, world_y), self.player.rect.center, self.inventory):
                        # Resource wurde geklickt - keine weitere Aktion
                        continue
                    
                    # 📦 Prüfe Lager-Klicks
                    if self.storage_system.handle_click((world_x, world_y), self.player.rect.center):
                        # Lager wurde geklickt
                        continue
                    
                    # 🏠 Prüfe Haus-Klicks  
                    if self.house_system.handle_click((world_x, world_y), self.player.rect.center):
                        # Haus wurde geklickt
                        continue
                    elif self.edit_mode and USE_SIMPLE_WORLD and hasattr(self.world, 'start_drag'):
                        # Edit-Modus: Drag & Drop starten
                        if not self.world.start_drag((world_x, world_y)):
                            # Kein Objekt gefunden - normale Bewegung
                            self.player.set_target((world_x, world_y))
                    elif (mods & pygame.KMOD_SHIFT) and USE_SIMPLE_WORLD and self.world:
                        # Debug Panel Platzierung
                        if not self.debug_panel.place_into_world(self.world, (world_x, world_y)):
                            self.player.set_target((world_x, world_y))
                    else:
                        # Normale Spieler-Bewegung
                        self.player.set_target((world_x, world_y))
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # Drag & Drop beenden (im Edit-Modus)
                if self.edit_mode and USE_SIMPLE_WORLD and hasattr(self.world, 'end_drag'):
                    self.world.end_drag()
                
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
        # 🚀 PERFORMANCE: Optimierte Update-Frequenz für bessere FPS
        
        # Kritische Systeme - jedes Frame
        self.game_time.update()
        self.all_sprites.update(dt)
        self.camera.update(self.player.rect, dt)
        
        # 🚀 PERFORMANCE: Timer für weniger kritische Updates
        if not hasattr(self, '_system_update_timer'):
            self._system_update_timer = 0.0
            
        self._system_update_timer += dt
        
        # Aktualisiere diese Systeme nur alle 0.1 Sekunden (10 FPS statt 60 FPS)
        if self._system_update_timer >= 0.1:
            self.hunger_system.update(self.game_time)
            self.farming_system.update(self._system_update_timer, self.game_time)
            self.tree_system.update(self._system_update_timer)
            self.mining_system.update(self._system_update_timer)
            self.storage_system.update(self._system_update_timer)
            self.house_system.update(self._system_update_timer)
            
            # Reset timer
            self._system_update_timer = 0.0
        
        # Chat-System - nur alle 0.05 Sekunden (20 FPS)
        if not hasattr(self, '_chat_update_timer'):
            self._chat_update_timer = 0.0
            
        self._chat_update_timer += dt
        if self._chat_update_timer >= 0.05:
            self.chat_system.update(self._chat_update_timer)
            self._chat_update_timer = 0.0
        
        # Hole Anführer-Antworten und zeige sie im Chat
        if hasattr(self, 'tribe_system') and self.tribe_system:
            if hasattr(self.tribe_system, 'volks'):
                # Hierarchisches System - hole Agent-Responses
                for volk in self.tribe_system.volks.values():
                    # Hier könnten wir Agent-Responses sammeln
                    pass
            else:
                # Altes System
                leader = self._get_tribe_leader('red')
                if leader and hasattr(leader, 'command_responses'):
                    for response in leader.command_responses:
                        self.chat_system.add_leader_response(response)
                    leader.command_responses.clear()
        
        # 🚀 PERFORMANCE: AI-System nur alle 0.2 Sekunden updaten (5 FPS statt 60 FPS)
        if not hasattr(self, '_ai_update_timer'):
            self._ai_update_timer = 0.0
            
        self._ai_update_timer += dt
        if self._ai_update_timer >= 0.2:
            if self.use_ai_tribess:
                world_state = {
                    'tree_system': self.tree_system,
                    'storage_system': self.storage_system,
                    'house_system': self.house_system,
                    'tribe_system': self.tribe_system
                }
                self.tribe_system.update(self._ai_update_timer, world_state)
            else:
                self.npc_system.update(self._ai_update_timer)
            
            self._ai_update_timer = 0.0
        
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
        
        # Memory Management - periodische Bereinigung (weniger häufig)
        if not hasattr(self, '_memory_cleanup_timer'):
            self._memory_cleanup_timer = 0.0
            self._memory_cleanup_interval = 120.0  # Erhöht von 60 auf 120 Sekunden
            
        self._memory_cleanup_timer += dt
        if self._memory_cleanup_timer >= self._memory_cleanup_interval:
            self._memory_cleanup_timer = 0.0
            self._cleanup_memory()

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
    
    def _cleanup_memory(self):
        """🚀 PERFORMANCE: Erweiterte Memory-Bereinigung"""
        try:
            # 1. Asset-Manager Cache-Status anzeigen
            if hasattr(self, 'world'):
                from asset_manager import asset_manager
                stats = asset_manager.get_cache_stats()
                print(f"📊 Asset Cache: {stats['images_cached']} images, {stats['scaled_cached']} scaled, {stats['hit_rate']} hit rate")
            
            # 2. NPC Speech Bubbles bereinigen
            if hasattr(self, 'tribe_system') and hasattr(self.tribe_system, 'tribes'):
                cleaned_bubbles = 0
                for tribe_color, npcs in self.tribe_system.tribes.items():
                    for npc in npcs:
                        if hasattr(npc, 'speech_bubble') and npc.speech_bubble:
                            if npc.speech_bubble.is_expired():
                                npc.speech_bubble = None
                                cleaned_bubbles += 1
                if cleaned_bubbles > 0:
                    print(f"🧹 Cleaned {cleaned_bubbles} expired speech bubbles")
            
            # 3. Dynamic Objects sind jetzt automatisch begrenzt in SimpleWorldOptimized
            if USE_SIMPLE_WORLD and hasattr(self.world, 'dynamic_objects'):
                obj_count = len(self.world.dynamic_objects)
                print(f"📦 Dynamic objects: {obj_count}/{getattr(self.world, 'max_dynamic_objects', 50)}")
            
            # 4. Pygame Surface Cache bereinigen (falls vorhanden)
            pygame.display.flip()  # Ensure display updates are processed
            
            print(f"🧹 Memory cleanup completed successfully")
            
        except Exception as e:
            print(f"❌ Memory cleanup error: {e}")

    def auto_load_world(self):
        """Lädt automatisch beim Start eine gespeicherte Welt"""
        save_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saved_world.json')
        if os.path.exists(save_path) and USE_SIMPLE_WORLD:
            if self.load_world():
                print("Gespeicherte Welt automatisch geladen!")

    def draw(self):
        # Bildschirm leeren
        self.screen.fill((0, 0, 0))
        
        # Welt direkt auf Bildschirm zeichnen
        if USE_SIMPLE_WORLD:
            self.world.render(self.screen, self.camera.camera)
        else:
            self.map.render(self.screen, self.camera.camera)
            
        # Farm-Tiles als Bodentextur zeichnen
        self.farm_ui.draw_farm_tiles(self.screen, self.camera)
        
        # Bäume zeichnen
        self.tree_system.draw(self.screen, self.camera.camera)
        
        # Mining-Resources zeichnen
        self.mining_system.draw(self.screen, self.camera.camera)
        
        # 📦 Lager zeichnen
        self.storage_system.draw(self.screen, self.camera.camera)
        
        # 🏠 Häuser zeichnen (vor NPCs für korrektes Layering)
        self.house_system.draw(self.screen, self.camera.camera)
            
        # Sprites zeichnen
        for sprite in self.all_sprites:
            screen_pos = self.camera.apply_to_point(sprite.rect.topleft)
            self.screen.blit(sprite.image, screen_pos)
            
        # Farming-Elemente zeichnen
        self.farm_ui.draw_crops(self.screen, self.camera, self.farming_system.crops)
        
        # Tiere zeichnen
        self.farming_system.draw_animals(self.screen, self.camera)
        
        # NPCs zeichnen
        if self.use_3d_npcs:
            # 3D-NPCs werden mit OpenGL gerendert (nach 2D-Rendering)
            pass  # 3D-Rendering erfolgt später
        elif self.use_ai_tribes:
            # Stamm-System mit Sprite-Rendering
            for color, npcs in self.tribe_system.tribes.items():
                for npc in npcs:
                    # Verwende die NPC-eigene draw-Methode mit Sprite-System
                    npc.draw(self.screen, self.camera)
        else:
            # Fallback: Einfache 2D-NPCs zeichnen
            self.npc_system.render(self.screen, self.camera)
        
        # Lichtsystem anwenden
        self.apply_lighting()
        
        # UI-Elemente zeichnen (nicht gezoomt)
        # Game-Time Statusleiste (Sonne/Tag/Nacht-System)
        self.game_time.draw_time_ui(self.screen, 10, 10)
        
        # Hunger-System zeichnen (Hunger-Balken)
        self.hunger_system.draw_hunger_ui(self.screen, 10, 200)
        
        # Farm-UI zeichnen
        mouse_pos = pygame.mouse.get_pos()
        self.farm_ui.draw(self.screen, self.camera, mouse_pos)
        
        # UI
        self.debug_panel.draw(self.screen)
        
        # Inventar zeichnen (über allem anderen)
        self.inventory.draw(self.screen)
        
        # Extra Hunger-Hint falls hungrig
        if self.hunger_system.is_hungry:
            self.hunger_system.draw_eating_hint(self.screen, 10, 280)
        
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
        
        # 💬 Chat-System zeichnen (über allem)
        self.chat_system.draw(self.screen)
        
        # Edit-Modus Anzeige
        if self.edit_mode:
            edit_text = "🎨 EDIT-MODUS - V: Toggle | Klick: Auswählen/Ziehen | Del: Löschen"
            edit_color = (255, 255, 0)
            pygame.font.init()
            edit_font = pygame.font.Font(None, 24)
            edit_surface = edit_font.render(edit_text, True, edit_color)
            # Zentriert oben
            edit_x = (SCREEN_WIDTH - edit_surface.get_width()) // 2
            edit_y = 50
            
            # Hintergrund für bessere Lesbarkeit
            bg_rect = pygame.Rect(edit_x - 10, edit_y - 5, edit_surface.get_width() + 20, edit_surface.get_height() + 10)
            pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect)
            pygame.draw.rect(self.screen, (255, 255, 0), bg_rect, 2)
            
            self.screen.blit(edit_surface, (edit_x, edit_y))
        
        # Asset-Input Anzeige
        if self.asset_input_mode:
            input_text = f"📝 Asset-Pfad: {self.asset_input_text}|"
            input_color = (0, 255, 255)
            pygame.font.init()
            input_font = pygame.font.Font(None, 24)
            input_surface = input_font.render(input_text, True, input_color)
            # Zentriert unten
            input_x = (SCREEN_WIDTH - input_surface.get_width()) // 2
            input_y = SCREEN_HEIGHT - 100
            
            # Hintergrund für bessere Lesbarkeit
            bg_rect = pygame.Rect(input_x - 10, input_y - 5, input_surface.get_width() + 20, input_surface.get_height() + 10)
            pygame.draw.rect(self.screen, (0, 0, 0, 200), bg_rect)
            pygame.draw.rect(self.screen, (0, 255, 255), bg_rect, 2)
            
            self.screen.blit(input_surface, (input_x, input_y))
            
            # Hilfe-Text
            help_text = "Enter: Laden | Escape: Abbrechen | Backspace: Löschen"
            help_surface = pygame.font.Font(None, 18).render(help_text, True, (200, 200, 200))
            help_x = (SCREEN_WIDTH - help_surface.get_width()) // 2
            help_y = input_y + 35
            self.screen.blit(help_surface, (help_x, help_y))
        
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
        print("")
        print("🧠 KI-STAMM STEUERUNG")
        print("="*50)
        print("🔬 I           = KI-Debug-Modus ein/aus")
        print("📊 K           = KI-Statistiken anzeigen")
        print("💰 O           = Ressourcen-Boost (zum Testen)")
        print("🚨 X           = Bedrohung simulieren (Hierarchisches System)")
        print("🤖 T           = Tribe Members teleportieren")
        print("")
        print("💬 CHAT-SYSTEM (2 VÖLKER):")
        print("   C           = Chat mit 🔴 Rotem Anführer")
        print("   Shift+C     = Chat mit 🔵 Blauem Anführer")  
        print("   Ctrl+C      = Chat mit BEIDEN Anführern")
        print("   Beispiele: 'baue 5 häuser', 'sammle holz', 'verteidige die stadt'")
        print("")
        print("🏛️ HIERARCHISCHES SYSTEM:")
        print("   🤝 Diplomat-Agent: Überwacht Bedrohungen")
        print("   ⚔️ Kriegsherr-Agent: Militärische Operationen") 
        print("   💰 Wirtschaftsminister: Ressourcen & Bau")
        print("   👥 Minions: Führen Befehle aus (Priorität-basiert)")
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
        """Platziert Demo-Tiere verteilt in der erweiterten 70x70 Welt"""
        if not USE_SIMPLE_WORLD or not self.world:
            return
            
        # Tiere weiter verteilt um Spieler herum in größerer Welt
        spawn_x, spawn_y = self.world.find_safe_spawn()
        
        # Mehr Tiere mit größerem Abstand
        # Kuh - etwas weiter entfernt
        cow_pos = (spawn_x + 120, spawn_y + 100)
        self.farming_system.place_animal("cow", cow_pos)
        
        # Schwein - mehr Abstand
        pig_pos = (spawn_x - 100, spawn_y + 140)
        self.farming_system.place_animal("pig", pig_pos)
        
        # Huhn - größerer Abstand
        chicken_pos = (spawn_x + 90, spawn_y - 110)
        self.farming_system.place_animal("chicken", chicken_pos)
        
        # Schaf - erweitert
        sheep_pos = (spawn_x - 90, spawn_y - 90)
        self.farming_system.place_animal("sheep", sheep_pos)
        
        # Zusätzliche Tiere für größere Welt
        # Zweite Kuh weiter weg
        cow2_pos = (spawn_x + 180, spawn_y - 80)
        self.farming_system.place_animal("cow", cow2_pos)
        
        # Zweites Huhn
        chicken2_pos = (spawn_x - 150, spawn_y + 80)
        self.farming_system.place_animal("chicken", chicken2_pos)
        
        print("Demo-Tiere platziert: 2 Kühe, Schwein, 2 Hühner, Schaf (erweiterte Verteilung)")
        print("Steuerung:")
        print("1/2 = Weizen/Karotte pflanzen (auf Farmland)")
        print("W = Gießen, H = Ernten")
        print("F = Tier füttern, C = Von Tier sammeln")
        print("🤖 T = AI Tribe Members zu dir teleportieren")
        print("🤖 I = AI Debug-Modus, K = AI Stats")
        print("🤖 R = Ressourcen anzeigen, B = Baufortschritt")
        print("🤖 O = Ressourcen-Boost (zum Testen)")
        print("💬 C = Chat mit 🔴 Rotem Anführer")
        print("💬 Shift+C = Chat mit 🔵 Blauem Anführer")
        print("💬 Ctrl+C = Chat mit BEIDEN Anführern")

if __name__ == '__main__':
    Game().run()
