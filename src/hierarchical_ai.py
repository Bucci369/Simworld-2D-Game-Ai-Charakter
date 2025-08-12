"""
Hierarchisches KI-Agenten-System für Völker
====================================

Dieses System implementiert eine skalierbare, hierarchische KI-Architektur 
mit zentralisierter Entscheidungsfindung und dezentraler Ausführung.

Kernprinzipien:
- Volk-Objekt als zentrale Dateninstanz
- Spezialisierte Anführer-Agenten für verschiedene Bereiche
- Einfache Minion-Einheiten mit Befehlsqueue-System
- Priority-basierte Befehlsüberschreibung
"""

import pygame
import logging
import random
import time
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
import math

logger = logging.getLogger(__name__)

class CommandPriority(IntEnum):
    """Priority levels for commands - higher numbers = higher priority"""
    IDLE = 0
    ECONOMIC = 10          # Resource gathering, building
    DIPLOMATIC = 20        # Trade, negotiation tasks  
    DEFENSIVE = 30         # Defense preparation
    MILITARY = 40          # Active combat operations
    EMERGENCY = 50         # Critical survival situations

class CommandType(Enum):
    # Economic commands
    GATHER_RESOURCE = "gather_resource"
    BUILD_STRUCTURE = "build_structure"
    FARM = "farm"
    TRADE = "trade"
    
    # Military commands
    ATTACK = "attack"
    DEFEND = "defend"
    PATROL = "patrol"
    RETREAT = "retreat"
    
    # Diplomatic commands
    NEGOTIATE = "negotiate"
    ESCORT = "escort"
    
    # Basic commands
    MOVE_TO = "move_to"
    IDLE = "idle"

@dataclass
class Command:
    """A command that can be issued to minions"""
    command_type: CommandType
    priority: CommandPriority
    target_position: Optional[tuple] = None
    target_object: Optional[Any] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    issued_time: float = field(default_factory=time.time)
    issuer_agent: str = ""
    
    def __post_init__(self):
        if self.issued_time == 0:
            self.issued_time = time.time()

class Territory:
    """Represents a controlled area with resources and strategic value"""
    def __init__(self, name: str, center: tuple, radius: float):
        self.name = name
        self.center = pygame.Vector2(center)
        self.radius = radius
        self.resources = {}  # resource_type -> amount
        self.strategic_value = 1.0
        self.under_threat = False
        self.last_threat_check = 0
    
    def contains_point(self, point: tuple) -> bool:
        """Check if a point is within this territory"""
        return self.center.distance_to(pygame.Vector2(point)) <= self.radius
    
    def get_border_points(self, num_points: int = 8) -> List[tuple]:
        """Get points along the territory border for patrol routes"""
        points = []
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            x = self.center.x + self.radius * math.cos(angle)
            y = self.center.y + self.radius * math.sin(angle)
            points.append((x, y))
        return points

class DiplomaticRelation:
    """Represents relationship with another Volk"""
    def __init__(self, target_volk_id: str):
        self.target_volk_id = target_volk_id
        self.relation_value = 0.0  # -1.0 (hostile) to 1.0 (allied)
        self.trade_agreements = []
        self.military_pacts = []
        self.last_contact = 0
        self.threat_level = 0.0  # 0.0 (no threat) to 1.0 (imminent danger)

