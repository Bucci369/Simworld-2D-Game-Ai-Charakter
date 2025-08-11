"""
House System - Individuelle Häuser für jeden NPC mit Stadtplanung
"""

import pygame
import os
import math
import random
from typing import Dict, List, Tuple, Optional

class House:
    """Ein individuelles Haus für einen NPC"""
    
    def __init__(self, position: Tuple[float, float], owner_id: str, tribe_color: str):
        self.position = pygame.Vector2(position)
        self.owner_id = owner_id
        self.tribe_color = tribe_color
        self.built = False
        self.build_progress = 0.0  # 0.0 = Bauplatz, 1.0 = fertig
        
        # Lade Haus-Sprite
        self.house_sprite = self._load_house_sprite()
        
        # Größe und Hitbox ZUERST definieren
        if self.house_sprite:
            self.size = self.house_sprite.get_size()
        else:
            self.size = (64, 48)  # Fallback-Größe
            
        # DANN Foundation erstellen (braucht self.size)
        self.foundation_sprite = self._create_foundation()
            
        self.rect = pygame.Rect(position[0], position[1], self.size[0], self.size[1])
        
        # Bau-Anforderungen
        self.wood_needed = 15
        self.stone_needed = 8
        self.wood_used = 0
        self.stone_used = 0
        
    def _load_house_sprite(self) -> Optional[pygame.Surface]:
        """Lade haus.png Sprite"""
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            house_path = os.path.join(base_dir, 'assets', 'Buildings', 'haus.png')
            
            if os.path.exists(house_path):
                sprite = pygame.image.load(house_path).convert_alpha()
                # Skaliere Haus auf angemessene Größe
                original_size = sprite.get_size()
                scale_factor = 1.2  # 20% größer
                new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                sprite = pygame.transform.scale(sprite, new_size)
                print(f"🏠 Haus-Sprite geladen: {original_size} → {new_size}")
                return sprite
        except Exception as e:
            print(f"⚠️ Konnte haus.png nicht laden: {e}")
        
        # Fallback: Erstelle einfaches Haus
        return self._create_simple_house()
    
    def _create_simple_house(self) -> pygame.Surface:
        """Erstelle einfaches Haus-Sprite als Fallback"""
        house = pygame.Surface((64, 48), pygame.SRCALPHA)
        
        # Hauswände (braun)
        pygame.draw.rect(house, (139, 69, 19), (8, 16, 48, 32))
        
        # Dach (dunkelrot)
        roof_points = [(4, 16), (32, 4), (60, 16)]
        pygame.draw.polygon(house, (120, 42, 42), roof_points)
        
        # Tür (dunkelbraun)
        pygame.draw.rect(house, (101, 67, 33), (26, 32, 12, 16))
        
        # Fenster (hellblau)
        pygame.draw.rect(house, (173, 216, 230), (16, 24, 8, 8))
        pygame.draw.rect(house, (173, 216, 230), (40, 24, 8, 8))
        
        # Volk-Farbe Markierung
        color_map = {
            'red': (255, 100, 100),
            'blue': (100, 100, 255),
            'green': (100, 255, 100)
        }
        
        tribe_color_rgb = color_map.get(self.tribe_color, (255, 255, 255))
        pygame.draw.rect(house, tribe_color_rgb, (28, 20, 8, 4))
        
        return house
    
    def _create_foundation(self) -> pygame.Surface:
        """Erstelle Fundament/Bauplatz-Sprite"""
        foundation = pygame.Surface(self.size, pygame.SRCALPHA)
        
        # Bauplatz-Umriss
        pygame.draw.rect(foundation, (139, 69, 19), foundation.get_rect(), 3)
        
        # Fundament-Steine
        for x in range(0, self.size[0], 16):
            for y in range(0, self.size[1], 12):
                pygame.draw.rect(foundation, (128, 128, 128), (x+2, y+2, 12, 8))
        
        return foundation
    
    def add_resources(self, wood: int = 0, stone: int = 0) -> bool:
        """Füge Bau-Ressourcen hinzu"""
        added_wood = min(wood, self.wood_needed - self.wood_used)
        added_stone = min(stone, self.stone_needed - self.stone_used)
        
        self.wood_used += added_wood
        self.stone_used += added_stone
        
        # Berechne Baufortschritt
        wood_progress = self.wood_used / self.wood_needed
        stone_progress = self.stone_used / self.stone_needed
        self.build_progress = min(wood_progress, stone_progress)
        
        # Haus fertig?
        if self.wood_used >= self.wood_needed and self.stone_used >= self.stone_needed:
            self.built = True
            print(f"🏠 Haus für {self.owner_id} ({self.tribe_color}) fertiggestellt!")
        
        return added_wood > 0 or added_stone > 0
    
    def get_build_requirements(self) -> Dict[str, int]:
        """Hole noch benötigte Ressourcen"""
        return {
            'wood': max(0, self.wood_needed - self.wood_used),
            'stone': max(0, self.stone_needed - self.stone_used)
        }
    
    def draw(self, screen: pygame.Surface, camera_rect: pygame.Rect):
        """Zeichne das Haus"""
        screen_x = self.position.x - camera_rect.left
        screen_y = self.position.y - camera_rect.top
        
        if self.built:
            # Fertiges Haus
            screen.blit(self.house_sprite, (screen_x, screen_y))
        else:
            # Bauplatz/Baustelle
            screen.blit(self.foundation_sprite, (screen_x, screen_y))
            
            # Baufortschritt anzeigen
            if self.build_progress > 0:
                self._draw_construction_progress(screen, screen_x, screen_y)
    
    def _draw_construction_progress(self, screen: pygame.Surface, screen_x: float, screen_y: float):
        """Zeige Baufortschritt"""
        try:
            # Fortschrittsbalken
            bar_width = self.size[0]
            bar_height = 6
            bar_x = screen_x
            bar_y = screen_y - 15
            
            # Hintergrund
            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
            
            # Fortschritt
            progress_width = int(bar_width * self.build_progress)
            pygame.draw.rect(screen, (100, 200, 100), (bar_x, bar_y, progress_width, bar_height))
            
            # Rahmen
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)
            
            # Prozent-Text
            font = pygame.font.Font(None, 16)
            percent_text = f"{int(self.build_progress * 100)}%"
            text_surface = font.render(percent_text, True, (255, 255, 255))
            text_x = bar_x + bar_width + 5
            screen.blit(text_surface, (text_x, bar_y - 2))
        except:
            pass


