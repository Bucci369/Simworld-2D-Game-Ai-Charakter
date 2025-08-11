"""
🧠 Hybrid AI System - 300 Charaktere Skalierung
10 Neural Network Leaders + 290 FSM Workers
Optimiert für Performance und Emergentes Verhalten
"""

import pygame
import tensorflow as tf
import numpy as np
import random
import math
import time
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from collections import deque
import logging

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CharacterTier(Enum):
    LEADER = "leader"      # 10 Charaktere mit Neural Networks
    WORKER = "worker"      # 290 Charaktere mit FSM

class ActionType(Enum):
    IDLE = "idle"
    GATHERING = "gathering"
    PATROL = "patrol"
    GUARD_DUTY = "guard_duty"
    CONSTRUCTION = "construction"
    TRADE = "trade"
    DIPLOMACY = "diplomacy"
    COMBAT = "combat"
    RESEARCH = "research"
    PLANNING = "planning"

class WorkerSpecialization(Enum):
    FARMER = "farmer"
    MINER = "miner"
    BUILDER = "builder"
    GUARD = "guard"
    TRADER = "trader"
    SCOUT = "scout"

@dataclass
class Command:
    """Befehle von Leaders an Workers"""
    action: ActionType
    target_x: float
    target_y: float
    priority: int = 1
    duration: float = 5.0
    issued_time: float = 0

