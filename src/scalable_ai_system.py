"""
🚀 Scalable AI System - Für 100+ Charaktere optimiert
Hierarchische AI-Architektur mit Shared Neural Networks und Update-Clustering
"""

import pygame
import tensorflow as tf
import numpy as np
import random
import time
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import List, Dict, Set
import threading
from concurrent.futures import ThreadPoolExecutor

# Performance Konstanten
MAX_AI_UPDATES_PER_FRAME = 5  # Nur 5 AI-Updates pro Frame bei 60 FPS
CLUSTER_SIZE = 10             # Charaktere werden in 10er-Gruppen verwaltet
SHARED_NETWORK_COUNT = 5      # Nur 5 verschiedene Neural Networks für alle
UPDATE_INTERVALS = {
    'high_priority': 0.2,     # Leader, nahe Spieler
    'medium_priority': 0.5,   # Aktive NPCs
    'low_priority': 1.0,      # Entfernte, idle NPCs
    'background': 2.0         # Sehr weit entfernte NPCs
}

@dataclass
class AICharacter:
    """Lightweight AI Character für Masse-Simulation"""
    id: str
    x: float
    y: float
    character_type: str = "worker"  # worker, guard, leader, trader, scout
    current_action: str = "idle"
    network_id: int = 0  # Shared Network ID
    priority_level: str = "low_priority"
    last_update: float = 0
    target_x: float = 0
    target_y: float = 0
    speed: float = 50
    energy: float = 1.0
    
    def __post_init__(self):
        self.target_x = self.x
        self.target_y = self.y

