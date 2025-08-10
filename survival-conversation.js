/**
 * Advanced Survival & Communication System
 * Charaktere haben echte Bedürfnisse und führen natürliche Gespräche
 */

class SurvivalSystem {
    constructor() {
        this.basicNeeds = {
            hunger: { threshold: 70, decay: 0.2, priority: 100 },
            thirst: { threshold: 80, decay: 0.3, priority: 120 },
            energy: { threshold: 20, decay: 0.1, priority: 80 },
            warmth: { threshold: 40, decay: 0.05, priority: 60 },
            social: { threshold: 60, decay: 0.15, priority: 40 }
        };
        
        this.resources = ['food', 'water', 'wood', 'shelter_materials'];
        this.workTime = 3000; // 3 Sekunden Arbeitszeit
    }

    updateSurvivalNeeds(character) {
    // Falls gameInstance noch nicht fertig initialisiert ist, kurz überspringen
    if (!window.gameInstance || window.gameInstance.gameTime == null) return;
    // Hunger steigt kontinuierlich
        character.hunger = Math.min(100, character.hunger + this.basicNeeds.hunger.decay);
        
        // Durst steigt schneller als Hunger
        character.thirst = Math.min(100, character.thirst + this.basicNeeds.thirst.decay);
        
        // Energie sinkt durch Aktivität
        if (character.currentAction !== 'schlafen' && character.currentAction !== 'idle') {
            character.energy = Math.max(0, character.energy - this.basicNeeds.energy.decay);
        }
        
        // Wärme sinkt in der Nacht
    const timeOfDay = window.gameInstance.gameTime / (24 * 60);
        if (timeOfDay < 0.25 || timeOfDay > 0.75) { // Nacht
            character.warmth = Math.max(0, character.warmth - this.basicNeeds.warmth.decay);
        } else {
            character.warmth = Math.min(100, character.warmth + 0.02); // Tag
        }
        
        // Soziale Bedürfnisse
        if (!this.hasNearbyCompanions(character)) {
            character.social = Math.max(0, character.social - this.basicNeeds.social.decay);
        }
        
        // Initialisiere Bedürfnisse falls nicht vorhanden
        if (character.thirst === undefined) character.thirst = 30 + Math.random() * 20;
        if (character.warmth === undefined) character.warmth = 70 + Math.random() * 20;
        if (character.social === undefined) character.social = 50 + Math.random() * 30;
        if (character.inventory === undefined) character.inventory = { food: 0, water: 0, wood: 0 };
    }

    hasNearbyCompanions(character) {
        if (!window.gameInstance) return false;
        
        const companions = window.gameInstance.characters.filter(other => {
            if (other === character) return false;
            const distance = Math.sqrt(
                Math.pow(character.x - other.x, 2) + 
                Math.pow(character.y - other.y, 2)
            );
            return distance < 80;
        });
        
        return companions.length > 0;
    }

    getMostUrgentNeed(character) {
        const needs = {
            thirst: character.thirst,
            hunger: character.hunger,
            energy: 100 - character.energy,
            warmth: 100 - character.warmth,
            social: 100 - character.social
        };
        
        let mostUrgent = null;
        let highestUrgency = 0;
        
        for (const [need, level] of Object.entries(needs)) {
            const threshold = this.basicNeeds[need]?.threshold || 50;
            const priority = this.basicNeeds[need]?.priority || 50;
            
            if (level > threshold) {
                const urgency = (level - threshold) * priority / 100;
                if (urgency > highestUrgency) {
                    highestUrgency = urgency;
                    mostUrgent = need;
                }
            }
        }
        
        return mostUrgent;
    }

    getSurvivalAction(character, urgentNeed) {
        switch (urgentNeed) {
            case 'thirst':
                return this.findNearestWaterSource(character) ? 'drink_water' : 'find_water';
            case 'hunger':
                return character.inventory.food > 0 ? 'eat_food' : 'gather_food';
            case 'energy':
                return 'rest';
            case 'warmth':
                return character.inventory.wood > 3 ? 'make_fire' : 'gather_wood';
            case 'social':
                return 'seek_conversation';
            default:
                return null;
        }
    }

