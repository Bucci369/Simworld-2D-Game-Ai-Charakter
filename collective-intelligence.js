/**
 * Collective Intelligence System
 * Ermöglicht Wissensaustausch zwischen KI-Charakteren
 */

class CollectiveIntelligence {
    constructor() {
        this.sharedKnowledge = new Map();
        this.socialNetwork = new Map();
        this.culturalLearning = [];
        this.emergentBehaviors = [];
        this.isEnabled = false;
        
        // Verschiedene Lerntypen
        this.learningTypes = {
            IMITATION: 'imitation',           // Nachahmen erfolgreicher Aktionen
            COMMUNICATION: 'communication',   // Direkter Wissensaustausch
            OBSERVATION: 'observation',       // Beobachten und Lernen
            CULTURAL: 'cultural'              // Kulturelle Evolution
        };
    }

    enable() {
        this.isEnabled = true;
        console.log('🌐 Collective Intelligence enabled');
        this.initializeSocialNetwork();
    }

    disable() {
        this.isEnabled = false;
        console.log('🌐 Collective Intelligence disabled');
    }

    initializeSocialNetwork() {
        if (!window.gameInstance || !window.gameInstance.characters) return;

        const characters = window.gameInstance.characters;
        
        // Erstelle soziales Netzwerk
        characters.forEach(character => {
            this.socialNetwork.set(character.name, {
                friends: [],
                reputation: 0.5,
                influence: character.traits.sozial || 0.5,
                lastInteraction: new Map()
            });
        });

        console.log('👥 Social network initialized for collective intelligence');
    }

    // Hauptmethode für kollektives Lernen
    processCollectiveLearning(characters) {
        if (!this.isEnabled) return;

        // Suche nach Interaktionen zwischen Charakteren
        this.detectSocialInteractions(characters);
        
        // Wissensaustausch zwischen nahestehenden Charakteren
        this.facilitateKnowledgeSharing(characters);
        
        // Imitationslernen
        this.processImitationLearning(characters);
        
        // Kulturelle Evolution
        this.processCulturalEvolution(characters);
        
        // Emergente Verhaltensweisen
        this.detectEmergentBehaviors(characters);
    }

    detectSocialInteractions(characters) {
        const interactionDistance = 80;
        
        for (let i = 0; i < characters.length; i++) {
            for (let j = i + 1; j < characters.length; j++) {
                const char1 = characters[i];
                const char2 = characters[j];
                
                const distance = Math.sqrt(
                    Math.pow(char1.x - char2.x, 2) + 
                    Math.pow(char1.y - char2.y, 2)
                );
                
                if (distance < interactionDistance) {
                    this.recordSocialInteraction(char1, char2);
                }
            }
        }
    }

    recordSocialInteraction(char1, char2) {
        const network1 = this.socialNetwork.get(char1.name);
        const network2 = this.socialNetwork.get(char2.name);
        
        if (!network1 || !network2) return;

        // Update letzte Interaktion
        network1.lastInteraction.set(char2.name, Date.now());
        network2.lastInteraction.set(char1.name, Date.now());
        
        // Erhöhe Freundschaft basierend auf Persönlichkeitskompatibilität
        const compatibility = this.calculateCompatibility(char1, char2);
        
        if (compatibility > 0.6) {
            if (!network1.friends.includes(char2.name)) {
                network1.friends.push(char2.name);
            }
            if (!network2.friends.includes(char1.name)) {
                network2.friends.push(char1.name);
            }
        }
    }