class LeaderAI:
    """Intelligente Leader mit Neural Networks"""
    
    def __init__(self, leader_id: str):
        self.leader_id = leader_id
        self.tribe_name = "Unknown Tribe"  # Tribe name for display
        self.neural_network = self._create_neural_network()
        self.territory_center = (0, 0)
        self.territory_radius = 500
        self.workers: List = []  # Assigned workers
        self.current_strategy = "expansion"
        self.resources = {"food": 100, "wood": 50, "stone": 30}
        self.relationships = {}  # Relations to other leaders
        
        # Decision making - OPTIMIZED!
        self.last_decision_time = 0
        self.decision_interval = random.uniform(3.0, 5.0)  # Staggered 3-5 seconds
        
        # Command queue for workers
        self.command_queue = deque(maxlen=50)
        
        # PERFORMANCE OPTIMIZATIONS
        self.cached_predictions = {}  # Cache predictions
        self.last_state_hash = None   # Track state changes
        self.fallback_decisions = [ActionType.GATHERING, ActionType.PATROL, ActionType.CONSTRUCTION]
        self.use_neural_network = True
        
        logger.info(f"👑 Leader {leader_id} created with Neural Network")
    
    def _create_neural_network(self):
        """Erstellt kleines, optimiertes Neural Network"""
        # Disable TensorFlow warnings
        import os
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        
        # Create model with fixed input shape
        inputs = tf.keras.Input(shape=(15,), name='leader_state')
        x = tf.keras.layers.Dense(32, activation='relu')(inputs)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = tf.keras.layers.Dense(16, activation='relu')(x)
        outputs = tf.keras.layers.Dense(len(ActionType), activation='softmax')(x)
        
        model = tf.keras.Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer='adam', loss='categorical_crossentropy')
        
        # Pre-warm the model to prevent retracing
        dummy_input = np.zeros((1, 15), dtype=np.float32)
        model.predict(dummy_input, verbose=0)
        
        return model
    
    def update(self, dt: float, world_state: Dict, other_leaders: List):
        """Update Leader AI - Neural Network Decisions (OPTIMIZED)"""
        current_time = time.time()
        
        if (current_time - self.last_decision_time) < self.decision_interval:
            return
            
        self.last_decision_time = current_time
        
        # Create state vector for neural network
        state_vector = self._create_state_vector(world_state, other_leaders)
        
        # Create a hash of the state to check if it changed significantly
        state_hash = hash(tuple(np.round(state_vector, 2)))
        
        # Use cached prediction if state hasn't changed much
        if (self.last_state_hash is not None and 
            abs(state_hash - self.last_state_hash) < 1000 and 
            state_hash in self.cached_predictions):
            strategic_action = self.cached_predictions[state_hash]
        else:
            # Neural network decision with error handling
            try:
                if self.use_neural_network:
                    # Convert to proper tensor format
                    input_tensor = tf.constant(state_vector.reshape(1, -1), dtype=tf.float32)
                    prediction = self.neural_network(input_tensor, training=False)
                    action_index = tf.argmax(prediction[0]).numpy()
                    strategic_action = list(ActionType)[action_index]
                    
                    # Cache this prediction
                    self.cached_predictions[state_hash] = strategic_action
                    self.last_state_hash = state_hash
                    
                    # Limit cache size
                    if len(self.cached_predictions) > 20:
                        # Remove oldest entries
                        oldest_keys = list(self.cached_predictions.keys())[:5]
                        for key in oldest_keys:
                            del self.cached_predictions[key]
                else:
                    # Use fallback decision
                    strategic_action = random.choice(self.fallback_decisions)
                    
            except Exception as e:
                # Fallback to simple decision if TensorFlow fails
                strategic_action = random.choice(self.fallback_decisions)
                self.use_neural_network = False  # Disable neural network for this leader
                logger.warning(f"👑 {self.leader_id}: Neural Network failed, using fallback: {e}")
        
        # Issue commands to workers based on strategy
        self._issue_commands_to_workers(strategic_action)
        
        # Only log occasionally to reduce spam
        if random.random() < 0.3:  # 30% chance to log
            logger.info(f"👑 {self.leader_id}: Strategic Decision - {strategic_action}")
    
    def _create_state_vector(self, world_state: Dict, other_leaders: List) -> np.ndarray:
        """Erstellt State Vector für Neural Network (OPTIMIZED)"""
        # Use more stable, less random inputs to prevent retracing
        worker_ratio = min(len(self.workers) / 50.0, 1.0)
        food_ratio = min(self.resources["food"] / 200.0, 1.0)
        wood_ratio = min(self.resources["wood"] / 100.0, 1.0)
        stone_ratio = min(self.resources["stone"] / 100.0, 1.0)
        leader_ratio = min(len(other_leaders) / 10.0, 1.0)
        threat_level = min(world_state.get("threat_level", 0.0), 1.0)
        time_normalized = (world_state.get("time_of_day", 12) % 24) / 24.0
        
        # Strategy flags (stable)
        expansion_flag = 1.0 if self.current_strategy == "expansion" else 0.0
        defense_flag = 1.0 if self.current_strategy == "defense" else 0.0
        trade_flag = 1.0 if self.current_strategy == "trade" else 0.0
        
        # Resource need flags (stable thresholds)
        food_need = 1.0 if self.resources["food"] < 50 else 0.0
        wood_need = 1.0 if self.resources["wood"] < 25 else 0.0
        stone_need = 1.0 if self.resources["stone"] < 15 else 0.0
        
        # Use leader_id hash for stable pseudo-randomness instead of random()
        leader_hash = hash(self.leader_id)
        pseudo_random_1 = (leader_hash % 1000) / 1000.0
        pseudo_random_2 = ((leader_hash * 7) % 1000) / 1000.0
        
        state = [
            worker_ratio,
            food_ratio,
            wood_ratio,
            stone_ratio,
            leader_ratio,
            threat_level,
            time_normalized,
            expansion_flag,
            defense_flag,
            trade_flag,
            food_need,
            wood_need,
            stone_need,
            pseudo_random_1,
            pseudo_random_2
        ]
        
        return np.array(state, dtype=np.float32)
    
    def _issue_commands_to_workers(self, strategic_action: ActionType):
        """Gibt Befehle an Workers basierend auf Strategie"""
        if not self.workers:
            return
            
        # Different command patterns based on strategic action
        if strategic_action == ActionType.GATHERING:
            # Send workers to gather resources
            for i, worker in enumerate(self.workers[:10]):  # Max 10 workers at once
                offset_x = random.randint(-200, 200)
                offset_y = random.randint(-200, 200)
                command = Command(
                    action=ActionType.GATHERING,
                    target_x=self.territory_center[0] + offset_x,
                    target_y=self.territory_center[1] + offset_y,
                    priority=2,
                    duration=random.uniform(5, 15)
                )
                worker.receive_command(command)
                
        elif strategic_action == ActionType.PATROL:
            # Send guards on patrol
            guards = [w for w in self.workers if w.specialization == WorkerSpecialization.GUARD]
            for guard in guards[:5]:
                patrol_x = self.territory_center[0] + random.randint(-300, 300)
                patrol_y = self.territory_center[1] + random.randint(-300, 300)
                command = Command(
                    action=ActionType.PATROL,
                    target_x=patrol_x,
                    target_y=patrol_y,
                    priority=3,
                    duration=20.0
                )
                guard.receive_command(command)
                
        elif strategic_action == ActionType.CONSTRUCTION:
            # Send builders to work
            builders = [w for w in self.workers if w.specialization == WorkerSpecialization.BUILDER]
            for builder in builders[:3]:
                build_x = self.territory_center[0] + random.randint(-100, 100)
                build_y = self.territory_center[1] + random.randint(-100, 100)
                command = Command(
                    action=ActionType.CONSTRUCTION,
                    target_x=build_x,
                    target_y=build_y,
                    priority=2,
                    duration=30.0
                )
                builder.receive_command(command)

