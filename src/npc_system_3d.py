"""
3D NPC System mit echtem 3D-Rendering in Pygame
Verwendet PyOpenGL für echtes 3D-Rendering der GLTF/GLB-Modelle
"""

import os
import math
import random
import pygame
from settings import TILE_SIZE

# 3D-Rendering Libraries
try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    import OpenGL.GL.shaders as shaders
    import numpy as np
    OPENGL_AVAILABLE = True
    print("✅ OpenGL verfügbar!")
except ImportError as e:
    OPENGL_AVAILABLE = False
    print(f"❌ OpenGL nicht verfügbar: {e}")

try:
    import trimesh
    TRIMESH_AVAILABLE = True
    print("✅ Trimesh verfügbar!")
except ImportError:
    TRIMESH_AVAILABLE = False
    print("❌ Trimesh nicht verfügbar")

class NPC3D:
    """Ein 3D-NPC mit echtem 3D-Modell"""
    
    def __init__(self, pos, world=None, npc_id=0, model_path=None):
        self.world = world
        self.npc_id = npc_id
        self.position = pygame.Vector3(pos[0], 0, pos[1])  # 3D-Position (x, y, z)
        self.rotation_y = 0.0  # Y-Rotation (Blickrichtung)
        
        # Bewegungs-AI (gleich wie vorher)
        self.speed = 120
        self.target_pos = None
        self.arrive_threshold = 8
        self.wander_timer = 0.0
        self.wander_delay = random.uniform(2.0, 5.0)
        self.home_area = pygame.Vector3(pos[0], 0, pos[1])
        self.wander_radius = 150
        
        # Schwarm-Verhalten
        self.flock_mates = []
        self.separation_distance = 40
        self.cohesion_distance = 80
        self.alignment_distance = 60
        
        # 3D-Model loading
        self.mesh = None
        self.vbo = None  # Vertex Buffer Object
        self.texture_id = None
        self.vertex_count = 0
        
        # Bounding Box für 2D-Kollision
        self.rect = pygame.Rect(pos[0] - 16, pos[1] - 16, 32, 32)
        
        if OPENGL_AVAILABLE and TRIMESH_AVAILABLE and model_path:
            self.load_3d_model(model_path)
        else:
            print(f"NPC {npc_id}: Verwende Fallback ohne 3D-Modell")
    
    def load_3d_model(self, model_path):
        """Lädt ein 3D-Modell (GLB/GLTF) mit Trimesh"""
        try:
            print(f"🎯 Lade 3D-Modell: {model_path}")
            
            # Lade Modell mit Trimesh
            scene = trimesh.load(model_path)
            
            if hasattr(scene, 'geometry'):
                # Multi-mesh Szene - nimm das erste Mesh
                meshes = list(scene.geometry.values())
                if meshes:
                    self.mesh = meshes[0]
            else:
                # Einzelnes Mesh
                self.mesh = scene
            
            if self.mesh is not None:
                print(f"✅ Modell geladen: {len(self.mesh.vertices)} Vertices, {len(self.mesh.faces)} Faces")
                self.prepare_opengl_buffers()
            else:
                print("❌ Kein Mesh im Modell gefunden")
                
        except Exception as e:
            print(f"❌ Fehler beim Laden des 3D-Modells: {e}")
            self.mesh = None
    
    def prepare_opengl_buffers(self):
        """Bereitet OpenGL Vertex Buffer vor"""
        if self.mesh is None or not OPENGL_AVAILABLE:
            return
        
        try:
            # Vertex-Daten vorbereiten
            vertices = self.mesh.vertices.astype(np.float32)
            
            # Normalisiere und skaliere das Modell
            bounds = self.mesh.bounds
            size = bounds[1] - bounds[0]
            max_size = np.max(size)
            
            # Zentriere das Modell
            center = (bounds[1] + bounds[0]) / 2
            vertices -= center
            
            # Skaliere auf passende Größe (etwa Spieler-Größe)
            if max_size > 0:
                vertices *= 32.0 / max_size  # 32 Pixel Größe
            
            # Vertex Buffer Object erstellen
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
            
            self.vertex_count = len(vertices)
            print(f"✅ OpenGL Buffer erstellt: {self.vertex_count} Vertices")
            
        except Exception as e:
            print(f"❌ Fehler bei OpenGL Buffer: {e}")
            self.vbo = None
    
    def update(self, dt):
        """Update der NPC AI und Bewegung (gleich wie 2D-Version)"""
        self.wander_timer += dt
        moving = False
        
        # Schwarm-Verhalten berechnen
        flock_force = self._calculate_flocking_force()
        
        # Neue Ziel-Position auswählen wenn nötig
        if not self.target_pos or self.wander_timer >= self.wander_delay:
            self.target_pos = self._get_random_target_in_area()
            self.wander_timer = 0.0
            self.wander_delay = random.uniform(2.0, 5.0)
        
        # Bewegung zum Ziel mit Schwarm-Einfluss
        if self.target_pos:
            current = pygame.Vector2(self.position.x, self.position.z)
            target_2d = pygame.Vector2(self.target_pos.x, self.target_pos.z)
            
            delta = target_2d - current
            dist = delta.length()
            
            if dist <= self.arrive_threshold:
                self.target_pos = None
            else:
                # Kombiniere Ziel-Richtung mit Schwarm-Kräften
                if dist > 0:
                    direction = delta / dist
                else:
                    direction = pygame.Vector2(0, 0)
                
                # Füge Schwarm-Kräfte hinzu
                direction += flock_force
                
                # Normalisiere falls nötig
                if direction.length() > 0:
                    direction = direction.normalize()
                
                # Berechne Bewegung
                step = direction * self.speed * dt
                new_pos = current + step
                
                # Update 3D-Position
                self.position.x = new_pos.x
                self.position.z = new_pos.y
                
                # Update 2D-Rect für Kollision
                self.rect.center = (int(new_pos.x), int(new_pos.y))
                
                # Update Rotation (Blickrichtung)
                if direction.length() > 0:
                    self.rotation_y = math.degrees(math.atan2(direction.x, direction.y))
                
                moving = True
    
    def _calculate_flocking_force(self):
        """Berechnet Schwarm-Kräfte (gleich wie 2D-Version)"""
        if not self.flock_mates:
            return pygame.Vector2(0, 0)
            
        my_pos = pygame.Vector2(self.position.x, self.position.z)
        
        separation = pygame.Vector2(0, 0)
        separation_count = 0
        cohesion = pygame.Vector2(0, 0)
        cohesion_count = 0
        
        for mate in self.flock_mates:
            if mate == self:
                continue
                
            mate_pos = pygame.Vector2(mate.position.x, mate.position.z)
            distance = my_pos.distance_to(mate_pos)
            
            # Separation
            if distance < self.separation_distance and distance > 0:
                diff = my_pos - mate_pos
                diff = diff.normalize() / distance
                separation += diff
                separation_count += 1
            
            # Cohesion
            if distance < self.cohesion_distance:
                cohesion += mate_pos
                cohesion_count += 1
        
        # Normalisiere die Kräfte
        if separation_count > 0:
            separation /= separation_count
            if separation.length() > 0:
                separation = separation.normalize() * 1.5
        
        if cohesion_count > 0:
            cohesion /= cohesion_count
            cohesion = cohesion - my_pos
            if cohesion.length() > 0:
                cohesion = cohesion.normalize() * 0.5
        
        return separation + cohesion
    
    def _get_random_target_in_area(self):
        """Gibt eine zufällige 3D-Position in der Nähe des Home-Bereichs zurück"""
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(20, self.wander_radius)
        
        target_x = self.home_area.x + math.cos(angle) * distance
        target_z = self.home_area.z + math.sin(angle) * distance
        
        return pygame.Vector3(target_x, 0, target_z)
    
    def render_3d(self, camera_pos, view_matrix, projection_matrix):
        """Rendert den 3D-NPC mit OpenGL"""
        if not OPENGL_AVAILABLE or self.vbo is None:
            return
        
        try:
            glPushMatrix()
            
            # Position setzen
            glTranslatef(self.position.x, self.position.y, self.position.z)
            
            # Rotation setzen
            glRotatef(self.rotation_y, 0, 1, 0)
            
            # Vertex Buffer binden
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, None)
            
            # Zeichne als Punkte oder Linien (einfaches Rendering)
            glColor3f(0.2 + (self.npc_id * 0.1) % 0.8, 
                     0.4 + (self.npc_id * 0.13) % 0.6, 
                     0.6 + (self.npc_id * 0.17) % 0.4)
            
            glDrawArrays(GL_POINTS, 0, self.vertex_count)
            
            # Cleanup
            glDisableClientState(GL_VERTEX_ARRAY)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            
            glPopMatrix()
            
        except Exception as e:
            print(f"Fehler beim 3D-Rendering: {e}")


