"""
🧠 Tribe AI System - TensorFlow-basierte Stamm-KI
Fortgeschrittenes KI-System für NPCs mit Neural Networks, NLP und Reinforcement Learning
"""

import pygame
import tensorflow as tf
import tensorflow_probability as tfp
import numpy as np
import pandas as pd
import random
import math
import json
import pickle
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import logging
from datetime import datetime
import os

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Aktionstypen für Stamm-Mitglieder"""
    IDLE = "idle"
    GATHERING = "gathering"
    CONVERSATION = "conversation"
    PLANNING = "planning"
    GUARD_DUTY = "guard_duty"
    RESOURCE_MANAGEMENT = "resource_management"
    DIPLOMACY = "diplomacy"
    RESEARCH = "research"
    TERRITORY_PATROL = "territory_patrol"
    TRADE = "trade"
    TEACHING = "teaching"
    # Neue Aktionen für Anführer/Untertan System
    COMMAND_FOLLOWERS = "command_followers"
    FOLLOW_LEADER = "follow_leader"
    WOOD_CHOPPING = "wood_chopping"
    STONE_MINING = "stone_mining"
    HOUSE_BUILDING = "house_building"
    WANDERING = "wandering"

class PersonalityTrait(Enum):
    """Persönlichkeitsmerkmale"""
    AGGRESSIVE = "aggressive"
    PEACEFUL = "peaceful"
    CURIOUS = "curious"
    CONSERVATIVE = "conservative"
    SOCIAL = "social"
    SOLITARY = "solitary"
    LEADER = "leader"
    FOLLOWER = "follower"

@dataclass
class TribeMemory:
    """Gedächtnis-System für Stamm-Mitglieder"""
    interactions: List[Dict] = None
    decisions: List[Dict] = None
    learned_behaviors: List[Dict] = None
    relationships: Dict[str, float] = None
    territory_knowledge: Dict[str, Any] = None
    # Neue Felder für Anführer-System
    leader_commands: List[Dict] = None
    resources_collected: Dict[str, int] = None
    building_progress: Dict[str, float] = None
    
    def __post_init__(self):
        if self.interactions is None:
            self.interactions = []
        if self.decisions is None:
            self.decisions = []
        if self.learned_behaviors is None:
            self.learned_behaviors = []
        if self.relationships is None:
            self.relationships = {}
        if self.territory_knowledge is None:
            self.territory_knowledge = {}
        if self.leader_commands is None:
            self.leader_commands = []
        if self.resources_collected is None:
            self.resources_collected = {'wood': 0, 'stone': 0}
        if self.building_progress is None:
            self.building_progress = {}

@dataclass
class ConversationData:
    """Gespräch-Daten für NLP"""
    speaker_id: str
    message: str
    context: Dict[str, Any]
    timestamp: float
    emotion: str
    importance: float

class TribeTerritory:
    """Stamm-Territorium Management"""
    
    def __init__(self, center_pos: Tuple[float, float], radius: float = 200):
        self.center = pygame.Vector2(center_pos)
        self.radius = radius
        self.zones = self._create_zones()
        self.resources = []
        self.buildings = []
        self.patrol_points = self._create_patrol_points()
        
    def _create_zones(self) -> Dict[str, pygame.Rect]:
        """Erstelle verschiedene Zonen im Territorium"""
        zones = {}
        
        # Zentrale Zone - Meetings und Planung
        zones['center'] = pygame.Rect(
            self.center.x - 30, self.center.y - 30, 60, 60
        )
        
        # Sammel-Zonen
        for i, angle in enumerate([0, 90, 180, 270]):
            rad = math.radians(angle)
            x = self.center.x + math.cos(rad) * (self.radius * 0.7)
            y = self.center.y + math.sin(rad) * (self.radius * 0.7)
            zones[f'gathering_{i}'] = pygame.Rect(x - 25, y - 25, 50, 50)
        
        # Wach-Posten
        for i, angle in enumerate([45, 135, 225, 315]):
            rad = math.radians(angle)
            x = self.center.x + math.cos(rad) * (self.radius * 0.9)
            y = self.center.y + math.sin(rad) * (self.radius * 0.9)
            zones[f'guard_{i}'] = pygame.Rect(x - 15, y - 15, 30, 30)
        
        return zones
    
    def _create_patrol_points(self) -> List[pygame.Vector2]:
        """Erstelle Patrouillenpunkte"""
        points = []
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x = self.center.x + math.cos(rad) * self.radius
            y = self.center.y + math.sin(rad) * self.radius
            points.append(pygame.Vector2(x, y))
        return points
    
    def get_zone_for_action(self, action: ActionType) -> Optional[pygame.Rect]:
        """Hole passende Zone für Aktion"""
        if action == ActionType.PLANNING or action == ActionType.CONVERSATION:
            return self.zones['center']
        elif action == ActionType.GATHERING:
            return random.choice([self.zones[f'gathering_{i}'] for i in range(4)])
        elif action == ActionType.GUARD_DUTY:
            return random.choice([self.zones[f'guard_{i}'] for i in range(4)])
        return self.zones['center']

class NeuralDecisionNetwork:
    """Neuronales Netzwerk für Entscheidungsfindung"""
    
    def __init__(self, input_size: int = 20, hidden_size: int = 64, output_size: int = 11):
        self.model = self._build_model(input_size, hidden_size, output_size)
        self.memory_buffer = []
        self.max_memory = 1000
        
    def _build_model(self, input_size: int, hidden_size: int, output_size: int):
        """Erstelle neuronales Netzwerk"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(hidden_size, activation='relu', input_shape=(input_size,)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(hidden_size // 2, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(output_size, activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def predict_action(self, state_vector: np.ndarray) -> ActionType:
        """Vorhersage der besten Aktion - PERFORMANCE OPTIMIZED"""
        # 🚀 Einfache Hash-basierte Action-Auswahl um TensorFlow Retracing zu vermeiden
        state_hash = hash(tuple(state_vector.round(2)))  # Runde für bessere Cache-Hits
        
        if hasattr(self, '_action_cache') and state_hash in self._action_cache:
            return self._action_cache[state_hash]
        
        if not hasattr(self, '_action_cache'):
            self._action_cache = {}
        
        # Verwende nur alle 10 Updates echte TensorFlow Prediction
        if not hasattr(self, '_tf_call_counter'):
            self._tf_call_counter = 0
            
        self._tf_call_counter += 1
        
        if self._tf_call_counter % 10 == 0:
            # Echte TensorFlow Prediction
            try:
                prediction = self.model.predict(state_vector.reshape(1, -1), verbose=0)
                action_index = np.argmax(prediction[0])
            except:
                # Fallback bei TensorFlow Problemen
                action_index = random.randint(0, self.output_size - 1)
        else:
            # Schnelle Rule-based Action Selection
            action_index = self._rule_based_action(state_vector)
        
        actions = list(ActionType)
        selected_action = actions[action_index % len(actions)]
        
        # Cache Result
        self._action_cache[state_hash] = selected_action
        if len(self._action_cache) > 50:  # Begrenze Cache
            self._action_cache.clear()
            
        return selected_action
    
    def _rule_based_action(self, state_vector: np.ndarray) -> int:
        """Schnelle regelbasierte Aktionsauswahl"""
        # Einfache Heuristiken basierend auf State Vector
        if state_vector[0] > 0.7:  # Hohe Energie
            return random.choice([1, 2, 3])  # Aktive Aktionen
        elif state_vector[1] > 0.6:  # Mittlere Gesundheit  
            return random.choice([4, 5, 6])  # Soziale Aktionen
        else:
            return 0  # Idle
    
    def store_experience(self, state: np.ndarray, action: ActionType, reward: float, next_state: np.ndarray):
        """Speichere Erfahrung für Training"""
        experience = {
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'timestamp': datetime.now()
        }
        
        self.memory_buffer.append(experience)
        if len(self.memory_buffer) > self.max_memory:
            self.memory_buffer.pop(0)
    
    def train_from_experience(self, batch_size: int = 32):
        """Trainiere aus gesammelten Erfahrungen - PERFORMANCE OPTIMIZED"""
        # 🚀 PERFORMANCE: Extrem reduziertes Training
        if len(self.memory_buffer) < 20:
            return
            
        if not hasattr(self, '_training_counter'):
            self._training_counter = 0
            
        self._training_counter += 1
        
        # Training nur alle 200 Aufrufe statt jedes Mal!
        if self._training_counter % 200 != 0:
            return
            
        # Sehr kleine Batch Size
        batch_size = min(batch_size, 3)
        
        try:
            batch = random.sample(self.memory_buffer, batch_size)
            states = np.array([exp['state'] for exp in batch])
            
            # Einfacheres Training ohne komplexe Q-Learning
            targets = []
            for exp in batch:
                target = np.zeros(self.output_size)
                action_idx = list(ActionType).index(exp['action'])
                target[action_idx] = max(0.1, exp['reward'])  # Minimum reward
                targets.append(target)
            
            targets = np.array(targets)
            
            # Minimal Training
            self.model.fit(states, targets, epochs=1, verbose=0, batch_size=1)
        except Exception as e:
            # Silent fail bei TensorFlow Problemen
            pass

class ConversationAI:
    """KI für dynamische Gespräche und NLP"""
    
    def __init__(self):
        self.conversation_history = []
        self.topics = [
            "resource_gathering", "territory_defense", "trading", 
            "weather", "plans", "relationships", "research"
        ]
        self.emotions = ["happy", "worried", "excited", "calm", "angry", "curious"]
        
    def generate_conversation(self, speaker_traits: List[PersonalityTrait], 
                            context: Dict[str, Any]) -> ConversationData:
        """Generiere dynamisches Gespräch basierend auf Kontext"""
        
        # Wähle Thema basierend auf Kontext
        topic = self._select_topic(context)
        emotion = self._determine_emotion(speaker_traits, context)
        
        # Generiere Nachricht basierend auf Persönlichkeit
        message = self._generate_message(speaker_traits, topic, emotion, context)
        
        return ConversationData(
            speaker_id=context.get('speaker_id', 'unknown'),
            message=message,
            context=context,
            timestamp=datetime.now().timestamp(),
            emotion=emotion,
            importance=self._calculate_importance(topic, context)
        )
    
    def _select_topic(self, context: Dict[str, Any]) -> str:
        """Wähle Gesprächsthema basierend auf Kontext"""
        if context.get('recent_action') == ActionType.GATHERING:
            return "resource_gathering"
        elif context.get('threat_level', 0) > 0.5:
            return "territory_defense"
        elif context.get('time_of_day') == 'evening':
            return "plans"
        else:
            return random.choice(self.topics)
    
    def _determine_emotion(self, traits: List[PersonalityTrait], context: Dict[str, Any]) -> str:
        """Bestimme Emotion basierend auf Traits und Kontext"""
        if PersonalityTrait.AGGRESSIVE in traits and context.get('threat_level', 0) > 0.3:
            return "angry"
        elif PersonalityTrait.CURIOUS in traits:
            return "curious"
        elif PersonalityTrait.SOCIAL in traits:
            return "happy"
        else:
            return random.choice(self.emotions)
    
    def _generate_message(self, traits: List[PersonalityTrait], topic: str, 
                         emotion: str, context: Dict[str, Any]) -> str:
        """Generiere Nachricht basierend auf allen Parametern"""
        
        message_templates = {
            "resource_gathering": {
                "happy": "Ich habe heute gute Beeren gefunden! Das Gebiet wird immer fruchtbarer.",
                "worried": "Die Ressourcen werden knapp. Wir sollten neue Gebiete erkunden.",
                "excited": "Ich kenne einen Ort mit viel Holz! Sollen wir hingehen?"
            },
            "territory_defense": {
                "angry": "Fremde sind zu nah gekommen! Wir müssen handeln!",
                "worried": "Unsere Grenzen sind nicht sicher genug...",
                "calm": "Die Patrouillen laufen gut. Alles ist ruhig."
            },
            "plans": {
                "curious": "Was denkst du über den neuen Handelsweg?",
                "excited": "Ich habe eine Idee für unsere Expansion!",
                "calm": "Wir sollten morgen früh mit dem Sammeln beginnen."
            }
        }
        
        if topic in message_templates and emotion in message_templates[topic]:
            return message_templates[topic][emotion]
        else:
            return f"Lass uns über {topic} sprechen. Ich fühle mich {emotion}."
    
    def _calculate_importance(self, topic: str, context: Dict[str, Any]) -> float:
        """Berechne Wichtigkeit der Nachricht"""
        importance_weights = {
            "territory_defense": 1.0,
            "resource_gathering": 0.8,
            "plans": 0.7,
            "trading": 0.6,
            "relationships": 0.5
        }
        
        base_importance = importance_weights.get(topic, 0.3)
        
        # Modifiziere basierend auf Kontext
        if context.get('threat_level', 0) > 0.5:
            base_importance *= 1.5
        
        return min(1.0, base_importance)

