import pygame
import random
import logging
import math
import time
from enum import Enum
from typing import List, Dict, Any
from ai_leader import AILeader, Task, TaskType, Priority

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NPCState(Enum):
    IDLE = "idle"
    COLLECTING_WOOD = "collecting_wood"
    BUILDING_HOUSE = "building_house"
    FOLLOWING_LEADER = "following_leader"
    RETURNING_TO_STORAGE = "returning_to_storage"
    GATHERING_FOOD = "gathering_food"
    DEFENDING = "defending"
    EXPLORING = "exploring"
    CRAFTING = "crafting"
    FARMING = "farming"
    HUNTING = "hunting"

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
    def __init__(self, npc_id: str, position, tribe_color: str, is_leader: bool = False, sprite_manager=None):
        self.npc_id = npc_id
        self.position = pygame.Vector2(position)
        self.is_leader = is_leader
        self.tribe_color = tribe_color
        self.state = NPCState.IDLE
        self.velocity = pygame.Vector2(0, 0)
        self.max_speed = 60
        self.target_tree = None
        # 🪵 NEUE BALANCE: Max 5 Holz tragen (ein Baum = ein Trip)
        self.carrying_wood = 0
        self.max_wood_capacity = 5  # Maximal 5 Holz tragen
        
        # Sprite Management
        self.sprite_manager = sprite_manager
        # Wähle Character Index basierend auf Rolle
        if self.is_leader:
            self.character_index = 0  # Leader bekommen den ersten Charakter (roten Teufel)
        else:
            self.character_index = random.randint(1, 10)  # Workers bekommen zufällige andere Charaktere
        
        logger.info(f"🎮 {self.npc_id} ({'Leader' if is_leader else 'Worker'}) verwendet Charakter {self.character_index}")
        
        self.wood_capacity = 5  # Gleich wie max_wood_capacity
        self.target_house = None
        self.leader = None
        self.speech_bubble = None
        self.current_order = None  # Speichert den aktuellen Befehl vom Leader
        self._last_check = 0       # Für Leader: Zeitpunkt der letzten Befehlsausgabe
        self.assigned_task = None  # Zugewiesene Task vom KI-Leader
        self.skill_level = random.uniform(0.8, 1.2)  # Individuelle Fähigkeiten
        self.experience = 0        # Erfahrungspunkte
        
        # Speech Bubble Spam Reduktion
        self._last_speech_time = 0.0  # Zeitpunkt der letzten Nachricht
        self._speech_cooldown = 5.0   # Mindestens 5 Sekunden zwischen Nachrichten
        
        # 🔨 NEUE FEATURES: Bauanimation
        self.is_building = False   # Aktuell am Bauen
        self.build_animation_timer = 0.0  # Timer für Bauanimation
        self.build_swing_direction = 1  # 1 oder -1 für Hammer-Schwung
        
        # 🪓 NEUE FEATURES: Realistisches Baumfällen
        self.chop_cooldown = 0.0   # Timer für Baumschläge (alle 2 Sekunden)
        self.max_chop_cooldown = 2.0  # 2 Sekunden zwischen Schlägen
        
        # Anführer - Befehlsverarbeitung
        if is_leader:
            self.player_commands = []  # Liste der Spieler-Befehle
            self.active_orders = []    # Aktive Befehle die ausgeführt werden
            self.command_responses = []  # Antworten an den Spieler
        
        # Anführer hat eine "Home Base" Position
        if is_leader:
            self.home_base = pygame.Vector2(position)  # Ursprungsposition als Home Base
        
        # Erstelle rect für Kollisionserkennung - passend zur Sprite-Größe
        self.rect = pygame.Rect(self.position.x, self.position.y, 32, 32)  # 32x32 passend zur Sprite-Größe

    def _can_show_speech_bubble(self) -> bool:
        """Prüft ob eine neue Speech Bubble angezeigt werden darf (Spam-Schutz)"""
        current_time = time.time()
        if current_time - self._last_speech_time < self._speech_cooldown:
            return False
        return True
    
    def _set_speech_bubble(self, text: str, duration: float = 3.0, priority: bool = False):
        """Setzt eine Speech Bubble mit Spam-Schutz"""
        if priority or self._can_show_speech_bubble():
            self.speech_bubble = SpeechBubble(text, duration)
            self._last_speech_time = time.time()

    def _random_tree_anecdote(self):
        """Zufällige lustige Anekdoten über Bäume und Baumstümpfe"""
        anecdotes = [
            "Ich hasse diese Baumstümpfe!",
            "Ufff noch nen Baum, ernsthaft?",
            "Wer hat hier alle Bäume gepflanzt?",
            "Diese Baumstümpfe nerven total!",
            "Kann mal jemand die Bäume wegräumen?",
            "Schon wieder über nen Stumpf gestolpert...",
            "Noch ein Baum im Weg... super!",
            "Baumstümpfe sollten illegal sein!",
            "Holz ist ja schön, aber muss es Sooo viel sein?",
            "Langsam bekomme ich Allergie gegen Bäume...",
            "Die Bäume haben sich wohl verschworen!",
            "Ich schwöre, diese Bäume beobachten mich!",
            ""
        ]
        
        # Nur anzeigen wenn noch keine Speech Bubble aktiv ist
        if not self.speech_bubble or self.speech_bubble.is_expired():
            random_anecdote = random.choice(anecdotes)
            self._set_speech_bubble(random_anecdote, 4.0)  # 4 Sekunden anzeigen

    def update(self, dt: float, world_state: Dict):
        if self.is_leader:
            self._update_leader(dt, world_state)
        else:
            self._update_worker(dt, world_state)
        
        # 🔨 Update Bauanimation
        if self.is_building:
            self.build_animation_timer += dt
            if self.build_animation_timer >= 0.5:  # Alle 0.5 Sekunden Hammer-Schwung
                self.build_animation_timer = 0.0
                self.build_swing_direction *= -1  # Richtung wechseln
        
        # 🪓 Update Baum-Schlag Cooldown
        if self.chop_cooldown > 0:
            self.chop_cooldown -= dt
        
        # Bewegung anwenden
        if self.velocity.length() > 0:
            # Normalisiere die Geschwindigkeit
            if self.velocity.length() > self.max_speed:
                self.velocity.scale_to_length(self.max_speed)
            
            # Bewege NPC
            old_pos = pygame.Vector2(self.position)
            self.position += self.velocity * dt
            
            # Aktualisiere rect Position
            self.rect.center = (self.position.x, self.position.y)
            
            # Debug: Zeige große Positionsänderungen
            if (self.position - old_pos).length() > 10:
                logger.info(f"⚡ {self.npc_id} große Bewegung: {int(old_pos.x)},{int(old_pos.y)} → {int(self.position.x)},{int(self.position.y)}")

    def draw(self, surface, camera):
        sprite_drawn = False
        
        try:
            # Versuche Sprite zu zeichnen
            if hasattr(self, 'sprite_manager') and hasattr(self, 'character_index') and self.sprite_manager:
                try:
                    is_moving = self.velocity.length() > 0.1
                    # Verwende dt für Animation nur wenn sich bewegend
                    dt = 0.016 if is_moving else 0  # 16ms für 60fps, 0 für stillstehend
                    current_frame = self.sprite_manager.get_frame(self.character_index, dt)
                    
                    if current_frame:
                        # Berechne die Bildschirmposition
                        screen_pos = camera.apply_to_point((
                            self.position.x - current_frame.get_width() // 2,
                            self.position.y - current_frame.get_height() // 2
                        ))
                        
                        # 🔨 BAUANIMATION: Modifiziere Sprite bei Bauarbeit
                        if self.is_building:
                            # Kopiere Frame für Modifikation
                            build_frame = current_frame.copy()
                            
                            # Leichte Bewegung während dem Bauen
                            offset_x = self.build_swing_direction * 2
                            offset_y = int(math.sin(self.build_animation_timer * 10) * 2)
                            
                            # Zeichne modifizierten Frame
                            surface.blit(build_frame, (screen_pos[0] + offset_x, screen_pos[1] + offset_y))
                            
                            # Zeichne Hammer-Symbol über NPC
                            hammer_x = screen_pos[0] + 20 + offset_x
                            hammer_y = screen_pos[1] - 10 + offset_y
                            pygame.draw.circle(surface, (139, 69, 19), (hammer_x, hammer_y), 3)  # Hammer-Kopf
                            pygame.draw.line(surface, (101, 67, 33), (hammer_x, hammer_y), (hammer_x-5, hammer_y+8), 2)  # Hammer-Stiel
                        else:
                            # Normale Sprite-Darstellung
                            # Spiegele das Sprite basierend auf der Bewegungsrichtung
                            if self.velocity.x < 0:  # Bewegt sich nach links
                                current_frame = pygame.transform.flip(current_frame, True, False)
                            
                            # Zeichne den Charakter
                            surface.blit(current_frame, screen_pos)
                        
                        sprite_drawn = True  # Erfolgreich gezeichnet
                        
                        # Debug-Logging (nur gelegentlich)
                        if random.random() < 0.01:  # 1% der Zeit
                            logger.info(f"✅ {self.npc_id} Sprite erfolgreich gezeichnet - Char: {self.character_index}, Pos: {screen_pos}")
                        
                    else:
                        logger.error(f"❌ Kein Frame erhalten für {self.npc_id} (Char: {self.character_index})")
                        
                except Exception as e:
                    logger.error(f"❌ Fehler beim Laden des Frames für {self.npc_id}: {str(e)}")
            else:
                # Debug-Info warum Sprite nicht gezeichnet wird
                reasons = []
                if not hasattr(self, 'sprite_manager'):
                    reasons.append("kein sprite_manager")
                elif not self.sprite_manager:
                    reasons.append("sprite_manager ist None")
                if not hasattr(self, 'character_index'):
                    reasons.append("kein character_index")
                logger.error(f"❌ {self.npc_id} kann Sprite nicht zeichnen: {', '.join(reasons)}")
                    
        except Exception as e:
            logger.error(f"❌ Fataler Zeichenfehler für {self.npc_id}: {str(e)}")
        
        # Nur Fallback zeichnen wenn Sprite NICHT erfolgreich gezeichnet wurde
        if not sprite_drawn:
            try:
                screen_pos = camera.apply_to_point(self.position)
                color = (255, 50, 50) if self.is_leader else (255, 0, 0) 
                pygame.draw.rect(surface, color, (screen_pos[0] - 15, screen_pos[1] - 15, 30, 30))
                if random.random() < 0.02:  # 2% der Zeit
                    logger.warning(f"⚠️ Verwende Fallback-Rendering für {self.npc_id}")
            except Exception as e:
                logger.error(f"❌ Fallback-Zeichenfehler für {self.npc_id}: {str(e)}")
        
        # Zeichne Sprechblase falls vorhanden
        try:
            if self.speech_bubble:
                if not self.speech_bubble.is_expired():
                    self.speech_bubble.draw(surface, camera, self.position)
                else:
                    # Bereinige abgelaufene Speech Bubbles (Memory Leak Fix)
                    self.speech_bubble = None
        except Exception as e:
            logger.error(f"❌ Sprechblase-Zeichenfehler für {self.npc_id}: {str(e)}")

    def _update_leader(self, dt: float, world_state: Dict):
        """Leader überprüft Häuser, gibt Aufträge UND baut sein eigenes Haus"""
        
        # ZUERST: Leader prüft seinen eigenen Hausstatus
        my_house = world_state.get('house_system').get_house(self.npc_id)
        
        # Debug: Log Leader house status
        if random.random() < 0.1:  # Regelmäßiges Logging
            if my_house:
                logger.info(f"👑 Leader {self.npc_id}: Mein Haus - Built: {my_house.built}, Progress: {my_house.build_progress:.0%}, State: {self.state.value}")
            else:
                logger.info(f"👑 Leader {self.npc_id}: Kein Haus vorhanden, State: {self.state.value}")
        
        # Leader baut auch sein eigenes Haus wenn nötig!
        if not my_house or not my_house.built:
            # Leader braucht auch ein Haus!
            if not my_house and self.carrying_wood < 5:
                # Als Anführer: Nehme Holz aus dem Lager statt selbst zu sammeln
                storage = world_state.get('storage_system', {}).get_storage(self.tribe_color)
                if storage and storage.get_resource_amount('wood') >= 5:
                    # Nehme Holz aus dem Lager
                    storage.remove_resources('wood', 5)
                    self.carrying_wood += 5
                    logger.info(f"👑 {self.npc_id} nimmt 5 Holz aus dem Lager für eigenes Haus!")
                    self._set_speech_bubble("Holz aus dem Lager geholt!", 3.0)
                else:
                    # Kein Holz im Lager - beauftrage Arbeiter
                    npcs = world_state['tribe_system'].tribes[self.tribe_color]
                    idle_workers = [npc for npc in npcs if not npc.is_leader 
                                   and npc.state == NPCState.FOLLOWING_LEADER]
                    if idle_workers:
                        worker = idle_workers[0]
                        worker.state = NPCState.COLLECTING_WOOD
                        worker._set_speech_bubble("Hole Holz für den Anführer!", 3.0)
                        logger.info(f"👑 {self.npc_id} beauftragt {worker.npc_id} Holz zu sammeln")
                    
                    # Anführer bleibt am Ort und wartet
                    self.velocity = pygame.Vector2(0, 0)
                    if random.random() < 0.1:
                        self._set_speech_bubble("Warte auf Holz...", 2.0)
                return
            elif not my_house and self.carrying_wood >= 5:
                # Ich habe genug Holz - baue mein Haus
                self.state = NPCState.BUILDING_HOUSE
                logger.info(f"👑 {self.npc_id} baut jetzt sein eigenes Haus!")
                self._build_house(world_state)
                return
            elif my_house and not my_house.built:
                # Ich habe ein Haus, aber es ist nicht fertig
                self.state = NPCState.BUILDING_HOUSE
                logger.info(f"👑 {self.npc_id} beendet Bau seines Hauses! (Progress: {my_house.build_progress:.0%})")
                self._build_house(world_state)
                return
        else:
            # Mein Haus ist fertig - sicherstellen dass ich IDLE bin wenn nichts anderes zu tun
            if self.state == NPCState.BUILDING_HOUSE:
                logger.info(f"✅ Leader {self.npc_id}: Haus fertig - wechsle zu IDLE")
                self.state = NPCState.IDLE
                self.target_house = None
        if not hasattr(self, '_last_check'):
            self._last_check = 0

        # DANN: Verarbeite Spieler-Befehle
        self._process_player_commands(world_state)
        
        # DANN: Management und gelegentlich auf Gespräche antworten
        if not hasattr(self, '_last_social_response'):
            self._last_social_response = 0
            
        # Prüfe ob Arbeiter in der Nähe sind und antworte gelegentlich
        npcs = world_state['tribe_system'].tribes[self.tribe_color]
        nearby_workers = [npc for npc in npcs if not npc.is_leader and 
                         npc.position.distance_to(self.position) < 100]
        
        if nearby_workers and time.time() - self._last_social_response > 5.0:
            if random.random() < 0.3:  # 30% Chance zu antworten (häufiger)
                self._last_social_response = time.time()
                leader_responses = [
                    "Gut gemacht, Arbeiter!",
                    "Das Dorf sieht prächtig aus",
                    "Bald werden wir expandieren",
                    "Ihr habt hart gearbeitet",
                    "Ruht euch aus, ihr habt es verdient",
                    "Überlege neue Pläne für unser Volk...",
                    "Vielleicht brauchen wir mehr Ressourcen",
                    "Das Wetter ist perfekt zum Arbeiten"
                ]
                response = random.choice(leader_responses)
                self.speech_bubble = SpeechBubble(response, 5.0)
                logger.info(f"💬 {self.npc_id} antwortet: '{response}'")

        # SCHLIESSLICH: Kehre zur Home Base zurück wenn nichts zu tun
        if hasattr(self, 'home_base'):
            distance_from_home = self.home_base.distance_to(self.position)
            if distance_from_home > 50:  # Zu weit von Home Base entfernt
                direction = (self.home_base - self.position).normalize()
                self.velocity = direction * self.max_speed * 0.3  # Langsam zurückkehren
                if random.random() < 0.02:
                    self.speech_bubble = SpeechBubble("Kehre zur Basis zurück...", 2.0)
            else:
                # Nahe der Home Base - kleine Patrol-Bewegungen
                if random.random() < 0.01:
                    patrol_dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                    if patrol_dir.length() > 0:
                        patrol_dir = patrol_dir.normalize()
                        self.velocity = patrol_dir * self.max_speed * 0.1

        # Alle 5 Sekunden Management prüfen
        if time.time() - self._last_check > 5.0:
            self._last_check = time.time()
            
            # Zähle Häuser und NPCs
            tribe_system = world_state.get('tribe_system')
            if not tribe_system:
                return

            # Hole ALLE Häuser des Stammes (fertig und im Bau)
            all_tribe_houses = [h for h in world_state['house_system'].houses.values() 
                              if h.tribe_color == self.tribe_color]
            
            # Hole nur die fertigen Häuser
            houses = [h for h in all_tribe_houses if h.built]
            
            # Hole die Häuser im Bau
            houses_under_construction = [h for h in all_tribe_houses 
                                      if h.build_progress > 0 and not h.built]
            
            npcs = world_state['tribe_system'].tribes[self.tribe_color]
            
            logger.info(f"👑 Leader Status - Häuser fertig: {len(houses)}, "
                       f"Im Bau: {len(houses_under_construction)}, "
                       f"Gesamt vorhanden: {len(all_tribe_houses)}, "
                       f"Benötigt: {len(npcs)}")
            
            # Zähle Häuser im Bau (build_progress > 0 aber < 100)
            houses_under_construction = [h for h in world_state['house_system'].houses.values()
                                      if h.tribe_color == self.tribe_color 
                                      and h.build_progress > 0 
                                      and h.build_progress < 100]
            
            # Berechne, wie viele Häuser noch fehlen
            total_needed = len(npcs)
            total_available = len(houses) + len(houses_under_construction)
            missing_houses = total_needed - total_available
            
            logger.info(f"📊 Häuser Status - Fertig: {len(houses)}, "
                       f"Im Bau: {len(houses_under_construction)}, "
                       f"Benötigt: {total_needed}")
            
            # Prüfe ob Häuser fehlen
            if missing_houses > 0:
                logger.info(f"👑 Leader {self.npc_id}: {missing_houses} Häuser fehlen! "
                          f"(Fertig: {len(houses)}, Im Bau: {len(houses_under_construction)}, "
                          f"Benötigt: {total_needed})")
                
                # Informiere alle NPCs über neue Bauaufträge
                for npc in npcs:
                    if not npc.is_leader:
                        # Prüfe ob der NPC gerade baut
                        if npc.state == NPCState.BUILDING_HOUSE:
                            logger.info(f"🏗️ {npc.npc_id} baut gerade, behält aktuelle Aufgabe")
                            continue
                            
                        # Prüfe ob der NPC schon einen BUILD_HOUSE Befehl hat
                        if npc.current_order == "BUILD_HOUSE":
                            logger.info(f"📋 {npc.npc_id} hat bereits einen Baubefehl")
                            continue
                            
                        # Neuen Baubefehl geben
                        npc.current_order = "BUILD_HOUSE"
                        if npc.state != NPCState.COLLECTING_WOOD:
                            npc.state = NPCState.COLLECTING_WOOD
                            npc.speech_bubble = SpeechBubble(f"Baue Haus {len(houses) + 1}/{len(npcs)}!", 3.0)
                            logger.info(f"📢 {self.npc_id} → {npc.npc_id}: Sammle Holz für Haus {len(houses) + 1}!")
                
                self.speech_bubble = SpeechBubble(f"Wir brauchen noch {missing_houses} Häuser!", 4.0)
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
        """Worker sammelt Holz oder baut Haus - EINFACHE LOGIK mit Spieler-Befehlen"""
        # DEAKTIVIERE KI-Tasks - verwende nur einfache Logik
        # if self.assigned_task and not self.assigned_task.completed:
        #     self._execute_assigned_task(dt, world_state)
        #     return
            
        # Verwende IMMER einfache Logik - behandle ALLE States
        # Prüfe zuerst ob grundsätzlich Häuser fehlen
        houses = [h for h in world_state['house_system'].houses.values() 
                 if h.tribe_color == self.tribe_color and h.built]
        npcs = world_state['tribe_system'].tribes[self.tribe_color]
        houses_needed = len(houses) < len(npcs)
        
        # NEUE LOGIK: Prüfe ob Spieler-Befehl aktiv ist
        has_player_command = (hasattr(self, 'current_order') and self.current_order is not None)
        
        # NETZWERK-KOORDINATION: Prüfe was andere Arbeiter tun
        other_workers = [npc for npc in npcs if not npc.is_leader and npc.npc_id != self.npc_id]
        workers_collecting = len([npc for npc in other_workers if npc.state == NPCState.COLLECTING_WOOD])
        workers_building = len([npc for npc in other_workers if npc.state == NPCState.BUILDING_HOUSE])
        
        # Koordinations-Logging für große Gruppen
        if random.random() < 0.02:  # Seltenes Koordinations-Log
            logger.info(f"🤝 {self.npc_id}: Koordination - {workers_collecting} sammeln, {workers_building} bauen, ich: {self.state.value}")
        
        # Debug: Log der Häusersituation mit Koordinationsinfo
        if random.random() < 0.01:  # Seltenes Logging um Spam zu vermeiden
            logger.info(f"📊 {self.npc_id}: Häuser {len(houses)}/{len(npcs)}, Needed: {houses_needed}, State: {self.state.value}, PlayerCmd: {has_player_command}, Team: {workers_collecting}S/{workers_building}B")
        
        if self.state == NPCState.IDLE or self.state == NPCState.FOLLOWING_LEADER:
            # PRIORITÄT 1: Führe Spieler-Befehle aus, auch wenn Häuser eigentlich nicht benötigt werden
            if has_player_command:
                if self.current_order == "BUILD_HOUSE":
                    self.state = NPCState.COLLECTING_WOOD
                    self.speech_bubble = SpeechBubble("Führe Spielerbefehl aus!", 3.0)
                    logger.info(f"🎮 {self.npc_id} führt Spielerbefehl BUILD_HOUSE aus")
                    return
            
            # PRIORITÄT 2: Automatische Hauslogik nur wenn keine Spielerbefehle
            elif houses_needed:
                # Es fehlen noch Häuser, entscheide was zu tun ist
                storage = world_state.get('storage_system', {}).get_storage(self.tribe_color)
                wood = storage.get_resource_amount('wood') if storage else 0
                
                # Prüfe ob andere NPCs bereits bauen
                building_npcs = [npc for npc in npcs if not npc.is_leader and 
                               npc.state == NPCState.BUILDING_HOUSE]
                
                if wood >= 5 and len(building_npcs) == 0:
                    # Genug Holz und niemand baut - fang an zu bauen
                    self.state = NPCState.BUILDING_HOUSE
                    self.speech_bubble = SpeechBubble("Baue Haus!", 3.0)
                    logger.info(f"🏗️ {self.npc_id} startet direkten Hausbau (Holz: {wood})")
                elif len(building_npcs) > 0:
                    # Jemand baut bereits - helfe beim Bauen
                    helping_target = building_npcs[0]
                    if helping_target.target_house:
                        self.target_house = helping_target.target_house
                        self.state = NPCState.BUILDING_HOUSE
                        self.speech_bubble = SpeechBubble("Helfe beim Bauen!", 3.0)
                        logger.info(f"🤝 {self.npc_id} hilft {helping_target.npc_id} beim Hausbau")
                    else:
                        self.state = NPCState.COLLECTING_WOOD
                        self.speech_bubble = SpeechBubble("Sammle Holz!", 3.0)
                        logger.info(f"🪓 {self.npc_id} sammelt Holz (kein Bauplatz verfügbar)")
                else:
                    # Nicht genug Holz - sammle Holz
                    self.state = NPCState.COLLECTING_WOOD
                    self.speech_bubble = SpeechBubble("Brauche Holz für Haus!", 3.0)
                    logger.info(f"🏗️ {self.npc_id} sammelt Holz ({len(houses)}/{len(npcs)} Häuser, Holz: {wood})")
            else:
                self._follow_leader()
            
        elif self.state == NPCState.COLLECTING_WOOD:
            # 🏠 NEUE BALANCE: Prüfe ob ich mein eigenes Haus baue
            my_house = world_state.get('house_system').get_house(self.npc_id)
            
            # NEUE LOGIK: Spielerbefehle haben Vorrang vor automatischer Hauslogik
            if has_player_command and self.current_order == "BUILD_HOUSE":
                # Spielerbefehl aktiv - sammle für mein eigenes Haus
                if self.carrying_wood >= self.wood_capacity:
                    logger.info(f"🔄 {self.npc_id} wechselt zu BUILDING_HOUSE (Spielerbefehl, Holz: {self.carrying_wood})")
                    self.state = NPCState.BUILDING_HOUSE  # 🏠 NEUE LOGIK: Direkt zum Hausbau
                else:
                    self._collect_wood(world_state)
            elif my_house and not my_house.built:
                # Ich habe mein eigenes Haus - sammle dafür
                if self.carrying_wood >= self.wood_capacity:
                    logger.info(f"🔄 {self.npc_id} wechselt zu BUILDING_HOUSE (eigenes Haus, Holz: {self.carrying_wood})")
                    self.state = NPCState.BUILDING_HOUSE  # 🏠 NEUE LOGIK: Direkt zum Hausbau
                else:
                    self._collect_wood(world_state)
            elif not houses_needed and not has_player_command:
                # Alle Häuser fertig - stoppe Arbeit (nur wenn kein Spielerbefehl)
                self.state = NPCState.FOLLOWING_LEADER
                self.speech_bubble = SpeechBubble("Alle Häuser fertig!", 2.0)
                logger.info(f"✅ {self.npc_id} stoppt Arbeit - alle Häuser fertig")
            elif self.carrying_wood >= self.wood_capacity:
                # Fallback: Gehe zum Lager (alte Logik)
                logger.info(f"🔄 {self.npc_id} wechselt zu RETURNING_TO_STORAGE (Holz: {self.carrying_wood})")
                self.state = NPCState.RETURNING_TO_STORAGE
            else:
                self._collect_wood(world_state)
                
        elif self.state == NPCState.RETURNING_TO_STORAGE:
            # 🏠 NEUE BALANCE: Prüfe ob ich mein eigenes Haus baue
            my_house = world_state.get('house_system').get_house(self.npc_id)
            
            # NEUE LOGIK: Spielerbefehle haben Vorrang
            if has_player_command and self.current_order == "BUILD_HOUSE":
                # Spielerbefehl aktiv - gehe zu meinem Haus statt zum Lager
                if my_house and not my_house.built:
                    logger.info(f"🏠 {self.npc_id} geht zu eigenem Haus statt zum Lager")
                    self.state = NPCState.BUILDING_HOUSE
                else:
                    self._return_to_storage(world_state)  # Fallback: Lager
            elif my_house and not my_house.built:
                # Ich habe mein eigenes Haus - gehe dorthin
                logger.info(f"🏠 {self.npc_id} geht zu eigenem Haus statt zum Lager")
                self.state = NPCState.BUILDING_HOUSE
            elif not houses_needed and not has_player_command:
                # Alle Häuser fertig - stoppe Arbeit (nur wenn kein Spielerbefehl)
                self.state = NPCState.FOLLOWING_LEADER
                self.carrying_wood = 0  # Reset Holz
                self.speech_bubble = SpeechBubble("Alle Häuser fertig!", 2.0)
                logger.info(f"✅ {self.npc_id} stoppt Einlagern - alle Häuser fertig")
            else:
                self._return_to_storage(world_state)

        elif self.state == NPCState.BUILDING_HOUSE:
            # NEUE LOGIK: Spielerbefehle haben Vorrang
            if has_player_command and self.current_order == "BUILD_HOUSE":
                # Spielerbefehl aktiv - weiter bauen auch wenn eigentlich genug Häuser da sind
                self._build_house(world_state)
            elif not houses_needed and not has_player_command:
                # Häuser sind fertig (durch anderen Worker?) - stoppe (nur wenn kein Spielerbefehl)
                self.state = NPCState.FOLLOWING_LEADER
                self.target_house = None
                self.speech_bubble = SpeechBubble("Hausbau nicht mehr nötig!", 2.0)
                logger.info(f"✅ {self.npc_id} stoppt Hausbau - alle Häuser fertig")
            else:
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
            search_radius = 1000  # Stark erhöhter Suchradius
            
            # Erstelle Liste der bereits als Ziel markierten Bäume
            targeted_trees = set()
            for npc in world_state.get('tribe_system').tribes[self.tribe_color]:
                if npc != self and npc.target_tree:
                    targeted_trees.add(npc.target_tree)
            
            # Zuerst in der Nähe suchen
            for tree in trees:
                if tree.alive and tree not in targeted_trees:
                    dist = pygame.Vector2(tree.x, tree.y).distance_to(self.position)
                    if dist < min_distance and dist < search_radius:
                        min_distance = dist
                        nearest_tree = tree
            
            # Wenn kein Baum in der Nähe, erweitere Suchradius
            if not nearest_tree:
                search_radius = 2000  # Sehr großer Suchradius als Fallback
                for tree in trees:
                    if tree.alive and tree not in targeted_trees:
                        dist = pygame.Vector2(tree.x, tree.y).distance_to(self.position)
                        if dist < min_distance:
                            min_distance = dist
                            nearest_tree = tree
            
            if nearest_tree:
                self.target_tree = nearest_tree
                self.speech_bubble = SpeechBubble("Dieser Baum sieht gut aus!", 2.0)
                logger.info(f"🌳 {self.npc_id} hat Baum gefunden! (Entfernung: {int(min_distance)})")
            else:
                # Wenn kein Baum gefunden wurde, gehe in Richtung Weltmitte
                world_center = pygame.Vector2(2000, 2000)  # Ungefähre Weltmitte
                direction = (world_center - self.position).normalize()
                self.velocity = direction * self.max_speed
                logger.info(f"🔍 {self.npc_id} geht zur Weltmitte und sucht Bäume...")
                self.speech_bubble = SpeechBubble("Gehe zur Weltmitte...", 2.0)
                return

        if self.target_tree:
            dist = pygame.Vector2(self.target_tree.x, self.target_tree.y).distance_to(self.position)
            
            if dist > 40:  # Gehe zum Baum
                direction = (pygame.Vector2(self.target_tree.x, self.target_tree.y) - self.position).normalize()
                self.velocity = direction * self.max_speed
            else:  # Fälle Baum
                self.velocity = pygame.Vector2(0, 0)
                
                # 🪓 REALISTISCHES BAUMFÄLLEN: Nur alle 2 Sekunden schlagen
                if self.chop_cooldown <= 0:
                    self.chop_cooldown = self.max_chop_cooldown  # Reset Cooldown
                    
                    # 🗣️ Zufällige Baum-Anekdoten beim Schlagen (10% Chance)
                    if random.random() < 0.1:
                        self._random_tree_anecdote()
                    
                    if self.target_tree.take_damage(25):  # Baum wurde gefällt (nach 4 Schlägen)
                        wood_amount = random.randint(4, 5)  # 4-5 Holz pro Baum
                        self.carrying_wood += wood_amount
                        # Nur bei größeren Mengen sprechen
                        if wood_amount >= 3:
                            self._set_speech_bubble(f"Habe {wood_amount} Holz gesammelt!", 2.0)
                        logger.info(f"🪓 {self.npc_id} hat {wood_amount} Holz gesammelt!")
                        self.target_tree = None
                        
                        # Wenn genug Holz gesammelt wurde, prüfe ob direkt bauen oder zum Lager
                        if self.carrying_wood >= self.wood_capacity:
                            # Prüfe ob Häuser fehlen
                            houses = [h for h in world_state.get('house_system', {}).houses.values() 
                                     if h.tribe_color == self.tribe_color and h.built]
                            npcs = world_state.get('tribe_system', {}).tribes.get(self.tribe_color, [])
                            
                            if len(houses) < len(npcs):
                                # Häuser fehlen - direkt bauen!
                                self.state = NPCState.BUILDING_HOUSE
                                self.speech_bubble = SpeechBubble(f"Baue Haus mit {self.carrying_wood} Holz!", 3.0)
                                logger.info(f"🏗️ {self.npc_id} hat {self.carrying_wood} Holz → startet direkten Hausbau!")
                            else:
                                # Alle Häuser fertig - zum Lager
                                logger.info(f"🎒 {self.npc_id} hat genug Holz ({self.carrying_wood}/{self.wood_capacity}), geht zum Lager")
                                self.speech_bubble = SpeechBubble("Genug Holz! Zurück zum Lager!", 2.0)
                    else:
                        # Baum noch nicht gefällt, zeige Fortschritt
                        hp_percent = int((self.target_tree.current_hp / self.target_tree.max_hp) * 100)
                        # Nur alle 3 Schläge sprechen statt bei jedem
                        if random.random() < 0.3:
                            self._set_speech_bubble(f"Fälle Baum... {hp_percent}% HP", 1.8)
                else:
                    # Warten auf nächsten Schlag
                    wait_time = int(self.chop_cooldown) + 1
                    # Nur gelegentlich sprechen beim Warten
                    if random.random() < 0.1:
                        self._set_speech_bubble(f"Bereite nächsten Schlag vor... {wait_time}s", 0.5)

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
                # Weniger häufige Nachrichten beim Transport
                if random.random() < 0.05 and (not self.speech_bubble or self.speech_bubble.is_expired()):  # Reduziert von 0.2 auf 0.05
                    self._set_speech_bubble(f"Bringe {self.carrying_wood} Holz zum Lager", 2.0)
                    logger.info(f"🚶 {self.npc_id} geht zum Lager (Distanz: {int(dist)})")
            else:  # Lagere Holz ein
                self.velocity = pygame.Vector2(0, 0)  # Stoppe Bewegung
                
                # Prüfe aktuelle Holzmenge im Lager
                current_wood = storage.get_resource_amount('wood')
                storage.add_resources('wood', self.carrying_wood)
                self._set_speech_bubble(f"{self.carrying_wood} Holz eingelagert!", 2.0)
                logger.info(f"📦 {self.npc_id} hat {self.carrying_wood} Holz eingelagert!")
                
                # Aktualisiere Zustand
                self.carrying_wood = 0
                
                new_wood = storage.get_resource_amount('wood')
                logger.info(f"📦 {self.npc_id}: Lager enthält {new_wood}/5 Holz")
                
                # Prüfe ob wir einen aktiven Baubefehl haben
                # Prüfe den aktuellen Status der Häuser
                houses = [h for h in world_state['house_system'].houses.values() 
                         if h.tribe_color == self.tribe_color and h.built]
                npcs = world_state['tribe_system'].tribes[self.tribe_color]
                houses_under_construction = [h for h in world_state['house_system'].houses.values()
                                          if h.tribe_color == self.tribe_color 
                                          and h.build_progress > 0 
                                          and h.build_progress < 100]
                
                total_houses_needed = len(npcs)
                total_houses_available = len(houses) + len(houses_under_construction)

                # Prüfe aktuellen Hausstatus
                houses = [h for h in world_state['house_system'].houses.values() 
                         if h.tribe_color == self.tribe_color and h.built]
                total_houses_needed = len(world_state['tribe_system'].tribes[self.tribe_color])
                
                # Nur weiterbauen wenn noch fertige Häuser fehlen
                if len(houses) < total_houses_needed:
                    if new_wood >= 5:
                        # Genug Holz für ein neues Haus
                        self.state = NPCState.BUILDING_HOUSE
                        self.speech_bubble = SpeechBubble("Jawohl, ich baue ein Haus!", 3.0)
                        logger.info(f"🏗️ {self.npc_id} beginnt mit dem Hausbau! ({len(houses)}/{total_houses_needed})")
                    else:
                        # Noch nicht genug Holz
                        self.state = NPCState.COLLECTING_WOOD
                        self.speech_bubble = SpeechBubble(f"Jawohl, hole noch mehr Holz! ({new_wood}/5)", 2.0)
                        logger.info(f"🪓 {self.npc_id} sammelt weiter Holz für Haus {len(houses) + 1}/{total_houses_needed}")
                else:
                    # Alle benötigten Häuser sind fertig
                    self.current_order = None
                    self.state = NPCState.FOLLOWING_LEADER
                    self.speech_bubble = SpeechBubble("Alle Häuser sind fertig!", 3.0)
                    logger.info(f"✅ {self.npc_id}: Keine weiteren Häuser benötigt ({len(houses)}/{total_houses_needed})")
        except Exception as e:
            logger.error(f"⚠️ Fehler beim Einlagern von Holz: {e}")
            self.state = NPCState.COLLECTING_WOOD
            self.carrying_wood = 0  # Verhindere Endlosschleife

    def _build_house(self, world_state: Dict):
        """Baue mein eigenes Haus - REALISTISCHER HAUSBAU MIT BAUPLÄTZEN"""
        # Prüfe ob ich bereits ein Haus habe
        my_house = world_state.get('house_system').get_house(self.npc_id)
        
        if my_house and my_house.built:
            # Mein Haus ist bereits fertig
            logger.info(f"✅ {self.npc_id}: Mein Haus ist bereits fertig!")
            self.state = NPCState.FOLLOWING_LEADER
            self.target_house = None
            return
            
        if not self.target_house:
            if my_house:
                # Ich habe ein Haus, aber es ist nicht fertig
                self.target_house = my_house
                logger.info(f"🏗️ {self.npc_id} setzt Bau am eigenen Haus fort")
            else:
                # Ich brauche ein neues Haus
                has_wood_inventory = self.carrying_wood >= 5
                storage = world_state.get('storage_system').get_storage(self.tribe_color)
                has_wood_storage = storage and storage.get_resource_amount('wood') >= 5
                
                if has_wood_inventory or has_wood_storage:
                    # Erstelle mein eigenes Haus
                    house = world_state.get('house_system').build_house_for_npc(self.npc_id, self.tribe_color)
                    if house:
                        self.target_house = house
                        logger.info(f"🏗️ {self.npc_id} erstellt Bauplatz für eigenes Haus!")
                        self.speech_bubble = SpeechBubble(f"Baue mein eigenes Haus!", 3.0)
                    else:
                        logger.info(f"❌ {self.npc_id} konnte kein Haus erstellen")
                        self.state = NPCState.COLLECTING_WOOD
                        return
                else:
                    logger.info(f"� {self.npc_id} braucht Holz für eigenes Haus")
                    self.state = NPCState.COLLECTING_WOOD
                    return

        # 🏗️ NEUE REALISTISCHE BAULOGIK
        if self.target_house:
            # Hole optimale Bauposition (direkt vor dem Haus)
            build_pos = pygame.Vector2(self.target_house.get_build_position())
            current_distance = build_pos.distance_to(self.position)

            # Schritt 1: Gehe zur Bauposition
            if current_distance > 15:  # Muss näher als 15 Pixel sein
                direction = (build_pos - self.position).normalize()
                self.velocity = direction * self.max_speed
                self.is_building = False  # 🔨 Keine Bauanimation beim Laufen
                if random.random() < 0.1:  # Gelegentliche Updates
                    logger.info(f"🚶 {self.npc_id} geht zum Bauplatz (Entfernung: {current_distance:.1f})")
                    self.speech_bubble = SpeechBubble("Gehe zum Bauplatz...", 2.0)
                return
            
            # Schritt 2: Prüfe ob ich in der Bauzone bin
            if not self.target_house.is_in_build_zone((self.position.x, self.position.y)):
                # Bewege mich in die Bauzone
                house_center = pygame.Vector2(
                    self.target_house.position.x + self.target_house.size[0]/2,
                    self.target_house.position.y + self.target_house.size[1]/2
                )
                direction = (house_center - self.position).normalize()
                self.velocity = direction * (self.max_speed * 0.3)  # Langsamer in der Bauzone
                self.is_building = False  # 🔨 Keine Bauanimation beim Positionieren
                if random.random() < 0.05:
                    self.speech_bubble = SpeechBubble("Positioniere mich zum Bauen...", 2.0)
                return
            
            # Schritt 3: Ich bin in der Bauzone - kann bauen!
            self.velocity = pygame.Vector2(0, 0)  # Stoppe Bewegung
            self.is_building = True  # 🔨 Aktiviere Bauanimation
            
            # Verwende Holz aus Inventar oder Lager für Bau
            if not self.target_house.built:
                wood_needed = self.target_house.get_build_requirements()['wood']
                
                if wood_needed > 0:
                    # Prüfe ob ich Holz habe oder aus Lager nehmen kann
                    wood_to_deposit = 0
                    if self.carrying_wood > 0:
                        wood_to_deposit = min(self.carrying_wood, 1)  # 1 Holz pro Frame
                        self.carrying_wood -= wood_to_deposit
                    else:
                        # Versuche Holz aus Lager zu nehmen
                        storage = world_state.get('storage_system').get_storage(self.tribe_color)
                        if storage and storage.get_resource_amount('wood') > 0:
                            storage.remove_resources('wood', 1)
                            wood_to_deposit = 1
                    
                    if wood_to_deposit > 0:
                        # Deponiere Holz am Bauplatz (aktualisiert wood_deposited und Counter)
                        deposited = self.target_house.deposit_wood(wood_to_deposit)
                        if deposited > 0:
                            # Verwende abgelegtes Holz für Bau (aktualisiert wood_used und build_progress)
                            used = self.target_house.add_resources(wood=deposited)
                            if used and random.random() < 0.1:  # Gelegentliche Updates
                                progress_percent = int(self.target_house.build_progress * 100)
                                logger.info(f"🔨 {self.npc_id} baut am Haus ({progress_percent}% fertig)")
                                self.speech_bubble = SpeechBubble(f"Baue... {progress_percent}%", 1.5)
                    else:
                        # Kein Holz verfügbar - sammle mehr
                        logger.info(f"🌲 {self.npc_id} braucht mehr Holz zum Bauen")
                        self.state = NPCState.COLLECTING_WOOD
                        self.speech_bubble = SpeechBubble("Brauche mehr Holz!", 2.0)
                        self.is_building = False  # 🔨 Deaktiviere Bauanimation
                        return
                
                # Prüfe ob Haus fertig ist
                if self.target_house.built:
                    logger.info(f"🏠 {self.npc_id} hat eigenes Haus fertiggestellt!")
                    self.speech_bubble = SpeechBubble("🏠 Mein Haus ist fertig!", 3.0)
                    self.target_house = None
                    self.is_building = False  # 🔨 Deaktiviere Bauanimation
                    # Spielerbefehl erfüllt - entferne current_order
                    if hasattr(self, 'current_order') and self.current_order == "BUILD_HOUSE":
                        self.current_order = None
                        logger.info(f"✅ {self.npc_id} hat Spielerbefehl BUILD_HOUSE erfüllt")
                    # Anführer geht zu IDLE, Worker zu FOLLOWING_LEADER
                    self.state = NPCState.IDLE if self.is_leader else NPCState.FOLLOWING_LEADER
            else:
                # Haus ist bereits fertig
                logger.info(f"✅ {self.npc_id}: Haus ist jetzt fertig!")
                self.target_house = None
                self.is_building = False  # 🔨 Deaktiviere Bauanimation
                # Spielerbefehl erfüllt - entferne current_order
                if hasattr(self, 'current_order') and self.current_order == "BUILD_HOUSE":
                    self.current_order = None
                    logger.info(f"✅ {self.npc_id} hat Spielerbefehl BUILD_HOUSE erfüllt")
                # Anführer geht zu IDLE, Worker zu FOLLOWING_LEADER
                self.state = NPCState.IDLE if self.is_leader else NPCState.FOLLOWING_LEADER

    def _follow_leader(self):
        """Soziales Verhalten: Sammle dich beim Anführer für Gespräche"""
        if not self.leader:
            return

        # Prüfe ob der Anführer beschäftigt ist (IDLE = nicht beschäftigt)
        leader_is_busy = (self.leader.state == NPCState.COLLECTING_WOOD or 
                         self.leader.state == NPCState.BUILDING_HOUSE or
                         self.leader.state == NPCState.RETURNING_TO_STORAGE)
        
        # Debug: Log leader state
        if random.random() < 0.01:  # Seltenes Debug-Log
            logger.info(f"🤖 {self.npc_id}: Leader state = {self.leader.state.value}, busy = {leader_is_busy}")
        
        dist = self.leader.position.distance_to(self.position)
        
        if leader_is_busy and dist < 80:
            # Anführer ist beschäftigt - halte respektvollen Abstand
            if dist < 60:
                # Weiche zurück um ihm Raum zu geben
                direction = (self.position - self.leader.position).normalize()
                self.velocity = direction * self.max_speed * 0.3
                if random.random() < 0.01:  # Seltene Nachrichten
                    self.speech_bubble = SpeechBubble("Der Anführer arbeitet...", 2.0)
            else:
                # Warte in respektvoller Entfernung
                self.velocity = pygame.Vector2(0, 0)
                if random.random() < 0.005:
                    self.speech_bubble = SpeechBubble("Warten auf den Anführer", 2.0)
        else:
            # Anführer ist nicht beschäftigt - normale soziale Sammlung
            if dist > 120:  # Zu weit weg - komme näher
                direction = (self.leader.position - self.position).normalize()
                self.velocity = direction * self.max_speed
            elif dist > 80:  # Mittlere Distanz - gemütlich nähern
                direction = (self.leader.position - self.position).normalize()
                self.velocity = direction * self.max_speed * 0.4
            else:  # Nahe genug für Gespräche
                # Kleine zufällige Bewegungen für natürliches Verhalten
                if random.random() < 0.02:
                    random_dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                    if random_dir.length() > 0:
                        random_dir = random_dir.normalize()
                        self.velocity = random_dir * self.max_speed * 0.2
                else:
                    self.velocity = pygame.Vector2(0, 0)
                
                # ERWEITERTE TEAM-GESPRÄCHE für große Gruppen
                if random.random() < 0.02:  # Reduziert von 0.08 auf 0.02 (weniger Gespräche)
                    # Vereinfachte Gespräche für große Gruppen
                    conversation_topics = [
                        "Schöne Häuser haben wir gebaut!",
                        "Was machen wir als nächstes?", 
                        "Das Dorf entwickelt sich gut",
                        "Friedliche Zeiten...",
                        "Die Arbeit ist getan!",
                        "Anführer, was sind deine Pläne?",
                        "Sollen wir mehr Häuser bauen?",
                        "Das Wetter ist heute schön",
                        "Unser Team ist groß und stark!",
                        "11 Charaktere - perfekte Gruppe!",
                        "Große Gruppe - starke Kraft!",
                        "Teamwork macht uns stark!",
                        "Koordination ist der Schlüssel!",
                        "Alle arbeiten gut zusammen!"
                    ]
                    topic = random.choice(conversation_topics)
                    self.speech_bubble = SpeechBubble(topic, 4.0)

    def receive_player_command(self, command_data: Dict):
        """Empfange Befehl vom Spieler über das Chat-System"""
        if not hasattr(self, 'player_commands'):
            self.player_commands = []
        
        self.player_commands.append(command_data)
        logger.info(f"👑 {self.npc_id} empfängt Befehl: {command_data.get('description', 'Unbekannt')}")

    def _process_player_commands(self, world_state: Dict):
        """Verarbeite alle Spieler-Befehle"""
        if not hasattr(self, 'player_commands'):
            return
            
        for command in self.player_commands[:]:  # Kopie für sichere Iteration
            self._execute_player_command(command, world_state)
            self.player_commands.remove(command)

    def _execute_player_command(self, command: Dict, world_state: Dict):
        """Führe einen Spieler-Befehl aus"""
        command_type = command.get('type', 'unknown')
        
        if command_type == 'build_houses':
            self._execute_build_houses_command(command, world_state)
        elif command_type == 'collect_resources':
            self._execute_collect_resources_command(command, world_state)
        elif command_type == 'status':
            self._execute_status_command(command, world_state)
        elif command_type == 'stop_all':
            self._execute_stop_all_command(command, world_state)
        else:
            response = f"Ich verstehe den Befehl '{command.get('original', '')}' nicht, Herr!"
            self.speech_bubble = SpeechBubble(response, 4.0)
            if hasattr(self, 'command_responses'):
                self.command_responses.append(response)

    def _execute_build_houses_command(self, command: Dict, world_state: Dict):
        """Führe Hausbau-Befehl aus"""
        house_count = command.get('count', 1)
        
        # Prüfe aktuellen Status
        npcs = world_state['tribe_system'].tribes[self.tribe_color]
        current_houses = len([h for h in world_state['house_system'].houses.values() 
                            if h.tribe_color == self.tribe_color and h.built])
        
        if house_count <= current_houses:
            response = f"Herr, wir haben bereits {current_houses} Häuser! Befehl nicht nötig."
        else:
            needed_houses = house_count - current_houses
            
            # Weise Arbeiter zu Hausbau zu
            idle_workers = [npc for npc in npcs if not npc.is_leader and 
                          npc.state in [NPCState.IDLE, NPCState.FOLLOWING_LEADER]]
            
            workers_assigned = 0
            houses_assigned = min(needed_houses, len(idle_workers))
            
            for worker in idle_workers[:needed_houses]:  # Max so viele wie gebraucht
                worker.current_order = "BUILD_HOUSE"
                worker.state = NPCState.COLLECTING_WOOD
                worker.speech_bubble = SpeechBubble(f"Jawohl! Baue Haus #{current_houses + workers_assigned + 1}!", 3.0)
                workers_assigned += 1
                logger.info(f"📢 {self.npc_id} → {worker.npc_id}: Baue Haus auf Spieler-Befehl!")
            
            # Berechne Holzbedarf
            wood_per_house = 5
            total_wood_needed = needed_houses * wood_per_house
            storage = world_state.get('storage_system').get_storage(self.tribe_color)
            wood_available = storage.get_resource_amount('wood') if storage else 0
            
            if wood_available < total_wood_needed:
                response = f"Jawohl! {workers_assigned} Arbeiter starten {houses_assigned} Häuser (benötigen mehr Holz für alle {needed_houses})"
            else:
                response = f"Jawohl! {workers_assigned} Arbeiter bauen {houses_assigned} Häuser in Teams!"
        
        self.speech_bubble = SpeechBubble(response, 8.0)  # Länger anzeigen für komplexe Befehle
        if hasattr(self, 'command_responses'):
            self.command_responses.append(response)

    def _execute_collect_resources_command(self, command: Dict, world_state: Dict):
        """Führe Ressourcen-Sammel-Befehl aus"""
        resource = command.get('resource', 'wood')
        amount = command.get('amount', 10)
        
        # Weise alle verfügbaren Arbeiter zum Sammeln zu
        npcs = world_state['tribe_system'].tribes[self.tribe_color]
        idle_workers = [npc for npc in npcs if not npc.is_leader and 
                      npc.state in [NPCState.IDLE, NPCState.FOLLOWING_LEADER]]
        
        if not idle_workers:
            response = "Alle Arbeiter sind beschäftigt, Herr!"
        else:
            # INTELLIGENTE RESSOURCENVERTEILUNG
            workers_needed = min(len(idle_workers), max(1, amount // 10))  # 1 Arbeiter pro 10 Einheiten
            if workers_needed == 0:
                workers_needed = 1
                
            # Teile Arbeiter in Sammel-Teams auf
            amount_per_worker = amount // workers_needed
            
            workers_assigned = 0
            for i, worker in enumerate(idle_workers[:workers_needed]):
                if resource == 'wood':
                    worker.state = NPCState.COLLECTING_WOOD
                    worker.current_order = f"COLLECT_WOOD_{amount_per_worker}"
                    
                    # Team-Koordination
                    if i == 0:
                        worker.speech_bubble = SpeechBubble(f"Team-Leader: {amount_per_worker} Holz!", 3.0)
                        logger.info(f"🌳 {self.npc_id} → {worker.npc_id}: Team-Leader sammelt {amount_per_worker} Holz")
                    else:
                        worker.speech_bubble = SpeechBubble(f"Team-Mitglied: {amount_per_worker} Holz!", 3.0)
                        logger.info(f"🌲 {self.npc_id} → {worker.npc_id}: Team-Mitglied sammelt {amount_per_worker} Holz")
                        
                workers_assigned += 1
            
            response = f"Jawohl! {workers_assigned} Arbeiter sammeln {amount} {resource} in {workers_needed} Teams!"
        
        self.speech_bubble = SpeechBubble(response, 6.0)  # Länger anzeigen für Team-Koordination
        if hasattr(self, 'command_responses'):
            self.command_responses.append(response)

    def _execute_status_command(self, command: Dict, world_state: Dict):
        """Gib detaillierten Statusbericht für große Gruppen"""
        npcs = world_state['tribe_system'].tribes[self.tribe_color]
        houses = [h for h in world_state['house_system'].houses.values() 
                 if h.tribe_color == self.tribe_color and h.built]
        houses_in_progress = [h for h in world_state['house_system'].houses.values() 
                            if h.tribe_color == self.tribe_color and not h.built]
        storage = world_state.get('storage_system', {}).get_storage(self.tribe_color)
        wood = storage.get_resource_amount('wood') if storage else 0
        
        # DETAILLIERTE NPC-ANALYSE für große Gruppen
        idle_workers = [npc for npc in npcs if not npc.is_leader and 
                       npc.state in [NPCState.IDLE, NPCState.FOLLOWING_LEADER]]
        collecting_workers = [npc for npc in npcs if not npc.is_leader and 
                            npc.state == NPCState.COLLECTING_WOOD]
        building_workers = [npc for npc in npcs if not npc.is_leader and 
                          npc.state == NPCState.BUILDING_HOUSE]
        
        # Berechne Effizienz
        total_workers = len(npcs) - 1  # -1 für Leader
        efficiency = ((len(collecting_workers) + len(building_workers)) / max(1, total_workers)) * 100
        
        response = f"Status: {len(houses)} Häuser fertig, {len(houses_in_progress)} in Bau, {wood} Holz | {total_workers} Arbeiter: {len(idle_workers)} bereit, {len(collecting_workers)} sammeln, {len(building_workers)} bauen | Effizienz: {efficiency:.0f}%"
        
        self.speech_bubble = SpeechBubble(response, 10.0)  # Langer Statusbericht braucht mehr Zeit
        if hasattr(self, 'command_responses'):
            self.command_responses.append(response)

    def _execute_stop_all_command(self, command: Dict, world_state: Dict):
        """Stoppe alle Arbeiter"""
        npcs = world_state['tribe_system'].tribes[self.tribe_color]
        stopped_count = 0
        
        for npc in npcs:
            if not npc.is_leader and npc.state != NPCState.FOLLOWING_LEADER:
                npc.state = NPCState.FOLLOWING_LEADER
                npc.speech_bubble = SpeechBubble("Befehl erhalten - stoppe Arbeit!", 3.0)
                npc.current_order = None
                stopped_count += 1
        
        response = f"Jawohl! {stopped_count} Arbeiter gestoppt."
        self.speech_bubble = SpeechBubble(response, 4.0)
        if hasattr(self, 'command_responses'):
            self.command_responses.append(response)

    def _execute_assigned_task(self, dt: float, world_state: Dict):
        """Führe zugewiesene Task vom KI-Leader aus - nutze normale Logik"""
        if not self.assigned_task:
            return
            
        task_type = self.assigned_task.task_type
        
        try:
            if task_type == TaskType.COLLECT_WOOD:
                # Nutze normale Holz-Sammel-Logik
                if self.state == NPCState.IDLE or self.state == NPCState.FOLLOWING_LEADER:
                    self.state = NPCState.COLLECTING_WOOD
                    self.speech_bubble = SpeechBubble("KI-Befehl: Holz sammeln!", 3.0)
                
                if self.state == NPCState.COLLECTING_WOOD:
                    # Normale Holz-Sammel-Logik
                    if self.carrying_wood >= self.wood_capacity:
                        # Prüfe ob Häuser fehlen
                        houses = [h for h in world_state.get('house_system', {}).houses.values() 
                                 if h.tribe_color == self.tribe_color and h.built]
                        npcs = world_state.get('tribe_system', {}).tribes.get(self.tribe_color, [])
                        
                        if len(houses) < len(npcs):
                            # Häuser fehlen - direkt bauen statt zum Lager gehen!
                            self.state = NPCState.BUILDING_HOUSE
                            self.speech_bubble = SpeechBubble(f"Baue mit {self.carrying_wood} Holz!", 3.0)
                            logger.info(f"🏗️ {self.npc_id} hat {self.carrying_wood} Holz → startet direkten Hausbau!")
                        else:
                            # Alle Häuser fertig - zum Lager
                            self.state = NPCState.RETURNING_TO_STORAGE
                    else:
                        self._collect_wood(world_state)
                elif self.state == NPCState.RETURNING_TO_STORAGE:
                    self._return_to_storage(world_state)
                    
            elif task_type == TaskType.BUILD_HOUSE:
                if self.state != NPCState.BUILDING_HOUSE and self.state != NPCState.COLLECTING_WOOD:
                    self.state = NPCState.COLLECTING_WOOD
                    self.speech_bubble = SpeechBubble("KI-Befehl: Haus bauen!", 3.0)
                
                if self.state == NPCState.COLLECTING_WOOD:
                    self._collect_wood(world_state)
                elif self.state == NPCState.RETURNING_TO_STORAGE:
                    self._return_to_storage(world_state)
                elif self.state == NPCState.BUILDING_HOUSE:
                    self._build_house(world_state)
                    
            elif task_type == TaskType.EXPLORE:
                self.state = NPCState.EXPLORING
                self._explore(world_state)
                
            elif task_type == TaskType.GATHER_FOOD:
                self.state = NPCState.GATHERING_FOOD
                self._gather_food(world_state)
                
            elif task_type == TaskType.DEFEND:
                self.state = NPCState.DEFENDING
                self._defend(world_state)
                
            # Prüfe Task-Completion
            self._check_task_completion(world_state)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Ausführen von Task {task_type}: {e}")
            self.assigned_task.completed = True

    def _explore(self, world_state: Dict):
        """Erkunde die Umgebung"""
        if not hasattr(self, '_exploration_target'):
            # Wähle zufälligen Punkt in der Nähe
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(200, 500)
            self._exploration_target = pygame.Vector2(
                self.position.x + math.cos(angle) * distance,
                self.position.y + math.sin(angle) * distance
            )
            self.speech_bubble = SpeechBubble("Erkunde die Gegend...", 3.0)
            logger.info(f"🗺️ {self.npc_id} erkundet Gebiet")
        
        # Bewege dich zum Ziel
        dist = self._exploration_target.distance_to(self.position)
        if dist > 30:
            direction = (self._exploration_target - self.position).normalize()
            self.velocity = direction * self.max_speed * 0.8
        else:
            # Ziel erreicht, neue Richtung wählen
            delattr(self, '_exploration_target')
            self.experience += 1
            
    def _gather_food(self, world_state: Dict):
        """Sammle Nahrung (Placeholder)"""
        self.velocity = pygame.Vector2(0, 0)
        self.speech_bubble = SpeechBubble("Sammle Beeren...", 2.0)
        # Vereinfacht: "sammle" nach kurzer Zeit
        if not hasattr(self, '_gather_timer'):
            self._gather_timer = time.time()
        elif time.time() - self._gather_timer > 5.0:
            logger.info(f"🫐 {self.npc_id} hat Nahrung gesammelt!")
            delattr(self, '_gather_timer')
            self.experience += 1
            
    def _defend(self, world_state: Dict):
        """Verteidige das Gebiet (Placeholder)"""
        self.velocity = pygame.Vector2(0, 0)
        self.speech_bubble = SpeechBubble("Verteidige!", 2.0)
        logger.info(f"🛡️ {self.npc_id} verteidigt das Gebiet")
        # Vereinfachte Verteidigung
        self.experience += 1
        
    def _check_task_completion(self, world_state: Dict):
        """Prüfe ob zugewiesene Task abgeschlossen ist"""
        if not self.assigned_task:
            return
            
        task_type = self.assigned_task.task_type
        
        # Task-spezifische Completion-Checks
        if task_type == TaskType.COLLECT_WOOD:
            # Wood collection task fertig wenn genug im Lager für ein Haus
            storage = world_state.get('storage_system', {}).get_storage(self.tribe_color)
            if storage and storage.get_resource_amount('wood') >= 5:
                self.assigned_task.completed = True
                self.speech_bubble = SpeechBubble("Genug Holz für Haus!", 2.0)
                logger.info(f"✅ {self.npc_id} hat Holz-Sammlung abgeschlossen! (Lager: {storage.get_resource_amount('wood')})")
                
                # Task ist abgeschlossen - KI-Leader wird beim nächsten Update neue Tasks erstellen
                logger.info(f"🔄 {self.npc_id} wartet auf neue Task vom KI-Leader")
                
        elif task_type == TaskType.BUILD_HOUSE:
            # House building task fertig wenn alle Häuser da sind
            houses = [h for h in world_state.get('house_system', {}).houses.values() 
                     if h.tribe_color == self.tribe_color and h.built]
            npcs = world_state.get('tribe_system', {}).tribes.get(self.tribe_color, [])
            if len(houses) >= len(npcs):
                self.assigned_task.completed = True
                self.speech_bubble = SpeechBubble("Hausbau-Auftrag erledigt!", 2.0)
                logger.info(f"✅ {self.npc_id} hat Hausbau abgeschlossen!")
                
        elif task_type in [TaskType.EXPLORE, TaskType.GATHER_FOOD, TaskType.DEFEND]:
            # Zeitbasierte Tasks - nach 30 Sekunden fertig
            if time.time() - self.assigned_task.created_time > 30:
                self.assigned_task.completed = True
                self.speech_bubble = SpeechBubble("Auftrag erledigt!", 2.0)
                logger.info(f"✅ {self.npc_id} hat {task_type.value} abgeschlossen!")
        
        # Wenn Task fertig, erhalte Erfahrung und gehe zu IDLE
        if self.assigned_task.completed:
            self.experience += 2
            self.assigned_task = None
            self.state = NPCState.IDLE

class SimpleTribeSystem:
    def __init__(self):
        self.tribes = {}  # Color -> [NPCs]
        self.ai_leaders = {}  # Color -> AILeader
        # Initialisiere den Sprite Manager
        from character_sprites import CharacterSprites
        self.sprite_manager = CharacterSprites()
        
    def create_tribe(self, color: str, leader_pos, num_workers: int = 2):
        """Erstelle einen neuen Stamm mit Leader und Workers"""
        # Begrenze Anzahl Workers für Performance (reduziert für optimale Performance)
        num_workers = min(num_workers, 4)  # Max 4 + 1 Leader = 5 total
        
        # Erstelle Lager in der Nähe des Leaders
        storage_pos = (leader_pos[0] + random.randint(-100, -50), 
                      leader_pos[1] + random.randint(-100, -50))
                      
        leader = SimpleNPC(f"leader_{color}", leader_pos, color, is_leader=True, sprite_manager=self.sprite_manager)
        workers = []
        
        # Erstelle Worker in Gruppen um Clustering zu vermeiden
        for i in range(num_workers):
            # Verschiedene Bereiche um den Leader
            angle = (i / num_workers) * 2 * math.pi
            distance = random.uniform(30, 100)
            worker_pos = (
                leader_pos[0] + math.cos(angle) * distance + random.randint(-20, 20),
                leader_pos[1] + math.sin(angle) * distance + random.randint(-20, 20)
            )
            
            worker = SimpleNPC(f"worker_{color}_{i}", worker_pos, color, sprite_manager=self.sprite_manager)
            worker.leader = leader
            workers.append(worker)
        
        self.tribes[color] = [leader] + workers
        
        # AKTIVIERT: KI-Leader System AN
        from ai_leader import AILeader
        ai_leader = AILeader(f"ai_leader_{color}", color, max_workers=num_workers)
        self.ai_leaders[color] = ai_leader
        
        logger.info(f"🏰 Neuer Stamm erstellt: {color} mit {num_workers} Arbeitern (KI-Leader AKTIVIERT)")
        
    def update(self, dt: float, world_state: Dict):
        """Update alle NPCs in allen Stämmen mit KI-Leader Integration"""
        for tribe_color, npcs in self.tribes.items():
            # AKTIVIERT: KI-Leader System AN!
            if tribe_color in self.ai_leaders:
                ai_leader = self.ai_leaders[tribe_color]
                ai_leader.update(world_state)
                
                # Weise Tasks zu verfügbaren Arbeitern zu
                available_workers = [npc for npc in npcs if not npc.is_leader 
                                   and (not npc.assigned_task or npc.assigned_task.completed)]
                
                if available_workers and ai_leader.active_tasks:
                    task_assignments = ai_leader.assign_tasks(available_workers)
                    
                    for worker_id, task in task_assignments.items():
                        worker = next((npc for npc in npcs if npc.npc_id == worker_id), None)
                        if worker:
                            worker.assigned_task = task
            #                 logger.info(f"📋 KI-Leader weist {worker_id} Task zu: {task.task_type.value}")
            
            # Update alle NPCs
            for npc in npcs:
                npc.update(dt, world_state)
