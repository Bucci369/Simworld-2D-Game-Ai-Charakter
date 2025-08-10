/**
 * Advanced AI Brain System for Village Characters
 * Nutzt TensorFlow.js für lokales maschinelles Lernen
 */

class AIBrain {
    constructor(personality) {
        this.personality = personality;
        this.memories = [];
        this.knowledgeBase = new Map();
        this.emotionalState = {
            happiness: 0.5,
            stress: 0.2,
            curiosity: personality.traits.neugier,
            social: personality.traits.sozial
        };
        
        // Neuronales Netzwerk für Entscheidungsfindung (async initialisiert)
        this.useNeuralNetwork = false;
        this.networkInitialized = false;
        this.initializeNeuralNetwork().catch(error => {
            console.warn(`Neural network initialization failed for ${personality.name}:`, error);
            this.useNeuralNetwork = false;
        });
        
        // Lernstatistiken
        this.learningStats = {
            decisionsKnnen: 0,
            successfulActions: 0,
            failedActions: 0,
            knowledgePoints: 0
        };
        
        // Kurz- und Langzeitgedächtnis
        this.shortTermMemory = [];
        this.longTermMemory = [];
        this.episodicMemory = []; // Spezifische Ereignisse
        
        // Adaptive Lernrate
        this.learningRate = 0.01;
        this.explorationRate = 0.3; // Epsilon für Exploration vs. Exploitation
    }

    async initializeNeuralNetwork() {
        try {
            // Warte auf TensorFlow.js
            if (typeof tf === 'undefined') {
                console.warn('TensorFlow.js not loaded, using fallback AI');
                this.useNeuralNetwork = false;
                this.networkInitialized = true;
                return;
            }

            this.useNeuralNetwork = true;

            // Input: [hunger, energy, time, weather, social_proximity, resource_availability, danger_level, emotional_state]
            // Output: [action_probabilities] für verschiedene Aktionen
            this.decisionNetwork = tf.sequential({
                layers: [
                    tf.layers.dense({ inputShape: [12], units: 32, activation: 'relu' }),
                    tf.layers.dropout({ rate: 0.2 }),
                    tf.layers.dense({ units: 24, activation: 'relu' }),
                    tf.layers.dropout({ rate: 0.2 }),
                    tf.layers.dense({ units: 16, activation: 'relu' }),
                    tf.layers.dense({ units: 8, activation: 'softmax' }) // 8 verschiedene Aktionen
                ]
            });

            // Compile des Netzwerks
            this.decisionNetwork.compile({
                optimizer: tf.train.adam(this.learningRate),
                loss: 'categoricalCrossentropy',
                metrics: ['accuracy']
            });

            // Wertenetzwerk für Reinforcement Learning
            this.valueNetwork = tf.sequential({
                layers: [
                    tf.layers.dense({ inputShape: [12], units: 24, activation: 'relu' }),
                    tf.layers.dense({ units: 16, activation: 'relu' }),
                    tf.layers.dense({ units: 1, activation: 'linear' }) // Werteschätzung
                ]
            });

            this.valueNetwork.compile({
                optimizer: tf.train.adam(this.learningRate),
                loss: 'meanSquaredError'
            });

            this.networkInitialized = true;
            console.log(`🧠 Neural network initialized for ${this.personality.name}`);
        } catch (error) {
            console.error(`Failed to initialize neural network for ${this.personality.name}:`, error);
            this.useNeuralNetwork = false;
            this.networkInitialized = true;
        }
    }

    // Wrapper method for game compatibility - ROBUST VERSION
    async makeDecision(environmentData, availableActions) {
        try {
            // Prevent endless loops - rate limit calls
            const now = Date.now();
            if (this.lastDecisionTime && (now - this.lastDecisionTime) < 100) {
                // Too frequent calls - return cached decision
                return this.cachedDecision || { action: 'idle', confidence: 0.5 };
            }
            this.lastDecisionTime = now;

            // Convert environmentData format to what makeIntelligentDecision expects
            const gameState = {
                gameTime: environmentData.gameTime || 480,
                isNight: (environmentData.gameTime || 480) > 1320 || (environmentData.gameTime || 480) < 360,
                characters: window.gameInstance?.characters || [],
                terrain: window.gameInstance?.terrain || []
            };
            
            // Find the character from game instance with better error handling
            const character = window.gameInstance?.characters?.find(c => c.aiBrain === this);
            if (!character) {
                console.warn('Could not find character for AI brain - using simple decision');
                return { action: this.getSimpleDecision(environmentData), confidence: 0.3 };
            }
            
            // Use simple rule-based decision if neural network not ready
            if (this.useNeuralNetwork && !this.networkInitialized) {
                const simpleDecision = this.getSimpleDecision(environmentData);
                this.cachedDecision = { action: simpleDecision, confidence: 0.4 };
                return this.cachedDecision;
            }
            
            const decision = await this.makeIntelligentDecision(gameState, character);
            const result = { 
                action: decision, 
                confidence: this.useNeuralNetwork ? 0.8 : 0.6 
            };
            
            this.cachedDecision = result;
            return result;
            
        } catch (error) {
            console.warn(`AI makeDecision error for ${this.personality?.name}:`, error.message);
            // Return safe fallback
            const fallback = { action: this.getSimpleDecision(environmentData), confidence: 0.2 };
            this.cachedDecision = fallback;
            return fallback;
        }
    }

    // Simple decision fallback to prevent loops
    getSimpleDecision(environmentData) {
        if (environmentData.hunger > 70) return 'gather_food';
        if (environmentData.energy < 30) return 'rest';
        if (Math.random() < 0.3) return 'explore';
        return 'gather_food';
    }

    // Hauptmethode für intelligente Entscheidungsfindung
    async makeIntelligentDecision(gameState, character) {
        try {
            // Warte auf Netzwerk-Initialisierung falls noch nicht abgeschlossen
            if (!this.networkInitialized) {
                await this.waitForInitialization();
            }
            
            // Sammle Umgebungsinformationen mit verbesserter Kontextanalyse
            const environmentData = this.perceiveEnvironment(gameState, character);
            
            // Update emotionalen Zustand mit Tag/Nacht-Einfluss
            this.updateEmotionalState(environmentData, character, gameState);
            
            // Überdenke vorherige Entscheidungen
            this.reflectOnPreviousActions();
            
            // Wenn Neuronales Netzwerk verfügbar, verwende es
            if (this.useNeuralNetwork && this.decisionNetwork) {
                return await this.neuralDecision(environmentData, character);
            } else {
                // Verbesserte regel-basierte AI mit Kontext
                return this.intelligentRuleBasedDecision(environmentData, character, gameState);
            }
        } catch (error) {
            console.error(`AI decision error for ${this.personality.name}:`, error);
            // Fallback auf einfache Regel-basierte Entscheidung
            return this.simpleDecision(character);
        }
    }
    
