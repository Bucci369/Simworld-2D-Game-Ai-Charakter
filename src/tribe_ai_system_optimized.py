"""
Performance-optimierte AI Tribe System
Reduziert CPU-Last durch intelligente Update-Zyklen
"""

import logging
import random
import time
import math
import numpy as np
import pygame

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FastDecisionSystem:
    """Schnelle Entscheidungsfindung ohne TensorFlow für bessere Performance"""
    
    def __init__(self):
        self.action_weights = {
            'idle': 0.3,
            'gathering': 0.2,
            'guard_duty': 0.15,
            'patrol': 0.1,
            'diplomacy': 0.08,
            'trade': 0.05,
            'construction': 0.05,
            'research': 0.03,
            'planning': 0.02,
            'resource_management': 0.02
        }
        
    def get_action(self, personality, world_state, nearby_members):
        """Schnelle Aktionsauswahl basierend auf Regeln"""
        weights = self.action_weights.copy()
        
        # Personality-basierte Anpassungen
        if personality.get('aggressiveness', 0.5) > 0.7:
            weights['guard_duty'] *= 1.5
            weights['patrol'] *= 1.5
            
        if personality.get('curiosity', 0.5) > 0.7:
            weights['research'] *= 1.5
            weights['exploration'] = 0.1
            
        # Situationsbasierte Anpassungen
        if len(nearby_members) > 2:
            weights['diplomacy'] *= 1.3
            
        # Gewichtete Zufallsauswahl
        actions = list(weights.keys())
        action_weights = list(weights.values())
        
        return random.choices(actions, weights=action_weights)[0]

class OptimizedTribeAIMember:
    """Optimierter Tribe Member mit reduzierter Update-Frequenz"""
    
    def __init__(self, member_id, x, y):
        self.member_id = member_id
        self.x = x
        self.y = y
        self.speed = 50
        
        # AI Komponenten
        self.decision_system = FastDecisionSystem()
        self.personality = self._generate_personality()
        
        # Status
        self.current_action = "idle"
        self.last_update = 0
        self.update_interval = random.uniform(0.3, 0.8)  # 300-800ms zwischen Updates
        
        # Bewegung
        self.target_x = x
        self.target_y = y
        self.moving = False
        
        # Performance Tracking
        self.action_history = []
        
        logger.info(f"🤖 Optimized Member {member_id} erstellt bei ({x}, {y})")
        
    def _generate_personality(self):
        """Generiert einfache Persönlichkeit"""
        return {
            'aggressiveness': random.uniform(0.2, 0.8),
            'curiosity': random.uniform(0.2, 0.8),
            'cooperation': random.uniform(0.4, 0.9),
            'activity_level': random.uniform(0.3, 1.0)
        }
    
    def should_update_ai(self, current_time):
        """Prüft ob AI Update nötig ist"""
        return (current_time - self.last_update) > self.update_interval
    
    def update_ai(self, dt, nearby_members, world_state):
        """Optimiertes AI Update mit reduzierter Frequenz"""
        current_time = time.time()
        
        if not self.should_update_ai(current_time):
            return
            
        self.last_update = current_time
        
        # Schnelle Aktionsauswahl
        new_action = self.decision_system.get_action(
            self.personality, world_state, nearby_members
        )
        
        if new_action != self.current_action:
            self.current_action = new_action
            self._set_movement_target()
            logger.info(f"🎯 {self.member_id}: Neue Aktion - {new_action}")
            
        # Action History für Lernen
        self.action_history.append(new_action)
        if len(self.action_history) > 10:
            self.action_history.pop(0)
    
    def _set_movement_target(self):
        """Setzt Bewegungsziel basierend auf Aktion"""
        if self.current_action == "patrol":
            self.target_x = self.x + random.randint(-100, 100)
            self.target_y = self.y + random.randint(-100, 100)
            self.moving = True
        elif self.current_action == "gathering":
            self.target_x = self.x + random.randint(-50, 50)
            self.target_y = self.y + random.randint(-50, 50)
            self.moving = True
        else:
            self.moving = False
    
    def update_movement(self, dt):
        """Aktualisiert Bewegung jeden Frame"""
        if not self.moving:
            return
            
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 5:
            self.x += (dx / distance) * self.speed * dt
            self.y += (dy / distance) * self.speed * dt
        else:
            self.moving = False

