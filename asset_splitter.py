#!/usr/bin/env python3
"""
Asset Splitter Tool
Hilft beim manuellen Trennen von Asset-Collections
"""

import pygame
import os
import json
from pathlib import Path

class AssetSplitter:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1200, 800))
        pygame.display.set_caption("Asset Splitter - Klicke und ziehe um Bereiche zu markieren")
        self.clock = pygame.time.Clock()
        
        self.current_image = None
        self.image_path = None
        self.selections = []
        self.current_selection = None
        self.dragging = False
        self.start_pos = None
        
        # Zoom und Pan
        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 8.0
        self.zoom_step = 0.2
        self.pan_x = 10
        self.pan_y = 10
        self.panning = False
        self.pan_start = None
        
        # UI
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
    def load_image(self, path):
        """Lade ein Asset-Image"""
        try:
            self.current_image = pygame.image.load(path)
            self.image_path = path
            self.selections = []
            # Reset zoom und pan
            self.zoom = 1.0
            self.pan_x = 10
            self.pan_y = 10
            print(f"Geladen: {path}")
            print(f"Größe: {self.current_image.get_size()}")
        except Exception as e:
            print(f"Fehler beim Laden: {e}")
            
    def screen_to_image_coords(self, screen_pos):
        """Konvertiere Bildschirmkoordinaten zu Bildkoordinaten"""
        if not self.current_image:
            return screen_pos
            
        screen_x, screen_y = screen_pos
        # Berücksichtige Pan und Zoom
        image_x = (screen_x - self.pan_x) / self.zoom
        image_y = (screen_y - self.pan_y) / self.zoom
        return (int(image_x), int(image_y))
        
    def image_to_screen_coords(self, image_pos):
        """Konvertiere Bildkoordinaten zu Bildschirmkoordinaten"""
        if not self.current_image:
            return image_pos
            
        image_x, image_y = image_pos
        # Wende Zoom und Pan an
        screen_x = image_x * self.zoom + self.pan_x
        screen_y = image_y * self.zoom + self.pan_y
        return (int(screen_x), int(screen_y))
            
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.save_selections()
                elif event.key == pygame.K_c:
                    self.selections.clear()
                    print("Auswahl gelöscht")
                elif event.key == pygame.K_u and self.selections:
                    self.selections.pop()
                    print("Letzte Auswahl rückgängig")
                elif event.key == pygame.K_r:
                    # Reset zoom und pan
                    self.zoom = 1.0
                    self.pan_x = 10
                    self.pan_y = 10
                    print("Zoom und Pan zurückgesetzt")
                elif event.key == pygame.K_ESCAPE:
                    return False
                    
            elif event.type == pygame.MOUSEWHEEL:
                # Zoom mit Mausrad
                mouse_pos = pygame.mouse.get_pos()
                old_zoom = self.zoom
                
                if event.y > 0:  # Zoom in
                    self.zoom = min(self.max_zoom, self.zoom + self.zoom_step)
                else:  # Zoom out
                    self.zoom = max(self.min_zoom, self.zoom - self.zoom_step)
                
                # Zoom zum Mauszeiger hin
                if self.zoom != old_zoom:
                    zoom_factor = self.zoom / old_zoom
                    self.pan_x = mouse_pos[0] - (mouse_pos[0] - self.pan_x) * zoom_factor
                    self.pan_y = mouse_pos[1] - (mouse_pos[1] - self.pan_y) * zoom_factor
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Linke Maustaste - Auswahl
                    self.start_pos = self.screen_to_image_coords(event.pos)
                    self.dragging = True
                elif event.button == 3:  # Rechte Maustaste - Pan
                    self.pan_start = event.pos
                    self.panning = True
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.dragging:
                    end_pos = self.screen_to_image_coords(event.pos)
                    if self.start_pos and end_pos:
                        # Berechne Rechteck in Bildkoordinaten
                        x1, y1 = self.start_pos
                        x2, y2 = end_pos
                        rect = pygame.Rect(min(x1, x2), min(y1, y2), 
                                         abs(x2 - x1), abs(y2 - y1))
                        if rect.width > 2 and rect.height > 2:  # Minimum Größe in Bildkoordinaten
                            self.selections.append(rect)
                            print(f"Auswahl hinzugefügt: {rect}")
                    self.dragging = False
                    self.start_pos = None
                elif event.button == 3:  # Rechte Maustaste loslassen
                    self.panning = False
                    self.pan_start = None
                    
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging and self.start_pos:
                    # Aktuelle Auswahl für Vorschau in Bildkoordinaten
                    end_pos = self.screen_to_image_coords(event.pos)
                    x1, y1 = self.start_pos
                    x2, y2 = end_pos
                    self.current_selection = pygame.Rect(min(x1, x2), min(y1, y2), 
                                                       abs(x2 - x1), abs(y2 - y1))
                elif self.panning and self.pan_start:
                    # Pan das Bild
                    dx = event.pos[0] - self.pan_start[0]
                    dy = event.pos[1] - self.pan_start[1]
                    self.pan_x += dx
                    self.pan_y += dy
                    self.pan_start = event.pos
                    
        return True
        
    def save_selections(self):
        """Speichere die markierten Bereiche als separate Dateien"""
        if not self.current_image or not self.selections:
            print("Keine Auswahl zum Speichern")
            return
            
        # Erstelle Ausgabe-Ordner
        base_name = Path(self.image_path).stem
        output_dir = Path("assets/split") / base_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Speichere jeden markierten Bereich
        for i, rect in enumerate(self.selections):
            # Extrahiere Teilbereich
            subsurface = self.current_image.subsurface(rect)
            
            # Speichere als PNG
            filename = f"{base_name}_{i+1:03d}.png"
            filepath = output_dir / filename
            pygame.image.save(subsurface, str(filepath))
            print(f"Gespeichert: {filepath}")
            
        # Speichere auch Metadaten
        metadata = {
            "source_image": self.image_path,
            "selections": [(rect.x, rect.y, rect.width, rect.height) for rect in self.selections],
            "total_items": len(self.selections)
        }
        
        metadata_file = output_dir / f"{base_name}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        print(f"Metadaten gespeichert: {metadata_file}")
        print(f"Insgesamt {len(self.selections)} Items gespeichert in {output_dir}")
        
    def draw(self):
        """Zeichne die UI"""
        self.screen.fill((50, 50, 50))
        
        if self.current_image:
            # Skaliere das Bild basierend auf Zoom
            scaled_width = int(self.current_image.get_width() * self.zoom)
            scaled_height = int(self.current_image.get_height() * self.zoom)
            scaled_image = pygame.transform.scale(self.current_image, (scaled_width, scaled_height))
            
            # Zeichne das skalierte Bild an der Pan-Position
            self.screen.blit(scaled_image, (self.pan_x, self.pan_y))
            
            # Zeichne gespeicherte Auswahlen (in Bildschirmkoordinaten)
            for i, rect in enumerate(self.selections):
                # Konvertiere Bildkoordinaten zu Bildschirmkoordinaten
                screen_x = rect.x * self.zoom + self.pan_x
                screen_y = rect.y * self.zoom + self.pan_y
                screen_width = rect.width * self.zoom
                screen_height = rect.height * self.zoom
                
                screen_rect = pygame.Rect(screen_x, screen_y, screen_width, screen_height)
                pygame.draw.rect(self.screen, (0, 255, 0), screen_rect, 2)
                
                # Nummer anzeigen
                text = self.small_font.render(str(i+1), True, (255, 255, 255))
                self.screen.blit(text, (screen_rect.x + 2, screen_rect.y + 2))
                
            # Zeichne aktuelle Auswahl (beim Ziehen)
            if self.current_selection:
                screen_x = self.current_selection.x * self.zoom + self.pan_x
                screen_y = self.current_selection.y * self.zoom + self.pan_y
                screen_width = self.current_selection.width * self.zoom
                screen_height = self.current_selection.height * self.zoom
                
                screen_rect = pygame.Rect(screen_x, screen_y, screen_width, screen_height)
                pygame.draw.rect(self.screen, (255, 255, 0), screen_rect, 2)
        
        # UI Text
        y_offset = 10
        ui_x = 10
        
        if self.image_path:
            text = self.font.render(f"Datei: {Path(self.image_path).name}", True, (255, 255, 255))
            self.screen.blit(text, (ui_x, y_offset))
            y_offset += 30
            
        # Zoom Info
        zoom_text = self.font.render(f"Zoom: {self.zoom:.1f}x", True, (255, 255, 0))
        self.screen.blit(text, (ui_x, y_offset))
        y_offset += 30
            
        instructions = [
            "STEUERUNG:",
            "• Linke Maus: Klicken und Ziehen zum Markieren",
            "• Rechte Maus: Ziehen zum Verschieben (Pan)",
            "• Mausrad: Zoomen",
            "• R: Zoom und Pan zurücksetzen",
            "• C: Alle Auswahlen löschen",
            "• U: Letzte Auswahl rückgängig", 
            "• Ctrl+S: Auswahlen speichern",
            "• ESC: Beenden",
            "",
            f"Markierte Bereiche: {len(self.selections)}",
            f"Zoom: {self.zoom:.1f}x (Bereich: {self.min_zoom:.1f}x - {self.max_zoom:.1f}x)"
        ]
        
        for instruction in instructions:
            if instruction.startswith("•"):
                color = (255, 255, 0)
            elif instruction.startswith("Markierte") or instruction.startswith("Zoom:"):
                color = (0, 255, 255)
            else:
                color = (200, 200, 200)
                
            text = self.small_font.render(instruction, True, color)
            self.screen.blit(text, (ui_x, y_offset))
            y_offset += 22
            
        pygame.display.flip()
        
    def run(self, image_path=None):
        """Hauptschleife"""
        if image_path:
            self.load_image(image_path)
            
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            self.clock.tick(60)
            
        pygame.quit()

def main():
    splitter = AssetSplitter()
    
    # Beispiel: Lade das farm.png
    farm_path = "assets/Pixel Crawler - Free Pack/Environment/Props/Static/Farm.png"
    if os.path.exists(farm_path):
        splitter.run(farm_path)
    else:
        print(f"Datei nicht gefunden: {farm_path}")
        print("Verfügbare Assets:")
        # Zeige verfügbare PNG Dateien
        for root, dirs, files in os.walk("assets"):
            for file in files:
                if file.endswith('.png'):
                    print(f"  {os.path.join(root, file)}")

if __name__ == "__main__":
    main()
