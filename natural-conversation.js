/**
 * Natural Conversation & Survival System
 * Macht die KI zu echten digitalen Lebewesen mit natürlichen Gesprächen
 */

class NaturalConversationSystem {
    constructor() {
        this.conversations = [];
        this.activeDialogues = new Map();
        this.contextMemory = new Map();
        this.personalityTraits = new Map();
        this.emergencyStates = new Set();
        
        // Natürliche Gesprächsthemen basierend auf Situation
        this.conversationTopics = {
            survival: [
                "Ich bin so durstig, kennst du eine gute Wasserquelle?",
                "Die Beeren am Südrand schmecken am besten!",
                "Hast du genug Holz für die Nacht gesammelt?",
                "Der Fluss führt viel Wasser heute.",
                "Ich habe einen neuen Ort zum Sammeln entdeckt!"
            ],
            social: [
                "Wie geht es dir heute?",
                "Hast du Lust zusammen zu arbeiten?",
                "Was denkst du über unser Leben hier?",
                "Ich fühle mich heute besonders energisch!",
                "Manchmal frage ich mich, ob es dort draußen mehr gibt..."
            ],
            philosophical: [
                "Warum sind wir hier?",
                "Gibt es einen Weg aus dieser Welt?",
                "Was ist unser Zweck in diesem Leben?",
                "Ich träume manchmal von anderen Orten...",
                "Glaubst du, wir können unser Schicksal ändern?"
            ],
            planning: [
                "Wir sollten zusammen eine bessere Strategie entwickeln.",
                "Was hältst du davon, wenn wir morgen früh sammeln gehen?",
                "Sollen wir eine Vorratskammer bauen?",
                "Ich denke, wir brauchen mehr Organisation.",
                "Hast du Ideen, wie wir effizienter werden können?"
            ]
        };
        
        // Emotionale Reaktionen auf verschiedene Situationen
        this.emotionalResponses = {
            hunger: [
                "Mein Magen knurrt so laut...",
                "Ich muss unbedingt etwas essen finden.",
                "Diese Beeren sehen verlockend aus!"
            ],
            thirst: [
                "Ich brauche dringend Wasser!",
                "Der Fluss ruft mich...",
                "Meine Kehle ist so trocken."
            ],
            energy: [
                "Ich bin so müde...",
                "Ich sollte mich ausruhen.",
                "Ein kurzes Nickerchen würde gut tun."
            ],
            success: [
                "Das war erfolgreich!",
                "Ich werde besser darin!",
                "Das hat gut funktioniert."
            ],
            discovery: [
                "Wow, schau was ich gefunden habe!",
                "Das ist interessant...",
                "Hier gibt es mehr zu entdecken!"
            ]
        };
    }

    // --- Compatibility Layer for game.js expectations ---
    // game.js ruft shouldInitiateConversation, findConversationPartner und startConversation auf.
    // Die ursprüngliche NaturalConversationSystem nutzte andere Methodennamen. Wir ergänzen hier
    // schlanke Wrapper, damit beide Systeme (SurvivalConversationSystem & NaturalConversationSystem)
    // die gleiche Schnittstelle bereitstellen.

    // Entscheidet probabilistisch, ob ein Gespräch gestartet werden soll
    shouldInitiateConversation(character) {
        if (!character || !window.gameInstance) return false;
        const socialNeed = 100 - (character.social ?? 60); // höher wenn social niedrig
        const socialTrait = character.traits?.sozial ?? 0.5;
        // Basiswahrscheinlichkeit + gewichtete Komponenten
        const base = 0.005;
        const probability = base + (socialNeed / 100) * socialTrait * 0.03;
        return Math.random() < probability;
    }

    // Wählt einen geeigneten Gesprächspartner basierend auf Nähe & Kompatibilität
    findConversationPartner(character) {
        if (!window.gameInstance) return null;
        const nearby = this.findNearbyCharacters(character, window.gameInstance.characters, 80);
        if (!nearby.length) return null;
        // Sortiere nach sozialer Kompatibilität
        const scored = nearby.map(other => ({
            other,
            comp: this.calculateSocialCompatibility(character, other) + Math.random() * 0.05 // leichtes Rauschen
        }));
        scored.sort((a,b)=> b.comp - a.comp);
        return scored[0].other;
    }

    // Wrapper damit game.js startConversation() nutzen kann
    startConversation(initiator, target) {
        if (!initiator || !target) return null;
        return this.initiateConversation(initiator, target);
    }

