class UIDebugManager {
    constructor() {
        this.debugPanel = null;
        this.gameInstance = null;
        this.editMode = 'none';
        this.selectedElement = null;
        this.isDragging = false;
        this.dragOffset = { x: 0, y: 0 };
        this.uiDragState = {
            isDragging: false,
            element: null,
            startX: 0,
            startY: 0,
            offsetX: 0,
            offsetY: 0
        };
        this.elements = {
            ui: {
                element: null,
                defaultStyles: { top: 20, left: 20, zIndex: 100 }
            },
            characterInfo: {
                element: null,
                defaultStyles: { top: 20, right: 20, zIndex: 100 }
            }
        };
        this.isVisible = false;
        this.init();
    }

    init() {
        this.debugPanel = document.getElementById('debugPanel');
        this.elements.ui.element = document.getElementById('ui');
        this.elements.characterInfo.element = document.getElementById('characterInfo');
        
        // Make debug panel draggable
        this.makeDebugPanelDraggable();
        
        // Wait for game instance to be available
        this.waitForGame();
        
        this.setupEventListeners();
        this.syncInputsWithCurrentStyles();
        this.loadSavedPreset();
        
        console.log('🔧 Debug Manager initialized. Press Ctrl+D to open debug panel.');
    }
    
    waitForGame() {
        const checkGame = () => {
            if (window.gameInstance) {
                this.gameInstance = window.gameInstance;
                this.setupTerrainControls();
                console.log('🎮 Game instance connected to debug manager');
            } else {
                setTimeout(checkGame, 100);
            }
        };
        checkGame();
    }