    findNearestWaterSource(character) {
        if (!window.gameInstance) return null;

        let candidates = [];

        // 1) Explizite Wasserquellen (water_source) bevorzugen
        const waterSpots = window.gameInstance.terrain.filter(t => t.type === 'water_source');
        candidates.push(...waterSpots.map(w => ({ x:w.x, y:w.y, ref:w, kind:'water_source' })));

        // 2) Fallback: einzelne Punkte des Flusses (wie zuvor)
        const rivers = window.gameInstance.terrain.filter(t => t.type === 'river');
        rivers.forEach(river => {
            if (river.points) {
                // Sample nur jeden 4. Punkt um Performance zu sparen
                river.points.forEach((point, idx) => {
                    if (idx % 4 === 0) candidates.push({ x:point.x, y:point.y, ref:river, kind:'river_point' });
                });
            }
        });

        if (!candidates.length) return null;
        candidates.sort((a,b)=> (Math.hypot(character.x-a.x, character.y-a.y) - Math.hypot(character.x-b.x, character.y-b.y)) );
        return candidates[0];
    }

    findNearestResource(character, resourceType) {
        if (!window.gameInstance) return null;
        
        const terrainTypes = {
            food: ['tree', 'bush'],
            wood: ['tree'],
            shelter_materials: ['mountain', 'tree']
        };
        
        const validTerrain = window.gameInstance.terrain.filter(t => 
            terrainTypes[resourceType]?.includes(t.type)
        );
        
        if (validTerrain.length === 0) return null;
        
        let nearest = null;
        let nearestDistance = Infinity;
        
        validTerrain.forEach(terrain => {
            const distance = Math.sqrt(
                Math.pow(character.x - terrain.x, 2) + 
                Math.pow(character.y - terrain.y, 2)
            );
            if (distance < nearestDistance) {
                nearestDistance = distance;
                nearest = terrain;
            }
        });
        
        return nearest;
    }
}

// NOTE: Renamed to SurvivalConversationSystem to avoid duplicate declaration with natural-conversation.js
class SurvivalConversationSystem {
    constructor() {
        this.conversationTopics = {
            survival: [
                "Ich bin so durstig... kennst du eine Wasserquelle?",
                "Der Hunger macht mich schwach. Wo finde ich Essen?",
                "Es wird kalt. Sollten wir Holz sammeln?",
                "Ich bin müde von der ganzen Arbeit.",
                "Hast du genug Vorräte für den Winter?"
            ],
            planning: [
                "Wie kommen wir hier raus?",
                "Was ist unser Plan für morgen?",
                "Sollen wir zusammen nach Norden gehen?",
                "Ich denke, wir sollten ein Lager aufbauen.",
                "Vielleicht gibt es einen Weg über die Berge?"
            ],
            social: [
                "Wie geht es dir heute?",
                "Bist du auch manchmal einsam hier?",
                "Erinnerst du dich an unser Zuhause?",
                "Ich bin froh, dass du bei mir bist.",
                "Zusammen schaffen wir das schon!"
            ],
            observation: [
                "Hast du die Vögel gehört? Sie fliegen nach Süden.",
                "Das Wetter ändert sich... es wird stürmisch.",
                "Dort drüben sehe ich Rauch. Sind das andere Menschen?",
                "Die Früchte an diesem Baum sehen reif aus.",
                "Der Fluss ist heute sehr reißend."
            ],
            philosophical: [
                "Warum sind wir hier? Was ist unser Zweck?",
                "Manchmal frage ich mich, ob es mehr gibt als nur überleben.",
                "Glaubst du, wir finden jemals einen Ausweg?",
                "Was würdest du tun, wenn du frei wärst?",
                "Das Leben hier lehrt uns, was wirklich wichtig ist."
            ]
        };
        
        this.responses = {
            agreement: [
                "Da hast du recht!", "Genau das denke ich auch!", "Sehr gute Idee!",
                "Ja, das sollten wir machen!", "Du sprichst mir aus der Seele!"
            ],
            concern: [
                "Das macht mir Sorgen...", "Ich bin nicht sicher...", "Das könnte gefährlich sein.",
                "Wir sollten vorsichtig sein.", "Ich habe ein ungutes Gefühl dabei."
            ],
            suggestion: [
                "Was hältst du davon, wenn wir...", "Ich schlage vor, wir...", "Vielleicht könnten wir...",
                "Wie wäre es, wenn...", "Ich habe eine Idee:"
            ],
            empathy: [
                "Das verstehe ich gut.", "Mir geht es genauso.", "Du bist nicht allein damit.",
                "Wir helfen uns gegenseitig.", "Ich fühle mit dir."
            ]
        };
        
        this.activeConversations = new Map();
        this.conversationHistory = new Map();
    }