class WorkerAI:
    """Einfache Worker mit Finite State Machine"""
    
    def __init__(self, worker_id: str, specialization: WorkerSpecialization):
        self.worker_id = worker_id
        self.specialization = specialization
        self.current_action = ActionType.IDLE
        self.current_command: Optional[Command] = None
        self.leader: Optional[LeaderAI] = None
        
        # State machine
        self.state = "idle"
        self.state_timer = 0
        
        # Update optimization
        self.last_update = 0
        self.update_interval = random.uniform(1.0, 2.0)  # Slower staggered updates
        
        # Movement
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        self.speed = 50
        self.moving = False
        
        logger.debug(f"👷 Worker {worker_id} ({specialization.value}) created")
    
    def assign_to_leader(self, leader: LeaderAI):
        """Weist Worker einem Leader zu"""
        self.leader = leader
        leader.workers.append(self)
        # Position near leader territory
        self.x = leader.territory_center[0] + random.randint(-100, 100)
        self.y = leader.territory_center[1] + random.randint(-100, 100)
    
    def receive_command(self, command: Command):
        """Empfängt Befehl vom Leader"""
        self.current_command = command
        command.issued_time = time.time()
        self.current_action = command.action
        self.target_x = command.target_x
        self.target_y = command.target_y
        self.moving = True
        self.state = "executing_command"
        self.state_timer = 0
        
        logger.debug(f"👷 {self.worker_id}: Received command - {command.action}")
    
    def update(self, dt: float):
        """Update Worker FSM - sehr lightweight"""
        current_time = time.time()
        
        # Throttle updates for performance
        if (current_time - self.last_update) < self.update_interval:
            # Only update movement every frame
            self._update_movement(dt)
            return
            
        self.last_update = current_time
        self.state_timer += dt
        
        # State machine logic
        if self.state == "idle":
            self._state_idle()
        elif self.state == "executing_command":
            self._state_executing_command()
        elif self.state == "specialization_work":
            self._state_specialization_work()
            
        # Update movement
        self._update_movement(dt)
    
    def _state_idle(self):
        """Idle state - wait for commands or do specialization work"""
        if self.current_command:
            self.state = "executing_command"
            return
            
        # Do specialization-specific idle work after some time
        if self.state_timer > 3.0:
            self.state = "specialization_work"
            self.state_timer = 0
            self._set_specialization_target()
    
    def _state_executing_command(self):
        """Executing leader command"""
        if not self.current_command:
            self.state = "idle"
            return
            
        # Check if command expired
        if (time.time() - self.current_command.issued_time) > self.current_command.duration:
            self.current_command = None
            self.current_action = ActionType.IDLE
            self.state = "idle"
            self.moving = False
            return
            
        # Check if reached target
        if not self.moving:
            # Stay at target for a while, then return to idle
            if self.state_timer > 2.0:
                self.current_command = None
                self.current_action = ActionType.IDLE
                self.state = "idle"
                self.state_timer = 0
    
    def _state_specialization_work(self):
        """Do work based on specialization"""
        if self.state_timer > 10.0:  # Work for 10 seconds
            self.state = "idle"
            self.state_timer = 0
            self.moving = False
            return
            
        # Set appropriate action based on specialization
        if self.specialization == WorkerSpecialization.FARMER:
            self.current_action = ActionType.GATHERING
        elif self.specialization == WorkerSpecialization.MINER:
            self.current_action = ActionType.GATHERING
        elif self.specialization == WorkerSpecialization.BUILDER:
            self.current_action = ActionType.CONSTRUCTION
        elif self.specialization == WorkerSpecialization.GUARD:
            self.current_action = ActionType.PATROL
        else:
            self.current_action = ActionType.IDLE
    
    def _set_specialization_target(self):
        """Sets target based on specialization"""
        if self.leader:
            center_x, center_y = self.leader.territory_center
            # Set target based on specialization
            if self.specialization == WorkerSpecialization.FARMER:
                # Go to farmland areas
                self.target_x = center_x + random.randint(-150, 150)
                self.target_y = center_y + random.randint(-150, 150)
            elif self.specialization == WorkerSpecialization.MINER:
                # Go to resource areas
                self.target_x = center_x + random.randint(-200, 200)
                self.target_y = center_y + random.randint(-200, 200)
            elif self.specialization == WorkerSpecialization.GUARD:
                # Patrol perimeter
                angle = random.uniform(0, 2 * math.pi)
                radius = random.randint(200, 300)
                self.target_x = center_x + radius * math.cos(angle)
                self.target_y = center_y + radius * math.sin(angle)
            else:
                # Random movement within territory
                self.target_x = center_x + random.randint(-100, 100)
                self.target_y = center_y + random.randint(-100, 100)
                
            self.moving = True
    
    def _update_movement(self, dt: float):
        """Updates movement towards target"""
        if not self.moving:
            return
            
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 10:
            self.moving = False
            return
            
        # Move towards target
        move_distance = self.speed * dt
        if distance > 0:
            self.x += (dx / distance) * move_distance
            self.y += (dy / distance) * move_distance