    setupEventListeners() {
        // Hotkey listener (Ctrl+D)
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key.toLowerCase() === 'd') {
                e.preventDefault();
                this.toggleDebugPanel();
            }
        });

        // UI Panel Controls
        this.setupControlListeners('ui', ['top', 'left', 'zIndex']);
        
        // Character Info Panel Controls  
        this.setupControlListeners('characterInfo', ['top', 'right', 'zIndex']);

        // Button listeners
        document.getElementById('copyCSS').addEventListener('click', () => this.copyCSS());
        document.getElementById('savePreset').addEventListener('click', () => this.savePreset());
        document.getElementById('loadPreset').addEventListener('click', () => this.loadPreset());
        document.getElementById('resetPositions').addEventListener('click', () => this.resetPositions());
        document.getElementById('closeDebug').addEventListener('click', () => this.hideDebugPanel());
        
        // Edit mode selector
        document.getElementById('edit-mode').addEventListener('change', (e) => {
            this.editMode = e.target.value;
            console.log('🎯 Edit mode:', this.editMode);
        });

        // Close panel when clicking outside
        this.debugPanel.addEventListener('click', (e) => e.stopPropagation());
        document.addEventListener('click', (e) => {
            if (this.isVisible && !this.debugPanel.contains(e.target)) {
                this.hideDebugPanel();
            }
        });
    }

    setupControlListeners(elementKey, properties) {
        properties.forEach(prop => {
            const slider = document.getElementById(`${elementKey}-${prop.toLowerCase()}`);
            const input = document.getElementById(`${elementKey}-${prop.toLowerCase()}-input`);
            
            if (slider && input) {
                // Slider change
                slider.addEventListener('input', (e) => {
                    const value = parseInt(e.target.value);
                    input.value = value;
                    this.updateElementStyle(elementKey, prop, value);
                });

                // Input change
                input.addEventListener('input', (e) => {
                    const value = parseInt(e.target.value) || 0;
                    slider.value = value;
                    this.updateElementStyle(elementKey, prop, value);
                });
            }
        });
    }

    updateElementStyle(elementKey, property, value) {
        const element = this.elements[elementKey].element;
        if (!element) return;

        switch(property) {
            case 'top':
                element.style.top = `${value}px`;
                break;
            case 'left':
                element.style.left = `${value}px`;
                break;
            case 'right':
                element.style.right = `${value}px`;
                break;
            case 'zIndex':
                element.style.zIndex = value;
                break;
        }
        
        this.updateCSSPreview();
    }

    syncInputsWithCurrentStyles() {
        // Get current computed styles and sync with inputs
        Object.keys(this.elements).forEach(key => {
            const element = this.elements[key].element;
            if (!element) return;

            const computedStyle = window.getComputedStyle(element);
            
            // Extract current values
            const currentStyles = {
                top: parseInt(computedStyle.top) || this.elements[key].defaultStyles.top || 20,
                left: parseInt(computedStyle.left) || this.elements[key].defaultStyles.left || undefined,
                right: parseInt(computedStyle.right) || this.elements[key].defaultStyles.right || undefined,
                zIndex: parseInt(computedStyle.zIndex) || this.elements[key].defaultStyles.zIndex || 100
            };

            // Sync sliders and inputs
            ['top', 'left', 'right', 'zIndex'].forEach(prop => {
                if (currentStyles[prop] !== undefined) {
                    const slider = document.getElementById(`${key}-${prop.toLowerCase()}`);
                    const input = document.getElementById(`${key}-${prop.toLowerCase()}-input`);
                    
                    if (slider && input && currentStyles[prop] !== undefined) {
                        slider.value = currentStyles[prop];
                        input.value = currentStyles[prop];
                    }
                }
            });
        });
    }

    toggleDebugPanel() {
        if (this.isVisible) {
            this.hideDebugPanel();
        } else {
            this.showDebugPanel();
        }
    }

    showDebugPanel() {
        this.debugPanel.classList.add('visible');
        this.isVisible = true;
        this.syncInputsWithCurrentStyles();
        this.updateCSSPreview();
        
        // Enable UI dragging when debug panel is visible
        this.enableUIDragging();
        
        // Hide hotkey hint
        document.getElementById('debugHotkey').style.display = 'none';
    }

    hideDebugPanel() {
        this.debugPanel.classList.remove('visible');
        this.isVisible = false;
        
        // Disable UI dragging when debug panel is hidden
        this.disableUIDragging();
        
        // Show hotkey hint again
        document.getElementById('debugHotkey').style.display = 'block';
    }

    getCurrentStyles() {
        const styles = {};
        
        Object.keys(this.elements).forEach(key => {
            const element = this.elements[key].element;
            if (!element) return;

            const computedStyle = window.getComputedStyle(element);
            styles[key] = {
                top: parseInt(computedStyle.top) || undefined,
                left: parseInt(computedStyle.left) || undefined,
                right: parseInt(computedStyle.right) || undefined,
                zIndex: parseInt(computedStyle.zIndex) || undefined
            };
        });
        
        return styles;
    }

    updateCSSPreview() {
        const styles = this.getCurrentStyles();
        let cssCode = '/* Generated CSS from Debug Panel */\n\n';
        
        Object.keys(styles).forEach(key => {
            cssCode += `#${key} {\n`;
            Object.keys(styles[key]).forEach(prop => {
                if (styles[key][prop] !== undefined) {
                    const cssProperty = prop === 'zIndex' ? 'z-index' : prop;
                    const value = prop === 'zIndex' ? styles[key][prop] : `${styles[key][prop]}px`;
                    cssCode += `    ${cssProperty}: ${value};\n`;
                }
            });
            cssCode += '}\n\n';
        });

        document.getElementById('cssOutput').textContent = cssCode;
    }

    async copyCSS() {
        const cssCode = document.getElementById('cssOutput').textContent;
        
        try {
            await navigator.clipboard.writeText(cssCode);
            
            // Visual feedback
            const button = document.getElementById('copyCSS');
            const originalText = button.textContent;
            button.textContent = '✅ Copied!';
            button.classList.add('success');
            
            setTimeout(() => {
                button.textContent = originalText;
                button.classList.remove('success');
            }, 2000);
            
            console.log('✅ CSS copied to clipboard!');
        } catch (err) {
            console.error('❌ Failed to copy CSS:', err);
            
            // Fallback: show in alert
            alert('CSS Code:\n\n' + cssCode);
        }
    }

    savePreset() {
        const styles = this.getCurrentStyles();
        const presetName = `debug_preset_${new Date().getTime()}`;
        
        try {
            localStorage.setItem('ui_debug_preset', JSON.stringify(styles));
            localStorage.setItem('ui_debug_preset_name', presetName);
            
            // Visual feedback
            const button = document.getElementById('savePreset');
            const originalText = button.textContent;
            button.textContent = '✅ Saved!';
            
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
            
            console.log('💾 Preset saved:', presetName);
        } catch (err) {
            console.error('❌ Failed to save preset:', err);
        }
    }

    loadPreset() {
        try {
            const savedPreset = localStorage.getItem('ui_debug_preset');
            if (!savedPreset) {
                alert('No saved preset found!');
                return;
            }
            
            const styles = JSON.parse(savedPreset);
            this.applyStyles(styles);
            this.syncInputsWithCurrentStyles();
            
            // Visual feedback
            const button = document.getElementById('loadPreset');
            const originalText = button.textContent;
            button.textContent = '✅ Loaded!';
            
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
            
            console.log('📂 Preset loaded successfully');
        } catch (err) {
            console.error('❌ Failed to load preset:', err);
            alert('Failed to load preset!');
        }
    }

    loadSavedPreset() {
        // Auto-load saved preset on page load
        try {
            const savedPreset = localStorage.getItem('ui_debug_preset');
            if (savedPreset) {
                const styles = JSON.parse(savedPreset);
                this.applyStyles(styles);
                console.log('🔄 Auto-loaded saved preset');
            }
        } catch (err) {
            console.warn('⚠️ Could not auto-load preset:', err);
        }
    }

    applyStyles(styles) {
        Object.keys(styles).forEach(key => {
            const element = this.elements[key].element;
            if (!element) return;

            Object.keys(styles[key]).forEach(prop => {
                if (styles[key][prop] !== undefined) {
                    this.updateElementStyle(key, prop, styles[key][prop]);
                }
            });
        });
        
        this.updateCSSPreview();
    }

    resetPositions() {
        Object.keys(this.elements).forEach(key => {
            const defaultStyles = this.elements[key].defaultStyles;
            this.applyStyles({ [key]: defaultStyles });
        });
        
        this.syncInputsWithCurrentStyles();
        
        // Visual feedback
        const button = document.getElementById('resetPositions');
        const originalText = button.textContent;
        button.textContent = '✅ Reset!';
        
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
        
        console.log('🔄 Positions reset to defaults');
    }
    
    setupTerrainControls() {
        if (!this.gameInstance) return;
        
        // Terrain generation sliders
        this.setupTerrainSlider('trees', 25);
        this.setupTerrainSlider('mountains', 8);
        this.setupTerrainSlider('bushes', 40);
        this.setupTerrainSlider('river-width', 40);
        
        // Brücken-Einstellungen
        this.setupBridgeControls();
        
        // Regeneration buttons
        document.getElementById('regenerate-trees').addEventListener('click', () => {
            this.regenerateTerrain('tree');
        });
        
        document.getElementById('regenerate-mountains').addEventListener('click', () => {
            this.regenerateTerrain('mountain');
        });
        
        document.getElementById('regenerate-bushes').addEventListener('click', () => {
            this.regenerateTerrain('bush');
        });
        
        document.getElementById('regenerate-river').addEventListener('click', () => {
            this.regenerateRiver();
        });
        
        // Terrain editor buttons
        document.getElementById('clear-terrain').addEventListener('click', () => {
            this.clearAllTerrain();
        });
        
        document.getElementById('export-terrain').addEventListener('click', () => {
            this.exportTerrain();
        });
        
        document.getElementById('randomize-terrain').addEventListener('click', () => {
            this.randomizeTerrain();
        });
        
        document.getElementById('load-custom-terrain').addEventListener('click', () => {
            this.loadCustomTerrain();
        });
        
        // Panel toggle button
        document.getElementById('toggle-debug-panel').addEventListener('click', () => {
            this.togglePanelVisibility();
        });
        
        document.getElementById('showPanelBtn').addEventListener('click', () => {
            this.showPanelFromFloat();
        });
        
        // Position copy buttons
        document.getElementById('copy-positions').addEventListener('click', () => {
            this.copyAllPositions();
        });
        
        document.getElementById('copy-selected').addEventListener('click', () => {
            this.copySelectedPosition();
        });
        
        // Canvas event handlers for drag & drop - enhanced debugging
        this.gameInstance.canvas.addEventListener('mousedown', (e) => {
            console.log('🎯 Canvas mousedown EVENT FIRED!');
            console.log('🎯 EditMode:', this.editMode, 'Visible:', this.isVisible);
            console.log('🎯 Event target:', e.target);
            console.log('🎯 Canvas element:', this.gameInstance.canvas);
            console.log('🎯 Target === Canvas:', e.target === this.gameInstance.canvas);
            console.log('🎯 UI Drag State:', this.uiDragState.isDragging);
            
            // Don't handle terrain dragging if UI is being dragged
            if (this.uiDragState.isDragging) {
                console.log('🚫 UI is being dragged, skipping terrain handling');
                return;
            }
            
            if (this.editMode === 'drag' && this.isVisible) {
                console.log('✅ Calling handleMouseDown for terrain drag');
                e.preventDefault(); // Prevent any default behavior
                e.stopPropagation(); // Stop event bubbling
                this.handleMouseDown(e);
            } else if (this.editMode !== 'none' && this.isVisible) {
                console.log('✅ Calling handleCanvasClick');
                this.handleCanvasClick(e);
            } else {
                console.log('❌ Conditions not met - EditMode:', this.editMode, 'Visible:', this.isVisible);
            }
        });
        
        // Add additional event listeners to debug
        this.gameInstance.canvas.addEventListener('click', (e) => {
            console.log('🖱️ Canvas CLICK event fired');
        });
        
        this.gameInstance.canvas.addEventListener('mouseenter', (e) => {
            console.log('📍 Mouse entered canvas');
        });
        
        document.addEventListener('mousedown', (e) => {
            console.log('🌐 Document mousedown - target:', e.target.tagName, e.target.id || 'no-id');
        });
        
        this.gameInstance.canvas.addEventListener('mousemove', (e) => {
            if (this.editMode === 'drag' && this.isVisible && !this.uiDragState.isDragging) {
                this.handleMouseMove(e);
            }
        });
        
        this.gameInstance.canvas.addEventListener('mouseup', (e) => {
            if (this.editMode === 'drag' && this.isVisible && !this.uiDragState.isDragging) {
                this.handleMouseUp(e);
            }
        });
    }
    
    setupTerrainSlider(type, defaultValue) {
        const slider = document.getElementById(`terrain-${type}`);
        const input = document.getElementById(`terrain-${type}-input`);
        
        if (slider && input) {
            slider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                input.value = value;
                this.updateTerrainCount(type, value);
            });
            
            input.addEventListener('input', (e) => {
                const value = parseInt(e.target.value) || 0;
                slider.value = value;
                this.updateTerrainCount(type, value);
            });
        }
    }
    
    setupBridgeControls() {
        // Brücken-Breite
        const widthSlider = document.getElementById('bridge-width');
        const widthInput = document.getElementById('bridge-width-input');
        
        if (widthSlider && widthInput) {
            widthSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                widthInput.value = value;
                this.updateBridgeProperty('width', value);
            });
            
            widthInput.addEventListener('input', (e) => {
                const value = parseInt(e.target.value) || 90;
                widthSlider.value = value;
                this.updateBridgeProperty('width', value);
            });
        }
        
        // Brücken-Höhe
        const heightSlider = document.getElementById('bridge-height');
        const heightInput = document.getElementById('bridge-height-input');
        
        if (heightSlider && heightInput) {
            heightSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                heightInput.value = value;
                this.updateBridgeProperty('height', value);
            });
            
            heightInput.addEventListener('input', (e) => {
                const value = parseInt(e.target.value) || 12;
                heightSlider.value = value;
                this.updateBridgeProperty('height', value);
            });
        }
        
        // Brücken-Winkel
        const angleSlider = document.getElementById('bridge-angle');
        const angleInput = document.getElementById('bridge-angle-input');
        
        if (angleSlider && angleInput) {
            angleSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                angleInput.value = value;
                this.updateBridgeProperty('angle', value * Math.PI / 180); // Convert to radians
            });
            
            angleInput.addEventListener('input', (e) => {
                const value = parseInt(e.target.value) || 23;
                angleSlider.value = value;
                this.updateBridgeProperty('angle', value * Math.PI / 180); // Convert to radians
            });
        }
    }
    
    updateBridgeProperty(property, value) {
        if (!this.gameInstance) return;
        
        const bridge = this.gameInstance.terrain.find(t => t.type === 'bridge');
        if (bridge) {
            bridge[property] = value;
            console.log(`🌉 Bridge ${property} updated to:`, value);
            
            // Update crossingPoints when bridge changes
            if (property === 'width' || property === 'height' || property === 'angle') {
                this.updateBridgeCrossingPoints(bridge);
            }
        }
    }
    
    updateBridgeCrossingPoints(bridge) {
        // Recalculate crossing points based on bridge position and angle
        const offsetX = Math.cos(bridge.angle) * bridge.width / 2;
        const offsetY = Math.sin(bridge.angle) * bridge.width / 2;
        
        bridge.crossingPoints = [
            { x: bridge.x - offsetX, y: bridge.y - offsetY },  // Einstieg
            { x: bridge.x + offsetX, y: bridge.y + offsetY }   // Ausstieg
        ];
    }
    
    updateTerrainCount(type, count) {
        if (!this.gameInstance) return;
        
        if (type === 'river-width') {
            // Update river width
            const river = this.gameInstance.terrain.find(t => t.type === 'river');
            if (river) {
                river.width = count;
            }
        } else {
            // Update terrain count by regenerating
            this.regenerateTerrain(type, count);
        }
    }
    
    regenerateTerrain(terrainType, count = null) {
        if (!this.gameInstance) return;
        
        // Remove existing terrain of this type (but keep river and bridge)
        this.gameInstance.terrain = this.gameInstance.terrain.filter(t => 
            t.type !== terrainType || t.type === 'river' || t.type === 'bridge'
        );
        
        // Get count from slider if not provided
        if (count === null) {
            const input = document.getElementById(`terrain-${terrainType}s-input`);
            count = input ? parseInt(input.value) : 25;
        }
        
        // Generate new terrain
        const width = this.gameInstance.canvas.width;
        const height = this.gameInstance.canvas.height;
        
        for (let i = 0; i < count; i++) {
            let newItem;
            
            switch (terrainType) {
                case 'tree':
                    newItem = {
                        type: 'tree',
                        x: Math.random() * width,
                        y: height * 0.5 + Math.random() * height * 0.4,
                        size: 15 + Math.random() * 10
                    };
                    break;
                    
                case 'mountain':
                    newItem = {
                        type: 'mountain',
                        x: Math.random() * width,
                        y: height * 0.1 + Math.random() * height * 0.2,
                        size: 30 + Math.random() * 40
                    };
                    break;
                    
                case 'bush':
                    newItem = {
                        type: 'bush',
                        x: Math.random() * width,
                        y: height * 0.4 + Math.random() * height * 0.5,
                        size: 8 + Math.random() * 8
                    };
                    break;
            }
            
            if (newItem) {
                this.gameInstance.terrain.push(newItem);
            }
        }
        
        console.log(`🌲 Regenerated ${count} ${terrainType}s`);
    }
    
    regenerateRiver() {
        if (!this.gameInstance) return;
        
        const width = this.gameInstance.canvas.width;
        const height = this.gameInstance.canvas.height;
        const riverWidth = parseInt(document.getElementById('terrain-river-width-input').value);
        
        // Remove existing river
        this.gameInstance.terrain = this.gameInstance.terrain.filter(t => t.type !== 'river');
        
        // Create new river with random path
        const river = {
            type: 'river',
            points: [
                { x: 0, y: height * (0.2 + Math.random() * 0.3) },
                { x: width * 0.25, y: height * (0.25 + Math.random() * 0.2) },
                { x: width * 0.5, y: height * (0.3 + Math.random() * 0.2) },
                { x: width * 0.75, y: height * (0.25 + Math.random() * 0.2) },
                { x: width, y: height * (0.2 + Math.random() * 0.3) }
            ],
            width: riverWidth
        };
        
        this.gameInstance.terrain.push(river);
        console.log('🌊 River regenerated');
    }
    
    handleCanvasClick(e) {
        if (!this.gameInstance) return;
        
        const rect = this.gameInstance.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        switch (this.editMode) {
            case 'add-tree':
                this.gameInstance.terrain.push({
                    type: 'tree',
                    x: x,
                    y: y,
                    size: 15 + Math.random() * 10
                });
                console.log('🌳 Tree added at', x, y);
                break;
                
            case 'add-mountain':
                this.gameInstance.terrain.push({
                    type: 'mountain',
                    x: x,
                    y: y,
                    size: 30 + Math.random() * 40
                });
                console.log('⛰️ Mountain added at', x, y);
                break;
                
            case 'add-bush':
                this.gameInstance.terrain.push({
                    type: 'bush',
                    x: x,
                    y: y,
                    size: 8 + Math.random() * 8
                });
                console.log('🌿 Bush added at', x, y);
                break;
                
            case 'delete':
                // Find closest terrain element
                let closestDistance = Infinity;
                let closestIndex = -1;
                
                this.gameInstance.terrain.forEach((item, index) => {
                    if (item.type !== 'river') {
                        const distance = Math.sqrt((x - item.x) ** 2 + (y - item.y) ** 2);
                        if (distance < closestDistance && distance < item.size) {
                            closestDistance = distance;
                            closestIndex = index;
                        }
                    }
                });
                
                if (closestIndex >= 0) {
                    const deleted = this.gameInstance.terrain.splice(closestIndex, 1)[0];
                    console.log('🗑️ Deleted', deleted.type, 'at', deleted.x, deleted.y);
                }
                break;
        }
    }
    
    clearAllTerrain() {
        if (!this.gameInstance) return;
        
        // Keep river and bridge when clearing
        this.gameInstance.terrain = this.gameInstance.terrain.filter(t => 
            t.type === 'river' || t.type === 'bridge'
        );
        console.log('🗑️ All terrain cleared (except river and bridge)');
    }
    
    exportTerrain() {
        if (!this.gameInstance) return;
        
        const terrainData = {
            terrain: this.gameInstance.terrain,
            timestamp: new Date().toISOString(),
            counts: {
                trees: this.gameInstance.terrain.filter(t => t.type === 'tree').length,
                mountains: this.gameInstance.terrain.filter(t => t.type === 'mountain').length,
                bushes: this.gameInstance.terrain.filter(t => t.type === 'bush').length,
                rivers: this.gameInstance.terrain.filter(t => t.type === 'river').length
            }
        };
        
        const dataStr = JSON.stringify(terrainData, null, 2);
        
        try {
            navigator.clipboard.writeText(dataStr);
            console.log('📄 Terrain data copied to clipboard');
            
            // Visual feedback
            const button = document.getElementById('export-terrain');
            const originalText = button.textContent;
            button.textContent = '✅ Copied!';
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
            
        } catch (err) {
            console.log('📄 Terrain export:', dataStr);
            alert('Terrain data logged to console');
        }
    }
    
    randomizeTerrain() {
        if (!this.gameInstance) return;
        
        // Random counts
        const treesCount = 15 + Math.floor(Math.random() * 40);
        const mountainsCount = 5 + Math.floor(Math.random() * 15);
        const bushesCount = 20 + Math.floor(Math.random() * 60);
        
        // Update sliders
        document.getElementById('terrain-trees').value = treesCount;
        document.getElementById('terrain-trees-input').value = treesCount;
        document.getElementById('terrain-mountains').value = mountainsCount;
        document.getElementById('terrain-mountains-input').value = mountainsCount;
        document.getElementById('terrain-bushes').value = bushesCount;
        document.getElementById('terrain-bushes-input').value = bushesCount;
        
        // Regenerate all
        this.regenerateTerrain('tree', treesCount);
        this.regenerateTerrain('mountain', mountainsCount);
        this.regenerateTerrain('bush', bushesCount);
        this.regenerateRiver();
        
        console.log('🎲 Random terrain generated');
        
        // Visual feedback
        const button = document.getElementById('randomize-terrain');
        const originalText = button.textContent;
        button.textContent = '✅ Random!';
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    }
    
    // Drag & Drop functionality
    handleMouseDown(e) {
        if (!this.gameInstance) {
            console.log('❌ No game instance available');
            return;
        }
        
        console.log('🎯 handleMouseDown called - processing terrain selection');
        
        const rect = this.gameInstance.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        console.log(`🎯 Mouse position: ${x}, ${y}`);
        console.log(`🎯 Available terrain elements: ${this.gameInstance.terrain.length}`);
        
        // Find clicked terrain element
        let clickedElement = null;
        let minDistance = Infinity;
        
        this.gameInstance.terrain.forEach((item, index) => {
            if (item.type !== 'river') {
                let hitRadius = item.size || 20; // Default size
                
                // Spezielle Behandlung für Brücke
                if (item.type === 'bridge') {
                    hitRadius = Math.max(item.width, item.height) / 2;
                }
                
                const distance = Math.sqrt((x - item.x) ** 2 + (y - item.y) ** 2);
                console.log(`🎯 Checking ${item.type} at (${Math.round(item.x)}, ${Math.round(item.y)}) - distance: ${Math.round(distance)}, radius: ${hitRadius}`);
                
                if (distance < hitRadius && distance < minDistance) {
                    minDistance = distance;
                    clickedElement = { item, index };
                    console.log(`✅ Found clickable element: ${item.type}`);
                }
            }
        });
        
        if (clickedElement) {
            this.selectedElement = clickedElement;
            this.isDragging = true;
            this.dragOffset.x = x - clickedElement.item.x;
            this.dragOffset.y = y - clickedElement.item.y;
            
            // Update selection info
            this.updateSelectionInfo();
            
            // Visual feedback
            this.gameInstance.canvas.style.cursor = 'grabbing';
            
            console.log('🎯 Selected:', clickedElement.item.type, 'at', clickedElement.item.x, clickedElement.item.y);
        } else {
            console.log('❌ No terrain element found at click position');
            this.selectedElement = null;
            this.updateSelectionInfo();
        }
    }
    
    handleMouseMove(e) {
        if (!this.gameInstance) return;
        
        const rect = this.gameInstance.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        if (this.isDragging && this.selectedElement) {
            // Update position
            this.selectedElement.item.x = x - this.dragOffset.x;
            this.selectedElement.item.y = y - this.dragOffset.y;
            
            // Keep within canvas bounds
            this.selectedElement.item.x = Math.max(this.selectedElement.item.size, 
                Math.min(this.gameInstance.canvas.width - this.selectedElement.item.size, this.selectedElement.item.x));
            this.selectedElement.item.y = Math.max(this.selectedElement.item.size, 
                Math.min(this.gameInstance.canvas.height - this.selectedElement.item.size, this.selectedElement.item.y));
            
            // Update info display
            this.updateSelectionInfo();
        } else {
            // Check if hovering over draggable element
            let hoveringElement = false;
            this.gameInstance.terrain.forEach(item => {
                if (item.type !== 'river') {
                    const distance = Math.sqrt((x - item.x) ** 2 + (y - item.y) ** 2);
                    if (distance < item.size) {
                        hoveringElement = true;
                    }
                }
            });
            
            this.gameInstance.canvas.style.cursor = hoveringElement ? 'grab' : 'default';
        }
    }
    
    handleMouseUp(e) {
        if (this.isDragging) {
            this.isDragging = false;
            this.gameInstance.canvas.style.cursor = 'grab';
            
            if (this.selectedElement) {
                console.log('🎯 Moved:', this.selectedElement.item.type, 'to', 
                    Math.round(this.selectedElement.item.x), Math.round(this.selectedElement.item.y));
            }
        }
    }
    
    updateSelectionInfo() {
        const infoDiv = document.getElementById('selected-info');
        
        if (this.selectedElement) {
            const item = this.selectedElement.item;
            let sizeInfo = '';
            
            if (item.type === 'bridge') {
                sizeInfo = `
                    <div style="margin-bottom: 4px;">
                        <strong>Width:</strong> ${Math.round(item.width)}px
                    </div>
                    <div style="margin-bottom: 4px;">
                        <strong>Height:</strong> ${Math.round(item.height)}px
                    </div>
                    <div style="margin-bottom: 4px;">
                        <strong>Angle:</strong> ${Math.round(item.angle * 180 / Math.PI)}°
                    </div>
                `;
            } else {
                sizeInfo = `
                    <div style="margin-bottom: 4px;">
                        <strong>Size:</strong> ${Math.round(item.size)}
                    </div>
                `;
            }
            
            infoDiv.innerHTML = `
                <div style="color: #64b5f6; font-weight: bold; margin-bottom: 8px;">
                    ${this.getElementEmoji(item.type)} ${item.type.toUpperCase()}
                </div>
                <div style="margin-bottom: 4px;">
                    <strong>X:</strong> ${Math.round(item.x)}px
                </div>
                <div style="margin-bottom: 4px;">
                    <strong>Y:</strong> ${Math.round(item.y)}px
                </div>
                ${sizeInfo}
                <div style="font-size: 10px; color: #94a3b8; margin-top: 8px;">
                    💡 Drag to move, or copy position below
                </div>
            `;
        } else {
            infoDiv.innerHTML = 'Select an element in Drag & Drop mode to see coordinates...';
        }
    }
    
    getElementEmoji(type) {
        const emojis = {
            'tree': '🌳',
            'mountain': '⛰️',
            'bush': '🌿',
            'river': '🌊',
            'bridge': '🌉'
        };
        return emojis[type] || '❓';
    }
    
    copyAllPositions() {
        if (!this.gameInstance) return;
        
        const positions = {};
        this.gameInstance.terrain.forEach((item, index) => {
            if (!positions[item.type]) {
                positions[item.type] = [];
            }
            positions[item.type].push({
                x: Math.round(item.x),
                y: Math.round(item.y),
                size: Math.round(item.size)
            });
        });
        
        const positionData = {
            timestamp: new Date().toISOString(),
            canvas_size: {
                width: this.gameInstance.canvas.width,
                height: this.gameInstance.canvas.height
            },
            terrain_positions: positions
        };
        
        const dataStr = JSON.stringify(positionData, null, 2);
        
        try {
            navigator.clipboard.writeText(dataStr);
            console.log('📋 All positions copied to clipboard');
            
            // Visual feedback
            const button = document.getElementById('copy-positions');
            const originalText = button.textContent;
            button.textContent = '✅ Copied!';
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
            
        } catch (err) {
            console.log('📋 All positions:', dataStr);
            alert('Position data logged to console');
        }
    }
    
    copySelectedPosition() {
        if (!this.selectedElement) {
            alert('No element selected! Switch to Drag & Drop mode and click an element first.');
            return;
        }
        
        const item = this.selectedElement.item;
        const positionData = {
            type: item.type,
            x: Math.round(item.x),
            y: Math.round(item.y),
            size: Math.round(item.size),
            timestamp: new Date().toISOString()
        };
        
        const dataStr = JSON.stringify(positionData, null, 2);
        
        try {
            navigator.clipboard.writeText(dataStr);
            console.log('📋 Selected position copied:', positionData);
            
            // Visual feedback
            const button = document.getElementById('copy-selected');
            const originalText = button.textContent;
            button.textContent = '✅ Copied!';
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
            
        } catch (err) {
            console.log('📋 Selected position:', dataStr);
            alert('Position data logged to console');
        }
    }
    
    loadCustomTerrain() {
        if (!this.gameInstance) return;
        
        // Reload the custom predefined terrain
        this.gameInstance.terrain = [];
        this.gameInstance.loadPredefinedTerrain();
        
        console.log('🎨 Custom terrain layout reloaded');
        
        // Visual feedback
        const button = document.getElementById('load-custom-terrain');
        const originalText = button.textContent;
        button.textContent = '✅ Loaded!';
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    }
    
    // UI Panel Dragging System
    enableUIDragging() {
        Object.keys(this.elements).forEach(key => {
            const element = this.elements[key].element;
            if (element) {
                this.makeElementDraggable(element, key);
            }
        });
    }
    
    disableUIDragging() {
        Object.keys(this.elements).forEach(key => {
            const element = this.elements[key].element;
            if (element) {
                this.removeElementDragging(element);
            }
        });
    }
    
    makeElementDraggable(element, elementKey) {
        // Add visual indicators
        element.classList.add('ui-draggable');
        
        // Add drag hint
        const dragHint = document.createElement('div');
        dragHint.className = 'ui-drag-hint';
        dragHint.textContent = '⋮⋮';
        dragHint.id = `drag-hint-${elementKey}`;
        element.appendChild(dragHint);
        
        // Mouse event handlers with proper priority
        const mouseDownHandler = (e) => {
            // Only handle UI dragging if we're clicking on the element itself or drag hint
            if (e.target === element || e.target.classList.contains('ui-drag-hint') || 
                e.target.tagName === 'H3' || e.target.tagName === 'P' || e.target.tagName === 'STRONG') {
                
                // Stop propagation to prevent terrain dragging
                e.stopPropagation();
                this.startUIDrag(e, element, elementKey);
            }
        };
        
        // Use capture phase to handle UI dragging first
        element.addEventListener('mousedown', mouseDownHandler, true);
        element._mouseDownHandler = mouseDownHandler; // Store for cleanup
    }
    
    removeElementDragging(element) {
        element.classList.remove('ui-draggable', 'ui-dragging');
        
        // Remove drag hint
        const dragHint = element.querySelector('.ui-drag-hint');
        if (dragHint) {
            dragHint.remove();
        }
        
        // Remove event listener with same capture setting
        if (element._mouseDownHandler) {
            element.removeEventListener('mousedown', element._mouseDownHandler, true);
            delete element._mouseDownHandler;
        }
    }
    
    startUIDrag(e, element, elementKey) {
        e.preventDefault();
        
        this.uiDragState.isDragging = true;
        this.uiDragState.element = { element, key: elementKey };
        this.uiDragState.startX = e.clientX;
        this.uiDragState.startY = e.clientY;
        
        // Calculate offset from mouse to element top-left
        const rect = element.getBoundingClientRect();
        this.uiDragState.offsetX = e.clientX - rect.left;
        this.uiDragState.offsetY = e.clientY - rect.top;
        
        element.classList.add('ui-dragging');
        
        // Add global mouse handlers
        document.addEventListener('mousemove', this.handleUIDragMove.bind(this));
        document.addEventListener('mouseup', this.handleUIDragEnd.bind(this));
        
        console.log('🎯 Started dragging UI element:', elementKey);
    }
    
    handleUIDragMove(e) {
        if (!this.uiDragState.isDragging) return;
        
        const element = this.uiDragState.element.element;
        const key = this.uiDragState.element.key;
        
        // Calculate new position
        let newX = e.clientX - this.uiDragState.offsetX;
        let newY = e.clientY - this.uiDragState.offsetY;
        
        // Keep within viewport bounds
        const maxX = window.innerWidth - element.offsetWidth;
        const maxY = window.innerHeight - element.offsetHeight;
        
        newX = Math.max(0, Math.min(maxX, newX));
        newY = Math.max(0, Math.min(maxY, newY));
        
        // Apply new position
        element.style.position = 'fixed';
        element.style.left = `${newX}px`;
        element.style.top = `${newY}px`;
        
        // Clear any right positioning for elements that use it
        if (key === 'characterInfo') {
            element.style.right = 'auto';
        }
        
        // Update debug controls in real-time
        this.updateControlsFromCurrentPosition(key, newX, newY);
    }
    
    handleUIDragEnd(e) {
        if (!this.uiDragState.isDragging) return;
        
        const element = this.uiDragState.element.element;
        const key = this.uiDragState.element.key;
        
        element.classList.remove('ui-dragging');
        
        // Remove global handlers
        document.removeEventListener('mousemove', this.handleUIDragMove.bind(this));
        document.removeEventListener('mouseup', this.handleUIDragEnd.bind(this));
        
        // Final position update
        const rect = element.getBoundingClientRect();
        console.log(`🎯 UI element ${key} moved to: ${Math.round(rect.left)}, ${Math.round(rect.top)}`);
        
        // Update CSS preview
        this.updateCSSPreview();
        
        // Reset drag state
        this.uiDragState.isDragging = false;
        this.uiDragState.element = null;
    }
    
    updateControlsFromCurrentPosition(elementKey, x, y) {
        // Update sliders and inputs to match current position
        const topSlider = document.getElementById(`${elementKey}-top`);
        const leftSlider = document.getElementById(`${elementKey}-left`);
        const rightSlider = document.getElementById(`${elementKey}-right`);
        const topInput = document.getElementById(`${elementKey}-top-input`);
        const leftInput = document.getElementById(`${elementKey}-left-input`);
        const rightInput = document.getElementById(`${elementKey}-right-input`);
        
        if (topSlider && topInput) {
            topSlider.value = Math.round(y);
            topInput.value = Math.round(y);
        }
        
        if (leftSlider && leftInput) {
            leftSlider.value = Math.round(x);
            leftInput.value = Math.round(x);
        }
        
        // For right-positioned elements, calculate right offset
        if (rightSlider && rightInput && elementKey === 'characterInfo') {
            const rightOffset = window.innerWidth - x - this.elements[elementKey].element.offsetWidth;
            rightSlider.value = Math.max(0, Math.round(rightOffset));
            rightInput.value = Math.max(0, Math.round(rightOffset));
        }
    }
    
    // Panel visibility toggle functions
    togglePanelVisibility() {
        const panel = document.getElementById('debugPanel');
        const floatingControls = document.getElementById('floatingControls');
        
        if (this.isVisible) {
            // Hide panel, show floating controls
            panel.style.display = 'none';
            floatingControls.style.display = 'flex';
            this.isVisible = false;
            console.log('📱 Debug panel hidden, terrain now accessible');
        } else {
            // Show panel, hide floating controls
            panel.style.display = 'block';
            floatingControls.style.display = 'none';
            this.isVisible = true;
            console.log('📱 Debug panel shown');
        }
    }
    
    showPanelFromFloat() {
        const panel = document.getElementById('debugPanel');
        const floatingControls = document.getElementById('floatingControls');
        
        // Show panel, hide floating controls
        panel.style.display = 'block';
        floatingControls.style.display = 'none';
        this.isVisible = true;
        console.log('📱 Debug panel restored from floating controls');
    }

    // Make Debug Panel draggable
    makeDebugPanelDraggable() {
        let isDragging = false;
        let startX, startY, startLeft, startTop;
        
        const header = this.debugPanel.querySelector('h2');
        
        header.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            
            const rect = this.debugPanel.getBoundingClientRect();
            startLeft = rect.left;
            startTop = rect.top;
            
            this.debugPanel.style.cursor = 'grabbing';
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;
            
            let newLeft = startLeft + deltaX;
            let newTop = startTop + deltaY;
            
            // Keep within viewport
            const maxLeft = window.innerWidth - this.debugPanel.offsetWidth;
            const maxTop = window.innerHeight - this.debugPanel.offsetHeight;
            
            newLeft = Math.max(0, Math.min(maxLeft, newLeft));
            newTop = Math.max(0, Math.min(maxTop, newTop));
            
            this.debugPanel.style.left = `${newLeft}px`;
            this.debugPanel.style.top = `${newTop}px`;
            this.debugPanel.style.right = 'auto';
            this.debugPanel.style.transform = 'none';
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                this.debugPanel.style.cursor = 'move';
            }
        });
    }
}

// Initialize when DOM is loaded
window.addEventListener('DOMContentLoaded', () => {
    window.debugManager = new UIDebugManager();
});