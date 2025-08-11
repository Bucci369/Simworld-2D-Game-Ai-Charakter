"""
Game Time System - 24 Spielstunden = 15 echte Minuten
"""

import pygame
import time
import json
import math
import random
from pathlib import Path

class GameTime:
    def __init__(self):
        # Zeit-Konfiguration
        self.real_seconds_per_game_day = 15 * 60  # 15 Minuten = 1 Spieltag
        self.real_seconds_per_game_hour = self.real_seconds_per_game_day / 24  # ~37.5 Sekunden = 1 Spielstunde
        self.real_seconds_per_game_minute = self.real_seconds_per_game_hour / 60  # ~0.625 Sekunden = 1 Spielminute
        
        # Spielzeit (Startet um 6:00 Uhr morgens)
        self.game_hours = 6
        self.game_minutes = 0
        self.game_day = 1
        
        # Tracking
        self.start_real_time = time.time()
        self.last_update_time = time.time()
        self.last_farming_update = time.time()  # Für Farming-System
        self.last_hunger_update = time.time()   # Für Hunger-System (separat!)
        self.paused = False
        self.time_speed = 1.0  # Zeitgeschwindigkeit (1.0 = normal, 2.0 = doppelt so schnell)
        
        # Font für UI
        pygame.font.init()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.button_font = pygame.font.Font(None, 20)
        
        # UI Button Rectangles (werden in draw_time_ui gesetzt)
        self.ui_buttons = {}
        self.ui_rect = None
        self.hovered_button = None
        
    def update(self):
        """Aktualisiere die Spielzeit basierend auf echter Zeit"""
        if self.paused:
            self.last_update_time = time.time()
            return
            
        current_real_time = time.time()
        real_time_passed = (current_real_time - self.last_update_time) * self.time_speed
        self.last_update_time = current_real_time
        
        # Konvertiere echte Zeit zu Spielzeit
        game_minutes_passed = real_time_passed / self.real_seconds_per_game_minute
        
        # Addiere die verstrichenen Minuten
        self.game_minutes += game_minutes_passed
        
        # Handle Überlauf
        while self.game_minutes >= 60:
            self.game_minutes -= 60
            self.game_hours += 1
            
        while self.game_hours >= 24:
            self.game_hours -= 24
            self.game_day += 1
            print(f"Neuer Tag! Tag {self.game_day}")
            
    def get_time_string(self):
        """Gib die Zeit als String zurück (HH:MM)"""
        hours = int(self.game_hours)
        minutes = int(self.game_minutes)
        return f"{hours:02d}:{minutes:02d}"
        
    def get_day_period(self):
        """Gib die Tageszeit zurück"""
        hour = int(self.game_hours)
        if 5 <= hour < 12:
            return "Morgen"
        elif 12 <= hour < 18:
            return "Mittag"
        elif 18 <= hour < 22:
            return "Abend"
        else:
            return "Nacht"
            
    def get_day_string(self):
        """Gib den Tag als String zurück"""
        return f"Tag {self.game_day}"
        
    def is_day(self):
        """Prüfe ob es Tag ist (5:30 - 19:30)"""
        current_time = self.game_hours + (self.game_minutes / 60)
        return 5.5 <= current_time < 19.5
        
    def is_night(self):
        """Prüfe ob es Nacht ist"""
        return not self.is_day()
        
    def get_hours_passed(self):
        """Gib die verstrichenen Spielstunden seit letztem Aufruf zurück (für Farming)"""
        if self.paused:
            self.last_farming_update = time.time()
            return 0.0
            
        current_real_time = time.time()
        real_time_passed = (current_real_time - self.last_farming_update) * self.time_speed
        self.last_farming_update = current_real_time
        
        # Konvertiere echte Zeit zu Spielstunden
        game_hours_passed = real_time_passed / self.real_seconds_per_game_hour
        return game_hours_passed
        
    def get_hours_passed_for_hunger(self):
        """Gib die verstrichenen Spielstunden seit letztem Aufruf zurück (für Hunger-System)"""
        if self.paused:
            self.last_hunger_update = time.time()
            return 0.0
            
        current_real_time = time.time()
        real_time_passed = (current_real_time - self.last_hunger_update) * self.time_speed
        self.last_hunger_update = current_real_time
        
        # Konvertiere echte Zeit zu Spielstunden
        game_hours_passed = real_time_passed / self.real_seconds_per_game_hour
        return game_hours_passed
        
    def get_daylight_factor(self):
        """Gib einen Helligkeitsfaktor zurück (0.0 = dunkel, 1.0 = hell)"""
        hour = self.game_hours
        
        if 5 <= hour < 6:  # Morgendämmerung
            return 0.4 + 0.6 * ((hour - 5))  # 0.4 bis 1.0
        elif 6 <= hour <= 8:  # Früher Morgen
            return 1.0
        elif 8 < hour <= 16:  # Voller Tag
            return 1.0
        elif 16 < hour <= 18:  # Nachmittag
            return 1.0
        elif 18 < hour <= 20:  # Abenddämmerung
            return 1.0 - 0.7 * ((hour - 18) / 2)  # 1.0 bis 0.3
        elif 20 < hour <= 22:  # Späte Dämmerung
            return 0.3 - 0.1 * ((hour - 20) / 2)  # 0.3 bis 0.2
        else:  # Tiefe Nacht (22:00 - 5:00)
            return 0.2  # Sehr dunkel!
            
    def get_sun_position(self, screen_width, screen_height):
        """Berechne die Position der Sonne am Himmel"""
        # Sonne geht um 5:30 auf und um 19:30 unter (längere Tageszeit)
        sunrise_hour = 5.5
        sunset_hour = 19.5
        
        if self.game_hours + (self.game_minutes / 60) < sunrise_hour or self.game_hours + (self.game_minutes / 60) > sunset_hour:
            # Nacht - Sonne ist "unter" dem Horizont
            return None
            
        # Berechne Sonnenposition (Bogen über den Himmel)
        total_daylight_hours = sunset_hour - sunrise_hour  # 14 Stunden Tageslicht
        hours_since_sunrise = self.game_hours + (self.game_minutes / 60) - sunrise_hour
        
        if hours_since_sunrise < 0:
            hours_since_sunrise = 0
        elif hours_since_sunrise > total_daylight_hours:
            hours_since_sunrise = total_daylight_hours
            
        # Fortschritt durch den Tag (0.0 bis 1.0)
        day_progress = hours_since_sunrise / total_daylight_hours
        
        # X-Position: von links nach rechts
        sun_x = int(screen_width * day_progress)
        
        # Y-Position: Bogen (niedrig am Morgen/Abend, hoch am Mittag)
        import math
        # Sinus-Kurve für den Bogen
        sun_angle = day_progress * math.pi  # 0 bis π
        sun_height_factor = math.sin(sun_angle)
        
        # Sonne startet und endet am Horizont (80% der Bildschirmhöhe)
        # und erreicht am Mittag etwa 20% der Bildschirmhöhe
        horizon_y = int(screen_height * 0.8)
        max_height_y = int(screen_height * 0.2)
        sun_y = horizon_y - int((horizon_y - max_height_y) * sun_height_factor)
        
        return (sun_x, sun_y)
        
    def get_light_color(self):
        """Gib die Lichtfarbe basierend auf der Tageszeit zurück"""
        hour = self.game_hours
        
        if 5 <= hour < 7:  # Früher Morgen - orange/rot
            return (255, 200, 150)
        elif 7 <= hour < 9:  # Morgen - gelb-orange
            return (255, 220, 180)
        elif 9 <= hour < 17:  # Tag - weißes Licht
            return (255, 255, 255)
        elif 17 <= hour < 19:  # Abend - orange
            return (255, 200, 150)
        elif 19 <= hour < 21:  # Späte Dämmerung - rot-orange
            return (255, 150, 100)
        else:  # Nacht - bläulich
            return (150, 150, 200)
            
    def get_shadow_overlay(self, screen_width, screen_height):
        """Erstelle eine Schatten-Overlay-Surface für Tag/Nacht-Zyklen"""
        overlay = pygame.Surface((screen_width, screen_height))
        
        daylight = self.get_daylight_factor()
        
        # Berechne Lichtfarbe basierend auf der Tageszeit
        if self.is_day():
            # Tag: Weißes/warmes Licht
            if 6 <= self.game_hours <= 8:  # Morgen
                light_color = (255, 240, 200)  # Warmes Morgenlicht
            elif 9 <= self.game_hours <= 16:  # Mittag
                light_color = (255, 255, 255)  # Neutrales Tageslicht
            else:  # Abend (17-19)
                light_color = (255, 200, 150)  # Warmes Abendlicht
        else:
            # Nacht: Bläuliches Mondlicht
            light_color = (150, 180, 220)  # Kühles Mondlicht
            
        # Lichtintensität (umgekehrt proportional zur Helligkeit)
        # Je dunkler es wird, desto mehr färbt sich alles
        light_intensity = 1.0 - daylight
        
        # Berechne finale Farbe
        final_r = int(light_color[0] * (1 - light_intensity * 0.8))
        final_g = int(light_color[1] * (1 - light_intensity * 0.8))
        final_b = int(light_color[2] * (1 - light_intensity * 0.8))
        
        overlay.fill((final_r, final_g, final_b))
        return overlay
            
    def pause(self):
        """Pausiere die Zeit"""
        self.paused = True
        
    def resume(self):
        """Setze die Zeit fort"""
        self.paused = False
        self.last_update_time = time.time()
        
    def set_time_speed(self, speed):
        """Setze die Zeitgeschwindigkeit (1.0 = normal)"""
        self.time_speed = max(0.1, min(10.0, speed))  # Begrenzt zwischen 0.1x und 10x
        
    def set_time(self, hours, minutes=0):
        """Setze die Spielzeit manuell"""
        self.game_hours = max(0, min(23, hours))
        self.game_minutes = max(0, min(59, minutes))
        
    def advance_time(self, hours=0, minutes=0):
        """Springe in der Zeit vorwärts"""
        self.game_minutes += minutes
        self.game_hours += hours
        
        while self.game_minutes >= 60:
            self.game_minutes -= 60
            self.game_hours += 1
            
        while self.game_hours >= 24:
            self.game_hours -= 24
            self.game_day += 1
            
    def draw_time_ui(self, screen, x=10, y=10):
        """Zeichne die Zeit-UI auf den Bildschirm als elegantes, klickbares Spielelement"""
        # Größere, elegantere UI
        ui_width = 400
        ui_height = 180
        
        # Speichere UI Rect für Event-Handling
        self.ui_rect = pygame.Rect(x, y, ui_width, ui_height)
        self.ui_buttons = {}
        
        # Eleganter Hintergrund mit Gradient-Effekt
        time_bg = pygame.Surface((ui_width, ui_height), pygame.SRCALPHA)
        
        # Gradient Hintergrund
        for i in range(ui_height):
            alpha = int(120 + 40 * (1 - i / ui_height))
            color = (20 + i//3, 20 + i//4, 30 + i//3, alpha)
            pygame.draw.rect(time_bg, color, (0, i, ui_width, 1))
        
        # Schöner Rahmen
        pygame.draw.rect(time_bg, (100, 150, 200), time_bg.get_rect(), 3)
        pygame.draw.rect(time_bg, (200, 220, 255), time_bg.get_rect(), 1)
        screen.blit(time_bg, (x, y))
        
        # Große Zeit-Anzeige mit Schatten
        time_str = self.get_time_string()
        
        # Schatten für die Zeit
        shadow_text = self.font.render(time_str, True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect(centerx=x + ui_width//2 + 2, y=y + 17)
        screen.blit(shadow_text, shadow_rect)
        
        # Hauptzeit
        time_text = self.font.render(time_str, True, (255, 255, 255))
        time_rect = time_text.get_rect(centerx=x + ui_width//2, y=y + 15)
        screen.blit(time_text, time_rect)
        
        # Tag und Tageszeit in einer Zeile
        day_period_text = self.small_font.render(f"{self.get_day_string()} • {self.get_day_period()}", True, (255, 215, 100))
        day_rect = day_period_text.get_rect(centerx=x + ui_width//2, y=y + 55)
        screen.blit(day_period_text, day_rect)
        
        # Erweiterte Sonnen-/Mond-Anzeige
        sky_rect = pygame.Rect(x + 20, y + 80, ui_width - 40, 50)
        
        # Schöner Himmel-Gradient
        daylight = self.get_daylight_factor()
        if self.is_day():
            # Tag: Schöner Himmel-Gradient
            for i in range(sky_rect.height):
                intensity = daylight
                top_color = (int(100 * intensity), int(150 * intensity), int(255 * intensity))
                bottom_color = (int(200 * intensity), int(220 * intensity), int(255 * intensity))
                
                # Interpoliere zwischen oben und unten
                ratio = i / sky_rect.height
                r = int(top_color[0] * (1-ratio) + bottom_color[0] * ratio)
                g = int(top_color[1] * (1-ratio) + bottom_color[1] * ratio)
                b = int(top_color[2] * (1-ratio) + bottom_color[2] * ratio)
                
                pygame.draw.rect(screen, (r, g, b), (sky_rect.x, sky_rect.y + i, sky_rect.width, 1))
        else:
            # Nacht: Dunkler Gradient mit Sternen-Effekt
            for i in range(sky_rect.height):
                intensity = daylight
                r = int(20 + 30 * intensity)
                g = int(20 + 40 * intensity)
                b = int(60 + 80 * intensity)
                pygame.draw.rect(screen, (r, g, b), (sky_rect.x, sky_rect.y + i, sky_rect.width, 1))
            
            # Sterne bei Nacht
            import random
            random.seed(42)
            for _ in range(12):
                star_x = sky_rect.x + random.randint(5, sky_rect.width - 5)
                star_y = sky_rect.y + random.randint(5, sky_rect.height - 5)
                star_brightness = random.randint(150, 255)
                pygame.draw.circle(screen, (star_brightness, star_brightness, star_brightness), (star_x, star_y), 1)
                # Gelegentlich funkelnde Sterne
                if random.random() < 0.3:
                    pygame.draw.circle(screen, (255, 255, 255), (star_x, star_y), 2)
        
        pygame.draw.rect(screen, (255, 255, 255), sky_rect, 2)
        
        # Sonne/Mond mit besseren Effekten
        sun_pos = self.get_sun_position(sky_rect.width, sky_rect.height)
        if sun_pos:
            sun_x, sun_y = sun_pos
            sun_screen_x = sky_rect.x + sun_x
            sun_screen_y = sky_rect.y + sun_y
            
            light_color = self.get_light_color()
            
            # Sonne mit Aura und Animation
            time_factor = pygame.time.get_ticks() * 0.003
            for radius in range(15, 6, -2):
                alpha = int(80 * (1 - radius / 15))
                pulsing = 1 + 0.1 * math.sin(time_factor + radius)
                actual_radius = int(radius * pulsing)
                
                sun_surface = pygame.Surface((actual_radius*2, actual_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(sun_surface, (*light_color, alpha), (actual_radius, actual_radius), actual_radius)
                screen.blit(sun_surface, (sun_screen_x - actual_radius, sun_screen_y - actual_radius))
            
            # Sonnenkern
            pygame.draw.circle(screen, (255, 255, 200), (sun_screen_x, sun_screen_y), 6)
            
            # Animierte Sonnenstrahlen
            for i in range(8):
                angle = i * math.pi / 4 + time_factor
                length = 12 + 3 * math.sin(time_factor * 2 + i)
                start_x = sun_screen_x + math.cos(angle) * 8
                start_y = sun_screen_y + math.sin(angle) * 8
                end_x = sun_screen_x + math.cos(angle) * length
                end_y = sun_screen_y + math.sin(angle) * length
                pygame.draw.line(screen, light_color, (start_x, start_y), (end_x, end_y), 2)
        else:
            # Schöner Mond mit Kratern
            moon_x = sky_rect.x + sky_rect.width // 2
            moon_y = sky_rect.y + sky_rect.height // 3
            
            # Mondschein-Aura
            for radius in range(12, 6, -1):
                alpha = int(40 * (1 - radius / 12))
                moon_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(moon_surface, (200, 220, 255, alpha), (radius, radius), radius)
                screen.blit(moon_surface, (moon_x - radius, moon_y - radius))
            
            # Mond
            pygame.draw.circle(screen, (240, 240, 240), (moon_x, moon_y), 8)
            # Krater
            pygame.draw.circle(screen, (200, 200, 200), (moon_x - 2, moon_y - 1), 2)
            pygame.draw.circle(screen, (210, 210, 210), (moon_x + 1, moon_y + 2), 1)
            pygame.draw.circle(screen, (190, 190, 190), (moon_x - 1, moon_y + 3), 1)
        
        # Klickbare Control-Buttons (untere Reihe)
        button_y = y + ui_height - 45
        button_height = 25
        button_spacing = 5
        
        # Zeitsteuerungs-Buttons
        buttons = [
            ("⏸" if not self.paused else "▶", "pause", (100, 200, 100) if not self.paused else (255, 100, 100)),
            ("−", "slower", (200, 150, 100)),
            ("1x", "normal", (150, 150, 150)),
            ("+", "faster", (200, 150, 100)),
        ]
        
        button_width = 35
        start_x = x + 20
        
        for i, (symbol, action, color) in enumerate(buttons):
            button_x = start_x + i * (button_width + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            self.ui_buttons[action] = button_rect
            
            # Button-Stil mit Hover-Effekt
            if self.hovered_button == action:
                button_color = tuple(min(255, c + 30) for c in color)
                pygame.draw.rect(screen, button_color, button_rect)
                pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)
            else:
                pygame.draw.rect(screen, color, button_rect)
                pygame.draw.rect(screen, (200, 200, 200), button_rect, 1)
            
            # Button-Text
            text = self.button_font.render(symbol, True, (255, 255, 255))
            text_rect = text.get_rect(center=button_rect.center)
            screen.blit(text, text_rect)
        
        # Schnell-Zeit-Buttons (rechte Seite)
        time_buttons = [
            ("🌅", "morning", (255, 200, 100)),
            ("☀️", "noon", (255, 255, 100)),
            ("🌆", "evening", (255, 150, 100)),
            ("🌙", "night", (100, 100, 200)),
        ]
        
        time_button_width = 30
        time_start_x = x + ui_width - 140
        
        for i, (symbol, action, color) in enumerate(time_buttons):
            button_x = time_start_x + i * (time_button_width + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, time_button_width, button_height)
            self.ui_buttons[action] = button_rect
            
            # Button-Stil mit Hover-Effekt
            if self.hovered_button == action:
                button_color = tuple(min(255, c + 40) for c in color)
                pygame.draw.rect(screen, button_color, button_rect)
                pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)
            else:
                pygame.draw.rect(screen, color, button_rect)
                pygame.draw.rect(screen, (200, 200, 200), button_rect, 1)
            
            # Button-Text (Emoji)
            text = self.button_font.render(symbol, True, (255, 255, 255))
            text_rect = text.get_rect(center=button_rect.center)
            screen.blit(text, text_rect)
        
        # Status-Informationen (eleganter)
        if self.time_speed != 1.0:
            speed_text = self.small_font.render(f"⚡ {self.time_speed:.1f}x Geschwindigkeit", True, (255, 255, 100))
            speed_rect = speed_text.get_rect(centerx=x + ui_width//2, y=button_y - 20)
            # Hintergrund für bessere Lesbarkeit
            bg_rect = speed_rect.inflate(10, 4)
            pygame.draw.rect(screen, (0, 0, 0, 100), bg_rect)
            screen.blit(speed_text, speed_rect)
            
    def save_time(self, filepath="save_game.json"):
        """Speichere die aktuelle Zeit"""
        time_data = {
            "game_hours": self.game_hours,
            "game_minutes": self.game_minutes,
            "game_day": self.game_day,
            "time_speed": self.time_speed
        }
        
        # Lade existierende Speicherdaten falls vorhanden
        save_data = {}
        if Path(filepath).exists():
            try:
                with open(filepath, 'r') as f:
                    save_data = json.load(f)
            except:
                pass
                
        save_data["time"] = time_data
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)
            
    def load_time(self, filepath="save_game.json"):
        """Lade die gespeicherte Zeit"""
        if not Path(filepath).exists():
            return False
            
        try:
            with open(filepath, 'r') as f:
                save_data = json.load(f)
                
            if "time" in save_data:
                time_data = save_data["time"]
                self.game_hours = time_data.get("game_hours", 6)
                self.game_minutes = time_data.get("game_minutes", 0)
                self.game_day = time_data.get("game_day", 1)
                self.time_speed = time_data.get("time_speed", 1.0)
                
                # Reset der Tracking-Zeit
                self.last_update_time = time.time()
                return True
        except Exception as e:
            print(f"Fehler beim Laden der Zeit: {e}")
            
        return False
        
    def handle_mouse_event(self, event):
        """Handle Maus-Events für die Zeit-UI - nur wenn in UI-Bereich"""
        mouse_pos = event.pos
        
        # Prüfe zuerst ob die Maus überhaupt in der UI ist
        if not hasattr(self, 'ui_rect') or self.ui_rect is None or not self.ui_rect.collidepoint(mouse_pos):
            # Wenn Maus nicht in UI ist, reset hover und gib False zurück
            if event.type == pygame.MOUSEMOTION:
                self.hovered_button = None
            return False
        
        if event.type == pygame.MOUSEMOTION:
            # Check welcher Button gehovered wird (nur wenn in UI)
            self.hovered_button = None
            
            if hasattr(self, 'ui_buttons'):
                for button_name, button_rect in self.ui_buttons.items():
                    if button_rect.collidepoint(mouse_pos):
                        self.hovered_button = button_name
                        break
                    
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Linke Maustaste
            # Nur Button-Klicks verarbeiten (UI-Bereich bereits geprüft)
            if hasattr(self, 'ui_buttons'):
                for button_name, button_rect in self.ui_buttons.items():
                    if button_rect.collidepoint(mouse_pos):
                        self._handle_button_click(button_name)
                        return True  # Event wurde verarbeitet
                    
        return False  # Event nicht verarbeitet
        
    def _handle_button_click(self, button_name):
        """Verarbeite Button-Klicks"""
        if button_name == "pause":
            if self.paused:
                self.resume()
            else:
                self.pause()
        elif button_name == "slower":
            new_speed = max(0.1, self.time_speed - 0.5)
            self.set_time_speed(new_speed)
        elif button_name == "faster":
            new_speed = min(10.0, self.time_speed + 0.5)
            self.set_time_speed(new_speed)
        elif button_name == "normal":
            self.set_time_speed(1.0)
        elif button_name == "morning":
            self.set_time(6, 0)
        elif button_name == "noon":
            self.set_time(12, 0)
        elif button_name == "evening":
            self.set_time(18, 0)
        elif button_name == "night":
            self.set_time(23, 0)
