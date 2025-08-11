"""
3D NPC System - Neue Version mit modernem 3D Renderer
Ersetzt das alte 2D NPC System mit echten 3D Modellen ohne OpenGL
"""

import pygame
import math
import random
from typing import List, Tuple
from renderer_3d import Mesh3D, Vec3


class NPC3D_Modern:
    """3D NPC mit Verhalten und 3D Modell (ohne OpenGL)"""
    def __init__(self, x: float, y: float, z: float = 0, mesh_file: str = None):
        # Position und Bewegung
        self.position = Vec3(x, y, z)
        self.velocity = Vec3(0, 0, 0)
        self.target_position = Vec3(x, y, z)
        
        # NPC Eigenschaften
        self.speed = 0.5 + random.random() * 0.5  # Zufällige Geschwindigkeit
        self.max_speed = 1.0
        self.size = 0.8 + random.random() * 0.4  # Zufällige Größe
        
        # Schwarm-Verhalten
        self.separation_radius = 2.0
        self.alignment_radius = 3.0
        self.cohesion_radius = 4.0
        self.wander_strength = 0.3
        
        # Wander behavior
        self.wander_angle = random.random() * 2 * math.pi
        self.wander_distance = 2.0
        self.wander_radius = 1.0
        self.wander_change = 0.1
        
        # Animation
        self.rotation_speed = 0.02
        self.bob_speed = 0.05
        self.bob_offset = random.random() * 2 * math.pi
        self.time = 0
        
        # 3D Mesh laden
        self.mesh = self._load_mesh(mesh_file)
        if self.mesh:
            self.mesh.scale = self.size
            self.mesh.position = self.position
    
    def _load_mesh(self, mesh_file: str) -> Mesh3D:
        """Lade 3D Mesh für diesen NPC"""
        if mesh_file and mesh_file.endswith(('.glb', '.gltf')):
            try:
                mesh = Mesh3D.from_gltf(mesh_file)
                print(f"Successfully loaded 3D mesh: {mesh_file}")
                return mesh
            except Exception as e:
                print(f"Failed to load mesh {mesh_file}: {e}")
        
        # Fallback: Erstelle einen kleinen farbigen Würfel
        mesh = Mesh3D.create_cube(1.0)
        # Zufällige Farbe für jeden NPC
        random_color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        for face in mesh.faces:
            face.color = random_color
        
        return mesh
    
    def update(self, npc_list: List['NPC3D_Modern'], dt: float):
        """Update NPC behavior and position"""
        self.time += dt
        
        # Schwarm-Verhalten berechnen
        separation = self._calculate_separation(npc_list)
        alignment = self._calculate_alignment(npc_list)
        cohesion = self._calculate_cohesion(npc_list)
        wander = self._calculate_wander()
        
        # Kräfte kombinieren
        total_force = Vec3(0, 0, 0)
        total_force = total_force + separation * 1.5  # Separation wichtiger
        total_force = total_force + alignment * 1.0
        total_force = total_force + cohesion * 1.0
        total_force = total_force + wander * self.wander_strength
        
        # Velocity aktualisieren
        self.velocity = self.velocity + total_force * dt
        
        # Speed limitieren
        speed = math.sqrt(self.velocity.x**2 + self.velocity.y**2 + self.velocity.z**2)
        if speed > self.max_speed:
            self.velocity = self.velocity * (self.max_speed / speed)
        
        # Position aktualisieren
        self.position = self.position + self.velocity * dt
        
        # Animation: Sanftes Auf und Ab
        bob_height = math.sin(self.time * self.bob_speed + self.bob_offset) * 0.1
        
        # Mesh Position und Rotation aktualisieren
        if self.mesh:
            self.mesh.position = Vec3(self.position.x, self.position.y, self.position.z + bob_height)
            
            # Rotation basierend auf Bewegungsrichtung
            if speed > 0.1:
                # Face movement direction
                angle_y = math.atan2(self.velocity.x, self.velocity.z)
                self.mesh.rotation.y = angle_y
            
            # Sanfte Y-Rotation für Leben
            self.mesh.rotation.y += self.rotation_speed * dt
    
    def _calculate_separation(self, npc_list: List['NPC3D_Modern']) -> Vec3:
        """Trennung von anderen NPCs"""
        force = Vec3(0, 0, 0)
        count = 0
        
        for other in npc_list:
            if other != self:
                distance = math.sqrt(
                    (self.position.x - other.position.x)**2 + 
                    (self.position.y - other.position.y)**2 + 
                    (self.position.z - other.position.z)**2
                )
                
                if distance < self.separation_radius and distance > 0:
                    diff = self.position - other.position
                    diff = diff * (1.0 / distance)  # Normalize
                    diff = diff * (1.0 / distance)  # Weight by distance
                    force = force + diff
                    count += 1
        
        if count > 0:
            force = force * (1.0 / count)
        
        return force
    
    def _calculate_alignment(self, npc_list: List['NPC3D_Modern']) -> Vec3:
        """Ausrichtung mit anderen NPCs"""
        avg_velocity = Vec3(0, 0, 0)
        count = 0
        
        for other in npc_list:
            if other != self:
                distance = math.sqrt(
                    (self.position.x - other.position.x)**2 + 
                    (self.position.y - other.position.y)**2 + 
                    (self.position.z - other.position.z)**2
                )
                
                if distance < self.alignment_radius:
                    avg_velocity = avg_velocity + other.velocity
                    count += 1
        
        if count > 0:
            avg_velocity = avg_velocity * (1.0 / count)
            # Normalize to max speed
            speed = math.sqrt(avg_velocity.x**2 + avg_velocity.y**2 + avg_velocity.z**2)
            if speed > 0:
                avg_velocity = avg_velocity * (self.max_speed / speed)
            
            force = avg_velocity - self.velocity
            return force
        
        return Vec3(0, 0, 0)
    
    def _calculate_cohesion(self, npc_list: List['NPC3D_Modern']) -> Vec3:
        """Zusammenhalt mit anderen NPCs"""
        center = Vec3(0, 0, 0)
        count = 0
        
        for other in npc_list:
            if other != self:
                distance = math.sqrt(
                    (self.position.x - other.position.x)**2 + 
                    (self.position.y - other.position.y)**2 + 
                    (self.position.z - other.position.z)**2
                )
                
                if distance < self.cohesion_radius:
                    center = center + other.position
                    count += 1
        
        if count > 0:
            center = center * (1.0 / count)
            desired = center - self.position
            
            # Normalize to max speed
            distance = math.sqrt(desired.x**2 + desired.y**2 + desired.z**2)
            if distance > 0:
                desired = desired * (self.max_speed / distance)
            
            force = desired - self.velocity
            return force
        
        return Vec3(0, 0, 0)
    
    def _calculate_wander(self) -> Vec3:
        """Zufällige Wanderbewegung"""
        # Update wander angle
        self.wander_angle += random.uniform(-self.wander_change, self.wander_change)
        
        # Calculate wander target
        circle_center = Vec3(
            self.position.x + self.velocity.x * self.wander_distance,
            self.position.y + self.velocity.y * self.wander_distance,
            self.position.z
        )
        
        displacement = Vec3(
            math.cos(self.wander_angle) * self.wander_radius,
            math.sin(self.wander_angle) * self.wander_radius,
            0
        )
        
        wander_target = circle_center + displacement
        desired = wander_target - self.position
        
        # Normalize
        distance = math.sqrt(desired.x**2 + desired.y**2 + desired.z**2)
        if distance > 0:
            desired = desired * (self.max_speed / distance)
        
        return desired - self.velocity


