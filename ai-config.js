/**
 * Advanced AI Configuration System
 * Ermöglicht verschiedene AI-Modi und Anpassungen
 */

class AIConfiguration {
    constructor() {
        this.aiModes = {
            BASIC: 'basic',           // Regel-basierte AI
            LEARNING: 'learning',     // Regel-basiert mit Gedächtnis
            NEURAL: 'neural',         // Neuronale Netzwerke
            HYBRID: 'hybrid'          // Kombination aus allem
        };
        
        this.currentMode = this.aiModes.HYBRID;
        this.globalSettings = {
            learningRate: 0.01,
            explorationRate: 0.3,
            memoryCapacity: 100,
            emotionalInfluence: 0.5,
            socialLearning: true,
            collectiveIntelligence: false,
            adaptivePersonality: true
        };
        
        this.setupConfigPanel();
    }

    setupConfigPanel() {
        // Steuerung erfolgt jetzt über Bottom Nav (Button mit data-panel="aiConfigPanel")
        this.createConfigPanel();
    }

    createConfigPanel() {
        this.configPanel = document.createElement('div');
        this.configPanel.id = 'aiConfigPanel';
        this.configPanel.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 500px;
            max-height: 70vh;
            background: rgba(0, 0, 0, 0.95);
            border: 2px solid #800080;
            border-radius: 15px;
            color: white;
            font-family: Arial, sans-serif;
            z-index: 11000;
            display: none;
            overflow-y: auto;
            backdrop-filter: blur(15px);
        `;

        const header = document.createElement('div');
        header.style.cssText = `
            padding: 20px;
            background: linear-gradient(45deg, #800080, #4a90e2);
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        `;
        header.innerHTML = `
            <span style="font-weight: bold; font-size: 16px;">⚙️ AI Configuration</span>
            <button id="closeConfigPanel" style="
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                padding: 8px 12px;
                border-radius: 5px;
                cursor: pointer;
            ">✕</button>
        `;

        this.configContent = document.createElement('div');
        this.configContent.style.cssText = `padding: 20px;`;
        
        this.configPanel.appendChild(header);
        this.configPanel.appendChild(this.configContent);
        document.body.appendChild(this.configPanel);

        document.getElementById('closeConfigPanel').addEventListener('click', () => {
            this.hideConfigPanel();
        });

        this.updateConfigContent();
    }

    updateConfigContent() {
        this.configContent.innerHTML = `
            ${this.renderAIModeSelection()}
            ${this.renderGlobalSettings()}
            ${this.renderCharacterSettings()}
            ${this.renderExperimentalFeatures()}
            ${this.renderPresets()}
        `;

        this.attachEventListeners();
    }

    renderAIModeSelection() {
        return `
            <div style="margin-bottom: 25px;">
                <h3 style="color: #4a90e2; margin-bottom: 15px;">🧠 AI Mode Selection</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    ${Object.entries(this.aiModes).map(([key, value]) => `
                        <label style="
                            display: flex;
                            align-items: center;
                            padding: 10px;
                            background: rgba(74, 144, 226, ${this.currentMode === value ? '0.3' : '0.1'});
                            border-radius: 8px;
                            cursor: pointer;
                            transition: background 0.3s ease;
                        ">
                            <input type="radio" name="aiMode" value="${value}" ${this.currentMode === value ? 'checked' : ''} 
                                   style="margin-right: 8px;">
                            <div>
                                <div style="font-weight: bold;">${this.getAIModeTitle(value)}</div>
                                <div style="font-size: 11px; color: #ccc;">${this.getAIModeDescription(value)}</div>
                            </div>
                        </label>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderGlobalSettings() {
        return `
            <div style="margin-bottom: 25px;">
                <h3 style="color: #50C878; margin-bottom: 15px;">⚡ Global AI Settings</h3>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px;">📚 Learning Rate: <span id="learningRateValue">${this.globalSettings.learningRate}</span></label>
                    <input type="range" id="learningRate" min="0.001" max="0.1" step="0.001" value="${this.globalSettings.learningRate}"
                           style="width: 100%; margin-bottom: 5px;">
                    <div style="font-size: 11px; color: #888;">How fast the AI learns from experiences</div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px;">🎲 Exploration Rate: <span id="explorationRateValue">${this.globalSettings.explorationRate}</span></label>
                    <input type="range" id="explorationRate" min="0.05" max="0.8" step="0.05" value="${this.globalSettings.explorationRate}"
                           style="width: 100%; margin-bottom: 5px;">
                    <div style="font-size: 11px; color: #888;">Balance between exploration and exploitation</div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px;">🧠 Memory Capacity: <span id="memoryCapacityValue">${this.globalSettings.memoryCapacity}</span></label>
                    <input type="range" id="memoryCapacity" min="50" max="500" step="50" value="${this.globalSettings.memoryCapacity}"
                           style="width: 100%; margin-bottom: 5px;">
                    <div style="font-size: 11px; color: #888;">Maximum number of memories each character can store</div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px;">🎭 Emotional Influence: <span id="emotionalInfluenceValue">${this.globalSettings.emotionalInfluence}</span></label>
                    <input type="range" id="emotionalInfluence" min="0" max="1" step="0.1" value="${this.globalSettings.emotionalInfluence}"
                           style="width: 100%; margin-bottom: 5px;">
                    <div style="font-size: 11px; color: #888;">How much emotions affect decision making</div>
                </div>
            </div>
        `;
    }

    renderCharacterSettings() {
        if (!window.gameInstance || !window.gameInstance.characters) {
            return '<div style="text-align: center; color: #888;">⏳ Waiting for characters to load...</div>';
        }

        const characters = window.gameInstance.characters;
        
        return `
            <div style="margin-bottom: 25px;">
                <h3 style="color: #FFD700; margin-bottom: 15px;">👥 Individual Character Settings</h3>
                ${characters.map((character, index) => `
                    <div style="
                        margin-bottom: 15px;
                        padding: 10px;
                        background: rgba(255, 215, 0, 0.1);
                        border-radius: 8px;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span style="font-weight: bold; color: ${character.color};">${character.name}</span>
                            <label style="display: flex; align-items: center;">
                                <input type="checkbox" id="learning_${index}" ${character.learningEnabled ? 'checked' : ''}
                                       style="margin-right: 5px;">
                                Learning Enabled
                            </label>
                        </div>
                        
                        ${character.aiBrain ? `
                            <div style="font-size: 11px; color: #888;">
                                Success Rate: ${(character.aiBrain.getSuccessRate() * 100).toFixed(1)}% | 
                                Decisions: ${character.aiBrain.learningStats.decisionsKnnen} |
                                Exploration: ${(character.aiBrain.explorationRate * 100).toFixed(1)}%
                            </div>
                            <button onclick="window.aiConfig.resetCharacterAI(${index})" style="
                                margin-top: 5px;
                                background: rgba(255, 107, 107, 0.3);
                                border: none;
                                color: white;
                                padding: 5px 10px;
                                border-radius: 5px;
                                cursor: pointer;
                                font-size: 10px;
                            ">🔄 Reset AI</button>
                        ` : '<div style="font-size: 11px; color: #FF6B6B;">Basic AI - No Learning</div>'}
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderExperimentalFeatures() {
        return `
            <div style="margin-bottom: 25px;">
                <h3 style="color: #FF6B6B; margin-bottom: 15px;">🧪 Experimental Features</h3>
                
                <label style="
                    display: flex;
                    align-items: center;
                    margin-bottom: 10px;
                    padding: 8px;
                    background: rgba(255, 107, 107, 0.1);
                    border-radius: 5px;
                ">
                    <input type="checkbox" id="socialLearning" ${this.globalSettings.socialLearning ? 'checked' : ''}
                           style="margin-right: 8px;">
                    <div>
                        <div style="font-weight: bold;">🤝 Social Learning</div>
                        <div style="font-size: 11px; color: #888;">Characters learn from observing others</div>
                    </div>
                </label>
                
                <label style="
                    display: flex;
                    align-items: center;
                    margin-bottom: 10px;
                    padding: 8px;
                    background: rgba(255, 107, 107, 0.1);
                    border-radius: 5px;
                ">
                    <input type="checkbox" id="collectiveIntelligence" ${this.globalSettings.collectiveIntelligence ? 'checked' : ''}
                           style="margin-right: 8px;">
                    <div>
                        <div style="font-weight: bold;">🌐 Collective Intelligence</div>
                        <div style="font-size: 11px; color: #888;">Shared knowledge across all characters</div>
                    </div>
                </label>
                
                <label style="
                    display: flex;
                    align-items: center;
                    margin-bottom: 10px;
                    padding: 8px;
                    background: rgba(255, 107, 107, 0.1);
                    border-radius: 5px;
                ">
                    <input type="checkbox" id="adaptivePersonality" ${this.globalSettings.adaptivePersonality ? 'checked' : ''}
                           style="margin-right: 8px;">
                    <div>
                        <div style="font-weight: bold;">🔄 Adaptive Personality</div>
                        <div style="font-size: 11px; color: #888;">Personalities evolve based on experiences</div>
                    </div>
                </label>
            </div>
        `;
    }

    renderPresets() {
        return `
            <div style="margin-bottom: 20px;">
                <h3 style="color: #DDA0DD; margin-bottom: 15px;">💾 AI Presets</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 15px;">
                    <button onclick="window.aiConfig.loadPreset('conservative')" style="
                        background: rgba(74, 144, 226, 0.3);
                        border: none;
                        color: white;
                        padding: 8px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 11px;
                    ">🛡️ Conservative</button>
                    
                    <button onclick="window.aiConfig.loadPreset('aggressive')" style="
                        background: rgba(255, 107, 107, 0.3);
                        border: none;
                        color: white;
                        padding: 8px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 11px;
                    ">⚡ Aggressive</button>
                    
                    <button onclick="window.aiConfig.loadPreset('balanced')" style="
                        background: rgba(80, 200, 120, 0.3);
                        border: none;
                        color: white;
                        padding: 8px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 11px;
                    ">⚖️ Balanced</button>
                </div>
                
                <div style="display: flex; gap: 8px;">
                    <button onclick="window.aiConfig.saveCurrentConfig()" style="
                        flex: 1;
                        background: rgba(128, 0, 128, 0.3);
                        border: none;
                        color: white;
                        padding: 10px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 12px;
                    ">💾 Save Config</button>
                    
                    <button onclick="window.aiConfig.resetToDefaults()" style="
                        flex: 1;
                        background: rgba(255, 140, 0, 0.3);
                        border: none;
                        color: white;
                        padding: 10px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 12px;
                    ">🔄 Reset</button>
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        // AI Mode selection
        document.querySelectorAll('input[name="aiMode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.setAIMode(e.target.value);
            });
        });

        // Global settings sliders
        ['learningRate', 'explorationRate', 'memoryCapacity', 'emotionalInfluence'].forEach(setting => {
            const slider = document.getElementById(setting);
            const valueDisplay = document.getElementById(setting + 'Value');
            
            if (slider && valueDisplay) {
                slider.addEventListener('input', (e) => {
                    const value = parseFloat(e.target.value);
                    this.globalSettings[setting] = value;
                    valueDisplay.textContent = value;
                    this.applyGlobalSettings();
                });
            }
        });

        // Character learning toggles
        if (window.gameInstance && window.gameInstance.characters) {
            window.gameInstance.characters.forEach((character, index) => {
                const toggle = document.getElementById(`learning_${index}`);
                if (toggle) {
                    toggle.addEventListener('change', (e) => {
                        character.learningEnabled = e.target.checked;
                        console.log(`${character.name} learning ${e.target.checked ? 'enabled' : 'disabled'}`);
                    });
                }
            });
        }

        // Experimental features
        ['socialLearning', 'collectiveIntelligence', 'adaptivePersonality'].forEach(feature => {
            const checkbox = document.getElementById(feature);
            if (checkbox) {
                checkbox.addEventListener('change', (e) => {
                    this.globalSettings[feature] = e.target.checked;
                    this.applyExperimentalFeatures();
                });
            }
        });
    }

    showConfigPanel() {
        this.configPanel.classList.remove('panel-hidden');
        this.configPanel.classList.add('panel-visible');
        this.updateConfigContent();
    }

    hideConfigPanel() {
        this.configPanel.classList.add('panel-hidden');
        this.configPanel.classList.remove('panel-visible');
    }

    toggleConfigPanel(){
        if (this.configPanel.classList.contains('panel-hidden')) this.showConfigPanel(); else this.hideConfigPanel();
    }

    setAIMode(mode) {
        this.currentMode = mode;
        console.log(`AI Mode set to: ${mode}`);
        
        // Apply mode-specific settings
        switch (mode) {
            case this.aiModes.BASIC:
                this.disableAllLearning();
                break;
            case this.aiModes.LEARNING:
                this.enableBasicLearning();
                break;
            case this.aiModes.NEURAL:
                this.enableNeuralLearning();
                break;
            case this.aiModes.HYBRID:
                this.enableHybridLearning();
                break;
        }
    }

    applyGlobalSettings() {
        if (!window.gameInstance || !window.gameInstance.characters) return;

        window.gameInstance.characters.forEach(character => {
            if (character.aiBrain) {
                character.aiBrain.learningRate = this.globalSettings.learningRate;
                character.aiBrain.explorationRate = this.globalSettings.explorationRate;
                // Apply other settings...
            }
        });
    }

    disableAllLearning() {
        if (!window.gameInstance) return;
        window.gameInstance.characters.forEach(character => {
            character.learningEnabled = false;
        });
    }

    enableBasicLearning() {
        if (!window.gameInstance) return;
        window.gameInstance.characters.forEach(character => {
            character.learningEnabled = true;
            if (character.aiBrain) {
                character.aiBrain.useNeuralNetwork = false;
            }
        });
    }

    enableNeuralLearning() {
        if (!window.gameInstance) return;
        window.gameInstance.characters.forEach(character => {
            character.learningEnabled = true;
            if (character.aiBrain) {
                character.aiBrain.useNeuralNetwork = true;
            }
        });
    }

    enableHybridLearning() {
        if (!window.gameInstance) return;
        window.gameInstance.characters.forEach(character => {
            character.learningEnabled = true;
            // Keep current neural network settings
        });
    }

    loadPreset(presetName) {
        const presets = {
            conservative: {
                learningRate: 0.005,
                explorationRate: 0.1,
                memoryCapacity: 200,
                emotionalInfluence: 0.3
            },
            aggressive: {
                learningRate: 0.05,
                explorationRate: 0.6,
                memoryCapacity: 50,
                emotionalInfluence: 0.8
            },
            balanced: {
                learningRate: 0.01,
                explorationRate: 0.3,
                memoryCapacity: 100,
                emotionalInfluence: 0.5
            }
        };

        if (presets[presetName]) {
            Object.assign(this.globalSettings, presets[presetName]);
            this.applyGlobalSettings();
            this.updateConfigContent();
            console.log(`Applied ${presetName} preset`);
        }
    }

    resetCharacterAI(characterIndex) {
        if (!window.gameInstance || !window.gameInstance.characters[characterIndex]) return;
        
        const character = window.gameInstance.characters[characterIndex];
        if (character.aiBrain) {
            // Reset AI brain
            const personality = {
                name: character.name,
                color: character.color,
                traits: character.traits,
                preferredAction: character.preferredAction
            };
            
            character.aiBrain = new AIBrain(personality);
            console.log(`Reset AI for ${character.name}`);
        }
    }

    getAIModeTitle(mode) {
        const titles = {
            basic: 'Basic AI',
            learning: 'Learning AI',
            neural: 'Neural AI',
            hybrid: 'Hybrid AI'
        };
        return titles[mode] || mode;
    }

    getAIModeDescription(mode) {
        const descriptions = {
            basic: 'Simple rule-based behavior',
            learning: 'Rules + memory learning',
            neural: 'Neural networks only',
            hybrid: 'Best of all approaches'
        };
        return descriptions[mode] || '';
    }

    saveCurrentConfig() {
        const config = {
            mode: this.currentMode,
            settings: this.globalSettings,
            timestamp: new Date().toISOString()
        };
        
        localStorage.setItem('aiConfig', JSON.stringify(config));
        console.log('AI Configuration saved');
    }

    loadSavedConfig() {
        const saved = localStorage.getItem('aiConfig');
        if (saved) {
            try {
                const config = JSON.parse(saved);
                this.currentMode = config.mode;
                Object.assign(this.globalSettings, config.settings);
                this.applyGlobalSettings();
                console.log('AI Configuration loaded');
            } catch (error) {
                console.error('Error loading AI config:', error);
            }
        }
    }

    resetToDefaults() {
        this.globalSettings = {
            learningRate: 0.01,
            explorationRate: 0.3,
            memoryCapacity: 100,
            emotionalInfluence: 0.5,
            socialLearning: true,
            collectiveIntelligence: false,
            adaptivePersonality: true
        };
        this.currentMode = this.aiModes.HYBRID;
        this.applyGlobalSettings();
        this.updateConfigContent();
        console.log('AI Configuration reset to defaults');
    }

    applyExperimentalFeatures() {
        // Implement experimental features here
        console.log('Applied experimental features:', this.globalSettings);
    }
}

// Initialize AI Configuration
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.aiConfig = new AIConfiguration();
        window.aiConfig.loadSavedConfig();
    });
} else {
    window.aiConfig = new AIConfiguration();
    window.aiConfig.loadSavedConfig();
}