class TribeAIMember:
    """Einzelnes Stamm-Mitglied mit fortgeschrittener KI"""
    
    def __init__(self, member_id: str, spawn_pos: Tuple[float, float], 
                 territory: TribeTerritory, sprites=None, is_leader: bool = False, 
                 tribe_color: str = "red"):
        self.member_id = member_id
        self.position = pygame.Vector2(spawn_pos)
        self.territory = territory
        self.sprites = sprites
        self.is_leader = is_leader
        self.tribe_color = tribe_color  # "red", "blue", "green"
        
        # KI-Komponenten
        self.neural_network = NeuralDecisionNetwork()
        self.conversation_ai = ConversationAI()
        self.memory = TribeMemory()
        
        # Anführer-Untertan System
        self.leader_id = None  # ID des Anführers (falls Untertan)
        self.followers = []    # Liste der Untertanen (falls Anführer)
        self.current_command = None  # Aktueller Befehl vom Anführer
        
        # Persönlichkeit (Anführer haben LEADER Trait)
        self.personality = self._generate_personality()
        self.current_action = ActionType.IDLE
        self.target_zone = None
        self.action_timer = 0.0
        self.conversation_cooldown = 0.0
        
        # Zustand für KI
        self.energy = random.uniform(0.7, 1.0)
        self.happiness = random.uniform(0.5, 1.0)
        self.stress = random.uniform(0.0, 0.3)
        self.knowledge_level = random.uniform(0.3, 0.8)
        
        # Job-Spezialisierung für realistische Arbeitsteilung
        self.job_specialization = self._assign_job_specialization()
        self.job_rotation_timer = random.uniform(30.0, 60.0)  # Job wechselt alle 30-60 Sekunden
        self.current_work_efficiency = 1.0  # Effizienz bei aktueller Arbeit
        
        # Rest und Erholungssystem für menschlicheres Verhalten
        self.fatigue = 0.0  # 0.0 = frisch, 1.0 = erschöpft
        self.rest_timer = random.uniform(120.0, 180.0)  # Alle 2-3 Minuten Pause
        self.is_resting = False
        self.rest_duration = 0.0  # Wie lange schon gerastet
        self.work_stamina = random.uniform(0.7, 1.0)  # Arbeitskraft
        
        # 🏠 Haus-System
        self.house = None  # Eigenes Haus (wird erstellt)
        self.assigned_task = None  # Aktueller Auftrag vom Anführer
        self.task_priority = 0  # Wichtigkeit des Auftrags (1-10)
        self.going_to_leader = False  # Gehe zum Anführer für neuen Auftrag
        self.last_leader_visit = 0.0  # Wann zuletzt beim Anführer
        
        # 📦 Ressourcen-Transport System
        self.carrying_resources = {'wood': 0, 'stone': 0}  # Was NPC trägt
        self.going_home = False  # Gehe nach Hause
        self.at_storage = False  # Am Lager angekommen
        
        # Bewegung
        self.velocity = pygame.Vector2(0, 0)
        self.max_speed = random.uniform(50, 80)
        self.direction = 'down'
        
        # Sprite-Animation
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.2
        
        # Ressourcen-bezogene Variablen
        self.current_resource_target = None
        self.carrying_resource = None
        self.resource_capacity = 5
        
        logger.info(f"🧠 {'Anführer' if is_leader else 'Untertan'} {member_id} erstellt - Persönlichkeit: {[p.value for p in self.personality]}")
    
    def _generate_personality(self) -> List[PersonalityTrait]:
        """Generiere zufällige Persönlichkeit"""
        traits = []
        
        # Haupteigenschaft
        main_traits = [PersonalityTrait.AGGRESSIVE, PersonalityTrait.PEACEFUL, 
                      PersonalityTrait.CURIOUS, PersonalityTrait.CONSERVATIVE]
        traits.append(random.choice(main_traits))
        
        # Soziale Eigenschaft
        social_traits = [PersonalityTrait.SOCIAL, PersonalityTrait.SOLITARY]
        traits.append(random.choice(social_traits))
        
        # Führungsqualität - Anführer haben garantiert LEADER Trait
        if self.is_leader:
            traits.append(PersonalityTrait.LEADER)
        else:
            traits.append(PersonalityTrait.FOLLOWER)
        
        return traits
    
    def _assign_job_specialization(self) -> str:
        """Weise jedem NPC eine Arbeitsspezialisierung zu für natürliche Arbeitsteilung"""
        if self.is_leader:
            # Anführer koordinieren meist, arbeiten weniger
            return random.choice(['coordinator', 'builder', 'explorer'])
        
        # Untertanen haben verschiedene Spezialisierungen
        job_types = [
            'wood_cutter',   # Spezialisiert auf Holz
            'miner',         # Spezialisiert auf Stein/Erz
            'builder',       # Spezialisiert auf Hausbau
            'gatherer',      # Sammelt verschiedene Ressourcen
            'guard',         # Bewacht Territorium
        ]
        
        return random.choice(job_types)
    
    def _get_job_efficiency(self, work_type: str) -> float:
        """Berechne Arbeitseffizienz basierend auf Spezialisierung"""
        # Grundeffizienz
        base_efficiency = 1.0
        
        # Bonus für Spezialisierung
        if work_type == 'wood_chopping' and self.job_specialization == 'wood_cutter':
            return base_efficiency * 1.5  # 50% effizienter
        elif work_type == 'stone_mining' and self.job_specialization == 'miner':
            return base_efficiency * 1.4  # 40% effizienter
        elif work_type == 'house_building' and self.job_specialization == 'builder':
            return base_efficiency * 1.6  # 60% effizienter
        
        # Normale Effizienz für nicht-spezialisierte Aufgaben
        return base_efficiency * 0.8  # 20% weniger effizient
    
    def _should_rotate_job(self, dt: float) -> bool:
        """Prüfe ob es Zeit für Jobrotation ist"""
        self.job_rotation_timer -= dt
        
        if self.job_rotation_timer <= 0:
            # Reset timer mit Variation
            self.job_rotation_timer = random.uniform(45.0, 90.0)  # 45-90 Sekunden
            return True
        
        return False
    
    def _choose_action_by_job(self) -> ActionType:
        """Wähle Aktion basierend auf Job-Spezialisierung"""
        # Basis-Aktionen für alle Jobs
        basic_actions = [ActionType.IDLE, ActionType.WANDERING, ActionType.CONVERSATION]
        
        # Job-spezifische Aktionen
        if self.job_specialization == 'wood_cutter':
            return random.choice([ActionType.WOOD_CHOPPING, ActionType.WOOD_CHOPPING, ActionType.IDLE])
        elif self.job_specialization == 'miner':
            return random.choice([ActionType.STONE_MINING, ActionType.STONE_MINING, ActionType.IDLE])
        elif self.job_specialization == 'builder':
            return random.choice([ActionType.HOUSE_BUILDING, ActionType.HOUSE_BUILDING, ActionType.WANDERING])
        elif self.job_specialization == 'gatherer':
            # Sammler mischen verschiedene Aufgaben
            return random.choice([ActionType.WOOD_CHOPPING, ActionType.STONE_MINING, ActionType.WANDERING])
        elif self.job_specialization == 'guard':
            return random.choice([ActionType.WANDERING, ActionType.CONVERSATION, ActionType.IDLE])
        elif self.job_specialization == 'coordinator':
            # Anführer koordinieren mehr als arbeiten
            return random.choice([ActionType.CONVERSATION, ActionType.WANDERING, ActionType.HOUSE_BUILDING])
        elif self.job_specialization == 'explorer':
            return random.choice([ActionType.WANDERING, ActionType.WANDERING, ActionType.CONVERSATION])
        
        # Fallback
        return random.choice(basic_actions)
    
    def _should_visit_leader(self) -> bool:
        """Prüfe ob NPC zum Anführer gehen sollte für neuen Auftrag"""
        if self.is_leader:
            return False  # Anführer gehen nicht zu sich selbst
        
        # Gehe zum Anführer wenn:
        # 1. Kein aktueller Auftrag
        # 2. Aufgabe beendet
        # 3. Lange nicht beim Anführer gewesen (>5 Minuten)
        
        current_time = time.time()
        time_since_visit = current_time - self.last_leader_visit
        
        if (not self.assigned_task or 
            self.assigned_task == "completed" or
            time_since_visit > 300):  # 5 Minuten
            return True
        
        return False
    
    def _go_to_leader(self):
        """Gehe zum Anführer für neuen Auftrag"""
        leader = self._find_leader()
        if leader:
            self.going_to_leader = True
            self._move_to_resource(leader)
            
            # Wenn nah genug am Anführer - hole neuen Auftrag
            distance = self.position.distance_to(leader.position)
            if distance < 80:
                self._request_task_from_leader(leader)
    
    def _request_task_from_leader(self, leader):
        """Bitte Anführer um neuen Auftrag"""
        if not leader.is_leader:
            return
        
        # Anführer analysiert Situation und gibt Auftrag
        task = leader._assign_task_to_follower(self)
        
        if task:
            self.assigned_task = task['type']
            self.task_priority = task['priority']
            self.going_to_leader = False
            self.last_leader_visit = time.time()
            
            logger.info(f"👑 Anführer {leader.member_id} → {self.member_id}: '{task['type']}' (Priorität: {task['priority']})")
        
    def _assign_task_to_follower(self, follower) -> dict:
        """Anführer gibt intelligenten Auftrag an Untertan (SMART LEADER LOGIC)"""
        if not self.is_leader:
            return None
        
        # 🧠 INTELLIGENTE ANFÜHRER-LOGIK - GESTAFFELTES BAUSYSTEM
        tribe_storage = None
        tribe_houses = []
        
        if hasattr(self, '_tribe_system'):
            if self._tribe_system.storage_system:
                tribe_storage = self._tribe_system.storage_system.get_storage(self.tribe_color)
            if self._tribe_system.house_system:
                tribe_houses = self._tribe_system.house_system.get_tribe_houses(self.tribe_color)
        
        # 🏗️ NEUES FEATURE: Gestaffeltes Bausystem (maximal 5 Baustellen)
        active_construction_sites = 0
        if hasattr(self, '_tribe_system'):
            tribe_members = [m for m in self._tribe_system.members if m.tribe_color == self.tribe_color]
            
            # Zähle aktive Baustellen
            for member in tribe_members:
                if (member.house and not member.house.built and 
                    member.house.build_progress > 0.0):
                    active_construction_sites += 1
        
        # Prioritäten analysieren:
        tasks = []
        
        # 1. HÄUSER BAUEN (höchste Priorität, aber gestaffelt)
        tribe_members = [m for m in self._tribe_system.members if m.tribe_color == self.tribe_color]
        homeless_count = 0
        next_homeless_member = None
        
        for member in tribe_members:
            if not member.house or not member.house.built:
                homeless_count += 1
                if not next_homeless_member and (not member.house or member.house.build_progress == 0.0):
                    next_homeless_member = member
        
        # 🏗️ GESTAFFELTES BAUSYSTEM: Nur neue Baustelle wenn < 5 aktive
        if homeless_count > 0 and active_construction_sites < 5:
            if next_homeless_member and not next_homeless_member.house:
                # Erstelle neue Baustelle nur wenn Platz frei
                house = self._tribe_system.house_system.build_house_for_npc(
                    next_homeless_member.member_id, self.tribe_color)
                next_homeless_member.house = house
                active_construction_sites += 1
                
                # Log für Debugging
                if random.random() < 0.1:  # 10% chance to log
                    logger.info(f"🏗️ {self.tribe_color.upper()} Anführer: Neue Baustelle #{active_construction_sites}/5 für {next_homeless_member.member_id}")
        
        # Arbeite an bestehenden Baustellen
        if homeless_count > 0:
            # Erstelle Haus für obdachlosen NPC (falls schon Baustelle existiert)
            if not follower.house:
                # Suche bestehende Baustelle für diesen Follower
                existing_houses = self._tribe_system.house_system.get_tribe_houses(self.tribe_color)
                unassigned_house = None
                for house in existing_houses:
                    if house.owner_id == follower.member_id:
                        unassigned_house = house
                        break
                
                if unassigned_house:
                    follower.house = unassigned_house
            
            # Prüfe was das Haus braucht
            if follower.house and not follower.house.built:
                requirements = follower.house.get_build_requirements()
                if requirements['wood'] > 0:
                    tasks.append({'type': 'collect_wood', 'priority': 9, 'reason': f'Haus braucht {requirements["wood"]} Holz'})
                if requirements['stone'] > 0:
                    tasks.append({'type': 'collect_stone', 'priority': 9, 'reason': f'Haus braucht {requirements["stone"]} Stein'})
                if requirements['wood'] == 0 and requirements['stone'] == 0:
                    tasks.append({'type': 'build_house', 'priority': 10, 'reason': 'Ressourcen verfügbar - baue Haus'})
        
        # Anführer Status-Update (gelegentlich)
        if random.random() < 0.05:  # 5% chance
            logger.info(f"👑 {self.tribe_color.upper()} Anführer Status: {active_construction_sites}/5 Baustellen aktiv, {homeless_count} obdachlos")
        
        # 2. LAGER-MANAGEMENT (mittlere Priorität)
        if tribe_storage:
            resources = tribe_storage.get_total_resources()
            
            # Zu wenig Holz im Lager
            if resources.get('wood', 0) < 20:
                tasks.append({'type': 'collect_wood', 'priority': 6, 'reason': 'Lager braucht mehr Holz'})
            
            # Zu wenig Stein im Lager  
            if resources.get('stone', 0) < 15:
                tasks.append({'type': 'collect_stone', 'priority': 7, 'reason': 'Lager braucht mehr Stein'})
        
        # 3. SPEZIALISIERTEN JOB FORTSETZEN (niedrige Priorität)
        if follower.job_specialization == 'wood_cutter':
            tasks.append({'type': 'collect_wood', 'priority': 3, 'reason': 'Spezialisierung: Holzfäller'})
        elif follower.job_specialization == 'miner':
            tasks.append({'type': 'collect_stone', 'priority': 3, 'reason': 'Spezialisierung: Bergarbeiter'})
        elif follower.job_specialization == 'builder':
            tasks.append({'type': 'build_house', 'priority': 4, 'reason': 'Spezialisierung: Bauarbeiter'})
        
        # 4. PAUSE/SOCIAL (niedrigste Priorität)
        tasks.append({'type': 'rest', 'priority': 1, 'reason': 'Erholung'})
        
        # Wähle Aufgabe mit höchster Priorität
        if tasks:
            best_task = max(tasks, key=lambda t: t['priority'])
            logger.info(f"🧠 Anführer {self.member_id} Analyse: {best_task['reason']} → {best_task['type']}")
            return best_task
        
        return {'type': 'rest', 'priority': 1, 'reason': 'Nichts zu tun'}
    
    def _should_go_home(self) -> bool:
        """Prüfe ob NPC nach Hause gehen sollte"""
        # Gehe nach Hause wenn:
        # 1. Für Pause (wenn müde)
        # 2. Ressourcen ins Lager bringen
        # 3. Schlafen (wenn sehr müde)
        
        carrying_total = sum(self.carrying_resources.values())
        
        if carrying_total >= 10:  # Volles Inventar
            return True
        
        if self.fatigue > 0.8:  # Sehr müde
            return True
        
        # Zufällig alle paar Minuten
        if random.random() < 0.01:  # 1% Chance pro Update
            return True
        
        return False
    
    def _go_home(self):
        """Gehe nach Hause oder zum Lager"""
        if self.is_resting and self.house and self.house.built:
            # Für Pause: Gehe zum eigenen Haus
            self.going_home = True
            house_center = (self.house.position.x + self.house.size[0]//2, 
                          self.house.position.y + self.house.size[1]//2)
            target_pos = pygame.Vector2(house_center)
            
            # Bewege zum Haus
            direction = target_pos - self.position
            if direction.length() > 0:
                direction = direction.normalize()
                self.velocity = direction * self.max_speed * 0.8  # Etwas langsamer nach Hause
            
            # Angekommen am Haus
            if self.position.distance_to(target_pos) < 40:
                self.going_home = False
                logger.info(f"🏠 {self.member_id} ist zu Hause angekommen")
                
        elif sum(self.carrying_resources.values()) > 0:
            # Für Ressourcen: Gehe zum Lager
            if hasattr(self, '_tribe_system') and self._tribe_system.storage_system:
                storage = self._tribe_system.storage_system.get_storage(self.tribe_color)
                if storage:
                    self.going_home = True
                    storage_center = (storage.position.x + storage.size[0]//2,
                                    storage.position.y + storage.size[1]//2)
                    target_pos = pygame.Vector2(storage_center)
                    
                    # Bewege zum Lager
                    direction = target_pos - self.position
                    if direction.length() > 0:
                        direction = direction.normalize()
                        self.velocity = direction * self.max_speed
                    
                    # Angekommen am Lager
                    if self.position.distance_to(target_pos) < 50:
                        self._deposit_resources_at_storage(storage)
                        self.going_home = False
                        self.at_storage = True
    
    def _deposit_resources_at_storage(self, storage):
        """Bringe Ressourcen zum Lager"""
        for resource_type, amount in self.carrying_resources.items():
            if amount > 0:
                storage.add_resources(resource_type, amount)
                self.carrying_resources[resource_type] = 0
                logger.info(f"📦 {self.member_id} bringt {amount} {resource_type} zum Lager")
    
    def _collect_resource(self, resource_type: str, amount: int):
        """Sammle Ressource (wird von Arbeits-Aktionen aufgerufen)"""
        self.carrying_resources[resource_type] += amount
        logger.info(f"🎒 {self.member_id} trägt jetzt {self.carrying_resources[resource_type]} {resource_type}")
    
    def _needs_rest(self) -> bool:
        """Prüfe ob NPC eine Pause braucht"""
        # Erschöpfung basierend auf Arbeit und Zeit
        if self.fatigue > 0.7:  # Sehr müde
            return True
        
        # Zeit-basierte Pausen
        if self.rest_timer <= 0:
            return True
            
        # Stress-basierte Pausen
        if self.stress > 0.6 and random.random() < 0.3:
            return True
            
        return False
    
    def _start_resting(self):
        """Beginne Ruhepause"""
        self.is_resting = True
        self.rest_duration = 0.0
        self.rest_timer = random.uniform(180.0, 300.0)  # 3-5 Minuten bis zur nächsten Pause
        
        if self.is_leader:
            logger.info(f"😴 Anführer {self.member_id} ({self.job_specialization}) macht Pause")
        else:
            logger.info(f"😴 Untertan {self.member_id} ({self.job_specialization}) macht Pause")
    
    def _handle_resting(self, dt: float):
        """Verwalte Ruhepause"""
        self.rest_duration += dt
        
        # Erholung während der Pause
        recovery_rate = 0.3 * dt  # 30% Erholung pro Sekunde
        self.fatigue = max(0.0, self.fatigue - recovery_rate)
        self.stress = max(0.0, self.stress - recovery_rate * 0.5)
        self.energy = min(1.0, self.energy + recovery_rate * 0.2)
        self.happiness = min(1.0, self.happiness + recovery_rate * 0.1)
        
        # Pause beenden nach 10-20 Sekunden
        rest_needed = random.uniform(10.0, 20.0)
        if self.rest_duration >= rest_needed or self.fatigue <= 0.1:
            self.is_resting = False
            self.rest_duration = 0.0
            
            if self.is_leader:
                logger.info(f"🏃 Anführer {self.member_id} ist ausgeruht und arbeitet wieder")
            else:
                logger.info(f"🏃 Untertan {self.member_id} ist ausgeruht und arbeitet wieder")
    
    def _add_work_fatigue(self, work_intensity: float = 0.1):
        """Füge Erschöpfung nach Arbeit hinzu"""
        # Erschöpfung basierend auf Arbeitsintensität und Spezialisierung
        base_fatigue = work_intensity
        
        # Spezialisten werden bei ihrer Arbeit weniger müde
        current_action = self.current_action
        if ((current_action == ActionType.WOOD_CHOPPING and self.job_specialization == 'wood_cutter') or
            (current_action == ActionType.STONE_MINING and self.job_specialization == 'miner') or
            (current_action == ActionType.HOUSE_BUILDING and self.job_specialization == 'builder')):
            base_fatigue *= 0.7  # 30% weniger Erschöpfung bei Spezialisierung
        
        self.fatigue = min(1.0, self.fatigue + base_fatigue)
        self.work_stamina = max(0.1, self.work_stamina - base_fatigue * 0.5)
    
    def get_state_vector(self, nearby_members: List, world_state: Dict[str, Any]) -> np.ndarray:
        """Erstelle Zustandsvektor für neuronales Netzwerk"""
        state = []
        
        # Eigener Zustand
        state.extend([self.energy, self.happiness, self.stress, self.knowledge_level])
        
        # Position relativ zum Territorium-Zentrum
        rel_pos = self.position - self.territory.center
        state.extend([rel_pos.x / self.territory.radius, rel_pos.y / self.territory.radius])
        
        # Anzahl Nachbarn
        state.append(len(nearby_members) / 10.0)  # Normalisiert
        
        # Zeit-basierte Features
        state.extend([
            world_state.get('time_of_day', 0.5),
            world_state.get('weather', 0.5),
            world_state.get('season', 0.5)
        ])
        
        # Persönlichkeits-Encoding
        personality_vector = [0.0] * len(PersonalityTrait)
        for trait in self.personality:
            personality_vector[list(PersonalityTrait).index(trait)] = 1.0
        state.extend(personality_vector[:8])  # Nehme nur erste 8 für Vektorgröße
        
        # Padding auf feste Größe (20)
        while len(state) < 20:
            state.append(0.0)
        
        return np.array(state[:20], dtype=np.float32)
    
    def update_ai(self, dt: float, nearby_members: List, world_state: Dict[str, Any]):
        """Hauptupdate für KI-Verhalten"""
        # 🚀 PERFORMANCE FIX: AI Update Throttling - WENIGER HÄUFIG
        if not hasattr(self, 'last_ai_update'):
            self.last_ai_update = 0
            self.ai_update_interval = random.uniform(2.0, 4.0)  # Viel weniger häufig für Performance
        
        current_time = time.time()
        should_update_ai = (current_time - self.last_ai_update) > self.ai_update_interval
        
        self.action_timer += dt
        self.conversation_cooldown = max(0, self.conversation_cooldown - dt)
        
        # Rest-System: Verwalte Pausen und Erschöpfung
        self.rest_timer -= dt
        
        # Wenn ruhend, führe Ruheverhalten aus
        if self.is_resting:
            self._handle_resting(dt)
            # Während der Pause: Idle-Verhalten oder Wandern
            if self.current_action not in [ActionType.IDLE, ActionType.WANDERING, ActionType.CONVERSATION]:
                self._change_action(ActionType.IDLE)
            return  # Früher Ausstieg - keine anderen Aktionen während Pause
        
        # Prüfe ob Pause nötig ist
        if self._needs_rest():
            self._start_resting()
            self._change_action(ActionType.IDLE)
            return  # Beginne sofort mit der Pause
        
        # 🏠 HEIMKEHR-SYSTEM: NPCs gehen nach Hause für Pausen oder Lager
        if self._should_go_home():
            self._go_home()
            return  # Gehe nach Hause, keine anderen Aktionen
        
        # 👑 KOMMANDO-SYSTEM: NPCs gehen zu Anführer für Aufträge
        if not self.is_leader and self._should_visit_leader():
            self._go_to_leader()
            return  # Gehe zum Anführer, keine anderen Aktionen
        
        # Hole aktuellen Zustand
        state_vector = self.get_state_vector(nearby_members, world_state)
        
        # Entscheide neue Aktion falls nötig - ABER NUR ALLE 0.5-1s!
        if should_update_ai and (self.action_timer > 5.0 or self.current_action == ActionType.IDLE):
            # 🎯 NEUES SYSTEM: Untertanen führen assigned_tasks aus
            if not self.is_leader and self.assigned_task:
                if self.assigned_task == 'collect_wood':
                    new_action = ActionType.WOOD_CHOPPING
                elif self.assigned_task == 'collect_stone':
                    new_action = ActionType.STONE_MINING
                elif self.assigned_task == 'build_house':
                    new_action = ActionType.HOUSE_BUILDING
                elif self.assigned_task == 'rest':
                    new_action = ActionType.IDLE
                else:
                    new_action = ActionType.WANDERING  # Fallback
            # Untertanen ohne Aufträge warten oder suchen Anführer
            elif not self.is_leader and not self.assigned_task:
                new_action = ActionType.WANDERING  # Suche Anführer
            else:
                # Anführer verwenden Neural Network, aber berücksichtigen Job-Spezialisierung
                self.last_ai_update = current_time
                old_state = state_vector.copy()
                
                # Prüfe Jobrotation
                if self._should_rotate_job(dt):
                    # Job-basierte Entscheidung (60% der Zeit)
                    if random.random() < 0.6:
                        new_action = self._choose_action_by_job()
                    else:
                        # KI-Entscheidung für Anführer
                        new_action = self.neural_network.predict_action(state_vector)
                else:
                    # Bleibe bei aktueller Spezialisierung wenn noch nicht Zeit zum Wechseln
                    if random.random() < 0.8:  # 80% der Zeit Job-fokussiert bleiben
                        new_action = self._choose_action_by_job()
                    else:
                        new_action = self.neural_network.predict_action(state_vector)
                
                # Belohnung für vorherige Aktion berechnen
                reward = self._calculate_reward(world_state)
                
                # Erfahrung speichern (begrenzt auf 100 Einträge)
                if hasattr(self, '_last_state') and len(self.neural_network.memory_buffer) < 100:
                    self.neural_network.store_experience(
                        self._last_state, self.current_action, reward, state_vector
                    )
                
                self._last_state = old_state
            
            self._change_action(new_action)
            self.action_timer = 0.0
        
        # Führe aktuelle Aktion aus
        self._execute_current_action(dt, nearby_members, world_state)
        
        # Gelegentliches Training
        if random.random() < 0.01:  # 1% Chance pro Update
            self.neural_network.train_from_experience()
    
    def _calculate_reward(self, world_state: Dict[str, Any]) -> float:
        """Berechne Belohnung für Reinforcement Learning"""
        reward = 0.0
        
        # Grundbelohnung für Energie und Glück
        reward += self.energy * 0.3
        reward += self.happiness * 0.3
        reward -= self.stress * 0.2
        
        # Aktions-spezifische Belohnungen
        if self.current_action == ActionType.GATHERING and world_state.get('resources_collected', 0) > 0:
            reward += 1.0
        elif self.current_action == ActionType.GUARD_DUTY and world_state.get('territory_safe', True):
            reward += 0.5
        elif self.current_action == ActionType.CONVERSATION and len(self.memory.interactions) > 0:
            reward += 0.3
        
        # Territorium-Belohnung
        dist_to_center = self.position.distance_to(self.territory.center)
        if dist_to_center < self.territory.radius:
            reward += 0.2
        else:
            reward -= 0.5  # Strafe für verlassen des Territoriums
        
        return np.clip(reward, -1.0, 2.0)
    
    def _change_action(self, new_action: ActionType):
        """Wechsle zu neuer Aktion"""
        self.current_action = new_action
        # DEAKTIVIERE target_zone für natürliche Bewegung - keine erzwungenen Zonen
        # self.target_zone = self.territory.get_zone_for_action(new_action)
        self.target_zone = None
        
        # Log der Entscheidung
        self.memory.decisions.append({
            'action': new_action.value,
            'timestamp': datetime.now().timestamp(),
            'reason': 'ai_decision'
        })
        
        logger.info(f"🎯 {self.member_id}: Neue Aktion - {new_action.value}")
    
    def _execute_current_action(self, dt: float, nearby_members: List, world_state: Dict[str, Any]):
        """Führe aktuelle Aktion aus"""
        
        if self.current_action == ActionType.CONVERSATION and self.conversation_cooldown <= 0:
            self._handle_conversation(nearby_members, world_state)
        
        elif self.current_action == ActionType.GATHERING:
            self._handle_gathering(world_state)
        
        elif self.current_action == ActionType.PLANNING:
            self._handle_planning(world_state)
        
        elif self.current_action == ActionType.GUARD_DUTY:
            self._handle_guard_duty(world_state)
        
        elif self.current_action == ActionType.COMMAND_FOLLOWERS:
            self._handle_command_followers(world_state)
        
        # ENTFERNT: FOLLOW_LEADER wird nicht mehr verwendet
        # elif self.current_action == ActionType.FOLLOW_LEADER:
        #     self._handle_follow_leader(world_state)
            
        elif self.current_action == ActionType.WOOD_CHOPPING:
            self._handle_wood_chopping(world_state)
            
        elif self.current_action == ActionType.STONE_MINING:
            self._handle_stone_mining(world_state)
            
        elif self.current_action == ActionType.HOUSE_BUILDING:
            self._handle_house_building(world_state)
            
        elif self.current_action == ActionType.WANDERING:
            self._handle_wandering(world_state)
        
        # DEAKTIVIERT: Bewege zu Ziel-Zone (für natürliche Bewegung)
        # if self.target_zone:
        #     self._move_to_zone(dt, self.target_zone)
    
    def _handle_conversation(self, nearby_members: List, world_state: Dict[str, Any]):
        """Führe Gespräch mit anderen Mitgliedern"""
        if not nearby_members:
            return
        
        # Wähle Gesprächspartner
        partner = min(nearby_members, key=lambda m: self.position.distance_to(m.position))
        
        if self.position.distance_to(partner.position) < 50:
            # Generiere Gespräch
            context = {
                'speaker_id': self.member_id,
                'partner_id': partner.member_id,
                'recent_action': self.current_action,
                'threat_level': world_state.get('threat_level', 0),
                'time_of_day': world_state.get('time_of_day', 'day')
            }
            
            conversation = self.conversation_ai.generate_conversation(
                self.personality, context
            )
            
            # Speichere Interaktion
            self.memory.interactions.append(asdict(conversation))
            
            # Beziehung verstärken
            if partner.member_id not in self.memory.relationships:
                self.memory.relationships[partner.member_id] = 0.0
            
            self.memory.relationships[partner.member_id] += 0.1
            self.conversation_cooldown = 10.0  # 10 Sekunden Cooldown
            
            logger.info(f"💬 {self.member_id} → {partner.member_id}: {conversation.message}")
    
    def _handle_gathering(self, world_state: Dict[str, Any]):
        """Ressourcen sammeln"""
        # Simuliere Ressourcen-Sammlung
        if random.random() < 0.1:  # 10% Chance pro Update
            world_state['resources_collected'] = world_state.get('resources_collected', 0) + 1
            self.knowledge_level = min(1.0, self.knowledge_level + 0.01)
            self.energy = max(0.1, self.energy - 0.05)
    
    def _handle_planning(self, world_state: Dict[str, Any]):
        """Strategische Planung"""
        self.knowledge_level = min(1.0, self.knowledge_level + 0.02)
        self.stress = max(0.0, self.stress - 0.01)
    
    def _handle_guard_duty(self, world_state: Dict[str, Any]):
        """Territorium bewachen"""
        world_state['territory_safe'] = True
        self.stress = min(1.0, self.stress + 0.01)
    
    def _handle_command_followers(self, world_state: Dict[str, Any]):
        """Anführer gibt Befehle an Untertanen"""
        if not self.is_leader or not self.followers:
            return
            
        # Intelligente Task-Auswahl basierend auf Stammes-Bedürfnissen
        if hasattr(self, '_tribe_system'):
            own_tribe_members = [m for m in self._tribe_system.members if m.tribe_color == self.tribe_color]
            total_wood = sum(m.memory.resources_collected['wood'] for m in own_tribe_members)
            total_stone = sum(m.memory.resources_collected['stone'] for m in own_tribe_members)
            
            # Intelligente Entscheidung
            if self.tribe_color == 'red' and total_wood < 30:
                current_task = 'wood_chopping'  # Rotes Volk braucht viel Holz
            elif self.tribe_color == 'green' and total_stone < 40:
                current_task = 'stone_mining'   # Grünes Volk braucht viel Stein
            elif self.tribe_color == 'blue' and (total_wood < 40 or total_stone < 25):
                current_task = 'wood_chopping' if total_wood < total_stone else 'stone_mining'
            elif total_wood >= 20 and total_stone >= 15:  # Genug für Hausbau
                current_task = 'house_building'
            else:
                # Standard: Sammle was fehlt
                current_task = 'wood_chopping' if total_wood < total_stone else 'stone_mining'
        else:
            # Fallback
            tasks = ['wood_chopping', 'stone_mining', 'house_building']
            current_task = random.choice(tasks)
        
        # Gib Befehl an alle Untertanen
        for follower in self.followers:
            if follower and hasattr(follower, 'receive_command'):
                follower.receive_command(current_task, self.member_id)
        
        # Log der Befehlsgebung
        self.memory.leader_commands.append({
            'command': current_task,
            'timestamp': time.time(),
            'followers_count': len(self.followers)
        })
        
        logger.info(f"👑 Anführer {self.member_id} befiehlt: {current_task} ({len(self.followers)} Untertanen)")
    
    # ENTFERNT: _handle_follow_leader - wird nicht mehr verwendet
    # Die Befehlslogik ist jetzt in update_ai() integriert
    
    def _handle_wood_chopping(self, world_state: Dict[str, Any]):
        """Aktive Holzsuche und -abbau mit realistischen Arbeitszeiten"""
        # AKTIVE SUCHE: Finde und gehe zu Bäumen
        if hasattr(self, '_tribe_system') and hasattr(self._tribe_system, 'tree_system'):
            target_tree = self._find_nearest_resource('wood')
            
            if target_tree:
                # Gehe zum Baum
                self._move_to_resource(target_tree)
                
                # Baue ab wenn nah genug - REALISTISCH LANGSAM
                distance = abs(target_tree.x - self.position.x) + abs(target_tree.y - self.position.y)
                if distance < 60:
                    # Arbeits-Timer für realistische Geschwindigkeit
                    if not hasattr(self, '_work_timer'):
                        self._work_timer = 0
                    
                    self._work_timer += 0.016  # dt (~60fps)
                    
                    # Arbeitsintervall basierend auf Spezialisierung
                    efficiency = self._get_job_efficiency('wood_chopping')
                    base_interval = random.uniform(2.0, 3.5)
                    work_interval = base_interval / efficiency  # Höhere Effizienz = schneller
                    
                    if self._work_timer >= work_interval:
                        # Reset timer für nächsten Schlag
                        self._work_timer = 0
                        
                        # Schade dem Baum (simuliere Angriff)
                        wood_pos = target_tree.take_damage(25)  # Standard Schaden
                        self._add_work_fatigue(0.08)  # Arbeit macht müde
                        
                        if wood_pos:  # Baum wurde gefällt
                            wood_collected = random.randint(3, 6)  # Holz erhalten
                            self._collect_resource('wood', wood_collected)  # 📦 NEUES SYSTEM
                            self.energy = max(0.1, self.energy - 0.05)
                            
                            if self.is_leader:
                                logger.info(f"🪓 Anführer {self.member_id} fällt Baum (+{wood_collected} Holz)")
                            else:
                                logger.info(f"🪓 Untertan {self.member_id} fällt Baum (+{wood_collected} Holz)")
                                
                            # Nach dem Fällen: Suche neuen Baum oder mache Pause
                            self._set_goal('find_wood')
                        else:
                            # Baum nur beschädigt, weitermachen
                            if self.is_leader:
                                logger.info(f"🪓 Anführer {self.member_id} schlägt Baum (HP: {target_tree.current_hp})")
                            else:
                                logger.info(f"🪓 Untertan {self.member_id} schlägt Baum (HP: {target_tree.current_hp})")
                    elif target_tree.alive:
                        # Baum nur beschädigt, nicht gefällt
                        self.energy = max(0.1, self.energy - 0.01)
            else:
                # Kein Baum gefunden - suche in größerem Radius oder wechsle Aufgabe
                if not self.is_leader:
                    self._wander_to_find_resources('wood')
        
        # Fallback: Simuliere Holz sammeln wenn keine echten Bäume
        elif random.random() < 0.05:  # Niedrigere Rate für virtuelles Holz
            wood_collected = random.randint(1, 2)
            self.memory.resources_collected['wood'] += wood_collected
            world_state['resources_collected'] = world_state.get('resources_collected', 0) + wood_collected
            self.energy = max(0.1, self.energy - 0.02)
            
            if self.is_leader:
                logger.info(f"🪓 Anführer {self.member_id} sammelt Holz (+{wood_collected})")
            else:
                logger.info(f"🪓 Untertan {self.member_id} sammelt Holz (+{wood_collected})")
    
    def _handle_stone_mining(self, world_state: Dict[str, Any]):
        """Aktive Steinsuche und -abbau mit realistischen Arbeitszeiten"""
        # AKTIVE SUCHE: Finde und gehe zu Steinen/Erzen
        if hasattr(self, '_tribe_system') and hasattr(self._tribe_system, 'mining_system'):
            target_resource = self._find_nearest_resource('stone')
            
            if target_resource:
                # Gehe zur Ressource
                self._move_to_resource(target_resource)
                
                # Baue ab wenn nah genug - REALISTISCH LANGSAM
                distance = abs(target_resource.x - self.position.x) + abs(target_resource.y - self.position.y)
                if distance < 60:
                    # Arbeits-Timer für realistische Geschwindigkeit (getrennt vom wood_timer)
                    if not hasattr(self, '_mining_timer'):
                        self._mining_timer = 0
                    
                    self._mining_timer += 0.016  # dt (~60fps)
                    
                    # Arbeitsintervall basierend auf Spezialisierung
                    efficiency = self._get_job_efficiency('stone_mining')
                    base_interval = random.uniform(3.0, 4.5)  # Steinabbau dauert länger als Holz
                    mining_interval = base_interval / efficiency  # Höhere Effizienz = schneller
                    
                    if self._mining_timer >= mining_interval:
                        # Reset timer für nächsten Schlag
                        self._mining_timer = 0
                        
                        # Schade der Ressource (simuliere Angriff)
                        depleted, drop_pos = target_resource.take_damage(1)  # 1 Schaden pro Schlag
                        self._add_work_fatigue(0.12)  # Bergbau ist anstrengender als Holzfällen
                        
                        if depleted or drop_pos:  # Ressource vollständig abgebaut oder Drop erhalten
                            stone_collected = random.randint(1, 3)  # Stein/Erz erhalten
                            self._collect_resource('stone', stone_collected)  # 📦 NEUES SYSTEM
                            self.energy = max(0.1, self.energy - 0.06)
                            
                            if self.is_leader:
                                logger.info(f"⛏️ Anführer {self.member_id} baut {target_resource.resource_type} ab (+{stone_collected})")
                            else:
                                logger.info(f"⛏️ Untertan {self.member_id} baut {target_resource.resource_type} ab (+{stone_collected})")
                            
                            # Nach dem Abbau: Suche neue Ressource oder mache Pause
                            self._set_goal('find_stone')
                        elif target_resource.alive:
                            # Ressource nur beschädigt, nicht abgebaut
                            if self.is_leader:
                                logger.info(f"⛏️ Anführer {self.member_id} schlägt {target_resource.resource_type} (HP: {target_resource.current_hp})")
                            else:
                                logger.info(f"⛏️ Untertan {self.member_id} schlägt {target_resource.resource_type} (HP: {target_resource.current_hp})")
                        self.energy = max(0.1, self.energy - 0.02)
            else:
                # Keine Ressource gefunden - erkunde umher
                if not self.is_leader:
                    self._wander_to_find_resources('stone')
        
        # Fallback: Simuliere Stein sammeln wenn keine echten Ressourcen
        elif random.random() < 0.03:  # Niedrigere Rate für virtuellen Stein
            stone_collected = random.randint(1, 2)
            self.memory.resources_collected['stone'] += stone_collected
            world_state['resources_collected'] = world_state.get('resources_collected', 0) + stone_collected
            self.energy = max(0.1, self.energy - 0.04)
            
            if self.is_leader:
                logger.info(f"⛏️ Anführer {self.member_id} sammelt Stein (+{stone_collected})")
            else:
                logger.info(f"⛏️ Untertan {self.member_id} sammelt Stein (+{stone_collected})")
    
    def _handle_wandering(self, world_state: Dict[str, Any]):
        """Natürliche Schwarmbewegung - keine Formation"""
        if not self.is_leader and self.leader_id:
            # Untertanen folgen ihrem Anführer mit natürlicher Schwarmbewegung
            leader = self._find_leader()
            if leader:
                self._follow_leader_naturally(leader, world_state)
            else:
                # Fallback: kleine zufällige Bewegung
                self._random_small_movement()
        else:
            # Anführer bewegen sich frei und langsam
            self._leader_free_movement()
    
    def _follow_leader_naturally(self, leader, world_state: Dict[str, Any]):
        """Natürliche Schwarmbewegung um Anführer - keine Formation"""
        leader_pos = leader.position
        current_pos = self.position
        
        # Berechne gewünschten Abstand zum Anführer (variabel pro Untertan)
        if not hasattr(self, '_preferred_distance'):
            self._preferred_distance = random.uniform(40, 120)  # Jeder hat seinen eigenen Abstand
        if not hasattr(self, '_preferred_angle_offset'):
            self._preferred_angle_offset = random.uniform(0, 2 * math.pi)
        
        # Aktuelle Entfernung zum Anführer
        distance_to_leader = current_pos.distance_to(leader_pos)
        
        # Verhalten basierend auf Entfernung
        if distance_to_leader > self._preferred_distance + 50:
            # Zu weit weg - näher zum Anführer bewegen
            direction = (leader_pos - current_pos).normalize()
            self.velocity = direction * self.max_speed * 0.8
        elif distance_to_leader < self._preferred_distance - 20:
            # Zu nah - etwas wegbewegen
            direction = (current_pos - leader_pos).normalize()
            self.velocity = direction * self.max_speed * 0.3
        else:
            # Gute Entfernung - langsam mitbewegen oder idle
            if leader.velocity.length() > 5:  # Anführer bewegt sich
                # Folge in gleiche Richtung aber mit Variation
                follow_direction = leader.velocity.normalize()
                # Füge etwas zufällige Variation hinzu
                angle_variation = random.uniform(-0.5, 0.5)
                rotated_direction = follow_direction.rotate(math.degrees(angle_variation))
                self.velocity = rotated_direction * self.max_speed * 0.5
            else:
                # Anführer steht - kleine zufällige Bewegung
                self._random_small_movement()
        
        # Vermeide Kollisionen mit anderen Untertanen
        self._avoid_other_followers(world_state)
        
        # Bewege Position
        if self.velocity.length() > 0:
            self.position += self.velocity * 0.016
            self._update_sprite_direction()
    
    def _avoid_other_followers(self, world_state: Dict[str, Any]):
        """Vermeide Kollisionen mit anderen Untertanen"""
        if not hasattr(self, '_tribe_system'):
            return
            
        nearby_followers = []
        for member in self._tribe_system.members:
            if (member != self and not member.is_leader and 
                self.position.distance_to(member.position) < 60):
                nearby_followers.append(member)
        
        if nearby_followers:
            # Berechne Ausweichrichtung
            avoidance_vector = pygame.Vector2(0, 0)
            for follower in nearby_followers:
                diff = self.position - follower.position
                if diff.length() > 0:
                    avoidance_vector += diff.normalize() / (diff.length() + 1)
            
            if avoidance_vector.length() > 0:
                avoidance_vector = avoidance_vector.normalize()
                self.velocity += avoidance_vector * 20  # Sanfte Korrektur
    
    def _leader_free_movement(self):
        """Anführer bewegt sich frei und langsam"""
        # Wähle neues Ziel alle 5-10 Sekunden
        if not hasattr(self, '_movement_timer'):
            self._movement_timer = 0
        
        self._movement_timer += 0.016
        
        if self._movement_timer > random.uniform(3, 8):
            self._movement_timer = 0
            
            # Neues Ziel in der Nähe
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(80, 200)
            target_x = self.position.x + math.cos(angle) * distance
            target_y = self.position.y + math.sin(angle) * distance
            
            # Begrenze auf Territorium
            territory_center = pygame.Vector2(self.territory.center)
            target_pos = pygame.Vector2(target_x, target_y)
            
            if territory_center.distance_to(target_pos) > self.territory.radius:
                direction = (territory_center - target_pos).normalize()
                target_pos = territory_center + direction * self.territory.radius * 0.8
            
            # Bewege langsam zum Ziel
            direction = (target_pos - self.position)
            if direction.length() > 10:
                direction = direction.normalize()
                self.velocity = direction * self.max_speed * 0.4  # Langsame Bewegung
            else:
                self.velocity = pygame.Vector2(0, 0)
        
        # Bewege Position
        if self.velocity.length() > 0:
            self.position += self.velocity * 0.016
            self._update_sprite_direction()
        else:
            # Stoppe nach einer Weile
            self.velocity = pygame.Vector2(0, 0)
    
    def _random_small_movement(self):
        """Kleine zufällige Bewegung"""
        if random.random() < 0.05:  # 5% Chance
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(10, 30)
            direction = pygame.Vector2(math.cos(angle), math.sin(angle))
            self.velocity = direction * self.max_speed * 0.2
            
            if self.velocity.length() > 0:
                self.position += self.velocity * 0.016
                self._update_sprite_direction()
    
    def _find_nearest_resource(self, resource_type: str):
        """Finde nächste verfügbare Ressource mit Arbeitsplatz-Management"""
        if not hasattr(self, '_tribe_system'):
            return None
        
        nearest_resource = None
        min_distance = 800  # Großer Suchradius
        available_resources = []
        
        if resource_type == 'wood' and hasattr(self._tribe_system, 'tree_system'):
            for tree in self._tribe_system.tree_system.trees:
                if tree.alive:
                    distance = abs(tree.x - self.position.x) + abs(tree.y - self.position.y)
                    if distance < min_distance:
                        available_resources.append((tree, distance))
        
        elif resource_type == 'stone' and hasattr(self._tribe_system, 'mining_system'):
            for resource in self._tribe_system.mining_system.resources:
                if resource.alive:
                    distance = abs(resource.x - self.position.x) + abs(resource.y - self.position.y)
                    if distance < min_distance:
                        available_resources.append((resource, distance))
        
        # Sortiere nach Entfernung
        available_resources.sort(key=lambda x: x[1])
        
        # Finde erste Ressource mit verfügbarem Arbeitsplatz
        for resource, distance in available_resources:
            if self._tribe_system._assign_worker_to_resource(self.member_id, resource):
                nearest_resource = resource
                min_distance = distance
                break
        
        return nearest_resource
    
    def _move_to_resource(self, resource):
        """Bewege dich aktiv zu einer Ressource oder einem anderen NPC"""
        # Unterscheide zwischen Ressourcen (.x/.y) und NPCs (.position.x/.position.y)
        if hasattr(resource, 'position'):  # NPC (wie Anführer)
            target_pos = pygame.Vector2(resource.position.x, resource.position.y)
        else:  # Ressource (Baum, Stein)
            target_pos = pygame.Vector2(resource.x, resource.y)
        
        direction = target_pos - self.position
        
        if direction.length() > 20:  # Noch nicht da
            direction = direction.normalize()
            self.velocity = direction * self.max_speed * 0.8  # Schnelle Bewegung zum Ziel
            self.position += self.velocity * 0.016
            self._update_sprite_direction()
        else:
            self.velocity = pygame.Vector2(0, 0)  # Stoppe beim Ziel
    
    def _wander_to_find_resources(self, resource_type: str):
        """Wandere umher um Ressourcen zu finden"""
        if not hasattr(self, '_exploration_timer'):
            self._exploration_timer = 0
        
        self._exploration_timer += 0.016
        
        # Alle 3-5 Sekunden neue Richtung
        if self._exploration_timer > random.uniform(3, 5):
            self._exploration_timer = 0
            
            # Bewege dich in zufällige Richtung (aber bleibe im Territorium)
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(100, 300)
            target_x = self.position.x + math.cos(angle) * distance
            target_y = self.position.y + math.sin(angle) * distance
            
            # Begrenze auf Territorium
            territory_center = pygame.Vector2(self.territory.center)
            target_pos = pygame.Vector2(target_x, target_y)
            
            if territory_center.distance_to(target_pos) > self.territory.radius:
                direction = (territory_center - target_pos).normalize()
                target_pos = territory_center + direction * self.territory.radius * 0.8
            
            # Bewege zu neuem Erkundungsgebiet
            direction = (target_pos - self.position)
            if direction.length() > 10:
                direction = direction.normalize()
                self.velocity = direction * self.max_speed * 0.6
                self.position += self.velocity * 0.016
                self._update_sprite_direction()
    
    def _set_goal(self, goal: str):
        """Setze ein langfristiges Ziel für den NPC"""
        if not hasattr(self, '_current_goal'):
            self._current_goal = None
        
        self._current_goal = goal
        
        if goal == 'transport_wood':
            # Finde Lagerplatz (beim Anführer)
            leader = self._find_leader()
            if leader:
                self._move_to_resource(leader)  # Gehe zum Anführer
        elif goal == 'transport_stone':
            leader = self._find_leader()
            if leader:
                self._move_to_resource(leader)
    
    def _find_leader(self):
        """Finde den Anführer dieses Untertanen"""
        if not self.leader_id:
            return None
        
        # Suche in der TribeAISystem-Instanz nach dem Anführer
        if hasattr(self, '_tribe_system'):
            for member in self._tribe_system.members:
                if hasattr(member, 'member_id') and member.member_id == self.leader_id and member.is_leader:
                    return member
        return None
    
    def _handle_house_building(self, world_state: Dict[str, Any]):
        """Autonomer Hausbau"""
        # Gehe zum Bauplatz (beim Anführer)
        if not self.is_leader and self.leader_id:
            leader = self._find_leader()
            if leader:
                # Bewege dich zum Bauplatz (nahe beim Anführer)
                self._move_to_resource(leader)
        else:
            # Anführer bleiben am Bauplatz
            self._leader_free_movement()
        
        # Prüfe Ressourcen nur vom eigenen Volk
        own_tribe_members = []
        if hasattr(self, '_tribe_system'):
            own_tribe_members = [m for m in self._tribe_system.members if m.tribe_color == self.tribe_color]
        
        total_wood = sum(m.memory.resources_collected['wood'] for m in own_tribe_members)
        total_stone = sum(m.memory.resources_collected['stone'] for m in own_tribe_members)
        
        # Jedes Volk baut sein eigenes Haus - verschiedene Anforderungen
        if self.tribe_color == 'red':
            wood_needed = 30   # Rotes Volk: Holzhäuser (weniger Stein)
            stone_needed = 15
        elif self.tribe_color == 'blue':
            wood_needed = 40   # Blaues Volk: Ausgewogene Häuser
            stone_needed = 25
        else:  # green
            wood_needed = 20   # Grünes Volk: Steinburgen (mehr Stein)
            stone_needed = 40
        
        # Jedes Volk hat seinen eigenen Hausbau-Progress
        house_key = f'house_progress_{self.tribe_color}'
        if house_key not in world_state:
            world_state[house_key] = 0.0
            
        if total_wood >= wood_needed and total_stone >= stone_needed:
            # Arbeits-Timer für realistischen Hausbau
            if not hasattr(self, '_building_timer'):
                self._building_timer = 0
            
            self._building_timer += 0.016  # dt (~60fps)
            
            # Arbeitsintervall basierend auf Spezialisierung
            efficiency = self._get_job_efficiency('house_building')
            base_interval = random.uniform(4.0, 6.0)  # Hausbau ist langsam
            building_interval = base_interval / efficiency  # Höhere Effizienz = schneller
            
            if self._building_timer >= building_interval:
                # Reset timer für nächsten Bauschritt
                self._building_timer = 0
                
                # 🏗️ NEUES HAUS-BAU SYSTEM: Baue eigenes Haus
                if self.house and not self.house.built:
                    # Verwende Ressourcen aus Lager für Hausbau
                    if hasattr(self, '_tribe_system') and self._tribe_system.storage_system:
                        storage = self._tribe_system.storage_system.get_storage(self.tribe_color)
                        requirements = self.house.get_build_requirements()
                        
                        wood_needed = min(1, requirements['wood'])
                        stone_needed = min(1, requirements['stone'])
                        
                        wood_taken = storage.take_resources('wood', wood_needed) if storage else 0
                        stone_taken = storage.take_resources('stone', stone_needed) if storage else 0
                        
                        if wood_taken > 0 or stone_taken > 0:
                            self.house.add_resources(wood_taken, stone_taken)
                            self._add_work_fatigue(0.10)  # Hausbau ist anstrengend
                            
                            if self.house.built:
                                logger.info(f"🏠 {self.member_id} hat sein Haus fertiggestellt!")
                                self.assigned_task = "completed"  # Task erledigt
                else:
                    # Fallback: Altes System für Stamm-Häuser
                    building_progress = random.uniform(0.02, 0.05)
                    world_state[house_key] += building_progress
                    self.memory.building_progress['house'] = world_state[house_key]
                    self._add_work_fatigue(0.10)
            
            # Verbrauche Ressourcen während dem Bau (langsam)
            if random.random() < 0.02:  # 2% Chance pro Baufortschritt
                if total_wood > 0:
                    # Finde ein Mitglied mit Holz und verbrauche es
                    for member in own_tribe_members:
                        if member.memory.resources_collected['wood'] > 0:
                            member.memory.resources_collected['wood'] -= 1
                            break
                if total_stone > 0:
                    for member in own_tribe_members:
                        if member.memory.resources_collected['stone'] > 0:
                            member.memory.resources_collected['stone'] -= 1
                            break
            
            if world_state[house_key] >= 1.0:
                world_state[f'house_completed_{self.tribe_color}'] = True
                if self.tribe_color == 'red':
                    logger.info(f"🏠🔴 ROTES HOLZHAUS FERTIGGESTELLT! Von {len(own_tribe_members)} Roten Stammesmitgliedern!")
                elif self.tribe_color == 'blue':
                    logger.info(f"🏠🔵 BLAUES HAUS FERTIGGESTELLT! Von {len(own_tribe_members)} Blauen Stammesmitgliedern!")
                else:
                    logger.info(f"🏠🟢 GRÜNE STEINBURG FERTIGGESTELLT! Von {len(own_tribe_members)} Grünen Stammesmitgliedern!")
            else:
                if self.is_leader:
                    logger.info(f"🔨 Anführer {self.member_id} baut {self.tribe_color} Haus ({world_state[house_key]:.1%})")
                else:
                    logger.info(f"🔨 Untertan {self.member_id} baut {self.tribe_color} Haus ({world_state[house_key]:.1%})")
        else:
            logger.info(f"🚫 Nicht genug Ressourcen für Hausbau: {total_wood}/{wood_needed} Holz, {total_stone}/{stone_needed} Stein")
    
    def receive_command(self, command: str, leader_id: str):
        """Empfange Befehl vom Anführer"""
        self.current_command = command
        self.leader_id = leader_id
        self.memory.leader_commands.append({
            'command': command,
            'from_leader': leader_id,
            'timestamp': time.time()
        })
        logger.info(f"📝 Untertan {self.member_id} erhielt Befehl: {command} von Anführer {leader_id}")
    
    def _move_to_zone(self, dt: float, target_zone: pygame.Rect):
        """Bewege zu Ziel-Zone"""
        target_center = pygame.Vector2(target_zone.center)
        direction = target_center - self.position
        
        if direction.length() > 10:
            direction = direction.normalize()
            self.velocity = direction * self.max_speed
            self.position += self.velocity * dt
            
            # Update Sprite-Richtung
            self._update_sprite_direction()
        else:
            self.velocity = pygame.Vector2(0, 0)
    
    def _update_sprite_direction(self):
        """Update Sprite-Richtung basierend auf Bewegung"""
        if self.velocity.length() > 1.0:
            angle = math.atan2(self.velocity.y, self.velocity.x)
            angle_deg = math.degrees(angle)
            
            if -45 <= angle_deg < 45:
                self.direction = 'right'
            elif 45 <= angle_deg < 135:
                self.direction = 'down'
            elif 135 <= angle_deg or angle_deg < -135:
                self.direction = 'left'
            else:
                self.direction = 'up'
    
    def get_current_sprite(self):
        """Hole aktuellen Sprite mit animationen"""
        if not self.sprites:
            # Fallback: farbiger Kreis mit Völker-Farbe
            size = 32
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            
            # Völker-Farben
            tribe_colors = {
                "red": (255, 100, 100),
                "blue": (100, 150, 255),
                "green": (100, 255, 100)
            }
            
            base_color = tribe_colors.get(self.tribe_color, (150, 150, 150))
            
            # Anführer haben größeren, goldenen Ring
            if self.is_leader:
                pygame.draw.circle(surface, (255, 215, 0), (size//2, size//2), size//2-2, 4)
                pygame.draw.circle(surface, base_color, (size//2, size//2), size//3)
            else:
                pygame.draw.circle(surface, base_color, (size//2, size//2), size//3)
            
            pygame.draw.circle(surface, (0, 0, 0), (size//2, size//2), size//3, 2)
            
            # Aktions-Indikator
            if self.current_action == ActionType.WOOD_CHOPPING:
                pygame.draw.circle(surface, (139, 69, 19), (size//2, size//4), 3)  # Braun für Holz
            elif self.current_action == ActionType.STONE_MINING:
                pygame.draw.circle(surface, (128, 128, 128), (size//2, size//4), 3)  # Grau für Stein
            elif self.current_action == ActionType.HOUSE_BUILDING:
                pygame.draw.circle(surface, (255, 215, 0), (size//2, size//4), 3)  # Gold für Hausbau
            elif self.current_action == ActionType.COMMAND_FOLLOWERS:
                pygame.draw.circle(surface, (255, 0, 255), (size//2, size//4), 3)  # Magenta für Befehle
                
            return surface
        
        # Verwende GandalfHardcore Sprites mit Animationen
        animation_key = 'idle'  # Standard
        
        # Bestimme Animation basierend auf Aktion und Bewegung
        if self.velocity.length() > 1.0:
            animation_key = 'walk'
        elif self.current_action in [ActionType.WOOD_CHOPPING, ActionType.STONE_MINING, ActionType.HOUSE_BUILDING]:
            animation_key = 'attack'  # Verwende attack-Animation für Arbeit
        else:
            animation_key = 'idle'
        
        # Fallback wenn Animation nicht vorhanden
        if animation_key not in self.sprites:
            if 'walk' in self.sprites:
                animation_key = 'walk'
            elif self.direction in self.sprites:
                animation_key = self.direction  # Fallback zu Richtungs-basiert
            else:
                animation_key = list(self.sprites.keys())[0]  # Erster verfügbarer
        
        sprites_for_animation = self.sprites[animation_key]
        
        # Sicherheitscheck für leere Sprite-Liste
        if not sprites_for_animation:
            return None
        
        # Update Animation Timer
        if not hasattr(self, 'anim_timer'):
            self.anim_timer = 0.0
        
        self.anim_timer += 0.1  # Zeit-basierte Animation
        
        if self.anim_timer > self.anim_speed:
            self.anim_frame = (self.anim_frame + 1) % len(sprites_for_animation)
            self.anim_timer = 0.0
        
        # Sicherheitscheck für anim_frame Index
        if self.anim_frame >= len(sprites_for_animation):
            self.anim_frame = 0
        
        return sprites_for_animation[self.anim_frame]

class TribeAISystem:
    """Haupt-KI-System für Stamm-Management"""
    
    def __init__(self, world=None, storage_system=None, house_system=None):
        self.world = world
        self.members = []
        self.territory = None
        self.storage_system = storage_system
        self.house_system = house_system
        
        self.world_state = {
            'time_of_day': 0.5,
            'weather': 0.5,
            'season': 0.5,
            'threat_level': 0.0,
            'resources_collected': 0,
            'territory_safe': True
        }
        
        # KI-System Status
        self.ai_enabled = True
        self.training_mode = True
        self.conversation_log = []
        
        # Arbeitsplatz-System: Tracke welche NPCs welche Ressourcen bearbeiten
        self.workplace_assignments = {}  # {resource_id: [worker_ids]}
        self.max_workers_per_resource = 2  # Max 2 NPCs pro Ressource (realistisch)
        
        logger.info("🧠 Tribe AI System initialisiert")
    
    def _get_resource_id(self, resource):
        """Erstelle eindeutige ID für eine Ressource"""
        return f"{resource.resource_type if hasattr(resource, 'resource_type') else 'tree'}_{resource.x}_{resource.y}"
    
    def _assign_worker_to_resource(self, worker_id: str, resource) -> bool:
        """Weise einen Arbeiter einer Ressource zu, falls Platz vorhanden"""
        resource_id = self._get_resource_id(resource)
        
        if resource_id not in self.workplace_assignments:
            self.workplace_assignments[resource_id] = []
        
        # Prüfe ob bereits zu viele Arbeiter
        if len(self.workplace_assignments[resource_id]) >= self.max_workers_per_resource:
            return False
        
        # Prüfe ob Arbeiter bereits zugewiesen
        if worker_id in self.workplace_assignments[resource_id]:
            return True  # Bereits zugewiesen
        
        # Weise Arbeiter zu
        self.workplace_assignments[resource_id].append(worker_id)
        return True
    
    def _release_worker_from_resource(self, worker_id: str, resource):
        """Entferne einen Arbeiter von einer Ressource"""
        resource_id = self._get_resource_id(resource)
        
        if resource_id in self.workplace_assignments:
            if worker_id in self.workplace_assignments[resource_id]:
                self.workplace_assignments[resource_id].remove(worker_id)
                
                # Entferne leere Einträge
                if not self.workplace_assignments[resource_id]:
                    del self.workplace_assignments[resource_id]
    
    def _clean_workplace_assignments(self):
        """Entferne ungültige Zuweisungen (tote Ressourcen oder abwesende NPCs)"""
        active_worker_ids = {member.member_id for member in self.members}
        
        # Sammle verfügbare Ressourcen
        available_resources = set()
        if hasattr(self, 'tree_system'):
            for tree in self.tree_system.trees:
                if tree.alive:
                    available_resources.add(self._get_resource_id(tree))
        if hasattr(self, 'mining_system'):
            for resource in self.mining_system.resources:
                if resource.alive:
                    available_resources.add(self._get_resource_id(resource))
        
        # Bereinige Zuweisungen
        to_remove = []
        for resource_id, worker_ids in self.workplace_assignments.items():
            # Entferne tote Ressourcen
            if resource_id not in available_resources:
                to_remove.append(resource_id)
                continue
                
            # Entferne abwesende NPCs
            self.workplace_assignments[resource_id] = [
                worker_id for worker_id in worker_ids 
                if worker_id in active_worker_ids
            ]
            
            # Entferne leere Listen
            if not self.workplace_assignments[resource_id]:
                to_remove.append(resource_id)
        
        for resource_id in to_remove:
            del self.workplace_assignments[resource_id]
    
    def create_tribe(self, center_pos: Tuple[float, float], member_count: int = 102, sprites=None):
        """Erstelle Stamm mit 3 farbigen Völkern (je 1 Anführer + 33 Untertanen)"""
        # Erstelle Territorium (viel größer für weit verteilte Völker)
        self.territory = TribeTerritory(center_pos, radius=800)
        
        # Definiere die 3 Völker mit ihren Farben
        tribe_colors = ["red", "blue", "green"]
        tribe_names = ["🔴 Rotes Volk", "🔵 Blaues Volk", "🟢 Grünes Volk"]
        
        # Lade farbige Sprites für jedes Volk
        tribe_sprites = {}
        for color in tribe_colors:
            sprites = self._load_gandalf_sprites(color)
            if sprites:
                tribe_sprites[color] = sprites
            else:
                # Fallback zu Player-Sprites
                tribe_sprites[color] = self._load_player_sprites()
        
        leaders = []
        followers = []
        
        # Erstelle 3 Anführer (einen pro Volk/Farbe)
        for i, color in enumerate(tribe_colors):
            # Anführer-Positionen in einem Dreieck um das Spielerhaus verteilen mit viel mehr Abstand
            angle = (i / 3) * 2 * math.pi
            offset = 600  # Sehr großer Abstand zwischen den Völkern
            spawn_x = center_pos[0] + math.cos(angle) * offset
            spawn_y = center_pos[1] + math.sin(angle) * offset
            
            leader = TribeAIMember(
                member_id=f"leader_{color}",
                spawn_pos=(spawn_x, spawn_y),
                territory=self.territory,
                sprites=tribe_sprites[color],
                is_leader=True,
                tribe_color=color
            )
            
            leaders.append(leader)
            self.members.append(leader)
            logger.info(f"👑 {tribe_names[i]} Anführer erstellt bei ({spawn_x:.0f}, {spawn_y:.0f})")
        
        # Erstelle 99 Untertanen (33 pro Anführer/Volk)
        followers_per_leader = 33
        for leader_idx, leader in enumerate(leaders):
            color = leader.tribe_color
            tribe_name = tribe_names[leader_idx]
            
            for f in range(followers_per_leader):
                # Untertanen zufällig um ihren Anführer verteilen - KEINE Formation
                angle = random.uniform(0, 2 * math.pi)  # Komplett zufällige Winkel
                offset = random.uniform(80, 200)  # Zufällige Entfernungen
                spawn_x = leader.position.x + math.cos(angle) * offset
                spawn_y = leader.position.y + math.sin(angle) * offset
                
                follower = TribeAIMember(
                    member_id=f"follower_{color}_{f}",
                    spawn_pos=(spawn_x, spawn_y),
                    territory=self.territory,
                    sprites=tribe_sprites[color],
                    is_leader=False,
                    tribe_color=color
                )
                
                # Verbinde Untertan mit Anführer
                follower.leader_id = leader.member_id
                follower._tribe_system = self  # Referenz für _find_leader
                leader.followers.append(follower)
                
                followers.append(follower)
                self.members.append(follower)
            
            logger.info(f"👥 {tribe_name}: {len(leader.followers)} Untertanen erstellt")
        
        # Speichere Listen für einfachen Zugriff
        self.leaders = leaders
        self.followers = followers
        self.tribe_colors = tribe_colors
        self.tribe_names = tribe_names
        
        logger.info(f"🏘️ 3 Völker erstellt: {len(leaders)} Anführer mit {len(followers)} Untertanen (Gesamt: {len(self.members)})")
        logger.info(f"🎨 Völker: {', '.join(tribe_names)}")
        
        # 🏗️ Erstelle Lager und Stadtplaner für jedes Volk
        if self.storage_system and self.house_system:
            for i, leader in enumerate(leaders):
                color = leader.tribe_color
                
                # Lager in der Nähe des Anführers erstellen
                storage_offset_x = -100  # Links vom Anführer
                storage_offset_y = 0
                storage_pos = (leader.position.x + storage_offset_x, leader.position.y + storage_offset_y)
                
                # Erstelle Lager
                storage = self.storage_system.create_storage(color, storage_pos)
                
                # Startressourcen ins Lager
                storage.add_resources('wood', 10)  # Start mit etwas Holz
                storage.add_resources('stone', 5)  # Start mit etwas Stein
                
                # Erstelle Stadtplaner (rechts vom Anführer für Häuser)
                city_center_x = leader.position.x + 150  # Rechts vom Anführer
                city_center_y = leader.position.y
                city_center = (city_center_x, city_center_y)
                self.house_system.create_city_planner(color, city_center)
                
                logger.info(f"🏗️ {color.upper()} Infrastruktur: Lager bei {storage_pos}, Stadt bei {city_center}")
        
        # Verbinde alle Mitglieder mit dem TribeAISystem (wichtig für Referenzen)
        for member in self.members:
            member._tribe_system = self
            
        # Starte sofort mit intelligenter Stadtplanung
        for leader in leaders:
            leader._change_action(ActionType.COMMAND_FOLLOWERS)
    
    def _load_player_sprites(self):
        """Lade Player-Sprites für NPCs (Fallback)"""
        try:
            import os
            base_dir = os.path.dirname(os.path.dirname(__file__))
            sprite_path = os.path.join(base_dir, 'assets', 'Player', 'character-grid-sprite.png')
            
            if os.path.exists(sprite_path):
                sheet = pygame.image.load(sprite_path).convert_alpha()
                sprites = {}
                directions = ['down', 'left', 'right', 'up']
                
                for row, direction in enumerate(directions):
                    sprites[direction] = []
                    for col in range(6):
                        x, y = col * 32, row * 32
                        sprite = pygame.Surface((32, 32), pygame.SRCALPHA)
                        sprite.blit(sheet, (0, 0), (x, y, 32, 32))
                        sprites[direction].append(sprite)
                
                return sprites
        except Exception as e:
            logger.warning(f"Konnte Player-Sprites nicht laden: {e}")
        
        return None
    
    def _load_gandalf_sprites(self, color: str):
        """Lade GandalfHardcore Archer Sprites für ein bestimmtes Volk"""
        try:
            import os
            base_dir = os.path.dirname(os.path.dirname(__file__))
            sprite_path = os.path.join(base_dir, 'assets', 'GandalfHardcore Archer', 
                                     f'GandalfHardcore Archer {color} sheet.png')
            
            if os.path.exists(sprite_path):
                sheet = pygame.image.load(sprite_path).convert_alpha()
                sprites = {}
                
                # GandalfHardcore Archer Sheet-Layout analysieren
                # Erste Reihe: Idle-Animation (5 Frames)
                # Zweite Reihe: Walk/Run-Animation (11 Frames) 
                # Dritte Reihe: Attack-Animation (8 Frames)
                # Vierte + Fünfte Reihe: mehr Animationen
                
                frame_width = 64  # Geschätzte Breite
                frame_height = 64  # Geschätzte Höhe
                
                # Extrahiere verschiedene Animationen
                sprites['idle'] = []
                sprites['walk'] = []
                sprites['attack'] = []
                
                # Idle-Animation (erste Reihe, 5 Frames)
                for col in range(5):
                    x, y = col * frame_width, 0
                    sprite = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    sprite.blit(sheet, (0, 0), (x, y, frame_width, frame_height))
                    sprites['idle'].append(sprite)
                
                # Walk-Animation (zweite Reihe, erste 8 Frames)
                for col in range(8):
                    x, y = col * frame_width, frame_height
                    sprite = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    sprite.blit(sheet, (0, 0), (x, y, frame_width, frame_height))
                    sprites['walk'].append(sprite)
                
                # Attack-Animation (dritte Reihe, erste 6 Frames)
                for col in range(6):
                    x, y = col * frame_width, frame_height * 2
                    sprite = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    sprite.blit(sheet, (0, 0), (x, y, frame_width, frame_height))
                    sprites['attack'].append(sprite)
                
                # Für Richtungen - verwende die walk-Animation für alle Richtungen
                sprites['down'] = sprites['walk']
                sprites['up'] = sprites['walk']  
                sprites['left'] = sprites['walk']
                sprites['right'] = sprites['walk']
                
                logger.info(f"✅ GandalfHardcore {color} Sprites geladen: {len(sprites['idle'])} idle, {len(sprites['walk'])} walk")
                return sprites
                
        except Exception as e:
            logger.warning(f"Konnte GandalfHardcore {color} Sprites nicht laden: {e}")
        
        return None
    
    def update(self, dt: float):
        """Update des gesamten Stamm-Systems"""
        if not self.ai_enabled or not self.members:
            return
        
        # Update Weltstate
        self._update_world_state()
        
        # Bereinige Arbeitsplatz-Zuweisungen (alle 2 Sekunden)
        if not hasattr(self, '_cleanup_timer'):
            self._cleanup_timer = 0
        self._cleanup_timer += dt
        
        if self._cleanup_timer >= 2.0:  # Alle 2 Sekunden bereinigen
            self._clean_workplace_assignments()
            self._cleanup_timer = 0
        
        # Füge alle Mitglieder zum World State hinzu für Ressourcen-Berechnung
        self.world_state['all_members'] = self.members
        
        # Update alle Mitglieder
        for member in self.members:
            nearby_members = self._get_nearby_members(member)
            member.update_ai(dt, nearby_members, self.world_state)
        
        # Prüfe ob Haus fertig gebaut wurde
        if self.world_state.get('house_completed') and not hasattr(self, 'house_built'):
            self.house_built = True
            self._spawn_house_visual()
    
    def _spawn_house_visual(self):
        """Spawne das visuelle Haus wenn der Bau abgeschlossen ist"""
        if self.territory:
            # Platziere Haus in der Mitte des Territoriums
            house_pos = (self.territory.center.x, self.territory.center.y)
            
            # Lade House.png
            import os
            try:
                base_dir = os.path.dirname(os.path.dirname(__file__))
                house_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', 'House.png')
                
                if os.path.exists(house_path):
                    house_image = pygame.image.load(house_path).convert_alpha()
                    
                    # Füge Haus zur Welt hinzu (falls möglich)
                    if hasattr(self, 'world') and self.world and hasattr(self.world, 'add_dynamic_object'):
                        self.world.add_dynamic_object(house_image, house_pos[0], house_pos[1], 'completed_house')
                        logger.info(f"🏠 House.png wurde in der Welt platziert bei {house_pos}!")
                    
                    # Speichere Haus-Info für Rendering
                    self.completed_house = {
                        'image': house_image,
                        'position': house_pos
                    }
                    
                else:
                    logger.warning("House.png nicht gefunden!")
                    
            except Exception as e:
                logger.error(f"Fehler beim Laden der House.png: {e}")
    
    def _update_world_state(self):
        """Update globaler Weltstate"""
        # Zeit-Simulation (sehr einfach)
        self.world_state['time_of_day'] = (pygame.time.get_ticks() / 100000) % 1.0
        
        # Bedrohungslevel basierend auf Spielernähe
        if hasattr(self, 'player_pos'):
            dist_to_player = pygame.Vector2(self.player_pos).distance_to(self.territory.center)
            self.world_state['threat_level'] = max(0, 1.0 - (dist_to_player / 300))
        
        # Wetter (zufällige Variation)
        self.world_state['weather'] = max(0, min(1, self.world_state['weather'] + random.uniform(-0.1, 0.1)))
    
    def _get_nearby_members(self, member: TribeAIMember, radius: float = 100) -> List[TribeAIMember]:
        """Hole Mitglieder in der Nähe"""
        nearby = []
        for other in self.members:
            if other != member:
                distance = member.position.distance_to(other.position)
                if distance < radius:
                    nearby.append(other)
        return nearby
    
    def render(self, screen: pygame.Surface, camera):
        """Rendere Stamm und UI-Elemente"""
        if not self.members:
            return
        
        # Rendere Territorium (Debug)
        if hasattr(self, 'debug_mode') and self.debug_mode:
            self._render_territory_debug(screen, camera)
        
        # Rendere fertiges Haus (falls vorhanden)
        if hasattr(self, 'completed_house'):
            house_pos = self.completed_house['position']
            house_screen_x = house_pos[0] - camera.camera.left
            house_screen_y = house_pos[1] - camera.camera.top
            
            if -100 <= house_screen_x <= screen.get_width() + 100 and -100 <= house_screen_y <= screen.get_height() + 100:
                house_rect = self.completed_house['image'].get_rect()
                house_rect.center = (house_screen_x, house_screen_y)
                screen.blit(self.completed_house['image'], house_rect)
                
                # "FERTIG!" Text über dem Haus
                font = pygame.font.Font(None, 36)
                complete_text = font.render("FERTIG!", True, (0, 255, 0))
                text_rect = complete_text.get_rect(center=(house_screen_x, house_screen_y - 60))
                screen.blit(complete_text, text_rect)
        
        # Rendere Mitglieder
        for member in self.members:
            screen_x = member.position.x - camera.camera.left
            screen_y = member.position.y - camera.camera.top
            
            # Culling
            if -50 <= screen_x <= screen.get_width() + 50 and -50 <= screen_y <= screen.get_height() + 50:
                sprite = member.get_current_sprite()
                sprite_rect = sprite.get_rect()
                sprite_rect.center = (screen_x, screen_y)
                screen.blit(sprite, sprite_rect)
                
                # Status-Anzeige für Anführer und Völker
                if member.is_leader:
                    # Größere goldene Krone für Anführer
                    crown_pos = (screen_x - 12, screen_y - 30)
                    pygame.draw.polygon(screen, (255, 215, 0), [
                        (crown_pos[0], crown_pos[1] + 10),
                        (crown_pos[0] + 6, crown_pos[1]),
                        (crown_pos[0] + 12, crown_pos[1] + 5),
                        (crown_pos[0] + 18, crown_pos[1]),
                        (crown_pos[0] + 24, crown_pos[1] + 10)
                    ])
                    pygame.draw.polygon(screen, (255, 140, 0), [
                        (crown_pos[0], crown_pos[1] + 10),
                        (crown_pos[0] + 6, crown_pos[1]),
                        (crown_pos[0] + 12, crown_pos[1] + 5),
                        (crown_pos[0] + 18, crown_pos[1]),
                        (crown_pos[0] + 24, crown_pos[1] + 10)
                    ], 2)
                    
                    # Völker-Emojis für Anführer
                    font = pygame.font.Font(None, 24)
                    if member.tribe_color == "red":
                        tribe_text = font.render("🔴", True, (255, 255, 255))
                    elif member.tribe_color == "blue":
                        tribe_text = font.render("🔵", True, (255, 255, 255))
                    elif member.tribe_color == "green":
                        tribe_text = font.render("🟢", True, (255, 255, 255))
                    else:
                        tribe_text = font.render("👑", True, (255, 215, 0))
                    
                    screen.blit(tribe_text, (screen_x - 10, screen_y - 55))
                
                else:
                    # Kleine Völker-Indikator für Untertanen
                    if hasattr(self, 'show_tribe_colors') and self.show_tribe_colors:
                        color_dot_pos = (screen_x + 12, screen_y - 12)
                        if member.tribe_color == "red":
                            pygame.draw.circle(screen, (255, 100, 100), color_dot_pos, 4)
                        elif member.tribe_color == "blue":
                            pygame.draw.circle(screen, (100, 150, 255), color_dot_pos, 4)
                        elif member.tribe_color == "green":
                            pygame.draw.circle(screen, (100, 255, 100), color_dot_pos, 4)
                
                # Aktions-Text (Debug)
                if hasattr(self, 'show_actions') and self.show_actions:
                    font = pygame.font.Font(None, 16)
                    action_text = font.render(member.current_action.value, True, (255, 255, 255))
                    screen.blit(action_text, (screen_x - 30, screen_y + 20))
    
    def _render_territory_debug(self, screen: pygame.Surface, camera):
        """Rendere Territorium-Debug-Info"""
        if not self.territory:
            return
        
        # Territorium-Kreis
        center_x = self.territory.center.x - camera.camera.left
        center_y = self.territory.center.y - camera.camera.top
        
        pygame.draw.circle(screen, (100, 100, 100), (int(center_x), int(center_y)), 
                          int(self.territory.radius), 2)
        
        # Zonen
        for zone_name, zone_rect in self.territory.zones.items():
            zone_screen = pygame.Rect(
                zone_rect.x - camera.camera.left,
                zone_rect.y - camera.camera.top,
                zone_rect.width,
                zone_rect.height
            )
            
            if zone_name.startswith('center'):
                pygame.draw.rect(screen, (0, 255, 0), zone_screen, 2)
            elif zone_name.startswith('gathering'):
                pygame.draw.rect(screen, (255, 255, 0), zone_screen, 2)
            elif zone_name.startswith('guard'):
                pygame.draw.rect(screen, (255, 0, 0), zone_screen, 2)
    
    def get_ai_stats(self) -> Dict[str, Any]:
        """Hole KI-Statistiken"""
        if not self.members:
            return {}
        
        total_happiness = sum(m.happiness for m in self.members)
        total_energy = sum(m.energy for m in self.members)
        total_knowledge = sum(m.knowledge_level for m in self.members)
        
        action_counts = {}
        for member in self.members:
            action = member.current_action.value
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Ressourcen-Statistiken
        total_wood = sum(m.memory.resources_collected['wood'] for m in self.members)
        total_stone = sum(m.memory.resources_collected['stone'] for m in self.members)
        
        # Völker-spezifische Statistiken
        tribe_stats = {}
        if hasattr(self, 'tribe_colors'):
            for i, color in enumerate(self.tribe_colors):
                tribe_members = [m for m in self.members if m.tribe_color == color]
                tribe_name = self.tribe_names[i] if hasattr(self, 'tribe_names') else f"{color} Volk"
                
                tribe_wood = sum(m.memory.resources_collected['wood'] for m in tribe_members)
                tribe_stone = sum(m.memory.resources_collected['stone'] for m in tribe_members)
                
                tribe_stats[tribe_name] = {
                    'members': len(tribe_members),
                    'wood': tribe_wood,
                    'stone': tribe_stone,
                    'leader': f"leader_{color}"
                }
        
        stats = {
            'member_count': len(self.members),
            'leaders': len(self.leaders) if hasattr(self, 'leaders') else 0,
            'followers': len(self.followers) if hasattr(self, 'followers') else 0,
            'avg_happiness': total_happiness / len(self.members),
            'avg_energy': total_energy / len(self.members),
            'avg_knowledge': total_knowledge / len(self.members),
            'actions': action_counts,
            'resources': {'wood': total_wood, 'stone': total_stone},
            'house_progress': self.world_state.get('house_progress', 0.0),
            'house_completed': self.world_state.get('house_completed', False),
            'conversations_today': len(self.conversation_log),
            'territory_center': (self.territory.center.x, self.territory.center.y) if self.territory else None,
            'tribes': tribe_stats
        }
        
        return stats
    
    def save_ai_data(self, filepath: str):
        """Speichere KI-Daten und Modelle"""
        data = {
            'members': [],
            'world_state': self.world_state,
            'conversation_log': self.conversation_log[-100:],  # Nur letzte 100
            'territory': {
                'center': (self.territory.center.x, self.territory.center.y) if self.territory else None,
                'radius': self.territory.radius if self.territory else None
            }
        }
        
        for member in self.members:
            member_data = {
                'id': member.member_id,
                'personality': [p.value for p in member.personality],
                'memory': asdict(member.memory),
                'stats': {
                    'energy': member.energy,
                    'happiness': member.happiness,
                    'stress': member.stress,
                    'knowledge': member.knowledge_level
                }
            }
            data['members'].append(member_data)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"KI-Daten gespeichert: {filepath}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern: {e}")
    
    def toggle_debug_mode(self):
        """Toggle Debug-Modus"""
        self.debug_mode = not hasattr(self, 'debug_mode') or not self.debug_mode
        self.show_actions = self.debug_mode
        self.show_tribe_colors = self.debug_mode
        logger.info(f"Debug-Modus: {'An' if self.debug_mode else 'Aus'}")
    
    def teleport_members_to_player(self, player_x: float, player_y: float):
        """Teleportiere alle Stamm-Mitglieder zum Spieler"""
        if not self.members:
            return
        
        # Teleportiere Anführer in einem Kreis um den Spieler
        if hasattr(self, 'leaders'):
            for i, leader in enumerate(self.leaders):
                angle = (i / len(self.leaders)) * 2 * math.pi
                offset_x = math.cos(angle) * 100
                offset_y = math.sin(angle) * 100
                leader.position = pygame.Vector2(player_x + offset_x, player_y + offset_y)
                
                # Teleportiere Untertanen in natürlicher Verteilung um ihre Anführer
                for j, follower in enumerate(leader.followers):
                    # Zufällige Position um Anführer - keine perfekte Formation
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(60, 150)
                    follower_x = leader.position.x + math.cos(angle) * distance
                    follower_y = leader.position.y + math.sin(angle) * distance
                    follower.position = pygame.Vector2(follower_x, follower_y)
                    
                    # Setze individuelle Präferenzen
                    follower._preferred_distance = random.uniform(40, 120)
                    follower._preferred_angle_offset = random.uniform(0, 2 * math.pi)
        else:
            # Fallback für alte Version
            for i, member in enumerate(self.members):
                angle = (i / len(self.members)) * 2 * math.pi
                offset_x = math.cos(angle) * 80
                offset_y = math.sin(angle) * 80
                member.position = pygame.Vector2(player_x + offset_x, player_y + offset_y)
        
        logger.info(f"🚁 Alle {len(self.members)} Stamm-Mitglieder zum Spieler teleportiert!")