class CityPlanner:
    """Stadtplanung - Platziert Häuser intelligent ohne Überlappung"""
    
    def __init__(self, center: Tuple[float, float], radius: float = 200):
        self.center = pygame.Vector2(center)
        self.radius = radius
        self.house_positions = []  # Bereits belegte Positionen
        self.min_house_distance = 80  # Mindestabstand zwischen Häusern
        
    def find_house_position(self, tribe_color: str) -> Tuple[float, float]:
        """Finde optimale Position für neues Haus"""
        attempts = 0
        max_attempts = 50
        
        while attempts < max_attempts:
            # Spiralförmige Platzierung vom Zentrum nach außen
            angle = (len(self.house_positions) * 2.4) % (2 * math.pi)  # Golden angle
            distance = 60 + (len(self.house_positions) * 15)  # Spirale nach außen
            
            x = self.center.x + math.cos(angle) * distance
            y = self.center.y + math.sin(angle) * distance
            
            position = (x, y)
            
            # Prüfe Überlappung mit anderen Häusern
            if self._is_position_valid(position):
                self.house_positions.append(position)
                print(f"🏠 Hausposition gefunden: {position} für {tribe_color}")
                return position
            
            attempts += 1
        
        # Fallback: Position am Rand
        fallback_x = self.center.x + len(self.house_positions) * 70
        fallback_y = self.center.y
        fallback_position = (fallback_x, fallback_y)
        self.house_positions.append(fallback_position)
        print(f"🏠 Fallback-Position: {fallback_position} für {tribe_color}")
        return fallback_position
    
    def _is_position_valid(self, position: Tuple[float, float]) -> bool:
        """Prüfe ob Position für Haus geeignet ist"""
        for existing_pos in self.house_positions:
            distance = math.sqrt((position[0] - existing_pos[0])**2 + 
                               (position[1] - existing_pos[1])**2)
            if distance < self.min_house_distance:
                return False
        return True