    async waitForInitialization(maxWait = 3000) {
        const startTime = Date.now();
        while (!this.networkInitialized && (Date.now() - startTime) < maxWait) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }
    
    simpleDecision(character) {
        // Sehr einfache Fallback-Entscheidung
        if (character.hunger > 70) return 'essen';
        if (character.energy < 30) return 'schlafen';
        if (Math.random() < 0.3) return 'erkunden';
        return 'sammeln';
    }

    perceiveEnvironment(gameState, character) {
        const nearbyCharacters = this.findNearbyCharacters(gameState.characters, character);
        const nearbyResources = this.findNearbyResources(gameState.terrain, character);
        const timeOfDay = gameState.gameTime / (24 * 60); // Normalisiert 0-1
        
        return {
            // Körperliche Bedürfnisse
            hunger: character.hunger / 100,
            energy: character.energy / 100,
            
            // Zeitkontext
            timeOfDay: timeOfDay,
            dayProgress: (gameState.gameTime % (24 * 60)) / (24 * 60),
            
            // Soziale Umgebung
            nearbyCharactersCount: nearbyCharacters.length,
            socialDesire: this.calculateSocialDesire(nearbyCharacters, character),
            
            // Ressourcenumgebung
            nearbyFood: nearbyResources.food,
            nearbyMaterials: nearbyResources.materials,
            dangerLevel: this.assessDanger(gameState, character),
            
            // Emotionaler Zustand
            happiness: this.emotionalState.happiness,
            stress: this.emotionalState.stress,
            curiosity: this.emotionalState.curiosity,
            
            // Wetter/Umgebung
            ambientLight: gameState.ambientLight || 0.8
        };
    }

    async neuralDecision(environmentData, character) {
        // KRITISCHE BEDÜRFNISSE überschreiben Neural Network
        if (environmentData.energy < 0.25) {
            console.log(`💤 ${character.name} NN OVERRIDE - kritische Müdigkeit`);
            return 'schlafen';
        }
        
        if (environmentData.hunger > 0.85) {
            console.log(`🍽️ ${character.name} NN OVERRIDE - kritischer Hunger`);
            return 'essen';
        }
        
        // Konvertiere Umgebungsdaten zu Tensor
        const inputTensor = tf.tensor2d([[
            environmentData.hunger,
            environmentData.energy,
            environmentData.timeOfDay,
            environmentData.dayProgress,
            environmentData.nearbyCharactersCount / 10, // Normalisiert
            environmentData.socialDesire,
            environmentData.nearbyFood / 10, // Normalisiert
            environmentData.nearbyMaterials / 10,
            environmentData.dangerLevel,
            environmentData.happiness,
            environmentData.stress,
            environmentData.curiosity
        ]]);

        try {
            // IMPROVED TENSORFLOW.JS MEMORY MANAGEMENT
            let prediction = null;
            let probabilities = null;
            
            try {
                // Vorhersage der Aktionswahrscheinlichkeiten
                prediction = this.decisionNetwork.predict(inputTensor);
                probabilities = await prediction.data();
                
                // Aktionen definieren
                const actions = ['sammeln', 'erkunden', 'bauen', 'sozialisieren', 'essen', 'schlafen', 'lernen', 'spielen'];
                
                let selectedAction;
                
                // Erhöhte Exploration Rate für besseres Lernen
                const adaptiveExploration = this.explorationRate * (1 + (1 - this.getSuccessRate()));
                
                if (Math.random() < Math.min(0.6, adaptiveExploration)) {
                    // Intelligente Exploration: bevorzuge sinnvolle Aktionen
                    const reasonableActions = this.filterReasonableActions(actions, environmentData);
                    selectedAction = reasonableActions[Math.floor(Math.random() * reasonableActions.length)];
                    if (Math.random() < 0.2) { // Reduce logging frequency
                        console.log(`🎲 ${character.name} intelligente Exploration: ${selectedAction}`);
                    }
                } else {
                    // Exploitation: Beste vorhergesagte Aktion
                    const bestActionIndex = probabilities.indexOf(Math.max(...probabilities));
                    selectedAction = actions[bestActionIndex];
                    if (Math.random() < 0.3) { // Reduce logging frequency
                        console.log(`🎯 ${character.name} NN wählt: ${selectedAction} (Confidence: ${(Math.max(...probabilities) * 100).toFixed(1)}%)`);
                    }
                }
                
                // Speichere Entscheidung für späteres Lernen (but don't store tensor to avoid memory leaks)
                this.storeDecisionForLearning(environmentData, selectedAction, null);
                
                return selectedAction;
                
            } finally {
                // CRITICAL: Always dispose tensors to prevent memory leaks
                if (inputTensor) {
                    try { inputTensor.dispose(); } catch(e) { console.warn('Failed to dispose inputTensor:', e); }
                }
                if (prediction) {
                    try { prediction.dispose(); } catch(e) { console.warn('Failed to dispose prediction:', e); }
                }
            }
            
        } catch (error) {
            console.warn('Neural decision error:', error.message);
            // Ensure tensor cleanup even on error
            if (inputTensor) {
                try { inputTensor.dispose(); } catch(e) { /* ignore */ }
            }
            
            return this.intelligentRuleBasedDecision(environmentData, character, {
                gameTime: window.gameInstance?.gameTime || 480,
                isNight: window.gameInstance?.isNight || false
            });
        }
    }
    
    filterReasonableActions(actions, environmentData) {
        const reasonable = [];
        
        // Immer sinnvolle Basisaktionen
        reasonable.push('sammeln', 'erkunden');
        
        // Kontext-abhängige Aktionen
        if (environmentData.energy < 0.6) reasonable.push('schlafen');
        if (environmentData.hunger > 0.5) reasonable.push('essen');
        if (environmentData.nearbyCharactersCount > 0) reasonable.push('sozialisieren');
        if (environmentData.curiosity > 0.5) reasonable.push('lernen');
        
        return reasonable.length > 0 ? reasonable : actions;
    }

