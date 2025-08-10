# 🧠 Advanced AI Village Simulator

## Überblick

Dieses Projekt erweitert Ihre Dorf-Simulation mit einer fortschrittlichen KI, die **lokal auf Ihrem Computer läuft** und mit der Zeit **intelligenter wird**. Die KI nutzt verschiedene moderne Techniken des maschinellen Lernens.

## 🚀 Neue KI-Features

### 1. **Neuronale Netzwerke (TensorFlow.js)**
- **Lokales Training**: Läuft komplett in Ihrem Browser
- **Reinforcement Learning**: Charaktere lernen aus Belohnungen/Bestrafungen
- **Adaptive Entscheidungsfindung**: Verbessert sich mit jeder Entscheidung
- **Keine Internetverbindung nötig**: Alles läuft offline

### 2. **Intelligentes Gedächtnis-System**
- **Kurzzeitgedächtnis**: Für aktuelle Erfahrungen
- **Langzeitgedächtnis**: Für wichtige Lernerfahrungen
- **Episodisches Gedächtnis**: Für spezielle Ereignisse
- **Adaptive Konsolidierung**: Wichtige Erinnerungen werden dauerhaft gespeichert

### 3. **Emotionale Intelligenz**
- **Emotionaler Zustand**: Glück, Stress, Neugier
- **Emotionsbasierte Entscheidungen**: Gefühle beeinflussen das Verhalten
- **Adaptive Persönlichkeit**: Charaktere entwickeln sich basierend auf Erfahrungen

### 4. **Kollektive Intelligenz** 🌐
- **Wissensaustausch**: Charaktere teilen erfolgreiche Strategien
- **Soziales Lernen**: Nachahmung erfolgreicher Verhaltensweisen
- **Kulturelle Evolution**: Entstehung von Trends und Traditionen
- **Emergente Verhaltensweisen**: Unerwartete Gruppendynamiken

### 5. **Verschiedene Lernmodi**
- **Basic AI**: Einfache regelbasierte Logik
- **Learning AI**: Regelbasiert + Gedächtnislernen
- **Neural AI**: Nur neuronale Netzwerke
- **Hybrid AI**: Kombination aller Ansätze (Empfohlen)

## 🎮 Bedienung

### Tastenkombinationen
- **Ctrl + I**: AI Dashboard öffnen/schließen
- **F**: Debug-Panel (ursprüngliches Feature)

### AI Dashboard (🧠 AI Stats Button)
- **Lernfortschritt** jedes Charakters
- **Erfolgsraten** und Statistiken
- **Emotionale Zustände**
- **Gedächtnis-Status**
- **Neural Network Status**

### AI Configuration (⚙️ AI Config Button)
- **AI-Modi** wechseln
- **Lernparameter** anpassen
- **Experimentelle Features** aktivieren
- **Presets** laden (Conservative, Aggressive, Balanced)
- **Individuelle Charaktere** konfigurieren

## 🧠 Wie die KI schlauer wird

### 1. **Reinforcement Learning**
```
Aktion → Ergebnis → Belohnung/Bestrafung → Anpassung
```
- Positive Ergebnisse verstärken das Verhalten
- Negative Ergebnisse reduzieren die Wahrscheinlichkeit
- Adaptive Exploration vs. Exploitation

### 2. **Erfahrungslernen**
- Erfolgreiche Strategien werden im Langzeitgedächtnis gespeichert
- Gescheiterte Ansätze werden vermieden
- Kontinuierliche Anpassung der Lernparameter

### 3. **Soziales Lernen**
- Beobachtung erfolgreicher Charaktere
- Nachahmung bewährter Strategien
- Wissensaustausch zwischen Freunden

### 4. **Emotionale Entwicklung**
- Erfolg steigert Selbstvertrauen (weniger Exploration)
- Misserfolg erhöht Experimentierfreude (mehr Exploration)
- Stress und Glück beeinflussen Entscheidungen

## 📊 Monitoring & Debugging

### Erfolgsmetriken
- **Success Rate**: Prozentsatz erfolgreicher Aktionen
- **Decision Count**: Anzahl getroffener Entscheidungen
- **Knowledge Points**: Angesammelte Lernerfahrung
- **Exploration Rate**: Experimentierfreudigkeit

### Gedächtnis-Tracking
- **Short Term**: Aktuelle Erfahrungen (max 20)
- **Long Term**: Wichtige Erinnerungen (max 100)
- **Episodic**: Besondere Ereignisse

### Kollektive Intelligenz
- **Social Connections**: Freundschaften zwischen Charakteren
- **Shared Knowledge**: Geteiltes Wissen
- **Cultural Trends**: Entstehende Traditionen
- **Emergent Behaviors**: Unerwartete Gruppenverhaltensweisen

## ⚙️ Technische Details

### Lokale Verarbeitung
- **TensorFlow.js**: Für neuronale Netzwerke
- **Browser-basiert**: Keine Server erforderlich
- **Echte KI**: Nicht nur Skripte, sondern lernende Algorithmen

### Ressourcennutzung
- **CPU-intensiv**: Nutzt Ihre lokale Rechenleistung
- **Speicher-effizient**: Intelligente Gedächtniskonsolidierung
- **Progressive Enhancement**: Funktioniert auch ohne TensorFlow.js

### Skalierbarkeit
- **Charaktere**: Unterstützt beliebig viele KI-Charaktere
- **Komplexität**: KI wird mit der Zeit komplexer
- **Performance**: Optimiert für Browser-Performance

## 🎯 Experimentelle Features

### Social Learning
Charaktere lernen durch Beobachtung anderer Charaktere.

### Collective Intelligence
Geteiltes Wissen und kulturelle Evolution zwischen allen Charakteren.

### Adaptive Personality
Persönlichkeitsmerkmale entwickeln sich basierend auf Erfahrungen.

## 🔧 Anpassung & Erweiterung

### Lernparameter
- **Learning Rate** (0.001 - 0.1): Geschwindigkeit des Lernens
- **Exploration Rate** (0.05 - 0.8): Experimentierfreudigkeit
- **Memory Capacity** (50 - 500): Gedächtniskapazität
- **Emotional Influence** (0 - 1): Einfluss der Emotionen

### Neue Aktionen hinzufügen
1. Erweitern Sie die `actions` Array in `ai-brain.js`
2. Implementieren Sie die Logik in `startAction()` und `completeAction()`
3. Definieren Sie Belohnungsstrukturen in `calculateReward()`

### Custom Rewards
Passen Sie die Belohnungslogik in `calculateReward()` an Ihre Spielmechaniken an.

## 📈 Performance-Optimierung

### Für bessere Performance
- Reduzieren Sie die `Learning Rate`
- Begrenzen Sie die `Memory Capacity`
- Deaktivieren Sie `Collective Intelligence` bei vielen Charakteren

### Für mehr Intelligenz
- Erhöhen Sie die `Memory Capacity`
- Aktivieren Sie alle experimentellen Features
- Verwenden Sie den `Hybrid AI` Modus

## 🔮 Zukunftspläne

- **Genetically evolving AI**: Evolutionäre Algorithmen
- **Meta-Learning**: AI lernt wie sie lernt
- **Dream-like consolidation**: Schlafphasen für Gedächtniskonsolidierung
- **Multi-layered personality**: Komplexere Persönlichkeitsmodelle

---

**Viel Spaß beim Experimentieren mit Ihrer intelligenten Dorf-KI!** 🏘️🧠

Die KI wird mit jeder Minute schlauer - beobachten Sie, wie sich Ihre Charaktere entwickeln und voneinander lernen!
