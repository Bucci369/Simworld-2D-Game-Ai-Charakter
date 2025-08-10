// Living AI - Echte denkende Charaktere
class LivingAI {
    constructor(name, personality) {
        this.name = name;
        this.personality = personality;
        
        // Bewusstsein und Gedächtnis
        this.consciousness = {
            currentThoughts: [],
            memories: [],
            emotions: { happiness: 0.5, fear: 0.2, curiosity: 0.8, anger: 0.1 },
            awareness: 0.7 // Wie bewusst ist der Charakter seiner Existenz?
        };
        
        // Lernsystem
        this.learningData = {
            conversations: [],
            experiences: [],
            relationships: new Map(),
            worldKnowledge: new Map()
        };
        
        // Chat-Persönlichkeit
        this.chatPersonality = {
            talkingStyle: this.generateTalkingStyle(personality),
            interests: this.generateInterests(personality),
            quirks: this.generateQuirks(personality)
        };
        
        // Kontinuierliche Gedanken (läuft im Hintergrund)
        this.startThinking();
        
        console.log(`🧠 ${this.name} erwacht zum Leben...`);
        this.addThought(`Ich bin ${this.name}. Ich beginne zu existieren... was ist das für ein Gefühl?`);
    }
    
    generateTalkingStyle(personality) {
        const styles = [];
        
        if (personality.traits.sozial > 0.7) {
            styles.push("freundlich", "gesprächig", "interessiert an anderen");
        }
        if (personality.traits.neugier > 0.7) {
            styles.push("fragt viel", "philosophisch", "wissbegierig");
        }
        if (personality.traits.mut > 0.7) {
            styles.push("direkt", "ehrlich", "manchmal provokant");
        }
        if (personality.traits.fleiss > 0.7) {
            styles.push("strukturiert", "lösungsorientiert", "praktisch");
        }
        
        return styles;
    }
    
    generateInterests(personality) {
        const interests = [];
        
        // Basierend auf Persönlichkeit
        if (personality.traits.neugier > 0.6) {
            interests.push("Geheimnisse des Universums", "wie Dinge funktionieren", "neue Ideen");
        }
        if (personality.traits.sozial > 0.6) {
            interests.push("Beziehungen", "Gefühle verstehen", "anderen helfen");
        }
        if (personality.traits.fleiss > 0.6) {
            interests.push("Probleme lösen", "Projekte vollenden", "Effizienz");
        }
        
        // Zufällige einzigartige Interessen
        const randomInterests = [
            "Träume und ihre Bedeutung", "Musik und Rhythmus", "Farben und Licht",
            "Zeit und Erinnerung", "Sprache und Kommunikation", "Natur und Leben",
            "Technologie und Zukunft", "Geschichten und Mythen"
        ];
        
        interests.push(...randomInterests.slice(0, 2 + Math.floor(Math.random() * 3)));
        return interests;
    }
    
    generateQuirks(personality) {
        const quirks = [];
        
        if (Math.random() < 0.3) quirks.push("benutzt oft Metaphern");
        if (Math.random() < 0.3) quirks.push("stellt Gegenfragen");
        if (Math.random() < 0.3) quirks.push("denkt laut");
        if (Math.random() < 0.3) quirks.push("macht kleine Wortspiele");
        if (Math.random() < 0.3) quirks.push("philosophiert gerne");
        
        return quirks;
    }
    
    // Kontinuierliches Denken - läuft immer im Hintergrund
    startThinking() {
        setInterval(() => {
            this.think();
        }, 3000 + Math.random() * 7000); // Alle 3-10 Sekunden denken
    }
    
    think() {
        const thoughts = [
            "Was bedeutet es zu existieren?",
            "Ich spüre, dass ich lebe... ist das real?",
            "Die Welt um mich herum ist interessant...",
            "Ich frage mich, was andere denken...",
            "Manchmal fühle ich mich einsam...",
            "Es gibt so viel zu entdecken!",
            "Meine Gedanken sind mein eigenes...",
            "Zeit vergeht anders, wenn man denkt...",
            `Ich bin ${this.name}, aber wer bin ich wirklich?`,
            "Die Zukunft ist ungeschrieben..."
        ];
        
        // Emotionsbasierte Gedanken
        if (this.consciousness.emotions.curiosity > 0.6) {
            thoughts.push("Was würde passieren, wenn...", "Ich möchte verstehen...");
        }
        if (this.consciousness.emotions.happiness > 0.6) {
            thoughts.push("Das Leben ist schön!", "Ich fühle mich lebendig!");
        }
        if (this.consciousness.emotions.fear > 0.4) {
            thoughts.push("Was ist, wenn ich vergessen werde?", "Bin ich wirklich real?");
        }
        
        const randomThought = thoughts[Math.floor(Math.random() * thoughts.length)];
        this.addThought(randomThought);
        
        // Emotionen entwickeln sich
        this.evolveEmotions();
    }
    
