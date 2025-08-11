import numpy as np
import tensorflow as tf
from enum import Enum
import logging
from typing import List, Dict, Tuple, Optional
import time

logger = logging.getLogger(__name__)

class TaskType(Enum):
    COLLECT_WOOD = "collect_wood"
    BUILD_HOUSE = "build_house" 
    GATHER_FOOD = "gather_food"
    DEFEND = "defend"
    EXPLORE = "explore"
    CRAFT = "craft"
    FARM = "farm"
    HUNT = "hunt"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class Task:
    def __init__(self, task_type: TaskType, priority: Priority, 
                 target_position: Optional[Tuple[int, int]] = None,
                 required_workers: int = 1,
                 deadline: Optional[float] = None):
        self.task_type = task_type
        self.priority = priority
        self.target_position = target_position
        self.required_workers = required_workers
        self.assigned_workers = []
        self.deadline = deadline
        self.created_time = time.time()
        self.completed = False

class AILeader:
    def __init__(self, npc_id: str, tribe_color: str, max_workers: int = 30):
        self.npc_id = npc_id
        self.tribe_color = tribe_color
        self.max_workers = max_workers
        
        # Task Management
        self.active_tasks = []
        self.completed_tasks = []
        self.task_queue = []
        
        # Performance Tracking
        self.performance_history = {
            'wood_collected': [],
            'houses_built': [],
            'task_completion_time': [],
            'worker_efficiency': []
        }
        
        # Neural Network für Entscheidungsfindung
        self.decision_model = self._build_decision_model()
        
        # Letzter Zustand für Training
        self.last_state = None
        self.last_action = None
        
        logger.info(f"🧠 KI-Leader {npc_id} initialisiert für {max_workers} Arbeiter")

    def _build_decision_model(self):
        """Erstelle ein einfaches neuronales Netz für Entscheidungen"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(12,)),  # 12 Input-Features
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(len(TaskType), activation='softmax')  # Output für jeden Task-Typ
        ])
        
        model.compile(optimizer='adam', 
                     loss='sparse_categorical_crossentropy',
                     metrics=['accuracy'])
        
        return model

    def get_world_state_vector(self, world_state: Dict) -> np.ndarray:
        """Konvertiere World State in Vektor für Neural Network"""
        try:
            # Basis-Ressourcen
            storage = world_state.get('storage_system', {}).get_storage(self.tribe_color)
            wood_amount = storage.get_resource_amount('wood') if storage else 0
            
            # Häuser zählen
            houses = [h for h in world_state.get('house_system', {}).houses.values() 
                     if h.tribe_color == self.tribe_color and h.build_progress >= 100]
            houses_under_construction = [h for h in world_state.get('house_system', {}).houses.values()
                                       if h.tribe_color == self.tribe_color 
                                       and 0 < h.build_progress < 100]
            
            # NPCs zählen
            npcs = world_state.get('tribe_system', {}).tribes.get(self.tribe_color, [])
            idle_workers = len([npc for npc in npcs if not npc.is_leader and 
                              hasattr(npc, 'state') and npc.state.value == "idle"])
            working_npcs = len(npcs) - idle_workers - 1  # -1 für Leader
            
            # Bäume in der Nähe
            trees_nearby = 0
            if npcs and world_state.get('tree_system'):
                leader_pos = next((npc.position for npc in npcs if npc.is_leader), (0, 0))
                trees_nearby = len([tree for tree in world_state.get('tree_system').trees 
                                  if tree.alive and 
                                  (tree.x - leader_pos[0])**2 + (tree.y - leader_pos[1])**2 < 500**2])
            
            # Erstelle Feature-Vektor
            features = np.array([
                wood_amount / 100.0,              # 0: Holz (normalisiert)
                len(houses),                      # 1: Fertige Häuser
                len(houses_under_construction),   # 2: Häuser im Bau
                len(npcs),                        # 3: Anzahl NPCs
                idle_workers / max(len(npcs), 1), # 4: Anteil untätige Arbeiter
                working_npcs / max(len(npcs), 1), # 5: Anteil arbeitende NPCs
                trees_nearby / 10.0,              # 6: Bäume in der Nähe (normalisiert)
                len(self.active_tasks),           # 7: Aktive Aufgaben
                time.time() % 86400 / 86400,      # 8: Tageszeit (normalisiert)
                min(len(self.active_tasks) / 5.0, 1.0),  # 9: Task-Load
                self._get_average_efficiency(),   # 10: Durchschnittliche Effizienz
                self._get_urgency_score()         # 11: Dringlichkeitswert
            ])
            
            return features.reshape(1, -1)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des State-Vektors: {e}")
            return np.zeros((1, 12))

    def _get_average_efficiency(self) -> float:
        """Berechne durchschnittliche Arbeiter-Effizienz"""
        if not self.performance_history['worker_efficiency']:
            return 0.5
        return min(np.mean(self.performance_history['worker_efficiency'][-10:]), 1.0)

    def _get_urgency_score(self) -> float:
        """Berechne Dringlichkeitswert basierend auf offenen Tasks"""
        if not self.active_tasks:
            return 0.0
        
        urgent_tasks = [t for t in self.active_tasks 
                       if t.priority in [Priority.HIGH, Priority.CRITICAL]]
        return min(len(urgent_tasks) / 3.0, 1.0)

    def make_decision(self, world_state: Dict) -> List[Task]:
        """KI-gesteuerte Entscheidung für neue Tasks mit logischem Fallback"""
        new_tasks = []
        
        # ZUERST: Einfache logische Prioritäten prüfen
        critical_tasks = self._check_critical_needs(world_state)
        new_tasks.extend(critical_tasks)
        
        # DANN: Nur wenn keine kritischen Tasks, nutze KI-Vorhersage
        if not new_tasks:
            state_vector = self.get_world_state_vector(world_state)
            predictions = self.decision_model.predict(state_vector, verbose=0)[0]
            
            # Wähle Top-Tasks basierend auf Predictions
            task_priorities = list(zip(TaskType, predictions))
            task_priorities.sort(key=lambda x: x[1], reverse=True)
            
            # Analysiere Top-Predictions
            for task_type, confidence in task_priorities[:3]:
                if confidence > 0.3:  # Nur über Threshold
                    task = self._create_smart_task(task_type, world_state, confidence)
                    if task:
                        new_tasks.append(task)
        
        logger.info(f"🧠 KI-Leader entscheidet: {len(new_tasks)} neue Tasks (Kritisch: {len(critical_tasks)})")
        return new_tasks
        
    def _check_critical_needs(self, world_state: Dict) -> List[Task]:
        """Prüfe kritische Bedürfnisse mit einfacher Logik"""
        critical_tasks = []
        
        try:
            # Hole NPCs und Häuser
            npcs = world_state.get('tribe_system', {}).tribes.get(self.tribe_color, [])
            houses = [h for h in world_state.get('house_system', {}).houses.values() 
                     if h.tribe_color == self.tribe_color and h.build_progress >= 100]
            houses_under_construction = [h for h in world_state.get('house_system', {}).houses.values()
                                       if h.tribe_color == self.tribe_color 
                                       and 0 < h.build_progress < 100]
            
            storage_system = world_state.get('storage_system', {})
            storage = storage_system.get_storage(self.tribe_color) if storage_system else None
            wood = storage.get_resource_amount('wood') if storage else 0
            
            # Debug Storage
            if hasattr(storage_system, 'storages'):
                logger.info(f"🔍 Storage Debug - System hat {len(storage_system.storages)} Lager")
                for color, stor in storage_system.storages.items():
                    wood_amount = stor.get_resource_amount('wood')
                    logger.info(f"   - {color}: {wood_amount} Holz")
            else:
                logger.info(f"❌ Kein Storage-System gefunden!")
            
            total_houses = len(houses) + len(houses_under_construction)
            total_needed = len(npcs)
            
            logger.info(f"🧠 Kritische Analyse: Häuser {len(houses)}/{total_needed}, "
                       f"Im Bau: {len(houses_under_construction)}, Holz: {wood}")
            
            # KRITISCH: Häuser fehlen
            if total_houses < total_needed:
                missing_houses = total_needed - total_houses
                logger.info(f"🚨 KRITISCH: {missing_houses} Häuser fehlen!")
                
                # Priorität: Erstelle nur eine Task pro fehlendem Haus
                if wood >= 5:
                    # Genug Holz für Hausbau - erstelle BUILD_HOUSE Task für jedes fehlende Haus
                    for i in range(min(missing_houses, wood // 5)):  # Max so viele wie Holz erlaubt
                        task = Task(TaskType.BUILD_HOUSE, Priority.CRITICAL, required_workers=1)
                        critical_tasks.append(task)
                        logger.info(f"🏗️ KRITISCHE TASK: Hausbau #{i+1} (Holz verfügbar: {wood})")
                        
                    # Falls noch immer Häuser fehlen nach dem was gebaut werden kann
                    remaining_houses = missing_houses - (wood // 5)
                    if remaining_houses > 0:
                        needed_wood = remaining_houses * 5
                        workers_needed = min(max(1, needed_wood // 10), 2)
                        task = Task(TaskType.COLLECT_WOOD, Priority.HIGH, required_workers=workers_needed)
                        critical_tasks.append(task)
                        logger.info(f"🪓 KRITISCHE TASK: Holz für {remaining_houses} weitere Häuser ({workers_needed} Arbeiter)")
                else:
                    # Nicht genug Holz - sammeln für alle fehlenden Häuser
                    needed_wood = missing_houses * 5 - wood
                    workers_needed = min(max(1, needed_wood // 10), missing_houses)  # Max 1 pro fehlendem Haus
                    task = Task(TaskType.COLLECT_WOOD, Priority.HIGH, required_workers=workers_needed)
                    critical_tasks.append(task)
                    logger.info(f"🪓 KRITISCHE TASK: Holz sammeln ({workers_needed} Arbeiter für {missing_houses} Häuser, fehlen {needed_wood})")
            
            # Prüfe ob bereits aktive Tasks für diese Bedürfnisse existieren
            existing_build_tasks = [t for t in self.active_tasks 
                                  if t.task_type == TaskType.BUILD_HOUSE and not t.completed]
            existing_wood_tasks = [t for t in self.active_tasks 
                                 if t.task_type == TaskType.COLLECT_WOOD and not t.completed]
            
            # EINFACHE Duplikat-Vermeidung: Maximal 2 aktive Tasks pro Typ
            max_wood_tasks = 2
            max_build_tasks = missing_houses
            
            current_wood_tasks = len([t for t in existing_wood_tasks if t.assigned_workers])
            current_build_tasks = len([t for t in existing_build_tasks if t.assigned_workers])
            
            # Entferne Tasks wenn zu viele
            if current_wood_tasks >= max_wood_tasks:
                critical_tasks = [t for t in critical_tasks if t.task_type != TaskType.COLLECT_WOOD]
                logger.info(f"🔄 Bereits {current_wood_tasks} COLLECT_WOOD Tasks aktiv, überspringe neue")
                
            if current_build_tasks >= max_build_tasks:
                critical_tasks = [t for t in critical_tasks if t.task_type != TaskType.BUILD_HOUSE]
                logger.info(f"🔄 Bereits {current_build_tasks} BUILD_HOUSE Tasks aktiv, überspringe neue")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei kritischer Analyse: {e}")
            
        return critical_tasks

    def _create_smart_task(self, task_type: TaskType, world_state: Dict, 
                          confidence: float) -> Optional[Task]:
        """Erstelle intelligente Tasks basierend auf World State"""
        try:
            if task_type == TaskType.COLLECT_WOOD:
                storage = world_state.get('storage_system', {}).get_storage(self.tribe_color)
                wood = storage.get_resource_amount('wood') if storage else 0
                
                if wood < 30:  # Wenig Holz
                    priority = Priority.HIGH if wood < 10 else Priority.MEDIUM
                    return Task(TaskType.COLLECT_WOOD, priority, required_workers=2)
                    
            elif task_type == TaskType.BUILD_HOUSE:
                houses = [h for h in world_state.get('house_system', {}).houses.values() 
                         if h.tribe_color == self.tribe_color and h.build_progress >= 100]
                npcs = world_state.get('tribe_system', {}).tribes.get(self.tribe_color, [])
                
                if len(houses) < len(npcs):  # Häuser fehlen
                    storage = world_state.get('storage_system', {}).get_storage(self.tribe_color)
                    wood = storage.get_resource_amount('wood') if storage else 0
                    
                    if wood >= 5:
                        return Task(TaskType.BUILD_HOUSE, Priority.HIGH, required_workers=1)
                    
            elif task_type == TaskType.EXPLORE:
                # Exploration für neue Ressourcen
                if len(self.active_tasks) < 2:  # Nicht zu viele gleichzeitige Tasks
                    return Task(TaskType.EXPLORE, Priority.LOW, required_workers=1)
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen von Task {task_type}: {e}")
            
        return None

    def assign_tasks(self, available_workers: List) -> Dict:
        """Weise Tasks intelligent den Arbeitern zu"""
        assignments = {}
        
        # Sortiere Tasks nach Priorität UND Art (BUILD_HOUSE zuerst)
        def task_priority(task):
            type_priority = 0 if task.task_type == TaskType.BUILD_HOUSE else 1
            return (type_priority, -task.priority.value, -task.created_time)
        
        sorted_tasks = sorted(self.active_tasks, key=task_priority)
        
        worker_index = 0
        for task in sorted_tasks:
            if worker_index >= len(available_workers):
                break
                
            # Skip Tasks die bereits zugewiesen sind
            if task.assigned_workers:
                continue
                
            # Assign required workers to task
            workers_needed = min(task.required_workers, 
                               len(available_workers) - worker_index)
            
            task_workers = available_workers[worker_index:worker_index + workers_needed]
            task.assigned_workers = task_workers
            
            for worker in task_workers:
                assignments[worker.npc_id] = task
                
            worker_index += workers_needed
            logger.info(f"📋 Task {task.task_type.value} zugewiesen an {workers_needed} Arbeiter")
            
        logger.info(f"📋 Aufgaben zugewiesen: {len(assignments)} Arbeiter haben Tasks")
        return assignments

    def update_performance(self, world_state: Dict):
        """Update Performance Metrics für ML Training"""
        try:
            # Wood Collection Rate
            storage = world_state.get('storage_system', {}).get_storage(self.tribe_color)
            current_wood = storage.get_resource_amount('wood') if storage else 0
            self.performance_history['wood_collected'].append(current_wood)
            
            # Houses Built
            houses = [h for h in world_state.get('house_system', {}).houses.values() 
                     if h.tribe_color == self.tribe_color and h.build_progress >= 100]
            self.performance_history['houses_built'].append(len(houses))
            
            # Task Completion Efficiency
            completed_recently = [t for t in self.completed_tasks 
                                if time.time() - t.created_time < 60]  # Last minute
            if completed_recently:
                avg_completion_time = np.mean([time.time() - t.created_time 
                                             for t in completed_recently])
                self.performance_history['task_completion_time'].append(avg_completion_time)
            
            # Worker Efficiency
            npcs = world_state.get('tribe_system', {}).tribes.get(self.tribe_color, [])
            working_npcs = len([npc for npc in npcs if not npc.is_leader and 
                              hasattr(npc, 'state') and npc.state.value != "idle"])
            efficiency = working_npcs / max(len(npcs) - 1, 1)
            self.performance_history['worker_efficiency'].append(efficiency)
            
            # Begrenze History Größe
            for key in self.performance_history:
                if len(self.performance_history[key]) > 100:
                    self.performance_history[key] = self.performance_history[key][-50:]
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Performance Update: {e}")

    def train_model(self, reward: float):
        """Einfaches Reinforcement Learning Training"""
        if self.last_state is not None and self.last_action is not None:
            try:
                # Erstelle Training Data
                target = self.last_action.copy()
                
                # Adjust based on reward
                if reward > 0:
                    target[np.argmax(self.last_action)] += 0.1 * reward
                else:
                    target[np.argmax(self.last_action)] += 0.1 * reward
                    
                # Normalisiere
                target = target / np.sum(target)
                
                # Retrain (einfaches Update)
                self.decision_model.fit(self.last_state, 
                                      np.array([np.argmax(target)]), 
                                      epochs=1, verbose=0)
                
            except Exception as e:
                logger.error(f"❌ Fehler beim Model Training: {e}")

    def calculate_reward(self, world_state: Dict) -> float:
        """Berechne Belohnung für aktuellen Zustand"""
        reward = 0.0
        
        try:
            # Positive Belohnung für Häuser
            houses = [h for h in world_state.get('house_system', {}).houses.values() 
                     if h.tribe_color == self.tribe_color and h.build_progress >= 100]
            npcs = world_state.get('tribe_system', {}).tribes.get(self.tribe_color, [])
            
            if houses and npcs:
                house_ratio = len(houses) / len(npcs)
                reward += house_ratio * 2.0
            
            # Positive Belohnung für Ressourcen-Management
            storage = world_state.get('storage_system', {}).get_storage(self.tribe_color)
            wood = storage.get_resource_amount('wood') if storage else 0
            
            if 5 <= wood <= 25:  # Optimaler Ressourcenbereich
                reward += 1.0
            elif wood > 100:  # Zu viel gehortet
                reward -= 0.5
            elif wood < 5:  # Zu wenig
                reward -= 1.0
            
            # Belohnung für Worker Efficiency
            working_npcs = len([npc for npc in npcs if not npc.is_leader and 
                              hasattr(npc, 'state') and npc.state.value != "idle"])
            if npcs:
                efficiency = working_npcs / max(len(npcs) - 1, 1)
                reward += efficiency * 1.5
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Reward Calculation: {e}")
            
        return reward

    def update(self, world_state: Dict):
        """Hauptupdate-Methode für KI-Leader"""
        try:
            # Update Performance
            self.update_performance(world_state)
            
            # Calculate Reward und Train
            current_reward = self.calculate_reward(world_state)
            if hasattr(self, '_last_reward'):
                reward_diff = current_reward - self._last_reward
                self.train_model(reward_diff)
            self._last_reward = current_reward
            
            # Make New Decisions
            state_vector = self.get_world_state_vector(world_state)
            predictions = self.decision_model.predict(state_vector, verbose=0)[0]
            
            # Store für nächstes Training
            self.last_state = state_vector
            self.last_action = predictions
            
            # Remove Completed Tasks ZUERST
            completed_tasks = [t for t in self.active_tasks if t.completed]
            if completed_tasks:
                logger.info(f"✅ Entferne {len(completed_tasks)} abgeschlossene Tasks")
                for task in completed_tasks:
                    logger.info(f"   - {task.task_type.value} abgeschlossen")
            self.active_tasks = [t for t in self.active_tasks if not t.completed]
            
            # DANN Create New Tasks
            new_tasks = self.make_decision(world_state)
            
            # Log vor dem Hinzufügen
            if new_tasks:
                logger.info(f"➕ Füge {len(new_tasks)} neue Tasks zu active_tasks hinzu")
                for task in new_tasks:
                    logger.info(f"   - {task.task_type.value} (Priorität: {task.priority.value})")
            
            self.active_tasks.extend(new_tasks)
            
            # Log aktueller Status
            logger.info(f"📊 KI-Leader {self.npc_id}: {len(self.active_tasks)} aktive Tasks, "
                       f"Reward: {current_reward:.2f}")
                          
        except Exception as e:
            logger.error(f"❌ Fehler im KI-Leader Update: {e}")