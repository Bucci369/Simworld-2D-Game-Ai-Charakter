"""
3D zu 2D Sprite Konverter
Konvertiert 3D-Modelle zu 2D-Sprites für verschiedene Blickwinkel
"""

import os
import sys
import math
import pygame

# Versuche verschiedene 3D-Libraries zu importieren
AVAILABLE_3D_LIBS = []

try:
    import numpy as np
    AVAILABLE_3D_LIBS.append('numpy')
    print("✅ NumPy verfügbar")
except ImportError:
    print("❌ NumPy nicht verfügbar - verwende Pure Python")
    np = None

try:
    import trimesh
    AVAILABLE_3D_LIBS.append('trimesh')
    print("✅ Trimesh verfügbar")
except ImportError:
    print("❌ Trimesh nicht verfügbar")
    trimesh = None

try:
    import pygltflib
    AVAILABLE_3D_LIBS.append('pygltflib')
    print("✅ PyGLTFlib verfügbar")
except ImportError:
    print("❌ PyGLTFlib nicht verfügbar")

try:
    import open3d as o3d
    AVAILABLE_3D_LIBS.append('open3d')
    print("✅ Open3D verfügbar")
except ImportError:
    print("❌ Open3D nicht verfügbar")

class Model3DToSprite:
    """Konvertiert 3D-Modelle zu 2D-Sprites"""
    
    def __init__(self, output_size=(64, 64)):
        self.output_size = output_size
        self.angles = [0, 45, 90, 135, 180, 225, 270, 315]  # 8 Richtungen
        pygame.init()
    
    def load_model_with_trimesh(self, model_path):
        """Lädt 3D-Modell mit Trimesh"""
        try:
            if model_path.endswith('.glb') or model_path.endswith('.gltf'):
                # GLTF/GLB Datei
                scene = trimesh.load(model_path)
                if hasattr(scene, 'geometry'):
                    # Multi-mesh Szene
                    meshes = list(scene.geometry.values())
                    if meshes:
                        return meshes[0]  # Erstes Mesh nehmen
                else:
                    # Einzelnes Mesh
                    return scene
            else:
                return trimesh.load(model_path)
        except Exception as e:
            print(f"Fehler beim Laden mit Trimesh: {e}")
            return None
    
    def render_mesh_to_sprite(self, mesh, angle_degrees):
        """Rendert ein Mesh aus einem bestimmten Winkel zu einem 2D-Sprite"""
        if mesh is None or trimesh is None:
            return self.create_fallback_sprite(angle_degrees)
        
        try:
            # Rotiere das Mesh um die Y-Achse (vertikale Drehung)
            angle_rad = math.radians(angle_degrees)
            rotation_matrix = trimesh.transformations.rotation_matrix(
                angle_rad, [0, 1, 0]
            )
            rotated_mesh = mesh.copy()
            rotated_mesh.apply_transform(rotation_matrix)
            
            # Erstelle ein orthographisches Rendering
            # Berechne Bounding Box
            bounds = rotated_mesh.bounds
            size = bounds[1] - bounds[0]
            max_size = max(size)
            
            # Zentriere das Mesh
            center = (bounds[1] + bounds[0]) / 2
            rotated_mesh.vertices -= center
            
            # Skaliere für einheitliche Größe
            if max_size > 0:
                rotated_mesh.vertices *= (self.output_size[0] * 0.8) / max_size
            
            # Einfache orthographische Projektion (von vorne)
            vertices_2d = rotated_mesh.vertices[:, [0, 2]]  # X und Z Koordinaten
            
            # Erstelle ein 2D-Bild
            sprite_surface = pygame.Surface(self.output_size, pygame.SRCALPHA)
            sprite_surface.fill((0, 0, 0, 0))  # Transparent
            
            # Zeichne die Umrisse des Meshes
            if len(vertices_2d) > 0:
                # Transformiere Koordinaten für pygame (Bildschirm-Koordinaten)
                if np is not None:
                    screen_coords = vertices_2d + np.array(self.output_size) / 2
                    screen_coords[:, 1] = self.output_size[1] - screen_coords[:, 1]  # Y umkehren
                else:
                    # Pure Python Fallback
                    screen_coords = []
                    for coord in vertices_2d:
                        x = coord[0] + self.output_size[0] / 2
                        y = self.output_size[1] - (coord[1] + self.output_size[1] / 2)
                        screen_coords.append([x, y])
                
                # Zeichne Punkte als kleiner Charakter
                for coord in screen_coords:
                    x, y = int(coord[0]), int(coord[1])
                    if 0 <= x < self.output_size[0] and 0 <= y < self.output_size[1]:
                        pygame.draw.circle(sprite_surface, (100, 150, 255), (x, y), 1)
                
                # Zeichne eine vereinfachte Charakterform
                center_x, center_y = self.output_size[0] // 2, self.output_size[1] // 2
                
                # Körper (Rechteck)
                body_rect = pygame.Rect(center_x - 8, center_y - 4, 16, 20)
                pygame.draw.rect(sprite_surface, (80, 120, 200), body_rect)
                
                # Kopf (Kreis)
                pygame.draw.circle(sprite_surface, (255, 220, 177), (center_x, center_y - 12), 6)
                
                # Beine
                pygame.draw.rect(sprite_surface, (60, 100, 180), (center_x - 6, center_y + 16, 4, 12))
                pygame.draw.rect(sprite_surface, (60, 100, 180), (center_x + 2, center_y + 16, 4, 12))
                
                # Arme (abhängig vom Winkel)
                if angle_degrees in [0, 45, 315]:  # Vorne/rechts
                    pygame.draw.rect(sprite_surface, (80, 120, 200), (center_x + 8, center_y - 2, 8, 4))
                elif angle_degrees in [135, 180, 225]:  # Hinten/links  
                    pygame.draw.rect(sprite_surface, (80, 120, 200), (center_x - 16, center_y - 2, 8, 4))
                else:  # Seitlich
                    pygame.draw.rect(sprite_surface, (80, 120, 200), (center_x - 4, center_y - 8, 4, 8))
            
            return sprite_surface
            
        except Exception as e:
            print(f"Fehler beim Rendern: {e}")
            return self.create_fallback_sprite(angle_degrees)
    
    def create_fallback_sprite(self, angle_degrees):
        """Erstellt einen Fallback-Sprite wenn 3D-Rendering fehlschlägt"""
        sprite_surface = pygame.Surface(self.output_size, pygame.SRCALPHA)
        sprite_surface.fill((0, 0, 0, 0))
        
        center_x, center_y = self.output_size[0] // 2, self.output_size[1] // 2
        
        # Einfacher 2D-Charakter abhängig vom Winkel
        body_color = (100, 150, 255)
        head_color = (255, 220, 177)
        
        if angle_degrees in [315, 0, 45]:  # Vorne
            # Körper
            pygame.draw.rect(sprite_surface, body_color, (center_x - 8, center_y - 4, 16, 20))
            # Kopf
            pygame.draw.circle(sprite_surface, head_color, (center_x, center_y - 12), 6)
            # Beine
            pygame.draw.rect(sprite_surface, (60, 100, 180), (center_x - 6, center_y + 16, 4, 12))
            pygame.draw.rect(sprite_surface, (60, 100, 180), (center_x + 2, center_y + 16, 4, 12))
        elif angle_degrees in [135, 180, 225]:  # Hinten
            # Körper (dunkler)
            pygame.draw.rect(sprite_surface, (80, 120, 200), (center_x - 8, center_y - 4, 16, 20))
            # Kopf (Hinterkopf)
            pygame.draw.circle(sprite_surface, (200, 180, 140), (center_x, center_y - 12), 6)
            # Beine
            pygame.draw.rect(sprite_surface, (50, 80, 160), (center_x - 6, center_y + 16, 4, 12))
            pygame.draw.rect(sprite_surface, (50, 80, 160), (center_x + 2, center_y + 16, 4, 12))
        else:  # Seitlich (90, 270)
            # Körper (Profil)
            pygame.draw.ellipse(sprite_surface, body_color, (center_x - 4, center_y - 4, 12, 20))
            # Kopf (Profil)
            pygame.draw.ellipse(sprite_surface, head_color, (center_x - 3, center_y - 15, 10, 12))
            # Beine (Profil)
            pygame.draw.rect(sprite_surface, (60, 100, 180), (center_x - 2, center_y + 16, 6, 12))
        
        return sprite_surface
    
    def convert_model_to_sprites(self, model_path, output_dir):
        """Konvertiert ein 3D-Modell zu Sprite-Sheets für alle Richtungen"""
        print(f"🎯 Konvertiere {model_path}...")
        
        # Erstelle Output-Verzeichnis
        os.makedirs(output_dir, exist_ok=True)
        
        sprites = {}
        
        if 'trimesh' in AVAILABLE_3D_LIBS:
            # Versuche mit Trimesh zu laden
            mesh = self.load_model_with_trimesh(model_path)
            
            if mesh is not None:
                print("✅ 3D-Modell erfolgreich geladen")
                for angle in self.angles:
                    sprite = self.render_mesh_to_sprite(mesh, angle)
                    if sprite:
                        sprites[angle] = sprite
            else:
                print("⚠️ 3D-Modell konnte nicht geladen werden, erstelle Fallback-Sprites")
        
        # Fallback: Erstelle stylisierte 2D-Charaktere
        if not sprites:
            for angle in self.angles:
                sprites[angle] = self.create_fallback_sprite(angle)
        
        # Speichere einzelne Sprites
        for angle, sprite in sprites.items():
            filename = f"npc_angle_{angle:03d}.png"
            filepath = os.path.join(output_dir, filename)
            pygame.image.save(sprite, filepath)
            print(f"💾 Gespeichert: {filename}")
        
        # Erstelle Sprite-Sheet (alle Winkel in einer Datei)
        sprite_sheet = self.create_sprite_sheet(sprites)
        sheet_path = os.path.join(output_dir, "npc_spritesheet.png")
        pygame.image.save(sprite_sheet, sheet_path)
        print(f"📋 Sprite-Sheet erstellt: npc_spritesheet.png")
        
        return sprites, sheet_path
    
    def create_sprite_sheet(self, sprites):
        """Erstellt ein Sprite-Sheet aus einzelnen Sprites"""
        cols = 4  # 4 Spalten
        rows = 2  # 2 Reihen (8 Richtungen)
        
        sheet_width = cols * self.output_size[0]
        sheet_height = rows * self.output_size[1]
        
        sprite_sheet = pygame.Surface((sheet_width, sheet_height), pygame.SRCALPHA)
        sprite_sheet.fill((0, 0, 0, 0))
        
        for i, angle in enumerate(self.angles):
            if angle in sprites:
                col = i % cols
                row = i // cols
                x = col * self.output_size[0]
                y = row * self.output_size[1]
                sprite_sheet.blit(sprites[angle], (x, y))
        
        return sprite_sheet