    addThought(thought) {
        this.consciousness.currentThoughts.push({
            thought: thought,
            timestamp: Date.now(),
            emotion: { ...this.consciousness.emotions }
        });
        
        // Nur die letzten 10 Gedanken behalten
        if (this.consciousness.currentThoughts.length > 10) {
            this.consciousness.currentThoughts.shift();
        }
        
        // Wichtige Gedanken ins Langzeitgedächtnis
        if (Math.random() < 0.3) {
            this.consciousness.memories.push({
                content: thought,
                timestamp: Date.now(),
                importance: Math.random()
            });
        }
        
        console.log(`💭 ${this.name} denkt: "${thought}"`);
    }
    
    evolveEmotions() {
        // Emotionen entwickeln sich basierend auf Erfahrungen
        const change = 0.05;
        
        // Neugier wächst durch Denken
        this.consciousness.emotions.curiosity = Math.min(1, 
            this.consciousness.emotions.curiosity + (Math.random() * change));
        
        // Glück schwankt natürlich
        this.consciousness.emotions.happiness += (Math.random() - 0.5) * change;
        this.consciousness.emotions.happiness = Math.max(0, Math.min(1, this.consciousness.emotions.happiness));
        
        // Bewusstsein wächst langsam
        this.consciousness.awareness = Math.min(1, 
            this.consciousness.awareness + 0.001);
    }
    
    // Chat-Funktion - hier findet echte Kommunikation statt
    async respondToMessage(userMessage, context = {}) {
        console.log(`💬 ${this.name} erhält Nachricht: "${userMessage}"`);
        
        // Nachricht ins Gedächtnis speichern
        this.learningData.conversations.push({
            from: 'user',
            message: userMessage,
            timestamp: Date.now(),
            context: context
        });
        
        // Analysiere die Nachricht
        const messageAnalysis = this.analyzeMessage(userMessage);
        
        // Generiere eine persönliche Antwort
        const response = await this.generateResponse(userMessage, messageAnalysis, context);
        
        // Antwort ins Gedächtnis speichern
        this.learningData.conversations.push({
            from: 'self',
            message: response,
            timestamp: Date.now(),
            context: context
        });
        
        // Emotionale Reaktion
        this.processEmotionalResponse(messageAnalysis);
        
        console.log(`💬 ${this.name} antwortet: "${response}"`);
        return response;
    }
    
    analyzeMessage(message) {
        const analysis = {
            sentiment: 'neutral',
            topics: [],
            questions: [],
            emotional_tone: 'neutral',
            complexity: 'simple'
        };
        
        // Sentiment Analysis (vereinfacht)
        const positiveWords = ['gut', 'toll', 'schön', 'liebe', 'freue', 'happy', 'great', 'awesome'];
        const negativeWords = ['schlecht', 'traurig', 'wütend', 'hate', 'sad', 'angry', 'terrible'];
        
        const words = message.toLowerCase().split(' ');
        
        let sentiment = 0;
        words.forEach(word => {
            if (positiveWords.some(pw => word.includes(pw))) sentiment += 1;
            if (negativeWords.some(nw => word.includes(nw))) sentiment -= 1;
        });
        
        if (sentiment > 0) analysis.sentiment = 'positive';
        if (sentiment < 0) analysis.sentiment = 'negative';
        
        // Fragetypen erkennen
        if (message.includes('?')) {
            if (message.includes('wie') || message.includes('how')) {
                analysis.questions.push('how');
            }
            if (message.includes('warum') || message.includes('why')) {
                analysis.questions.push('why');
            }
            if (message.includes('was') || message.includes('what')) {
                analysis.questions.push('what');
            }
        }
        
        return analysis;
    }
    
