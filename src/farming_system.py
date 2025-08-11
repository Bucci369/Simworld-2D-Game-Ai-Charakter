import pygame
import random
import math
import os
from settings import TILE_SIZE

# Verbesserte Farming und Tier-System für das Spiel mit Maus-Steuerung

class Crop:
    """Einzelne Pflanze auf einem Farmland-Tile"""
    def __init__(self, crop_type, tile_x, tile_y):
        self.crop_type = crop_type  # "carrot"
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.x = tile_x * TILE_SIZE  # Welt-Koordinaten
        self.y = tile_y * TILE_SIZE
        self.growth_stage = 0  # 0 = Samen, 1-3 = Wachstum, 3 = Reif
        self.max_growth = 3  # Karotten haben 3 Stufen
        self.growth_time = 0.0  # Zeit seit letztem Wachstum (in Spielstunden)
        self.watered = False
        self.ready_to_harvest = False
        
        # Karotten brauchen nur 10 Sekunden pro Stufe (für schnelle Tests!)
        self.growth_rate = 0.1  # 0.1 Spielstunden = ~4 echte Sekunden pro Wachstumsstufe
        
    def update(self, game_hours_passed):
        """Update der Pflanze basierend auf Spielzeit"""
        if self.growth_stage >= self.max_growth:
            self.ready_to_harvest = True
            return
            
        # Nur wachsen wenn gegossen
        if self.watered:
            self.growth_time += game_hours_passed
            
            # Wachse zur nächsten Stufe
            if self.growth_time >= self.growth_rate:
                self.growth_stage += 1
                self.growth_time = 0.0
                self.watered = False  # Muss wieder gegossen werden
                
                if self.growth_stage >= self.max_growth:
                    self.ready_to_harvest = True
                    print(f"Karotte bei ({self.tile_x}, {self.tile_y}) ist reif zum Ernten!")
    
    def water(self):
        """Pflanze gießen"""
        if self.growth_stage < self.max_growth:
            self.watered = True
            print(f"Karotte bei ({self.tile_x}, {self.tile_y}) gegossen!")
            
    def harvest(self):
        """Pflanze ernten - gibt Items zurück"""
        if self.ready_to_harvest:
            yield_amount = random.randint(1, 3)  # 1-3 Karotten
            return {"carrot": yield_amount}
        return {}

