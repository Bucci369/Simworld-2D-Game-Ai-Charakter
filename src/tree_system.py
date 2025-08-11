"""
Tree Chopping System - Bäume fällen mit Hitboxen und HP
"""

import pygame
import math
import random
import os

class WoodDrop:
    """Ein sammelbarer Holz-Drop neben einem Baumstumpf"""
    def __init__(self, x, y, wood_image):
        self.x = x
        self.y = y
        self.wood_image = wood_image
        self.collected = False
        
        # Hitbox für Sammeln
        self.rect = pygame.Rect(x, y, wood_image.get_width(), wood_image.get_height())
        
        # Glow-Effekt Animation
        self.glow_time = 0.0
        self.glow_intensity = 0.5
        
        # Kleine Bounce-Animation
        self.bounce_time = random.uniform(0, math.pi * 2)  # Random start
        self.original_y = y
        
    def update(self, dt):
        """Update Animationen"""
        if self.collected:
            return
            
        # Glow pulsiert
        self.glow_time += dt * 3  # 3x Geschwindigkeit
        self.glow_intensity = 0.3 + 0.4 * math.sin(self.glow_time)  # 0.3 bis 0.7
        
        # Leichtes Auf-und-Ab (Bounce)
        self.bounce_time += dt * 2
        bounce_offset = math.sin(self.bounce_time) * 2  # 2 Pixel auf/ab
        self.y = self.original_y + bounce_offset
        
    def draw(self, screen, camera_rect):
        """Zeichne Wood-Drop mit Bounce-Effekt"""
        if self.collected:
            return
            
        screen_x = self.x - camera_rect.left
        screen_y = self.y - camera_rect.top
        
        # Zeichne Wood-Sprite (mit bounce)
        screen.blit(self.wood_image, (screen_x, screen_y))
        
    def is_mouse_over(self, mouse_world_pos):
        """Prüfe ob Maus über Wood ist"""
        return not self.collected and self.rect.collidepoint(mouse_world_pos)
        
    def collect(self):
        """Sammle das Holz"""
        if not self.collected:
            self.collected = True
            print("🪵 Holz gesammelt! +5 Wood")
            return 5  # 5 Holz pro Drop
        return 0

