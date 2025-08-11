# 🎮 Top Down 2D Farming & Adventure Spiel

Ein vollständiges 2D Top-Down Spiel mit Farming-System, Tieren, Tag/Nacht-Zyklus und umfangreichem World Editor, entwickelt mit Python und pygame.

## 🌟 Features

### 🏞️ Welten-System
- **Prozedurale Welt-Generierung**: Automatisch generierte Landschaft mit Gras, Bäumen, Seen und Wegen
- **Tiled Map Support**: Lädt auch externe TMX-Karten aus Tiled Map Editor
- **Kollisionssystem**: Intelligente Kollisionserkennung (z.B. kein Laufen auf Wasser)
- **Dynamische Objekt-Platzierung**: Platziere Assets mit dem World Editor

### 🚜 Farming System
- **Pflanzensystem**: Pflanze Weizen, Karotten und andere Crops auf Farmland-Tiles
- **Wachstumsphasen**: Pflanzen wachsen durch verschiedene Stufen (Samen → Wachstum → Reif)
- **Bewässerung**: Pflanzen müssen regelmäßig gegossen werden
- **Ernten**: Sammle deine Ernte ein und verwalte dein Inventar

### 🐄 Tiersystem
- **Animierte Tiere**: Kühe, Schweine, Hühner und Schafe mit vollständiger Sprite-Animation
- **Tier-AI**: Tiere wandern selbstständig umher mit realistischen Bewegungsmustern
- **Fütterung & Pflege**: Kümmere dich um deine Tiere für bessere Produktion
- **Produktion**: Sammle Milch, Eier, Wolle und Trüffel von deinen Tieren

### ⏰ Zeit & Wetter-System
- **Tag/Nacht-Zyklus**: Vollständiger 24-Stunden Zyklus mit realistische Beleuchtung
- **Sonnen-Animation**: Sonne wandert realistisch über den Himmel
- **Zeit-Steuerung**: Pausiere, beschleunige oder springe zu bestimmten Tageszeiten
- **Interaktive Zeit-UI**: Elegante, klickbare Zeitanzeige mit Sonnen-Indikator

### 🛠️ World Editor & Debug-System
- **Asset Browser**: Durchsuche alle 120+ Game Assets mit intelligenter Sprite-Sheet Erkennung
- **Intelligente Asset-Erkennung**: Automatisches Aufteilen von Sprite-Sheets und Tile-Sets
- **Platzierungsmodi**: Einzeln, Raster (5x5) oder zufällig platzieren
- **Frame-Navigation**: Navigiere durch Sprite-Animationen mit Tasten 1-9/0
- **Speicher/Laden**: Speichere deine Welten mit allen platzierten Objekten

### 🎨 Umfangreiche Asset-Bibliothek
- **120+ Sprites**: Tiere, Pflanzen, Gebäude, Werkzeuge, Möbel und mehr
- **Pixel Art Style**: Konsistenter Retro-Pixel-Art-Stil
- **Animationen**: Vollständige Lauf-, Idle- und Aktions-Animationen
- **Strukturen**: Häuser, Zäune, Brücken und Dekorationen

## 📋 Voraussetzungen (macOS)
- **Python 3.11** (empfohlen - pygame Wheels verfügbar)
- Python 3.13 kann zu Kompilierungsproblemen führen

```bash
# Python Version prüfen
python3 --version
# oder gezielt
python3.11 --version
```

## 🚀 Installation

### Einfache Installation (Python 3.11)
```bash
# 1. Python 3.11 installieren (falls nötig)
brew install python@3.11

# 2. Virtuelle Umgebung erstellen
python3.11 -m venv .venv
source .venv/bin/activate

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. Spiel starten
python src/main.py
```

### 📦 Dependencies
```
pygame==2.5.2
pytmx==3.32
```

### 🔧 Troubleshooting (Python 3.13)
Falls pygame Build-Fehler auftreten:

**Option A** (empfohlen): Wechsel zu Python 3.11 (siehe oben)

**Option B** (kompilieren):
```bash
brew install pkg-config freetype sdl2 sdl2_image sdl2_mixer sdl2_ttf
pip install --no-cache-dir pygame==2.5.2
```

**Option C** (Community Fork):
```bash
pip uninstall pygame -y
pip install pygame-ce
```

## 🎮 Steuerung

### 🚶 Bewegung
- **Mausklick**: Bewege Spieler zur angeklickten Position
- **Rechtsklick**: Stoppe Bewegung

### 🌾 Farming
- **1**: Weizen pflanzen (auf Farmland)
- **2**: Karotte pflanzen (auf Farmland)
- **W**: Pflanze gießen
- **H**: Pflanze ernten

### 🐮 Tiere
- **F**: Tier füttern (in der Nähe eines Tieres)
- **C**: Von Tier sammeln (Milch, Eier, etc.)

### ⏰ Zeit-Steuerung
- **P**: Zeit pausieren/fortsetzen
- **SPACE**: Zeitraffer (5x ein/aus)
- **+ / -**: Zeit beschleunigen/verlangsamen
- **T**: Normale Geschwindigkeit
- **Shift+T**: 1 Stunde vorspulen
- **Ctrl+T**: 6 Stunden vorspulen
- **M**: Springe zu Morgen (6:00)
- **N**: Springe zu Mittag (12:00)
- **E**: Springe zu Abend (18:00)

### 🛠️ World Editor
- **TAB / F1**: Debug Panel ein/ausblenden
- **Shift+Klick**: Asset aus Panel platzieren
- **Ctrl+Shift+Klick**: 5x5 Raster platzieren
- **Alt+Shift+Klick**: 5 zufällige Platzierungen
- **1-9, 0**: Sprite-Frame auswählen (Frame 1-10)
- **←→**: Durch Sprite-Frames navigieren
- **↑↓**: Im Asset-Panel scrollen
- **Page Up/Down**: Schnell scrollen
- **S**: Welt speichern
- **C**: Alle platzierten Objekte löschen
- **R**: Assets neu laden

