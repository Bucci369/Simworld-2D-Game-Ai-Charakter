"""
Hunger-System für den Spieler
- Zeitbasierter Hunger-Verlust (10% pro Spielstunde)
- Verzehrbare Items
- UI-Anzeige
"""

import pygame

class HungerSystem:
    def __init__(self):
        # Hunger-Werte
        self.max_hunger = 100.0
        self.current_hunger = 100.0
        self.hunger_loss_per_hour = 1.5  # 1.5% pro Spielstunde (~67 Stunden = völlig hungrig)
        
        # Status
        self.is_starving = False  # Wenn Hunger unter 20%
        self.is_hungry = False    # Wenn Hunger unter 50%
        
        # UI
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        
        # Verzehrbare Items mit Hunger-Wiederherstellung
        self.food_items = {
            "carrot": {
                "hunger_restore": 25.0,  # Karotten stellen 25% Hunger wieder her
                "name": "Karotte",
                "description": "Knackige Karotte (+25% Hunger)"
            }
            # Hier können weitere verzehrbare Items hinzugefügt werden
        }
        
    def update(self, game_time):
        """Update des Hunger-Systems basierend auf Spielzeit"""
        if not game_time:
            return
            
        # Berechne Hunger-Verlust basierend auf verstrichener Spielzeit
        hours_passed = game_time.get_hours_passed_for_hunger() if hasattr(game_time, 'get_hours_passed_for_hunger') else 0
        
        # Reduziere Hunger
        hunger_loss = hours_passed * self.hunger_loss_per_hour
        self.current_hunger = max(0.0, self.current_hunger - hunger_loss)
        
        # Status aktualisieren
        self.is_starving = self.current_hunger < 20.0
        self.is_hungry = self.current_hunger < 50.0
        
    def eat_item(self, item_type, inventory=None):
        """Esse ein Item und stelle Hunger wieder her"""
        if item_type not in self.food_items:
            return False
            
        # Prüfe ob Item im Inventar ist (falls Inventar übergeben wurde)
        if inventory and not inventory.has_item(item_type):
            print(f"Keine {self.food_items[item_type]['name']} im Inventar!")
            return False
            
        # Hungerwert wiederherstellen
        restore_amount = self.food_items[item_type]["hunger_restore"]
        old_hunger = self.current_hunger
        self.current_hunger = min(self.max_hunger, self.current_hunger + restore_amount)
        
        # Item aus Inventar entfernen (falls Inventar übergeben wurde)
        if inventory:
            inventory.remove_item(item_type, 1)
            
        # Feedback
        actual_restore = self.current_hunger - old_hunger
        print(f"{self.food_items[item_type]['name']} gegessen! Hunger: +{actual_restore:.1f}% (jetzt: {self.current_hunger:.1f}%)")
        
        return True
        
    def get_hunger_percentage(self):
        """Gib Hunger als Prozentsatz zurück"""
        return (self.current_hunger / self.max_hunger) * 100
        
    def get_hunger_status(self):
        """Gib Hunger-Status als String zurück"""
        percentage = self.get_hunger_percentage()
        
        if percentage > 80:
            return "Satt"
        elif percentage > 50:
            return "Leicht hungrig"
        elif percentage > 20:
            return "Hungrig"
        else:
            return "Am Verhungern!"
            
    def get_hunger_color(self):
        """Gib Farbe für Hunger-Anzeige zurück"""
        percentage = self.get_hunger_percentage()
        
        if percentage > 60:
            return (100, 200, 100)  # Grün
        elif percentage > 40:
            return (200, 200, 100)  # Gelb
        elif percentage > 20:
            return (255, 150, 100)  # Orange
        else:
            return (255, 100, 100)  # Rot
            
    def is_food_item(self, item_type):
        """Prüfe ob ein Item essbar ist"""
        return item_type in self.food_items
        
    def get_food_info(self, item_type):
        """Gib Informationen über ein essbares Item zurück"""
        return self.food_items.get(item_type, None)
        
    def draw_hunger_ui(self, screen, x=10, y=200):
        """Zeichne die Hunger-UI"""
        # Hunger-Balken Hintergrund
        bar_width = 200
        bar_height = 20
        border_thickness = 2
        
        # Hintergrund-Rechteck
        bg_rect = pygame.Rect(x, y, bar_width + border_thickness * 2, bar_height + border_thickness * 2 + 30)
        pygame.draw.rect(screen, (40, 40, 50, 180), bg_rect)
        pygame.draw.rect(screen, (100, 100, 120), bg_rect, 1)
        
        # Label
        label_text = self.font.render("Hunger", True, (255, 255, 255))
        screen.blit(label_text, (x + 5, y + 5))
        
        # Hunger-Balken
        bar_rect = pygame.Rect(x + border_thickness, y + 25, bar_width, bar_height)
        
        # Balken-Hintergrund (dunkelgrau)
        pygame.draw.rect(screen, (60, 60, 60), bar_rect)
        
        # Hunger-Füllung
        fill_width = int((self.current_hunger / self.max_hunger) * bar_width)
        if fill_width > 0:
            fill_rect = pygame.Rect(x + border_thickness, y + 25, fill_width, bar_height)
            hunger_color = self.get_hunger_color()
            pygame.draw.rect(screen, hunger_color, fill_rect)
            
        # Balken-Rahmen
        pygame.draw.rect(screen, (200, 200, 200), bar_rect, 1)
        
        # Prozentsatz-Text
        percentage_text = f"{self.current_hunger:.1f}%"
        percent_surf = self.small_font.render(percentage_text, True, (255, 255, 255))
        percent_rect = percent_surf.get_rect(center=(x + bar_width//2 + border_thickness, y + 35))
        screen.blit(percent_surf, percent_rect)
        
        # Status-Text
        status_text = self.get_hunger_status()
        status_color = self.get_hunger_color()
        status_surf = self.small_font.render(status_text, True, status_color)
        screen.blit(status_surf, (x + bar_width + 15, y + 28))
        
        # Warnung bei niedrigem Hunger
        if self.is_starving:
            # Blinkende Warnung
            if (pygame.time.get_ticks() // 500) % 2:  # Blinkt alle 500ms
                warning_text = self.font.render("ESSEN BENÖTIGT!", True, (255, 100, 100))
                screen.blit(warning_text, (x, y + 55))
                
    def draw_eating_hint(self, screen, x=10, y=280):
        """Zeichne Hinweis zum Essen"""
        if self.is_hungry:
            hint_text = self.small_font.render("Tipp: Drücke 'E' um Essen aus dem Inventar zu verzehren", True, (200, 200, 100))
            screen.blit(hint_text, (x, y))