class HouseSystem:
    """Verwaltet alle Häuser und Stadtplanung"""
    
    def __init__(self):
        self.houses = {}  # {owner_id: House}
        self.city_planners = {}  # {tribe_color: CityPlanner}
        # 🏗️ NEUES FEATURE: Baustellen-Tracking
        self.construction_stats = {
            'red': {'active': 0, 'completed': 0, 'total_planned': 0},
            'blue': {'active': 0, 'completed': 0, 'total_planned': 0},
            'green': {'active': 0, 'completed': 0, 'total_planned': 0}
        }
        # Maximale parallele Baustellen pro Volk (schrittweiser Aufbau)
        if not hasattr(self, 'max_active_sites_per_tribe'):
            self.max_active_sites_per_tribe = 2
        
    def get_construction_stats(self, tribe_color: str) -> Dict[str, int]:
        """Hole Baustatistiken für ein Volk"""
        return self.construction_stats.get(tribe_color, {'active': 0, 'completed': 0, 'total_planned': 0})
    
    def update_construction_stats(self):
        """Aktualisiere Baustatistiken"""
        # Reset stats
        for tribe in self.construction_stats:
            self.construction_stats[tribe] = {'active': 0, 'completed': 0, 'total_planned': 0}
        
        # Zähle alle Häuser
        for house in self.houses.values():
            tribe = house.tribe_color
            if tribe in self.construction_stats:
                self.construction_stats[tribe]['total_planned'] += 1
                # Als "active" zählen jetzt ALLE unfertigen Häuser (auch Fortschritt 0.0)
                if house.built:
                    self.construction_stats[tribe]['completed'] += 1
                else:
                    self.construction_stats[tribe]['active'] += 1
        
    def create_city_planner(self, tribe_color: str, center: Tuple[float, float]):
        """Erstelle Stadtplaner für ein Volk"""
        planner = CityPlanner(center)
        self.city_planners[tribe_color] = planner
        print(f"🏗️ Stadtplaner für {tribe_color} erstellt bei {center}")
        
    def build_house_for_npc(self, owner_id: str, tribe_color: str) -> House:
        """Baue Haus für NPC - 🏗️ GESTAFFELTES SYSTEM"""
        if owner_id in self.houses:
            return self.houses[owner_id]  # Haus bereits vorhanden
        
        # 🏗️ NEUES FEATURE: Prüfe Baustellen-Limit (konfigurierbar pro Volk)
        self.update_construction_stats()
        stats = self.get_construction_stats(tribe_color)
        active_limit = self.max_active_sites_per_tribe
        if stats['active'] >= active_limit:
            if random.random() < 0.1:
                print(f"🏗️ {tribe_color.upper()}: Baustellen-Limit erreicht ({stats['active']}/{active_limit})")
            return None
        
        # Finde Position mit Stadtplaner
        planner = self.city_planners.get(tribe_color)
        if not planner:
            print(f"⚠️ Kein Stadtplaner für {tribe_color}!")
            return None
            
        position = planner.find_house_position(tribe_color)
        house = House(position, owner_id, tribe_color)
        self.houses[owner_id] = house
        
        print(f"🏗️ Bauplatz für {owner_id} ({tribe_color}) erstellt")
        return house
    
    def get_house(self, owner_id: str) -> Optional[House]:
        """Hole Haus eines NPCs"""
        return self.houses.get(owner_id)
    
    def get_tribe_houses(self, tribe_color: str) -> List[House]:
        """Hole alle Häuser eines Volkes"""
        return [house for house in self.houses.values() if house.tribe_color == tribe_color]
    
    def count_built_houses(self, tribe_color: str) -> int:
        """Zähle fertige Häuser eines Volkes"""
        tribe_houses = self.get_tribe_houses(tribe_color)
        return sum(1 for house in tribe_houses if house.built)
    
    def count_total_houses(self, tribe_color: str) -> int:
        """Zähle alle Häuser (auch Baustellen) eines Volkes"""
        return len(self.get_tribe_houses(tribe_color))
    
    def update(self, dt: float):
        """Update alle Häuser und Statistiken"""
        # Aktualisiere Baustatistiken regelmäßig
        self.update_construction_stats()
    
    def draw(self, screen: pygame.Surface, camera_rect: pygame.Rect):
        """Zeichne alle Häuser"""
        # Sortiere nach Y-Position für korrektes Layering
        sorted_houses = sorted(self.houses.values(), key=lambda h: h.position.y + h.size[1])
        
        for house in sorted_houses:
            house.draw(screen, camera_rect)
    
    def handle_click(self, world_pos: Tuple[float, float], player_pos: Tuple[float, float]):
        """Handle Klicks auf Häuser"""
        for owner_id, house in self.houses.items():
            if house.rect.collidepoint(world_pos):
                if house.built:
                    print(f"🏠 {owner_id}s Haus ({house.tribe_color})")
                else:
                    requirements = house.get_build_requirements()
                    print(f"🏗️ Baustelle von {owner_id}:")
                    print(f"  Braucht noch: {requirements['wood']} Holz, {requirements['stone']} Stein")
                    print(f"  Fortschritt: {int(house.build_progress * 100)}%")
                return True
        return False