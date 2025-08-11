"""
Mining System - Stone und Gold abbauen mit Hitboxen und HP
"""

import pygame
import math
import random
import os

class ResourceDrop:
    """Ein sammelbarer Resource-Drop (Stone/Gold)"""
    def __init__(self, x, y, resource_image, resource_type, amount=3):
        self.x = x
        self.y = y
        self.resource_image = resource_image
        self.resource_type = resource_type  # "stone" oder "gold"
        self.amount = amount
        self.collected = False
        
        # Hitbox für Sammeln
        self.rect = pygame.Rect(x, y, resource_image.get_width(), resource_image.get_height())
        
        # Bounce-Animation
        self.bounce_time = random.uniform(0, math.pi * 2)  # Random start
        self.original_y = y
        
    def update(self, dt):
        """Update Animationen"""
        if self.collected:
            return
            
        # Leichtes Auf-und-Ab (Bounce)
        self.bounce_time += dt * 2
        bounce_offset = math.sin(self.bounce_time) * 2  # 2 Pixel auf/ab
        self.y = self.original_y + bounce_offset
        
    def draw(self, screen, camera_rect):
        """Zeichne Resource-Drop mit Bounce-Effekt"""
        if self.collected:
            return
            
        screen_x = self.x - camera_rect.left
        screen_y = self.y - camera_rect.top
        
        # Zeichne Resource-Sprite (mit bounce)
        screen.blit(self.resource_image, (screen_x, screen_y))
        
    def is_mouse_over(self, mouse_world_pos):
        """Prüfe ob Maus über Resource ist"""
        return not self.collected and self.rect.collidepoint(mouse_world_pos)
        
    def collect(self):
        """Sammle die Resource"""
        if not self.collected:
            self.collected = True
            print(f"⛏️ {self.resource_type.capitalize()} gesammelt! +{self.amount}")
            return self.amount
        return 0

class MineableResource:
    """Eine abbaubare Resource mit HP und Hitbox"""
    def __init__(self, x, y, resource_image, resource_type):
        self.x = x
        self.y = y
        self.resource_type = resource_type  # "stone" oder "gold"
        self.max_hp = 100
        self.current_hp = 100
        self.alive = True
        
        # Images
        self.resource_image = resource_image
        self.current_image = resource_image
        
        # Hitbox (ähnlich wie Baum)
        self.rect = pygame.Rect(x, y, resource_image.get_width(), resource_image.get_height())
        self.hitbox = pygame.Rect(
            x + resource_image.get_width() * 0.1,
            y + resource_image.get_height() * 0.1,
            resource_image.get_width() * 0.8,
            resource_image.get_height() * 0.8
        )
        
        # Animation
        self.shake_time = 0.0
        self.shake_intensity = 0.0
        self.original_x = x
        
        # HP Bar
        self.show_hp_bar = False
        self.hp_bar_timer = 0.0
        
        # Drop tracking (jeder 10. Schlag)
        self.hits_since_drop = 0
        
    def take_damage(self, damage=1):
        """Resource nimmt Schaden"""
        if not self.alive:
            return False
            
        self.current_hp -= damage
        self.hits_since_drop += damage
        self.show_hp_bar = True
        self.hp_bar_timer = 3.0  # 3 Sekunden HP-Bar anzeigen
        
        # Schüttel-Animation
        self.shake_time = 0.2  # 200ms schütteln
        self.shake_intensity = 3.0
        
        print(f"⛏️ {self.resource_type.capitalize()} getroffen! HP: {self.current_hp}/{self.max_hp}")
        
        # Alle 10 Schläge droppen (außer beim letzten Schlag)
        drop_position = None
        if self.hits_since_drop >= 10 and self.current_hp > 0:
            self.hits_since_drop = 0
            drop_position = self._get_drop_position()
            print(f"💎 {self.resource_type.capitalize()}-Drop nach 10 Schlägen!")
        
        # Resource vollständig abgebaut?
        if self.current_hp <= 0:
            self.deplete_resource()
            return (True, drop_position)  # True = vollständig abgebaut
        
        return (False, drop_position)  # False = noch nicht abgebaut, aber möglicherweise Drop
        
    def _get_drop_position(self):
        """Gib Position für Resource-Drop zurück"""
        drop_x = self.x + self.resource_image.get_width() + 10
        drop_y = self.y + self.resource_image.get_height() - 20
        return (drop_x, drop_y)
        
    def deplete_resource(self):
        """Resource ist vollständig abgebaut"""
        if not self.alive:
            return
            
        self.alive = False
        print(f"⛏️ {self.resource_type.capitalize()} vollständig abgebaut!")
        self.show_hp_bar = False
        
    def update(self, dt):
        """Update Animationen"""
        # Schüttel-Animation
        if self.shake_time > 0:
            self.shake_time -= dt
            shake_offset = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            self.x = self.original_x + shake_offset
            
            # Shake-Intensität abnehmen
            self.shake_intensity = max(0, self.shake_intensity - dt * 15)
        else:
            self.x = self.original_x
            
        # HP-Bar Timer
        if self.hp_bar_timer > 0:
            self.hp_bar_timer -= dt
            if self.hp_bar_timer <= 0:
                self.show_hp_bar = False
                
    def draw(self, screen, camera_rect):
        """Zeichne die Resource"""
        if not self.alive:
            return
            
        screen_x = self.x - camera_rect.left
        screen_y = self.y - camera_rect.top
        
        screen.blit(self.current_image, (screen_x, screen_y))
        
        # HP-Balken zeichnen (nur bei beschädigten Resources)
        if self.alive and self.show_hp_bar and self.current_hp < self.max_hp:
            self.draw_hp_bar(screen, screen_x, screen_y)
            
    def draw_hp_bar(self, screen, screen_x, screen_y):
        """Zeichne HP-Balken über der Resource"""
        bar_width = 40
        bar_height = 6
        bar_x = screen_x + (self.current_image.get_width() - bar_width) // 2
        bar_y = screen_y - 15
        
        # Hintergrund (grau)
        background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (100, 100, 100), background_rect)
        
        # HP-Füllung 
        hp_percentage = self.current_hp / self.max_hp
        fill_width = int(bar_width * hp_percentage)
        
        if fill_width > 0:
            # Farbe je nach Resource-Type
            if self.resource_type == "gold":
                color = (255, 215, 0)  # Gold
            else:  # stone
                color = (128, 128, 128)  # Grau
                
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            pygame.draw.rect(screen, color, fill_rect)
        
        # Rahmen
        pygame.draw.rect(screen, (255, 255, 255), background_rect, 1)
        
    def is_mouse_over(self, mouse_world_pos):
        """Prüfe ob Maus über Hitbox ist"""
        return self.alive and self.hitbox.collidepoint(mouse_world_pos)


