import pygame
import os
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from asset_manager import asset_manager

class InventorySlot:
    """Ein einzelner Inventar-Slot"""
    def __init__(self, item_type=None, quantity=0, max_stack=99):
        self.item_type = item_type  # "carrot", "carrot_seeds", etc.
        self.quantity = quantity
        self.max_stack = max_stack
        
    def is_empty(self):
        return self.item_type is None or self.quantity <= 0
        
    def can_add_item(self, item_type, quantity=1):
        """Prüfe ob Item hinzugefügt werden kann"""
        if self.is_empty():
            return True
        if self.item_type == item_type and (self.quantity + quantity) <= self.max_stack:
            return True
        return False
    
    def add_item(self, item_type, quantity=1):
        """Füge Items hinzu, gibt überschüssige Menge zurück"""
        if self.is_empty():
            self.item_type = item_type
            self.quantity = min(quantity, self.max_stack)
            return max(0, quantity - self.max_stack)
        elif self.item_type == item_type:
            space_left = self.max_stack - self.quantity
            added = min(quantity, space_left)
            self.quantity += added
            return quantity - added
        else:
            return quantity  # Kann nicht hinzufügen
    
    def remove_item(self, quantity=1):
        """Entferne Items, gibt entfernte Menge zurück"""
        if self.is_empty():
            return 0
        removed = min(quantity, self.quantity)
        self.quantity -= removed
        if self.quantity <= 0:
            self.item_type = None
            self.quantity = 0
        return removed
    
    def clear(self):
        """Slot leeren"""
        self.item_type = None
        self.quantity = 0

