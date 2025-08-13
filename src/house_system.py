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
        
        # 🏗️ NEUE FEATURE: Bauplatz-Zonen für realistischen Hausbau
        self.build_zone_radius = 25  # NPCs müssen innerhalb 25 Pixel zum Bauplatz
        self.build_zone_rect = pygame.Rect(
            position[0] - self.build_zone_radius, 
            position[1] - self.build_zone_radius,
            self.size[0] + 2 * self.build_zone_radius,
            self.size[1] + 2 * self.build_zone_radius
        )
        
        # 🏠 NEUE BALANCE: Haus kostet 25 Holz (5 Bäume = 5 Trips á 5 Holz)
        self.wood_needed = 25  # 25 Holz benötigt (war 5)
        self.stone_needed = 0  # Kein Stein benötigt - nur Holz für schnellen Hausbau
        self.wood_used = 0
        self.stone_used = 0
        
        # 🔨 HAUSBAU-MECHANIK: Holz sammeln bis 25, dann bauen
        self.wood_deposited = 0  # Holz das am Bauplatz liegt
        self.construction_hits = 0  # Anzahl Bau-Schläge (10 needed)
        self.max_construction_hits = 10  # 10 Schläge für Hausbau
        
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
        """Füge Bau-Ressourcen hinzu - 🏠 NEUE BALANCE"""
        added_wood = min(wood, self.wood_needed - self.wood_used)
        added_stone = min(stone, self.stone_needed - self.stone_used)
        
        self.wood_used += added_wood
        self.stone_used += added_stone
        
        # Berechne Baufortschritt (sichere Division)
        wood_progress = self.wood_used / self.wood_needed if self.wood_needed > 0 else 1.0
        stone_progress = self.stone_used / self.stone_needed if self.stone_needed > 0 else 1.0
        self.build_progress = min(wood_progress, stone_progress)
        
        # Haus fertig?
        if self.wood_used >= self.wood_needed and self.stone_used >= self.stone_needed:
            self.built = True
            print(f"🏠 Haus für {self.owner_id} ({self.tribe_color}) fertiggestellt!")
        
        return added_wood > 0 or added_stone > 0
    
    def deposit_wood(self, wood_amount: int) -> int:
        """Lagere Holz am Bauplatz ab - 🏠 NEUE MECHANIK"""
        space_available = self.wood_needed - self.wood_deposited
        wood_to_deposit = min(wood_amount, space_available)
        self.wood_deposited += wood_to_deposit
        
        print(f"🪵 {wood_to_deposit} Holz am Bauplatz abgelegt ({self.wood_deposited}/{self.wood_needed})")
        return wood_to_deposit  # Wie viel tatsächlich abgelegt wurde
    
    def can_start_construction(self) -> bool:
        """Prüfe ob Bau beginnen kann (25 Holz vorhanden)"""
        return self.wood_deposited >= self.wood_needed
    
    def perform_construction_hit(self) -> bool:
        """Führe einen Bau-Schlag aus - 🔨 NEUE MECHANIK"""
        if not self.can_start_construction():
            return False
        
        self.construction_hits += 1
        progress_percent = (self.construction_hits / self.max_construction_hits) * 100
        
        print(f"🔨 Bau-Schlag {self.construction_hits}/{self.max_construction_hits} ({progress_percent:.0f}%)")
        
        # Haus fertig nach 10 Schlägen
        if self.construction_hits >= self.max_construction_hits:
            self.built = True
            self.build_progress = 1.0
            print(f"🏠 Haus für {self.owner_id} ({self.tribe_color}) fertiggestellt!")
            return True
        
        # Update Baufortschritt
        self.build_progress = self.construction_hits / self.max_construction_hits
        return False
    
    def is_in_build_zone(self, npc_position: Tuple[float, float]) -> bool:
        """Prüft ob NPC in der Bauzone steht (nah genug zum Bauen)"""
        npc_pos = pygame.Vector2(npc_position)
        house_center = pygame.Vector2(self.position.x + self.size[0]/2, self.position.y + self.size[1]/2)
        distance = npc_pos.distance_to(house_center)
        return distance <= self.build_zone_radius
    
    def get_build_position(self) -> Tuple[float, float]:
        """Gibt optimale Position zum Bauen zurück (vor dem Haus)"""
        # Position direkt vor dem Haus (unten)
        build_x = self.position.x + self.size[0] / 2
        build_y = self.position.y + self.size[1] + 10  # 10 Pixel vor dem Haus
        return (build_x, build_y)
    
    def get_build_requirements(self) -> Dict[str, int]:
        """Hole noch benötigte Ressourcen"""
        return {
            'wood': max(0, self.wood_needed - self.wood_deposited),  # Verwende wood_deposited statt wood_used
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
            
            # 🏗️ NEUE FEATURE: Visualisiere Bauzone
            self._draw_build_zone(screen, camera_rect)
            
            # Baufortschritt anzeigen
            if self.build_progress > 0:
                self._draw_construction_progress(screen, screen_x, screen_y)
    
    def _draw_build_zone(self, screen: pygame.Surface, camera_rect: pygame.Rect):
        """Zeichne die Bauzone als gestrichelten Kreis"""
        try:
            # Berechne Bauzone-Center in Bildschirmkoordinaten
            zone_center_x = self.position.x + self.size[0]/2 - camera_rect.left
            zone_center_y = self.position.y + self.size[1]/2 - camera_rect.top
            
            # Zeichne gestrichelten Kreis um die Bauzone
            import math
            for angle in range(0, 360, 15):  # Alle 15 Grad einen Punkt
                rad = math.radians(angle)
                x = zone_center_x + self.build_zone_radius * math.cos(rad)
                y = zone_center_y + self.build_zone_radius * math.sin(rad)
                pygame.draw.circle(screen, (200, 200, 100), (int(x), int(y)), 2)
        except:
            pass
    
    def _draw_construction_progress(self, screen: pygame.Surface, screen_x: float, screen_y: float):
        """Zeige Baufortschritt und Holz-Stapel"""
        try:
            # 🪵 NEUE FEATURE: Zeige Holz-Stapel am Bauplatz
            if self.wood_deposited > 0:
                self._draw_wood_pile(screen, screen_x, screen_y)
            
            # Fortschrittsbalken (nur wenn Bau begonnen)
            if self.construction_hits > 0:
                bar_width = self.size[0]
                bar_height = 6
                bar_x = screen_x
                bar_y = screen_y - 15
                
                # Hintergrund
                pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
                
                # Baufortschritt (basierend auf construction_hits)
                progress_width = int(bar_width * (self.construction_hits / self.max_construction_hits))
                pygame.draw.rect(screen, (100, 200, 100), (bar_x, bar_y, progress_width, bar_height))
                
                # Rahmen
                pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)
                
                # Bau-Prozent-Text
                font = pygame.font.Font(None, 16)
                percent_text = f"Bau: {self.construction_hits}/{self.max_construction_hits}"
                text_surface = font.render(percent_text, True, (255, 255, 255))
                text_x = bar_x + bar_width + 5
                screen.blit(text_surface, (text_x, bar_y - 2))
            
            # Holz-Status Text
            if not self.built:
                font = pygame.font.Font(None, 14)
                wood_text = f"Holz: {self.wood_deposited}/{self.wood_needed}"
                text_color = (100, 255, 100) if self.can_start_construction() else (255, 255, 100)
                wood_surface = font.render(wood_text, True, text_color)
                
                text_x = screen_x
                text_y = screen_y - 30
                screen.blit(wood_surface, (text_x, text_y))
        except:
            pass
    
    def _draw_wood_pile(self, screen: pygame.Surface, screen_x: float, screen_y: float):
        """Zeichne Holz-Stapel am Bauplatz"""
        try:
            # Zeichne Holz-Stapel basierend auf wood_deposited
            wood_piles = min(self.wood_deposited // 5, 5)  # Max 5 Stapel
            pile_size = 8
            
            for i in range(wood_piles):
                pile_x = screen_x + 10 + (i * 12)
                pile_y = screen_y + self.size[1] - 15
                
                # Braune Holz-Rechtecke
                pygame.draw.rect(screen, (139, 69, 19), (pile_x, pile_y, pile_size, pile_size))
                pygame.draw.rect(screen, (101, 67, 33), (pile_x, pile_y, pile_size, pile_size), 1)
            
            # Zeige einzelnes Holz für Reste
            remainder = self.wood_deposited % 5
            if remainder > 0 and wood_piles < 5:
                for j in range(remainder):
                    single_x = screen_x + 10 + (wood_piles * 12) + (j * 3)
                    single_y = screen_y + self.size[1] - 10
                    pygame.draw.rect(screen, (160, 82, 45), (single_x, single_y, 4, 8))
        except:
            pass


class CityPlanner:
    """Stadtplanung - 🏘️ NEUE FEATURE: Schönes Stadtraster mit Lager und Marktplatz"""
    
    def __init__(self, center: Tuple[float, float], radius: float = 300):
        self.center = pygame.Vector2(center)
        self.radius = radius
        self.house_positions = []  # Bereits belegte Positionen
        self.min_house_distance = 100  # Mehr Abstand zwischen Häusern für schönes Raster
        self.world = None  # Referenz zur Welt für Kollisionserkennung
        
        # 🏘️ STADTPLANUNG: Definiere spezielle Gebäude-Bereiche
        self.storage_position = None  # Lager in der Mitte
        self.marketplace_position = None  # Marktplatz
        self.has_storage = False
        self.has_marketplace = False
        
        # Raster-Parameter
        self.grid_size = 120  # Abstand zwischen Häusern im Raster
        self.rows = 3  # 3 Reihen von Häusern
        self.houses_per_row = 4  # 4 Häuser pro Reihe
        
    def set_world(self, world):
        """Setze World-Referenz für Kollisionserkennung"""
        self.world = world
        
    def setup_city_center(self):
        """Erstelle Lager und Marktplatz in der Stadtmitte mit Kollisionserkennung"""
        if not self.has_storage:
            # Suche sichere Position für das Lager
            storage_pos = self._find_safe_building_position(self.center.x, self.center.y, max_attempts=20)
            self.storage_position = storage_pos
            self.has_storage = True
            print(f"🏬 Lager geplant bei {self.storage_position}")
        
        if not self.has_marketplace:
            # Suche sichere Position für den Marktplatz neben dem Lager
            market_x = self.storage_position[0] + 80
            market_y = self.storage_position[1]
            market_pos = self._find_safe_building_position(market_x, market_y, max_attempts=20)
            self.marketplace_position = market_pos
            self.has_marketplace = True
            print(f"🏪 Marktplatz geplant bei {self.marketplace_position}")
            
    def _find_safe_building_position(self, x: float, y: float, max_attempts: int = 10) -> Tuple[float, float]:
        """Finde sichere Position für Gebäude, die nicht auf Wasser liegt"""
        # Teste zuerst die ursprüngliche Position
        if self._is_building_position_safe(x, y):
            return (x, y)
        
        # Suche in Spirale um die ursprüngliche Position
        for attempt in range(max_attempts):
            radius = (attempt + 1) * 30
            for angle in range(0, 360, 45):  # 8 Richtungen
                test_x = x + math.cos(math.radians(angle)) * radius
                test_y = y + math.sin(math.radians(angle)) * radius
                
                if self._is_building_position_safe(test_x, test_y):
                    return (test_x, test_y)
        
        # Fallback: Gib ursprüngliche Position zurück
        print(f"⚠️ Keine sichere Position gefunden, verwende Fallback bei ({x}, {y})")
        return (x, y)
    
    def _is_building_position_safe(self, x: float, y: float) -> bool:
        """Prüfe ob eine Gebäude-Position sicher ist (nicht auf Wasser)"""
        if not self.world or not hasattr(self.world, 'is_walkable'):
            return True  # Ohne World-Referenz können wir nicht prüfen
        
        building_size = (64, 64)  # Standard-Gebäudegröße
        
        # Prüfe mehrere Punkte des Gebäudes
        test_points = [
            (x, y),  # Ecke links oben
            (x + building_size[0], y),  # Ecke rechts oben
            (x, y + building_size[1]),  # Ecke links unten
            (x + building_size[0], y + building_size[1]),  # Ecke rechts unten
            (x + building_size[0]/2, y + building_size[1]/2)  # Mitte
        ]
        
        for test_point in test_points:
            if not self.world.is_walkable(test_point[0], test_point[1]):
                return False
        
        return True
        
    def find_house_position(self, tribe_color: str) -> Tuple[float, float]:
        """Finde Position im schönen Stadtraster - 🏘️ NEUE SYSTEMATIK"""
        house_index = len(self.house_positions)
        
        # Setup city center falls noch nicht geschehen
        if not self.has_storage:
            self.setup_city_center()
        
        # Bestimme Reihe und Position in der Reihe
        row = house_index // self.houses_per_row
        col = house_index % self.houses_per_row
        
        # Berechne Raster-Position um das Zentrum herum
        if row < self.rows:
            # Normalraster: Häuser um Lager/Marktplatz anordnen
            start_x = self.center.x - (self.houses_per_row * self.grid_size) // 2
            start_y = self.center.y - 150  # Häuser oberhalb des Zentrums
            
            x = start_x + (col * self.grid_size)
            y = start_y + (row * 80)  # Geringerer Zeilenabstand
        else:
            # Zusätzliche Häuser: Spiralförmig um die Stadt
            angle = (house_index - (self.rows * self.houses_per_row)) * 0.8
            distance = 200 + ((house_index - (self.rows * self.houses_per_row)) * 30)
            
            x = self.center.x + math.cos(angle) * distance
            y = self.center.y + math.sin(angle) * distance
        
        position = (x, y)
        
        # Prüfe Überlappung und justiere falls nötig
        if self._is_position_valid(position):
            self.house_positions.append(position)
            print(f"🏠 Hausposition im Raster: Reihe {row+1}, Haus {col+1} bei {position}")
            return position
        else:
            # Fallback: Suche freie Position in der Nähe
            for offset_x in range(-50, 51, 25):
                for offset_y in range(-50, 51, 25):
                    test_pos = (x + offset_x, y + offset_y)
                    if self._is_position_valid(test_pos):
                        self.house_positions.append(test_pos)
                        print(f"🏠 Hausposition (justiert): {test_pos}")
                        return test_pos
        
        # Final fallback
        fallback_position = (self.center.x + len(self.house_positions) * 70, self.center.y + 100)
        self.house_positions.append(fallback_position)
        print(f"🏠 Fallback-Position: {fallback_position}")
        return fallback_position
        
    def _is_position_valid(self, position: Tuple[float, float]) -> bool:
        """Prüfe ob Position für Haus geeignet ist (erweiterte Prüfung mit Kollisionserkennung)"""
        # 🚫 KOLLISIONSERKENNUNG: Prüfe ob Position begehbar ist
        if self.world and hasattr(self.world, 'is_walkable'):
            house_size = (64, 64)  # Standard-Hausgröße
            
            # Prüfe mehrere Punkte des Hauses
            test_points = [
                position,  # Ecke links oben
                (position[0] + house_size[0], position[1]),  # Ecke rechts oben
                (position[0], position[1] + house_size[1]),  # Ecke links unten
                (position[0] + house_size[0], position[1] + house_size[1]),  # Ecke rechts unten
                (position[0] + house_size[0]/2, position[1] + house_size[1]/2)  # Mitte
            ]
            
            for test_point in test_points:
                if not self.world.is_walkable(test_point[0], test_point[1]):
                    return False
        
        # Prüfe Abstand zu anderen Häusern
        for existing_pos in self.house_positions:
            distance = math.sqrt((position[0] - existing_pos[0])**2 + 
                               (position[1] - existing_pos[1])**2)
            if distance < self.min_house_distance:
                return False
        
        # Prüfe Abstand zu Lager und Marktplatz
        if self.storage_position:
            storage_distance = math.sqrt((position[0] - self.storage_position[0])**2 + 
                                       (position[1] - self.storage_position[1])**2)
            if storage_distance < 60:  # Mindestens 60 Pixel Abstand zum Lager
                return False
                
        if self.marketplace_position:
            market_distance = math.sqrt((position[0] - self.marketplace_position[0])**2 + 
                                      (position[1] - self.marketplace_position[1])**2)
            if market_distance < 60:  # Mindestens 60 Pixel Abstand zum Marktplatz
                return False
        
        return True


class HouseSystem:
    """Verwaltet alle Häuser und Stadtplanung"""
    
    def __init__(self):
        self.houses = {}  # {owner_id: House}
        self.city_planners = {}  # {tribe_color: CityPlanner}
        self.world = None  # � Welt-Referenz für sichere Platzierung
        # �🏗️ NEUES FEATURE: Baustellen-Tracking
        self.construction_stats = {
            'red': {'active': 0, 'completed': 0, 'total_planned': 0},
            'blue': {'active': 0, 'completed': 0, 'total_planned': 0},
            'green': {'active': 0, 'completed': 0, 'total_planned': 0}
        }
        # Maximale parallele Baustellen pro Volk (skaliert für bis zu 11 NPCs)
        if not hasattr(self, 'max_active_sites_per_tribe'):
            self.max_active_sites_per_tribe = 11  # Ein Haus pro NPC
            
    def set_world(self, world):
        """Setze Welt-Referenz für sichere Haus-Platzierung"""
        self.world = world
        print("🏠 Welt-Referenz für House-System gesetzt!")
        # Gebe Welt auch an alle City Planner weiter
        for city_planner in self.city_planners.values():
            if hasattr(city_planner, 'set_world'):
                city_planner.set_world(world)
            else:
                city_planner.world = world
        
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
        # Setze World-Referenz für Kollisionserkennung
        if hasattr(self, 'world') and self.world:
            planner.set_world(self.world)
        self.city_planners[tribe_color] = planner
        print(f"🏗️ Stadtplaner für {tribe_color} erstellt bei {center}")
        
    def build_house_for_npc(self, owner_id: str, tribe_color: str) -> House:
        """Baue Haus für NPC - SKALIERBARE LÖSUNG"""
        if owner_id in self.houses:
            return self.houses[owner_id]  # Haus bereits vorhanden
        
        # NEUE STRATEGIE: Einfache Regel - ein Haus pro NPC
        tribe_houses = self.get_tribe_houses(tribe_color)
        print(f"🏗️ {tribe_color}: {owner_id} will Haus bauen - bereits {len(tribe_houses)} Häuser vorhanden")
        
        # Kein Limit mehr - jeder NPC kann sein Haus haben
        
        # Finde Position mit Stadtplaner
        planner = self.city_planners.get(tribe_color)
        if not planner:
            print(f"⚠️ Kein Stadtplaner für {tribe_color}!")
            return None
            
        position = planner.find_house_position(tribe_color)
        house = House(position, owner_id, tribe_color)
        self.houses[owner_id] = house
        
        print(f"🏗️ Bauplatz für {owner_id} ({tribe_color}) erstellt - Haus #{len(tribe_houses) + 1}")
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