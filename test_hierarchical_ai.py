#!/usr/bin/env python3
"""
Test script for the Hierarchical AI System
==========================================

This script tests the hierarchical AI system independently of the main game
to verify that all agents work correctly and communicate properly.
"""

import sys
import os
sys.path.append('src')

import pygame
import time
import logging
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_hierarchical_ai():
    """Test the hierarchical AI system"""
    
    print("🧪 Testing Hierarchical AI System")
    print("=" * 50)
    
    # Initialize pygame (required for Vector2 and sprites)
    pygame.init()
    pygame.display.set_mode((800, 600))
    
    try:
        # Import the hierarchical system
        from hierarchical_tribe_system import HierarchicalTribeSystem
        
        # Create the system
        tribe_system = HierarchicalTribeSystem()
        print("✅ Successfully created HierarchicalTribeSystem")
        
        # Create a test tribe
        starting_pos = (400, 300)
        volk = tribe_system.create_tribe("red", starting_pos, num_workers=8)
        print(f"✅ Created tribe with {len(volk.minions)} minions")
        
        # Test basic world state
        world_state = {
            'player_position': (400, 300),
            'resources_available': {'wood': True, 'stone': True},
            'time': time.time()
        }
        
        print("\n🔄 Running AI simulation for 30 seconds...")
        print("-" * 50)
        
        start_time = time.time()
        simulation_time = 30.0
        dt = 0.5  # Half second updates
        
        step_count = 0
        while time.time() - start_time < simulation_time:
            # Update the system
            tribe_system.update(dt, world_state)
            
            step_count += 1
            
            # Print status every 5 seconds
            if step_count % 10 == 0:  # Every 5 seconds (10 * 0.5s)
                elapsed = time.time() - start_time
                stats = tribe_system.get_ai_stats()
                
                print(f"\n📊 Status at {elapsed:.1f}s:")
                print(f"   Minions: {stats['total_minions']}")
                print(f"   Agents: {stats['total_agents']}")  
                print(f"   Decisions: {stats['total_decisions']}")
                print(f"   Commands: {stats['total_commands']}")
                
                # Show volk details
                for color, details in stats['volk_details'].items():
                    print(f"   {color.upper()} Volk:")
                    print(f"     Resources: Wood={details['resources']['wood']}, Stone={details['resources']['stone']}")
                    print(f"     Military: {details['military_strength']:.1%}")
                    print(f"     Economic: {details['economic_output']:.1%}")
            
            # Test threat simulation at 10 seconds
            if step_count == 20:  # 10 seconds
                print("\n🚨 SIMULATING THREAT...")
                tribe_system.simulate_threat("red", threat_level=0.9)
            
            # Sleep to simulate real-time
            time.sleep(dt)
        
        # Final statistics
        final_stats = tribe_system.get_ai_stats()
        print(f"\n🎯 Final Results:")
        print(f"   Total Decisions Made: {final_stats['total_decisions']}")
        print(f"   Total Commands Issued: {final_stats['total_commands']}")
        print(f"   Average Decisions/Second: {final_stats['total_decisions']/simulation_time:.1f}")
        print(f"   Average Commands/Second: {final_stats['total_commands']/simulation_time:.1f}")
        
        # Test agent communication
        print(f"\n📡 Testing Agent Communication:")
        red_volk = tribe_system.volks['red']
        
        # Test diplomatic message
        if 'diplomat' in red_volk.agents:
            diplomat = red_volk.agents['diplomat']
            print(f"   Diplomat decisions: {diplomat.decisions_made}")
            print(f"   Diplomat commands: {diplomat.commands_issued}")
        
        # Test military readiness
        if 'kriegsherr' in red_volk.agents:
            kriegsherr = red_volk.agents['kriegsherr']
            print(f"   Kriegsherr decisions: {kriegsherr.decisions_made}")
            print(f"   Kriegsherr commands: {kriegsherr.commands_issued}")
            print(f"   Combat mode: {kriegsherr.combat_mode}")
            print(f"   Active threats: {len(kriegsherr.active_threats)}")
        
        # Test economic management
        if 'wirtschaftsminister' in red_volk.agents:
            wirtschaftsminister = red_volk.agents['wirtschaftsminister']
            print(f"   Wirtschaftsminister decisions: {wirtschaftsminister.decisions_made}")
            print(f"   Wirtschaftsminister commands: {wirtschaftsminister.commands_issued}")
            print(f"   Military override: {wirtschaftsminister.military_override}")
        
        # Test minion command states
        print(f"\n👥 Minion Command Analysis:")
        command_counts = {}
        for minion in red_volk.minions.values():
            if minion.current_command:
                cmd_type = minion.current_command.command_type.value
                priority = minion.current_command.priority.name
                key = f"{cmd_type} ({priority})"
                command_counts[key] = command_counts.get(key, 0) + 1
            else:
                command_counts['IDLE'] = command_counts.get('IDLE', 0) + 1
        
        for command, count in command_counts.items():
            print(f"   {command}: {count} minions")
        
        print(f"\n✅ Hierarchical AI Test Completed Successfully!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        pygame.quit()

def test_performance():
    """Test performance with multiple tribes"""
    print(f"\n🚀 Performance Test: Multiple Tribes")
    print("-" * 50)
    
    pygame.init()
    pygame.display.set_mode((800, 600))
    
    try:
        from hierarchical_tribe_system import HierarchicalTribeSystem
        
        system = HierarchicalTribeSystem()
        
        # Create multiple tribes
        colors = ['red', 'blue', 'green']
        positions = [(200, 200), (600, 200), (400, 500)]
        
        for color, pos in zip(colors, positions):
            system.create_tribe(color, pos, num_workers=15)
            print(f"   Created {color} tribe at {pos}")
        
        # Run performance test
        world_state = {'time': time.time()}
        
        print(f"\n⏱️ Performance test with {len(colors)} tribes...")
        
        start_time = time.time()
        num_updates = 100
        
        for i in range(num_updates):
            system.update(0.1, world_state)  # 10 FPS simulation
        
        elapsed = time.time() - start_time
        stats = system.get_ai_stats()
        
        print(f"   Updates: {num_updates}")
        print(f"   Time: {elapsed:.2f}s") 
        print(f"   Updates/Second: {num_updates/elapsed:.1f}")
        print(f"   Total Minions: {stats['total_minions']}")
        print(f"   Total Agents: {stats['total_agents']}")
        print(f"   Total Decisions: {stats['total_decisions']}")
        print(f"   Decisions/Update: {stats['total_decisions']/num_updates:.1f}")
        
        print(f"✅ Performance test completed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        pygame.quit()

def main():
    """Main test function"""
    print("🧪 Hierarchical AI System Test Suite")
    print("====================================")
    
    # Test 1: Basic functionality
    basic_test = test_hierarchical_ai()
    
    # Test 2: Performance
    perf_test = test_performance()
    
    # Summary
    print(f"\n📋 TEST SUMMARY")
    print(f"================")
    print(f"Basic Functionality: {'✅ PASS' if basic_test else '❌ FAIL'}")
    print(f"Performance Test: {'✅ PASS' if perf_test else '❌ FAIL'}")
    
    if basic_test and perf_test:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"The hierarchical AI system is ready for integration!")
    else:
        print(f"\n⚠️ Some tests failed. Please check the implementation.")
    
    return basic_test and perf_test

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)