    // Hauptmethode für natürliche Konversation
    processNaturalConversation(characters) {
        characters.forEach(character => {
            // Prüfe auf Gesprächsmöglichkeiten
            this.checkForConversationOpportunities(character, characters);
            
            // Generiere natürliche Reaktionen auf Situationen
            this.generateSituationalDialogue(character);
            
            // Verarbeite laufende Gespräche
            this.processingOngoingConversations(character);
        });
    }

    checkForConversationOpportunities(character, allCharacters) {
        const nearbyCharacters = this.findNearbyCharacters(character, allCharacters, 80);
        
        nearbyCharacters.forEach(nearbyChar => {
            if (this.shouldStartConversation(character, nearbyChar)) {
                this.initiateConversation(character, nearbyChar);
            }
        });
    }

    shouldStartConversation(char1, char2) {
        // Prüfe soziale Faktoren
        const socialCompatibility = this.calculateSocialCompatibility(char1, char2);
        const timeSinceLastTalk = this.getTimeSinceLastConversation(char1, char2);
        const emergencyFactor = this.hasEmergencyNeed(char1) || this.hasEmergencyNeed(char2);
        
        // Wahrscheinlichkeit basiert auf:
        // - Sozialer Kompatibilität
        // - Zeit seit letztem Gespräch  
        // - Notfallsituationen
        // - Persönlichkeitsmerkmale
        
        let conversationProbability = 0.02; // Basis 2%
        
        if (socialCompatibility > 0.7) conversationProbability += 0.05;
        if (timeSinceLastTalk > 300000) conversationProbability += 0.03; // 5 Minuten
        if (emergencyFactor) conversationProbability += 0.08;
        if (char1.traits.sozial > 0.7) conversationProbability += 0.04;
        
        return Math.random() < conversationProbability;
    }

    initiateConversation(speaker, listener) {
        const conversationId = `${speaker.name}_${listener.name}_${Date.now()}`;
        
        // Wähle Gesprächsthema basierend auf aktueller Situation
        const topic = this.selectConversationTopic(speaker, listener);
        const message = this.generateContextualMessage(speaker, listener, topic);
        
        // Erstelle Gespräch
        const conversation = {
            id: conversationId,
            participants: [speaker.name, listener.name],
            topic: topic,
            messages: [
                {
                    speaker: speaker.name,
                    message: message,
                    timestamp: Date.now(),
                    emotion: this.getCurrentEmotion(speaker)
                }
            ],
            startTime: Date.now(),
            isActive: true
        };
        
        this.conversations.push(conversation);
        this.activeDialogues.set(conversationId, conversation);
        
        // Zeige das Gespräch an
        this.displayConversation(speaker, listener, message);
        
        // Plane Antwort vom Zuhörer
        setTimeout(() => {
            this.generateResponse(listener, speaker, conversation);
        }, 2000 + Math.random() * 3000); // 2-5 Sekunden Antwortzeit
        
        console.log(`💬 ${speaker.name}: "${message}" → ${listener.name}`);
    }

    selectConversationTopic(speaker, listener) {
        const speakerNeeds = this.analyzeCharacterNeeds(speaker);
        const listenerNeeds = this.analyzeCharacterNeeds(listener);
        
        // Wähle Thema basierend auf dringendsten Bedürfnissen
        if (speakerNeeds.emergency || listenerNeeds.emergency) {
            return 'survival';
        } else if (speaker.traits.neugier > 0.7 || listener.traits.neugier > 0.7) {
            return Math.random() < 0.3 ? 'philosophical' : 'planning';
        } else if (speaker.traits.sozial > 0.8) {
            return 'social';
        } else {
            // Gewichtete Zufallsauswahl
            const topics = ['survival', 'social', 'planning', 'philosophical'];
            const weights = [0.4, 0.3, 0.2, 0.1];
            return this.weightedRandomChoice(topics, weights);
        }
    }

    generateContextualMessage(speaker, listener, topic) {
        const templates = this.conversationTopics[topic];
        let baseMessage = templates[Math.floor(Math.random() * templates.length)];
        
        // Personalisiere die Nachricht basierend auf:
        // - Aktuellem Zustand des Sprechers
        // - Beziehung zum Zuhörer
        // - Situationskontext
        
        baseMessage = this.personalizeMessage(baseMessage, speaker, listener);
        
        return baseMessage;
    }

