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
                 territory: TribeTerritory, sprites=None):
        self.member_id = member_id
        self.position = pygame.Vector2(spawn_pos)
        self.territory = territory
        self.sprites = sprites
        
        # KI-Komponenten
        self.neural_network = NeuralDecisionNetwork()
        self.conversation_ai = ConversationAI()
        self.memory = TribeMemory()
        
        # Persönlichkeit (zufällig generiert)
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
        
        # Bewegung
        self.velocity = pygame.Vector2(0, 0)
        self.max_speed = random.uniform(50, 80)
        self.direction = 'down'
        
        # Sprite-Animation
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.2
        
        logger.info(f"🧠 KI-Mitglied {member_id} erstellt - Persönlichkeit: {[p.value for p in self.personality]}")
    
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
        
        # Führungsqualität
        if random.random() < 0.2:  # 20% Chance für Leadership
            traits.append(PersonalityTrait.LEADER)
        else:
            traits.append(PersonalityTrait.FOLLOWER)
        
        return traits
    
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
        # 🚀 PERFORMANCE FIX: AI Update Throttling
        if not hasattr(self, 'last_ai_update'):
            self.last_ai_update = 0
            self.ai_update_interval = random.uniform(0.5, 1.0)
        
        current_time = time.time()
        should_update_ai = (current_time - self.last_ai_update) > self.ai_update_interval
        
        self.action_timer += dt
        self.conversation_cooldown = max(0, self.conversation_cooldown - dt)
        
        # Hole aktuellen Zustand
        state_vector = self.get_state_vector(nearby_members, world_state)
        
        # Entscheide neue Aktion falls nötig - ABER NUR ALLE 0.5-1s!
        if should_update_ai and (self.action_timer > 5.0 or self.current_action == ActionType.IDLE):
            self.last_ai_update = current_time
            old_state = state_vector.copy()
            
            # KI-Entscheidung
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
        self.target_zone = self.territory.get_zone_for_action(new_action)
        
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
        
        # Bewege zu Ziel-Zone
        if self.target_zone:
            self._move_to_zone(dt, self.target_zone)
    
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
        """Hole aktuellen Sprite"""
        if not self.sprites or self.direction not in self.sprites:
            # Fallback: farbiger Kreis mit Aktions-Indikator
            size = 24
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            
            # Hauptfarbe basierend auf Persönlichkeit
            if PersonalityTrait.LEADER in self.personality:
                color = (255, 215, 0)  # Gold für Leader
            elif PersonalityTrait.AGGRESSIVE in self.personality:
                color = (255, 100, 100)  # Rot für Aggressive
            elif PersonalityTrait.PEACEFUL in self.personality:
                color = (100, 255, 100)  # Grün für Friedliche
            else:
                color = (100, 150, 255)  # Blau für Standard
            
            pygame.draw.circle(surface, color, (size//2, size//2), size//3)
            pygame.draw.circle(surface, (0, 0, 0), (size//2, size//2), size//3, 2)
            
            # Aktions-Indikator
            if self.current_action == ActionType.GUARD_DUTY:
                pygame.draw.circle(surface, (255, 0, 0), (size//2, size//4), 3)
            elif self.current_action == ActionType.GATHERING:
                pygame.draw.circle(surface, (0, 255, 0), (size//2, size//4), 3)
            elif self.current_action == ActionType.CONVERSATION:
                pygame.draw.circle(surface, (255, 255, 0), (size//2, size//4), 3)
            
            return surface
        
        # Verwende echte Sprites falls verfügbar
        sprites_for_direction = self.sprites[self.direction]
        if self.velocity.length() > 1.0:
            sprite = sprites_for_direction[self.anim_frame % len(sprites_for_direction)]
        else:
            sprite = sprites_for_direction[0]
        
        return sprite

class TribeAISystem:
    """Haupt-KI-System für Stamm-Management"""
    
    def __init__(self, world=None):
        self.world = world
        self.members = []
        self.territory = None
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
        
        logger.info("🧠 Tribe AI System initialisiert")
    
    def create_tribe(self, center_pos: Tuple[float, float], member_count: int = 6, sprites=None):
        """Erstelle Stamm mit KI-Mitgliedern"""
        # Erstelle Territorium
        self.territory = TribeTerritory(center_pos, radius=150)
        
        # Lade Player-Sprites für NPCs
        if not sprites:
            sprites = self._load_player_sprites()
        
        # Erstelle Mitglieder
        for i in range(member_count):
            # Spawn-Position im Territorium
            angle = (i / member_count) * 2 * math.pi
            offset = random.uniform(20, 60)
            spawn_x = center_pos[0] + math.cos(angle) * offset
            spawn_y = center_pos[1] + math.sin(angle) * offset
            
            member = TribeAIMember(
                member_id=f"tribe_member_{i}",
                spawn_pos=(spawn_x, spawn_y),
                territory=self.territory,
                sprites=sprites
            )
            
            self.members.append(member)
        
        logger.info(f"🏘️ Stamm erstellt: {len(self.members)} KI-Mitglieder")
    
    def _load_player_sprites(self):
        """Lade Player-Sprites für NPCs"""
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
    
    def update(self, dt: float):
        """Update des gesamten Stamm-Systems"""
        if not self.ai_enabled or not self.members:
            return
        
        # Update Weltstate
        self._update_world_state()
        
        # Update alle Mitglieder
        for member in self.members:
            nearby_members = self._get_nearby_members(member)
            member.update_ai(dt, nearby_members, self.world_state)
    
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
                
                # Status-Anzeige für Leader
                if PersonalityTrait.LEADER in member.personality:
                    crown_pos = (screen_x - 8, screen_y - 20)
                    pygame.draw.polygon(screen, (255, 215, 0), [
                        (crown_pos[0], crown_pos[1] + 6),
                        (crown_pos[0] + 4, crown_pos[1]),
                        (crown_pos[0] + 8, crown_pos[1] + 3),
                        (crown_pos[0] + 12, crown_pos[1]),
                        (crown_pos[0] + 16, crown_pos[1] + 6)
                    ])
                
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
        
        return {
            'member_count': len(self.members),
            'avg_happiness': total_happiness / len(self.members),
            'avg_energy': total_energy / len(self.members),
            'avg_knowledge': total_knowledge / len(self.members),
            'actions': action_counts,
            'conversations_today': len(self.conversation_log),
            'territory_center': (self.territory.center.x, self.territory.center.y) if self.territory else None
        }
    
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
        logger.info(f"Debug-Modus: {'An' if self.debug_mode else 'Aus'}")