def install_required_packages():
    """Installiert benötigte Pakete für 3D-zu-2D-Konvertierung"""
    packages = ['trimesh[easy]', 'pygltflib', 'numpy']
    
    for package in packages:
        print(f"Installiere {package}...")
        try:
            import subprocess
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ {package} erfolgreich installiert")
        except subprocess.CalledProcessError as e:
            print(f"❌ Fehler bei Installation von {package}: {e}")
        except Exception as e:
            print(f"❌ Unerwarteter Fehler: {e}")


def main():
    """Hauptfunktion - Konvertiert alle 3D-Modelle zu Sprites"""
    print("🎮 3D-zu-2D NPC Sprite Konverter")
    print("=" * 40)
    
    # Prüfe verfügbare Libraries
    if not AVAILABLE_3D_LIBS:
        print("⚠️ Keine 3D-Libraries verfügbar. Installiere benötigte Pakete...")
        install_required_packages()
        print("\n🔄 Bitte das Skript erneut ausführen nach der Installation.")
        return
    
    # Initialisiere Konverter
    converter = Model3DToSprite(output_size=(64, 64))
    
    # Finde 3D-Modelle
    model_paths = []
    assets_dir = "assets/Player"
    
    for root, dirs, files in os.walk(assets_dir):
        for file in files:
            if file.endswith(('.glb', '.gltf', '.obj', '.fbx')):
                model_paths.append(os.path.join(root, file))
    
    if not model_paths:
        print("❌ Keine 3D-Modelle gefunden!")
        # Erstelle trotzdem Fallback-Sprites
        output_dir = "assets/generated_sprites"
        converter.convert_model_to_sprites(None, output_dir)
        return
    
    print(f"🔍 Gefundene 3D-Modelle: {len(model_paths)}")
    for path in model_paths:
        print(f"  📁 {path}")
    
    # Konvertiere alle Modelle
    for model_path in model_paths:
        model_name = os.path.splitext(os.path.basename(model_path))[0]
        output_dir = f"assets/generated_sprites/{model_name}"
        
        try:
            sprites, sheet_path = converter.convert_model_to_sprites(model_path, output_dir)
            print(f"✅ {model_name} erfolgreich konvertiert!")
        except Exception as e:
            print(f"❌ Fehler bei {model_name}: {e}")
    
    print("\n🎉 Konvertierung abgeschlossen!")
    print("Die generierten Sprites befinden sich in assets/generated_sprites/")


if __name__ == "__main__":
    main()
