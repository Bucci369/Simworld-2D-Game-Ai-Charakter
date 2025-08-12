"""
Hierarchical Tribe System Integration
=====================================

This module provides the integration layer between the new hierarchical AI system
and the existing game infrastructure. It replaces the old SimpleTribeSystem
with a scalable, agent-based approach.
"""

import pygame
import logging
import random
import math
import time
from typing import Dict, List, Optional, Any

from hierarchical_ai import (
    Volk, Minion, Territory, 
    DiplomatAgent, KriegsherrAgent, WirtschaftsministerAgent,
    Command, CommandType, CommandPriority
)
from character_sprites import CharacterSprites

logger = logging.getLogger(__name__)

class HierarchicalTribeSystem:
    """
    Integration layer that connects the hierarchical AI system
    with the existing game world and rendering system.
    """
    
    def __init__(self):
        self.volks: Dict[str, Volk] = {}
        self.sprite_manager = CharacterSprites()
        
        # Game integration
        self.debug_mode = False
        self.render_debug_info = False
        
        # Performance tracking
        self.total_decisions_made = 0
        self.total_commands_issued = 0
        
        logger.info("🏛️ Hierarchical Tribe System initialized")
    
    def create_tribe(self, color: str, starting_position: tuple, num_workers: int = 10):
        """
        Create a new tribe with hierarchical AI agents.
        
        This replaces the old SimpleTribeSystem.create_tribe() method
        """
        volk_id = f"volk_{color}"
        
        # Create the central Volk object
        volk = Volk(volk_id, color, starting_position)
        
        # Create initial territory (larger for city building)
        main_territory = Territory(
            name=f"{color}_homeland", 
            center=starting_position, 
            radius=200.0  # Larger radius for city expansion
        )
        volk.add_territory(main_territory)
        
        # Create and register specialized agents
        diplomat = DiplomatAgent(volk)
        kriegsherr = KriegsherrAgent(volk)
        wirtschaftsminister = WirtschaftsministerAgent(volk)
        
        volk.register_agent(diplomat)
        volk.register_agent(kriegsherr)
        volk.register_agent(wirtschaftsminister)
        
        # Create minions (workers) 
        self._create_minions_for_volk(volk, starting_position, num_workers)
        
        # Store the Volk
        self.volks[color] = volk
        
        logger.info(f"🏛️ Created hierarchical tribe {color} with {num_workers} minions and 3 agents for city building")
        
        return volk
    
    def _create_minions_for_volk(self, volk: Volk, center_pos: tuple, num_minions: int):
        """Create minions around the starting position"""
        for i in range(num_minions):
            # Distribute minions in a circle around the center
            angle = (i / num_minions) * 2 * 3.14159
            radius = random.uniform(30, 80)
            
            pos_x = center_pos[0] + radius * math.cos(angle)
            pos_y = center_pos[1] + radius * math.sin(angle)
            
            minion_id = f"{volk.volk_id}_minion_{i}"
            minion = Minion(minion_id, (pos_x, pos_y), self.sprite_manager)
            
            # Connect to game systems for real building/gathering
            if hasattr(self, 'game_house_system'):
                minion.game_house_system = self.game_house_system
            if hasattr(self, 'game_world_resources'):
                minion.game_world_resources = self.game_world_resources
            
            volk.add_minion(minion)
    
    def teleport_members_to_player(self, player_x: float, player_y: float):
        """Teleport tribe members to player position (compatibility method)"""
        for volk in self.volks.values():
            for i, minion in enumerate(volk.minions.values()):
                # Spread minions around player
                offset_x = random.uniform(-100, 100)
                offset_y = random.uniform(-100, 100)
                
                minion.position.x = player_x + offset_x
                minion.position.y = player_y + offset_y
                minion.rect.center = (minion.position.x, minion.position.y)
        
        total_minions = sum(len(volk.minions) for volk in self.volks.values())
        logger.info(f"🚁 Teleported {total_minions} hierarchical tribe members to player")
    
    def update(self, dt: float, world_state: Dict):
        """Update all Volks and their agents"""
        for volk in self.volks.values():
            volk.update(dt, world_state)
            
            # Update all minions
            for minion in volk.minions.values():
                minion.update(dt, world_state)
        
        # Update performance statistics
        self._update_performance_stats()
    
    def draw(self, surface, camera):
        """Draw all minions and debug information"""
        for volk in self.volks.values():
            # Draw all minions
            for minion in volk.minions.values():
                minion.draw(surface, camera)
            
            # Draw debug information if enabled
            if self.render_debug_info:
                self._draw_debug_info(surface, camera, volk)
    
    def _draw_debug_info(self, surface, camera, volk: Volk):
        """Draw debug information for a Volk"""
        # Draw territories
        for territory in volk.territories.values():
            screen_center = camera.apply_to_point(territory.center)
            screen_radius = int(territory.radius * camera.zoom)
            
            color = (0, 255, 0, 50) if not territory.under_threat else (255, 0, 0, 50)
            pygame.draw.circle(surface, color[:3], screen_center, screen_radius, 2)
        
        # Draw agent status
        y_offset = 10
        for agent_type, agent in volk.agents.items():
            status_text = f"{agent_type}: {agent.decisions_made} decisions, {agent.commands_issued} commands"
            # This would need a font system - simplified for now
            pass
    
    def _update_performance_stats(self):
        """Update performance tracking statistics"""
        self.total_decisions_made = sum(
            sum(agent.decisions_made for agent in volk.agents.values())
            for volk in self.volks.values()
        )
        
        self.total_commands_issued = sum(
            sum(agent.commands_issued for agent in volk.agents.values())
            for volk in self.volks.values()
        )
    
    def toggle_debug_mode(self):
        """Toggle debug mode for all agents"""
        self.debug_mode = not self.debug_mode
        self.render_debug_info = self.debug_mode
        
        for volk in self.volks.values():
            for agent in volk.agents.values():
                # Agents could have their own debug settings
                pass
        
        logger.info(f"🐛 Hierarchical AI debug mode: {'ON' if self.debug_mode else 'OFF'}")
    
    def get_ai_stats(self) -> Dict[str, Any]:
        """Get comprehensive AI statistics"""
        stats = {
            'total_volks': len(self.volks),
            'total_minions': sum(len(volk.minions) for volk in self.volks.values()),
            'total_agents': sum(len(volk.agents) for volk in self.volks.values()),
            'total_decisions': self.total_decisions_made,
            'total_commands': self.total_commands_issued,
            'volk_details': {}
        }
        
        for color, volk in self.volks.items():
            stats['volk_details'][color] = volk.get_status()
        
        return stats
    
    def create_growth_oriented_tribe_near_player(self, color: str, player_position: tuple, distance: float = 300.0, num_workers: int = 10):
        """
        Create a growth-oriented tribe near the player for city building demonstration
        """
        # Calculate position near player but not too close
        angle = random.uniform(0, 2 * math.pi)
        spawn_x = player_position[0] + math.cos(angle) * distance
        spawn_y = player_position[1] + math.sin(angle) * distance
        spawn_position = (spawn_x, spawn_y)
        
        # Create the tribe
        volk = self.create_tribe(color, spawn_position, num_workers)
        
        # Set up growth-oriented parameters
        if 'wirtschaftsminister' in volk.agents:
            wirtschaftsminister = volk.agents['wirtschaftsminister']
            # Start with more resources for active city building
            volk.resources['wood'] = 50
            volk.resources['stone'] = 30
            # Set aggressive construction schedule
            wirtschaftsminister.decision_interval = 2.0  # Even faster decisions
            
        logger.info(f"🏗️ Created growth-oriented tribe {color} near player at {spawn_position}")
        logger.info(f"🏗️ Tribe will build: {num_workers + 1} houses, marketplace, well, farm, animal pen")
        
        return volk
    
    def simulate_threat(self, volk_color: str, threat_level: float = 0.8):
        """Simulate a threat for testing the military system"""
        if volk_color not in self.volks:
            logger.warning(f"Cannot simulate threat - Volk {volk_color} not found")
            return
        
        volk = self.volks[volk_color]
        
        # Find a territory to threaten
        if not volk.territories:
            logger.warning(f"Cannot simulate threat - Volk {volk_color} has no territories")
            return
        
        territory = list(volk.territories.values())[0]
        
        # Send threat to diplomat
        if 'diplomat' in volk.agents:
            diplomat = volk.agents['diplomat']
            threat_data = {
                'territory': territory.name,
                'threat_level': threat_level,
                'position': tuple(territory.center),
                'detected_time': time.time()
            }
            diplomat.detected_threats.append(threat_data)
            diplomat.send_message_to_agent('kriegsherr', 'threat_detected', threat_data)
            
            logger.warning(f"🚨 Simulated threat (level {threat_level}) in {territory.name}")
        else:
            logger.warning("No diplomat agent found to process simulated threat")
    
    def get_tribe_leaders(self) -> Dict[str, Any]:
        """Get tribe leaders for compatibility with existing chat system"""
        leaders = {}
        
        for color, volk in self.volks.items():
            # Create a leader-like object for compatibility
            leader_data = {
                'volk_id': volk.volk_id,
                'position': volk.starting_position,
                'is_leader': True,
                'command_responses': [],
                'agents': volk.agents
            }
            leaders[color] = leader_data
        
        return leaders
    
    def process_player_command(self, volk_color: str, command_text: str):
        """Process player commands through the appropriate agent"""
        if volk_color not in self.volks:
            logger.warning(f"Cannot process command - Volk {volk_color} not found")
            return
        
        volk = self.volks[volk_color]
        
        # Simple command parsing - route to appropriate agent
        command_lower = command_text.lower()
        
        if any(word in command_lower for word in ['attack', 'defend', 'military', 'war']):
            if 'kriegsherr' in volk.agents:
                # Military command
                self.simulate_threat(volk_color, 0.9)  # High threat to activate military
                logger.info(f"⚔️ Military command sent to Kriegsherr: {command_text}")
            
        elif any(word in command_lower for word in ['build', 'gather', 'work', 'resource']):
            if 'wirtschaftsminister' in volk.agents:
                # Economic command
                wirtschaftsminister = volk.agents['wirtschaftsminister']
                # Force immediate resource assignment
                wirtschaftsminister.decision_interval = 0.5  # Speed up decisions
                logger.info(f"💰 Economic command sent to Wirtschaftsminister: {command_text}")
                
        elif any(word in command_lower for word in ['trade', 'peace', 'negotiate']):
            if 'diplomat' in volk.agents:
                # Diplomatic command  
                logger.info(f"🤝 Diplomatic command sent to Diplomat: {command_text}")
        
        else:
            # General command - send to economic minister by default
            logger.info(f"📋 General command processed: {command_text}")


# Compatibility layer for existing code
class SimpleTribeSystem(HierarchicalTribeSystem):
    """
    Compatibility wrapper to replace the old SimpleTribeSystem
    without breaking existing code.
    """
    
    def __init__(self):
        super().__init__()
        
        # Add compatibility properties
        self.tribes = {}  # Will be populated with minion lists for compatibility
        
    def create_tribe(self, color: str, starting_position: tuple, num_workers: int = 10):
        """Create tribe and maintain compatibility interface"""
        volk = super().create_tribe(color, starting_position, num_workers)
        
        # Create compatibility interface - expose minions as a tribe list
        self.tribes[color] = list(volk.minions.values())
        
        return volk
    
    def update(self, dt: float, world_state: Dict):
        """Update with compatibility for world_state structure"""
        super().update(dt, world_state)
        
        # Update compatibility interface
        for color, volk in self.volks.items():
            self.tribes[color] = list(volk.minions.values())


# Backwards compatibility - import existing CharacterSprites if available
try:
    import math
    logger.info("✅ Math module loaded for hierarchical system")
except ImportError:
    logger.error("❌ Math module required for hierarchical system")

logger.info("🏛️ Hierarchical Tribe System integration layer loaded")