class MiningSystem:
    """Verwaltet alle abbaubaren Resources in der Welt"""
    def __init__(self, simple_world=None):
        self.resources = []
        self.resource_drops = []  # Liste aller Resource-Drops
        self.simple_world = simple_world
        
        # Lade Resource-Sprites
        self.resource_images = self._load_resource_images()
        
        # Konvertiere existierende Resources aus SimpleWorld
        if simple_world:
            self._convert_existing_resources()
            
    def _load_resource_images(self):
        """Lade Resource-Sprites"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        images = {}
        
        # Stone und Gold Sprites laden
        stone_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', 'stone.png')
        gold_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', 'gold.png')
        stone_barren_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', 'stein_barren.png')
        gold_barren_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', 'gold_barren.png')
        
        for name, path in [('stone', stone_path), ('gold', gold_path), 
                          ('stone_barren', stone_barren_path), ('gold_barren', gold_barren_path)]:
            if os.path.exists(path):
                try:
                    sprite = pygame.image.load(path).convert_alpha()
                    
                    # Stone und Gold größer machen (aber nicht die Barren-Items)
                    if name in ['stone', 'gold']:
                        original_size = sprite.get_size()
                        scale_factor = 2.5  # 2.5x größer
                        new_width = int(original_size[0] * scale_factor)
                        new_height = int(original_size[1] * scale_factor)
                        sprite = pygame.transform.scale(sprite, (new_width, new_height))
                        print(f"⛏️ {name} skaliert: {original_size} → {(new_width, new_height)}")
                    
                    images[name] = sprite
                    print(f"⛏️ {name} Sprite geladen: {sprite.get_size()}")
                except Exception as e:
                    print(f"⚠️ Fehler beim Laden von {name}: {e}")
            else:
                print(f"⚠️ {name} Sprite nicht gefunden: {path}")
                
        return images
        
    def _convert_existing_resources(self):
        """Konvertiere bestehende Resources aus SimpleWorld decorations"""
        if not self.simple_world or not hasattr(self.simple_world, 'decorations'):
            return
            
        # Finde stone.png und gold.png decorations und konvertiere sie zu MineableResource
        resources_to_remove = []
        
        for i, decoration in enumerate(self.simple_world.decorations):
            if decoration['name'] in ['stone.png', 'gold.png']:
                resource_type = decoration['name'].replace('.png', '')
                resource_image = decoration['sprite']
                
                resource = MineableResource(decoration['x'], decoration['y'], resource_image, resource_type)
                self.resources.append(resource)
                resources_to_remove.append(i)
                
        # Entferne konvertierte Decorations
        for i in reversed(resources_to_remove):
            self.simple_world.decorations.pop(i)
            
        print(f"⛏️ {len(self.resources)} Resources zu Mining-System konvertiert!")
        
    def handle_click(self, world_pos, player_pos, inventory=None):
        """Handle Mausklick auf Resources und Resource-Drops"""
        mouse_x, mouse_y = world_pos
        player_x, player_y = player_pos
        
        # Prüfe zuerst Resource-Drops (haben Priorität)
        for resource_drop in self.resource_drops:
            if resource_drop.is_mouse_over((mouse_x, mouse_y)):
                # Prüfe Entfernung zum Spieler
                distance = math.sqrt((resource_drop.x - player_x)**2 + (resource_drop.y - player_y)**2)
                
                if distance <= 60:  # Reichweite für Sammeln
                    amount = resource_drop.collect()
                    if amount > 0 and inventory:
                        # Füge Resource zum Inventar hinzu
                        inventory.add_item(resource_drop.resource_type, amount)
                        # Entferne gesammelten Drop aus Liste
                        self.resource_drops.remove(resource_drop)
                    return True
                else:
                    print(f"🚶 Zu weit weg! Gehe näher zu {resource_drop.resource_type}.")
                    return False
        
        # Dann prüfe Resources
        for resource in self.resources:
            if resource.is_mouse_over((mouse_x, mouse_y)):
                # Prüfe Entfernung zum Spieler
                distance = math.sqrt((resource.x - player_x)**2 + (resource.y - player_y)**2)
                
                if distance <= 50:
                    depleted, drop_pos = resource.take_damage(1)  # 1 Schaden pro Klick
                    
                    # Wenn Drop-Position zurückgegeben wird, erstelle Drop
                    if drop_pos:
                        resource_type = resource.resource_type
                        if resource_type == "stone":
                            drop_image = self.resource_images.get('stone_barren')
                        else:  # gold
                            drop_image = self.resource_images.get('gold_barren')
                            
                        if drop_image:
                            resource_drop = ResourceDrop(drop_pos[0], drop_pos[1], drop_image, resource_type, 3)
                            self.resource_drops.append(resource_drop)
                            print(f"💎 {resource_type.capitalize()}-Drop ist erschienen!")
                    
                    # Wenn Resource vollständig abgebaut wurde
                    if depleted:
                        print(f"⛏️ {resource.resource_type.capitalize()} vollständig abgebaut!")
                    
                    return True
                else:
                    print(f"🚶 Zu weit weg! Gehe näher zu {resource.resource_type}.")
                    return False
        
        return False
        
    def update(self, dt):
        """Update alle Resources und Resource-Drops"""
        for resource in self.resources:
            resource.update(dt)
            
        # Update Resource-Drops (Bounce-Animation)
        for resource_drop in self.resource_drops:
            resource_drop.update(dt)
            
    def draw(self, screen, camera_rect):
        """Zeichne alle Resources und Resource-Drops"""
        # Zeichne Resources (sortiert nach Y-Position)
        visible_resources = [r for r in self.resources if r.alive and r.rect.colliderect(camera_rect)]
        visible_resources.sort(key=lambda r: r.y + r.current_image.get_height())
        
        for resource in visible_resources:
            resource.draw(screen, camera_rect)
            
        # Zeichne Resource-Drops (nach Resources, damit sie sichtbar sind)
        for resource_drop in self.resource_drops:
            if not resource_drop.collected:
                resource_drop.draw(screen, camera_rect)
            
    def get_collision_rects(self):
        """Gib Kollisions-Rechtecke für lebende Resources zurück"""
        return [resource.hitbox for resource in self.resources if resource.alive]