class NPCSystem3D:
    """Verwaltet 3D-NPCs mit OpenGL-Rendering"""
    
    def __init__(self, world=None):
        self.world = world
        self.npcs = []
        self.opengl_initialized = False
        
        # Finde verfügbare 3D-Modelle
        self.model_paths = self._find_3d_models()
        print(f"Gefundene 3D-Modelle: {len(self.model_paths)}")
        for path in self.model_paths:
            print(f"  📁 {path}")
    
    def _find_3d_models(self):
        """Findet alle verfügbaren 3D-Modelle"""
        model_paths = []
        assets_dir = "assets/Player"
        
        for root, dirs, files in os.walk(assets_dir):
            for file in files:
                if file.endswith(('.glb', '.gltf')):
                    model_paths.append(os.path.join(root, file))
        
        return model_paths
    
    def initialize_opengl(self):
        """Initialisiert OpenGL für 3D-Rendering"""
        if not OPENGL_AVAILABLE:
            print("❌ OpenGL nicht verfügbar - verwende 2D-Fallback")
            return False
        
        try:
            # OpenGL Kontext ist bereits von pygame erstellt
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)
            
            # Basis-Beleuchtung
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            
            light_pos = [1.0, 1.0, 1.0, 0.0]
            glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
            
            self.opengl_initialized = True
            print("✅ OpenGL für 3D-NPCs initialisiert")
            return True
            
        except Exception as e:
            print(f"❌ OpenGL-Initialisierung fehlgeschlagen: {e}")
            return False
    
    def spawn_npc_group(self, center_pos, count=8, spread=100):
        """Spawnt eine Gruppe von 3D-NPCs"""
        model_path = self.model_paths[0] if self.model_paths else None
        
        for i in range(count):
            # Zufällige Position um den Mittelpunkt
            angle = (i / count) * 2 * math.pi + random.uniform(-0.5, 0.5)
            distance = random.uniform(20, spread)
            
            x = center_pos[0] + math.cos(angle) * distance
            y = center_pos[1] + math.sin(angle) * distance
            
            npc = NPC3D((x, y), self.world, i, model_path)
            self.npcs.append(npc)
        
        print(f"3D-NPCs spawned: {len(self.npcs)} NPCs um Position {center_pos}")
    
    def update(self, dt):
        """Update aller 3D-NPCs"""
        # Schwarm-Information weitergeben
        for npc in self.npcs:
            npc.flock_mates = self.npcs
            npc.update(dt)
    
    def render_3d(self, camera_pos=None):
        """Rendert alle 3D-NPCs mit OpenGL"""
        if not self.opengl_initialized:
            return
        
        try:
            # 3D-Projektion setzen
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(60.0, 16.0/9.0, 0.1, 1000.0)
            
            # Kamera-Position
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            
            if camera_pos:
                gluLookAt(camera_pos[0], 50, camera_pos[1] + 100,  # Kamera-Position
                         camera_pos[0], 0, camera_pos[1],           # Blick-Ziel  
                         0, 1, 0)                                   # Up-Vektor
            
            # Rendere alle NPCs
            for npc in self.npcs:
                npc.render_3d(camera_pos, None, None)
                
        except Exception as e:
            print(f"Fehler beim 3D-Rendering: {e}")
    
    def draw_2d_fallback(self, screen, camera):
        """2D-Fallback-Rendering falls OpenGL nicht funktioniert"""
        for npc in self.npcs:
            # Zeichne als einfachen farbigen Kreis
            screen_pos = camera.world_to_screen((npc.position.x, npc.position.z))
            color = (100 + (npc.npc_id * 30) % 155, 
                    150 + (npc.npc_id * 40) % 105, 
                    200 + (npc.npc_id * 50) % 55)
            pygame.draw.circle(screen, color, screen_pos, 16)
            
            # Richtungsindikator
            end_x = screen_pos[0] + math.cos(math.radians(npc.rotation_y)) * 20
            end_y = screen_pos[1] + math.sin(math.radians(npc.rotation_y)) * 20
            pygame.draw.line(screen, (255, 255, 255), screen_pos, (end_x, end_y), 2)