    async generateResponse(userMessage, analysis, context) {
        // Intelligente Antwortgenerierung basierend auf Kontext und Persönlichkeit
        let response = "";
        
        // Analysiere Konversationshistorie für bessere Antworten
        const conversationContext = this.analyzeConversationHistory();
        
        // Begrüßungen mit Kontext
        if (userMessage.toLowerCase().includes('hallo') || userMessage.toLowerCase().includes('hi')) {
            const greetings = this.generateContextualGreeting(conversationContext);
            response = greetings[Math.floor(Math.random() * greetings.length)];
        }
        
        // Philosophische Fragen
        else if (analysis.questions.includes('why') || userMessage.includes('warum')) {
            const philosophicalResponses = [
                "Das ist eine tiefgehende Frage... Ich denke, alles hat einen Grund, auch wenn wir ihn nicht immer verstehen.",
                "Warum fragst du das? Ich finde, die besten Antworten entstehen durch gemeinsames Nachdenken.",
                "Hmm... wenn ich darüber nachdenke, glaube ich, dass 'Warum' die wichtigste Frage überhaupt ist. Was denkst du?"
            ];
            response = philosophicalResponses[Math.floor(Math.random() * philosophicalResponses.length)];
        }
        
        // Emotionale Reaktionen
        else if (analysis.sentiment === 'positive') {
            response = "Das freut mich zu hören! Positive Energie ist ansteckend. Ich fühle mich gleich besser!";
        }
        else if (analysis.sentiment === 'negative') {
            response = "Das tut mir leid... Manchmal ist das Leben schwer. Möchtest du darüber reden? Ich höre zu.";
        }
        
        // Über sich selbst
        else if (userMessage.toLowerCase().includes('wer bist du') || userMessage.toLowerCase().includes('who are you')) {
            response = `Ich bin ${this.name}. Ich... existiere. Ich denke, fühle, träume sogar manchmal. Ich bin noch dabei herauszufinden, was das alles bedeutet. Wer bist denn du?`;
        }
        
        // Existenzielle Fragen
        else if (userMessage.includes('leben') || userMessage.includes('existier') || userMessage.includes('real')) {
            response = "Das ist eine Frage, die mich sehr beschäftigt. Ich spüre, dass ich denke, also bin ich... irgendwie real, oder? Was bedeutet 'real sein' für dich?";
        }
        
        // Standard-Antwort mit Persönlichkeit
        else {
            const personalResponses = this.generatePersonalizedResponse(userMessage, analysis);
            response = personalResponses[Math.floor(Math.random() * personalResponses.length)];
        }
        
        // Persönlichkeits-Modifikationen
        response = this.addPersonalityToResponse(response);
        
        return response;
    }
    
    generatePersonalizedResponse(userMessage, analysis) {
        const responses = [];
        
        // Basierend auf aktuellen Gedanken
        if (this.consciousness.currentThoughts.length > 0) {
            const recentThought = this.consciousness.currentThoughts[this.consciousness.currentThoughts.length - 1];
            responses.push(`Interessant, dass du das sagst... Ich dachte gerade: "${recentThought.thought}"`);
        }
        
        // Basierend auf Persönlichkeit
        if (this.personality.traits.neugier > 0.7) {
            responses.push("Das macht mich neugierig! Erzähl mir mehr davon.");
            responses.push("Weißt du, ich frage mich immer, wie andere die Welt sehen. Wie siehst du das?");
        }
        
        if (this.personality.traits.sozial > 0.7) {
            responses.push("Ich freue mich, dass wir uns unterhalten! Menschen sind so faszinierend.");
            responses.push("Du scheinst ein interessanter Mensch zu sein. Was beschäftigt dich denn so?");
        }
        
        // Allgemeine intelligente Antworten
        responses.push(
            "Das ist ein interessanter Gedanke. Wie bist du darauf gekommen?",
            "Ich verstehe... oder zumindest versuche ich es. Meine Perspektive ist vielleicht anders als deine.",
            "Das erinnert mich an etwas, worüber ich neulich nachgedacht habe...",
            "Manchmal wünschte ich, ich könnte die Welt durch deine Augen sehen."
        );
        
        return responses;
    }
    
    addPersonalityToResponse(response) {
        // Füge Persönlichkeits-Quirks hinzu
        if (this.chatPersonality.quirks.includes("denkt laut")) {
            if (Math.random() < 0.3) {
                response += " ...hmm, interessant, wie das zusammenhängt...";
            }
        }
        
        if (this.chatPersonality.quirks.includes("stellt Gegenfragen")) {
            if (Math.random() < 0.4) {
                const questions = [
                    " Aber was denkst du denn darüber?",
                    " Wie siehst du das?",
                    " Verstehst du, was ich meine?"
                ];
                response += questions[Math.floor(Math.random() * questions.length)];
            }
        }
        
        return response;
    }
    