class HybridAISystem:
    """Hauptsystem für 300 Charaktere (10 Leaders + 290 Workers)"""
    
    def __init__(self, world_width: int = 3200, world_height: int = 2400):
        self.world_width = world_width
        self.world_height = world_height
        
        # Characters
        self.leaders: List[LeaderAI] = []
        self.workers: List[WorkerAI] = []
        
        # World state
        self.world_state = {
            "time_of_day": 12.0,
            "threat_level": 0.0,
            "total_population": 0
        }
        
        # Performance tracking
        self.performance_stats = {
            "leaders_updated": 0,
            "workers_updated": 0,
            "update_time_ms": 0,
            "frame_count": 0
        }
        
        # Visual settings
        self.leader_size = 20  # Größer für bessere Sichtbarkeit
        self.worker_size = 8
        
        logger.info("🏗️ Hybrid AI System initialized")
    
    def spawn_characters(self, total_count: int = 300, player_x: float = 0, player_y: float = 0):
        """Erstellt 3 Leaders + 297 Workers in Spielernähe"""
        leader_count = 3  # Nur 3 Anführer!
        worker_count = total_count - leader_count
        
        # Create leaders first
        self._create_leaders(leader_count, player_x, player_y)
        
        # Create workers and assign to leaders
        self._create_workers(worker_count)
        
        logger.info(f"🏘️ Spawned {len(self.leaders)} Leaders and {len(self.workers)} Workers near player")
    
    def _create_leaders(self, count: int, player_x: float, player_y: float):
        """Erstellt 3 Leader in gesundem Abstand um den Spieler"""
        tribe_names = ["🔴 Nord-Stamm", "🔵 Ost-Stamm", "🟢 Süd-Stamm"]
        
        # 3 Anführer in einem Dreieck um den Spieler verteilt mit 800px Abstand
        leader_positions = [
            (player_x - 800, player_y - 600),  # Nordwest - Roter Stamm
            (player_x + 800, player_y - 600),  # Nordost - Blauer Stamm
            (player_x, player_y + 800)         # Süden - Grüner Stamm
        ]
        
        for i in range(min(count, 3)):  # Max 3 Leaders
            tribe_name = tribe_names[i] if i < len(tribe_names) else f"Stamm_{i}"
            leader = LeaderAI(f"{tribe_name}_leader")
            
            # Setze Position und Tribe Info
            leader.territory_center = leader_positions[i]
            leader.tribe_name = tribe_name
            leader.territory_radius = 800  # Großes Territorium für 99 Workers
            
            self.leaders.append(leader)
            logger.info(f"👑 {tribe_name} established at {leader.territory_center}")
    
    def _create_workers(self, count: int):
        """Erstellt 297 Workers (99 pro Anführer)"""
        specializations = list(WorkerSpecialization)
        workers_per_leader = count // len(self.leaders)  # 99 pro Leader
        
        logger.info(f"👷 Creating {workers_per_leader} workers per leader ({len(self.leaders)} leaders)")
        
        for leader_idx, leader in enumerate(self.leaders):
            # Assign 99 workers to this leader
            for worker_idx in range(workers_per_leader):
                global_worker_id = leader_idx * workers_per_leader + worker_idx
                
                # Rotate through specializations für Vielfalt
                specialization = specializations[worker_idx % len(specializations)]
                
                worker = WorkerAI(f"tribe_worker_{global_worker_id}", specialization)
                worker.assign_to_leader(leader)
                
                # Position workers in a circle around their leader
                angle = (worker_idx / workers_per_leader) * 2 * math.pi
                distance = random.randint(100, 600)  # Spread workers around leader
                offset_x = distance * math.cos(angle)
                offset_y = distance * math.sin(angle)
                
                worker.x = leader.territory_center[0] + offset_x
                worker.y = leader.territory_center[1] + offset_y
                
                self.workers.append(worker)
        
        # Handle remaining workers (falls 297 nicht perfekt durch 3 teilbar)
        remaining = count - (workers_per_leader * len(self.leaders))
        for i in range(remaining):
            leader = self.leaders[i % len(self.leaders)]
            specialization = random.choice(specializations)
            
            worker = WorkerAI(f"tribe_worker_extra_{i}", specialization)
            worker.assign_to_leader(leader)
            
            # Random position near leader
            offset_x = random.randint(-300, 300)
            offset_y = random.randint(-300, 300)
            worker.x = leader.territory_center[0] + offset_x
            worker.y = leader.territory_center[1] + offset_y
            
            self.workers.append(worker)
        
        logger.info(f"👷 Total workers created: {len(self.workers)}")
    
    def update(self, dt: float, player_x: float = 0, player_y: float = 0):
        """Update all characters with performance optimization"""
        start_time = time.time()
        
        # Update world state
        self.world_state["time_of_day"] += dt * 0.1
        if self.world_state["time_of_day"] > 24:
            self.world_state["time_of_day"] = 0
        
        self.world_state["total_population"] = len(self.leaders) + len(self.workers)
        
        # Update leaders (all leaders update every frame - they're smart)
        leaders_updated = 0
        for leader in self.leaders:
            leader.update(dt, self.world_state, self.leaders)
            leaders_updated += 1
        
        # Update workers (staggered updates for performance)
        workers_updated = 0
        for worker in self.workers:
            worker.update(dt)
            workers_updated += 1
        
        # Performance tracking
        self.performance_stats["leaders_updated"] = leaders_updated
        self.performance_stats["workers_updated"] = workers_updated
        self.performance_stats["update_time_ms"] = (time.time() - start_time) * 1000
        self.performance_stats["frame_count"] += 1
    
    def render(self, screen: pygame.Surface, camera_x: float = 0, camera_y: float = 0):
        """Render all characters with culling"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        rendered_count = 0
        
        # Render workers first (they're in background)
        for worker in self.workers:
            screen_x = worker.x - camera_x
            screen_y = worker.y - camera_y
            
            # Frustum culling
            if (-50 < screen_x < screen_width + 50 and 
                -50 < screen_y < screen_height + 50):
                
                color = self._get_worker_color(worker)
                pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), self.worker_size)
                rendered_count += 1
        
        # Render leaders on top (they're important)
        for i, leader in enumerate(self.leaders):
            center_x, center_y = leader.territory_center
            screen_x = center_x - camera_x
            screen_y = center_y - camera_y
            
            # Always render leaders if they're on screen
            if (-50 < screen_x < screen_width + 50 and 
                -50 < screen_y < screen_height + 50):
                
                # Different colors for each tribe leader
                leader_colors = [
                    (255, 215, 0),   # Gold - Tribe 1
                    (255, 69, 0),    # Red Orange - Tribe 2  
                    (138, 43, 226)   # Blue Violet - Tribe 3
                ]
                color = leader_colors[i % len(leader_colors)]
                
                # Leader crown/marker (bigger)
                pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), self.leader_size)
                
                # Draw territory radius (very faint)
                territory_color = (*color[:3], 50)
                pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), 
                                 int(leader.territory_radius * 0.2), 3)
                
                # Draw tribe indicator
                font = pygame.font.Font(None, 24)
                tribe_text = font.render(f"Tribe {i+1}", True, (255, 255, 255))
                screen.blit(tribe_text, (int(screen_x - 30), int(screen_y - 40)))
                
                rendered_count += 1
        
        return rendered_count
    
    def _get_worker_color(self, worker: WorkerAI) -> Tuple[int, int, int]:
        """Farbe basierend auf Spezialisierung und Aktion"""
        # Base color by specialization
        specialization_colors = {
            WorkerSpecialization.FARMER: (34, 139, 34),    # Forest Green
            WorkerSpecialization.MINER: (165, 42, 42),     # Brown
            WorkerSpecialization.BUILDER: (255, 140, 0),   # Dark Orange  
            WorkerSpecialization.GUARD: (220, 20, 60),     # Crimson
            WorkerSpecialization.TRADER: (138, 43, 226),   # Blue Violet
            WorkerSpecialization.SCOUT: (0, 191, 255)      # Deep Sky Blue
        }
        
        base_color = specialization_colors.get(worker.specialization, (128, 128, 128))
        
        # Modify brightness based on activity
        if worker.current_action == ActionType.IDLE:
            return tuple(c // 2 for c in base_color)  # Dimmed
        else:
            return base_color  # Full brightness
    
    def teleport_nearby_to_player(self, player_x: float, player_y: float, radius: float = 300):
        """Teleportiert nahegelegene Charaktere zum Spieler"""
        teleported = 0
        
        # Teleport some workers
        for worker in self.workers[:20]:  # Max 20 workers
            offset_x = random.randint(-150, 150)
            offset_y = random.randint(-150, 150)
            worker.x = player_x + offset_x
            worker.y = player_y + offset_y
            teleported += 1
        
        # Teleport nearest leader
        if self.leaders:
            nearest_leader = min(self.leaders, 
                               key=lambda l: math.sqrt((l.territory_center[0] - player_x)**2 + 
                                                     (l.territory_center[1] - player_y)**2))
            nearest_leader.territory_center = (player_x, player_y)
            teleported += 1
        
        logger.info(f"🚁 {teleported} characters teleported to player")
    
    def get_stats(self) -> Dict:
        """Statistiken für Debug Panel"""
        return {
            'member_count': len(self.leaders) + len(self.workers),
            'leaders': len(self.leaders),
            'workers': len(self.workers),
            'update_time_ms': self.performance_stats['update_time_ms'],
            'max_update_ms': self.performance_stats.get('max_update_ms', 0),
            'actions': self._get_action_distribution(),
            'world_time': f"{self.world_state['time_of_day']:.1f}h",
            'resources': {'population': self.world_state['total_population']}
        }
    
    def _get_action_distribution(self) -> Dict[str, int]:
        """Aktionsverteilung aller Charaktere"""
        actions = {}
        
        # Count worker actions
        for worker in self.workers:
            action = worker.current_action.value
            actions[action] = actions.get(action, 0) + 1
        
        return actions

# Test Implementation
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Hybrid AI Test - 300 Characters")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    
    # Create hybrid AI system
    ai_system = HybridAISystem()
    ai_system.spawn_characters(300)
    
    camera_x, camera_y = 0, 0
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    ai_system.teleport_nearby_to_player(camera_x + 600, camera_y + 400)
        
        # Camera movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: camera_x -= 300 * dt
        if keys[pygame.K_RIGHT]: camera_x += 300 * dt
        if keys[pygame.K_UP]: camera_y -= 300 * dt
        if keys[pygame.K_DOWN]: camera_y += 300 * dt
        
        # Update AI
        ai_system.update(dt, camera_x + 600, camera_y + 400)
        
        # Rendering
        screen.fill((20, 40, 20))  # Dark green background
        rendered_count = ai_system.render(screen, camera_x, camera_y)
        
        # Stats
        stats = ai_system.get_stats()
        info_lines = [
            f"🏘️ Hybrid AI System",
            f"👑 Leaders: {stats['leaders']} | 👷 Workers: {stats['workers']}",
            f"⚡ Update: {stats['update_time_ms']:.1f}ms",
            f"🎨 Rendered: {rendered_count}",
            f"🕐 Time: {stats['world_time']}",
            f"📊 FPS: {clock.get_fps():.1f}",
            "",
            "🎮 Controls:",
            "Arrow Keys: Move Camera",
            "T: Teleport Characters to Center"
        ]
        
        y_offset = 10
        for line in info_lines:
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (10, y_offset))
            y_offset += 25
        
        pygame.display.flip()
    
    pygame.quit()