class NPCSystemModern:
    """Manager für alle modernen 3D NPCs"""
    def __init__(self, renderer_3d):
        self.npcs: List[NPC3D_Modern] = []
        self.renderer_3d = renderer_3d
        
    def spawn_npc_group(self, center_x: float, center_y: float, count: int = 8, mesh_file: str = None):
        """Spawne eine Gruppe von NPCs um einen Mittelpunkt"""
        for i in range(count):
            # Zufällige Position um den Mittelpunkt
            angle = (i / count) * 2 * math.pi + random.uniform(-0.5, 0.5)
            radius = 2 + random.uniform(0, 3)
            
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius
            z = random.uniform(0, 0.5)  # Leicht unterschiedliche Höhen
            
            npc = NPC3D_Modern(x, y, z, mesh_file)
            self.npcs.append(npc)
            
            # Mesh zum Renderer hinzufügen
            if npc.mesh:
                self.renderer_3d.add_mesh(npc.mesh)
        
        print(f"Spawned {count} moderne 3D NPCs at ({center_x}, {center_y})")
    
    def update(self, dt: float):
        """Update alle NPCs"""
        for npc in self.npcs:
            npc.update(self.npcs, dt)
    
    def get_npc_positions(self) -> List[Tuple[float, float]]:
        """Gib alle NPC Positionen zurück (für Kompatibilität)"""
        return [(npc.position.x, npc.position.y) for npc in self.npcs]
    
    def clear_npcs(self):
        """Entferne alle NPCs"""
        # Remove meshes from renderer
        for npc in self.npcs:
            if npc.mesh and npc.mesh in self.renderer_3d.meshes:
                self.renderer_3d.meshes.remove(npc.mesh)
        
        self.npcs.clear()
        print("Cleared all moderne 3D NPCs")