class Animal(pygame.sprite.Sprite):
    """Animiertes Tier mit Sprite-Sheet Animation wie der Player"""
    def __init__(self, animal_type, pos, world=None):
        super().__init__()
        self.animal_type = animal_type  # "cow", "pig", "chicken", "sheep"
        self.world = world
        self.speed = 50  # Langsamer als Player
        
        # Animation System (wie Player)
        self.direction = 'down'
        self.anim_time_acc = 0.0
        self.anim_frame_index = 0
        self.animations = {}
        self.idle_frames = {}
        
        # Tier-spezifische Eigenschaften
        self.hunger = 100
        self.happiness = 100
        self.last_fed = 0  # Wann zuletzt gefüttert (Spielstunden)
        self.production_time = 0.0  # Zeit bis nächste Produktion
        
        # Bewegungs-AI
        self.target_pos = None
        self.wander_timer = 0.0
        self.wander_delay = random.uniform(3.0, 8.0)  # 3-8 Sekunden bis nächste Bewegung
        self.moving = False
        
        # Produktions-Eigenschaften
        self.products = {
            "cow": {"milk": {"time": 6.0, "amount": 1}},      # Alle 6 Spielstunden 1 Milch
            "chicken": {"egg": {"time": 4.0, "amount": 1}},   # Alle 4 Spielstunden 1 Ei
            "pig": {"truffle": {"time": 12.0, "amount": 1}},  # Alle 12 Spielstunden 1 Trüffel
            "sheep": {"wool": {"time": 8.0, "amount": 1}}     # Alle 8 Spielstunden 1 Wolle
        }
        
        self._load_animal_sprite()
        
        # Position setzen
        if self.image:
            self.rect = self.image.get_rect(center=pos)
        else:
            self.rect = pygame.Rect(pos[0]-16, pos[1]-16, 32, 32)
    
    def _load_animal_sprite(self):
        """Lädt das Sprite-Sheet für das Tier"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Tier-spezifische Pfade
        animal_paths = {
            "cow": os.path.join(base_dir, 'assets', 'Animals', 'Cow', 'Cow.png'),
            "pig": os.path.join(base_dir, 'assets', 'Animals', 'Pig', 'Pig.png'),
            "chicken": os.path.join(base_dir, 'assets', 'Animals', 'Chicken', 'Chicken.png'),
            "sheep": os.path.join(base_dir, 'assets', 'Animals', 'Sheep', 'Sheep.png')
        }
        
        sprite_path = animal_paths.get(self.animal_type)
        if not sprite_path or not os.path.exists(sprite_path):
            # Fallback: Farbiges Rechteck
            self._create_fallback_sprite()
            return
            
        try:
            sheet = pygame.image.load(sprite_path).convert_alpha()
            self._extract_animations(sheet)
        except Exception as e:
            print(f"Fehler beim Laden von {sprite_path}: {e}")
            self._create_fallback_sprite()
    
    def _create_fallback_sprite(self):
        """Erstellt einen farbigen Fallback-Sprite"""
        colors = {
            "cow": (139, 69, 19),      # Braun
            "pig": (255, 182, 193),    # Rosa
            "chicken": (255, 255, 255), # Weiß
            "sheep": (248, 248, 255)   # Weiß-grau
        }
        
        color = colors.get(self.animal_type, (128, 128, 128))
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        surf.fill(color)
        
        # Einfache Form
        pygame.draw.ellipse(surf, color, (4, 8, 24, 16))  # Körper
        pygame.draw.circle(surf, color, (16, 6), 6)       # Kopf
        
        # Für alle Richtungen das gleiche Bild
        self.animations = {d: [surf] for d in ['down', 'up', 'left', 'right']}
        self.idle_frames = {d: surf for d in ['down', 'up', 'left', 'right']}
        self.image = surf
    
    def _extract_animations(self, sheet):
        """Extrahiert Animationen aus dem Sprite-Sheet"""
        w, h = sheet.get_size()
        
        # Prüfe verschiedene Grid-Größen
        if w == h:  # Quadratisches Bild - versuche 2x2 oder 4x1
            if w >= 64:  # Mindestgröße für 2x2
                frame_size = w // 2
                frames = []
                for row in range(2):
                    for col in range(2):
                        frame = pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
                        frame.blit(sheet, (0, 0), (col * frame_size, row * frame_size, frame_size, frame_size))
                        frames.append(pygame.transform.scale(frame, (32, 32)))
                
                # Weise Frames zu Richtungen zu
                self.animations = {
                    'down': [frames[0], frames[1]] if len(frames) >= 2 else [frames[0]],
                    'up': [frames[2], frames[3]] if len(frames) >= 4 else [frames[0]],
                    'left': [frames[0], frames[1]] if len(frames) >= 2 else [frames[0]],
                    'right': [frames[0], frames[1]] if len(frames) >= 2 else [frames[0]]
                }
            else:
                # Zu klein - verwende ganzes Bild
                scaled = pygame.transform.scale(sheet, (32, 32))
                self.animations = {d: [scaled] for d in ['down', 'up', 'left', 'right']}
        else:
            # Rechteckiges Bild - versuche horizontale oder vertikale Aufteilung
            if w > h:  # Horizontal
                frames_count = min(4, w // h) if h > 0 else 1
                frame_width = w // frames_count if frames_count > 0 else w
                frames = []
                for i in range(frames_count):
                    frame = pygame.Surface((frame_width, h), pygame.SRCALPHA)
                    frame.blit(sheet, (0, 0), (i * frame_width, 0, frame_width, h))
                    frames.append(pygame.transform.scale(frame, (32, 32)))
                
                self.animations = {
                    'down': frames,
                    'up': frames,
                    'left': frames,
                    'right': frames
                }
            else:  # Vertikal
                frames_count = min(4, h // w) if w > 0 else 1
                frame_height = h // frames_count if frames_count > 0 else h
                frames = []
                for i in range(frames_count):
                    frame = pygame.Surface((w, frame_height), pygame.SRCALPHA)
                    frame.blit(sheet, (0, 0), (0, i * frame_height, w, frame_height))
                    frames.append(pygame.transform.scale(frame, (32, 32)))
                
                self.animations = {
                    'down': frames,
                    'up': frames,
                    'left': frames,
                    'right': frames
                }
        
        # Idle Frames sind erste Frames jeder Richtung
        self.idle_frames = {direction: frames[0] for direction, frames in self.animations.items()}
        self.image = self.idle_frames['down']
    
    def update(self, dt, game_time):
        """Update des Tiers"""
        # Hunger und Glück verringern sich über Zeit
        hours_passed = dt / 3600  # dt ist in Sekunden, umrechnen zu Stunden
        self.hunger = max(0, self.hunger - hours_passed * 5)  # 5 Hunger pro Stunde
        self.happiness = max(0, self.happiness - hours_passed * 2)  # 2 Glück pro Stunde
        
        # Bewegungs-AI
        self._update_movement(dt)
        
        # Animation
        self._update_animation(dt)
        
        # Produktion
        self._update_production(game_time)
    
    def _update_movement(self, dt):
        """Einfache Wander-AI"""
        self.wander_timer += dt
        
        if self.target_pos and self.moving:
            # Bewege zum Ziel
            direction = pygame.Vector2(self.target_pos) - pygame.Vector2(self.rect.center)
            distance = direction.length()
            
            if distance > 5:
                direction = direction.normalize()
                movement = direction * self.speed * dt
                self.rect.center = (self.rect.centerx + movement.x, self.rect.centery + movement.y)
                
                # Bestimme Animations-Richtung
                if abs(direction.x) > abs(direction.y):
                    self.direction = 'right' if direction.x > 0 else 'left'
                else:
                    self.direction = 'down' if direction.y > 0 else 'up'
            else:
                # Ziel erreicht
                self.target_pos = None
                self.moving = False
                self.wander_timer = 0.0
                self.wander_delay = random.uniform(2.0, 6.0)
        
        elif self.wander_timer >= self.wander_delay:
            # Neues Ziel wählen
            if self.world:
                # Wähle Position in der Nähe
                offset_x = random.randint(-100, 100)
                offset_y = random.randint(-100, 100)
                new_x = max(50, min(self.world.width - 50, self.rect.centerx + offset_x))
                new_y = max(50, min(self.world.height - 50, self.rect.centery + offset_y))
                self.target_pos = (new_x, new_y)
                self.moving = True
    
    def _update_animation(self, dt):
        """Animation wie beim Player"""
        if self.moving and self.direction in self.animations:
            self.anim_time_acc += dt
            if self.anim_time_acc >= 0.2:  # 200ms pro Frame
                self.anim_time_acc = 0.0
                frames = self.animations[self.direction]
                self.anim_frame_index = (self.anim_frame_index + 1) % len(frames)
                self.image = frames[self.anim_frame_index]
        else:
            # Idle
            if self.direction in self.idle_frames:
                self.image = self.idle_frames[self.direction]
    
    def _update_production(self, game_time):
        """Tier-Produktion basierend auf Spielzeit"""
        if self.animal_type not in self.products:
            return
            
        product_info = list(self.products[self.animal_type].values())[0]
        production_interval = product_info["time"]
        
        self.production_time += game_time.get_hours_passed()
        
        # Nur produzieren wenn zufrieden
        if self.hunger > 50 and self.happiness > 30:
            if self.production_time >= production_interval:
                self.production_time = 0.0
                return True  # Bereit zur Produktion
        
        return False
    
    def feed(self):
        """Tier füttern"""
        self.hunger = min(100, self.hunger + 30)
        self.happiness = min(100, self.happiness + 10)
    
    def pet(self):
        """Tier streicheln"""
        self.happiness = min(100, self.happiness + 20)

class FarmingSystem:
    """Maus-basiertes Farming-System mit Grid-UI"""
    def __init__(self, world):
        self.world = world
        self.crops = {}  # Dictionary: (tile_x, tile_y) -> Crop
        self.animals = pygame.sprite.Group()
        
        # Inventar
        self.seeds_inventory = {"carrot": 20}  # Genug Karotten-Samen
        self.products_inventory = {}
        
        # Farm-Bereiche (werden vom UI verwaltet)
        self.farm_tiles = set()
        
    def set_farm_tiles(self, farm_tiles):
        """Setze Farm-Tiles vom UI"""
        self.farm_tiles = farm_tiles
        
    def plant_crop_at_tile(self, tile_x, tile_y, crop_type="carrot"):
        """Pflanze Crop an Tile-Koordinaten"""
        if crop_type not in self.seeds_inventory or self.seeds_inventory[crop_type] <= 0:
            print(f"Keine {crop_type}-Samen im Inventar!")
            return False
            
        # Prüfe ob es ein Farm-Tile ist
        if (tile_x, tile_y) not in self.farm_tiles:
            print("Das ist kein Farm-Bereich!")
            return False
        
        # Prüfe ob bereits bepflanzt
        if (tile_x, tile_y) in self.crops:
            print("Hier wächst bereits etwas!")
            return False
            
        # Pflanze Crop
        crop = Crop(crop_type, tile_x, tile_y)
        self.crops[(tile_x, tile_y)] = crop
        self.seeds_inventory[crop_type] -= 1
        print(f"{crop_type.title()} gepflanzt bei ({tile_x}, {tile_y})!")
        return True
    
    def water_crop_at_tile(self, tile_x, tile_y):
        """Gieße Pflanze an Tile-Koordinaten"""
        if (tile_x, tile_y) in self.crops:
            crop = self.crops[(tile_x, tile_y)]
            crop.water()
            return True
        print("Keine Pflanze zum Gießen hier!")
        return False
    
    def harvest_crop_at_tile(self, tile_x, tile_y, inventory=None):
        """Ernte Pflanze an Tile-Koordinaten"""
        if (tile_x, tile_y) in self.crops:
            crop = self.crops[(tile_x, tile_y)]
            if crop.ready_to_harvest:
                items = crop.harvest()
                # Füge zu Inventar hinzu
                for item, amount in items.items():
                    if inventory:
                        # Neues Stack-basiertes Inventar verwenden
                        added = inventory.add_item(item, amount)
                        print(f"Geerntet! +{added} {item}")
                    else:
                        # Fallback auf altes System
                        if item not in self.products_inventory:
                            self.products_inventory[item] = 0
                        self.products_inventory[item] += amount
                        print(f"Geerntet! +{amount} {item}. Inventar: {self.products_inventory}")
                
                # Entferne Pflanze
                del self.crops[(tile_x, tile_y)]
                return True
            else:
                print("Pflanze ist noch nicht reif!")
        else:
            print("Keine Pflanze zum Ernten hier!")
        return False
    
    def handle_farm_action(self, action_data, inventory=None):
        """Behandle Farm-Aktionen vom UI"""
        if not action_data:
            return False
            
        action = action_data['action']
        world_pos = action_data['pos']
        tile_x = int(world_pos[0] // TILE_SIZE)
        tile_y = int(world_pos[1] // TILE_SIZE)
        
        if action == 'plant':
            crop_type = action_data.get('crop', 'carrot')
            return self.plant_crop_at_tile(tile_x, tile_y, crop_type)
        elif action == 'harvest':
            return self.harvest_crop_at_tile(tile_x, tile_y, inventory)
        elif action == 'water':
            return self.water_crop_at_tile(tile_x, tile_y)
            
        return False
    
    def place_animal(self, animal_type, world_pos):
        """Platziere ein Tier in der Welt"""
        animal = Animal(animal_type, world_pos, self.world)
        self.animals.add(animal)
        return animal
    
    def interact_with_animal(self, world_pos, action="feed"):
        """Interagiere mit Tier an Position"""
        for animal in self.animals:
            distance = math.sqrt((animal.rect.centerx - world_pos[0])**2 + 
                               (animal.rect.centery - world_pos[1])**2)
            if distance < 40:  # In der Nähe
                if action == "feed":
                    animal.feed()
                elif action == "pet":
                    animal.pet()
                elif action == "collect":
                    # Versuche Produktion zu sammeln
                    if animal._update_production(None):  # Prüfe ob bereit
                        product_name = list(animal.products[animal.animal_type].keys())[0]
                        amount = animal.products[animal.animal_type][product_name]["amount"]
                        
                        if product_name not in self.products_inventory:
                            self.products_inventory[product_name] = 0
                        self.products_inventory[product_name] += amount
                        animal.production_time = 0.0  # Reset
                return True
        return False
    
    def update(self, dt, game_time):
        """Update aller Farming-Elemente"""
        # Update Pflanzen
        hours_passed = game_time.get_hours_passed() if hasattr(game_time, 'get_hours_passed') else dt / 3600
        for crop in self.crops.values():
            crop.update(hours_passed)
        
        # Update Tiere
        self.animals.update(dt, game_time)
    
    def draw_crops(self, screen, camera):
        """Zeichne alle Pflanzen - wird von farm_ui.draw_crops übernommen"""
        # Diese Methode wird nicht mehr verwendet, da farm_ui.draw_crops die Pflanzen zeichnet
        pass
    
    def draw_animals(self, screen, camera):
        """Zeichne alle Tiere"""
        for animal in self.animals:
            screen_pos = camera.apply_to_point(animal.rect.topleft)
            screen.blit(animal.image, screen_pos)
