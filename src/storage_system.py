"""
Storage System - Visuelle Lager für jedes Volk
"""

import pygame
import os
from typing import Dict, Tuple, List

class TribeStorage:
    """Ein visuelles Lager für ein Volk mit Rohstoffen"""
    
    def __init__(self, position: Tuple[float, float], tribe_color: str):
        self.position = pygame.Vector2(position)
        self.tribe_color = tribe_color
        
        # Rohstoffe im Lager
        self.resources = {
            'wood': 0,
            'stone': 0,
            'food': 0
        }
        
        # Visuelles
        self.size = (80, 60)  # Lager-Größe
        self.sprite = self._create_storage_sprite()
        
        # Hitbox für Interaktion
        self.rect = pygame.Rect(position[0], position[1], self.size[0], self.size[1])
        
    def get_resource_amount(self, resource: str) -> int:
        """Gibt die Menge einer Ressource zurück"""
        return self.resources.get(resource, 0)
        
    def add_resources(self, resource: str, amount: int):
        """Fügt Ressourcen zum Lager hinzu"""
        if resource in self.resources:
            self.resources[resource] += amount
            print(f"📦 {self.tribe_color.upper()} Lager: +{amount} {resource} (Total: {self.resources[resource]})")
            
    def remove_resources(self, resource: str, amount: int) -> bool:
        """Entfernt Ressourcen aus dem Lager"""
        if resource in self.resources and self.resources[resource] >= amount:
            self.resources[resource] -= amount
            print(f"📦 {self.tribe_color.upper()} Lager: -{amount} {resource} (Total: {self.resources[resource]})")
            return True
        return False
        
        # Visuelles
        self.size = (80, 60)  # Lager-Größe
        self.sprite = self._create_storage_sprite()
        
        # Hitbox für Interaktion
        self.rect = pygame.Rect(position[0], position[1], self.size[0], self.size[1])
        
    def _create_storage_sprite(self) -> pygame.Surface:
        """Erstelle visuelles Lager-Sprite"""
        storage = pygame.Surface(self.size, pygame.SRCALPHA)
        
        # Basis-Lager (braune Kiste)
        pygame.draw.rect(storage, (101, 67, 33), (0, 0, self.size[0], self.size[1]))
        pygame.draw.rect(storage, (139, 69, 19), (5, 5, self.size[0]-10, self.size[1]-10))
        
        # Volk-spezifische Farb-Markierung
        color_map = {
            'red': (255, 100, 100),
            'blue': (100, 100, 255), 
            'green': (100, 255, 100)
        }
        
        tribe_color_rgb = color_map.get(self.tribe_color, (255, 255, 255))
        pygame.draw.rect(storage, tribe_color_rgb, (10, 10, 20, 20))
        
        # "LAGER" Text
        font_size = 12
        try:
            font = pygame.font.Font(None, font_size)
            text = font.render("LAGER", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.size[0]//2, self.size[1]//2))
            storage.blit(text, text_rect)
        except:
            pass  # Fallback ohne Text
            
        return storage
    
    def take_resources(self, resource_type: str, amount: int) -> int:
        """Nimm Rohstoffe aus dem Lager"""
        if resource_type in self.resources:
            available = min(self.resources[resource_type], amount)
            self.resources[resource_type] -= available
            if available > 0:
                print(f"📦 {self.tribe_color.upper()} Lager: -{available} {resource_type} (Remaining: {self.resources[resource_type]})")
            return available
        return 0
    
    def has_resources(self, resource_type: str, amount: int) -> bool:
        """Prüfe ob genug Rohstoffe vorhanden sind"""
        return self.resources.get(resource_type, 0) >= amount
    
    def get_total_resources(self) -> Dict[str, int]:
        """Hole alle Rohstoffe"""
        return self.resources.copy()
    
    def draw(self, screen: pygame.Surface, camera_rect: pygame.Rect):
        """Zeichne das Lager"""
        screen_x = self.position.x - camera_rect.left
        screen_y = self.position.y - camera_rect.top
        
        screen.blit(self.sprite, (screen_x, screen_y))
        
        # Zeige Rohstoff-Informationen
        self._draw_resource_info(screen, screen_x, screen_y)
    
    def _draw_resource_info(self, screen: pygame.Surface, screen_x: float, screen_y: float):
        """Zeige Rohstoff-Mengen über dem Lager"""
        try:
            font = pygame.font.Font(None, 16)
            y_offset = -30
            
            for resource, amount in self.resources.items():
                if amount > 0:
                    color = (255, 255, 255)
                    if resource == 'wood':
                        color = (139, 69, 19)  # Braun
                    elif resource == 'stone':
                        color = (128, 128, 128)  # Grau
                    elif resource == 'food':
                        color = (255, 215, 0)  # Gold
                    
                    text = font.render(f"{resource}: {amount}", True, color)
                    screen.blit(text, (screen_x, screen_y + y_offset))
                    y_offset -= 18
        except:
            pass  # Fallback ohne Text


class StorageSystem:
    """Verwaltet alle Lager der Völker"""
    
    def __init__(self):
        self.storages = {}  # {tribe_color: TribeStorage}
    
    def create_storage(self, position: Tuple[float, float], tribe_color: str):
        """Erstelle ein Lager für ein Volk"""
        storage = TribeStorage(position, tribe_color)
        self.storages[tribe_color] = storage
        print(f"📦 {tribe_color.upper()} Lager erstellt bei {position}")
        return storage
    
    def get_storage(self, tribe_color: str) -> TribeStorage:
        """Hole das Lager eines Volkes"""
        return self.storages.get(tribe_color)
    
    def update(self, dt: float):
        """Update alle Lager"""
        pass  # Lager brauchen kein Update
    
    def draw(self, screen: pygame.Surface, camera_rect: pygame.Rect):
        """Zeichne alle Lager"""
        for storage in self.storages.values():
            storage.draw(screen, camera_rect)
    
    def handle_click(self, world_pos: Tuple[float, float], player_pos: Tuple[float, float]):
        """Handle Klicks auf Lager"""
        for tribe_color, storage in self.storages.items():
            if storage.rect.collidepoint(world_pos):
                # Zeige Lager-Informationen
                resources = storage.get_total_resources()
                print(f"📦 {tribe_color.upper()} LAGER:")
                for resource, amount in resources.items():
                    print(f"  {resource}: {amount}")
                return True
        return False