    generateNaturalResponse(speaker, listener, topic, context) {
        // Analysiere den Kontext und die Persönlichkeiten
        const speakerTraits = speaker.traits;
        const listenerTraits = listener.traits;
        const urgentNeed = window.survivalSystem?.getMostUrgentNeed(listener);
        
        let responseType = 'agreement';
        let message = '';
        
        // Bestimme Antworttyp basierend auf Persönlichkeit und Kontext
        if (urgentNeed === 'thirst' || urgentNeed === 'hunger') {
            responseType = 'concern';
            if (urgentNeed === 'thirst') {
                message = "Ich auch! Lass uns schnell zum Fluss gehen.";
            } else {
                message = "Mein Magen knurrt auch. Sollen wir zusammen sammeln?";
            }
        } else if (listenerTraits.sozial > 0.7) {
            responseType = 'empathy';
            message = this.getRandomFromArray(this.responses.empathy);
        } else if (listenerTraits.neugier > 0.7) {
            responseType = 'suggestion';
            message = this.generateCuriousResponse(topic);
        } else if (listenerTraits.mut < 0.4) {
            responseType = 'concern';
            message = this.getRandomFromArray(this.responses.concern);
        } else {
            responseType = 'agreement';
            message = this.getRandomFromArray(this.responses.agreement);
        }
        
        return {
            speaker: listener.name,
            message: message,
            type: responseType,
            timestamp: Date.now()
        };
    }

    generateCuriousResponse(topic) {
        const suggestions = {
            survival: "Lass uns eine Karte der Ressourcen zeichnen!",
            planning: "Ich habe eine Idee! Was, wenn wir...",
            social: "Erzähl mir mehr darüber!",
            observation: "Das sollten wir genauer untersuchen!",
            philosophical: "Das ist eine interessante Frage... ich denke..."
        };
        
        return suggestions[topic] || "Das ist faszinierend! Was denkst du darüber?";
    }

    startConversation(initiator, target) {
        if (!initiator || !target || initiator === target) return null;
        
        // Prüfe Distanz
        const distance = Math.sqrt(
            Math.pow(initiator.x - target.x, 2) + 
            Math.pow(initiator.y - target.y, 2)
        );
        
        if (distance > 60) return null;
        
        // Bestimme Gesprächsthema basierend auf Kontext
        const topic = this.selectConversationTopic(initiator, target);
        const initialMessage = this.generateInitialMessage(initiator, topic);
        
        const conversationId = `${initiator.name}_${target.name}_${Date.now()}`;
        
        const conversation = {
            id: conversationId,
            participants: [initiator, target],
            topic: topic,
            messages: [
                {
                    speaker: initiator.name,
                    message: initialMessage,
                    timestamp: Date.now()
                }
            ],
            startTime: Date.now(),
            active: true
        };
        
        this.activeConversations.set(conversationId, conversation);
        
        // Zeige Gespräch visuell
        this.displayConversation(conversation);
        
        // Generiere Antwort nach kurzer Pause
        setTimeout(() => {
            this.generateResponse(conversationId, target, initiator, topic);
        }, 2000 + Math.random() * 3000);
        
        return conversation;
    }

