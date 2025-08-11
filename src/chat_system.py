"""
Chat System - Spieler kann dem Anführer Befehle geben
"""

import pygame
import time
from typing import List, Optional, Dict, Any
from enum import Enum

class ChatState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    TYPING = "typing"

class Command:
    """Ein Befehl vom Spieler"""
    def __init__(self, command_text: str, timestamp: float):
        self.command_text = command_text
        self.timestamp = timestamp
        self.parsed = False
        self.response = ""
        self.completed = False

class CommandParser:
    """Parst Spieler-Befehle und konvertiert sie zu Aktionen"""
    
    def __init__(self):
        self.command_patterns = {
            'build_houses': ['baue', 'errichte', 'konstruiere', 'bau'],
            'collect_resources': ['sammle', 'hole', 'bringe', 'sammel'],
            'expand': ['erweitere', 'expandiere', 'vergrößere'],
            'stop': ['stopp', 'halt', 'stop', 'pause'],
            'status': ['status', 'bericht', 'situation', 'info'],
        }
    
    def parse_command(self, command_text: str) -> Dict[str, Any]:
        """Parse einen Befehl und extrahiere Intention und Parameter"""
        command_lower = command_text.lower()
        
        # Zahlen extrahieren
        numbers = []
        words = command_lower.split()
        for word in words:
            try:
                num = int(word)
                numbers.append(num)
            except ValueError:
                continue
        
        # Kommando-Typ bestimmen
        command_type = 'unknown'
        for cmd_type, keywords in self.command_patterns.items():
            for keyword in keywords:
                if keyword in command_lower:
                    command_type = cmd_type
                    break
            if command_type != 'unknown':
                break
        
        # Spezifische Parsing-Logik
        if command_type == 'build_houses':
            count = numbers[0] if numbers else 1
            if 'haus' in command_lower or 'häuser' in command_lower:
                return {
                    'type': 'build_houses',
                    'count': count,
                    'description': f"Baue {count} Häuser"
                }
        
        elif command_type == 'collect_resources':
            amount = numbers[0] if numbers else 10
            resource_type = 'wood'  # Default
            if 'holz' in command_lower:
                resource_type = 'wood'
            elif 'stein' in command_lower:
                resource_type = 'stone'
            
            return {
                'type': 'collect_resources',
                'resource': resource_type,
                'amount': amount,
                'description': f"Sammle {amount} {resource_type}"
            }
        
        elif command_type == 'status':
            return {
                'type': 'status',
                'description': "Gib Statusbericht"
            }
        
        elif command_type == 'stop':
            return {
                'type': 'stop_all',
                'description': "Stoppe alle Aktivitäten"
            }
        
        # Fallback für unbekannte Befehle
        return {
            'type': 'unknown',
            'original': command_text,
            'description': f"Verstehe nicht: '{command_text}'"
        }