    ruleBasedDecisionWithLearning(environmentData, character) {
        const decisions = [];
        
        // Intelligente Prioritätensberechnung basierend auf Lernerfahrung
        const learnedWeights = this.getLearnedWeights();
        
        // Kritische Bedürfnisse (hohe Priorität)
        if (environmentData.hunger > 0.7) {
            decisions.push({ 
                action: 'essen', 
                priority: environmentData.hunger * 100 * learnedWeights.eating 
            });
        }
        
        if (environmentData.energy < 0.3) {
            decisions.push({ 
                action: 'schlafen', 
                priority: (1 - environmentData.energy) * 80 * learnedWeights.sleeping 
            });
        }
        
        // Persönlichkeitsbasierte Entscheidungen mit Lernanpassung
        if (Math.random() < character.traits.fleiss * 0.02) {
            const preference = character.preferredAction;
            decisions.push({ 
                action: preference, 
                priority: 50 * learnedWeights[preference] || 1.0 
            });
        }
        
        // Adaptive Exploration basierend auf Erfolg
        if (Math.random() < character.traits.neugier * this.emotionalState.curiosity * 0.015) {
            decisions.push({ 
                action: 'erkunden', 
                priority: 30 * learnedWeights.exploring || 1.0 
            });
        }
        
        // Soziale Interaktion basierend auf gelernten Mustern
        if (environmentData.socialDesire > 0.5) {
            decisions.push({ 
                action: 'sozialisieren', 
                priority: environmentData.socialDesire * 40 * learnedWeights.socializing || 1.0 
            });
        }
        
        // Neue Aktion: Lernen/Denken
        if (this.shouldConsiderLearning(environmentData)) {
            decisions.push({ 
                action: 'lernen', 
                priority: this.emotionalState.curiosity * 35 
            });
        }
        
        // Wähle beste Entscheidung und lerne daraus
        if (decisions.length > 0) {
            const bestDecision = decisions.reduce((a, b) => a.priority > b.priority ? a : b);
            this.recordDecision(environmentData, bestDecision.action);
            return bestDecision.action;
        }
        
        return 'idle';
    }

    // Lernsystem - Belohnung/Bestrafung basierend auf Aktionsergebnis
    async learnFromActionResult(action, environmentBefore, environmentAfter, character) {
        const reward = this.calculateReward(action, environmentBefore, environmentAfter, character);
        
        // Update Lernstatistiken
        this.learningStats.decisionsKnnen++;
        if (reward > 0) {
            this.learningStats.successfulActions++;
        } else {
            this.learningStats.failedActions++;
        }
        
        // Speichere Erfahrung im Gedächtnis
        const experience = {
            action,
            environmentBefore,
            environmentAfter,
            reward,
            timestamp: Date.now()
        };
        
        this.shortTermMemory.push(experience);
        
        // Übertrage wichtige Erfahrungen ins Langzeitgedächtnis
        if (Math.abs(reward) > 0.5 || this.shortTermMemory.length > 20) {
            this.consolidateMemory();
        }
        
        // Neural Network Training (falls verfügbar)
        if (this.useNeuralNetwork && this.decisionNetwork) {
            await this.trainNeuralNetwork(experience);
        }
        
        // Update adaptive Parameter
        this.updateLearningParameters(reward);
        
        // REDUZIERTES LOGGING - verhindert Spam von unwichtigen Lernvorgängen
        const shouldLog = this.shouldLogLearning(action, reward, character);
        if (shouldLog) {
            console.log(`📚 ${character.name} learned from ${action}: reward=${reward.toFixed(2)}, exploration_rate=${this.explorationRate.toFixed(2)}`);
        }
    }

    shouldLogLearning(action, reward, character) {
        // INTELLIGENTE LOG-FILTERUNG um Spam zu reduzieren
        
        // Nie loggen für komplett unwichtige Aktionen
        if (action === 'idle' || !action) {
            return Math.random() < 0.05; // Nur 5% der idle-Lernvorgänge loggen
        }
        
        // Immer loggen für signifikante Belohnungen/Bestrafungen
        if (Math.abs(reward) > 0.5) {
            return true;
        }
        
        // Loggen für erste paar Lerndurchgänge (damit man sieht dass es funktioniert)
        if (this.learningStats.decisionsKnnen < 20) {
            return true;
        }
        
        // Seltener loggen für mittlere Belohnungen bei erfahrenen Charakteren
        if (this.learningStats.decisionsKnnen > 100) {
            if (Math.abs(reward) < 0.3) {
                return Math.random() < 0.1; // Nur 10% der geringen Belohnungen loggen
            } else {
                return Math.random() < 0.3; // 30% der mittleren Belohnungen loggen
            }
        }
        
        // Standardfall: logge wichtige Aktionen häufiger
        const importantActions = ['essen', 'schlafen', 'gather_food', 'drink_water'];
        if (importantActions.includes(action)) {
            return Math.random() < 0.4; // 40% der wichtigen Aktionen loggen
        }
        
        // Andere Aktionen: moderat loggen
        return Math.random() < 0.2; // 20% der anderen Aktionen loggen
    }