class OptimizedTribeAISystem:
    """Hauptsystem mit Performance-Optimierungen"""
    
    def __init__(self, world=None):
        # Wenn SimpleWorld übergeben wird, verwende dessen Dimensionen
        if hasattr(world, 'WORLD_WIDTH') and hasattr(world, 'WORLD_HEIGHT'):
            self.world_width = world.WORLD_WIDTH
            self.world_height = world.WORLD_HEIGHT
        else:
            # Standard-Dimensionen
            self.world_width = 1600
            self.world_height = 1200
        
        self.world = world
        
        # AI Members (reduziert auf 3 für bessere Performance)
        self.members = []
        self._create_initial_members(3)
        
        # World State
        self.world_state = {
            'time_of_day': 0,
            'resources': {'food': 100, 'wood': 50, 'stone': 30},
            'threat_level': 0.0
        }
        
        # Performance Monitoring
        self.update_time = 0
        self.max_update_time = 0
        
        logger.info("🚀 Optimized Tribe AI System initialisiert")
    
    def _create_initial_members(self, count):
        """Erstellt initiale Members in der Nähe des Spawns"""
        # Spawn sie in der Nähe des Player-Spawns (800, 600)
        spawn_x, spawn_y = 800, 600
        for i in range(count):
            # Platziere sie in einem Radius um den Spawn
            angle = (i / count) * 2 * math.pi
            radius = 100 + (i * 30)  # Verschiedene Entfernungen
            x = spawn_x + math.cos(angle) * radius
            y = spawn_y + math.sin(angle) * radius
            member = OptimizedTribeAIMember(f"tribe_member_{i}", x, y)
            self.members.append(member)
    
    def create_tribe(self, spawn_pos, member_count=3):
        """Erstellt einen neuen Stamm (Kompatibilität)"""
        logger.info(f"🏕️ Erstelle Stamm mit {member_count} Mitgliedern bei {spawn_pos}")
        # Für Optimierung: Ignoriere zusätzliche Members, behalte nur die initial erstellten
        pass
    
    def get_nearby_members(self, member, radius=150):
        """Findet nahegelegene Members"""
        nearby = []
        for other in self.members:
            if other != member:
                dx = other.x - member.x
                dy = other.y - member.y
                if math.sqrt(dx*dx + dy*dy) < radius:
                    nearby.append(other)
        return nearby
    
    def update(self, dt):
        """Hauptupdate mit Performance-Monitoring"""
        start_time = time.time()
        
        # World State Update (weniger häufig)
        self._update_world_state(dt)
        
        # Member Updates
        for member in self.members:
            # AI Update (reduzierte Frequenz)
            nearby = self.get_nearby_members(member)
            member.update_ai(dt, nearby, self.world_state)
            
            # Movement Update (jeden Frame)
            member.update_movement(dt)
        
        # Performance Tracking
        self.update_time = time.time() - start_time
        self.max_update_time = max(self.max_update_time, self.update_time)
    
    def _update_world_state(self, dt):
        """Updated World State weniger häufig"""
        self.world_state['time_of_day'] += dt * 0.1
        if self.world_state['time_of_day'] > 24:
            self.world_state['time_of_day'] = 0
    
    def render(self, screen, camera=None):
        """Rendering mit Culling für bessere Performance"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Camera Offset bestimmen
        if camera and hasattr(camera, 'x') and hasattr(camera, 'y'):
            camera_x = camera.x
            camera_y = camera.y
        else:
            camera_x = 0
            camera_y = 0
        
        for member in self.members:
            # Culling - nur rendern wenn sichtbar
            screen_x = member.x - camera_x
            screen_y = member.y - camera_y
            
            if (-50 < screen_x < screen_width + 50 and 
                -50 < screen_y < screen_height + 50):
                
                # Member als größerer Kreis mit Rand
                color = self._get_member_color(member)
                # Äußerer schwarzer Rand
                pygame.draw.circle(screen, (0, 0, 0), 
                                 (int(screen_x), int(screen_y)), 17)
                # Innerer farbiger Kreis
                pygame.draw.circle(screen, color, 
                                 (int(screen_x), int(screen_y)), 15)
                
                # Action Label (immer anzeigen)
                font = pygame.font.Font(None, 20)
                text = font.render(f"{member.member_id}", True, (255, 255, 255))
                text_rect = text.get_rect(center=(screen_x, screen_y - 30))
                # Schwarzer Hintergrund für Text
                pygame.draw.rect(screen, (0, 0, 0), text_rect.inflate(4, 2))
                screen.blit(text, text_rect)
                
                # Action Text
                action_text = font.render(member.current_action, True, (255, 255, 0))
                action_rect = action_text.get_rect(center=(screen_x, screen_y + 25))
                pygame.draw.rect(screen, (0, 0, 0), action_rect.inflate(4, 2))
                screen.blit(action_text, action_rect)
    
    def _get_member_color(self, member):
        """Farbe basierend auf Aktion"""
        action_colors = {
            'idle': (100, 100, 100),
            'gathering': (0, 255, 0),
            'guard_duty': (255, 0, 0),
            'patrol': (255, 255, 0),
            'diplomacy': (0, 0, 255),
            'trade': (255, 0, 255),
            'construction': (165, 42, 42),
            'research': (128, 0, 128),
            'planning': (255, 165, 0),
            'resource_management': (0, 128, 128)
        }
        return action_colors.get(member.current_action, (150, 150, 150))
    
    def render_debug_info(self, screen, font):
        """Debug Info für Performance"""
        debug_lines = [
            f"AI Members: {len(self.members)}",
            f"Update Time: {self.update_time*1000:.1f}ms",
            f"Max Update: {self.max_update_time*1000:.1f}ms",
            "",
            "Actions:",
        ]
        
        # Current Actions
        for member in self.members:
            debug_lines.append(f"  {member.member_id}: {member.current_action}")
        
        y_offset = 10
        for line in debug_lines:
            if line:  # Skip empty lines
                text = font.render(line, True, (255, 255, 255))
                screen.blit(text, (10, y_offset))
            y_offset += 20
    
    def teleport_members_to_player(self, player_x, player_y):
        """Teleportiert alle Members in die Nähe des Players"""
        logger.info(f"🚁 Teleportiere {len(self.members)} Members zu Player bei ({player_x}, {player_y})")
        for i, member in enumerate(self.members):
            # Platziere sie in einem Kreis um den Player
            angle = (i / len(self.members)) * 2 * math.pi
            radius = 80 + (i * 20)  # Verschiedene Entfernungen
            member.x = player_x + math.cos(angle) * radius
            member.y = player_y + math.sin(angle) * radius
            member.target_x = member.x
            member.target_y = member.y
            member.moving = False
    
    def get_stats(self):
        """Statistiken für Debug Panel"""
        action_counts = {}
        for member in self.members:
            action = member.current_action
            action_counts[action] = action_counts.get(action, 0) + 1
            
        return {
            'member_count': len(self.members),
            'update_time_ms': self.update_time * 1000,
            'max_update_ms': self.max_update_time * 1000,
            'actions': action_counts,
            'world_time': f"{self.world_state['time_of_day']:.1f}h",
            'resources': self.world_state['resources']
        }

# Test wenn direkt ausgeführt
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Optimized AI Test")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    
    ai_system = OptimizedTribeAISystem()
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        ai_system.update(dt)
        
        screen.fill((50, 50, 50))
        ai_system.render(screen)
        ai_system.render_debug_info(screen, font)
        
        pygame.display.flip()
    
    pygame.quit()