class Inventory:
    """Inventar-System mit 20 Slots und Stacking"""
    
    def __init__(self):
        self.slots = [InventorySlot() for _ in range(20)]  # 20 Slots
        self.visible = False
        self.slot_size = 48
        self.padding = 4
        self.slots_per_row = 5
        self.rows = 4
        
        # UI-Eigenschaften
        self.inventory_width = self.slots_per_row * (self.slot_size + self.padding) - self.padding
        self.inventory_height = self.rows * (self.slot_size + self.padding) - self.padding
        self.x = (SCREEN_WIDTH - self.inventory_width) // 2
        self.y = (SCREEN_HEIGHT - self.inventory_height) // 2
        
        # Fonts
        pygame.font.init()
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)
        
        # Item-Icons laden
        self.item_icons = self._load_item_icons()
        
        # Start-Items
        self._add_starter_items()
    
    def _load_item_icons(self):
        """Lade Icons für Items"""
        icons = {}
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Karotten-Icon (verwende Stufe 3 als Icon)
        carrot_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', 'Karotte_stufe3.png')
        if os.path.exists(carrot_path):
            try:
                icon_size = (self.slot_size - 8, self.slot_size - 8)
                icons['carrot'] = asset_manager.load_scaled_image('split/Farm/broccoli.png', icon_size)
                print("Karotten-Icon geladen!")
            except Exception as e:
                print(f"Fehler beim Laden des Karotten-Icons: {e}")
                icons['carrot'] = self._create_fallback_icon((255, 140, 0))  # Orange
        else:
            icons['carrot'] = self._create_fallback_icon((255, 140, 0))  # Orange
        
        # Karotten-Samen-Icon (verwende Stufe 1)
        seeds_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', 'Karotte_stufe1.png')
        if os.path.exists(seeds_path):
            try:
                img = pygame.image.load(seeds_path).convert_alpha()
                icons['carrot_seeds'] = pygame.transform.scale(img, (self.slot_size - 8, self.slot_size - 8))
                print("Karotten-Samen-Icon geladen!")
            except Exception as e:
                print(f"Fehler beim Laden des Samen-Icons: {e}")
                icons['carrot_seeds'] = self._create_fallback_icon((139, 69, 19))  # Braun
        else:
            icons['carrot_seeds'] = self._create_fallback_icon((139, 69, 19))  # Braun
        
        # Wood-Icon
        wood_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', 'wood.png')
        if os.path.exists(wood_path):
            try:
                img = pygame.image.load(wood_path).convert_alpha()
                icons['wood'] = pygame.transform.scale(img, (self.slot_size - 8, self.slot_size - 8))
                print("Holz-Icon geladen!")
            except Exception as e:
                print(f"Fehler beim Laden des Holz-Icons: {e}")
                icons['wood'] = self._create_fallback_icon((139, 69, 19))  # Braun
        else:
            icons['wood'] = self._create_fallback_icon((139, 69, 19))  # Braun
        
        # Stone-Icon (stein_barren.png)
        stone_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', 'stein_barren.png')
        if os.path.exists(stone_path):
            try:
                img = pygame.image.load(stone_path).convert_alpha()
                icons['stone'] = pygame.transform.scale(img, (self.slot_size - 8, self.slot_size - 8))
                print("Stein-Icon geladen!")
            except Exception as e:
                print(f"Fehler beim Laden des Stein-Icons: {e}")
                icons['stone'] = self._create_fallback_icon((128, 128, 128))  # Grau
        else:
            icons['stone'] = self._create_fallback_icon((128, 128, 128))  # Grau
        
        # Gold-Icon (gold_barren.png)
        gold_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', 'gold_barren.png')
        if os.path.exists(gold_path):
            try:
                img = pygame.image.load(gold_path).convert_alpha()
                icons['gold'] = pygame.transform.scale(img, (self.slot_size - 8, self.slot_size - 8))
                print("Gold-Icon geladen!")
            except Exception as e:
                print(f"Fehler beim Laden des Gold-Icons: {e}")
                icons['gold'] = self._create_fallback_icon((255, 215, 0))  # Gold-gelb
        else:
            icons['gold'] = self._create_fallback_icon((255, 215, 0))  # Gold-gelb
        
        return icons
    
    def _create_fallback_icon(self, color):
        """Erstelle Fallback-Icon"""
        surf = pygame.Surface((self.slot_size - 8, self.slot_size - 8), pygame.SRCALPHA)
        surf.fill(color)
        pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 2)
        return surf
    
    def _add_starter_items(self):
        """Füge Start-Items hinzu"""
        self.add_item("carrot_seeds", 20)  # 20 Karotten-Samen
        print("Start-Inventar: 20 Karotten-Samen hinzugefügt!")
    
    def toggle_visibility(self):
        """Inventar öffnen/schließen"""
        self.visible = not self.visible
        print(f"Inventar {'geöffnet' if self.visible else 'geschlossen'}")
    
    def add_item(self, item_type, quantity=1):
        """Füge Items zum Inventar hinzu"""
        remaining = quantity
        
        # Erst versuchen in bestehende Stacks zu füllen
        for slot in self.slots:
            if not slot.is_empty() and slot.item_type == item_type:
                remaining = slot.add_item(item_type, remaining)
                if remaining <= 0:
                    break
        
        # Dann neue Slots füllen
        if remaining > 0:
            for slot in self.slots:
                if slot.is_empty():
                    remaining = slot.add_item(item_type, remaining)
                    if remaining <= 0:
                        break
        
        added = quantity - remaining
        if added > 0:
            print(f"Inventar: +{added} {item_type}")
        if remaining > 0:
            print(f"Inventar voll! {remaining} {item_type} konnten nicht hinzugefügt werden!")
        
        return added
    
    def remove_item(self, item_type, quantity=1):
        """Entferne Items aus dem Inventar"""
        remaining = quantity
        
        # Von hinten nach vorne durchgehen (neueste Stacks zuerst)
        for slot in reversed(self.slots):
            if not slot.is_empty() and slot.item_type == item_type:
                removed = slot.remove_item(remaining)
                remaining -= removed
                if remaining <= 0:
                    break
        
        removed = quantity - remaining
        if removed > 0:
            print(f"Inventar: -{removed} {item_type}")
        
        return removed
    
    def has_item(self, item_type, quantity=1):
        """Prüfe ob genug Items vorhanden sind"""
        total = 0
        for slot in self.slots:
            if not slot.is_empty() and slot.item_type == item_type:
                total += slot.quantity
                if total >= quantity:
                    return True
        return False
    
    def get_item_count(self, item_type):
        """Gib Anzahl eines Items zurück"""
        total = 0
        for slot in self.slots:
            if not slot.is_empty() and slot.item_type == item_type:
                total += slot.quantity
        return total
    
    def handle_mouse_event(self, event, hunger_system=None):
        """Behandle Maus-Events für das Inventar"""
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            
            # Prüfe ob Klick im Inventar-Bereich
            if (self.x <= mouse_x <= self.x + self.inventory_width and 
                self.y <= mouse_y <= self.y + self.inventory_height):
                
                # Bestimme welcher Slot geklickt wurde
                rel_x = mouse_x - self.x
                rel_y = mouse_y - self.y
                
                slot_x = rel_x // (self.slot_size + self.padding)
                slot_y = rel_y // (self.slot_size + self.padding)
                
                if 0 <= slot_x < self.slots_per_row and 0 <= slot_y < self.rows:
                    slot_index = slot_y * self.slots_per_row + slot_x
                    if 0 <= slot_index < len(self.slots):
                        slot = self.slots[slot_index]
                        if not slot.is_empty():
                            # Prüfe ob es ein essbares Item ist
                            if hunger_system and hunger_system.is_food_item(slot.item_type):
                                # Esse das Item
                                if hunger_system.eat_item(slot.item_type, self):
                                    print(f"🍴 {slot.item_type} gegessen!")
                                else:
                                    print(f"Kann {slot.item_type} nicht essen!")
                            else:
                                print(f"Slot {slot_index}: {slot.quantity}x {slot.item_type}")
                
                return True  # Event verarbeitet
        
        return False
    
    def draw(self, screen):
        """Zeichne das Inventar"""
        if not self.visible:
            return
        
        # Inventar-Hintergrund
        bg_surface = pygame.Surface((self.inventory_width + 20, self.inventory_height + 60), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 200))  # Halbtransparent schwarz
        pygame.draw.rect(bg_surface, (100, 100, 100), bg_surface.get_rect(), 3)
        screen.blit(bg_surface, (self.x - 10, self.y - 30))
        
        # Titel
        title_text = self.font.render("Inventar (I zum Schließen)", True, (255, 255, 255))
        title_rect = title_text.get_rect(centerx=self.x + self.inventory_width // 2, y=self.y - 25)
        screen.blit(title_text, title_rect)
        
        # Slots zeichnen
        for i, slot in enumerate(self.slots):
            row = i // self.slots_per_row
            col = i % self.slots_per_row
            
            slot_x = self.x + col * (self.slot_size + self.padding)
            slot_y = self.y + row * (self.slot_size + self.padding)
            
            # Slot-Rahmen
            slot_color = (80, 80, 80) if slot.is_empty() else (120, 120, 120)
            slot_rect = pygame.Rect(slot_x, slot_y, self.slot_size, self.slot_size)
            pygame.draw.rect(screen, slot_color, slot_rect)
            pygame.draw.rect(screen, (200, 200, 200), slot_rect, 2)
            
            # Item-Icon und Anzahl
            if not slot.is_empty():
                # Icon zeichnen
                if slot.item_type in self.item_icons:
                    icon = self.item_icons[slot.item_type]
                    icon_x = slot_x + (self.slot_size - icon.get_width()) // 2
                    icon_y = slot_y + (self.slot_size - icon.get_height()) // 2
                    screen.blit(icon, (icon_x, icon_y))
                
                # Anzahl zeichnen (wenn > 1)
                if slot.quantity > 1:
                    quantity_text = self.small_font.render(str(slot.quantity), True, (255, 255, 255))
                    quantity_x = slot_x + self.slot_size - quantity_text.get_width() - 2
                    quantity_y = slot_y + self.slot_size - quantity_text.get_height() - 2
                    
                    # Schatten für bessere Lesbarkeit
                    shadow_text = self.small_font.render(str(slot.quantity), True, (0, 0, 0))
                    screen.blit(shadow_text, (quantity_x + 1, quantity_y + 1))
                    screen.blit(quantity_text, (quantity_x, quantity_y))
        
        # Inventar-Info unten
        info_y = self.y + self.inventory_height + 10
        
        # Karotten-Samen Anzahl
        seeds_count = self.get_item_count("carrot_seeds")
        seeds_text = self.small_font.render(f"Karotten-Samen: {seeds_count}", True, (255, 255, 255))
        screen.blit(seeds_text, (self.x, info_y))
        
        # Karotten Anzahl
        carrots_count = self.get_item_count("carrot")
        carrots_text = self.small_font.render(f"Karotten: {carrots_count}", True, (255, 215, 100))
        screen.blit(carrots_text, (self.x + 150, info_y))
        
        # Hinweis zum Essen
        if carrots_count > 0:
            eat_hint = self.small_font.render("💡 Karotten anklicken oder 'E' drücken zum Essen", True, (150, 255, 150))
            screen.blit(eat_hint, (self.x, info_y + 18))