    calculateCompatibility(char1, char2) {
        const traits1 = char1.traits;
        const traits2 = char2.traits;
        
        // Berechne Ähnlichkeit der Persönlichkeitsmerkmale
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

    facilitateKnowledgeSharing(characters) {
        characters.forEach(character => {
            if (!character.aiBrain) return;
            
            const network = this.socialNetwork.get(character.name);
            if (!network) return;
            
            // Teile Wissen mit Freunden
            network.friends.forEach(friendName => {
                const friend = characters.find(c => c.name === friendName);
                if (friend && friend.aiBrain) {
                    this.shareKnowledge(character, friend);
                }
            });
        });
    }

    shareKnowledge(giver, receiver) {
        if (!giver.aiBrain || !receiver.aiBrain) return;
        
        // Teile erfolgreiche Strategien
        const giverMemories = giver.aiBrain.longTermMemory;
        const successfulMemories = giverMemories.filter(memory => memory.reward > 0.3);
        
        if (successfulMemories.length > 0) {
            const sharedMemory = successfulMemories[Math.floor(Math.random() * successfulMemories.length)];
            
            // Übertrage Wissen mit Vertrauensfaktor
            const network = this.socialNetwork.get(receiver.name);
            const trustFactor = network.friends.includes(giver.name) ? 0.8 : 0.3;
            
            if (Math.random() < trustFactor) {
                // Adaptiere das geteilte Wissen an den Empfänger
                const adaptedMemory = this.adaptKnowledgeToReceiver(sharedMemory, receiver);
                receiver.aiBrain.longTermMemory.push(adaptedMemory);
                
                console.log(`🤝 ${giver.name} shared knowledge about "${sharedMemory.action}" with ${receiver.name}`);
                
                // Speichere in geteiltem Wissen
                const knowledgeKey = `${sharedMemory.action}_strategy`;
                if (!this.sharedKnowledge.has(knowledgeKey)) {
                    this.sharedKnowledge.set(knowledgeKey, []);
                }
                this.sharedKnowledge.get(knowledgeKey).push({
                    source: giver.name,
                    action: sharedMemory.action,
                    effectiveness: sharedMemory.reward,
                    timestamp: Date.now()
                });
            }
        }
    }

    adaptKnowledgeToReceiver(memory, receiver) {
        return {
            ...memory,
            // Passe die Umgebungsdaten an die Persönlichkeit des Empfängers an
            environmentBefore: {
                ...memory.environmentBefore,
                curiosity: receiver.traits.neugier || memory.environmentBefore.curiosity,
                socialDesire: receiver.traits.sozial || memory.environmentBefore.socialDesire
            },
            reward: memory.reward * 0.8, // Reduziere Belohnung bei geteiltem Wissen
            timestamp: Date.now(),
            source: 'shared_knowledge'
        };
    }

    processImitationLearning(characters) {
        characters.forEach(character => {
            if (!character.aiBrain) return;
            
            // Finde erfolgreichste Charaktere in der Nähe
            const nearbyCharacters = this.findNearbyCharacters(character, characters, 120);
            const successfulCharacters = nearbyCharacters
                .filter(c => c.aiBrain && c.aiBrain.getSuccessRate() > character.aiBrain.getSuccessRate())
                .sort((a, b) => b.aiBrain.getSuccessRate() - a.aiBrain.getSuccessRate());
            
            if (successfulCharacters.length > 0 && Math.random() < 0.1) {
                const roleModel = successfulCharacters[0];
                this.imitateCharacter(character, roleModel);
            }
        });
    }

    imitateCharacter(imitator, roleModel) {
        if (!imitator.aiBrain || !roleModel.aiBrain) return;
        
        // Imitiere die Explorationsstrategie
        const exploration_adjustment = (roleModel.aiBrain.explorationRate - imitator.aiBrain.explorationRate) * 0.1;
        imitator.aiBrain.explorationRate = Math.max(0.05, Math.min(0.8, 
            imitator.aiBrain.explorationRate + exploration_adjustment
        ));
        
        // Imitiere erfolgreiche Aktionsmuster
        const roleModelActions = roleModel.aiBrain.longTermMemory
            .filter(m => m.reward > 0.5)
            .map(m => m.action);
        
        if (roleModelActions.length > 0) {
            const imitatedAction = roleModelActions[Math.floor(Math.random() * roleModelActions.length)];
            
            // Füge imitierte Aktion mit moderater Belohnung hinzu
            imitator.aiBrain.longTermMemory.push({
                action: imitatedAction,
                environmentBefore: imitator.aiBrain.perceiveEnvironment(
                    { characters: window.gameInstance.characters, terrain: window.gameInstance.terrain },
                    imitator
                ),
                reward: 0.4, // Moderate Belohnung für imitiertes Verhalten
                timestamp: Date.now(),
                source: 'imitation'
            });
            
            console.log(`👀 ${imitator.name} imitates ${roleModel.name}'s ${imitatedAction} strategy`);
        }
    }

    processCulturalEvolution(characters) {
        // Sammle kulturelle Trends
        const actionFrequency = new Map();
        
        characters.forEach(character => {
            if (character.aiBrain && character.currentAction !== 'idle') {
                actionFrequency.set(character.currentAction, 
                    (actionFrequency.get(character.currentAction) || 0) + 1);
            }
        });
        
        // Identifiziere dominante Kulturen
        const culturalTrend = Array.from(actionFrequency.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 2);
        
        if (culturalTrend.length > 0) {
            this.culturalLearning.push({
                trend: culturalTrend[0][0],
                popularity: culturalTrend[0][1],
                timestamp: Date.now()
            });
            
            // Begrenze kulturelle Geschichte
            if (this.culturalLearning.length > 20) {
                this.culturalLearning.shift();
            }
        }
    }

    detectEmergentBehaviors(characters) {
        // Suche nach unerwarteten Verhaltensmustern
        const currentBehaviors = characters.map(c => ({
            name: c.name,
            action: c.currentAction,
            position: { x: c.x, y: c.y },
            traits: c.traits
        }));
        
        // Gruppenerkennung
        const groups = this.detectGroups(currentBehaviors);
        if (groups.length > 1) {
            const emergentBehavior = {
                type: 'group_formation',
                groups: groups,
                timestamp: Date.now()
            };
            
            this.emergentBehaviors.push(emergentBehavior);
            console.log('🌟 Emergent behavior detected: Group formation', groups);
        }
        
        // Begrenze emergente Verhaltensgeschichte
        if (this.emergentBehaviors.length > 10) {
            this.emergentBehaviors.shift();
        }
    }

    detectGroups(behaviors) {
        const groups = [];
        const processed = new Set();
        
        behaviors.forEach(behavior => {
            if (processed.has(behavior.name)) return;
            
            const group = [behavior];
            processed.add(behavior.name);
            
            // Finde nahestehende Charaktere mit ähnlichem Verhalten
            behaviors.forEach(other => {
                if (processed.has(other.name)) return;
                
                const distance = Math.sqrt(
                    Math.pow(behavior.position.x - other.position.x, 2) +
                    Math.pow(behavior.position.y - other.position.y, 2)
                );
                
                if (distance < 100 && behavior.action === other.action) {
                    group.push(other);
                    processed.add(other.name);
                }
            });
            
            if (group.length >= 2) {
                groups.push(group);
            }
        });
        
        return groups;
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

    // Debugging und Monitoring
    getCollectiveStats() {
        return {
            isEnabled: this.isEnabled,
            sharedKnowledgeCount: this.sharedKnowledge.size,
            culturalTrends: this.culturalLearning.slice(-5),
            emergentBehaviors: this.emergentBehaviors.slice(-3),
            socialConnections: Array.from(this.socialNetwork.entries()).map(([name, network]) => ({
                name,
                friendCount: network.friends.length,
                reputation: network.reputation,
                influence: network.influence
            }))
        };
    }

    getSharedKnowledgeByCategory() {
        const categories = {};
        
        for (const [key, knowledge] of this.sharedKnowledge) {
            const category = key.split('_')[0];
            if (!categories[category]) {
                categories[category] = [];
            }
            categories[category].push(...knowledge);
        }
        
        return categories;
    }
}

// Globale Instanz für kollektive Intelligenz
if (typeof window !== 'undefined') {
    window.collectiveIntelligence = new CollectiveIntelligence();
    
    // Integration in Game Loop
    if (window.gameInstance) {
        const originalUpdateCharacters = window.gameInstance.updateCharacters;
        window.gameInstance.updateCharacters = function() {
            originalUpdateCharacters.call(this);
            window.collectiveIntelligence.processCollectiveLearning(this.characters);
        };
    }
}