## 🏗️ Projekt-Struktur

```
Game/
├── src/
│   ├── main.py              # Haupt-Game-Loop und UI
│   ├── player.py            # Spieler-Klasse mit Animation
│   ├── simple_world.py      # Prozedurale Welt-Generierung
│   ├── farming_system.py    # Farming und Tier-System
│   ├── time_system.py       # Tag/Nacht-Zyklus
│   ├── map_loader.py        # Tiled Map Loader
│   └── settings.py          # Konfiguration
├── assets/
│   ├── Animals/            # Tier-Sprites (Kuh, Schwein, Huhn, Schaf)
│   ├── Enemies/            # Gegner (Skeleton, Slime)
│   ├── Outdoor decoration/ # Bäume, Häuser, Zäune
│   ├── Player/             # Spieler-Sprites
│   ├── Tiles/              # Grund-Tiles (Gras, Wasser, Pfad)
│   ├── Pixel Crawler/      # Umfangreiche Pixel-Art Sammlung
│   └── 001/                # Tiled Map Editor Dateien
├── requirements.txt
├── StartGame.command       # macOS Start-Script
├── run.sh                  # Unix Start-Script
└── asset_splitter.py       # Asset-Management Tool
```

## 🎯 Aktuelle Features im Detail

### 🌍 World System
- **160x120 Tiles große Welt** (5120x3840 Pixel)
- **Prozedurale Generierung** mit konfigurierbarem Seed
- **Verschiedene Biome**: Gras, Seen, Farmland-Patches, Wege
- **Strukturen**: Automatisch platzierte Häuser

### 🌱 Farming Mechaniken
- **Realistische Wachstumszeiten**: Karotten brauchen 3 Spielstunden (1 pro Stufe)
- **Bewässerungssystem**: Pflanzen müssen nach jeder Wachstumsstufe gegossen werden
- **Visuelles Feedback**: Farbcodierte Pflanzen (Braun=Samen, Gelb=Wächst, Blau=Gegossen, Grün=Reif)

### 🐾 Tier-AI System
- **Autonome Bewegung**: Tiere wandern selbstständig umher
- **Bedürfnisse**: Hunger und Glück beeinflussen Produktion
- **Produktions-Timer**: Jedes Tier hat eigene Produktionszyklen
- **Realistische Sprite-Animation**: 4-Richtungs-Animation mit Frame-Cycling

### 🕐 Zeit-System
- **Realistische Sonnen-Bewegung**: Sonne wandert von Ost nach West
- **Dynamische Beleuchtung**: Schatten-Overlay basierend auf Tageszeit
- **Flexible Zeit-Geschwindigkeit**: 0.1x bis 10x Speed
- **Persistenz**: Zeit wird mit Welt gespeichert und geladen

### 🎨 Asset-Management
- **Intelligente Sprite-Sheet Erkennung**: Automatisches Erkennen von Animation-Sheets
- **Grid-Erkennung**: Automatisches Aufteilen von Tile-Sets und Asset-Sammlungen
- **Frame-Navigation**: Echtzeit-Durchblättern von Sprite-Frames
- **Performance**: Nur 120 Assets gleichzeitig geladen für flüssige Performance

## 📈 Geplante Erweiterungen

- **Combat System**: Kampf gegen Skelette und Slimes
- **NPC System**: Interaktive Charaktere (Knight, Rogue, Wizard)
- **Quest System**: Missions und Objectives
- **Inventory UI**: Grafisches Inventar-Management
- **Sound System**: Musik und Sound-Effekte
- **Save System**: Mehrere Spielstände
- **Multiplayer**: Lokaler Koop-Modus

## 🔧 Konfiguration

Die wichtigsten Einstellungen in `src/settings.py`:

```python
# Bildschirm
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FULLSCREEN = False

# Welt-Generierung
SIMPLE_WORLD_WIDTH_TILES = 160
SIMPLE_WORLD_HEIGHT_TILES = 120
SIMPLE_WORLD_TREE_DENSITY = 0.02
SIMPLE_WORLD_SEED = 42  # Reproduzierbare Welt

# Debug Panel
DEBUG_PANEL_WIDTH = 260
DEBUG_ENABLE_AUTO_SCAN = True
```

## 🎮 Erste Schritte

1. **Starte das Spiel** mit `python src/main.py`
2. **Erkunde die Welt** per Mausklick
3. **Öffne das Debug Panel** mit TAB
4. **Platziere Objekte** mit Shift+Klick aus dem Panel
5. **Probiere das Farming** auf den braunen Farmland-Bereichen
6. **Interagiere mit Tieren** die automatisch in der Welt platziert werden
7. **Experimentiere mit der Zeit** (Drücke H für vollständige Zeit-Hilfe)
8. **Speichere deine Welt** mit S

## 🏆 Besondere Features

- **Shader-basierte Beleuchtung**: Realistische Tag/Nacht-Übergänge
- **Intelligente Kollision**: Spieler stoppt vor Wasser, kann aber bis zum Rand laufen
- **Performance-Optimierung**: Effiziente Rendering nur sichtbarer Bereiche
- **Modulare Architektur**: Saubere Trennung von Systemen
- **Extensible Asset System**: Einfaches Hinzufügen neuer Sprites

---

**Entwickelt mit ❤️ in Python & pygame**

Viel Spaß beim Spielen und Experimentieren! 🎮