class SharedNeuralNetwork:
    """Ein Neural Network das von vielen Charakteren geteilt wird"""
    
    def __init__(self, network_id: int, character_type: str):
        self.network_id = network_id
        self.character_type = character_type
        self.model = self._build_lightweight_model()
        self.prediction_cache = {}  # Cache für ähnliche Inputs
        self.cache_ttl = 1.0  # Cache 1 Sekunde gültig
        
    def _build_lightweight_model(self):
        """Kleines, schnelles Neural Network"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(32, activation='relu', input_shape=(10,)),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(8, activation='softmax')  # 8 Aktionen
        ])
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy')
        return model
    
    def predict_batch(self, state_vectors: List[np.ndarray]) -> List[int]:
        """Batch-Prediction für bessere Performance"""
        if not state_vectors:
            return []
            
        # Stack alle Inputs
        batch_input = np.array(state_vectors)
        
        # Einmalige Prediction für alle
        predictions = self.model.predict(batch_input, verbose=0)
        
        # Konvertiere zu Aktions-IDs
        actions = np.argmax(predictions, axis=1)
        return actions.tolist()

class AICluster:
    """Verwaltet eine Gruppe von AI Charakteren"""
    
    def __init__(self, cluster_id: int, characters: List[AICharacter]):
        self.cluster_id = cluster_id
        self.characters = characters
        self.last_update = 0
        self.update_frequency = random.uniform(0.3, 0.7)
        
    def should_update(self, current_time: float) -> bool:
        """Prüft ob dieser Cluster ein Update braucht"""
        return (current_time - self.last_update) > self.update_frequency
    
    def update(self, world_state: Dict, shared_networks: Dict[int, SharedNeuralNetwork]):
        """Updated alle Charaktere im Cluster"""
        self.last_update = time.time()
        
        # Gruppiere nach Network-Typ für Batch-Processing
        network_batches = defaultdict(list)
        
        for char in self.characters:
            if char.priority_level != "background":  # Skip background characters
                # Erstelle State Vector (vereinfacht)
                state_vector = self._create_simple_state(char, world_state)
                network_batches[char.network_id].append((char, state_vector))
        
        # Batch-Processing für jedes Network
        for network_id, char_states in network_batches.items():
            if network_id in shared_networks:
                network = shared_networks[network_id]
                
                # Extrahiere nur die State Vectors
                states = [state for _, state in char_states]
                
                # Batch-Prediction
                actions = network.predict_batch(states)
                
                # Weise Aktionen zu
                for (char, _), action_id in zip(char_states, actions):
                    new_action = self._action_id_to_string(action_id)
                    if new_action != char.current_action:
                        char.current_action = new_action
                        self._set_movement_target(char)
    
    def _create_simple_state(self, char: AICharacter, world_state: Dict) -> np.ndarray:
        """Erstellt vereinfachten State Vector"""
        # Nur 10 Features statt 20+ für bessere Performance
        return np.array([
            char.x / 1000.0,  # Normalisierte Position
            char.y / 1000.0,
            char.energy,
            world_state.get('time_of_day', 0) / 24.0,
            len(world_state.get('nearby_characters', [])) / 10.0,
            random.random(),  # Noise für Variation
            char.speed / 100.0,
            world_state.get('threat_level', 0),
            world_state.get('resource_availability', 0.5),
            1.0 if char.character_type == "leader" else 0.0
        ])
    
    def _action_id_to_string(self, action_id: int) -> str:
        """Konvertiert Action ID zu String"""
        actions = ["idle", "move", "gather", "guard", "explore", "trade", "build", "rest"]
        return actions[min(action_id, len(actions) - 1)]
    
    def _set_movement_target(self, char: AICharacter):
        """Setzt Bewegungsziel basierend auf Aktion"""
        if char.current_action == "move":
            char.target_x = char.x + random.randint(-100, 100)
            char.target_y = char.y + random.randint(-100, 100)
        elif char.current_action == "explore":
            char.target_x = char.x + random.randint(-200, 200)
            char.target_y = char.y + random.randint(-200, 200)

class ScalableAIManager:
    """Hauptsystem für 100+ AI Charaktere"""
    
    def __init__(self, world_width: int = 3200, world_height: int = 2400):
        self.world_width = world_width
        self.world_height = world_height
        
        # Shared Neural Networks (nur 5 verschiedene!)
        self.shared_networks = {}
        self._create_shared_networks()
        
        # Character Management
        self.characters: List[AICharacter] = []
        self.clusters: List[AICluster] = []
        
        # Update Scheduling
        self.update_queue = deque()
        self.current_frame = 0
        
        # Performance Monitoring
        self.performance_stats = {
            'ai_updates_per_frame': 0,
            'total_characters': 0,
            'active_characters': 0,
            'update_time_ms': 0
        }
        
        # Background Processing
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        print(f"🚀 Scalable AI Manager initialized for {world_width}x{world_height} world")
    
    def _create_shared_networks(self):
        """Erstellt geteilte Neural Networks"""
        network_types = ["worker", "guard", "leader", "trader", "scout"]
        
        for i, char_type in enumerate(network_types):
            self.shared_networks[i] = SharedNeuralNetwork(i, char_type)
        
        print(f"🧠 Created {len(self.shared_networks)} shared neural networks")
    
    def spawn_characters(self, count: int = 100, num_clusters: int = 10):
        """Spawnt viele Charaktere effizient in Clustern"""
        character_types = ["worker", "guard", "leader", "trader", "scout"]
        
        # Erstelle Clusters
        cluster_centers = []
        for i in range(num_clusters):
            center_x = random.randint(200, self.world_width - 200)
            center_y = random.randint(200, self.world_height - 200)
            cluster_centers.append((center_x, center_y))
        
        for i in range(count):
            char_type = random.choice(character_types)
            network_id = character_types.index(char_type)
            
            # Wähle zufälligen Cluster
            cluster_center = random.choice(cluster_centers)
            cluster_radius = 150
            
            # Spawne in Clusternähe
            char_x = cluster_center[0] + random.randint(-cluster_radius, cluster_radius)
            char_y = cluster_center[1] + random.randint(-cluster_radius, cluster_radius)
            
            # Halte in Weltgrenzen
            char_x = max(50, min(char_x, self.world_width - 50))
            char_y = max(50, min(char_y, self.world_height - 50))
            
            char = AICharacter(
                id=f"ai_char_{i}",
                x=char_x,
                y=char_y,
                character_type=char_type,
                network_id=network_id,
                priority_level="low_priority"
            )
            
            self.characters.append(char)
        
        # Erstelle Cluster
        self._create_clusters()
        
        print(f"✅ Spawned {count} AI characters in {len(self.clusters)} clusters")
    
    def _create_clusters(self):
        """Gruppiert Charaktere in Cluster für effiziente Updates"""
        self.clusters = []
        
        for i in range(0, len(self.characters), CLUSTER_SIZE):
            cluster_chars = self.characters[i:i + CLUSTER_SIZE]
            cluster = AICluster(i // CLUSTER_SIZE, cluster_chars)
            self.clusters.append(cluster)
            self.update_queue.append(cluster)
    
    def update_character_priorities(self, player_x: float, player_y: float):
        """Updated Prioritäten basierend auf Spieler-Nähe"""
        for char in self.characters:
            distance = math.sqrt((char.x - player_x)**2 + (char.y - player_y)**2)
            
            if distance < 200:
                char.priority_level = "high_priority"
            elif distance < 500:
                char.priority_level = "medium_priority"
            elif distance < 1000:
                char.priority_level = "low_priority"
            else:
                char.priority_level = "background"
    
    def update(self, dt: float, player_x: float = 0, player_y: float = 0):
        """Hauptupdate mit Frame-Budget"""
        start_time = time.time()
        self.current_frame += 1
        
        # Update Prioritäten alle 60 Frames (1x pro Sekunde)
        if self.current_frame % 60 == 0:
            self.update_character_priorities(player_x, player_y)
        
        # Begrenze AI Updates pro Frame
        updates_this_frame = 0
        current_time = time.time()
        
        # Rotiere durch Cluster
        while updates_this_frame < MAX_AI_UPDATES_PER_FRAME and self.update_queue:
            cluster = self.update_queue.popleft()
            
            if cluster.should_update(current_time):
                # World State für diesen Cluster
                world_state = self._get_world_state_for_cluster(cluster)
                
                # Update Cluster
                cluster.update(world_state, self.shared_networks)
                updates_this_frame += 1
            
            # Cluster zurück in Queue
            self.update_queue.append(cluster)
        
        # Update Movement für alle (lightweight)
        for char in self.characters:
            self._update_character_movement(char, dt)
        
        # Performance Stats
        self.performance_stats['ai_updates_per_frame'] = updates_this_frame
        self.performance_stats['total_characters'] = len(self.characters)
        self.performance_stats['active_characters'] = sum(1 for c in self.characters if c.priority_level != "background")
        self.performance_stats['update_time_ms'] = (time.time() - start_time) * 1000
    
    def _get_world_state_for_cluster(self, cluster: AICluster) -> Dict:
        """Erstellt World State für einen Cluster"""
        # Vereinfacht für Performance
        return {
            'time_of_day': (self.current_frame / 60) % 24,
            'threat_level': 0.1,
            'resource_availability': 0.7,
            'nearby_characters': []  # Könnte optimiert werden
        }
    
    def _update_character_movement(self, char: AICharacter, dt: float):
        """Updated Bewegung (jeden Frame, aber lightweight)"""
        dx = char.target_x - char.x
        dy = char.target_y - char.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 5:
            char.x += (dx / distance) * char.speed * dt
            char.y += (dy / distance) * char.speed * dt
        
        # Energy Management
        if char.current_action != "idle":
            char.energy = max(0, char.energy - 0.1 * dt)
        else:
            char.energy = min(1.0, char.energy + 0.2 * dt)
    
    def render(self, screen: pygame.Surface, camera_x: float = 0, camera_y: float = 0):
        """Rendering mit Aggressive Culling"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        rendered_count = 0
        
        for char in self.characters:
            # Culling
            screen_x = char.x - camera_x
            screen_y = char.y - camera_y
            
            if (-50 < screen_x < screen_width + 50 and -50 < screen_y < screen_height + 50):
                # Farbe basierend auf Typ
                color = self._get_character_color(char)
                
                # Größe basierend auf Priorität
                size = 8 if char.priority_level == "background" else 12
                
                pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), size)
                rendered_count += 1
        
        return rendered_count
    
    def _get_character_color(self, char: AICharacter) -> tuple:
        """Farbe basierend auf Typ und Status"""
        type_colors = {
            "worker": (100, 150, 100),
            "guard": (150, 100, 100),
            "leader": (150, 150, 100),
            "trader": (100, 100, 150),
            "scout": (150, 100, 150)
        }
        
        base_color = type_colors.get(char.character_type, (100, 100, 100))
        
        # Dimme Background Characters
        if char.priority_level == "background":
            return tuple(c // 2 for c in base_color)
        
        return base_color
    
    def teleport_nearby_to_player(self, player_x, player_y, radius=500):
        """Teleportiert nahegelegene Charaktere zum Spieler"""
        teleported = 0
        
        for cluster_id, cluster in self.clusters.items():
            for char in cluster['characters']:
                # Prüfe Distanz zum Spieler
                dx = char.x - player_x
                dy = char.y - player_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= radius:
                    # Teleportiere in Spielernähe
                    offset_x = random.randint(-100, 100)
                    offset_y = random.randint(-100, 100)
                    char.x = player_x + offset_x
                    char.y = player_y + offset_y
                    teleported += 1
                    
                    if teleported >= 10:  # Max 10 Charaktere teleportieren
                        break
            
            if teleported >= 10:
                break
                
        print(f"🚁 {teleported} AI Charaktere zu dir teleportiert!")
    
    def get_stats(self):
        """Statistiken für Debug Panel - Kompatibilität mit main.py"""
        active_chars = sum(1 for cluster in self.clusters.values() 
                          for char in cluster['characters'] if char.active)
        
        return {
            'member_count': len(self.all_characters),
            'update_time_ms': self.performance_stats['update_time_ms'],
            'max_update_ms': self.performance_stats.get('max_update_ms', 0),
            'actions': self._get_action_distribution(),
            'world_time': f"{self.performance_stats.get('simulation_time', 0):.1f}h",
            'resources': {'food': 100, 'wood': 50, 'stone': 30}  # Dummy für Kompatibilität
        }
    
    def _get_action_distribution(self):
        """Aktionsverteilung für Stats"""
        actions = {}
        for char in self.all_characters:
            action = char.current_action
            actions[action] = actions.get(action, 0) + 1
        return actions
    
    def get_performance_stats(self) -> Dict:
        """Performance Statistiken"""
        return self.performance_stats.copy()

# Test-Implementation
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Scalable AI Test - 100 Characters")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    
    # AI Manager mit 100 Charakteren
    ai_manager = ScalableAIManager()
    ai_manager.spawn_characters(100)
    
    camera_x, camera_y = 0, 0
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Respawn Characters
                    ai_manager.spawn_characters(100)
        
        # Camera Movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: camera_x -= 200 * dt
        if keys[pygame.K_RIGHT]: camera_x += 200 * dt
        if keys[pygame.K_UP]: camera_y -= 200 * dt
        if keys[pygame.K_DOWN]: camera_y += 200 * dt
        
        # Update AI
        ai_manager.update(dt, camera_x + 600, camera_y + 400)
        
        # Rendering
        screen.fill((30, 30, 30))
        rendered_count = ai_manager.render(screen, camera_x, camera_y)
        
        # Performance Info
        stats = ai_manager.get_performance_stats()
        info_lines = [
            f"Characters: {stats['total_characters']} (Active: {stats['active_characters']})",
            f"AI Updates/Frame: {stats['ai_updates_per_frame']}",
            f"Update Time: {stats['update_time_ms']:.1f}ms",
            f"Rendered: {rendered_count}",
            f"FPS: {clock.get_fps():.1f}",
            "",
            "Controls:",
            "Arrow Keys: Move Camera",
            "Space: Respawn 100 Characters"
        ]
        
        y_offset = 10
        for line in info_lines:
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (10, y_offset))
            y_offset += 25
        
        pygame.display.flip()
    
    pygame.quit()
