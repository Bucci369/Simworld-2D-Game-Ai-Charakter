/**
 * AI Monitoring Dashboard
 * Zeigt Lernfortschritt und AI-Statistiken der Charaktere an
 */

class AIMonitoringDashboard {
    constructor() {
        this.isVisible = false;
        this.updateInterval = null;
        this.createDashboard();
        this.setupEventListeners();
    }

    createDashboard() {
        // Hauptcontainer
        this.dashboard = document.createElement('div');
        this.dashboard.id = 'aiDashboard';
        this.dashboard.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 400px;
            max-height: 80vh;
            background: rgba(0, 0, 0, 0.9);
            border: 2px solid #4a90e2;
            border-radius: 15px;
            color: white;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            z-index: 10000;
            display: none;
            overflow-y: auto;
            backdrop-filter: blur(10px);
        `;

        // Header
        const header = document.createElement('div');
        header.style.cssText = `
            padding: 15px;
            background: linear-gradient(45deg, #4a90e2, #50C878);
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        `;
        header.innerHTML = `
            <span style="font-weight: bold; font-size: 14px;">🧠 AI Learning Dashboard</span>
            <button id="closeDashboard" style="
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                cursor: pointer;
            ">✕</button>
        `;

        // Content Container
        this.content = document.createElement('div');
        this.content.style.cssText = `
            padding: 15px;
        `;

        this.dashboard.appendChild(header);
        this.dashboard.appendChild(this.content);
        document.body.appendChild(this.dashboard);

        // Toggle Button
        this.toggleButton = document.createElement('button');
        this.toggleButton.id = 'toggleAIDashboard';
        this.toggleButton.innerHTML = '🧠 AI Stats';
        this.toggleButton.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: rgba(74, 144, 226, 0.9);
            border: none;
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
            z-index: 9999;
            backdrop-filter: blur(5px);
            transition: all 0.3s ease;
        `;
        this.toggleButton.addEventListener('mouseenter', () => {
            this.toggleButton.style.background = 'rgba(74, 144, 226, 1)';
            this.toggleButton.style.transform = 'scale(1.05)';
        });
        this.toggleButton.addEventListener('mouseleave', () => {
            this.toggleButton.style.background = 'rgba(74, 144, 226, 0.9)';
            this.toggleButton.style.transform = 'scale(1)';
        });
        document.body.appendChild(this.toggleButton);
    }

    setupEventListeners() {
        this.toggleButton.addEventListener('click', () => this.toggle());
        
        document.getElementById('closeDashboard').addEventListener('click', () => this.hide());
        
        // Keyboard shortcut: Ctrl + I für AI Dashboard
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'i') {
                e.preventDefault();
                this.toggle();
            }
        });
    }

    show() {
        this.isVisible = true;
        this.dashboard.style.display = 'block';
        this.startUpdating();
        console.log('🧠 AI Dashboard opened');
    }

    hide() {
        this.isVisible = false;
        this.dashboard.style.display = 'none';
        this.stopUpdating();
        console.log('🧠 AI Dashboard closed');
    }

    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }

    startUpdating() {
        this.updateInterval = setInterval(() => {
            this.updateContent();
        }, 1000); // Update every second
        this.updateContent(); // Initial update
    }

    stopUpdating() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    updateContent() {
        if (!window.gameInstance || !window.gameInstance.characters) {
            this.content.innerHTML = '<div style="text-align: center; padding: 20px;">⏳ Waiting for game to load...</div>';
            return;
        }

        const characters = window.gameInstance.characters;
        let html = '';

        // Global AI Statistics
        html += this.renderGlobalStats(characters);

        // Individual Character Stats
        characters.forEach((character, index) => {
            html += this.renderCharacterStats(character, index);
        });

        // Neural Network Status
        html += this.renderNeuralNetworkStatus(characters);

        // Learning Trends
        html += this.renderLearningTrends(characters);

        this.content.innerHTML = html;
    }

    renderGlobalStats(characters) {
        const aiEnabled = characters.filter(c => c.aiBrain).length;
        const totalDecisions = characters.reduce((sum, c) => 
            sum + (c.aiBrain ? c.aiBrain.learningStats.decisionsKnnen : 0), 0);
        const totalSuccesses = characters.reduce((sum, c) => 
            sum + (c.aiBrain ? c.aiBrain.learningStats.successfulActions : 0), 0);
        const avgSuccessRate = totalDecisions > 0 ? (totalSuccesses / totalDecisions * 100).toFixed(1) : 0;

        return `
            <div style="margin-bottom: 20px; padding: 10px; background: rgba(80, 200, 120, 0.1); border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #50C878;">🌍 Global AI Status</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>📊 AI Characters: <span style="color: #4a90e2;">${aiEnabled}/${characters.length}</span></div>
                    <div>🎯 Avg Success: <span style="color: ${avgSuccessRate > 60 ? '#50C878' : avgSuccessRate > 40 ? '#FFD700' : '#FF6B6B'}">${avgSuccessRate}%</span></div>
                    <div>🧮 Total Decisions: <span style="color: #4a90e2;">${totalDecisions}</span></div>
                    <div>⭐ Total Successes: <span style="color: #50C878;">${totalSuccesses}</span></div>
                </div>
            </div>
        `;
    }

    renderCharacterStats(character, index) {
        if (!character.aiBrain) {
            return `
                <div style="margin-bottom: 15px; padding: 10px; background: rgba(255, 107, 107, 0.1); border-radius: 8px;">
                    <h4 style="margin: 0 0 8px 0; color: ${character.color};">${character.name}</h4>
                    <div style="color: #FF6B6B;">❌ Basic AI (No Learning)</div>
                </div>
            `;
        }

        const stats = character.aiBrain.getAIStats();
        const successRate = stats.successRate * 100;
        
        return `
            <div style="margin-bottom: 15px; padding: 10px; background: rgba(74, 144, 226, 0.1); border-radius: 8px;">
                <h4 style="margin: 0 0 8px 0; color: ${character.color};">${character.name}</h4>
                
                <!-- Learning Progress -->
                <div style="margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                        <span>📈 Success Rate</span>
                        <span style="color: ${successRate > 60 ? '#50C878' : successRate > 40 ? '#FFD700' : '#FF6B6B'}">${successRate.toFixed(1)}%</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); border-radius: 10px; height: 6px;">
                        <div style="background: ${successRate > 60 ? '#50C878' : successRate > 40 ? '#FFD700' : '#FF6B6B'}; width: ${successRate}%; height: 100%; border-radius: 10px; transition: width 0.3s ease;"></div>
                    </div>
                </div>
                
                <!-- Decision Stats -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px; margin-bottom: 8px;">
                    <div>🎯 Decisions: ${stats.learningStats.decisionsKnnen}</div>
                    <div>✅ Successes: ${stats.learningStats.successfulActions}</div>
                    <div>❌ Failures: ${stats.learningStats.failedActions}</div>
                    <div>🧠 Knowledge: ${stats.learningStats.knowledgePoints}</div>
                </div>
                
                <!-- Emotional State -->
                <div style="margin-bottom: 8px;">
                    <div style="font-size: 11px; margin-bottom: 3px;">🎭 Emotional State</div>
                    <div style="display: flex; gap: 10px; font-size: 10px;">
                        <span>😊 ${(stats.emotionalState.happiness * 100).toFixed(0)}%</span>
                        <span>😰 ${(stats.emotionalState.stress * 100).toFixed(0)}%</span>
                        <span>🤔 ${(stats.emotionalState.curiosity * 100).toFixed(0)}%</span>
                    </div>
                </div>
                
                <!-- Learning Parameters -->
                <div style="display: flex; justify-content: space-between; font-size: 10px; color: #888;">
                    <span>🔍 Exploration: ${(stats.explorationRate * 100).toFixed(1)}%</span>
                    <span>📚 Learning Rate: ${(stats.learningRate * 1000).toFixed(1)}</span>
                </div>
                
                <!-- Memory Status -->
                <div style="margin-top: 5px; font-size: 10px; color: #888;">
                    💾 Memory: ST:${stats.memoryStats.shortTerm} LT:${stats.memoryStats.longTerm} E:${stats.memoryStats.episodic}
                </div>
            </div>
        `;
    }

    renderNeuralNetworkStatus(characters) {
        const neuralNetworkChars = characters.filter(c => c.aiBrain && c.aiBrain.useNeuralNetwork);
        const tfStatus = typeof tf !== 'undefined' ? 'Loaded' : 'Not Available';
        
        return `
            <div style="margin-bottom: 20px; padding: 10px; background: rgba(255, 215, 0, 0.1); border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #FFD700;">🔬 Neural Network Status</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 11px;">
                    <div>🚀 TensorFlow.js: <span style="color: ${tfStatus === 'Loaded' ? '#50C878' : '#FF6B6B'}">${tfStatus}</span></div>
                    <div>🧠 Neural Chars: <span style="color: #4a90e2;">${neuralNetworkChars.length}/${characters.length}</span></div>
                </div>
                ${tfStatus === 'Loaded' ? `
                    <div style="margin-top: 8px; font-size: 10px; color: #888;">
                        ⚡ Each character runs local neural networks for decision making and learning
                    </div>
                ` : `
                    <div style="margin-top: 8px; font-size: 10px; color: #FF6B6B;">
                        ⚠️ TensorFlow.js not loaded - using rule-based AI with memory learning
                    </div>
                `}
            </div>
        `;
    }

    renderLearningTrends(characters) {
        // Calculate learning trends over time
        let totalMemories = 0;
        let avgExploration = 0;
        let activeAIs = 0;

        characters.forEach(character => {
            if (character.aiBrain) {
                const stats = character.aiBrain.getAIStats();
                totalMemories += stats.memoryStats.shortTerm + stats.memoryStats.longTerm;
                avgExploration += stats.explorationRate;
                activeAIs++;
            }
        });

        if (activeAIs > 0) {
            avgExploration = (avgExploration / activeAIs * 100).toFixed(1);
        }

        return `
            <div style="padding: 10px; background: rgba(128, 0, 128, 0.1); border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #DDA0DD;">📊 Learning Trends</h3>
                <div style="font-size: 11px;">
                    <div style="margin-bottom: 5px;">📚 Total Memories: <span style="color: #4a90e2;">${totalMemories}</span></div>
                    <div style="margin-bottom: 5px;">🎲 Avg Exploration: <span style="color: #FFD700;">${avgExploration}%</span></div>
                    <div style="font-size: 10px; color: #888; margin-top: 10px;">
                        💡 Higher exploration means more experimentation, lower means more exploitation of known strategies
                    </div>
                </div>
            </div>
        `;
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.aiDashboard = new AIMonitoringDashboard();
    });
} else {
    window.aiDashboard = new AIMonitoringDashboard();
}
