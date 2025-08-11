import math
import random
import pygame
import os
from settings import TILE_SIZE, PLAYER_SHEET_ROWS, PLAYER_FRAMES_PER_DIRECTION

ANIM_FRAME_TIME = 0.15  # Sekunden pro Frame

class NPC(pygame.sprite.Sprite):
    """Ein NPC der wie der Player aussieht aber AI-gesteuert ist"""
    def __init__(self, pos, world=None, npc_id=0):
        super().__init__()
        self.speed = 120  # Etwas langsamer als Player
        self.world = world
        self.npc_id = npc_id
        
        # Bewegungs-AI
        self.target_pos = None
        self.arrive_threshold = 8
        self.wander_timer = 0.0
        self.wander_delay = random.uniform(2.0, 5.0)  # Sekunden zwischen Bewegungen
        self.home_area = pygame.Vector2(pos)  # Startgebiet
        self.wander_radius = 150  # Wie weit vom Startpunkt entfernt
        
        # Schwarm-Verhalten
        self.flock_mates = []  # Andere NPCs in der Nähe
        self.separation_distance = 40  # Mindestabstand zu anderen
        self.cohesion_distance = 80   # Sichtweite für Schwarm
        self.alignment_distance = 60  # Ausrichtung an anderen
        
        # Animationsverwaltung (kopiert vom Player)
        self.direction = 'down'
        self.anim_time_acc = 0.0
        self.anim_frame_index = 0
        self.animations = {}
        self.idle_frames = {}
        
        self._load_sheet()
        # Fallback falls nichts geladen wurde
        if not self.animations:
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            # Verschiedene Farben für verschiedene NPCs
            colors = [(100, 255, 100), (100, 100, 255), (255, 100, 100), 
                     (255, 255, 100), (255, 100, 255), (100, 255, 255),
                     (200, 150, 100), (150, 200, 150)]
            color = colors[npc_id % len(colors)]
            surf.fill(color)
            self.animations = {d: [surf] for d in ['down','up','left','right']}
            self.idle_frames = {d: surf for d in ['down','up','left','right']}

        self.image = self.idle_frames[self.direction]
        self.rect = self.image.get_rect(topleft=pos)
        
    def _load_sheet(self):
        """Lädt das gleiche Sprite-Sheet wie der Player"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        sheet_path = os.path.join(base_dir, 'assets', 'Player', 'character-grid-sprite.png')
        if not os.path.exists(sheet_path):
            return
        try:
            sheet = pygame.image.load(sheet_path).convert_alpha()
        except Exception:
            return
        w, h = sheet.get_size()
        cols = w // TILE_SIZE
        rows = h // TILE_SIZE
        
        # Slice alle Tiles (gleich wie Player)
        grid = []
        for ry in range(rows):
            row_frames = []
            y = ry * TILE_SIZE
            for cx in range(cols):
                x = cx * TILE_SIZE
                frame = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                frame.blit(sheet, (0, 0), (x, y, TILE_SIZE, TILE_SIZE))
                if pygame.mask.from_surface(frame).count() == 0:
                    continue
                row_frames.append(frame)
            if row_frames:
                grid.append(row_frames)

        # Konfiguriertes Mapping der Reihen (gleich wie Player)
        for direction, row_index in PLAYER_SHEET_ROWS.items():
            if row_index == -1 and direction == 'left':
                continue
            if 0 <= row_index < len(grid):
                row_frames = grid[row_index]
                frames = row_frames[:PLAYER_FRAMES_PER_DIRECTION] if PLAYER_FRAMES_PER_DIRECTION else row_frames
                if frames:
                    self.animations[direction] = frames
                    self.idle_frames[direction] = frames[0]

        # Mirroring für left falls konfiguriert
        if PLAYER_SHEET_ROWS.get('left') == -1 and 'right' in self.animations:
            mirrored = [pygame.transform.flip(f, True, False) for f in self.animations['right']]
            self.animations['left'] = mirrored
            self.idle_frames['left'] = mirrored[0]

        # Fallback falls bestimmte Richtungen fehlen
        if len(self.animations) < 4 and grid:
            first = next(iter(self.animations.values()), grid[0])
            for d in ['down','left','right','up']:
                if d not in self.animations:
                    self.animations[d] = first
                    self.idle_frames[d] = first[0]
    
    def _calculate_flocking_force(self):
        """Berechnet Schwarm-Kräfte: Trennung, Kohäsion, Ausrichtung"""
        if not self.flock_mates:
            return pygame.Vector2(0, 0)
            
        my_pos = pygame.Vector2(self.rect.center)
        
        # Separation: Weg von zu nahen NPCs
        separation = pygame.Vector2(0, 0)
        separation_count = 0
        
        # Cohesion: Hin zur Mitte der Gruppe
        cohesion = pygame.Vector2(0, 0)
        cohesion_count = 0
        
        # Alignment: Gleiche Richtung wie andere
        alignment = pygame.Vector2(0, 0)
        alignment_count = 0
        
        for mate in self.flock_mates:
            if mate == self:
                continue
                
            mate_pos = pygame.Vector2(mate.rect.center)
            distance = my_pos.distance_to(mate_pos)
            
            # Separation
            if distance < self.separation_distance and distance > 0:
                diff = my_pos - mate_pos
                diff = diff.normalize() / distance  # Stärker bei kürzerer Distanz
                separation += diff
                separation_count += 1
            
            # Cohesion
            if distance < self.cohesion_distance:
                cohesion += mate_pos
                cohesion_count += 1
                
            # Alignment
            if distance < self.alignment_distance and hasattr(mate, 'velocity'):
                alignment += mate.velocity
                alignment_count += 1
        
        # Normalisiere die Kräfte
        if separation_count > 0:
            separation /= separation_count
            if separation.length() > 0:
                separation = separation.normalize() * 1.5  # Starke Trennung
        
        if cohesion_count > 0:
            cohesion /= cohesion_count
            cohesion = cohesion - my_pos  # Richtung zur Mitte
            if cohesion.length() > 0:
                cohesion = cohesion.normalize() * 0.5  # Schwache Kohäsion
        
        if alignment_count > 0:
            alignment /= alignment_count
            if alignment.length() > 0:
                alignment = alignment.normalize() * 0.3  # Schwache Ausrichtung
        
        return separation + cohesion + alignment
    
    def _get_random_target_in_area(self):
        """Gibt eine zufällige Position in der Nähe des Home-Bereichs zurück"""
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(20, self.wander_radius)
        
        target_x = self.home_area.x + math.cos(angle) * distance
        target_y = self.home_area.y + math.sin(angle) * distance
        
        return pygame.Vector2(target_x, target_y)
    
    def _update_direction(self, move_vec):
        """Update der Blickrichtung basierend auf Bewegung"""
        if move_vec.length_squared() == 0:
            return
        dx, dy = move_vec.x, move_vec.y
        if abs(dx) > abs(dy):
            self.direction = 'right' if dx > 0 else 'left'
        else:
            self.direction = 'down' if dy > 0 else 'up'
    
    def _animate(self, dt, moving):
        """Animation basierend auf Bewegung"""
        frames = self.animations[self.direction]
        if not moving:
            self.anim_frame_index = 0
            self.image = self.idle_frames[self.direction]
            return
        self.anim_time_acc += dt
        if self.anim_time_acc >= ANIM_FRAME_TIME:
            self.anim_time_acc -= ANIM_FRAME_TIME
            self.anim_frame_index = (self.anim_frame_index + 1) % len(frames)
        self.image = frames[self.anim_frame_index]
    
    def update(self, dt):
        """Update der NPC AI und Bewegung"""
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
            current = pygame.Vector2(self.rect.center)
            
            # Grundrichtung zum Ziel
            delta = self.target_pos - current
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
                tentative = current + step
                new_rect = self.rect.copy()
                new_rect.center = (round(tentative.x), round(tentative.y))
                
                # Kollision mit Wasser prüfen
                if self.world and hasattr(self.world, 'is_blocked_rect') and self.world.is_blocked_rect(new_rect):
                    # Neues Ziel suchen wenn blockiert
                    self.target_pos = self._get_random_target_in_area()
                else:
                    self.rect = new_rect
                    self.velocity = step  # Für Alignment speichern
                    moving = True
                
                self._update_direction(direction)
        
        self._animate(dt, moving)


class NPCSystem:
    """Verwaltet alle NPCs und ihr Schwarm-Verhalten"""
    def __init__(self, world=None):
        self.world = world
        self.npcs = pygame.sprite.Group()
        
    def spawn_npc_group(self, center_pos, count=8, spread=100):
        """Spawnt eine Gruppe von NPCs um eine zentrale Position"""
        for i in range(count):
            # Zufällige Position um den Mittelpunkt
            angle = (i / count) * 2 * math.pi + random.uniform(-0.5, 0.5)
            distance = random.uniform(20, spread)
            
            x = center_pos[0] + math.cos(angle) * distance
            y = center_pos[1] + math.sin(angle) * distance
            
            npc = NPC((x, y), self.world, i)
            self.npcs.add(npc)
            
        print(f"NPCs spawned: {len(self.npcs)} NPCs um Position {center_pos}")
    
    def update(self, dt):
        """Update aller NPCs mit Schwarm-Information"""
        # Jeder NPC bekommt die Liste aller anderen NPCs für Schwarm-Verhalten
        npc_list = list(self.npcs)
        for npc in self.npcs:
            npc.flock_mates = npc_list
            npc.update(dt)
    
    def draw(self, screen, camera):
        """Zeichne alle NPCs"""
        for npc in self.npcs:
            screen_pos = camera.world_to_screen(npc.rect.topleft)
            screen.blit(npc.image, screen_pos)