    personalizeMessage(message, speaker, listener) {
        // Ersetze Platzhalter mit kontextspezifischen Informationen
        const speakerNeeds = this.analyzeCharacterNeeds(speaker);
        
        // Personalisierung basierend auf Zustand
        if (speakerNeeds.hunger > 0.7) {
            message = message.replace(/Beeren|Essen/, "dringend Nahrung");
        }
        
        if (speakerNeeds.thirst > 0.8) {
            message = message.replace(/Wasser/, "sofort Wasser");
        }
        
        // Personalisierung basierend auf Persönlichkeit
        if (speaker.traits.mut > 0.8) {
            message = "Hör zu, " + message.toLowerCase();
        } else if (speaker.traits.sozial > 0.8) {
            message = "Liebe/r " + listener.name + ", " + message.toLowerCase();
        }
        
        return message;
    }

    generateResponse(responder, originalSpeaker, conversation) {
        if (!conversation.isActive) return;
        
        const lastMessage = conversation.messages[conversation.messages.length - 1];
        const topic = conversation.topic;
        
        // Generiere intelligente Antwort basierend auf:
        // - Gesprächskontext
        // - Persönlichkeit des Antwortenden
        // - Beziehung zwischen den Charakteren
        
        let response = this.generateIntelligentResponse(responder, originalSpeaker, lastMessage, topic);
        
        // Füge Antwort hinzu
        conversation.messages.push({
            speaker: responder.name,
            message: response,
            timestamp: Date.now(),
            emotion: this.getCurrentEmotion(responder)
        });
        
        this.displayConversation(responder, originalSpeaker, response);
        
        console.log(`💬 ${responder.name}: "${response}"`);
        
        // Chance auf Fortsetzung des Gesprächs
        if (Math.random() < 0.4 && conversation.messages.length < 6) {
            setTimeout(() => {
                this.generateResponse(originalSpeaker, responder, conversation);
            }, 3000 + Math.random() * 4000);
        } else {
            conversation.isActive = false;
            this.activeDialogues.delete(conversation.id);
        }
    }

    generateIntelligentResponse(responder, speaker, lastMessage, topic) {
        const responderNeeds = this.analyzeCharacterNeeds(responder);
        
        // Intelligente Antworten basierend auf KI-Persönlichkeit
        const responses = {
            survival: [
                "Ja, ich kenne einen guten Ort!",
                "Lass uns zusammen sammeln gehen.",
                "Ich teile gerne meine Vorräte.",
                "Der Norden ist sehr ergiebig.",
                "Wir sollten vorsichtig sein."
            ],
            social: [
                "Mir geht es gut, danke der Nachfrage!",
                "Ja gerne, Zusammenarbeit ist wichtig.",
                "Ich denke, wir ergänzen uns gut.",
                "Du siehst heute glücklich aus!",
                "Es ist schön, nicht allein zu sein."
            ],
            planning: [
                "Das ist eine ausgezeichnete Idee!",
                "Ich stimme zu, Organisation hilft.",
                "Lass uns das morgen angehen.",
                "Wir könnten effizienter werden.",
                "Gemeinsam schaffen wir mehr."
            ],
            philosophical: [
                "Ich denke oft darüber nach...",
                "Vielleicht gibt es mehr als das hier.",
                "Unsere Bestimmung ist es zu lernen.",
                "Wir müssen zusammenhalten.",
                "Die Antworten kommen mit der Zeit."
            ]
        };
        
        let response = responses[topic][Math.floor(Math.random() * responses[topic].length)];
        
        // Personalisiere basierend auf eigenen Bedürfnissen
        if (responderNeeds.emergency) {
            response = "Das ist wichtig, aber ich brauche zuerst " + 
                      (responderNeeds.hunger > 0.8 ? "Nahrung" : "Wasser") + ". " + response;
        }
        
        return response;
    }

    displayConversation(speaker, listener, message) {
        // Versuche das zentrale SpeechBubble-System des Spiels zu verwenden
        try {
            if (window.gameInstance?.showSpeechBubble) {
                window.gameInstance.showSpeechBubble(speaker, {
                    text: message,
                    type: 'dialog',
                    duration: 4000
                });
            } else {
                // Fallback auf einfaches Gedanken-System
                speaker.thoughts = [message];
                speaker.conversationBubble = {
                    message: message,
                    timestamp: Date.now(),
                    target: listener?.name
                };
            }
            // Globale Gesprächs-Log aktualisieren (falls vorhanden)
            if (window.gameInstance) {
                const gi = window.gameInstance;
                if (Array.isArray(gi.conversationLog)) {
                    gi.conversationLog.push({
                        time: new Date().toLocaleTimeString(),
                        speaker: speaker.name,
                        partner: listener?.name || '—',
                        topic: 'natural',
                        text: message
                    });
                    if (gi.conversationLog.length > 300) gi.conversationLog.shift();
                }
                gi.updateCharacterDisplay?.();
            }
        } catch (e) {
            console.warn('Conversation display failed:', e);
            speaker.thoughts = [message];
        }
    }