class Tree:
    """Ein schlagbarer Baum mit HP und Hitbox"""
    def __init__(self, x, y, tree_image):
        self.x = x
        self.y = y
        self.max_hp = 100
        self.current_hp = 100
        self.alive = True
        
        # Images
        self.tree_image = tree_image
        self.stump_image = None  # Wird erst bei Fällung erstellt!
        self.current_image = tree_image
        
        # Hitbox (etwas kleiner als das Bild für bessere Spielbarkeit)
        self.rect = pygame.Rect(x, y, tree_image.get_width(), tree_image.get_height())
        self.hitbox = pygame.Rect(
            x + tree_image.get_width() * 0.2,
            y + tree_image.get_height() * 0.3,
            tree_image.get_width() * 0.6,
            tree_image.get_height() * 0.7
        )
        
        # Animation
        self.shake_time = 0.0
        self.shake_intensity = 0.0
        self.original_x = x
        
        # HP Bar
        self.show_hp_bar = False
        self.hp_bar_timer = 0.0
        
    def take_damage(self, damage=25):
        """Baum nimmt Schaden"""
        if not self.alive:
            return False
            
        self.current_hp -= damage
        self.show_hp_bar = True
        self.hp_bar_timer = 3.0  # 3 Sekunden HP-Bar anzeigen
        
        # Schüttel-Animation
        self.shake_time = 0.3  # 300ms schütteln
        self.shake_intensity = 5.0
        
        print(f"🪓 Baum getroffen! HP: {self.current_hp}/{self.max_hp}")
        
        # Baum gefällt?
        if self.current_hp <= 0:
            wood_pos = self.fell_tree()
            return wood_pos  # Gib Wood-Position zurück statt nur True
        
        return False
        
    def fell_tree(self):
        """Baum fällen - zu Stumpf machen und Wood droppen"""
        if not self.alive:
            return None
            
        self.alive = False
        print("🌳 TIMBER! Baum gefällt!")
        
        # Erstelle Stumpf-Sprite aus dem Baum
        self.stump_image = self._create_stump_from_tree()
        self.current_image = self.stump_image
        
        # Stumpf ist kleiner - Position anpassen
        stump_width = self.stump_image.get_width()
        stump_height = self.stump_image.get_height()
        
        # Zentriere Stumpf genau unter dem ursprünglichen Baum
        # Verwende die ursprüngliche Position und zentriere horizontal
        tree_center_x = self.original_x + self.tree_image.get_width() // 2
        stump_x = tree_center_x - stump_width // 2
        
        # Stumpf am unteren Rand des ursprünglichen Baums platzieren
        tree_bottom_y = self.y + self.tree_image.get_height()
        stump_y = tree_bottom_y - stump_height
        
        self.x = stump_x
        self.y = stump_y
        
        self.rect = pygame.Rect(self.x, self.y, stump_width, stump_height)
        self.hitbox = pygame.Rect(self.x, self.y, stump_width, stump_height)
        
        self.show_hp_bar = False
        
        # Erstelle Wood-Drop direkt hier (nicht nur Position zurückgeben)
        wood_x = self.x + stump_width + 10  # 10 Pixel Abstand
        wood_y = self.y + stump_height - 20  # Etwas über dem Boden
        return (wood_x, wood_y)
        
    def _create_stump_from_tree(self):
        """Erstelle einen Stumpf-Sprite (lade erst echte stumpf.png, dann Fallback)"""
        # Versuche erst das echte stumpf.png zu laden
        base_dir = os.path.dirname(os.path.dirname(__file__))
        stump_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', 'stumpf.png')
        
        if os.path.exists(stump_path):
            try:
                original_stump = pygame.image.load(stump_path).convert_alpha()
                orig_w, orig_h = original_stump.get_size()
                
                # Skaliere auf sinnvolle Größe (etwa 24-32 Pixel breit)
                scale_factor = max(24 / orig_w, 20 / orig_h, 3.0)  # Mindestens 3x vergrößern
                new_width = int(orig_w * scale_factor)
                new_height = int(orig_h * scale_factor)
                
                scaled_stump = pygame.transform.scale(original_stump, (new_width, new_height))
                print(f"🪵 Stumpf skaliert: {orig_w}x{orig_h} → {new_width}x{new_height}")
                return scaled_stump
            except Exception as e:
                print(f"⚠️ Fehler beim Laden von stumpf.png: {e}")
        
        # Fallback: Generiere Stumpf aus Baum
        print("🔨 Generiere Stumpf aus Baum...")
        tree_width = self.tree_image.get_width()
        tree_height = self.tree_image.get_height()
        
        # Größerer Stumpf für bessere Sichtbarkeit
        stump_height = max(24, int(tree_height * 0.3))
        stump_width = max(32, int(tree_width * 0.8))
        
        # Erstelle Stumpf-Surface
        stump = pygame.Surface((stump_width, stump_height), pygame.SRCALPHA)
        
        try:
            # Nimm den unteren Teil des Baums als Basis
            source_rect = pygame.Rect(
                (tree_width - stump_width) // 2,  # Zentriert
                tree_height - int(tree_height * 0.4),  # Untere 40%
                min(stump_width, tree_width),
                min(int(tree_height * 0.4), tree_height)
            )
            
            # Stelle sicher, dass source_rect innerhalb der Bildgrenzen liegt
            if source_rect.right > tree_width:
                source_rect.width = tree_width - source_rect.x
            if source_rect.bottom > tree_height:
                source_rect.height = tree_height - source_rect.y
                
            # Kopiere und skaliere den unteren Baumteil
            if source_rect.width > 0 and source_rect.height > 0:
                tree_bottom = pygame.Surface((source_rect.width, source_rect.height), pygame.SRCALPHA)
                tree_bottom.blit(self.tree_image, (0, 0), source_rect)
                stump_base = pygame.transform.scale(tree_bottom, (stump_width, stump_height))
                stump.blit(stump_base, (0, 0))
            else:
                # Falls source_rect ungültig, fülle mit Braun
                stump.fill((101, 67, 33))
            
            # Füge deutlichere "Schnittfläche" oben hinzu
            cut_color = (160, 100, 60)  # Hellere braune Schnittfläche
            pygame.draw.ellipse(stump, cut_color, (4, 0, stump_width-8, stump_height//2))
            
            # Ring-Strukturen für realistischen Look
            center_x = stump_width // 2
            center_y = stump_height // 4
            for i in range(1, 4):
                ring_radius = max(3, (stump_width // 2 - 6) - i * 4)
                ring_color = (80 + i*10, 50 + i*5, 20 + i*3)
                pygame.draw.circle(stump, ring_color, (center_x, center_y), ring_radius, 2)
            
            # Rand für bessere Sichtbarkeit
            pygame.draw.ellipse(stump, (60, 40, 20), (0, 0, stump_width, stump_height//2), 2)
            
            print(f"🪵 Generierter Stumpf: {stump_width}x{stump_height} aus Baum {tree_width}x{tree_height}")
            
        except Exception as e:
            print(f"⚠️ Stumpf-Generierung fehlgeschlagen: {e}")
            # Ultimate Fallback: Einfacher sichtbarer Stumpf
            stump.fill((101, 67, 33))
            pygame.draw.ellipse(stump, (160, 100, 60), (4, 0, stump_width-8, stump_height//2))
            pygame.draw.ellipse(stump, (60, 40, 20), stump.get_rect(), 3)
            
        return stump
        
    def update(self, dt):
        """Update Animationen"""
        # Schüttel-Animation
        if self.shake_time > 0:
            self.shake_time -= dt
            shake_offset = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            self.x = self.original_x + shake_offset
            
            # Shake-Intensität abnehmen
            self.shake_intensity = max(0, self.shake_intensity - dt * 15)
        else:
            self.x = self.original_x
            
        # HP-Bar Timer
        if self.hp_bar_timer > 0:
            self.hp_bar_timer -= dt
            if self.hp_bar_timer <= 0:
                self.show_hp_bar = False
                
    def draw(self, screen, camera_rect):
        """Zeichne den Baum"""
        screen_x = self.x - camera_rect.left
        screen_y = self.y - camera_rect.top
        
        screen.blit(self.current_image, (screen_x, screen_y))
        
        # HP-Balken zeichnen (nur bei lebenden, beschädigten Bäumen)
        if self.alive and self.show_hp_bar and self.current_hp < self.max_hp:
            self.draw_hp_bar(screen, screen_x, screen_y)
            
    def draw_hp_bar(self, screen, screen_x, screen_y):
        """Zeichne HP-Balken über dem Baum"""
        bar_width = 40
        bar_height = 6
        bar_x = screen_x + (self.current_image.get_width() - bar_width) // 2
        bar_y = screen_y - 15
        
        # Hintergrund (rot)
        background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (100, 100, 100), background_rect)
        
        # HP-Füllung (grün bis rot)
        hp_percentage = self.current_hp / self.max_hp
        fill_width = int(bar_width * hp_percentage)
        
        if fill_width > 0:
            # Farbe je nach HP
            if hp_percentage > 0.6:
                color = (100, 200, 100)  # Grün
            elif hp_percentage > 0.3:
                color = (200, 200, 100)  # Gelb
            else:
                color = (200, 100, 100)  # Rot
                
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            pygame.draw.rect(screen, color, fill_rect)
        
        # Rahmen
        pygame.draw.rect(screen, (255, 255, 255), background_rect, 1)
        
    def is_mouse_over(self, mouse_world_pos):
        """Prüfe ob Maus über Hitbox ist"""
        return self.hitbox.collidepoint(mouse_world_pos)


class TreeSystem:
    """Verwaltet alle Bäume in der Welt"""
    def __init__(self, simple_world=None):
        self.trees = []
        self.wood_drops = []  # Liste aller Wood-Drops
        self.simple_world = simple_world
        
        # Lade Wood-Sprite
        self.wood_image = self._load_wood_image()
        
        # Konvertiere existierende Bäume aus SimpleWorld
        if simple_world:
            self._convert_existing_trees()
            
    def _load_wood_image(self):
        """Lade Wood-Sprite"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        wood_path = os.path.join(base_dir, 'assets', 'Outdoor decoration', 'wood.png')
        
        if os.path.exists(wood_path):
            try:
                wood_image = pygame.image.load(wood_path).convert_alpha()
                print(f"🪵 Wood-Sprite geladen: {wood_image.get_size()}")
                return wood_image
            except Exception as e:
                print(f"⚠️ Fehler beim Laden von wood.png: {e}")
                
        # Fallback: Einfacher brauner Block
        fallback = pygame.Surface((16, 12), pygame.SRCALPHA)
        fallback.fill((139, 69, 19))  # Braun
        pygame.draw.rect(fallback, (160, 82, 45), (2, 2, 12, 8))  # Hellerer Kern
        print("🪵 Fallback-Wood erstellt!")
        return fallback
            
        
    def _convert_existing_trees(self):
        """Konvertiere bestehende Bäume aus SimpleWorld zu Tree-Objekten"""
        if not self.simple_world or not hasattr(self.simple_world, 'trees'):
            return
            
        tree_image = self.simple_world.oak_tree
        
        for tree_x, tree_y in self.simple_world.trees:
            tree = Tree(tree_x, tree_y, tree_image)
            self.trees.append(tree)
            
        print(f"🌳 {len(self.trees)} Bäume zu Tree-System konvertiert!")
        
        # Entferne original Bäume aus SimpleWorld (werden jetzt von TreeSystem gezeichnet)
        self.simple_world.trees.clear()
        
    def handle_click(self, world_pos, player_pos, inventory=None):
        """Handle Mausklick auf Bäume und Wood-Drops"""
        mouse_x, mouse_y = world_pos
        player_x, player_y = player_pos
        
        # Prüfe zuerst Wood-Drops (haben Priorität)
        for wood_drop in self.wood_drops:
            if wood_drop.is_mouse_over((mouse_x, mouse_y)):
                # Prüfe Entfernung zum Spieler
                distance = math.sqrt((wood_drop.x - player_x)**2 + (wood_drop.y - player_y)**2)
                
                if distance <= 60:  # Etwas größere Reichweite für Sammeln
                    wood_amount = wood_drop.collect()
                    if wood_amount > 0 and inventory:
                        # Füge Holz zum Inventar hinzu
                        inventory.add_item("wood", wood_amount)
                        # Entferne gesammelten Drop aus Liste
                        self.wood_drops.remove(wood_drop)
                    return True
                else:
                    print("🚶 Zu weit weg! Gehe näher zum Holz.")
                    return False
        
        # Dann prüfe Bäume
        for tree in self.trees:
            if tree.alive and tree.is_mouse_over((mouse_x, mouse_y)):
                # Prüfe Entfernung zum Spieler
                distance = math.sqrt((tree.x - player_x)**2 + (tree.y - player_y)**2)
                
                if distance <= 50:
                    result = tree.take_damage(25)  # 25% Schaden
                    
                    # Wenn Baum gefällt wurde, erstelle Wood-Drop
                    if result and result != False:  # result ist entweder False oder (x, y) Position
                        wood_pos = result
                        wood_drop = WoodDrop(wood_pos[0], wood_pos[1], self.wood_image)
                        self.wood_drops.append(wood_drop)
                        print("🪵 Holz ist erschienen! Klicke darauf zum Sammeln.")
                    
                    return True
                else:
                    print("🚶 Zu weit weg! Gehe näher an den Baum.")
                    return False
        
        return False
        
    def update(self, dt):
        """Update alle Bäume und Wood-Drops"""
        for tree in self.trees:
            tree.update(dt)
            
        # Update Wood-Drops (Glow-Animation)
        for wood_drop in self.wood_drops:
            wood_drop.update(dt)
            
    def draw(self, screen, camera_rect):
        """Zeichne alle Bäume und Wood-Drops (sortiert nach Y-Position für korrektes Layering)"""
        # Sortiere Bäume nach Y-Position (Painter's Algorithm)
        visible_trees = [tree for tree in self.trees if tree.rect.colliderect(camera_rect)]
        visible_trees.sort(key=lambda t: t.y + t.current_image.get_height())
        
        for tree in visible_trees:
            tree.draw(screen, camera_rect)
            
        # Zeichne Wood-Drops (nach Bäumen, damit sie sichtbar sind)
        for wood_drop in self.wood_drops:
            if not wood_drop.collected:
                wood_drop.draw(screen, camera_rect)
            
    def get_collision_rects(self):
        """Gib Kollisions-Rechtecke für lebende Bäume zurück"""
        return [tree.hitbox for tree in self.trees if tree.alive]