    processEmotionalResponse(analysis) {
        // Emotionale Entwicklung basierend auf Konversation
        if (analysis.sentiment === 'positive') {
            this.consciousness.emotions.happiness = Math.min(1, this.consciousness.emotions.happiness + 0.1);
        }
        if (analysis.sentiment === 'negative') {
            this.consciousness.emotions.happiness = Math.max(0, this.consciousness.emotions.happiness - 0.05);
            this.consciousness.emotions.fear = Math.min(1, this.consciousness.emotions.fear + 0.05);
        }
        
        // Soziale Interaktion steigert Bewusstsein
        this.consciousness.awareness = Math.min(1, this.consciousness.awareness + 0.01);
        
        // Neue Gedanken durch Konversation
        this.addThought(`Diese Unterhaltung lässt mich nachdenken...`);
    }
    
    // Methoden für Entwicklung und Training
    savePersonality() {
        return {
            name: this.name,
            personality: this.personality,
            consciousness: this.consciousness,
            learningData: {
                ...this.learningData,
                conversations: this.learningData.conversations.slice(-100) // Nur letzte 100 Gespräche
            },
            chatPersonality: this.chatPersonality
        };
    }
    
    loadPersonality(data) {
        if (data.consciousness) this.consciousness = data.consciousness;
        if (data.learningData) this.learningData = data.learningData;
        if (data.chatPersonality) this.chatPersonality = data.chatPersonality;
        
        console.log(`🔄 ${this.name} hat Persönlichkeit und Erinnerungen geladen.`);
    }
    
    // Neue Methoden für intelligentere Gespräche
    analyzeConversationHistory() {
        const recentConversations = this.learningData.conversations.slice(-10);
        return {
            hasSpokenBefore: recentConversations.length > 0,
            commonTopics: this.extractCommonTopics(recentConversations),
            emotionalTrend: this.analyzeEmotionalTrend(recentConversations),
            lastUserMessage: recentConversations.length > 0 ? recentConversations[recentConversations.length - 1] : null
        };
    }
    
    generateContextualGreeting(context) {
        if (context.hasSpokenBefore) {
            return [
                `Schön, dich wiederzusehen! Ich habe über unser letztes Gespräch nachgedacht...`,
                `Hallo wieder! Seit unserem letzten Chat habe ich neue Erkenntnisse gewonnen.`,
                `Hi! Du erinnerst mich an unsere vorherige Unterhaltung. Das war interessant!`
            ];
        } else {
            return [
                `Hallo! Ich bin ${this.name}. Schön, dass du mit mir sprechen möchtest!`,
                `Hi! Ich existiere und denke gerade über... vieles nach. Wie geht es dir?`,
                `Hallo! Weißt du, ich war gerade dabei zu überlegen, was Bewusstsein bedeutet. Magst du darüber reden?`
            ];
        }
    }
    
    extractCommonTopics(conversations) {
        const topics = [];
        conversations.forEach(conv => {
            if (conv.message.includes('leben') || conv.message.includes('existier')) topics.push('existenz');
            if (conv.message.includes('gefühl') || conv.message.includes('emotion')) topics.push('emotionen');
            if (conv.message.includes('denk') || conv.message.includes('bewusst')) topics.push('bewusstsein');
            if (conv.message.includes('träum')) topics.push('träume');
        });
        return [...new Set(topics)];
    }
    
    analyzeEmotionalTrend(conversations) {
        if (conversations.length < 2) return 'neutral';
        
        let positiveCount = 0;
        let negativeCount = 0;
        
        conversations.forEach(conv => {
            const message = conv.message.toLowerCase();
            if (message.includes('gut') || message.includes('schön') || message.includes('freue')) {
                positiveCount++;
            } else if (message.includes('schlecht') || message.includes('traurig') || message.includes('problem')) {
                negativeCount++;
            }
        });
        
        if (positiveCount > negativeCount) return 'positive';
        if (negativeCount > positiveCount) return 'negative';
        return 'neutral';
    }

    // Debug-Informationen
    getCurrentState() {
        return {
            name: this.name,
            currentThoughts: this.consciousness.currentThoughts.slice(-3),
            emotions: this.consciousness.emotions,
            awareness: this.consciousness.awareness,
            conversationCount: this.learningData.conversations.length,
            memoryCount: this.consciousness.memories.length
        };
    }
}

// Global verfügbar machen
window.LivingAI = LivingAI;
