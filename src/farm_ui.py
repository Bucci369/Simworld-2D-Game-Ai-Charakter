import pygame
import os
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE

class FarmUI:
    """UI-System für Farming mit Maus-Steuerung"""
    
    def __init__(self):
        # UI-Dimensionen
        self.ui_height = 120
        self.ui_y = SCREEN_HEIGHT - self.ui_height
        self.ui_rect = pygame.Rect(0, self.ui_y, SCREEN_WIDTH, self.ui_height)
        
        # Fonts
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Farm-Modi
        self.mode = "normal"  # "normal", "build_farm", "plant_crops"
        self.selected_crop = "carrot"
        self.farm_area_start = None
        self.farm_area_end = None
        self.farm_tiles = set()  # Set von (tile_x, tile_y) für Farm-Tiles
        
        # UI-Buttons
        self.buttons = {}
        self._create_buttons()
        
        # Grid-Overlay
        self.show_grid = False
        self.grid_color = (255, 255, 255, 100)
        
        # Crop-Assets laden
        self.crop_assets = self._load_crop_assets()
        
        # Farm-Tile Asset laden
        self.farmland_tile = self._load_farmland_tile()
        
    def _create_buttons(self):
        """Erstelle UI-Buttons"""
        button_width = 120
        button_height = 35
        margin = 10
        start_x = (SCREEN_WIDTH - (button_width * 3 + margin * 2)) // 2
        
        # Farm bauen Button
        self.buttons['build_farm'] = {
            'rect': pygame.Rect(start_x, self.ui_y + 20, button_width, button_height),
            'text': 'Farm bauen',
            'active': False
        }
        
        # Pflanzen Button
        self.buttons['plant_crops'] = {
            'rect': pygame.Rect(start_x + button_width + margin, self.ui_y + 20, button_width, button_height),
            'text': 'Karotten pflanzen',
            'active': False
        }
        
        # Normal Modus Button
        self.buttons['normal'] = {
            'rect': pygame.Rect(start_x + (button_width + margin) * 2, self.ui_y + 20, button_width, button_height),
            'text': 'Normal',
            'active': True
        }
        
        # Ernten Button (unter plant_crops)
        self.buttons['harvest'] = {
            'rect': pygame.Rect(start_x + button_width + margin, self.ui_y + 65, button_width, button_height),
            'text': 'Ernten',
            'active': False
        }
        
        # Gießen Button (unter build_farm)
        self.buttons['water'] = {
            'rect': pygame.Rect(start_x, self.ui_y + 65, button_width, button_height),
            'text': 'Gießen 💧',
            'active': False
        }
    
    def _load_crop_assets(self):
        """Lade Karotten-Assets"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        assets = {}
        
        for stage in [1, 2, 3]:
            asset_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', f'Karotte_stufe{stage}.png')
            if os.path.exists(asset_path):
                try:
                    img = pygame.image.load(asset_path).convert_alpha()
                    print(f"Original Karotten-Asset Stufe {stage}: {img.get_size()}")
                    
                    # Bessere Skalierung für kleine Assets
                    original_size = img.get_size()
                    if original_size[0] < TILE_SIZE or original_size[1] < TILE_SIZE:
                        # Für kleine Assets: Verwende NEAREST (pixelig) anstatt smooth
                        scaled_img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    else:
                        scaled_img = pygame.transform.smoothscale(img, (TILE_SIZE, TILE_SIZE))
                    
                    assets[f'carrot_stage_{stage}'] = scaled_img
                    print(f"✅ Karotten-Asset geladen: Stufe {stage} - Original: {original_size} → Skaliert: {scaled_img.get_size()}")
                except Exception as e:
                    print(f"❌ Fehler beim Laden von Karotte Stufe {stage}: {e}")
                    # Fallback: Farbiges Rechteck
                    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    colors = {1: (139, 69, 19), 2: (255, 165, 0), 3: (255, 140, 0)}  # Braun, Orange, Orange-Rot
                    surf.fill(colors[stage])
                    assets[f'carrot_stage_{stage}'] = surf
                    print(f"🔄 Fallback für Karotte Stufe {stage} erstellt")
            else:
                print(f"❌ Asset nicht gefunden: {asset_path}")
                # Fallback erstellen
                surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                colors = {1: (139, 69, 19), 2: (255, 165, 0), 3: (255, 140, 0)}
                surf.fill(colors[stage])
                assets[f'carrot_stage_{stage}'] = surf
                print(f"🔄 Fallback für fehlende Karotte Stufe {stage} erstellt")
        
        return assets
    
    def _load_farmland_tile(self):
        """Lade FarmLand_Tile.png Asset"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        farmland_path = os.path.join(base_dir, 'assets', 'Tiles', 'FarmLand_Tile.png')
        
        if os.path.exists(farmland_path):
            try:
                img = pygame.image.load(farmland_path).convert_alpha()
                # Skaliere auf Tile-Größe
                scaled_img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                print("FarmLand_Tile.png erfolgreich geladen!")
                return scaled_img
            except Exception as e:
                print(f"Fehler beim Laden von FarmLand_Tile.png: {e}")
        else:
            print(f"FarmLand_Tile.png nicht gefunden: {farmland_path}")
        
        # Fallback: Braunes Rechteck
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill((139, 69, 19))  # Braun für Farmland
        return surf
    
    def handle_mouse_event(self, event, camera):
        """Behandle Maus-Events für das Farm-UI"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Linksklick
            mouse_pos = pygame.mouse.get_pos()
            
            # Prüfe UI-Button-Klicks
            if self.ui_rect.collidepoint(mouse_pos):
                return self._handle_ui_click(mouse_pos)
            
            # Welt-Klicks je nach Modus
            else:
                world_pos = camera.screen_to_world(mouse_pos)
                return self._handle_world_click(world_pos, event)
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # Ende der Farm-Bereich-Auswahl
            if self.mode == "build_farm" and self.farm_area_start:
                mouse_pos = pygame.mouse.get_pos()
                if not self.ui_rect.collidepoint(mouse_pos):
                    world_pos = camera.screen_to_world(mouse_pos)
                    self.farm_area_end = self._snap_to_grid(world_pos)
                    self._create_farm_area()
                    return True
        
        return False
    
    def _handle_ui_click(self, mouse_pos):
        """Behandle Klicks auf UI-Buttons"""
        for button_name, button in self.buttons.items():
            if button['rect'].collidepoint(mouse_pos):
                # Alle Buttons deaktivieren
                for btn in self.buttons.values():
                    btn['active'] = False
                
                # Gewählten Button aktivieren
                button['active'] = True
                
                # Modus setzen
                if button_name == 'build_farm':
                    self.mode = "build_farm"
                    self.show_grid = True
                    print("Farm-Bau-Modus aktiviert. Ziehe einen Bereich auf!")
                elif button_name == 'plant_crops':
                    self.mode = "plant_crops"
                    self.show_grid = False  # Kein Grid beim Pflanzen
                    print("Pflanz-Modus aktiviert. Klicke auf Farm-Tiles um zu pflanzen!")
                elif button_name == 'harvest':
                    self.mode = "harvest"
                    self.show_grid = False  # Kein Grid beim Ernten
                    print("Ernte-Modus aktiviert. Klicke auf reife Pflanzen!")
                elif button_name == 'water':
                    self.mode = "water"
                    self.show_grid = False  # Kein Grid beim Gießen
                    print("Gießen-Modus aktiviert. Klicke auf Pflanzen um sie zu gießen!")
                else:  # normal
                    self.mode = "normal"
                    self.show_grid = False
                    self.farm_area_start = None
                    self.farm_area_end = None
                    print("Normal-Modus aktiviert")
                
                return True
        return False
    
    def _handle_world_click(self, world_pos, event):
        """Behandle Klicks in der Spielwelt"""
        tile_pos = self._snap_to_grid(world_pos)
        tile_x, tile_y = int(tile_pos[0] // TILE_SIZE), int(tile_pos[1] // TILE_SIZE)
        
        if self.mode == "build_farm":
            if not self.farm_area_start:
                self.farm_area_start = tile_pos
                print(f"Farm-Bereich Start: {tile_pos}")
                return True
                
        elif self.mode == "plant_crops":
            # Nur auf Farm-Tiles pflanzen
            if (tile_x, tile_y) in self.farm_tiles:
                return {'action': 'plant', 'pos': tile_pos, 'crop': self.selected_crop}
            else:
                print("Kann nur auf Farm-Bereichen pflanzen!")
                
        elif self.mode == "harvest":
            return {'action': 'harvest', 'pos': tile_pos}
            
        elif self.mode == "water":
            return {'action': 'water', 'pos': tile_pos}
            
        return False
    
    def _snap_to_grid(self, world_pos):
        """Snapp Position zum Grid"""
        tile_x = int(world_pos[0] // TILE_SIZE) * TILE_SIZE
        tile_y = int(world_pos[1] // TILE_SIZE) * TILE_SIZE
        return (tile_x, tile_y)
    
    def _create_farm_area(self):
        """Erstelle Farm-Bereich zwischen Start und Ende"""
        if not self.farm_area_start or not self.farm_area_end:
            return
            
        start_tile_x = int(self.farm_area_start[0] // TILE_SIZE)
        start_tile_y = int(self.farm_area_start[1] // TILE_SIZE)
        end_tile_x = int(self.farm_area_end[0] // TILE_SIZE)
        end_tile_y = int(self.farm_area_end[1] // TILE_SIZE)
        
        # Sorge dafür, dass start <= end
        min_x, max_x = min(start_tile_x, end_tile_x), max(start_tile_x, end_tile_x)
        min_y, max_y = min(start_tile_y, end_tile_y), max(start_tile_y, end_tile_y)
        
        # Füge alle Tiles im Bereich hinzu
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                self.farm_tiles.add((x, y))
        
        farm_count = len(self.farm_tiles)
        print(f"Farm-Bereich erstellt! {farm_count} Felder verfügbar.")
        
        # Reset und Grid ausblenden nach Farm-Erstellung
        self.farm_area_start = None
        self.farm_area_end = None
        self.show_grid = False  # Grid ausblenden
        
        # Wechsle automatisch in Pflanz-Modus nach Farm-Erstellung
        self.mode = "plant_crops"
        for btn in self.buttons.values():
            btn['active'] = False
        self.buttons['plant_crops']['active'] = True
        print("Automatisch in Pflanz-Modus gewechselt!")
    
    def get_current_selection(self, mouse_pos, camera):
        """Zeige aktuelle Auswahl basierend auf Maus-Position"""
        if self.mode == "build_farm" and self.farm_area_start:
            world_pos = camera.screen_to_world(mouse_pos)
            current_end = self._snap_to_grid(world_pos)
            return {
                'type': 'farm_area',
                'start': self.farm_area_start,
                'end': current_end
            }
        elif self.mode in ["plant_crops", "harvest"]:
            world_pos = camera.screen_to_world(mouse_pos)
            tile_pos = self._snap_to_grid(world_pos)
            return {
                'type': 'single_tile',
                'pos': tile_pos
            }
        return None
    
    def draw(self, screen, camera, mouse_pos=None):
        """Zeichne das Farm-UI"""
        # UI-Hintergrund
        ui_surface = pygame.Surface((SCREEN_WIDTH, self.ui_height), pygame.SRCALPHA)
        ui_surface.fill((0, 0, 0, 180))  # Halbtransparent
        pygame.draw.rect(ui_surface, (100, 100, 100), (0, 0, SCREEN_WIDTH, self.ui_height), 2)
        screen.blit(ui_surface, (0, self.ui_y))
        
        # Buttons zeichnen
        for button_name, button in self.buttons.items():
            color = (70, 130, 180) if button['active'] else (60, 60, 60)
            border_color = (255, 255, 255) if button['active'] else (150, 150, 150)
            
            pygame.draw.rect(screen, color, button['rect'])
            pygame.draw.rect(screen, border_color, button['rect'], 2)
            
            # Button-Text
            text_surface = self.font.render(button['text'], True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=button['rect'].center)
            screen.blit(text_surface, text_rect)
        
        # Mode-Info
        mode_text = f"Modus: {self.mode.replace('_', ' ').title()}"
        if self.mode == "build_farm":
            mode_text += " - Ziehe einen Bereich auf"
        elif self.mode == "plant_crops":
            mode_text += " - Klicke auf Farm-Felder"
        elif self.mode == "harvest":
            mode_text += " - Klicke auf reife Pflanzen"
        elif self.mode == "water":
            mode_text += " - Klicke auf Pflanzen zum Gießen"
            
        mode_surface = self.small_font.render(mode_text, True, (255, 255, 255))
        screen.blit(mode_surface, (20, self.ui_y + 5))
        
        # Farm-Bereich Info
        if self.farm_tiles:
            farm_info = f"Farm-Felder: {len(self.farm_tiles)}"
            farm_surface = self.small_font.render(farm_info, True, (255, 255, 255))
            screen.blit(farm_surface, (SCREEN_WIDTH - 150, self.ui_y + 5))
        
        # Grid und Auswahl-Overlay zeichnen
        if self.show_grid and self.mode == "build_farm":
            self._draw_grid_overlay(screen, camera)
            
        if mouse_pos and not self.ui_rect.collidepoint(mouse_pos):
            self._draw_selection_overlay(screen, camera, mouse_pos)
    
    def _draw_grid_overlay(self, screen, camera):
        """Zeichne Grid-Overlay nur im Farm-Bau-Modus"""
        if self.mode != "build_farm":
            return
            
        # Nur während des Ziehens das Grid zeigen
        # Farm-Tiles werden jetzt als echte Tiles gezeichnet, nicht als Overlay
    
    def _draw_selection_overlay(self, screen, camera, mouse_pos):
        """Zeichne Auswahl-Overlay"""
        selection = self.get_current_selection(mouse_pos, camera)
        
        if selection:
            if selection['type'] == 'farm_area':
                # Zeige Farm-Bereich-Auswahl
                start_screen = camera.world_to_screen(selection['start'])
                end_screen = camera.world_to_screen(selection['end'])
                
                # Berechne Rechteck
                min_x = min(start_screen[0], end_screen[0])
                min_y = min(start_screen[1], end_screen[1])
                width = abs(end_screen[0] - start_screen[0]) + TILE_SIZE
                height = abs(end_screen[1] - start_screen[1]) + TILE_SIZE
                
                selection_rect = pygame.Rect(min_x, min_y, width, height)
                pygame.draw.rect(screen, (255, 255, 0, 100), selection_rect)
                pygame.draw.rect(screen, (255, 255, 0), selection_rect, 3)
                
            elif selection['type'] == 'single_tile':
                # Zeige einzelnes Tile
                screen_pos = camera.world_to_screen(selection['pos'])
                tile_rect = pygame.Rect(screen_pos[0], screen_pos[1], TILE_SIZE, TILE_SIZE)
                
                if self.mode == "plant_crops":
                    color = (0, 255, 0) if self._is_farm_tile(selection['pos']) else (255, 0, 0)
                elif self.mode == "harvest":
                    color = (255, 165, 0)
                else:
                    color = (255, 255, 255)
                    
                pygame.draw.rect(screen, (*color, 100), tile_rect)
                pygame.draw.rect(screen, color, tile_rect, 3)
    
    def _is_farm_tile(self, world_pos):
        """Prüfe ob Position ein Farm-Tile ist"""
        tile_x = int(world_pos[0] // TILE_SIZE)
        tile_y = int(world_pos[1] // TILE_SIZE)
        return (tile_x, tile_y) in self.farm_tiles
    
    def draw_crops(self, screen, camera, crops):
        """Zeichne alle Pflanzen mit den richtigen Assets"""
        for crop in crops.values():
            screen_pos = camera.world_to_screen((crop.x, crop.y))
            
            # Nur zeichnen wenn sichtbar
            if (-TILE_SIZE <= screen_pos[0] < SCREEN_WIDTH and 
                -TILE_SIZE <= screen_pos[1] < SCREEN_HEIGHT):
                
                # Bestimme Asset basierend auf Wachstumsstadium
                if crop.growth_stage == 0:
                    # Samen - kleiner brauner Punkt
                    pygame.draw.circle(screen, (139, 69, 19), 
                                     (screen_pos[0] + TILE_SIZE//2, screen_pos[1] + TILE_SIZE//2), 3)
                elif 1 <= crop.growth_stage <= 3:
                    # Verwende Karotten-Assets
                    asset_key = f'carrot_stage_{crop.growth_stage}'
                    if asset_key in self.crop_assets:
                        # Zeichne das echte Asset
                        screen.blit(self.crop_assets[asset_key], screen_pos)
                    else:
                        # Fallback falls Asset fehlt
                        color = (255, 140, 0) if crop.growth_stage == 3 else (255, 165, 0)
                        pygame.draw.circle(screen, color, 
                                         (screen_pos[0] + TILE_SIZE//2, screen_pos[1] + TILE_SIZE//2), 
                                         8 + crop.growth_stage * 2)
                
                # Status-Indikatoren
                if crop.watered and crop.growth_stage < 3:
                    # Blaue Punkte für "gegossen"
                    pygame.draw.circle(screen, (0, 100, 255), 
                                     (screen_pos[0] + TILE_SIZE - 8, screen_pos[1] + 8), 4)
                
                if crop.ready_to_harvest:
                    # Grüner Rahmen für "bereit zum Ernten"
                    harvest_rect = pygame.Rect(screen_pos[0], screen_pos[1], TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(screen, (0, 255, 0), harvest_rect, 3)
    
    def get_farm_tiles(self):
        """Gib alle Farm-Tiles zurück"""
        return self.farm_tiles.copy()
    
    def draw_farm_tiles(self, screen, camera):
        """Zeichne Farm-Tiles mit FarmLand_Tile.png Textur"""
        for tile_x, tile_y in self.farm_tiles:
            world_x, world_y = tile_x * TILE_SIZE, tile_y * TILE_SIZE
            screen_pos = camera.world_to_screen((world_x, world_y))
            
            # Nur zeichnen wenn sichtbar
            if (-TILE_SIZE <= screen_pos[0] < SCREEN_WIDTH and 
                -TILE_SIZE <= screen_pos[1] < SCREEN_HEIGHT):
                screen.blit(self.farmland_tile, screen_pos)