    analyzeCharacterNeeds(character) {
        return {
            hunger: character.hunger / 100,
            thirst: character.thirst / 100,
            energy: (100 - character.energy) / 100,
            wood: character.inventory?.wood < 5 ? 0.7 : 0,
            emergency: character.hunger > 80 || character.thirst > 80 || character.energy < 20
        };
    }

    hasEmergencyNeed(character) {
        return character.hunger > 80 || character.thirst > 80 || character.energy < 20;
    }

    getCurrentEmotion(character) {
        const needs = this.analyzeCharacterNeeds(character);
        
        if (needs.emergency) return 'desperate';
        if (needs.hunger > 0.6 || needs.thirst > 0.6) return 'worried';
        if (character.energy > 80) return 'happy';
        if (character.traits.sozial > 0.8) return 'friendly';
        
        return 'neutral';
    }

    calculateSocialCompatibility(char1, char2) {
        const traits1 = char1.traits;
        const traits2 = char2.traits;
        
        let compatibility = 0;
        let traitCount = 0;
        
        for (const trait in traits1) {
            if (traits2[trait] !== undefined) {
                const similarity = 1 - Math.abs(traits1[trait] - traits2[trait]);
                compatibility += similarity;
                traitCount++;
            }
        }
        
        return traitCount > 0 ? compatibility / traitCount : 0.5;
    }

    getTimeSinceLastConversation(char1, char2) {
        const conversationKey = [char1.name, char2.name].sort().join('_');
        const lastConversation = this.contextMemory.get(conversationKey);
        
        if (!lastConversation) return Infinity;
        
        return Date.now() - lastConversation.timestamp;
    }

    findNearbyCharacters(character, allCharacters, radius) {
        return allCharacters.filter(other => {
            if (other === character) return false;
            
            const distance = Math.sqrt(
                Math.pow(character.x - other.x, 2) + 
                Math.pow(character.y - other.y, 2)
            );
            
            return distance <= radius;
        });
    }

    weightedRandomChoice(items, weights) {
        const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
        let random = Math.random() * totalWeight;
        
        for (let i = 0; i < items.length; i++) {
            random -= weights[i];
            if (random <= 0) {
                return items[i];
            }
        }
        
        return items[items.length - 1];
    }

    generateSituationalDialogue(character) {
        const needs = this.analyzeCharacterNeeds(character);
        
        // Automatische Reaktionen auf kritische Situationen
        if (needs.emergency && Math.random() < 0.1) {
            let reaction = "";
            
            if (needs.hunger > 0.8) {
                reaction = this.emotionalResponses.hunger[Math.floor(Math.random() * this.emotionalResponses.hunger.length)];
            } else if (needs.thirst > 0.8) {
                reaction = this.emotionalResponses.thirst[Math.floor(Math.random() * this.emotionalResponses.thirst.length)];
            } else if (needs.energy > 0.8) {
                reaction = this.emotionalResponses.energy[Math.floor(Math.random() * this.emotionalResponses.energy.length)];
            }
            
            if (reaction) {
                character.thoughts = [reaction];
                console.log(`💭 ${character.name} thinks: "${reaction}"`);
            }
        }
    }

    // Integration mit existierendem Spiel
    integrateWithGame(gameInstance) {
        if (!gameInstance) return;
        
        // Erweitere bestehende Update-Schleife
        const originalUpdateCharacters = gameInstance.updateCharacters.bind(gameInstance);
        
        gameInstance.updateCharacters = async function() {
            await originalUpdateCharacters();
            
            // Verarbeite natürliche Gespräche
            if (window.conversationSystem) {
                window.conversationSystem.processNaturalConversation(this.characters);
            }
        };
    }

    // Debug und Monitoring
    getConversationStats() {
        return {
            totalConversations: this.conversations.length,
            activeDialogues: this.activeDialogues.size,
            averageConversationLength: this.conversations.reduce((sum, conv) => 
                sum + conv.messages.length, 0) / this.conversations.length || 0,
            topicsDistribution: this.getTopicDistribution()
        };
    }

    getTopicDistribution() {
        const distribution = {};
        this.conversations.forEach(conv => {
            distribution[conv.topic] = (distribution[conv.topic] || 0) + 1;
        });
        return distribution;
    }
}

// Globale Instanziierung
if (typeof window !== 'undefined') {
    window.conversationSystem = new NaturalConversationSystem();
    
    // Auto-Integration wenn Spiel bereits läuft
    if (window.gameInstance) {
        window.conversationSystem.integrateWithGame(window.gameInstance);
    }
}