class ChatSystem:
    """Chat-Interface für Spieler-Befehle"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state = ChatState.CLOSED
        
        # UI Eigenschaften
        self.chat_width = 400
        self.chat_height = 300
        self.input_height = 40
        self.margin = 10
        
        # Position (unten rechts)
        self.chat_x = screen_width - self.chat_width - self.margin
        self.chat_y = screen_height - self.chat_height - self.margin
        
        # Input Text
        self.input_text = ""
        self.cursor_visible = True
        self.last_cursor_toggle = time.time()
        
        # Chat History
        self.messages: List[Dict[str, str]] = []
        self.commands: List[Command] = []
        
        # Font
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.input_font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 32)
        
        # Parser
        self.parser = CommandParser()
        
        # Colors
        self.bg_color = (40, 40, 40, 200)  # Semi-transparent
        self.input_bg_color = (60, 60, 60, 255)
        self.text_color = (255, 255, 255)
        self.command_color = (100, 200, 255)
        self.response_color = (100, 255, 100)
        self.border_color = (100, 100, 100)
        
        # Willkommensnachricht
        self.add_message("system", "💬 Chat geöffnet! Gib dem Anführer Befehle:")
        self.add_message("system", "• 'baue 5 häuser' - Bauaufträge")
        self.add_message("system", "• 'sammle 50 holz' - Ressourcen")
        self.add_message("system", "• 'status' - Aktueller Stand")
    
    def toggle_chat(self):
        """Öffne/schließe Chat"""
        if self.state == ChatState.CLOSED:
            self.state = ChatState.OPEN
            print("💬 Chat geöffnet")
        else:
            self.state = ChatState.CLOSED
            print("💬 Chat geschlossen")
    
    def add_message(self, sender: str, message: str):
        """Füge Nachricht zum Chat hinzu"""
        self.messages.append({
            'sender': sender,
            'message': message,
            'timestamp': time.time()
        })
        
        # Begrenze History
        if len(self.messages) > 20:
            self.messages = self.messages[-15:]
    
    def handle_input(self, event):
        """Handle Keyboard Input"""
        if self.state == ChatState.CLOSED:
            return None
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Submit command
                if self.input_text.strip():
                    command = self.submit_command(self.input_text.strip())
                    self.input_text = ""
                    return command
                    
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                
            elif event.key == pygame.K_ESCAPE:
                self.toggle_chat()
                
            else:
                # Add character (sichere Unicode-Behandlung)
                if len(self.input_text) < 50 and hasattr(event, 'unicode'):  # Limit length
                    char = event.unicode
                    # Nur druckbare Zeichen erlauben
                    if char and char.isprintable():
                        self.input_text += char
        
        return None
    
    def submit_command(self, command_text: str) -> Command:
        """Submit einen neuen Befehl"""
        # Füge zur Chat-History hinzu
        self.add_message("player", f"🎮 {command_text}")
        
        # Parse den Befehl
        command = Command(command_text, time.time())
        self.commands.append(command)
        
        # Parse für sofortiges Feedback
        parsed = self.parser.parse_command(command_text)
        if parsed['type'] != 'unknown':
            self.add_message("system", f"✅ Verstanden: {parsed['description']}")
        else:
            self.add_message("system", f"❓ {parsed['description']}")
        
        return command
    
    def add_leader_response(self, response: str):
        """Anführer antwortet auf Befehl"""
        self.add_message("leader", f"👑 {response}")
    
    def update(self, dt: float):
        """Update Chat System"""
        if self.state == ChatState.CLOSED:
            return
            
        # Cursor blinken
        if time.time() - self.last_cursor_toggle > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.last_cursor_toggle = time.time()
    
    def draw(self, screen: pygame.Surface):
        """Zeichne Chat Interface"""
        if self.state == ChatState.CLOSED:
            # Zeige nur kleinen Indikator
            indicator_rect = pygame.Rect(self.screen_width - 100, self.screen_height - 30, 90, 25)
            pygame.draw.rect(screen, (60, 60, 60, 180), indicator_rect)
            pygame.draw.rect(screen, self.border_color, indicator_rect, 2)
            
            indicator_text = self.font.render("💬 Chat (C)", True, self.text_color)
            screen.blit(indicator_text, (indicator_rect.x + 5, indicator_rect.y + 3))
            return
        
        # Haupt-Chat-Fenster
        chat_rect = pygame.Rect(self.chat_x, self.chat_y, self.chat_width, self.chat_height)
        
        # Semi-transparenter Hintergrund
        chat_surface = pygame.Surface((self.chat_width, self.chat_height), pygame.SRCALPHA)
        chat_surface.fill(self.bg_color)
        screen.blit(chat_surface, (self.chat_x, self.chat_y))
        
        # Border
        pygame.draw.rect(screen, self.border_color, chat_rect, 2)
        
        # Title
        title_text = self.title_font.render("💬 Anführer-Chat", True, self.command_color)
        screen.blit(title_text, (self.chat_x + 10, self.chat_y + 5))
        
        # Messages
        message_area_y = self.chat_y + 35
        message_area_height = self.chat_height - 35 - self.input_height - 10
        
        # Zeichne Nachrichten (neueste unten)
        y_offset = message_area_y + message_area_height - 25
        for i in range(len(self.messages) - 1, -1, -1):  # Von unten nach oben
            if y_offset < message_area_y:
                break
                
            message = self.messages[i]
            sender = message['sender']
            text = message['message']
            
            # Farbe je nach Sender
            if sender == "player":
                color = self.command_color
            elif sender == "leader":
                color = self.response_color
            else:
                color = self.text_color
            
            # Text rendern (mit Wordwrap)
            words = text.split(' ')
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if self.font.size(test_line)[0] < self.chat_width - 20:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Zeichne Zeilen
            for line in reversed(lines):
                if y_offset < message_area_y:
                    break
                text_surface = self.font.render(line, True, color)
                screen.blit(text_surface, (self.chat_x + 10, y_offset))
                y_offset -= 25
        
        # Input Box
        input_rect = pygame.Rect(self.chat_x + 5, 
                                self.chat_y + self.chat_height - self.input_height - 5,
                                self.chat_width - 10, 
                                self.input_height)
        
        pygame.draw.rect(screen, self.input_bg_color, input_rect)
        pygame.draw.rect(screen, self.border_color, input_rect, 2)
        
        # Input Text
        display_text = self.input_text
        if self.cursor_visible:
            display_text += "|"
        
        input_surface = self.input_font.render(display_text, True, self.text_color)
        screen.blit(input_surface, (input_rect.x + 5, input_rect.y + 8))
        
        # Hilfstext
        if not self.input_text:
            help_text = self.font.render("Befehl eingeben... (ESC = schließen)", True, (150, 150, 150))
            screen.blit(help_text, (input_rect.x + 5, input_rect.y + 8))