    calculateReward(action, envBefore, envAfter, character) {
        let reward = 0;
        
        // NEUE AGGRESSIVE BELOHNUNGSFORMUNG - verhindert 0.00 rewards komplett
        const MIN_REWARD = 0.15; // Minimum positive reward
        const MIN_PENALTY = -0.15; // Minimum negative penalty
        
        // Belohnung für Bedürfnisbefriedigung
        const hungerChange = envBefore.hunger - envAfter.hunger;
        const energyChange = envAfter.energy - envBefore.energy;
        const thirstChange = envBefore.thirst - envAfter.thirst;
        
        // DIREKTE BEDÜRFNISBEFRIEDIGUNG - hohe Belohnungen
        if (action === 'essen' && hungerChange > 0) {
            reward += Math.max(0.4, hungerChange * 4); // Minimum 0.4, skaliert hoch
        } else if (action === 'essen' && hungerChange <= 0 && envBefore.hunger > 0.3) {
            reward -= 0.3; // Bestrafe sinnloses Essen
        }
        
        if (action === 'schlafen' && energyChange > 0) {
            reward += Math.max(0.4, energyChange * 3.5); // Minimum 0.4, skaliert hoch
        } else if (action === 'schlafen' && energyChange <= 0 && envBefore.energy > 0.7) {
            reward -= 0.25; // Bestrafe unnötiges Schlafen
        }
        
        if (action === 'trinken' && thirstChange > 0) {
            reward += Math.max(0.3, thirstChange * 3);
        }
        
        // KRITISCHE BEDÜRFNISSE - massive Belohnungen/Bestrafungen
        if (envBefore.hunger > 0.85 && action === 'essen') {
            reward += 0.8; // Große Belohnung für kritischen Hunger
        }
        if (envBefore.hunger > 0.8 && action !== 'essen') {
            reward -= 0.9; // Massive Bestrafung für ignorieren von kritischem Hunger
        }
        
        if (envBefore.energy < 0.25 && action === 'schlafen') {
            reward += 0.7; // Große Belohnung für kritische Müdigkeit
        }
        if (envBefore.energy < 0.3 && action !== 'schlafen') {
            reward -= 0.8; // Massive Bestrafung für ignorieren kritischer Müdigkeit
        }
        
        // ZEIT-BASIERTE BELOHNUNGEN
        const gameTime = window.gameInstance?.gameTime || 480;
        const timeOfDay = gameTime / 60;
        const isNight = timeOfDay >= 22 || timeOfDay < 6;
        
        if (action === 'schlafen' && isNight && envBefore.energy < 0.6) {
            reward += 0.5; // Starke Belohnung für nächtliches Schlafen
        } else if (action === 'schlafen' && !isNight && envBefore.energy > 0.5) {
            reward -= 0.4; // Bestrafe Tagschlaf wenn nicht müde
        }
        
        if (action === 'erkunden' && !isNight && character.traits.neugier > 0.6) {
            reward += 0.3; // Belohne Tag-Exploration
        } else if (action === 'erkunden' && isNight) {
            reward -= 0.2; // Bestrafe Nacht-Exploration
        }
        
        // PRODUKTIVITÄTS-BELOHNUNGEN
        if (action === 'sammeln' && character.inventory.food < 50) {
            reward += 0.25; // Belohne produktives Sammeln
        } else if (action === 'sammeln' && character.inventory.food >= 60) {
            reward -= 0.3; // Bestrafe sinnloses Sammeln bei vollem Inventar
        }
        
        if (action === 'gather_wood' && character.inventory.wood < 40) {
            reward += 0.2; // Belohne Holzsammeln
        }
        
        // PERSÖNLICHKEITS-KONSISTENZ
        if (action === character.preferredAction && Math.random() < 0.7) {
            reward += 0.25; // Belohne Persönlichkeitskonsistenz
        }
        
        // SOZIALE BELOHNUNGEN
        if (action === 'sozialisieren' && character.traits.sozial > 0.7 && envBefore.nearbyCharactersCount > 0) {
            reward += 0.35; // Belohne sozialen Charakter für soziale Interaktion
        }
        
        // UNTÄTIGKEIT BESTRAFEN
        if (action === 'idle' || !action) {
            reward -= 0.4; // Starke Bestrafung für Untätigkeit
        }
        
        // GARANTIERE NICHT-NEUTRALE BELOHNUNGEN
        if (Math.abs(reward) < 0.1) {
            // Basiere minimale Belohnung auf Aktion und Kontext
            if (action === 'essen' || action === 'schlafen') {
                reward = reward >= 0 ? MIN_REWARD : MIN_PENALTY;
            } else if (action === 'sammeln' || action === 'erkunden') {
                reward = character.traits.fleiss > 0.5 ? MIN_REWARD : MIN_PENALTY * 0.7;
            } else if (action === 'idle') {
                reward = MIN_PENALTY * 1.5; // Bestrafe Untätigkeit stärker
            } else {
                reward = Math.random() > 0.5 ? MIN_REWARD : MIN_PENALTY * 0.8;
            }
        }
        
        // Normalisiere und stelle sicher, dass Belohnung signifikant ist
        const finalReward = Math.max(-1, Math.min(1, reward));
        
        // LETZTE SICHERHEIT: Wenn immer noch zu neutral, forciere Richtung
        if (Math.abs(finalReward) < 0.1) {
            return finalReward > 0 ? 0.15 : -0.15;
        }
        
        return finalReward;
    }

    async trainNeuralNetwork(experience) {
        try {
            // Erstelle Trainingsdaten
            const inputData = [
                experience.environmentBefore.hunger,
                experience.environmentBefore.energy,
                experience.environmentBefore.timeOfDay,
                experience.environmentBefore.dayProgress,
                experience.environmentBefore.nearbyCharactersCount / 10,
                experience.environmentBefore.socialDesire,
                experience.environmentBefore.nearbyFood / 10,
                experience.environmentBefore.nearbyMaterials / 10,
                experience.environmentBefore.dangerLevel,
                experience.environmentBefore.happiness,
                experience.environmentBefore.stress,
                experience.environmentBefore.curiosity
            ];
            
            // Target basierend auf Belohnung anpassen
            const actions = ['sammeln', 'erkunden', 'bauen', 'sozialisieren', 'essen', 'schlafen', 'lernen', 'spielen'];
            const actionIndex = actions.indexOf(experience.action);
            
            if (actionIndex !== -1) {
                const target = new Array(actions.length).fill(0);
                target[actionIndex] = Math.max(0.1, Math.min(0.9, 0.5 + experience.reward * 0.5));
                
                const inputTensor = tf.tensor2d([inputData]);
                const targetTensor = tf.tensor2d([target]);
                
                // Training
                await this.decisionNetwork.fit(inputTensor, targetTensor, {
                    epochs: 1,
                    verbose: 0
                });
                
                inputTensor.dispose();
                targetTensor.dispose();
            }
        } catch (error) {
            console.error('Neural network training error:', error);
        }
    }

    // Hilfsmethoden
    findNearbyCharacters(allCharacters, character) {
        return allCharacters.filter(c => {
            if (c === character) return false;
            const dx = c.x - character.x;
            const dy = c.y - character.y;
            return Math.sqrt(dx * dx + dy * dy) < 100;
        });
    }

    findNearbyResources(terrain, character) {
        let food = 0;
        let materials = 0;
        
        terrain.forEach(item => {
            const dx = item.x - character.x;
            const dy = item.y - character.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < 150) {
                if (item.type === 'tree' || item.type === 'bush') {
                    food++;
                }
                if (item.type === 'mountain' || item.type === 'tree') {
                    materials++;
                }
            }
        });
        
