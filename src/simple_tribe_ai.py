import pygame
import random
import logging
import math
from enum import Enum
from typing import List, Dict, Any
import time

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NPCState(Enum):
    IDLE = "idle"
    COLLECTING_WOOD = "collecting_wood"
    BUILDING_HOUSE = "building_house"
    FOLLOWING_LEADER = "following_leader"
    RETURNING_TO_STORAGE = "returning_to_storage"

class SpeechBubble:
    def __init__(self, text: str, duration: float = 3.0):
        self.text = text
        self.duration = duration
        self.start_time = time.time()
        self.font = pygame.font.SysFont('Arial', 14)
        
    def is_expired(self) -> bool:
        return time.time() - self.start_time > self.duration
        
    def draw(self, surface, camera, position):
        if self.is_expired():
            return
            
        text_surface = self.font.render(self.text, True, (0, 0, 0))
        background = pygame.Surface((text_surface.get_width() + 10, text_surface.get_height() + 10))
        background.fill((255, 255, 255))
        pygame.draw.rect(background, (0, 0, 0), background.get_rect(), 1)
        
        background.blit(text_surface, (5, 5))
        screen_pos = camera.apply_to_point((position[0] - background.get_width()/2, position[1] - 50))
        surface.blit(background, screen_pos)

class SimpleNPC:
    def __init__(self, npc_id: str, position, tribe_color: str, is_leader: bool = False):
        self.npc_id = npc_id
        self.position = pygame.Vector2(position)
        self.is_leader = is_leader
        self.tribe_color = tribe_color
        self.state = NPCState.IDLE
        self.velocity = pygame.Vector2(0, 0)
        self.max_speed = 60
        self.target_tree = None
        self.carrying_wood = 0
        self.wood_capacity = 5
        self.target_house = None
        self.leader = None
        self.speech_bubble = None
        
        # Erstelle rect für Kollisionserkennung
        self.rect = pygame.Rect(self.position.x, self.position.y, 32, 32)  # 32x32 ist die typische Sprite-Größe

    def update(self, dt: float, world_state: Dict):
        if self.is_leader:
            self._update_leader(dt, world_state)
        else:
            self._update_worker(dt, world_state)
        
        # Bewegung anwenden
        if self.velocity.length() > 0:
            # Normalisiere die Geschwindigkeit
            if self.velocity.length() > self.max_speed:
                self.velocity.scale_to_length(self.max_speed)
            
            # Bewege NPC
            old_pos = pygame.Vector2(self.position)
            self.position += self.velocity * dt
            
            # Debug: Zeige große Positionsänderungen
            if (self.position - old_pos).length() > 10:
                logger.info(f"⚡ {self.npc_id} große Bewegung: {int(old_pos.x)},{int(old_pos.y)} → {int(self.position.x)},{int(self.position.y)}")

    def _update_leader(self, dt: float, world_state: Dict):
        """Leader überprüft Häuser und gibt Aufträge"""
        if not hasattr(self, '_last_check'):
            self._last_check = 0

        # Alle 5 Sekunden prüfen
        if time.time() - self._last_check > 5.0:
            self._last_check = time.time()
            
            # Zähle Häuser und NPCs
            tribe_system = world_state.get('tribe_system')
            if not tribe_system:
                return

            houses = [h for h in world_state['house_system'].houses if h.tribe_color == self.tribe_color]
            npcs = world_state['tribe_system'].tribes[self.tribe_color]
            
            # Prüfe ob Häuser fehlen
            if len(houses) < len(npcs):
                logger.info(f"👑 Leader {self.npc_id}: Haus fehlt! ({len(houses)}/{len(npcs)})")
                # Informiere alle untätigen NPCs
                npcs = tribe_system.tribes[self.tribe_color]
                self.speech_bubble = SpeechBubble("Wir brauchen ein neues Haus!", 4.0)
                for npc in npcs:
                    if not npc.is_leader and npc.state == NPCState.IDLE:
                        npc.state = NPCState.COLLECTING_WOOD
                        npc.speech_bubble = SpeechBubble("Jawohl, ich hole Holz!", 3.0)
                        logger.info(f"📢 {self.npc_id} → {npc.npc_id}: Sammle Holz für neues Haus!")

    def _update_worker(self, dt: float, world_state: Dict):
        """Worker sammelt Holz oder baut Haus"""
        if self.state == NPCState.IDLE:
            self._follow_leader()
            
        elif self.state == NPCState.COLLECTING_WOOD:
            # Prüfe zuerst, ob wir genug Holz haben
            if self.carrying_wood >= self.wood_capacity:
                logger.info(f"🔄 {self.npc_id} wechselt zu RETURNING_TO_STORAGE (Holz: {self.carrying_wood})")
                self.state = NPCState.RETURNING_TO_STORAGE
            else:
                self._collect_wood(world_state)
                
        elif self.state == NPCState.RETURNING_TO_STORAGE:
            self._return_to_storage(world_state)

        elif self.state == NPCState.BUILDING_HOUSE:
            self._build_house(world_state)

        elif self.state == NPCState.FOLLOWING_LEADER:
            self._follow_leader()

    def _collect_wood(self, world_state: Dict):
        """Finde und fälle Bäume"""
        if not self.target_tree:
            # Finde nächsten Baum
            trees = world_state.get('tree_system').trees
            nearest_tree = None
            min_distance = float('inf')
            search_radius = 500  # Erhöhter Suchradius
            
            for tree in trees:
                if tree.alive:
                    dist = pygame.Vector2(tree.x, tree.y).distance_to(self.position)
                    # Prüfe ob der Baum nicht von einem anderen Worker als Ziel hat
                    tree_is_target = False
                    for npc in world_state.get('tribe_system').tribes[self.tribe_color]:
                        if npc != self and npc.target_tree == tree:
                            tree_is_target = True
                            break
                            
                    if dist < min_distance and dist < search_radius and not tree_is_target:
                        min_distance = dist
                        nearest_tree = tree
            
            if nearest_tree:
                self.target_tree = nearest_tree
                self.speech_bubble = SpeechBubble("Dieser Baum sieht gut aus!", 2.0)
                logger.info(f"🌳 {self.npc_id} hat Baum gefunden!")
            else:
                # Wenn kein Baum gefunden wurde, bewege dich vom aktuellen Punkt weg
                logger.info(f"❌ {self.npc_id} sucht neue Bäume...")
                # Zufällige Richtung wählen und ein Stück in diese Richtung gehen
                angle = random.uniform(0, 2 * math.pi)
                new_x = self.position.x + math.cos(angle) * 100
                new_y = self.position.y + math.sin(angle) * 100
                self.velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * self.max_speed
                self.speech_bubble = SpeechBubble("Suche nach Bäumen...", 2.0)
                return

        if self.target_tree:
            dist = pygame.Vector2(self.target_tree.x, self.target_tree.y).distance_to(self.position)
            
            if dist > 40:  # Gehe zum Baum
                direction = (pygame.Vector2(self.target_tree.x, self.target_tree.y) - self.position).normalize()
                self.velocity = direction * self.max_speed
            else:  # Fälle Baum
                self.velocity = pygame.Vector2(0, 0)
                if self.target_tree.take_damage(25):  # Baum wurde gefällt
                    wood_amount = random.randint(3, 5)
                    self.carrying_wood += wood_amount
                    self.speech_bubble = SpeechBubble(f"Habe {wood_amount} Holz gesammelt!", 2.0)
                    logger.info(f"🪓 {self.npc_id} hat {wood_amount} Holz gesammelt!")
                    self.target_tree = None
                    
                    # Wenn genug Holz gesammelt wurde, zum Lager gehen
                    if self.carrying_wood >= self.wood_capacity:
                        logger.info(f"🎒 {self.npc_id} hat genug Holz ({self.carrying_wood}/{self.wood_capacity}), geht zum Lager")
                        self.speech_bubble = SpeechBubble("Genug Holz! Zurück zum Lager!", 2.0)
                        self.state = NPCState.RETURNING_TO_STORAGE

    def _return_to_storage(self, world_state: Dict):
        """Bringe Holz zum Lager"""
        try:
            storage = world_state.get('storage_system').get_storage(self.tribe_color)
            if not storage:
                logger.info(f"❌ {self.npc_id} findet kein Lager!")
                self.state = NPCState.FOLLOWING_LEADER
                return

            storage_pos = pygame.Vector2(storage.position)
            dist = storage_pos.distance_to(self.position)

            if dist > 40:  # Gehe zum Lager
                direction = (storage_pos - self.position).normalize()
                self.velocity = direction * self.max_speed
                if not self.speech_bubble or self.speech_bubble.is_expired():
                    self.speech_bubble = SpeechBubble(f"Bringe {self.carrying_wood} Holz zum Lager", 2.0)
                    logger.info(f"🚶 {self.npc_id} geht zum Lager (Distanz: {int(dist)})")
            else:  # Lagere Holz ein
                self.velocity = pygame.Vector2(0, 0)  # Stoppe Bewegung
                
                # Prüfe aktuelle Holzmenge im Lager
                current_wood = storage.get_resource_amount('wood')
                storage.add_resources('wood', self.carrying_wood)
                self.speech_bubble = SpeechBubble(f"{self.carrying_wood} Holz eingelagert!", 2.0)
                logger.info(f"📦 {self.npc_id} hat {self.carrying_wood} Holz eingelagert!")
                
                # Aktualisiere Zustand
                self.carrying_wood = 0
                
                # Prüfe ob genug Holz für Hausbau da ist
                new_wood = storage.get_resource_amount('wood')
                if new_wood >= 15:  # 15 Holz für ein Haus
                    # Prüfe ob schon ein anderer Worker baut
                    other_building = False
                    for npc in world_state.get('tribe_system').tribes[self.tribe_color]:
                        if npc != self and npc.state == NPCState.BUILDING_HOUSE:
                            other_building = True
                            break
                            
                    if not other_building:
                        self.state = NPCState.BUILDING_HOUSE
                        self.speech_bubble = SpeechBubble("Genug Holz! Fange an zu bauen!", 3.0)
                        logger.info(f"🏗️ {self.npc_id} wechselt zu BUILDING_HOUSE (Holz im Lager: {new_wood})")
                    else:
                        self.state = NPCState.COLLECTING_WOOD
                        self.speech_bubble = SpeechBubble("Andere bauen schon, ich hole mehr Holz!", 2.0)
                else:
                    self.state = NPCState.COLLECTING_WOOD
                    self.speech_bubble = SpeechBubble(f"Brauchen noch mehr Holz! ({new_wood}/15)", 2.0)
        except Exception as e:
            logger.error(f"⚠️ Fehler beim Einlagern von Holz: {e}")
            self.state = NPCState.COLLECTING_WOOD
            self.carrying_wood = 0  # Verhindere Endlosschleife

    def _build_house(self, world_state: Dict):
        """Baue ein Haus wenn genug Ressourcen da sind"""
        if not self.target_house:
            storage = world_state.get('storage_system').get_storage(self.tribe_color)
            if storage and storage.get_resource_amount('wood') >= 15:
                # Erstelle neues Haus
                house = world_state.get('house_system').create_house(self.npc_id, self.tribe_color)
                if house:
                    self.target_house = house
                    storage.remove_resources('wood', 15)
                    self.speech_bubble = SpeechBubble("Beginne mit dem Hausbau!", 3.0)
                    logger.info(f"🏗️ {self.npc_id} beginnt Hausbau!")
                else:
                    logger.info(f"❌ {self.npc_id} konnte kein Haus bauen!")

        if self.target_house:
            house_pos = pygame.Vector2(self.target_house.position)
            dist = house_pos.distance_to(self.position)

            if dist > 40:  # Gehe zum Bauplatz
                direction = (house_pos - self.position).normalize()
                self.velocity = direction * self.max_speed
            else:  # Baue am Haus
                self.velocity = pygame.Vector2(0, 0)
                self.target_house.build_progress += 0.1
                
                if self.target_house.build_progress >= 100:  # Haus fertig
                    logger.info(f"🏠 {self.npc_id} hat Haus fertiggestellt!")
                    self.target_house = None
                    self.state = NPCState.FOLLOWING_LEADER

    def _follow_leader(self):
        """Folge dem Leader"""
        if not self.leader:
            return

        dist = self.leader.position.distance_to(self.position)
        if dist > 100:  # Zu weit weg
            direction = (self.leader.position - self.position).normalize()
            self.velocity = direction * self.max_speed
        elif dist > 60:  # Mittlere Distanz
            direction = (self.leader.position - self.position).normalize()
            self.velocity = direction * self.max_speed * 0.5
        else:  # Nahe genug
            self.velocity = pygame.Vector2(0, 0)

class SimpleTribeSystem:
    def __init__(self):
        self.tribes = {}  # Color -> [NPCs]
        
    def create_tribe(self, color: str, leader_pos, num_workers: int = 2):
        """Erstelle einen neuen Stamm mit Leader und Workers"""
        # Erstelle Lager in der Nähe des Leaders
        storage_pos = (leader_pos[0] + random.randint(-100, -50), 
                      leader_pos[1] + random.randint(-100, -50))
                      
        leader = SimpleNPC(f"leader_{color}", leader_pos, color, is_leader=True)
        workers = [
            SimpleNPC(f"worker_{color}_{i}", 
                     (leader_pos[0] + random.randint(-50, 50),
                      leader_pos[1] + random.randint(-50, 50)),
                     color)
            for i in range(num_workers)
        ]
        
        # Setze Leader für Worker
        for worker in workers:
            worker.leader = leader
            
        self.tribes[color] = [leader] + workers
        logger.info(f"🏰 Neuer Stamm erstellt: {color} mit {num_workers} Arbeitern")
        
    def update(self, dt: float, world_state: Dict):
        """Update alle NPCs in allen Stämmen"""
        for tribe_color, npcs in self.tribes.items():
            for npc in npcs:
                npc.update(dt, world_state)
