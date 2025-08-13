"""
Intelligentes 2D NPC System mit echten Charaktersprites
Verwendet Player-Sprites und verbessertes Schwarmverhalten
"""

import pygame
import math
import random
import os
from settings import TILE_SIZE


def load_player_sprites():
    """Lade Player-Sprites für NPCs"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    sprite_path = os.path.join(base_dir, 'assets', 'Player', 'character-grid-sprite.png')
    
    if not os.path.exists(sprite_path):
        return None
    
    try:
        sheet = pygame.image.load(sprite_path).convert_alpha()
        w, h = sheet.get_size()
        
        # character-grid-sprite.png ist 192x320 = 6x10 Tiles von 32x32
        sprites = {}
        directions = ['down', 'left', 'right', 'up']
        
        for row, direction in enumerate(directions):
            sprites[direction] = []
            for col in range(6):  # 6 Frames pro Richtung
                x = col * 32
                y = row * 32
                sprite = pygame.Surface((32, 32), pygame.SRCALPHA)
                sprite.blit(sheet, (0, 0), (x, y, 32, 32))
                sprites[direction].append(sprite)
        
        print(f"✅ Player-Sprites geladen: {w}x{h}")
        return sprites
    except Exception as e:
        print(f"❌ Fehler beim Laden der Player-Sprites: {e}")
        return None


class NPC2D:
    """Intelligenter 2D-NPC mit echten Charaktersprites"""
    
    def __init__(self, pos, world=None, npc_id=0, sprites=None):
        self.world = world
        self.npc_id = npc_id
        self.position = pygame.Vector2(pos[0], pos[1])
        self.velocity = pygame.Vector2(0, 0)
        self.direction = 'down'
        
        # Animation
        self.sprites = sprites if sprites else {}
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.15  # Frames pro Sekunde
        
        # Bewegungs-AI (verbessert)
        self.speed = random.uniform(40, 80)
        self.max_speed = random.uniform(60, 100)
        self.target_pos = None
        self.arrive_threshold = random.uniform(5, 15)
        self.wander_timer = 0.0
        self.wander_delay = random.uniform(1.0, 4.0)
        self.home_area = pygame.Vector2(pos[0], pos[1])
        self.wander_radius = random.uniform(80, 150)
        
        # Intelligentes Schwarm-Verhalten
        self.separation_distance = random.uniform(25, 45)
        self.alignment_distance = random.uniform(50, 80)
        self.cohesion_distance = random.uniform(70, 120)
        self.neighbor_radius = 100
        
        # Persönlichkeits-Eigenschaften
        self.aggression = random.uniform(0.3, 1.5)  # Wie stark Separation
        self.sociability = random.uniform(0.5, 1.2)  # Wie stark Cohesion
        self.conformity = random.uniform(0.6, 1.1)   # Wie stark Alignment
        self.wanderlust = random.uniform(0.2, 0.8)   # Wie stark Wander
        
        # Farb-Variation für Unterscheidung
        self.color_tint = (
            random.randint(200, 255),
            random.randint(200, 255),
            random.randint(200, 255)
        )
        
        # Leadership & Following
        self.is_leader = random.random() < 0.15  # 15% Chance für Leadership
        self.follow_target = None
        self.leadership_strength = random.uniform(0.8, 1.5) if self.is_leader else random.uniform(0.2, 0.7)
        
        # Obstacle avoidance
        self.vision_distance = 60
        self.avoidance_strength = 2.0
        
        print(f"🎯 NPC{npc_id}: Leader={self.is_leader}, Aggro={self.aggression:.1f}, Social={self.sociability:.1f}")
    
    def update(self, dt, other_npcs):
        """Intelligente NPC-Update mit verbessertem Schwarmverhalten"""
        self.wander_timer += dt
        self.anim_timer += dt
        
        # Animation-Update
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0.0
            if self.velocity.length() > 1.0:  # Nur animieren wenn bewegend
                self.anim_frame = (self.anim_frame + 1) % 6
        
        # Intelligente Schwarm-Kräfte
        separation = self._calculate_separation(other_npcs) * self.aggression
        alignment = self._calculate_alignment(other_npcs) * self.conformity
        cohesion = self._calculate_cohesion(other_npcs) * self.sociability
        
        # Leadership/Following-Verhalten
        leadership = self._calculate_leadership(other_npcs)
        
        # Obstacle avoidance (falls Welt vorhanden)
        avoidance = self._calculate_avoidance()
        
        # Wander-Verhalten
        wander = self._calculate_intelligent_wander() * self.wanderlust
        
        # Kombiniere Kräfte intelligent
        total_force = pygame.Vector2(0, 0)
        
        # Prioritäten-System
        if avoidance.length() > 0.1:
            total_force += avoidance * 3.0  # Hindernisse haben höchste Priorität
        
        if separation.length() > 0.1:
            total_force += separation * 2.0  # Dann Separation
        
        total_force += alignment * 1.0
        total_force += cohesion * 1.2
        total_force += leadership * 1.5
        total_force += wander * 0.6
        
        # Smooth steering
        desired_velocity = self.velocity + total_force * dt
        
        # Speed limiting mit Persönlichkeit
        max_speed_current = self.max_speed
        if self.is_leader:
            max_speed_current *= 0.9  # Leader sind etwas langsamer
        
        if desired_velocity.length() > max_speed_current:
            desired_velocity.scale_to_length(max_speed_current)
        
        # 🚀 SMOOTH: Improved velocity interpolation for smoother movement
        lerp_factor = min(0.15, 8.0 * dt)  # Adaptive lerp based on frame time
        self.velocity = self.velocity.lerp(desired_velocity, lerp_factor)
        
        # 🚀 SMOOTH: Position update with floating-point precision
        new_position = self.position + self.velocity * dt
        
        # 🚀 PERFORMANCE: Only update rect when position changes significantly
        if abs(new_position.x - self.position.x) > 0.1 or abs(new_position.y - self.position.y) > 0.1:
            self.position = new_position
        else:
            # Prevent micro-jittering
            self.velocity *= 0.95
        
        # Richtung für Sprite
        self._update_direction()
    
    def _calculate_separation(self, other_npcs):
        """Verbesserte Separation mit Gewichtung"""
        force = pygame.Vector2(0, 0)
        count = 0
        
        for other in other_npcs:
            if other != self:
                distance = self.position.distance_to(other.position)
                if 0 < distance < self.separation_distance:
                    diff = self.position - other.position
                    if diff.length() > 0:
                        diff = diff.normalize()
                        # Gewichtung: näher = stärker
                        weight = (self.separation_distance - distance) / self.separation_distance
                        diff *= weight * weight  # Quadratische Gewichtung
                        force += diff
                        count += 1
        
        if count > 0:
            force = force.normalize() if force.length() > 0 else pygame.Vector2(0, 0)
        
        return force
    
    def _calculate_alignment(self, other_npcs):
        """Verbesserte Alignment mit Nachbarschaftsfilter"""
        avg_velocity = pygame.Vector2(0, 0)
        count = 0
        
        for other in other_npcs:
            if other != self:
                distance = self.position.distance_to(other.position)
                if distance < self.alignment_distance:
                    # Gewichte basierend auf Leadership
                    weight = other.leadership_strength if hasattr(other, 'leadership_strength') else 1.0
                    avg_velocity += other.velocity * weight
                    count += 1
        
        if count > 0:
            avg_velocity /= count
            if avg_velocity.length() > 0:
                avg_velocity.scale_to_length(self.max_speed * 0.8)
            force = avg_velocity - self.velocity
            return force * 0.5  # Moderatere Alignment
        
        return pygame.Vector2(0, 0)
    
    def _calculate_cohesion(self, other_npcs):
        """Verbesserte Cohesion mit Gruppen-Erkennung"""
        center = pygame.Vector2(0, 0)
        count = 0
        
        # Filtere Nachbarn im Sichtbereich
        neighbors = []
        for other in other_npcs:
            if other != self:
                distance = self.position.distance_to(other.position)
                if distance < self.cohesion_distance:
                    neighbors.append(other)
        
        if not neighbors:
            return pygame.Vector2(0, 0)
        
        # Berechne gewichtetes Zentrum
        for other in neighbors:
            weight = other.leadership_strength if hasattr(other, 'leadership_strength') else 1.0
            center += other.position * weight
            count += weight
        
        if count > 0:
            center /= count
            desired = center - self.position
            
            # Nur bewegen wenn Gruppe groß genug
            if len(neighbors) >= 2:
                distance = desired.length()
                if distance > self.arrive_threshold:
                    if distance > 0:
                        desired = desired.normalize() * self.max_speed * 0.6
                    force = desired - self.velocity
                    return force * 0.4
        
        return pygame.Vector2(0, 0)
    
    def _calculate_leadership(self, other_npcs):
        """Leadership/Following Verhalten"""
        force = pygame.Vector2(0, 0)
        
        if self.is_leader:
            # Leaders führen die Gruppe zu interessanten Stellen
            if random.random() < 0.01:  # 1% Chance pro Frame für neue Richtung
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(100, 200)
                new_target = self.home_area + pygame.Vector2(
                    math.cos(angle) * distance,
                    math.sin(angle) * distance
                )
                self.target_pos = new_target
            
            if self.target_pos:
                desired = self.target_pos - self.position
                if desired.length() > 20:
                    force = desired.normalize() * 0.3
        else:
            # Followers suchen Leader
            leader = None
            min_distance = float('inf')
            
            for other in other_npcs:
                if hasattr(other, 'is_leader') and other.is_leader:
                    distance = self.position.distance_to(other.position)
                    if distance < min_distance and distance < 150:
                        min_distance = distance
                        leader = other
            
            if leader:
                self.follow_target = leader
                desired = leader.position - self.position
                if desired.length() > 40:  # Folge nur wenn weit genug weg
                    force = desired.normalize() * 0.4
        
        return force
    
    def _calculate_avoidance(self):
        """Hindernissvermeidung (falls Welt vorhanden)"""
        if not self.world:
            return pygame.Vector2(0, 0)
        
        # Vereinfachte Hindernissvermeidung - prüfe Tiles vor NPC
        force = pygame.Vector2(0, 0)
        
        # Prüfe mehrere Punkte vor dem NPC
        look_ahead = self.velocity.normalize() * self.vision_distance if self.velocity.length() > 0 else pygame.Vector2(1, 0)
        
        for i in range(3):
            angle_offset = (i - 1) * 0.5  # -0.5, 0, 0.5 Radians
            rotated = look_ahead.rotate(math.degrees(angle_offset))
            check_pos = self.position + rotated
            
            # Konvertiere zu Tile-Koordinaten
            tile_x = int(check_pos.x // TILE_SIZE)
            tile_y = int(check_pos.y // TILE_SIZE)
            
            # Prüfe ob Tile blockiert (vereinfacht)
            if (tile_x < 0 or tile_y < 0 or 
                tile_x >= self.world.area_width_tiles or 
                tile_y >= self.world.area_height_tiles):
                # Rand der Welt erreicht
                avoidance_dir = self.position - check_pos
                if avoidance_dir.length() > 0:
                    force += avoidance_dir.normalize() * 2.0
        
        return force
    
    def _calculate_intelligent_wander(self):
        """Intelligenteres Wanderverhalten"""
        if self.wander_timer > self.wander_delay:
            self.wander_timer = 0
            self.wander_delay = random.uniform(2.0, 6.0)
            
            # Leaders wandern weiter, Followers bleiben näher
            wander_distance = self.wander_radius * (1.5 if self.is_leader else 0.8)
            
            # Bevorzuge Richtungen weg von der Gruppe wenn überfüllt
            group_center = self._get_group_center([])
            if group_center:
                away_from_group = self.position - group_center
                if away_from_group.length() > 0:
                    # Mische Wander-Richtung mit "weg von Gruppe"
                    random_angle = random.uniform(0, 2 * math.pi)
                    away_angle = math.atan2(away_from_group.y, away_from_group.x)
                    
                    # Gewichte: 70% random, 30% weg von Gruppe
                    final_angle = random_angle * 0.7 + away_angle * 0.3
                    
                    self.target_pos = self.home_area + pygame.Vector2(
                        math.cos(final_angle) * wander_distance,
                        math.sin(final_angle) * wander_distance
                    )
        
        # Bewege zu Wander-Ziel
        if self.target_pos:
            desired = self.target_pos - self.position
            distance = desired.length()
            
            if distance > self.arrive_threshold:
                if distance > 0:
                    # Arrival behavior - langsamer werden nahe am Ziel
                    speed = min(self.max_speed, distance / 50.0 * self.max_speed)
                    desired = desired.normalize() * speed
                force = desired - self.velocity
                return force * 0.3
            else:
                self.target_pos = None
        
        return pygame.Vector2(0, 0)
    
    def _get_group_center(self, other_npcs):
        """Berechne Gruppen-Zentrum"""
        if not other_npcs:
            return None
        
        center = pygame.Vector2(0, 0)
        count = 0
        
        for other in other_npcs:
            if self.position.distance_to(other.position) < self.neighbor_radius:
                center += other.position
                count += 1
        
        return center / count if count > 0 else None
    
    def _update_direction(self):
        """Update Sprite-Richtung basierend auf Bewegung"""
        if self.velocity.length() > 1.0:
            angle = math.atan2(self.velocity.y, self.velocity.x)
            angle_deg = math.degrees(angle)
            
            # Konvertiere Winkel zu Richtung
            if -45 <= angle_deg < 45:
                self.direction = 'right'
            elif 45 <= angle_deg < 135:
                self.direction = 'down'
            elif 135 <= angle_deg or angle_deg < -135:
                self.direction = 'left'
            else:
                self.direction = 'up'
    
    def get_current_sprite(self):
        """Hole aktuellen Sprite basierend auf Richtung und Animation"""
        if not self.sprites or self.direction not in self.sprites:
            # Fallback: einfacher Kreis
            size = 32
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surface, self.color_tint, (size//2, size//2), size//3)
            return surface
        
        sprites_for_direction = self.sprites[self.direction]
        if not sprites_for_direction:
            return self.get_fallback_sprite()
        
        # Hole Frame (falls bewegend) oder ersten Frame (falls still)
        if self.velocity.length() > 1.0:
            sprite = sprites_for_direction[self.anim_frame % len(sprites_for_direction)]
        else:
            sprite = sprites_for_direction[0]  # Idle frame
        
        # Wende Farbtönung an
        tinted_sprite = sprite.copy()
        tinted_sprite.fill(self.color_tint, special_flags=pygame.BLEND_MULT)
        
        return tinted_sprite
    
    def get_fallback_sprite(self):
        """Fallback wenn keine Sprites verfügbar"""
        size = 32
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surface, self.color_tint, (size//2, size//2), size//3)
        pygame.draw.circle(surface, (0, 0, 0), (size//2, size//2), size//3, 2)
        return surface


class NPCSystem2D:
    """Verwaltung aller 2D-NPCs mit intelligenter Verteilung"""
    
    def __init__(self, world=None):
        self.world = world
        self.npcs = []
        self.sprites_loaded = False
        self.player_sprites = None
        
        # Performance-Optimierung
        self.update_groups = []  # NPCs in Gruppen für effizientere Updates
        self.group_size = 4  # 4 NPCs pro Update-Gruppe
        self.current_group = 0
        
        # Intelligente Spawn-Parameter
        self.max_npcs = 8
        self.min_group_size = 3
        self.max_group_size = 6
        self.spawn_radius = 200
        
        # Lade Player-Sprites einmalig
        self._load_sprites()
    
    def _load_sprites(self):
        """Lade Player-Sprites für alle NPCs"""
        self.player_sprites = load_player_sprites()
        if self.player_sprites:
            self.sprites_loaded = True
            print("✅ NPC-System: Player-Sprites erfolgreich geladen")
        else:
            print("⚠️ NPC-System: Fallback auf einfache Kreise")
    
    def spawn_intelligent_swarm(self, near_pos, count=None):
        """Spawne intelligente Schwarm-Gruppen"""
        if count is None:
            count = self.max_npcs
        
        print(f"🎯 Spawne intelligenten Schwarm: {count} NPCs nahe {near_pos}")
        
        # Lösche alte NPCs
        self.npcs.clear()
        
        # Erstelle Gruppen
        groups_needed = max(1, count // self.max_group_size)
        npcs_per_group = count // groups_needed
        
        for group_id in range(groups_needed):
            group_center = pygame.Vector2(
                near_pos[0] + random.uniform(-100, 100),
                near_pos[1] + random.uniform(-100, 100)
            )
            
            # Spawne NPCs in dieser Gruppe
            group_npcs = min(npcs_per_group, count - len(self.npcs))
            if group_id == groups_needed - 1:  # Letzte Gruppe bekommt Rest
                group_npcs = count - len(self.npcs)
            
            for i in range(group_npcs):
                # Position innerhalb der Gruppe
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(10, 40)
                
                spawn_pos = (
                    group_center.x + math.cos(angle) * distance,
                    group_center.y + math.sin(angle) * distance
                )
                
                npc = NPC2D(
                    pos=spawn_pos,
                    world=self.world,
                    npc_id=len(self.npcs),
                    sprites=self.player_sprites
                )
                
                self.npcs.append(npc)
                print(f"  👤 NPC{npc.npc_id}: Pos=({spawn_pos[0]:.0f},{spawn_pos[1]:.0f}), Leader={npc.is_leader}")
        
        # Organisiere Update-Gruppen für Performance
        self._organize_update_groups()
        
        print(f"✅ Schwarm gespawnt: {len(self.npcs)} NPCs in {groups_needed} Gruppen")
    
    def _organize_update_groups(self):
        """Organisiere NPCs in Update-Gruppen für bessere Performance"""
        self.update_groups = []
        for i in range(0, len(self.npcs), self.group_size):
            group = self.npcs[i:i + self.group_size]
            self.update_groups.append(group)
    
    def update(self, dt):
        """Update NPCs mit Performance-Optimierung"""
        if not self.npcs:
            return
        
        # Update nur eine Gruppe pro Frame für bessere Performance
        if self.update_groups:
            current_group = self.update_groups[self.current_group]
            
            # Update alle NPCs in dieser Gruppe
            for npc in current_group:
                # Berechne Nachbarn für diesen NPC
                neighbors = self._get_neighbors(npc)
                npc.update(dt, neighbors)
            
            # Nächste Gruppe für nächsten Frame
            self.current_group = (self.current_group + 1) % len(self.update_groups)
        else:
            # Fallback: Update alle
            for npc in self.npcs:
                npc.update(dt, self.npcs)
    
    def _get_neighbors(self, npc):
        """Hole Nachbarn für einen NPC (Performance-optimiert)"""
        neighbors = []
        max_distance = 150  # Maximale Nachbarschafts-Distanz
        
        for other in self.npcs:
            if other != npc:
                distance = npc.position.distance_to(other.position)
                if distance < max_distance:
                    neighbors.append(other)
        
        return neighbors
    
    def render(self, screen, camera):
        """🚀 SMOOTH NPC Rendering: Optimized for smooth movement"""
        if not self.npcs:
            return
        
        # 🚀 PERFORMANCE: Pre-calculate camera values
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        camera_left = camera.camera.left
        camera_top = camera.camera.top
        rendered_count = 0
        
        for npc in self.npcs:
            # 🚀 SMOOTH: Use floating-point positions for smooth rendering
            screen_x = npc.position.x - camera_left
            screen_y = npc.position.y - camera_top
            
            # 🚀 PERFORMANCE: Optimized frustum culling with larger buffer
            if (-64 <= screen_x <= screen_width + 64 and 
                -64 <= screen_y <= screen_height + 64):
                
                # 🚀 SMOOTH: Get sprite and render with optimized positioning
                sprite = npc.get_current_sprite()
                
                if sprite:
                    # 🚀 PERFORMANCE: Avoid rect creation, use direct positioning
                    sprite_w = sprite.get_width()
                    sprite_h = sprite.get_height()
                    render_x = int(screen_x - sprite_w // 2)
                    render_y = int(screen_y - sprite_h // 2)
                    
                    # Render sprite with integer positions for crisp pixels
                    screen.blit(sprite, (render_x, render_y))
                    rendered_count += 1
                
                    # Debug-Info für Leader - optimized rendering
                    if hasattr(npc, 'is_leader') and npc.is_leader:
                        # 🚀 PERFORMANCE: Simplified crown rendering
                        crown_x = int(screen_x - 5)
                        crown_y = int(screen_y - 25)
                        pygame.draw.circle(screen, (255, 215, 0), (crown_x + 5, crown_y + 4), 6, 2)
        
        # Debug-Info
        if hasattr(self, 'debug_enabled') and self.debug_enabled:
            debug_text = f"NPCs: {len(self.npcs)} (sichtbar: {rendered_count})"
            font = pygame.font.Font(None, 24)
            text_surface = font.render(debug_text, True, (255, 255, 255))
            screen.blit(text_surface, (10, 150))
    
    def get_stats(self):
        """Hole Statistiken über das NPC-System"""
        if not self.npcs:
            return {"count": 0, "leaders": 0, "groups": 0}
        
        leaders = sum(1 for npc in self.npcs if hasattr(npc, 'is_leader') and npc.is_leader)
        
        return {
            "count": len(self.npcs),
            "leaders": leaders,
            "groups": len(self.update_groups),
            "sprites_loaded": self.sprites_loaded
        }
    
    def cleanup(self):
        """Aufräumen"""
        self.npcs.clear()
        self.update_groups.clear()
        print("🧹 NPC-System aufgeräumt")