        return { food, materials };
    }

    calculateSocialDesire(nearbyCharacters, character) {
        const baseDesire = character.traits.sozial;
        const proximity = Math.min(1, nearbyCharacters.length / 3);
        return baseDesire * (1 - proximity * 0.3); // Weniger Verlangen wenn schon viele in der Nähe
    }

    assessDanger(gameState, character) {
        // Einfache Gefahrenbewertung - kann erweitert werden
        let danger = 0;
        
        if (character.energy < 0.1) danger += 0.3;
        if (character.hunger > 0.9) danger += 0.4;
        
        return Math.min(1, danger);
    }

    updateEmotionalState(environmentData, character, gameState) {
        // Happiness basierend auf Bedürfniserfüllung
        const needsSatisfaction = (1 - environmentData.hunger) * (environmentData.energy);
        this.emotionalState.happiness = this.emotionalState.happiness * 0.9 + needsSatisfaction * 0.1;
        
        // Tag/Nacht-Einfluss auf Emotionen
        const isNight = gameState && gameState.isNight;
        if (isNight) {
            this.emotionalState.stress = Math.min(1, this.emotionalState.stress * 1.1);
            this.emotionalState.curiosity = Math.max(0.1, this.emotionalState.curiosity * 0.95);
        } else {
            this.emotionalState.curiosity = Math.min(0.9, this.emotionalState.curiosity * 1.02);
        }
        
        // Stress basierend auf unerfüllten Bedürfnissen und Gefahr
        const stressFactors = environmentData.hunger + (1 - environmentData.energy) + environmentData.dangerLevel;
        this.emotionalState.stress = this.emotionalState.stress * 0.9 + (stressFactors / 3) * 0.1;
        
        // Soziale Einsamkeit
        if (environmentData.nearbyCharactersCount === 0 && character.traits.sozial > 0.6) {
            this.emotionalState.stress = Math.min(1, this.emotionalState.stress + 0.02);
        }
        
        // Curiosity passt sich an Erfolg und Zeit an
        this.emotionalState.curiosity = Math.max(0.1, Math.min(0.9, 
            this.emotionalState.curiosity + (this.getSuccessRate() - 0.5) * 0.01
        ));
    }

    getSuccessRate() {
        if (this.learningStats.decisionsKnnen === 0) return 0.5;
        return this.learningStats.successfulActions / this.learningStats.decisionsKnnen;
    }

    getLearnedWeights() {
        // Standardgewichte
        const weights = {
            eating: 1.0,
            sleeping: 1.0,
            sammeln: 1.0,
            erkunden: 1.0,
            bauen: 1.0,
            sozialisieren: 1.0,
            lernen: 1.0,
            spielen: 1.0
        };
        
        // Anpassung basierend auf Erfahrungen im Langzeitgedächtnis
        this.longTermMemory.forEach(memory => {
            if (memory.reward > 0.3) {
                weights[memory.action] = Math.min(2.0, weights[memory.action] + 0.1);
            } else if (memory.reward < -0.3) {
                weights[memory.action] = Math.max(0.5, weights[memory.action] - 0.1);
            }
        });
        
        return weights;
    }

    consolidateMemory() {
        // Übertrage wichtige Kurzzeitgedächtnisse ins Langzeitgedächtnis
        const importantMemories = this.shortTermMemory.filter(memory => 
            Math.abs(memory.reward) > 0.3 || Math.random() < 0.1
        );
        
        this.longTermMemory.push(...importantMemories);
        
        // Begrenze Langzeitgedächtnis Größe
        if (this.longTermMemory.length > 100) {
            this.longTermMemory = this.longTermMemory
                .sort((a, b) => Math.abs(b.reward) - Math.abs(a.reward))
                .slice(0, 100);
        }
        
        // Lösche altes Kurzzeitgedächtnis
        this.shortTermMemory = [];
    }

    updateLearningParameters(reward) {
        // VERBESSERTE ADAPTIVE EXPLORATION RATE - reagiert auf neue Belohnungsstruktur
        if (reward > 0.4) {
            // Sehr gute Ergebnisse -> deutlich weniger Exploration
            this.explorationRate = Math.max(0.03, this.explorationRate * 0.95);
        } else if (reward > 0.15) {
            // Gute Ergebnisse -> weniger Exploration
            this.explorationRate = Math.max(0.05, this.explorationRate * 0.98);
        } else if (reward < -0.4) {
            // Sehr schlechte Ergebnisse -> mehr Exploration
            this.explorationRate = Math.min(0.6, this.explorationRate * 1.05);
        } else if (reward < -0.15) {
            // Schlechte Ergebnisse -> etwas mehr Exploration
            this.explorationRate = Math.min(0.5, this.explorationRate * 1.02);
        }
        // Mittlere Belohnungen (-0.15 bis 0.15) lassen Rate unverändert für Stabilität
        
        // DYNAMISCHE LEARNING RATE basierend auf Belohnungsvariation
        const successRate = this.getSuccessRate();
        if (successRate > 0.85) {
            // Sehr erfolgreich -> niedrige Learning Rate für Stabilität
            this.learningRate = Math.max(0.001, this.learningRate * 0.92);
        } else if (successRate > 0.7) {
            // Erfolgreich -> etwas niedrigere Learning Rate
            this.learningRate = Math.max(0.005, this.learningRate * 0.96);
        } else if (successRate < 0.3) {
            // Wenig erfolgreich -> höhere Learning Rate für schnelleres Lernen
            this.learningRate = Math.min(0.08, this.learningRate * 1.08);
        } else if (successRate < 0.5) {
            // Mäßig erfolgreich -> etwas höhere Learning Rate
            this.learningRate = Math.min(0.05, this.learningRate * 1.03);
        }
        
        // EXPLORATION DECAY - verhindert zu viel Exploration bei älteren Charakteren
        if (this.learningStats.decisionsKnnen > 100) {
            this.explorationRate = Math.max(0.02, this.explorationRate * 0.999);
        }
    }

    shouldConsiderLearning(environmentData) {
        // Lerne wenn Curiosity hoch ist und keine dringenden Bedürfnisse bestehen
        return this.emotionalState.curiosity > 0.6 && 
               environmentData.hunger < 0.6 && 
               environmentData.energy > 0.4 &&
               Math.random() < 0.05;
    }

    recordDecision(environmentData, action) {
        // Einfache Entscheidungsaufzeichnung für Regel-basierte AI
        this.memories.push({
            environment: { ...environmentData },
            action,
            timestamp: Date.now()
        });
        
        // Begrenze Memory-Größe
        if (this.memories.length > 50) {
            this.memories.shift();
        }
    }

    storeDecisionForLearning(environmentData, action, inputTensor) {
        // Speichere für späteres Reinforcement Learning (without tensor to avoid memory leaks)
        this.pendingLearning = {
            environmentData,
            action,
            inputTensor: null, // Don't store tensor to prevent memory leaks
            timestamp: Date.now()
        };
    }

    // Simple learn method for game compatibility
    learn(action, result) {
        try {
            // Simple learning without complex tensor operations to prevent loops
            if (result === 'success') {
                this.learningStats.successfulActions++;
            } else {
                this.learningStats.failedActions++;
            }
            this.learningStats.decisionsKnnen++;
            
            // Update exploration rate based on success
            if (result === 'success') {
                this.explorationRate = Math.max(0.05, this.explorationRate * 0.99);
            } else {
                this.explorationRate = Math.min(0.6, this.explorationRate * 1.01);
            }
            
            // Reduced logging to prevent spam
            if (Math.random() < 0.1) { // Only log 10% of learning events
                console.log(`📚 ${this.personality?.name} learned: ${action} → ${result}`);
            }
            
        } catch (error) {
            console.warn(`Learning error for ${this.personality?.name}:`, error.message);
        }
    }

    // Neue Methode: Überdenke vorherige Entscheidungen
    reflectOnPreviousActions() {
        if (this.shortTermMemory.length < 3) return;
        
        // Analysiere letzte 3 Aktionen
        const recentActions = this.shortTermMemory.slice(-3);
        const avgReward = recentActions.reduce((sum, mem) => sum + mem.reward, 0) / recentActions.length;
        
        // Lerne aus Mustern - REDUZIERTES LOGGING
        if (avgReward < -0.2) {
            // Logge nur gelegentlich oder bei extremen Fällen
            if (Math.random() < 0.3 || avgReward < -0.5) {
                console.log(`🤔 ${this.personality.name} reflects: Recent actions unsuccessful, increasing exploration`);
            }
            this.explorationRate = Math.min(0.8, this.explorationRate * 1.1);
        } else if (avgReward > 0.3) {
            // Logge nur gelegentlich oder bei sehr guten Ergebnissen
            if (Math.random() < 0.3 || avgReward > 0.6) {
                console.log(`😊 ${this.personality.name} reflects: Recent actions successful, continuing strategy`);
            }
            this.explorationRate = Math.max(0.05, this.explorationRate * 0.95);
        }
    }
    
    // Verbesserte regelbasierte Entscheidung mit Kontext
    intelligentRuleBasedDecision(environmentData, character, gameState) {
        const decisions = [];
        const timeOfDay = gameState.gameTime / 60; // Stunden
        const isNight = gameState.isNight;
        
        // KRITISCHE BEDÜRFNISSE HABEN ABSOLUTE PRIORITÄT
        if (environmentData.energy < 0.25) {
            console.log(`💤 ${character.name} KRITISCH MÜDE - forciert Schlaf`);
            return 'schlafen';
        }
        
        if (environmentData.hunger > 0.85) {
            console.log(`🍽️ ${character.name} KRITISCH HUNGRIG - forciert Essen`);
            return 'essen';
        }
        
        // Intelligente Prioritätensberechnung
        const learnedWeights = this.getLearnedWeights();
        
        // Energie-bewusste Entscheidungen
        if (environmentData.energy < 0.5) {
            decisions.push({ 
                action: 'schlafen', 
                priority: (1 - environmentData.energy) * 120,
                reason: 'Niedrige Energie'
            });
        }
        
        // Hunger-bewusste Entscheidungen  
        if (environmentData.hunger > 0.6) {
            decisions.push({ 
                action: 'essen', 
                priority: environmentData.hunger * 100,
                reason: 'Hunger steigt'
            });
        }
        
        // Tag/Nacht-abhängige Aktivitäten
        if (isNight) {
            // Nachts bevorzugt schlafen
            if (environmentData.energy < 0.7) {
                decisions.push({ 
                    action: 'schlafen', 
                    priority: 80,
                    reason: 'Nachtzeit - natürlicher Schlafzyklus'
                });
            }
        } else {
            // Tags aktiver sein
            if (Math.random() < character.traits.neugier * 0.03) {
                decisions.push({ 
                    action: 'erkunden', 
                    priority: 35 * learnedWeights.erkunden || 35,
                    reason: 'Tageslicht - Exploration'
                });
            }
            
            if (Math.random() < character.traits.fleiss * 0.02) {
                decisions.push({ 
                    action: 'sammeln', 
                    priority: 30 * learnedWeights.sammeln || 30,
                    reason: 'Tageslicht - produktive Arbeit'
                });
            }
        }
        
        // Soziale Interaktion
        if (environmentData.socialDesire > 0.4 && environmentData.nearbyCharactersCount > 0) {
            const socialBonus = this.emotionalState.happiness > 0.6 ? 1.3 : 0.9;
            decisions.push({ 
                action: 'sozialisieren', 
                priority: environmentData.socialDesire * 45 * socialBonus,
                reason: 'Soziales Bedürfnis + andere in der Nähe'
            });
        }
        
        // Lager-Management Logik
        const warehouse = this.getWarehouse();
        if (warehouse) {
            if (!warehouse.completed) {
                // Lager bauen
                if (character.inventory.wood > 0 && warehouse.stackedWood < warehouse.requiredWood) {
                    decisions.push({ 
                        action: 'deliver_warehouse_wood', 
                        priority: 60,
                        reason: 'Lager braucht Holz zum Bauen'
                    });
                } else if (warehouse.stackedWood < warehouse.requiredWood) {
                    decisions.push({ 
                        action: 'gather_wood', 
                        priority: 50,
                        reason: 'Holz für Lager sammeln'
                    });
                } else {
                    decisions.push({ 
                        action: 'build_warehouse', 
                        priority: 65,
                        reason: 'Lager fertigstellen'
                    });
                }
            } else if (warehouse.completed) {
                // Intelligente Lager-Nutzung
                if (character.inventory.wood > 15 && warehouse.storage.wood < warehouse.capacity.wood * 0.8) {
                    decisions.push({ 
                        action: 'store_wood', 
                        priority: 35,
                        reason: 'Überschüssiges Holz einlagern'
                    });
                }
                
                if (character.inventory.food > 10 && warehouse.storage.food < warehouse.capacity.food * 0.8) {
                    decisions.push({ 
                        action: 'store_food', 
                        priority: 40,
                        reason: 'Überschüssige Nahrung einlagern'
                    });
                }
                
                // Aus Lager holen wenn eigenes Inventar niedrig
                if (character.inventory.wood < 3 && warehouse.storage.wood > 10) {
                    decisions.push({ 
                        action: 'retrieve_wood', 
                        priority: 45,
                        reason: 'Holz aus Lager holen'
                    });
                }
                
                if (character.inventory.food < 2 && warehouse.storage.food > 5) {
                    decisions.push({ 
                        action: 'retrieve_food', 
                        priority: 55,
                        reason: 'Nahrung aus Lager holen'
                    });
                }
            }
        } else {
            // Lager existiert noch nicht - bauen vorschlagen
            if (environmentData.nearbyCharactersCount > 1 && Math.random() < 0.05) {
                decisions.push({ 
                    action: 'build_warehouse', 
                    priority: 20,
                    reason: 'Gemeinsames Lager wäre nützlich'
                });
            }
        }

        // Persönlichkeitsbasierte Präferenzen
        const preference = character.preferredAction;
        if (preference && Math.random() < 0.2) {
            decisions.push({ 
                action: preference, 
                priority: 25 * learnedWeights[preference] || 25,
                reason: 'Persönlichkeitspräferenz'
            });
        }
        
        // ZWECKORIENTIERTE GRUPPENAKTIVITÄTEN - verhindert sinnloses Herumirren
        this.considerPurposefulActivities(decisions, environmentData, character, gameState);
        
        // POST-HOUSING ENTWICKLUNG - was tun nach Grundversorgung?
        this.considerAdvancedDevelopment(decisions, environmentData, character, gameState);
        
        // Wähle beste Entscheidung oder fallback
        if (decisions.length > 0) {
            const bestDecision = decisions.reduce((a, b) => a.priority > b.priority ? a : b);
            console.log(`🧠 ${character.name} wählt ${bestDecision.action}: ${bestDecision.reason} (Priorität: ${bestDecision.priority.toFixed(1)})`);
            this.recordDecision(environmentData, bestDecision.action);
            return bestDecision.action;
        }
        
        // Fallback: Wenn keine Entscheidung, dann sammeln (produktiv)
        console.log(`🤷 ${character.name} keine klare Entscheidung - sammelt Ressourcen`);
        return 'sammeln';
    }
    
    // ZWECKORIENTIERTE AKTIVITÄTEN - Charaktere sollen sinnvolle Dinge tun
    considerPurposefulActivities(decisions, environmentData, character, gameState) {
        // Sozialisierung mit anderen Charakteren suchen
        if (environmentData.nearbyCharactersCount > 0) {
            decisions.push({
                action: 'sozialisieren',
                priority: 30,
                reason: 'Soziale Interaktion mit anderen'
            });
        } else if (environmentData.nearbyCharactersCount === 0 && character.traits.sozial > 0.6) {
            decisions.push({
                action: 'seek_conversation',
                priority: 35,
                reason: 'Andere Charaktere für Gespräche suchen'
            });
        }
        
        // Gruppenbauprojekte initiieren
        const allCharacters = window.gameInstance?.characters || [];
        const nearbyCharacters = allCharacters.filter(c => 
            c !== character && 
            Math.sqrt(Math.pow(c.x - character.x, 2) + Math.pow(c.y - character.y, 2)) < 150
        );
        
        if (nearbyCharacters.length >= 2 && Math.random() < 0.1) {
            decisions.push({
                action: 'propose_group_project',
                priority: 40,
                reason: 'Gruppenprojekt vorschlagen'
            });
        }
        
        // Dorfverbesserungen planen
        if (character.traits.fleiss > 0.6 && Math.random() < 0.05) {
            decisions.push({
                action: 'plan_village_improvement',
                priority: 25,
                reason: 'Dorfentwicklung planen'
            });
        }
        
        // Wissensaustausch
        if (character.traits.neugier > 0.7 && nearbyCharacters.length > 0) {
            decisions.push({
                action: 'share_knowledge',
                priority: 20,
                reason: 'Wissen mit anderen teilen'
            });
        }
        
        // Gemeinsame Ressourcenplanung
        if (environmentData.nearbyCharactersCount >= 2) {
            decisions.push({
                action: 'discuss_resources',
                priority: 28,
                reason: 'Ressourcenverteilung besprechen'
            });
        }
        
        // Existenzielle Reflexionen (weniger häufig, aber tiefgreifend)
        if (character.consciousness && character.consciousness.awarenessLevel > 0.5 && Math.random() < 0.02) {
            decisions.push({
                action: 'contemplate_existence',
                priority: 15,
                reason: 'Über Existenz und Sinn nachdenken'
            });
        }
        
        // Langfristige Ziele entwickeln
        if (environmentData.hunger < 0.4 && environmentData.energy > 0.6 && Math.random() < 0.03) {
            decisions.push({
                action: 'develop_long_term_goals',
                priority: 22,
                reason: 'Langfristige Lebensziele entwickeln'
            });
        }
        
        // Mentor-Rolle übernehmen für jüngere Charaktere
        const youngerCharacters = allCharacters.filter(c => 
            c.age && character.age && c.age < character.age - 5 &&
            Math.sqrt(Math.pow(c.x - character.x, 2) + Math.pow(c.y - character.y, 2)) < 100
        );
        
        if (youngerCharacters.length > 0 && character.age > 25) {
            decisions.push({
                action: 'mentor_others',
                priority: 18,
                reason: 'Jüngere Charaktere mentorieren'
            });
        }
    }
    
    // POST-HOUSING ENTWICKLUNG - Aktivitäten nach Grundversorgung
    considerAdvancedDevelopment(decisions, environmentData, character, gameState) {
        const gameInstance = window.gameInstance;
        if (!gameInstance) return;
        
        // Zähle vorhandene Strukturen
        const houses = gameInstance.structures?.filter(s => (s.type === 'house' || s.type === 'hut') && s.completed) || [];
        const warehouses = gameInstance.structures?.filter(s => s.type === 'warehouse' && s.completed) || [];
        const characterCount = gameInstance.characters?.length || 0;
        
        // Grundversorgung erfüllt? (Alle haben Häuser)
        const basicNeedsMet = houses.length >= characterCount;
        
        if (basicNeedsMet) {
            // DORF-INFRASTRUKTUR PROJEKTE
            this.considerInfrastructureProjects(decisions, character, gameInstance);
            
            // KULTURELLE AKTIVITÄTEN
            this.considerCulturalActivities(decisions, environmentData, character);
            
            // SPEZIALISIERUNG UND HANDWERK
            this.considerSkillSpecialization(decisions, character);
            
            // FORSCHUNG UND ENTWICKLUNG
            this.considerResearchActivities(decisions, environmentData, character);
        }
    }
    
    considerInfrastructureProjects(decisions, character, gameInstance) {
        // Marktplatz/Zentrum bauen
        const hasMarketplace = gameInstance.structures?.some(s => s.type === 'marketplace');
        if (!hasMarketplace && Math.random() < 0.1) {
            decisions.push({
                action: 'build_marketplace',
                priority: 45,
                reason: 'Marktplatz für Dorfzentrum bauen'
            });
        }
        
        // Straßen und Wege anlegen
        if (Math.random() < 0.05) {
            decisions.push({
                action: 'build_roads',
                priority: 30,
                reason: 'Wege zwischen Häusern anlegen'
            });
        }
        
        // Brunnen/Wassersystem
        const hasWell = gameInstance.structures?.some(s => s.type === 'well');
        if (!hasWell && Math.random() < 0.08) {
            decisions.push({
                action: 'build_well',
                priority: 40,
                reason: 'Zentralen Brunnen bauen'
            });
        }
        
        // Werkstätten für Handwerk
        const hasWorkshop = gameInstance.structures?.some(s => s.type === 'workshop');
        if (!hasWorkshop && character.traits.fleiss > 0.7 && Math.random() < 0.06) {
            decisions.push({
                action: 'build_workshop',
                priority: 35,
                reason: 'Werkstatt für Handwerk errichten'
            });
        }
        
        // Gemeinschaftshaus/Versammlungsort
        const hasCommunityHall = gameInstance.structures?.some(s => s.type === 'community_hall');
        if (!hasCommunityHall && Math.random() < 0.04) {
            decisions.push({
                action: 'build_community_hall',
                priority: 38,
                reason: 'Gemeinschaftshaus für Versammlungen'
            });
        }
    }
    
    considerCulturalActivities(decisions, environmentData, character) {
        // Geschichten erzählen
        if (character.traits.sozial > 0.6 && environmentData.nearbyCharactersCount > 1) {
            decisions.push({
                action: 'tell_stories',
                priority: 25,
                reason: 'Geschichten und Legenden erzählen'
            });
        }
        
        // Feste und Feiern organisieren
        if (Math.random() < 0.02) {
            decisions.push({
                action: 'organize_festival',
                priority: 20,
                reason: 'Dorffest oder Feier organisieren'
            });
        }
        
        // Kunst und Dekoration
        if (character.traits.neugier > 0.7 && Math.random() < 0.03) {
            decisions.push({
                action: 'create_art',
                priority: 15,
                reason: 'Kunstwerke oder Dekoration schaffen'
            });
        }
        
        // Musik und Gesang
        if (character.traits.sozial > 0.8 && Math.random() < 0.025) {
            decisions.push({
                action: 'make_music',
                priority: 18,
                reason: 'Musik machen oder singen'
            });
        }
        
        // Spiele und Wettkämpfe
        if (environmentData.nearbyCharactersCount >= 2 && Math.random() < 0.04) {
            decisions.push({
                action: 'organize_games',
                priority: 22,
                reason: 'Spiele oder Wettkämpfe veranstalten'
            });
        }
    }
    
    considerSkillSpecialization(decisions, character) {
        // Jeder Charakter kann sich spezialisieren
        const possibleSpecializations = ['builder', 'farmer', 'crafter', 'healer', 'teacher', 'trader'];
        
        if (!character.specialization && character.age > 20) {
            // Wähle Spezialisierung basierend auf Persönlichkeit
            let preferredSpec = null;
            if (character.traits.fleiss > 0.8) preferredSpec = 'builder';
            else if (character.traits.neugier > 0.8) preferredSpec = 'teacher';
            else if (character.traits.sozial > 0.8) preferredSpec = 'healer';
            else preferredSpec = possibleSpecializations[Math.floor(Math.random() * possibleSpecializations.length)];
            
            if (Math.random() < 0.1) {
                decisions.push({
                    action: 'develop_specialization',
                    priority: 28,
                    reason: `Spezialisierung als ${preferredSpec} entwickeln`,
                    targetSpecialization: preferredSpec
                });
            }
        }
        
        // Fähigkeiten durch Spezialisierung
        if (character.specialization) {
            const specActions = {
                builder: 'advanced_construction',
                farmer: 'advanced_farming', 
                crafter: 'craft_tools',
                healer: 'help_others',
                teacher: 'teach_skills',
                trader: 'organize_trade'
            };
            
            const specAction = specActions[character.specialization];
            if (specAction && Math.random() < 0.15) {
                decisions.push({
                    action: specAction,
                    priority: 32,
                    reason: `Spezialisierte ${character.specialization} Aktivität`
                });
            }
        }
    }
    
    considerResearchActivities(decisions, environmentData, character) {
        // Neue Technologien erforschen
        if (character.traits.neugier > 0.8 && environmentData.energy > 0.6) {
            const researchTopics = [
                'better_tools', 'improved_farming', 'medicine_knowledge', 
                'construction_techniques', 'food_preservation', 'water_management'
            ];
            
            if (Math.random() < 0.05) {
                const topic = researchTopics[Math.floor(Math.random() * researchTopics.length)];
                decisions.push({
                    action: 'research_technology',
                    priority: 24,
                    reason: `Forschung: ${topic}`,
                    researchTopic: topic
                });
            }
        }
        
        // Umgebung erkunden für neue Ressourcen
        if (character.traits.neugier > 0.6 && Math.random() < 0.08) {
            decisions.push({
                action: 'explore_for_resources',
                priority: 26,
                reason: 'Neue Ressourcenquellen erforschen'
            });
        }
        
        // Wetter und Natur beobachten
        if (character.traits.neugier > 0.7 && Math.random() < 0.03) {
            decisions.push({
                action: 'observe_nature',
                priority: 12,
                reason: 'Natur und Wettermuster studieren'
            });
        }
    }
    
    shouldConsiderDeepThinking(environmentData, timeOfDay) {
        // Denken bevorzugt in ruhigen Momenten
        return this.emotionalState.curiosity > 0.6 && 
               environmentData.hunger < 0.5 && 
               environmentData.energy > 0.5 &&
               environmentData.nearbyCharactersCount < 2 &&
               (timeOfDay < 8 || (timeOfDay > 14 && timeOfDay < 18)) && // Morgen oder Nachmittag
               Math.random() < 0.08;
    }
    
    getWarehouse() {
        // Helper-Funktion um Lager zu finden
        return window.gameInstance?.structures?.find(s => s.type === 'warehouse') || null;
    }

    // Debugging und Monitoring
    getAIStats() {
        return {
            personality: this.personality.name,
            learningStats: this.learningStats,
            emotionalState: this.emotionalState,
            memoryStats: {
                shortTerm: this.shortTermMemory.length,
                longTerm: this.longTermMemory.length,
                episodic: this.episodicMemory.length
            },
            neuralNetwork: this.useNeuralNetwork,
            explorationRate: this.explorationRate,
            learningRate: this.learningRate,
            successRate: this.getSuccessRate()
        };
    }
}

// Export für Browser-Umgebung
if (typeof window !== 'undefined') {
    window.AIBrain = AIBrain;
}