class Volk:
    """
    Central management object for a people/tribe.
    
    This class serves as the data hub for all agents and contains:
    - All minion units
    - Territory information  
    - Resource management
    - Diplomatic relations
    - Global tribe state
    """
    
    def __init__(self, volk_id: str, color: str, starting_position: tuple):
        self.volk_id = volk_id
        self.color = color
        self.starting_position = pygame.Vector2(starting_position)
        
        # Core data structures
        self.minions: Dict[str, 'Minion'] = {}
        self.territories: Dict[str, Territory] = {}
        self.resources: Dict[str, int] = {
            'wood': 0,
            'stone': 0,
            'food': 0,
            'gold': 0
        }
        
        # Diplomatic relations
        self.diplomatic_relations: Dict[str, DiplomaticRelation] = {}
        self.known_volks: Set[str] = set()
        
        # Agent references
        self.agents: Dict[str, 'AgentBase'] = {}
        
        # Global state tracking
        self.population = 0
        self.military_strength = 0.0
        self.economic_output = 0.0
        self.territory_control = 0.0
        self.threat_level = 0.0
        
        # Communication system
        self.agent_messages: List[Dict] = []
        self.global_alerts: List[Dict] = []
        
        # Performance tracking
        self.last_full_update = time.time()
        self.update_interval = 1.0  # Update every second for performance
        
        logger.info(f"🏛️ Volk {volk_id} ({color}) created at {starting_position}")
    
    def register_agent(self, agent: 'AgentBase'):
        """Register a leader agent with this Volk"""
        self.agents[agent.agent_type] = agent
        agent.volk = self
        logger.info(f"📋 Agent {agent.agent_type} registered with Volk {self.volk_id}")
    
    def add_minion(self, minion: 'Minion'):
        """Add a minion to this Volk"""
        self.minions[minion.minion_id] = minion
        minion.volk = self
        self.population += 1
        logger.info(f"👤 Minion {minion.minion_id} added to Volk {self.volk_id}")
    
    def remove_minion(self, minion_id: str):
        """Remove a minion from this Volk"""
        if minion_id in self.minions:
            del self.minions[minion_id]
            self.population -= 1
            logger.info(f"👤 Minion {minion_id} removed from Volk {self.volk_id}")
    
    def add_territory(self, territory: Territory):
        """Add a territory under this Volk's control"""
        self.territories[territory.name] = territory
        self._recalculate_territory_control()
        logger.info(f"🗺️ Territory {territory.name} added to Volk {self.volk_id}")
    
    def get_territory_at(self, position: tuple) -> Optional[Territory]:
        """Get the territory that contains the given position"""
        for territory in self.territories.values():
            if territory.contains_point(position):
                return territory
        return None
    
    def update_resource(self, resource_type: str, amount: int):
        """Update resource amount (positive = add, negative = consume)"""
        if resource_type not in self.resources:
            self.resources[resource_type] = 0
        self.resources[resource_type] = max(0, self.resources[resource_type] + amount)
    
    def can_afford(self, costs: Dict[str, int]) -> bool:
        """Check if the Volk can afford the given resource costs"""
        for resource_type, cost in costs.items():
            if self.resources.get(resource_type, 0) < cost:
                return False
        return True
    
    def spend_resources(self, costs: Dict[str, int]) -> bool:
        """Spend resources if possible, return success"""
        if not self.can_afford(costs):
            return False
        
        for resource_type, cost in costs.items():
            self.update_resource(resource_type, -cost)
        return True
    
    def send_agent_message(self, from_agent: str, to_agent: str, message_type: str, data: Dict):
        """Send a message between agents"""
        message = {
            'from': from_agent,
            'to': to_agent,
            'type': message_type,
            'data': data,
            'timestamp': time.time()
        }
        self.agent_messages.append(message)
    
    def get_messages_for_agent(self, agent_type: str) -> List[Dict]:
        """Get all unread messages for an agent"""
        messages = [msg for msg in self.agent_messages if msg['to'] == agent_type]
        # Remove processed messages
        self.agent_messages = [msg for msg in self.agent_messages if msg['to'] != agent_type]
        return messages
    
    def raise_global_alert(self, alert_type: str, data: Dict):
        """Raise a global alert that all agents should be aware of"""
        alert = {
            'type': alert_type,
            'data': data,
            'timestamp': time.time()
        }
        self.global_alerts.append(alert)
        logger.warning(f"🚨 Global alert raised for Volk {self.volk_id}: {alert_type}")
    
    def get_global_alerts(self, max_age: float = 30.0) -> List[Dict]:
        """Get recent global alerts"""
        current_time = time.time()
        recent_alerts = [alert for alert in self.global_alerts 
                        if current_time - alert['timestamp'] <= max_age]
        return recent_alerts
    
    def _recalculate_territory_control(self):
        """Recalculate total territory control value"""
        self.territory_control = sum(t.strategic_value for t in self.territories.values())
    
    def update(self, dt: float, world_state: Dict):
        """Update the Volk's global state periodically"""
        current_time = time.time()
        
        # Only do full updates periodically for performance
        if current_time - self.last_full_update >= self.update_interval:
            self._full_update(world_state)
            self.last_full_update = current_time
        
        # Always update agents (they manage their own update frequency)
        for agent in self.agents.values():
            agent.update(dt, world_state)
    
    def _full_update(self, world_state: Dict):
        """Perform a full state update"""
        # Update population count
        self.population = len(self.minions)
        
        # Calculate military strength
        self.military_strength = sum(1.0 for m in self.minions.values() 
                                   if m.current_command and 
                                   m.current_command.priority >= CommandPriority.DEFENSIVE)
        
        # Calculate economic output
        self.economic_output = sum(1.0 for m in self.minions.values() 
                                 if m.current_command and 
                                 m.current_command.priority == CommandPriority.ECONOMIC)
        
        # Clean up old messages and alerts
        current_time = time.time()
        self.agent_messages = [msg for msg in self.agent_messages 
                              if current_time - msg['timestamp'] < 60.0]
        self.global_alerts = [alert for alert in self.global_alerts 
                             if current_time - alert['timestamp'] < 60.0]
        
        logger.debug(f"📊 Volk {self.volk_id}: Pop={self.population}, Military={self.military_strength:.1f}, Economic={self.economic_output:.1f}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information"""
        return {
            'volk_id': self.volk_id,
            'population': self.population,
            'resources': self.resources.copy(),
            'territories': len(self.territories),
            'military_strength': self.military_strength,
            'economic_output': self.economic_output,
            'territory_control': self.territory_control,
            'threat_level': self.threat_level,
            'active_agents': list(self.agents.keys())
        }


class AgentBase:
    """
    Base class for all specialized leader agents.
    
    Each agent is responsible for a specific domain (military, economic, diplomatic)
    and makes decisions within that domain. Agents communicate through the Volk object
    and can issue commands to minions.
    """
    
    def __init__(self, agent_type: str, volk: Optional['Volk'] = None):
        self.agent_type = agent_type
        self.volk = volk
        
        # Agent state
        self.active = True
        self.last_decision_time = 0
        self.decision_interval = 2.0  # Make decisions every 2 seconds
        
        # Performance tracking
        self.decisions_made = 0
        self.commands_issued = 0
        
        # Agent-specific data
        self.agent_data = {}
        self.priorities = []
        
        logger.info(f"🤖 Agent {agent_type} initialized")
    
    def update(self, dt: float, world_state: Dict):
        """Update this agent - called every frame"""
        if not self.active or not self.volk:
            return
        
        current_time = time.time()
        
        # Only make decisions periodically for performance
        if current_time - self.last_decision_time >= self.decision_interval:
            self._make_decisions(world_state)
            self.last_decision_time = current_time
    
    def _make_decisions(self, world_state: Dict):
        """Override this method to implement agent-specific decision making"""
        pass
    
    def issue_command_to_minion(self, minion_id: str, command: Command) -> bool:
        """Issue a command to a specific minion"""
        if minion_id not in self.volk.minions:
            logger.warning(f"❌ Agent {self.agent_type} tried to command non-existent minion {minion_id}")
            return False
        
        minion = self.volk.minions[minion_id]
        success = minion.receive_command(command)
        
        if success:
            self.commands_issued += 1
            command.issuer_agent = self.agent_type
            logger.debug(f"📤 Agent {self.agent_type} issued {command.command_type.value} to {minion_id}")
        
        return success
    
    def issue_command_to_group(self, minion_ids: List[str], command: Command) -> int:
        """Issue the same command to multiple minions, returns number of successful assignments"""
        success_count = 0
        for minion_id in minion_ids:
            if self.issue_command_to_minion(minion_id, command):
                success_count += 1
        return success_count
    
    def find_available_minions(self, max_priority: CommandPriority = CommandPriority.ECONOMIC) -> List[str]:
        """Find minions that can accept commands up to the given priority level"""
        available = []
        for minion_id, minion in self.volk.minions.items():
            if minion.can_accept_command_priority(max_priority):
                available.append(minion_id)
        return available
    
    def send_message_to_agent(self, target_agent: str, message_type: str, data: Dict):
        """Send a message to another agent"""
        self.volk.send_agent_message(self.agent_type, target_agent, message_type, data)
    
    def get_messages(self) -> List[Dict]:
        """Get all messages sent to this agent"""
        return self.volk.get_messages_for_agent(self.agent_type)
    
    def raise_alert(self, alert_type: str, data: Dict):
        """Raise a global alert"""
        self.volk.raise_global_alert(alert_type, data)


class Minion:
    """
    Individual execution unit with command queue system.
    
    Minions are simple units that execute commands from leader agents.
    They have no strategic intelligence, only tactical execution capabilities.
    """
    
    def __init__(self, minion_id: str, position: tuple, sprite_manager=None):
        self.minion_id = minion_id
        self.position = pygame.Vector2(position)
        self.sprite_manager = sprite_manager
        
        # Command system
        self.current_command: Optional[Command] = None
        self.command_queue: List[Command] = []
        
        # Physical properties
        self.velocity = pygame.Vector2(0, 0)
        self.max_speed = 50.0
        self.health = 100.0
        self.carrying_capacity = 5
        self.inventory = {}
        
        # Behavior state
        self.last_position_update = time.time()
        self.stuck_detection_timer = 0.0
        self.last_stuck_check = pygame.Vector2(position)
        
        # Visual properties
        self.character_index = random.randint(1, 10)  # Random character sprite
        self.rect = pygame.Rect(position[0], position[1], 32, 32)
        
        # References
        self.volk: Optional['Volk'] = None
        
        logger.debug(f"👤 Minion {minion_id} created at {position}")
    
    def receive_command(self, command: Command) -> bool:
        """
        Receive a command from a leader agent.
        Higher priority commands immediately replace current command.
        """
        if not command:
            return False
        
        # Check if this command should override current command
        if (not self.current_command or 
            command.priority > self.current_command.priority):
            
            # Store current command in queue if it's not completed
            if self.current_command and self.current_command.priority < command.priority:
                self.command_queue.insert(0, self.current_command)
            
            self.current_command = command
            self._start_command_execution()
            
            logger.debug(f"📥 Minion {self.minion_id} received priority {command.priority} command: {command.command_type.value}")
            return True
        else:
            # Queue the command if it can't override
            self.command_queue.append(command)
            return True
    
    def can_accept_command_priority(self, priority: CommandPriority) -> bool:
        """Check if this minion can accept a command of the given priority"""
        if not self.current_command:
            return True
        return priority > self.current_command.priority
    
    def _start_command_execution(self):
        """Initialize execution of the current command"""
        if not self.current_command:
            return
        
        command = self.current_command
        
        # Reset movement state for new command
        self.velocity = pygame.Vector2(0, 0)
        
        # Command-specific initialization
        if command.command_type == CommandType.MOVE_TO:
            if command.target_position:
                self._start_movement_to(command.target_position)
        
        elif command.command_type == CommandType.GATHER_RESOURCE:
            if command.target_object:
                # Move to resource first
                target_pos = getattr(command.target_object, 'position', command.target_position)
                if target_pos:
                    self._start_movement_to(target_pos)
        
        elif command.command_type == CommandType.IDLE:
            self.velocity = pygame.Vector2(0, 0)
    
    def _start_movement_to(self, target: tuple):
        """Start moving toward a target position"""
        target_vec = pygame.Vector2(target)
        direction = (target_vec - self.position).normalize()
        self.velocity = direction * self.max_speed
    
    def update(self, dt: float, world_state: Dict):
        """Update minion behavior and execute current command"""
        self._execute_current_command(dt, world_state)
        self._update_movement(dt)
        self._check_command_completion()
        
        # Update rect position for collision detection
        self.rect.center = (self.position.x, self.position.y)
    
    def _execute_current_command(self, dt: float, world_state: Dict):
        """Execute the current active command"""
        if not self.current_command:
            return
        
        command = self.current_command
        
        if command.command_type == CommandType.MOVE_TO:
            self._execute_move_command(dt)
        
        elif command.command_type == CommandType.GATHER_RESOURCE:
            self._execute_gather_command(dt, world_state)
        
        elif command.command_type == CommandType.BUILD_STRUCTURE:
            self._execute_build_command(dt, world_state)
        
        elif command.command_type == CommandType.PATROL:
            self._execute_patrol_command(dt)
    
    def _execute_move_command(self, dt: float):
        """Execute movement to target position"""
        if not self.current_command.target_position:
            self._complete_current_command()
            return
        
        target = pygame.Vector2(self.current_command.target_position)
        distance = self.position.distance_to(target)
        
        if distance < 5.0:  # Close enough
            self._complete_current_command()
        else:
            # Continue moving
            direction = (target - self.position).normalize()
            self.velocity = direction * self.max_speed
    
    def _execute_gather_command(self, dt: float, world_state: Dict):
        """Execute resource gathering"""
        # This is a simplified implementation
        # In practice, you'd interact with the world's resource system
        
        if random.random() < 0.02:  # 2% chance per frame to gather
            resource_type = self.current_command.parameters.get('resource_type', 'wood')
            amount = self.current_command.parameters.get('amount', 1)
            
            # Add to inventory
            if resource_type not in self.inventory:
                self.inventory[resource_type] = 0
            self.inventory[resource_type] += amount
            
            # Update Volk resources
            if self.volk:
                self.volk.update_resource(resource_type, amount)
            
            logger.debug(f"⛏️ Minion {self.minion_id} gathered {amount} {resource_type}")
            
            # Complete command after gathering
            if self.inventory.get(resource_type, 0) >= self.carrying_capacity:
                self._complete_current_command()
    
    def _execute_build_command(self, dt: float, world_state: Dict):
        """Execute building construction"""
        # Simplified building - just takes time
        build_time = self.current_command.parameters.get('build_time', 5.0)
        elapsed = time.time() - self.current_command.issued_time
        
        if elapsed >= build_time:
            logger.info(f"🏗️ Minion {self.minion_id} completed construction")
            self._complete_current_command()
    
    def _execute_patrol_command(self, dt: float):
        """Execute patrol behavior"""
        # Simple patrol - move between waypoints
        waypoints = self.current_command.parameters.get('waypoints', [])
        if not waypoints:
            self._complete_current_command()
            return
        
        current_waypoint_index = self.current_command.parameters.get('current_waypoint', 0)
        if current_waypoint_index >= len(waypoints):
            current_waypoint_index = 0
            self.current_command.parameters['current_waypoint'] = current_waypoint_index
        
        target = pygame.Vector2(waypoints[current_waypoint_index])
        distance = self.position.distance_to(target)
        
        if distance < 10.0:  # Reached waypoint
            self.current_command.parameters['current_waypoint'] = (current_waypoint_index + 1) % len(waypoints)
        
        # Move toward current waypoint
        direction = (target - self.position).normalize()
        self.velocity = direction * self.max_speed * 0.7  # Slower patrol speed
    
    def _update_movement(self, dt: float):
        """Update position based on velocity"""
        if self.velocity.length() > 0:
            # Normalize velocity if too fast
            if self.velocity.length() > self.max_speed:
                self.velocity.scale_to_length(self.max_speed)
            
            # Update position
            self.position += self.velocity * dt
    
    def _check_command_completion(self):
        """Check if current command is completed and move to next"""
        # Commands complete themselves when done
        pass
    
    def _complete_current_command(self):
        """Mark current command as completed and move to next in queue"""
        if self.current_command:
            logger.debug(f"✅ Minion {self.minion_id} completed {self.current_command.command_type.value}")
        
        self.current_command = None
        
        # Get next command from queue
        if self.command_queue:
            self.current_command = self.command_queue.pop(0)
            self._start_command_execution()
        else:
            # No commands - go idle
            idle_command = Command(
                command_type=CommandType.IDLE,
                priority=CommandPriority.IDLE
            )
            self.current_command = idle_command
    
    def draw(self, surface, camera):
        """Draw the minion using the sprite system"""
        if self.sprite_manager:
            is_moving = self.velocity.length() > 0.1
            dt = 0.016 if is_moving else 0
            current_frame = self.sprite_manager.get_frame(self.character_index, dt)
            
            if current_frame:
                screen_pos = camera.apply_to_point((
                    self.position.x - current_frame.get_width() // 2,
                    self.position.y - current_frame.get_height() // 2
                ))
                
                # Mirror sprite when moving left
                if self.velocity.x < 0:
                    current_frame = pygame.transform.flip(current_frame, True, False)
                
                surface.blit(current_frame, screen_pos)
                return
        
        # Fallback rendering
        screen_pos = camera.apply_to_point(self.position)
        color = (200, 200, 200)  # Gray for default
        
        # Color based on command priority
        if self.current_command:
            if self.current_command.priority >= CommandPriority.MILITARY:
                color = (255, 0, 0)  # Red for military
            elif self.current_command.priority >= CommandPriority.DEFENSIVE:
                color = (255, 165, 0)  # Orange for defense
            elif self.current_command.priority >= CommandPriority.ECONOMIC:
                color = (0, 255, 0)  # Green for economic
        
        pygame.draw.circle(surface, color, screen_pos, 16)


# =============================================================================
# SPECIALIZED LEADER AGENTS
# =============================================================================

class DiplomatAgent(AgentBase):
    """
    Diplomat-Agent: Manages external relations and threat detection.
    
    Responsibilities:
    - Monitor other Volks and their activities
    - Detect threats and hostile movements
    - Negotiate trade agreements
    - Signal military agents when threats are detected
    """
    
    def __init__(self, volk: Optional['Volk'] = None):
        super().__init__("diplomat", volk)
        self.decision_interval = 3.0  # Check diplomatic situation every 3 seconds
        
        # Diplomatic state
        self.threat_scan_radius = 200.0
        self.last_threat_scan = 0
        self.detected_threats = []
        
        logger.info("🤝 Diplomat-Agent initialized")
    
    def _make_decisions(self, world_state: Dict):
        """Make diplomatic decisions"""
        self.decisions_made += 1
        
        # Check for threats
        self._scan_for_threats(world_state)
        
        # Process diplomatic messages
        messages = self.get_messages()
        for message in messages:
            self._process_diplomatic_message(message)
        
        # Update diplomatic relations
        self._update_relations(world_state)
    
    def _scan_for_threats(self, world_state: Dict):
        """Scan for hostile forces near our territories"""
        current_time = time.time()
        
        # Only scan periodically
        if current_time - self.last_threat_scan < 5.0:
            return
        
        self.last_threat_scan = current_time
        threats_detected = []
        
        # Check for enemy units in our territories
        for territory in self.volk.territories.values():
            # This would need integration with world state to detect foreign units
            # Simplified for demonstration
            if random.random() < 0.1:  # 10% chance to detect threat
                threat_data = {
                    'territory': territory.name,
                    'threat_level': random.uniform(0.3, 1.0),
                    'position': territory.center,
                    'detected_time': current_time
                }
                threats_detected.append(threat_data)
        
        # If threats detected, alert military
        if threats_detected:
            for threat in threats_detected:
                self.send_message_to_agent("kriegsherr", "threat_detected", threat)
                logger.warning(f"⚠️ Diplomat detected threat in {threat['territory']}")
    
    def _process_diplomatic_message(self, message: Dict):
        """Process incoming diplomatic messages"""
        message_type = message['type']
        data = message['data']
        
        if message_type == "trade_request":
            # Handle trade requests
            self._handle_trade_request(data)
        elif message_type == "peace_offer":
            # Handle peace offers
            self._handle_peace_offer(data)
    
    def _handle_trade_request(self, data: Dict):
        """Handle incoming trade requests"""
        # Simplified trade logic
        if self.volk.resources.get('wood', 0) > 10:
            logger.info("🤝 Diplomat accepting trade offer")
        else:
            logger.info("🤝 Diplomat declining trade offer - insufficient resources")
    
    def _handle_peace_offer(self, data: Dict):
        """Handle peace offers from other Volks"""
        logger.info("🤝 Diplomat considering peace offer")
    
    def _update_relations(self, world_state: Dict):
        """Update diplomatic relations based on recent events"""
        # Update threat levels for known relations
        for relation in self.volk.diplomatic_relations.values():
            # Decay threat levels over time
            relation.threat_level *= 0.95


class KriegsherrAgent(AgentBase):
    """
    Kriegsherr-Agent: Military command with highest priority.
    
    Responsibilities:
    - Defend territories from threats
    - Plan and execute military operations
    - Override all other commands during emergencies
    - Coordinate defensive positions
    """
    
    def __init__(self, volk: Optional['Volk'] = None):
        super().__init__("kriegsherr", volk)
        self.decision_interval = 1.0  # Fast military decisions
        
        # Military state
        self.active_threats = []
        self.military_units = set()
        self.defense_positions = []
        self.combat_mode = False
        
        logger.info("⚔️ Kriegsherr-Agent initialized")
    
    def _make_decisions(self, world_state: Dict):
        """Make military decisions"""
        self.decisions_made += 1
        
        # Process threat alerts from diplomat
        messages = self.get_messages()
        for message in messages:
            if message['type'] == "threat_detected":
                self._handle_threat_alert(message['data'])
        
        # Manage active threats
        self._manage_active_threats(world_state)
        
        # Update military readiness
        self._update_military_readiness()
    
    def _handle_threat_alert(self, threat_data: Dict):
        """Handle threat alerts from Diplomat"""
        logger.warning(f"⚔️ Kriegsherr responding to threat in {threat_data['territory']}")
        
        self.active_threats.append(threat_data)
        
        # If serious threat, activate combat mode
        if threat_data['threat_level'] > 0.7:
            self._activate_combat_mode(threat_data)
    
    def _activate_combat_mode(self, threat_data: Dict):
        """Activate combat mode - override all other activities"""
        if self.combat_mode:
            return
        
        self.combat_mode = True
        logger.warning("🚨 KRIEGSHERR: Combat mode activated!")
        
        # Find available minions for military service
        available_minions = self.find_available_minions(CommandPriority.MILITARY)
        
        # Convert economic workers to military
        economic_workers = []
        for minion_id, minion in self.volk.minions.items():
            if (minion.current_command and 
                minion.current_command.priority == CommandPriority.ECONOMIC):
                economic_workers.append(minion_id)
        
        # Combine available and converted units
        military_force = available_minions + economic_workers[:5]  # Convert up to 5 workers
        
        # Issue defensive commands
        threat_pos = threat_data['position']
        for i, minion_id in enumerate(military_force):
            # Create defensive positions around the threat
            angle = (i / len(military_force)) * 2 * math.pi
            defense_radius = 50.0
            defense_x = threat_pos[0] + defense_radius * math.cos(angle)
            defense_y = threat_pos[1] + defense_radius * math.sin(angle)
            
            defend_command = Command(
                command_type=CommandType.DEFEND,
                priority=CommandPriority.MILITARY,
                target_position=(defense_x, defense_y),
                parameters={'threat_position': threat_pos}
            )
            
            self.issue_command_to_minion(minion_id, defend_command)
        
        self.military_units.update(military_force)
        
        # Alert other agents
        self.send_message_to_agent("wirtschaftsminister", "combat_mode", {
            'active': True,
            'units_commandeered': len(economic_workers)
        })
    
    def _manage_active_threats(self, world_state: Dict):
        """Manage and resolve active threats"""
        current_time = time.time()
        resolved_threats = []
        
        for threat in self.active_threats:
            # Simple threat resolution - threats fade over time
            time_since_detection = current_time - threat['detected_time']
            
            if time_since_detection > 30.0:  # Threat expires after 30 seconds
                resolved_threats.append(threat)
                logger.info(f"✅ Threat in {threat['territory']} resolved")
        
        # Remove resolved threats
        for threat in resolved_threats:
            self.active_threats.remove(threat)
        
        # Deactivate combat mode if no threats
        if self.combat_mode and not self.active_threats:
            self._deactivate_combat_mode()
    
    def _deactivate_combat_mode(self):
        """Deactivate combat mode and return units to normal duties"""
        self.combat_mode = False
        logger.info("✅ KRIEGSHERR: Combat mode deactivated")
        
        # Release military units back to economic duty
        for minion_id in self.military_units:
            if minion_id in self.volk.minions:
                # Let Wirtschaftsminister reassign them
                self.send_message_to_agent("wirtschaftsminister", "units_returned", {
                    'minion_ids': [minion_id]
                })
        
        self.military_units.clear()
        
        # Notify other agents
        self.send_message_to_agent("wirtschaftsminister", "combat_mode", {
            'active': False
        })
    
    def _update_military_readiness(self):
        """Update overall military preparedness"""
        # Calculate military strength
        military_count = len(self.military_units)
        total_population = len(self.volk.minions)
        
        if total_population > 0:
            self.volk.military_strength = military_count / total_population
        else:
            self.volk.military_strength = 0.0


class WirtschaftsministerAgent(AgentBase):
    """
    Wirtschaftsminister-Agent: Resource and economic management.
    
    Responsibilities:
    - Assign workers to resource gathering
    - Manage construction projects  
    - Optimize economic efficiency
    - Yield to military commands during emergencies
    """
    
    def __init__(self, volk: Optional['Volk'] = None):
        super().__init__("wirtschaftsminister", volk)
        self.decision_interval = 3.0  # Economic decisions every 3 seconds for active growth
        
        # Economic state
        self.work_assignments = {}
        self.construction_projects = []
        self.resource_priorities = {
            'wood': 1.0,
            'stone': 0.8,
            'food': 0.6,
            'gold': 0.4
        }
        self.military_override = False
        
        # 🏗️ GROWTH-ORIENTED CITY BUILDING
        self.city_plan = {
            'houses_built': 0,
            'houses_needed': 0,  # Will be set based on population
            'infrastructure_built': {
                'marketplace': False,
                'well': False,
                'farm': False,
                'animal_pen': False
            },
            'construction_queue': [],
            'growth_phase': 'housing'  # housing -> infrastructure -> expansion
        }
        
        logger.info("💰 Wirtschaftsminister-Agent initialized (Growth-Oriented)")
    
    def _make_decisions(self, world_state: Dict):
        """Make economic decisions"""
        self.decisions_made += 1
        
        # Process messages from other agents
        messages = self.get_messages()
        for message in messages:
            self._process_economic_message(message)
        
        # Skip economic decisions during military override
        if self.military_override:
            return
        
        # Assign workers to resource gathering
        self._assign_resource_workers(world_state)
        
        # Manage construction projects
        self._manage_construction_projects(world_state)
        
        # Optimize resource allocation
        self._optimize_resource_allocation()
    
    def _process_economic_message(self, message: Dict):
        """Process messages from other agents"""
        message_type = message['type']
        data = message['data']
        
        if message_type == "combat_mode":
            self.military_override = data['active']
            if data['active']:
                logger.info("💰 Wirtschaftsminister: Military override active")
            else:
                logger.info("💰 Wirtschaftsminister: Resuming economic operations")
        
        elif message_type == "units_returned":
            # Reassign returned military units
            for minion_id in data['minion_ids']:
                self._assign_economic_work(minion_id)
    
    def _assign_resource_workers(self, world_state: Dict):
        """Assign available workers to resource gathering"""
        available_minions = self.find_available_minions(CommandPriority.ECONOMIC)
        
        # Determine resource needs
        resource_needs = self._calculate_resource_needs()
        
        # Assign workers based on needs
        for minion_id in available_minions:
            if not resource_needs:
                break
            
            # Get highest priority resource need
            resource_type = max(resource_needs.keys(), key=lambda k: resource_needs[k])
            
            # Create gathering command
            gather_command = Command(
                command_type=CommandType.GATHER_RESOURCE,
                priority=CommandPriority.ECONOMIC,
                parameters={
                    'resource_type': resource_type,
                    'amount': 5
                }
            )
            
            success = self.issue_command_to_minion(minion_id, gather_command)
            if success:
                # Reduce need for this resource
                resource_needs[resource_type] -= 0.5
                if resource_needs[resource_type] <= 0:
                    del resource_needs[resource_type]
    
    def _assign_economic_work(self, minion_id: str):
        """Assign a specific minion to economic work"""
        if minion_id not in self.volk.minions:
            return
        
        # Simple assignment - gather wood
        gather_command = Command(
            command_type=CommandType.GATHER_RESOURCE,
            priority=CommandPriority.ECONOMIC,
            parameters={
                'resource_type': 'wood',
                'amount': 5
            }
        )
        
        self.issue_command_to_minion(minion_id, gather_command)
    
    def _calculate_resource_needs(self) -> Dict[str, float]:
        """Calculate current resource needs"""
        needs = {}
        
        for resource_type, priority in self.resource_priorities.items():
            current_amount = self.volk.resources.get(resource_type, 0)
            desired_amount = 50  # Base desired amount
            
            if current_amount < desired_amount:
                shortage = (desired_amount - current_amount) / desired_amount
                needs[resource_type] = shortage * priority
        
        return needs
    
    def _manage_construction_projects(self, world_state: Dict):
        """Manage ongoing construction projects"""
        # Simplified construction management
        if len(self.construction_projects) < 2 and self.volk.resources.get('wood', 0) > 20:
            # Start new construction project
            available_builders = self.find_available_minions(CommandPriority.ECONOMIC)
            
            if available_builders:
                builder_id = available_builders[0]
                build_command = Command(
                    command_type=CommandType.BUILD_STRUCTURE,
                    priority=CommandPriority.ECONOMIC,
                    parameters={
                        'structure_type': 'house',
                        'build_time': 10.0
                    }
                )
                
                success = self.issue_command_to_minion(builder_id, build_command)
                if success:
                    self.construction_projects.append({
                        'builder': builder_id,
                        'type': 'house',
                        'start_time': time.time()
                    })
                    
                    # Spend resources
                    self.volk.spend_resources({'wood': 10, 'stone': 5})
                    logger.info(f"🏗️ Construction project started by {builder_id}")
    
    def _optimize_resource_allocation(self):
        """Optimize resource allocation based on current situation"""
        # Update economic output
        economic_workers = sum(1 for minion in self.volk.minions.values()
                              if minion.current_command and
                              minion.current_command.priority == CommandPriority.ECONOMIC)
        
        total_population = len(self.volk.minions)
        if total_population > 0:
            self.volk.economic_output = economic_workers / total_population
        else:
            self.volk.economic_output = 0.0