"""
Performance-Fix für das Tribe AI System
Reduziert die Update-Frequenz der Neural Networks
"""

import time
import random

class PerformanceOptimizer:
    """Klasse zur Performance-Optimierung der AI"""
    
    def __init__(self):
        self.member_timers = {}
        self.global_update_counter = 0
        
    def should_update_ai(self, member_id):
        """Bestimmt ob ein Member AI-Update braucht"""
        current_time = time.time()
        
        if member_id not in self.member_timers:
            # Erstes Update für diesen Member
            self.member_timers[member_id] = {
                'last_update': 0,
                'interval': random.uniform(0.3, 0.8)  # 300-800ms
            }
            
        member_data = self.member_timers[member_id]
        
        # Prüfe ob genug Zeit vergangen ist
        if (current_time - member_data['last_update']) > member_data['interval']:
            member_data['last_update'] = current_time
            # Randomisiere das nächste Interval
            member_data['interval'] = random.uniform(0.3, 0.8)
            return True
            
        return False
    
    def should_train_network(self):
        """Bestimmt ob Neural Network Training stattfinden soll"""
        self.global_update_counter += 1
        
        # Training nur alle 60 Updates (etwa 1x pro Sekunde bei 60 FPS)
        return self.global_update_counter % 60 == 0

# Globaler Performance Optimizer
performance_optimizer = PerformanceOptimizer()