    selectConversationTopic(initiator, target) {
        const urgentNeed = window.survivalSystem?.getMostUrgentNeed(initiator);
        
        if (urgentNeed) {
            return 'survival';
        }
        
        const timeOfDay = window.gameInstance.gameTime / (24 * 60);
        const topics = Object.keys(this.conversationTopics);
        
        // Gewichtung basierend auf Persönlichkeit
        const weights = {
            survival: initiator.traits.fleiss || 0.5,
            planning: (initiator.traits.neugier + initiator.traits.mut) / 2,
            social: initiator.traits.sozial || 0.5,
            observation: initiator.traits.neugier || 0.5,
            philosophical: (1 - initiator.traits.fleiss) * initiator.traits.neugier
        };
        
        // Tageszeit beeinflusst Themen
        if (timeOfDay < 0.3 || timeOfDay > 0.8) { // Früh morgens oder spät abends
            weights.philosophical *= 1.5;
            weights.social *= 1.3;
        }
        
        // Wähle gewichtetes zufälliges Thema
        let totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);
        let random = Math.random() * totalWeight;
        
        for (const [topic, weight] of Object.entries(weights)) {
            random -= weight;
            if (random <= 0) {
                return topic;
            }
        }
        
        return 'social'; // Fallback
    }

    generateInitialMessage(character, topic) {
        const urgentNeed = window.survivalSystem?.getMostUrgentNeed(character);
        
        // Angepasste Nachrichten basierend auf aktuellen Bedürfnissen
        if (urgentNeed === 'thirst') {
            return "Meine Kehle ist so trocken... weißt du, wo der Fluss ist?";
        } else if (urgentNeed === 'hunger') {
            return "Ich habe solchen Hunger. Hast du etwas zu essen gefunden?";
        } else if (urgentNeed === 'energy') {
            return "Ich bin so müde... können wir eine Pause machen?";
        }
        
        const messages = this.conversationTopics[topic] || this.conversationTopics.social;
        return this.getRandomFromArray(messages);
    }

    generateResponse(conversationId, responder, initiator, topic) {
        const conversation = this.activeConversations.get(conversationId);
        if (!conversation || !conversation.active) return;
        
        const response = this.generateNaturalResponse(initiator, responder, topic, conversation);
        
        conversation.messages.push(response);
        this.displayConversation(conversation);
        
        // Möglicherweise weitere Antworten generieren
        if (conversation.messages.length < 4 && Math.random() < 0.7) {
            setTimeout(() => {
                if (Math.random() < 0.6) {
                    this.generateResponse(conversationId, initiator, responder, topic);
                } else {
                    this.endConversation(conversationId);
                }
            }, 3000 + Math.random() * 4000);
        } else {
            setTimeout(() => this.endConversation(conversationId), 2000);
        }
    }

    displayConversation(conversation) {
        const lastMessage = conversation.messages[conversation.messages.length - 1];
        
        // Finde den sprechenden Charakter
        const speaker = window.gameInstance.characters.find(c => c.name === lastMessage.speaker);
        if (!speaker) return;
        
        // Zeige Sprechblase
        this.showSpeechBubble(speaker, lastMessage.message);
        
        // Konsolen-Output für Debugging
        console.log(`💬 ${lastMessage.speaker}: "${lastMessage.message}"`);
        
        // Update Gedanken des Charakters
        speaker.thoughts = [lastMessage.message];
        
        // Verbessere soziale Bedürfnisse durch Gespräch
        conversation.participants.forEach(participant => {
            if (participant.social !== undefined) {
                participant.social = Math.min(100, participant.social + 5);
            }
        });
    }

    showSpeechBubble(character, message) {
        // Entferne alte Sprechblasen
        const oldBubbles = document.querySelectorAll('.speech-bubble');
        oldBubbles.forEach(bubble => bubble.remove());
        
        // Erstelle neue Sprechblase
        const bubble = document.createElement('div');
        bubble.className = 'speech-bubble';
        bubble.style.cssText = `
            position: absolute;
            background: rgba(255, 255, 255, 0.95);
            border: 2px solid #333;
            border-radius: 15px;
            padding: 8px 12px;
            font-size: 12px;
            max-width: 200px;
            color: #333;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            pointer-events: none;
        `;
        
        bubble.textContent = message;
        
        // Positioniere Sprechblase über dem Charakter
        const canvas = document.getElementById('gameCanvas');
        const rect = canvas.getBoundingClientRect();
        
        bubble.style.left = (rect.left + character.x - 100) + 'px';
        bubble.style.top = (rect.top + character.y - 60) + 'px';
        
        document.body.appendChild(bubble);
        
        // Entferne Sprechblase nach 4 Sekunden
        setTimeout(() => {
            if (bubble.parentNode) {
                bubble.remove();
            }
        }, 4000);
    }

    endConversation(conversationId) {
        const conversation = this.activeConversations.get(conversationId);
        if (!conversation) return;
        
        conversation.active = false;
        conversation.endTime = Date.now();
        
        // Speichere in Verlauf
        if (!this.conversationHistory.has(conversationId)) {
            this.conversationHistory.set(conversationId, conversation);
        }
        
        this.activeConversations.delete(conversationId);
        
        console.log(`💬 Conversation ended between ${conversation.participants.map(p => p.name).join(' and ')}`);
    }

    getRandomFromArray(array) {
        return array[Math.floor(Math.random() * array.length)];
    }

    // Für AI Brain Integration
    shouldInitiateConversation(character) {
        const socialNeed = 100 - (character.social || 50);
        const socialTrait = character.traits?.sozial || 0.5;
        
        // Höhere Wahrscheinlichkeit wenn sozialer und einsam
        const probability = (socialNeed / 100) * socialTrait * 0.02;
        
        return Math.random() < probability;
    }

    findConversationPartner(character) {
        if (!window.gameInstance) return null;
        
        const nearbyCharacters = window.gameInstance.characters.filter(other => {
            if (other === character) return false;
            
            const distance = Math.sqrt(
                Math.pow(character.x - other.x, 2) + 
                Math.pow(character.y - other.y, 2)
            );
            
            return distance < 80;
        });
        
        if (nearbyCharacters.length === 0) return null;
        
        // Bevorzuge Charaktere mit hoher sozialer Kompatibilität
        const compatibleCharacters = nearbyCharacters.filter(other => {
            const compatibility = this.calculateSocialCompatibility(character, other);
            return compatibility > 0.4;
        });
        
        const candidates = compatibleCharacters.length > 0 ? compatibleCharacters : nearbyCharacters;
        return candidates[Math.floor(Math.random() * candidates.length)];
    }

    calculateSocialCompatibility(char1, char2) {
        const traits1 = char1.traits;
        const traits2 = char2.traits;
        
        let compatibility = 0;
        let count = 0;
        
        for (const trait in traits1) {
            if (traits2[trait] !== undefined) {
                const similarity = 1 - Math.abs(traits1[trait] - traits2[trait]);
                compatibility += similarity;
                count++;
            }
        }
        
        return count > 0 ? compatibility / count : 0.5;
    }

    getConversationStats() {
        return {
            activeConversations: this.activeConversations.size,
            totalConversations: this.conversationHistory.size,
            topicsDiscussed: Array.from(this.conversationHistory.values())
                .map(c => c.topic)
                .reduce((acc, topic) => {
                    acc[topic] = (acc[topic] || 0) + 1;
                    return acc;
                }, {})
        };
    }
}

// Globale Instanzen
if (typeof window !== 'undefined') {
    window.survivalSystem = new SurvivalSystem();
    // Falls bereits eine umfassendere Konversations-Engine existiert, nicht überschreiben
    if (!window.conversationSystem) {
        window.conversationSystem = new SurvivalConversationSystem();
    }
}
