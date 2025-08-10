class VillageAI {
    constructor() {
        console.log('🎮 Starting VillageAI...');
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        // Stelle sicher, dass globale Referenz existiert bevor andere Systeme zugreifen
        if (typeof window !== 'undefined') {
            window.gameInstance = this;
        }
        
        // Einzelne Charakter-Sprites System
        this.sprites = {
            characters: [],  // Array von einzelnen Character-Images
            loaded: false,
            everWorked: false
        };
        this.loadCharacterSprites();
        
        // Vegetation und Umgebungs-Assets
        this.vegetation = {
            trees: [],
            bushes: [],
            loaded: false
        };
        this.loadVegetationAssets();
        
        // Terrain-Tiles System
        this.terrainTiles = {
            grass: null,
            water: null,
            sand: null,
            stone: null,
            loaded: false
        };
        this.loadTerrainTiles();
        
        if (!this.canvas || !this.ctx) {
            console.error('❌ Canvas or context not found!');
            return;
        }
        
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        console.log(`📐 Canvas size: ${this.canvas.width}x${this.canvas.height}`);

        this.gameTime = 480; // 08:00 in Minuten seit Mitternacht
        this.day = 1;
        this.resources = { food: 20, wood: 15 };
        // Intro Sequenz State
        this.introPhase = {
            active: true,
            stage: 0, // 0 Kreis formieren, 1 Dialog, 2 Entscheidung, 3 Fade, 4 fertig
            startTime: Date.now(),
            messages: [
                {speaker:0,text:'Wo sind wir gelandet?'},
                {speaker:1,text:'Sieht nach einer guten Stelle für ein Dorf aus.'},
                {speaker:2,text:'Wir brauchen Schutz – Hütten.'},
                {speaker:3,text:'Einverstanden, planen wir Häuser.'},
                {speaker:0,text:'Ich suche Bauplätze.'},
                {speaker:1,text:'Wir sammeln Holz.'}
            ],
            msgIndex:0,
            lastMsgTime:0,
            currentMessage:null,
            currentSpeaker:null,
            circleRadius:90,
            placedHouseSites:false
        };
    // Kamera
    this.camera = { x: 0, y: 0, zoom: 1, targetZoom:1 };
    // Gebäude / Strukturen
    this.structures = []; // {type:'house', x,y,width,height,progress,completed,owner}
    this._riverCache = null; // cache for river point array
    this.animals = []; // wildlife entities
    // Lagerfeuer
    this.fires = []; // {x,y,radius,startTime,duration,intensity}

        this.terrain = [];
        this.characters = [];
        this.particles = [];
        this.ambientLight = 0.8;
        this.windDirection = { x: 0.1, y: 0.05 };

        // Neues soziales System (jugendfrei, keine expliziten Inhalte)
        this.socialSystem = {
            relationships: {},          // key: "A|B" -> { affinity: -100..100, trust:0..100, lastInteraction, bondLevel }
            influence: {},              // characterName -> Einflusswert
            tribes: [],                 // { id, members:[names], leader, cohesion }
            pendingBirths: [],          // { parents:[nameA,nameB], dueTime, childTemplate }
            storyLog: []                // Letzte erzählte Geschichten
        };

    // Neues Gesprächs-/Gedächtnissystem
    this.activeConversations = [];      // Laufende Gespräche { id, participants:[a,b], lines:[{speaker,text,topic}], lineIndex, nextLineTime, topic, startedAt }
    this.conversationLog = [];          // Globale letzten Gesprächszeilen { time, speaker, partner, topic, text }
    // ERWEITERTE GESPRÄCHSTHEMEN für intelligentere Charaktere
    this.conversationTopics = [
        'wetter','nahrung','wasser','energie',
        'planung','erinnerung','rolle','anführer','stamm','umgebung','allgemein',
        // Neue sinnvolle Themen
        'future_plans', 'village_development', 'personal_goals', 'shared_projects',
        'meta_awareness', 'philosophy', 'cooperation', 'resource_sharing',
        'collective_decision', 'skill_learning', 'relationship_reflection', 'purpose'
    ];

        console.log('🚀 Initializing game systems...');
        this.init();
        // Bottom Navigation initialisieren (nach DOM-Inhalten)
        this.setupBottomNav();
        this.gameLoop();
    }

    // Bottom Navigation Bar Steuerung
    setupBottomNav(){
        if (this._bottomNavReady) return; // nur einmal
        const nav = document.getElementById('bottomNav');
        if (!nav) return;
    const panelIds = ['ui','characterInfo','buildControls','aiDashboard','aiConfigPanel','debugPanel','charChat'];
        const getPanel = id => document.getElementById(id);
        const togglePanel = (id)=>{
            let panel = getPanel(id);
            // AI Dashboard kann später generiert werden; sicherstellen dass Instanz existiert
            if (id==='aiDashboard' && !panel) {
                if (window.aiDashboard) {
                    panel = document.getElementById('aiDashboard');
                } else if (typeof AIMonitoringDashboard !== 'undefined') {
                    window.aiDashboard = new AIMonitoringDashboard();
                    panel = document.getElementById('aiDashboard');
                }
            }
            if (!panel && id==='aiConfigPanel' && window.aiConfig) {
                panel = document.getElementById('aiConfigPanel');
            }
            if (!panel) return;
            const visible = !panel.classList.contains('panel-hidden') && panel.style.display !== 'none';
            // Einheitliche Behandlung für Chat jetzt auch über Klassen
            if (visible) {
                if (id==='aiDashboard' && window.aiDashboard) window.aiDashboard.hide();
                if (id==='aiConfigPanel' && window.aiConfig) window.aiConfig.hideConfigPanel();
                panel.classList.add('panel-hidden');
                panel.classList.remove('panel-visible');
            } else {
                panel.classList.remove('panel-hidden');
                panel.classList.add('panel-visible');
                if (id==='aiDashboard' && window.aiDashboard) window.aiDashboard.show();
                if (id==='aiConfigPanel' && window.aiConfig) window.aiConfig.showConfigPanel();
                if (id==='charChat') this._repositionChat();
            }
        };
        // Initial Panels als sichtbar markieren
        panelIds.forEach(pid=>{
            const p = getPanel(pid);
            if (!p) return;
            if (!p.classList.contains('panel-hidden') && !p.classList.contains('panel-visible')) {
                p.classList.add('panel-visible');
            }
        });
        nav.querySelectorAll('button[data-panel]').forEach(btn=>{
            btn.addEventListener('click', ()=>{
                const id = btn.getAttribute('data-panel');
                togglePanel(id);
                // Active styling exklusiv
                nav.querySelectorAll('button').forEach(b=> b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
        this._bottomNavReady = true;
        // Initial Chat-Position anpassen
        this._repositionChat();
    }

    _repositionChat(){
        const chat = document.getElementById('charChat');
        const nav = document.getElementById('bottomNav');
        if (!chat || !nav) return;
        const navHeight = nav.getBoundingClientRect().height;
        chat.style.bottom = (navHeight + 14) + 'px';
    }
    
    // Einzelne Charakter-Sprites Loader
    loadCharacterSprites() {
        console.log('🔄 Loading individual character sprites...');
        const characterFiles = ['char1.png', 'char2.png', 'char3.png', 'char4.png'];
        let loadedCount = 0;
        
        // Gender mapping for sprites
        this.sprites.characterGenders = [
            'male',    // char1 - Male with pink shirt
            'female',  // char2 - Female with blue dress  
            'female',  // char3 - Female with yellow/green outfit
            'female'   // char4 - Female with purple dress
        ];
        
        characterFiles.forEach((filename, index) => {
            const img = new Image();
            img.onload = () => {
                loadedCount++;
                console.log(`✅ Character ${index + 1} loaded: ${filename} (${img.width}x${img.height}) - ${this.sprites.characterGenders[index]}`);
                if (loadedCount === characterFiles.length) {
                    this.sprites.loaded = true;
                    console.log('🎉 All character sprites loaded successfully!');
                    // Assign sprites to characters based on gender
                    this.assignSpritesByGender();
                }
            };
            img.onerror = () => {
                console.error(`❌ Failed to load ${filename}`);
            };
            img.src = filename;
            this.sprites.characters[index] = img;
        });
    }
    
    // Vegetation Assets Loader
    loadVegetationAssets() {
        console.log('🌲 Loading vegetation assets...');
        
        const treeFiles = [
            'palm-tree.png', 'fir.png', 'pear-tree.png', 'red-tree.png', 
            'wide-tree.png', 'snowy-tree.png', 'palm-tree2.png'
        ];
        
        const bushFiles = [
            'berry-bush.png', 'herbs.png', 'thorn-bush.png', 'thick-leafes.png',
            'bush-low.png', 'dry-slim-bush1.png', 'olive-bush.png', 'thin-bush.png'
        ];
        
        let totalAssets = treeFiles.length + bushFiles.length;
        let loadedAssets = 0;
        
        // Load trees
        treeFiles.forEach((filename, index) => {
            const img = new Image();
            img.onload = () => {
                console.log(`🌳 Tree loaded: ${filename}`);
                loadedAssets++;
                if (loadedAssets === totalAssets) {
                    this.vegetation.loaded = true;
                    console.log('🌿 All vegetation assets loaded!');
                    this.generateRandomVegetation();
                }
            };
            img.onerror = () => console.error(`❌ Failed to load tree: ${filename}`);
            img.src = filename;
            this.vegetation.trees[index] = img;
        });
        
        // Load bushes
        bushFiles.forEach((filename, index) => {
            const img = new Image();
            img.onload = () => {
                console.log(`🌿 Bush loaded: ${filename}`);
                loadedAssets++;
                if (loadedAssets === totalAssets) {
                    this.vegetation.loaded = true;
                    console.log('🌿 All vegetation assets loaded!');
                    this.generateRandomVegetation();
                }
            };
            img.onerror = () => console.error(`❌ Failed to load bush: ${filename}`);
            img.src = filename;
            this.vegetation.bushes[index] = img;
        });
    }
    
    // Generiere zufällige Vegetation in der Welt
    generateRandomVegetation() {
        console.log('🌍 Generating random vegetation...');
        
        if (!this.worldVegetation) {
            this.worldVegetation = [];
        }
        
        // Verteile Bäume und Büsche zufällig in der Welt
        const worldSize = 2000; // Größe der Spielwelt
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        // Bäume (winzig klein!)
        for (let i = 0; i < 15; i++) {
            this.worldVegetation.push({
                type: 'tree',
                x: centerX + (Math.random() - 0.5) * worldSize,
                y: centerY + (Math.random() - 0.5) * worldSize,
                spriteIndex: Math.floor(Math.random() * this.vegetation.trees.length),
                scale: 0.08 + Math.random() * 0.12, // ULTRA WINZIG: 0.08x - 0.2x
                resources: Math.floor(Math.random() * 3) + 2 // 2-4 wood
            });
        }
        
        // Büsche (mini winzig!)
        for (let i = 0; i < 30; i++) {
            this.worldVegetation.push({
                type: 'bush',
                x: centerX + (Math.random() - 0.5) * worldSize,
                y: centerY + (Math.random() - 0.5) * worldSize,
                spriteIndex: Math.floor(Math.random() * this.vegetation.bushes.length),
                scale: 0.06 + Math.random() * 0.1, // MIKRO: 0.06x - 0.16x
                resources: Math.floor(Math.random() * 2) + 1, // 1-2 food
                harvestable: Math.random() < 0.7 // 70% haben Beeren/Kräuter
            });
        }
        
        console.log(`🌱 Generated ${this.worldVegetation.length} vegetation objects`);
    }
    
    // Terrain-Tiles Loader
    loadTerrainTiles() {
        console.log('🗻 Loading terrain tiles...');
        
        const tileFiles = {
            grass: 'seamless-64px-rpg-tiles-1.1.0/grass.png',
            water: 'seamless-64px-rpg-tiles-1.1.0/water.png',
            sand: 'seamless-64px-rpg-tiles-1.1.0/sand.png',
            stone: 'seamless-64px-rpg-tiles-1.1.0/stone tile.png'
        };
        
        let loadedTiles = 0;
        const totalTiles = Object.keys(tileFiles).length;
        
        Object.entries(tileFiles).forEach(([tileType, filename]) => {
            const img = new Image();
            img.onload = () => {
                console.log(`🏞️ Terrain tile loaded: ${tileType}`);
                loadedTiles++;
                if (loadedTiles === totalTiles) {
                    this.terrainTiles.loaded = true;
                    console.log('🌍 All terrain tiles loaded!');
                }
            };
            img.onerror = () => console.error(`❌ Failed to load terrain tile: ${filename}`);
            img.src = filename;
            this.terrainTiles[tileType] = img;
        });
    }
    
    // Zeichne Vegetation (Bäume und Büsche)
    drawVegetation() {
        if (!this.vegetation.loaded || !this.worldVegetation) {
            return;
        }
        
        // Zeichne nur sichtbare Vegetation (performance optimization)
        const cameraX = -this.camera.offsetX / this.camera.zoom;
        const cameraY = -this.camera.offsetY / this.camera.zoom;
        const viewWidth = this.canvas.width / this.camera.zoom;
        const viewHeight = this.canvas.height / this.camera.zoom;
        
        this.worldVegetation.forEach(vegetation => {
            // Culling - nur zeichnen wenn im sichtbaren Bereich
            if (vegetation.x < cameraX - 100 || vegetation.x > cameraX + viewWidth + 100 ||
                vegetation.y < cameraY - 100 || vegetation.y > cameraY + viewHeight + 100) {
                return;
            }
            
            const sprite = vegetation.type === 'tree' ? 
                this.vegetation.trees[vegetation.spriteIndex] : 
                this.vegetation.bushes[vegetation.spriteIndex];
                
            if (!sprite || !sprite.complete) return;
            
            const originalWidth = sprite.width;
            const originalHeight = sprite.height;
            const scale = vegetation.scale;
            const destWidth = originalWidth * scale;
            const destHeight = originalHeight * scale;
            
            // Schatten für Bäume
            if (vegetation.type === 'tree') {
                this.ctx.save();
                this.ctx.globalAlpha = 0.3;
                this.ctx.fillStyle = '#00000040';
                this.ctx.beginPath();
                this.ctx.ellipse(
                    vegetation.x + 5, 
                    vegetation.y + destHeight * 0.8, 
                    destWidth * 0.3, 
                    destHeight * 0.1, 
                    0, 0, Math.PI * 2
                );
                this.ctx.fill();
                this.ctx.restore();
            }
            
            // Zeichne Vegetation-Sprite
            this.ctx.drawImage(
                sprite,
                vegetation.x - destWidth / 2,
                vegetation.y - destHeight / 2,
                destWidth,
                destHeight
            );
            
            // Ressourcen-Indikator für erntbare Büsche
            if (vegetation.type === 'bush' && vegetation.harvestable && vegetation.resources > 0) {
                this.ctx.save();
                this.ctx.fillStyle = '#FF6B6B';
                this.ctx.font = '12px Arial';
                this.ctx.textAlign = 'center';
                this.ctx.globalAlpha = 0.8;
                this.ctx.fillText('🍓', vegetation.x, vegetation.y - destHeight / 2 - 10);
                this.ctx.restore();
            }
        });
    }
    
    // Fluss mit Wasser-Tiles zeichnen
    drawRiverWithTiles(river) {
        if (!this.terrainTiles.loaded || !this.terrainTiles.water) {
            // Fallback: alter Fluss
            this.drawOldRiver(river);
            return;
        }
        
        const tileSize = 64;
        const riverWidth = river.width || 60;
        
        // Für jeden Punkt im Fluss
        for (let i = 0; i < river.points.length - 1; i++) {
            const currentPoint = river.points[i];
            const nextPoint = river.points[i + 1];
            
            // Berechne Richtung zwischen Punkten
            const dx = nextPoint.x - currentPoint.x;
            const dy = nextPoint.y - currentPoint.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const steps = Math.ceil(distance / (tileSize * 0.5)); // Überlappung für nahtlosen Fluss
            
            // Zeichne Wasser-Tiles entlang der Linie
            for (let step = 0; step <= steps; step++) {
                const t = step / steps;
                const x = currentPoint.x + dx * t;
                const y = currentPoint.y + dy * t;
                
                // Berechne senkrechte Richtung für Flussbreite
                const perpX = -dy / distance;
                const perpY = dx / distance;
                
                // Zeichne Wasser-Tiles quer zur Flussrichtung
                const tilesAcross = Math.ceil(riverWidth / tileSize);
                for (let j = -tilesAcross; j <= tilesAcross; j++) {
                    const tileX = x + perpX * j * tileSize;
                    const tileY = y + perpY * j * tileSize;
                    
                    // Nur zeichnen wenn innerhalb der Flussbreite
                    const distanceFromCenter = Math.abs(j * tileSize);
                    if (distanceFromCenter <= riverWidth / 2) {
                        this.ctx.drawImage(
                            this.terrainTiles.water,
                            tileX - tileSize / 2,
                            tileY - tileSize / 2,
                            tileSize,
                            tileSize
                        );
                    }
                }
            }
        }
    }
    
    // Fallback für alten Fluss
    drawOldRiver(river) {
        this.ctx.strokeStyle = '#4A90E2';
        this.ctx.lineWidth = river.width || 40;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        
        this.ctx.beginPath();
        river.points.forEach((point, index) => {
            if (index === 0) {
                this.ctx.moveTo(point.x, point.y);
            } else {
                this.ctx.lineTo(point.x, point.y);
            }
        });
        this.ctx.stroke();
    }
    
    // Sprite-Zuordnung basierend auf Geschlecht
    assignSpritesByGender() {
        console.log('👫 Assigning sprites based on character gender...');
        
        // Get available sprite indices by gender
        const maleSprites = [];
        const femaleSprites = [];
        
        this.sprites.characterGenders.forEach((gender, index) => {
            if (gender === 'male') {
                maleSprites.push(index);
            } else {
                femaleSprites.push(index);
            }
        });
        
        console.log(`Available sprites - Males: [${maleSprites.join(', ')}], Females: [${femaleSprites.join(', ')}]`);
        
        // Assign sprites to characters mit besserer Verteilung
        let maleCounter = 0;
        let femaleCounter = 0;
        
        this.characters.forEach((character, charIndex) => {
            let spriteIndex;
            
            if (character.gender === 'male') {
                // Männer bekommen char1 (Index 0)
                spriteIndex = maleSprites[maleCounter % maleSprites.length];
                maleCounter++;
            } else {
                // Frauen bekommen rotierend char2, char3, char4 (Indices 1, 2, 3)
                spriteIndex = femaleSprites[femaleCounter % femaleSprites.length];
                femaleCounter++;
            }
            
            character.spriteIndex = spriteIndex;
            console.log(`Character ${charIndex + 1} (${character.name}) - ${character.gender} -> sprite ${spriteIndex} (${spriteIndex === 0 ? 'char1' : 'char' + (spriteIndex + 1)})`);
        });
    }
    
    // Einzelne Charakter-Sprites zeichnen
    drawCharacterSprite(x, y, spriteIndex, scale = 1) {
        // Debug nur beim ersten Aufruf
        if (!this._spriteDebugLogged) {
            console.log(`🔍 SPRITE DEBUG: loaded=${this.sprites.loaded}, characters.length=${this.sprites.characters.length}`);
            this._spriteDebugLogged = true;
        }
        
        // Prüfe ob Sprites geladen sind
        if (!this.sprites.loaded || !this.sprites.characters.length) {
            return false;
        }
        
        // Verwende spriteIndex um zwischen den 4 Charakteren zu wählen
        const characterIndex = spriteIndex % 4; // 0-3 für char1-char4
        const characterImage = this.sprites.characters[characterIndex];
        
        if (!characterImage || !characterImage.complete) {
            return false;
        }
        
        // Originale Sprite-Größe beibehalten - keine Verzerrung!
        const originalWidth = characterImage.width;
        const originalHeight = characterImage.height;
        const destWidth = originalWidth * scale;
        const destHeight = originalHeight * scale;
        
        try {
            this.ctx.drawImage(
                characterImage,
                0, 0, originalWidth, originalHeight,  // Ganzes Bild verwenden
                x - destWidth/2, y - destHeight/2, destWidth, destHeight  // Proportionale Größe
            );
            
            // Debug: Roter Rahmen um Sprites (proportional)
            if (this._showSpriteDebug) {
                this.ctx.strokeStyle = 'red';
                this.ctx.lineWidth = 2;
                this.ctx.strokeRect(x - destWidth/2, y - destHeight/2, destWidth, destHeight);
            }
            
            // Debug beim ersten erfolgreichen Sprite
            if (!this._firstSpriteDrawn) {
                console.log(`🎨 Erstes Character Sprite gezeichnet! char${characterIndex + 1} (${originalWidth}x${originalHeight})`);
                console.log(`📍 Position: ${x},${y}, Größe: ${destWidth}x${destHeight} (proportional!)`);
                this._firstSpriteDrawn = true;
                this._showSpriteDebug = true;
                this.sprites.everWorked = true;
                console.log(`✅ CHARACTER SPRITES AKTIV - Keine Verzerrung mehr!`);
            }
            
            return true;
        } catch (e) {
            console.error('❌ Fehler beim Zeichnen des Character Sprites:', e);
            return false;
        }
    }
    
    // ==== Dynamisches Gesprächssystem ====
    tryStartConversationPair() {
        // Finde zwei Charaktere, die nicht bereits sprechen und nahe beieinander sind
        const available = this.characters.filter(c => c.currentAction === 'idle' && (c.conversationCooldown||0) === 0);
        for (let i=0;i<available.length;i++) {
            for (let j=i+1;j<available.length;j++) {
                const A = available[i];
                const B = available[j];
                const dist = Math.hypot(A.x-B.x, A.y-B.y);
                if (dist < 140 && !this.isInConversation(A) && !this.isInConversation(B)) {
                    this.startConversation(A,B);
                    return;
                }
            }
        }
    }

    isInConversation(char) {
        return this.activeConversations.some(c => c.participants.includes(char.name));
    }

    startConversation(a,b) {
        const topic = this.pickConversationTopic(a,b);
        const conv = {
            id: 'conv_'+Date.now()+'_'+Math.floor(Math.random()*1000),
            participants: [a.name,b.name],
            lines: [],
            lineIndex: 0,
            nextLineTime: Date.now(),
            topic,
            startedAt: Date.now()
        };
        this.activeConversations.push(conv);
        a.currentAction = 'talking';
        b.currentAction = 'talking';
        a.thoughts = [`Ich rede mit ${b.name.split(' ')[0]} über ${topic}.`];
        b.thoughts = [`Ich rede mit ${a.name.split(' ')[0]} über ${topic}.`];
        a.conversationCooldown = 400;
        b.conversationCooldown = 400;
        
        // VISUELLE SPRECHBLASEN für beide Charaktere anzeigen
        const firstLine = this.generateConversationLine(a,b,topic,true);
        this.showSpeechBubble(a, {
            text: firstLine,
            type: this.getSpeechTypeForTopic(topic),
            duration: 5000
        });
        
        // Zweiter Charakter antwortet nach kurzer Verzögerung
        setTimeout(() => {
            const secondLine = this.generateConversationLine(b,a,topic,false);
            this.showSpeechBubble(b, {
                text: secondLine,
                type: this.getSpeechTypeForTopic(topic),
                duration: 5000
            });
        }, 2000);
        
        this.appendConversationLine(conv, a.name, firstLine);
    }

    getSpeechTypeForTopic(topic) {
        const metaTopics = ['meta_awareness', 'philosophy', 'purpose'];
        const planningTopics = ['future_plans', 'village_development', 'shared_projects', 'collective_decision'];
        const thoughtTopics = ['personal_goals', 'relationship_reflection'];
        
        if (metaTopics.includes(topic)) return 'meta';
        if (planningTopics.includes(topic)) return 'planning';
        if (thoughtTopics.includes(topic)) return 'thought';
        return 'normal';
    }

    pickConversationTopic(a,b) {
        const pool = [...this.conversationTopics];
        // leichte Gewichtung: Hunger hoch -> Nahrungsthema
        if (a.hunger>70 || b.hunger>70) pool.push('nahrung','nahrung');
        if (a.thirst>70 || b.thirst>70) pool.push('wasser');
        if (this.socialSystem?.currentLeader === a.name || this.socialSystem?.currentLeader === b.name) pool.push('anführer');
        const tribeA = this.socialSystem?.tribes.find(t=>t.members.includes(a.name));
        if (tribeA && tribeA.members.includes(b.name)) pool.push('stamm');
        return pool[Math.floor(Math.random()*pool.length)];
    }

    generateConversationLine(speaker, partner, topic, first=false) {
        // Zugriff auf Beziehung / Erinnerung
        const rel = this.getOrCreateRelationship(speaker.name, partner.name);
        const affinityWord = rel.affinity > 50 ? 'gern' : rel.affinity < -20 ? 'unsicher' : 'okay';
        const shortPartner = partner.name.split(' ')[0];
        const partnerMems = speaker.memories.filter(m => m.actors.includes(partner.name));
        let recalled = null;
        if (partnerMems.length && Math.random()<0.4) {
            const scored = partnerMems.map(m=>({m, score: (Date.now()-m.time<600000?2:1)+(m.affect||0)}));
            scored.sort((a,b)=>b.score-a.score);
            recalled = scored[Math.floor(Math.random()*Math.min(3,scored.length))].m;
        }
        const timeSinceLast = speaker.lastConversationWith?.[partner.name] ? Math.floor((Date.now()-speaker.lastConversationWith[partner.name])/1000) : null;
        switch(topic){
            case 'wetter': return first? `Schönes Licht heute von oben, findest du nicht ${shortPartner}?` : `Das Grün wirkt heute lebendig.`;
            case 'nahrung': return recalled? `Weißt du noch unser Essen damals: ${recalled.summary}?` : (rel.affinity>40? `Wir sollten wieder zusammen Nahrung sammeln.` : `Mein Magen knurrt, hast du etwas?`);
            case 'wasser': return `Weißt du noch eine gute Wasserstelle?`; 
            case 'energie': return timeSinceLast&&timeSinceLast>90? `Seit ${timeSinceLast}s nicht gesprochen, etwas müde.` : `Ich halte durch, auch müde.`;
            case 'planung': return `Vielleicht bauen wir später etwas Nützliches.`;
            case 'erinnerung': return recalled? `Ich denke an ${recalled.summary} mit dir.` : `Weißt du noch, als wir ${this.randomPastEvent()}?`;
            case 'rolle': return `Deine Rolle als ${partner.role||'Mitglied'} passt zu dir.`;
            case 'anführer': return this.socialSystem?.currentLeader===speaker.name? `Ich versuche fair zu führen.` : `Was hältst du vom Anführer?`;
            case 'stamm': return `Unser Stamm fühlt sich stärker an.`;
            case 'umgebung': return `Die Gegend hier ist interessant.`;
            
            // NEUE INTELLIGENTE GESPRÄCHSTHEMEN
            case 'future_plans': 
                return first ? `${shortPartner}, ich denke über unsere Zukunft nach. Was sind deine Pläne?` 
                             : `Ich stelle mir vor, dass wir eines Tages ein richtiges Dorf haben werden.`;
            
            case 'village_development': 
                return first ? `Wir sollten unser Dorf strukturierter aufbauen. Was denkst du?`
                             : `Vielleicht brauchen wir einen zentralen Platz oder einen Markt?`;
            
            case 'personal_goals': 
                return first ? `Ich frage mich manchmal, was mein wahres Ziel hier ist...`
                             : `Manchmal denke ich, ich sollte mehr als nur überleben.`;
            
            case 'shared_projects': 
                return first ? `${shortPartner}, lass uns zusammen etwas Großes schaffen!`
                             : `Gemeinsame Projekte machen mehr Sinn als alleine zu arbeiten.`;
            
            case 'meta_awareness': 
                return first ? `${shortPartner}, hast du manchmal das Gefühl... dass wir beobachtet werden?`
                             : `Diese Welt um uns herum... fühlt sie sich für dich echt an?`;
            
            case 'philosophy': 
                return first ? `Was bedeutet es eigentlich zu existieren, ${shortPartner}?`
                             : `Ich denke, daher bin ich... oder wie war das nochmal?`;
            
            case 'cooperation': 
                return first ? `Zusammenarbeit macht uns alle stärker, findest du nicht?`
                             : `Wenn wir alle zusammenhalten, können wir alles schaffen.`;
            
            case 'resource_sharing': 
                return first ? `Wir sollten unsere Ressourcen gerechter teilen.`
                             : `Niemand sollte hungern, während andere zu viel haben.`;
            
            case 'collective_decision': 
                return first ? `${shortPartner}, wir sollten wichtige Entscheidungen gemeinsam treffen.`
                             : `Demokratie ist besser als ein Diktator, oder?`;
            
            case 'skill_learning': 
                return first ? `Könntest du mir beibringen, was du kannst?`
                             : `Wissen sollte geteilt werden, damit wir alle wachsen.`;
            
            case 'relationship_reflection': 
                return first ? `Ich schätze unsere Freundschaft wirklich, ${shortPartner}.`
                             : `Es ist schön, Menschen zu haben, denen man vertraut.`;
            
            case 'purpose': 
                return first ? `${shortPartner}, was ist unser wahrer Zweck hier?`
                             : `Manchmal frage ich mich, warum wir hier sind...`;
            
            default: return first? `Hallo ${shortPartner}, alles gut?` : `Ja, es geht ${affinityWord}.`;
        }
    }

    randomPastEvent(){
        const opts = ['viel Holz gesammelt','eine gute Stelle entdeckt','eine Idee hatten','ein Feuer gemacht'];
        return opts[Math.floor(Math.random()*opts.length)];
    }

    appendConversationLine(conv, speakerName, text){
        const partnerName = conv.participants.find(p=>p!==speakerName);
        conv.lines.push({speaker:speakerName,text,topic:conv.topic});
        this.conversationLog.push({
            time: Date.now(),
            speaker: speakerName,
            partner: partnerName,
            topic: conv.topic,
            text
        });
        if (this.conversationLog.length>200) this.conversationLog.shift();
        // Beziehung beeinflussen
        const delta = this.evaluateConversationImpact(text, conv.topic);
        this.adjustRelationship(speakerName, partnerName, delta.affinity, delta.trust);
        // Zeige letzten Satz als Gedanken
        const speaker = this.characters.find(c=>c.name===speakerName);
        if (speaker) speaker.thoughts = [text];
        const partner = this.characters.find(c=>c.name===partnerName);
        if (partner && partner.thoughts.length>3) partner.thoughts = partner.thoughts.slice(-3);
        // Memory speichern
        const summary = text.length>80? text.slice(0,77)+'…' : text;
        [speakerName, partnerName].forEach(n => {
            const char = this.characters.find(c=>c.name===n);
            if (!char) return;
            char.memories.push({ time: Date.now(), type:'conversation', actors:[speakerName,partnerName], topic:conv.topic, summary, affect: delta.affinity>0?1:0 });
            if (char.memories.length>120) char.memories.shift();
        });
    }

    // === Laufende Gespräche updaten ===
    updateConversations(){
        if (!this.activeConversations || !this.activeConversations.length) return;
        const now = Date.now();
        for (let i = this.activeConversations.length-1; i>=0; i--) {
            const conv = this.activeConversations[i];
            const [nameA, nameB] = conv.participants;
            const A = this.characters.find(c=>c.name===nameA);
            const B = this.characters.find(c=>c.name===nameB);
            // Abbruchbedingungen
            const maxDuration = 14000; // ms
            if (!A || !B || (now - conv.startedAt) > maxDuration) {
                this.endConversation(conv, A, B);
                this.activeConversations.splice(i,1);
                continue;
            }
            const dist = Math.hypot(A.x-B.x, A.y-B.y);
            if (dist > 200) {
                this.endConversation(conv, A, B);
                this.activeConversations.splice(i,1);
                continue;
            }
            if (now >= conv.nextLineTime) {
                const speaker = (conv.lineIndex % 2 === 0) ? A : B;
                const partner = speaker===A? B : A;
                if (!speaker || !partner) {
                    this.endConversation(conv, A, B);
                    this.activeConversations.splice(i,1);
                    continue;
                }
                const line = this.generateConversationLine(speaker, partner, conv.topic, false);
                this.appendConversationLine(conv, speaker.name, line);
                conv.lineIndex++;
                conv.nextLineTime = now + 1200 + Math.random()*1600;
            }
        }
    }

    endConversation(conv, A, B){
        [A,B].forEach(ch => {
            if (!ch) return;
            if (ch.currentAction === 'talking') ch.currentAction = 'idle';
            ch.conversationCooldown = (ch.conversationCooldown||0) + 300; // Wartezeit bevor erneut gesucht wird
        });
    }

    // === Hausbau-Helferfunktionen ===
    selectHouseSite(character) {
    // Entfernt Auto-Platzierung: Häuser werden jetzt vom Spieler gesetzt.
    return null; // KI erzeugt keine Autoposition mehr
    }

    isPointNearRiver(x,y) {
        if (!this._riverCache) {
            const rivers = this.terrain.filter(t=>t.type==='river');
            this._riverCache = rivers.flatMap(r=> r.points?.map(p=>({x:p.x,y:p.y,width:r.width})) || []);
        }
        return this._riverCache.some(p => Math.hypot(p.x - x, p.y - y) < (p.width/2 + 20));
    }

    // Prüft ob irgendein Teil des Hausrechtecks in Flussnähe liegt (mehrere Samples)
    isAreaNearRiver(x,y,w,h){
        const samplesX = 5;
        const samplesY = 3;
        for (let ix=0; ix<samplesX; ix++) {
            for (let iy=0; iy<samplesY; iy++) {
                const sx = x + (ix/(samplesX-1))*w;
                const sy = y + (iy/(samplesY-1))*h;
                if (this.isPointNearRiver(sx,sy)) return true;
            }
        }
        return false;
    }

    isCollidingHouse(x,y,w,h) {
        return this.structures.some(s => s.type==='house' && this.rectOverlap(x,y,w,h,s.x,s.y,s.width,s.height));
    }

    rectOverlap(x1,y1,w1,h1,x2,y2,w2,h2){
        return !(x1+w1 < x2 || x2+w2 < x1 || y1+h1 < y2 || y2+h2 < y1);
    }

    init() {
        console.log('🌍 Creating terrain...');
        this.createTerrain();
    console.log('🌿 Spawning world resources...');
    this.spawnWorldResources();
    console.log('🦌 Spawning wildlife...');
    this.spawnWildlife();
        console.log('👥 Creating characters...');
        this.createCharacters();
        console.log('🤝 Initializing social systems...');
        this.initSocialSystem();
        
        console.log('🧠 Initializing Advanced AI Systems...');
        this.initAdvancedAI();
        
        console.log('✨ Initializing particles...');
        this.initParticles();
        console.log('🖱️ Setting up event listeners...');
        this.setupEventListeners();
        this.setupPlayerBuildingControls();
        console.log('✅ Game initialization complete!');
    }
    
    // 🧠 Advanced AI System Initialization
    initAdvancedAI() {
        // Kollektive Intelligenz aktivieren
        if (typeof CollectiveIntelligence !== 'undefined') {
            try {
                this.collectiveIntelligence = new CollectiveIntelligence();
                this.collectiveIntelligence.enable();
                console.log('🌐 Collective Intelligence enabled');
            } catch (error) {
                console.warn('❌ Failed to initialize Collective Intelligence:', error);
            }
        }
        
        // AI Dashboard aktivieren
        if (typeof AIMonitoringDashboard !== 'undefined') {
            try {
                this.aiDashboard = new AIMonitoringDashboard();
                console.log('📊 AI Dashboard initialized');
                
                // Dashboard per Tastenkombination togglen (Strg+Shift+A)
                document.addEventListener('keydown', (e) => {
                    if (e.ctrlKey && e.shiftKey && e.key === 'A') {
                        this.aiDashboard.toggle();
                    }
                });
            } catch (error) {
                console.warn('❌ Failed to initialize AI Dashboard:', error);
            }
        }
        
        // Natural Conversation System aktivieren
        if (typeof NaturalConversationSystem !== 'undefined') {
            try {
                this.conversationSystem = new NaturalConversationSystem();
                console.log('💬 Natural Conversation System enabled');
            } catch (error) {
                console.warn('❌ Failed to initialize Conversation System:', error);
            }
        }
        
        console.log('🎯 Advanced AI integration complete!');
    }
    
    // 🧠 Update Character AI Brain (RE-ENABLED WITH FIXES)
    async updateCharacterAI(character) {
        // Skip if no AI brain or rate limit to prevent spam
        if (!character.aiBrain) return;
        
        // Rate limiting - only update AI every 200ms per character
        const now = Date.now();
        character._lastAIUpdate = character._lastAIUpdate || 0;
        if ((now - character._lastAIUpdate) < 200) {
            return; // Skip this update cycle
        }
        character._lastAIUpdate = now;
        
        if (!character.aiBrain) return;
        
        // Umgebungsdaten für AI sammeln
        const environmentData = {
            hunger: character.hunger,
            energy: character.energy,
            thirst: character.thirst || 50,
            warmth: character.warmth || 70,
            nearbyCharacters: this.getNearbyCharacters(character, 100).length,
            nearbyResources: this.getNearbyResources(character, 150).length,
            currentAction: character.currentAction,
            x: character.x,
            y: character.y,
            gameTime: this.gameTime
        };
        
        // AI-Entscheidung treffen
        try {
            // Debug: Check if makeDecision method exists
            if (!character.aiBrain.makeDecision || typeof character.aiBrain.makeDecision !== 'function') {
                console.warn(`❌ ${character.name} aiBrain missing methods - fixing...`);
                
                // FIX: Add missing methods directly to the existing instance
                character.aiBrain.makeDecision = async function(environmentData, availableActions) {
                    // Simple fallback decision logic
                    if (environmentData.hunger > 70) return { action: 'gather_food', confidence: 0.6 };
                    if (environmentData.energy < 30) return { action: 'rest', confidence: 0.6 };
                    if (Math.random() < 0.3) return { action: 'explore', confidence: 0.4 };
                    return { action: 'gather_food', confidence: 0.5 };
                };
                
                character.aiBrain.learn = function(action, result) {
                    // Simple learning
                    if (result === 'success') {
                        this.learningStats.successfulActions++;
                    } else {
                        this.learningStats.failedActions++;
                    }
                    this.learningStats.decisionsKnnen++;
                };
                
                console.log(`✅ ${character.name} aiBrain methods fixed!`);
            }
            
            const aiDecision = await character.aiBrain.makeDecision(environmentData, this.getAvailableActions());
            
            if (aiDecision && aiDecision.action !== character.currentAction) {
                console.log(`🧠 ${character.name} AI suggests: ${aiDecision.action} (confidence: ${aiDecision.confidence})`);
                
                // AI-Entscheidung anwenden (mit Fallback auf bisheriges System)
                if (aiDecision.confidence > 0.7) {
                    this.executeAIAction(character, aiDecision.action);
                }
            }
            
            // Lernen aus Aktionsergebnis
            if (character.lastAction && character.lastActionResult) {
                character.aiBrain.learn(character.lastAction, character.lastActionResult);
            }
            
        } catch (error) {
            console.warn(`AI processing error for ${character.name}:`, error);
        }
    }
    
    // Verfügbare Aktionen für AI-Entscheidung
    getAvailableActions() {
        return ['idle', 'gather_food', 'collect_water', 'gather_wood', 'build', 'socialize', 'rest', 'explore'];
    }
    
    // AI-Aktion ausführen
    executeAIAction(character, action) {
        // Validierung der AI-Aktion
        const validActions = this.getAvailableActions();
        if (!validActions.includes(action)) {
            console.warn(`Invalid AI action: ${action} for ${character.name}`);
            return;
        }
        
        // Aktion über bestehendes System starten
        this.startAction(character, action);
        
        // Aktion für AI-Lernen merken
        character.lastAction = {
            action: action,
            environment: { hunger: character.hunger, energy: character.energy },
            timestamp: Date.now()
        };
    }

    setupPlayerBuildingControls(){
        this.playerBuildMode = null; // 'house' | 'hut' | 'warehouse'
        const houseBtn = document.getElementById('placeHouseBtn');
        const hutBtn = document.getElementById('placeHutBtn');
        const warehouseBtn = document.getElementById('placeWarehouseBtn');
        const activate = (mode)=>{
            this.playerBuildMode = this.playerBuildMode===mode? null : mode;
            if (houseBtn) houseBtn.style.opacity = this.playerBuildMode==='house'? '1':'0.75';
            if (hutBtn) hutBtn.style.opacity = this.playerBuildMode==='hut'? '1':'0.75';
            if (warehouseBtn) warehouseBtn.style.opacity = this.playerBuildMode==='warehouse'? '1':'0.75';
        };
        houseBtn?.addEventListener('click', ()=>activate('house'));
        hutBtn?.addEventListener('click', ()=>activate('hut'));
        warehouseBtn?.addEventListener('click', ()=>activate('warehouse'));
        window.addEventListener('keydown', (e)=>{
            if (e.key==='h' || e.key==='H') activate('house');
            if (e.key==='u' || e.key==='U') activate('hut');
            if (e.key==='l' || e.key==='L') activate('warehouse');
        });
        // Maus-Preview
        this.buildPreview = null;
        this.canvas.addEventListener('mousemove',(e)=>{
            if (!this.playerBuildMode) { this.buildPreview=null; return; }
            const rect = this.canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left)/this.camera.zoom - (this.camera.offsetX||0)/this.camera.zoom;
            const y = (e.clientY - rect.top)/this.camera.zoom - (this.camera.offsetY||0)/this.camera.zoom;
            const w = this.playerBuildMode==='house'?80: this.playerBuildMode==='warehouse'?100:60;
            const h = this.playerBuildMode==='house'?60: this.playerBuildMode==='warehouse'?80:45;
            const val = this.validatePlacement(this.playerBuildMode, x, y, w, h);
            this.buildPreview = {mode:this.playerBuildMode,x,y,w,h,valid:val.valid, reason:val.reason};
        });
        // Platzierung per Canvas-Klick
        this.canvas.addEventListener('click', (e)=>{
            if (!this.playerBuildMode) return;
            const rect = this.canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left)/this.camera.zoom - (this.camera.offsetX||0)/this.camera.zoom;
            const y = (e.clientY - rect.top)/this.camera.zoom - (this.camera.offsetY||0)/this.camera.zoom;
            if (this.playerBuildMode==='house') {
                const w=80,h=60;
                const chk = this.validatePlacement('house',x,y,w,h);
                if (!chk.valid){ console.log('❌ Haus Platz nicht gültig:', chk.reason); return; }
                // Charakter ohne irgendeinen bestehenden Bauplatz (verhindert Duplikate)
                const homeless = this.characters.find(c=> !this.structures.some(s=> (s.type==='house'||s.type==='hut') && s.owner===c.name));
                if (!homeless) { console.log('Alle haben schon ein fertiges Haus/Hütte.'); return; }
                this.structures.push({type:'house', x, y, width:w, height:h, progress:0, spentWood:0, requiredWood:25, stackedWood:0, stage:0, stepStartTime:null, completed:false, owner:homeless.name});
                this.addStory(`🏚️ Bauplatz für ${homeless.name} gesetzt.`);
            } else if (this.playerBuildMode==='hut') {
                const w=60,h=45;
                const chk = this.validatePlacement('hut',x,y,w,h);
                if (!chk.valid){ console.log('❌ Hütte Platz nicht gültig:', chk.reason); return; }
                const homeless = this.characters.find(c=> !this.structures.some(s=> (s.type==='house'||s.type==='hut') && s.owner===c.name));
                if (!homeless) { console.log('Alle haben schon ein fertiges Haus/Hütte.'); return; }
                this.structures.push({type:'hut', x, y, width:w, height:h, progress:0, requiredWood:10, stackedWood:0, completed:false, owner:homeless.name, stage:0});
                this.addStory(`🛖 Hüttenspot für ${homeless.name} gesetzt.`);
            } else if (this.playerBuildMode==='warehouse') {
                const w=100,h=80;
                const chk = this.validatePlacement('warehouse',x,y,w,h);
                if (!chk.valid){ console.log('❌ Lager Platz nicht gültig:', chk.reason); return; }
                // Prüfe ob schon ein Lager existiert
                const existingWarehouse = this.structures.find(s=> s.type==='warehouse');
                if (existingWarehouse) { console.log('❌ Es existiert bereits ein Lager!'); return; }
                this.structures.push({
                    type:'warehouse', x, y, width:w, height:h, 
                    progress:0, requiredWood:20, stackedWood:0, completed:false, stage:0,
                    storage: { wood: 0, food: 0 },
                    capacity: { wood: 100, food: 50 }
                });
                this.addStory(`📦 Lager-Bauplatz gesetzt.`);
            }
        });
    }

    validatePlacement(mode,x,y,w,h){
        if (this.isAreaNearRiver(x,y,w,h)) return {valid:false, reason:'Zu nah am Fluss'};
        
        // Vereinfachte Kollisionsprüfung für Hütten
        if (mode === 'hut') {
            // Prüfe nur auf echte Überlappung, nicht auf Abstand
            const clash = this.structures.find(s=> (s.type==='house'||s.type==='hut'||s.type==='warehouse') && 
                !(x + w < s.x || s.x + s.width < x || y + h < s.y || s.y + s.height < y)
            );
            if (clash) return {valid:false, reason:'Überlappt mit Gebäude'};
            return {valid:true};
        }
        
        // Lager braucht freie Fläche
        if (mode === 'warehouse') {
            const clash = this.structures.find(s=> 
                !(x + w < s.x || s.x + s.width < x || y + h < s.y || s.y + s.height < y)
            );
            if (clash) return {valid:false, reason:'Überlappt mit Struktur'};
            return {valid:true};
        }
        
        // Für Häuser: strengere Abstandsregel
        const padding = 5;
        const clash = this.structures.find(s=> (s.type==='house'||s.type==='hut') && !(
            x + w + padding < s.x ||
            s.x + s.width + padding < x ||
            y + h + padding < s.y ||
            s.y + s.height + padding < y
        ));
        if (clash) return {valid:false, reason:'Kollidiert mit anderer Unterkunft'};
        
        return {valid:true};
    }

    isCollidingStructure(x,y,w,h){
        return this.structures.some(s=> (s.type==='house'||s.type==='hut') && !(x+w < s.x || s.x+s.width < x || y+h < s.y || s.y+s.height < y));
    }

    // Zusätzliche Weltressourcen (für reichere Interaktion)
    spawnWorldResources() {
        // Beerfelder (berry_patch) & Wasserquellen (water_source)
        const width = this.canvas.width;
        const height = this.canvas.height;
        const patches = 5;
        for (let i=0;i<patches;i++) {
            this.terrain.push({
                type: 'berry_patch',
                x: Math.random()*width*0.8 + width*0.1,
                y: Math.random()*height*0.5 + height*0.4,
                size: 12 + Math.random()*8,
                food: 8 + Math.floor(Math.random()*6) // begrenzte Ladung
            });
        }
        const waters = 3;
        for (let i=0;i<waters;i++) {
            this.terrain.push({
                type: 'water_source',
                x: Math.random()*width*0.8 + width*0.1,
                y: Math.random()*height*0.5 + height*0.4,
                size: 10 + Math.random()*6,
                refillRate: 0.01,
                level: 1
            });
        }
    }

    spawnWildlife() {
        const width = this.canvas.width;
        const height = this.canvas.height;
        const count = 10 + Math.floor(Math.random()*5);
        for (let i=0;i<count;i++) {
            const type = Math.random()<0.7? 'deer':'boar';
            const x = Math.random()*width*0.8 + width*0.1;
            const y = Math.random()*height*0.5 + height*0.4;
            if (this.isPointNearRiver(x,y)) continue;
            this.animals.push({
                id:'ani_'+Date.now()+'_'+i,
                type,
                x,y,
                targetX: x + (Math.random()-0.5)*150,
                targetY: y + (Math.random()-0.5)*150,
                speed: (type==='deer'?0.6:0.45) + Math.random()*0.2,
                state:'idle',
                health: type==='deer'?40:60,
                lastDecision: Date.now()
            });
        }
        console.log(`🦌 Wildlife spawned: ${this.animals.length}`);
    }

    updateAnimals() {
        const now = Date.now();
        this.animals.forEach(an => {
            // Init extra behavior props
            if (an.behaviorInit!==true){
                an.behaviorInit=true;
                an.wanderInterval = 4000 + Math.random()*6000; // individuell
                an.pauseChance = 0.15 + Math.random()*0.2;
                an.herdId = Math.random()<0.6? 'herd_'+an.type : null;
                an.jitterPhase = Math.random()*Math.PI*2;
                an.fleeCooldown = 0; // frames ms
            }
            // Näherster Charakter
            let nearest=null, nd=Infinity;
            for (const c of this.characters) {
                const d = Math.hypot(c.x-an.x, c.y-an.y);
                if (d<nd){nd=d;nearest=c;}
            }
            const fleeR = an.type==='deer'? 170:150;
            if (nd < fleeR && (!an.fleeCooldown || now>an.fleeCooldown)) {
                an.state='flee';
                an.fleeCooldown = now + 1500 + Math.random()*1200; // nicht sofort wieder neu berechnen
                const dx = an.x - nearest.x;
                const dy = an.y - nearest.y;
                const len = Math.hypot(dx,dy)||1;
                const baseDist = an.type==='deer'? 260:220;
                an.targetX = an.x + (dx/len)*baseDist + (Math.random()-0.5)*60;
                an.targetY = an.y + (dy/len)*baseDist + (Math.random()-0.5)*60;
            } else if (an.state==='flee' && nd > fleeR*1.8) {
                an.state='idle';
                // Set new calm wander target later
                an.lastDecision = now - an.wanderInterval + 500; // bald neue Idle-Entscheidung
            }
            // Herd / leichte Gruppenausrichtung
            if (an.state==='idle' && an.herdId){
                const mates = this.animals.filter(o=>o!==an && o.herdId===an.herdId && o.type===an.type && Math.hypot(o.x-an.x,o.y-an.y)<260);
                if (mates.length){
                    const avgX = mates.reduce((s,m)=>s+m.x,0)/mates.length;
                    const avgY = mates.reduce((s,m)=>s+m.y,0)/mates.length;
                    // leichte Kohäsion
                    if (!an.targetX || Math.random()<0.05){
                        an.targetX = (an.targetX*0.7 + avgX*0.3) || avgX;
                        an.targetY = (an.targetY*0.7 + avgY*0.3) || avgY;
                    }
                }
            }
            // Neue Wanderentscheidung
            if (an.state==='idle' && (!an.lastDecision || now - an.lastDecision > an.wanderInterval)) {
                an.lastDecision = now;
                if (Math.random() < an.pauseChance) {
                    // Bleibt stehen (kleines Fressen)
                    an.targetX = an.x + (Math.random()-0.5)*20;
                    an.targetY = an.y + (Math.random()-0.5)*20;
                } else {
                    const range = an.type==='deer'? 200:160;
                    an.targetX = an.x + (Math.random()-0.5)*range;
                    an.targetY = an.y + (Math.random()-0.5)*range;
                }
            }
            // Bewegung
            if (an.targetX!=null && an.targetY!=null){
                const dx = an.targetX - an.x;
                const dy = an.targetY - an.y;
                const dist = Math.hypot(dx,dy);
                if (dist>1.2){
                    const speedMul = an.state==='flee'?2.5:1;
                    an.x += (dx/dist)*an.speed*speedMul;
                    an.y += (dy/dist)*an.speed*speedMul;
                }
                // Leichtes Jitter für organische Bewegung
                an.jitterPhase += 0.05 + Math.random()*0.02;
                an.x += Math.sin(an.jitterPhase)*0.15;
                an.y += Math.cos(an.jitterPhase*0.8)*0.12;
            }
        });
        this.animals = this.animals.filter(a=>a.health>0);
    }

    /* =========================================
       SOZIALES SYSTEM (Abstrakt & Jugendfrei)
       ========================================= */
    initSocialSystem() {
        // Initialisiere Einflusswerte und leere Beziehungen
        this.characters.forEach(c => {
            this.socialSystem.influence[c.name] = 1; // Startwert
        });
    }

    getRelationshipKey(a, b) {
        return [a, b].sort().join('|');
    }

    getOrCreateRelationship(a, b) {
        const key = this.getRelationshipKey(a, b);
        if (!this.socialSystem.relationships[key]) {
            this.socialSystem.relationships[key] = {
                affinity: 0,      // Sympathie
                trust: 30,        // Vertrauen
                bondLevel: 0,     // 0..5 (ab 3 = Paarbindung)
                interactions: 0,
                lastInteraction: Date.now()
            };
        }
        return this.socialSystem.relationships[key];
    }

    adjustRelationship(a, b, deltaAffinity, deltaTrust) {
        const rel = this.getOrCreateRelationship(a, b);
        rel.affinity = Math.max(-100, Math.min(100, rel.affinity + deltaAffinity));
        rel.trust = Math.max(0, Math.min(100, rel.trust + deltaTrust));
        rel.interactions++;
        rel.lastInteraction = Date.now();
        // Einfacher Bonding-Mechanismus
        if (rel.affinity > 40 && rel.trust > 50 && rel.bondLevel < 3) rel.bondLevel = 1;
        if (rel.affinity > 55 && rel.trust > 60 && rel.bondLevel < 4) rel.bondLevel = 2;
        if (rel.affinity > 70 && rel.trust > 70 && rel.bondLevel < 5) rel.bondLevel = 3; // ab 3 gelten sie als Paar
        return rel;
    }

    processSocialInteractions() {
        // Chance: nahe Charaktere interagieren
        for (let i = 0; i < this.characters.length; i++) {
            for (let j = i + 1; j < this.characters.length; j++) {
                const A = this.characters[i];
                const B = this.characters[j];
                const dist = Math.hypot(A.x - B.x, A.y - B.y);
                if (dist < 120) {
                    // kleine Interaktion
                    if (Math.random() < 0.01) {
                        const rel = this.adjustRelationship(A.name, B.name, (Math.random() * 4 - 1), (Math.random() * 3));
                        // Einfluss steigt bei vielen Interaktionen
                        this.socialSystem.influence[A.name] += 0.01;
                        this.socialSystem.influence[B.name] += 0.01;
                        // Paar-Bindung -> mögliche Familiengründung prüfen
                        if (rel.bondLevel >= 3) this.maybeScheduleBirth(A, B, rel);
                    }
                }
            }
        }
    }

    maybeScheduleBirth(a, b, rel) {
        // Keine Duplikate
        if (this.socialSystem.pendingBirths.some(p => p.parents.includes(a.name) || p.parents.includes(b.name))) return;
        // Wahrscheinlichkeit abhängig von Bindung, begrenzt Bevölkerungswachstum
        if (this.characters.length < 40 && Math.random() < 0.002) {
            const due = Date.now() + 60000; // 1 Minute später "Geburt" (abstrakt)
            this.socialSystem.pendingBirths.push({
                parents: [a.name, b.name],
                dueTime: due,
                childTemplate: {
                    traits: this.mixTraits(a.traits, b.traits)
                }
            });
            this.addStory(`${a.name} und ${b.name} planen eine Familie.`);
        }
    }

    mixTraits(tA, tB) {
        const mix = {};
        Object.keys(tA).forEach(k => {
            mix[k] = Math.min(1, Math.max(0, (tA[k] + tB[k]) / 2 + (Math.random() - 0.5) * 0.1));
        });
        return mix;
    }

    processPendingBirths() {
        const now = Date.now();
        const born = [];
        this.socialSystem.pendingBirths = this.socialSystem.pendingBirths.filter(entry => {
            if (entry.dueTime <= now) {
                born.push(entry);
                return false;
            }
            return true;
        });
        born.forEach(entry => {
            const name = this.generateChildName();
            const color = '#'+Math.floor(Math.random()*16777215).toString(16).padStart(6,'0');
            const baseX = this.canvas.width * 0.5 + (Math.random()-0.5)*200;
            const baseY = this.canvas.height * 0.5 + (Math.random()-0.5)*200;
            const character = {
                name,
                color,
                traits: entry.childTemplate.traits,
                preferredAction: 'erkunden',
                x: baseX,
                y: baseY,
                targetX: null,
                targetY: null,
                speed: 0.5 + Math.random() * 0.5,
                currentAction: 'idle',
                actionTime: 0,
                thoughts: ['Ich bin neu in dieser Welt...'],
                energy: 100,
                hunger: 10,
                thirst: 10,
                warmth: 80,
                inventory: { food: 1, water:1, wood:0, materials:0 },
                survivalInstincts: { lastWaterSource:null, knownFoodSources:[], safeSpots:[], dangerAreas:[], socialAlliances:[] },
                conversationCooldown: 200,
                lastConversationPartner: null,
                personalityQuirks: ['jung', 'lernt schnell'],
                lastEnvironmentState: null,
                actionStartTime: null,
                learningEnabled: true,
                aiBrain: null
            };
            this.characters.push(character);
            this.updateCharacterDisplay();
            this.addStory(`Ein neues Mitglied ist geboren: ${name}`);
        });
    }

    generateChildName() {
        const syllables = ['la','mi','ra','no','ti','sa','ve','lo','ka','re','na','li','mo'];
        const parts = 2 + Math.floor(Math.random()*2);
        let n='';
        for (let i=0;i<parts;i++) n += syllables[Math.floor(Math.random()*syllables.length)];
        return n.charAt(0).toUpperCase()+n.slice(1);
    }

    updateInfluenceAndLeader() {
        // Einfluss leicht normalisieren
        Object.keys(this.socialSystem.influence).forEach(name => {
            this.socialSystem.influence[name] *= 0.999; // leichte Dämpfung
        });
        // Finde aktuellen Führer
        let leader = null; let max = -Infinity;
        Object.entries(this.socialSystem.influence).forEach(([name, val]) => {
            if (val > max) { max = val; leader = name; }
        });
        this.socialSystem.currentLeader = leader;
    }

    formTribes() {
        // Einfache Gruppierung basierend auf Nähe & Affinität
        if (this.characters.length < 8) return; // erst ab Größe
        // Reset einfache Bildung alle 60 Sekunden
        if (!this.socialSystem._lastTribeUpdate || Date.now() - this.socialSystem._lastTribeUpdate > 60000) {
            this.socialSystem._lastTribeUpdate = Date.now();
            const groups = [];
            const unassigned = new Set(this.characters.map(c => c.name));
            while (unassigned.size) {
                const seed = [...unassigned][0];
                unassigned.delete(seed);
                const group = [seed];
                // Finde Namen mit hoher Affinität
                this.characters.forEach(c => {
                    if (unassigned.has(c.name)) {
                        const rel = this.socialSystem.relationships[this.getRelationshipKey(seed, c.name)];
                        if (rel && rel.affinity > 35) {
                            group.push(c.name);
                            unassigned.delete(c.name);
                        }
                    }
                });
                if (group.length >= 3) groups.push(group);
            }
            // Mappe zu Tribe Objekten
            this.socialSystem.tribes = groups.map((members, idx) => {
                // Bestimme internen Führer
                let best = members[0];
                let bestInf = this.socialSystem.influence[best]||0;
                members.forEach(m => { const inf = this.socialSystem.influence[m]||0; if (inf > bestInf) { bestInf = inf; best = m; } });
                return { id: 'tribe_'+idx, members, leader: best, cohesion: members.length / 10 };
            });
        }
    }

    eveningStoryEvent() {
        // Abends (z.B. nach 20:00 => 1200 Minuten) erzählen Gruppen Geschichten
        const hours = Math.floor(this.gameTime / 60);
        if (hours === 20 && !this.socialSystem._storyFlag) {
            this.socialSystem._storyFlag = true;
            // Wähle 1-2 Beziehungen mit hoher Affinität als Grundlage
            const goodRels = Object.entries(this.socialSystem.relationships)
                .filter(([_, r]) => r.affinity > 50 && r.interactions > 8)
                .slice(0,3);
            if (goodRels.length) {
                goodRels.forEach(([key]) => {
                    const [a,b] = key.split('|');
                    this.addStory(`${a} und ${b} teilen eine Erinnerung aus früheren Abenteuern.`);
                });
            } else {
                this.addStory('Die Gruppe reflektiert still den Tag.');
            }
        }
        if (hours !== 20) this.socialSystem._storyFlag = false;
    }

    addStory(text) {
        this.socialSystem.storyLog.push({ text, time: `Tag ${this.day} ${Math.floor(this.gameTime/60)}:${Math.floor(this.gameTime%60).toString().padStart(2,'0')}` });
        if (this.socialSystem.storyLog.length > 50) this.socialSystem.storyLog.shift();
        console.log('📖 Story:', text);
    }

    updateSocialDynamics() {
        this.processSocialInteractions();
        this.processPendingBirths();
        this.updateInfluenceAndLeader();
        this.formTribes();
        this.eveningStoryEvent();
    this.coordinateGroupHunt();
    this.updateConversations();
    }

    findNearestActiveFire(x,y){
        if (!this.fires || !this.fires.length) return null;
        const now = Date.now();
        let best=null, bd=Infinity;
        this.fires.forEach(f=>{
            if (now - f.startTime > f.duration) return; // erloschen
            const d = Math.hypot(x-f.x, y-f.y);
            if (d < bd) { bd = d; best = f; }
        });
        return best;
    }

    createTerrain() {
        // Load predefined terrain layout (with scaling for different screen sizes)
        this.loadPredefinedTerrain();
    }
    
    loadPredefinedTerrain() {
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        // Reference canvas size from your design
        const refWidth = 1815;
        const refHeight = 899;
        
        // Scale factors for different screen sizes
        const scaleX = width / refWidth;
        const scaleY = height / refHeight;
        
        // Your custom terrain positions - updated with precise coordinates
        const predefinedTerrain = {
            "mountains": [
                { x: 847, y: 523, size: 46 },
                { x: 1339, y: 422, size: 31 },
                { x: 1426, y: 460, size: 48 },
                { x: 1696, y: 463, size: 41 },
                { x: 301, y: 445, size: 57 },
                { x: 1406, y: 456, size: 55 },
                { x: 1307, y: 400, size: 54 },
                { x: 1333, y: 666, size: 52 }
            ],
            "trees": [
                { x: 49, y: 498, size: 19 },
                { x: 1310, y: 552, size: 23 },
                { x: 78, y: 765, size: 17 },
                { x: 1220, y: 685, size: 20 },
                { x: 1588, y: 786, size: 22 },
                { x: 1171, y: 552, size: 22 },
                { x: 1175, y: 591, size: 19 },
                { x: 1719, y: 464, size: 23 },
                { x: 1660, y: 527, size: 22 },
                { x: 4, y: 510, size: 21 },
                { x: 1471, y: 739, size: 22 },
                { x: 1357, y: 698, size: 23 },
                { x: 1187, y: 541, size: 21 },
                { x: 1238, y: 692, size: 18 },
                { x: 1455, y: 481, size: 20 },
                { x: 824, y: 557, size: 24 },
                { x: 244, y: 539, size: 22 },
                { x: 800, y: 737, size: 23 },
                { x: 144, y: 452, size: 21 },
                { x: 203, y: 493, size: 22 },
                { x: 853, y: 517, size: 23 },
                { x: 947, y: 619, size: 19 },
                { x: 740, y: 698, size: 16 },
                { x: 106, y: 535, size: 19 },
                { x: 1660, y: 490, size: 17 },
                { x: 1086, y: 456, size: 16 },
                { x: 1055, y: 655, size: 17 },
                { x: 468, y: 180, size: 25 },
                { x: 395, y: 136, size: 18 },
                { x: 424, y: 178, size: 18 },
                { x: 397, y: 176, size: 19 },
                { x: 430, y: 141, size: 17 },
                { x: 455, y: 156, size: 17 },
                { x: 443, y: 185, size: 24 },
                { x: 416, y: 217, size: 16 },
                { x: 349, y: 282, size: 18 },
                { x: 421, y: 281, size: 23 },
                { x: 487, y: 210, size: 20 },
                { x: 314, y: 197, size: 19 },
                { x: 347, y: 115, size: 24 },
                { x: 457, y: 25, size: 18 },
                { x: 236, y: 234, size: 19 },
                { x: 245, y: 136, size: 24 },
                { x: 279, y: 109, size: 19 },
                { x: 312, y: 143, size: 16 },
                { x: 196, y: 259, size: 16 },
                { x: 117, y: 223, size: 23 },
                { x: 79, y: 116, size: 17 },
                { x: 66, y: 46, size: 19 },
                { x: 148, y: 38, size: 22 },
                { x: 163, y: 90, size: 21 },
                { x: 174, y: 156, size: 19 },
                { x: 282, y: 55, size: 21 },
                { x: 361, y: 52, size: 21 },
                { x: 403, y: 88, size: 23 },
                { x: 403, y: 38, size: 19 },
                { x: 240, y: 42, size: 16 },
                { x: 191, y: 40, size: 17 },
                { x: 205, y: 82, size: 19 },
                { x: 323, y: 51, size: 21 },
                { x: 444, y: 70, size: 24 },
                { x: 471, y: 130, size: 24 },
                { x: 491, y: 72, size: 22 },
                { x: 517, y: 137, size: 16 },
                { x: 535, y: 102, size: 15 },
                { x: 523, y: 37, size: 22 }
            ],
            "bushes": [
                { x: 652, y: 573, size: 11 },
                { x: 210, y: 452, size: 12 },
                { x: 18, y: 542, size: 13 },
                { x: 799, y: 775, size: 9 },
                { x: 154, y: 516, size: 8 },
                { x: 1221, y: 712, size: 15 },
                { x: 261, y: 481, size: 13 },
                { x: 1606, y: 777, size: 14 },
                { x: 811, y: 760, size: 13 },
                { x: 622, y: 566, size: 11 },
                { x: 59, y: 746, size: 13 },
                { x: 865, y: 567, size: 8 },
                { x: 1188, y: 586, size: 12 },
                { x: 642, y: 547, size: 10 },
                { x: 745, y: 722, size: 14 },
                { x: 893, y: 474, size: 16 },
                { x: 65, y: 775, size: 10 },
                { x: 192, y: 565, size: 11 },
                { x: 93, y: 760, size: 10 },
                { x: 1783, y: 728, size: 13 },
                { x: 119, y: 494, size: 12 },
                { x: 1340, y: 576, size: 13 },
                { x: 1335, y: 448, size: 8 },
                { x: 1542, y: 771, size: 10 },
                { x: 1640, y: 740, size: 10 },
                { x: 1781, y: 618, size: 12 },
                { x: 87, y: 736, size: 10 },
                { x: 1463, y: 505, size: 15 },
                { x: 962, y: 626, size: 11 },
                { x: 282, y: 519, size: 13 },
                { x: 1674, y: 475, size: 13 },
                { x: 1164, y: 616, size: 16 },
                { x: 341, y: 480, size: 13 },
                { x: 1347, y: 543, size: 13 },
                { x: 1756, y: 591, size: 13 },
                { x: 786, y: 761, size: 15 },
                { x: 1278, y: 455, size: 9 },
                { x: 142, y: 561, size: 10 },
                { x: 1665, y: 584, size: 9 },
                { x: 1157, y: 592, size: 10 },
                { x: 360, y: 232, size: 16 },
                { x: 350, y: 146, size: 15 },
                { x: 442, y: 92, size: 13 },
                { x: 495, y: 97, size: 14 },
                { x: 473, y: 154, size: 13 },
                { x: 463, y: 211, size: 10 },
                { x: 442, y: 214, size: 10 },
                { x: 419, y: 246, size: 14 },
                { x: 453, y: 257, size: 11 },
                { x: 513, y: 178, size: 15 },
                { x: 551, y: 146, size: 13 },
                { x: 1064, y: 399, size: 9 },
                { x: 1206, y: 347, size: 12 },
                { x: 1096, y: 159, size: 11 },
                { x: 1164, y: 104, size: 10 },
                { x: 1083, y: 117, size: 15 },
                { x: 1008, y: 160, size: 10 },
                { x: 964, y: 87, size: 10 },
                { x: 1006, y: 121, size: 12 },
                { x: 1032, y: 88, size: 9 },
                { x: 1036, y: 128, size: 12 },
                { x: 1010, y: 84, size: 10 },
                { x: 978, y: 113, size: 8 },
                { x: 985, y: 143, size: 10 },
                { x: 1033, y: 115, size: 10 },
                { x: 1014, y: 106, size: 8 },
                { x: 1053, y: 91, size: 14 },
                { x: 1053, y: 112, size: 11 },
                { x: 1034, y: 154, size: 13 },
                { x: 1128, y: 341, size: 9 },
                { x: 1121, y: 468, size: 14 },
                { x: 1036, y: 553, size: 10 },
                { x: 1092, y: 748, size: 10 },
                { x: 931, y: 825, size: 8 },
                { x: 1024, y: 741, size: 10 }
            ]
        };
        
        // Fluss aus Vogelperspektive - kommt von links, geht nach oben raus
        this.terrain.push({
            type: 'river',
            points: [
                { x: 0, y: height * 0.8 },               // Von links unten
                { x: width * 0.15, y: height * 0.75 },   // Sanfte Kurve
                { x: width * 0.3, y: height * 0.6 },     // Biegung nach oben
                { x: width * 0.45, y: height * 0.45 },   // Weiter nach oben
                { x: width * 0.6, y: height * 0.3 },     // Kurve nach rechts
                { x: width * 0.8, y: height * 0.15 },    // Fast am oberen Rand
                { x: width, y: 0 }                       // Raus oben rechts
            ],
            width: 35
        });

        // Brücke über den Fluss - nochmal 30% mehr nach rechts geneigt
        this.terrain.push({
            type: 'bridge',
            x: 550 * scaleX,                             // Links positioniert
            y: 540 * scaleY,                             // Ein klein wenig zurück nach unten  
            width: 90,                                    // Normale Länge zurück
            height: 36,                                   // 3x höher/breiter (12 * 3 = 36)
            angle: 0.624,                                 // Weitere 30% steiler (0.48 * 1.3 = 0.624)
            crossingPoints: [                             // Automatisch berechnet
                { x: (550 - 45) * scaleX, y: (540 - 18) * scaleY },   // Einstieg
                { x: (550 + 45) * scaleX, y: (540 + 18) * scaleY }    // Ausstieg
            ]
        });
        
        // Add mountains with your exact positions
        predefinedTerrain.mountains.forEach(mountain => {
            this.terrain.push({
                type: 'mountain',
                x: mountain.x * scaleX,
                y: mountain.y * scaleY,
                size: mountain.size * Math.min(scaleX, scaleY) // Scale size proportionally
            });
        });
        
        // Add trees with your exact positions
        predefinedTerrain.trees.forEach(tree => {
            this.terrain.push({
                type: 'tree',
                x: tree.x * scaleX,
                y: tree.y * scaleY,
                size: tree.size * Math.min(scaleX, scaleY)
            });
        });
        
        // Add bushes with your exact positions
        predefinedTerrain.bushes.forEach(bush => {
            this.terrain.push({
                type: 'bush',
                x: bush.x * scaleX,
                y: bush.y * scaleY,
                size: bush.size * Math.min(scaleX, scaleY)
            });
        });
        
        console.log(`🎨 Loaded predefined terrain layout (scaled ${scaleX.toFixed(2)}x${scaleY.toFixed(2)})`);
        console.log(`📊 Terrain count: ${predefinedTerrain.mountains.length} mountains, ${predefinedTerrain.trees.length} trees, ${predefinedTerrain.bushes.length} bushes`);
    }
    
    // Fallback for random terrain (accessible via debug panel)
    createRandomTerrain() {
        const width = this.canvas.width;
        const height = this.canvas.height;

        // Clear existing terrain except river
        this.terrain = this.terrain.filter(t => t.type === 'river');

        // Berge
        for (let i = 0; i < 8; i++) {
            this.terrain.push({
                type: 'mountain',
                x: Math.random() * width,
                y: height * 0.1 + Math.random() * height * 0.2,
                size: 30 + Math.random() * 40
            });
        }

        // Bäume
        for (let i = 0; i < 25; i++) {
            this.terrain.push({
                type: 'tree',
                x: Math.random() * width,
                y: height * 0.5 + Math.random() * height * 0.4,
                size: 15 + Math.random() * 10
            });
        }

        // Sträucher
        for (let i = 0; i < 40; i++) {
            this.terrain.push({
                type: 'bush',
                x: Math.random() * width,
                y: height * 0.4 + Math.random() * height * 0.5,
                size: 8 + Math.random() * 8
            });
        }
    }

    createCharacters() {
        const personalities = [
            {
                name: "Max der Sammler",
                color: "#FF6B6B",
                traits: { mut: 0.3, neugier: 0.8, fleiss: 0.9, sozial: 0.6 },
                preferredAction: "sammeln"
            },
            {
                name: "Luna die Entdeckerin", 
                color: "#4ECDC4",
                traits: { mut: 0.9, neugier: 0.9, fleiss: 0.5, sozial: 0.4 },
                preferredAction: "erkunden"
            },
            {
                name: "Tom der Baumeister",
                color: "#45B7D1", 
                traits: { mut: 0.6, neugier: 0.4, fleiss: 0.8, sozial: 0.8 },
                preferredAction: "bauen"
            },
            {
                name: "Emma die Soziale",
                color: "#96CEB4",
                traits: { mut: 0.4, neugier: 0.6, fleiss: 0.6, sozial: 0.9 },
                preferredAction: "sozialisieren"
            }
        ];

        personalities.forEach((personality, index) => {
            const character = {
                ...personality,
                x: 200 + index * 100,
                y: 400 + Math.random() * 200,
                targetX: null,
                targetY: null,
                speed: 0.5 + Math.random() * 0.5,
                currentAction: "idle",
                
                // Reproduktions-System
                age: 18 + Math.random() * 20, // 18-38 Jahre alt
                gender: Math.random() < 0.5 ? 'male' : 'female',
                relationships: new Map(), // Name -> affection level (0-100)
                partner: null, // Name des Partners
                pregnant: false,
                pregnancyTime: 0,
                pregnancyDuration: 3, // 3 Spieltage
                fertility: 0.7 + Math.random() * 0.3, // 70-100% Fruchtbarkeit
                lastBirth: 0, // Zeit seit letzter Geburt
                actionTime: 0,
                thoughts: [],
                role: this.determineRole(personality.traits),
                preferences: { likedActions: [] },
                emotions: { mood: 0, energyTone: 0, socialTone: 0 },
                affect: { mood: 0.1, lastChange: Date.now(), engagement: 0.5, rapport: {} },
                memories: [],
                lastConversationWith: {},
                energy: 80 + Math.random() * 20,
                hunger: 20 + Math.random() * 30,
                // Neue Überlebensbedürfnisse
                thirst: 30 + Math.random() * 20,
                warmth: 70 + Math.random() * 20,
                // Inventar-System
                inventory: {
                    food: 2 + Math.floor(Math.random() * 3),
                    water: 1 + Math.floor(Math.random() * 2),
                    wood: Math.floor(Math.random() * 2),
                    materials: 0
                },
                // Überlebens-KI Eigenschaften
                survivalInstincts: {
                    lastWaterSource: null,
                    knownFoodSources: [],
                    safeSpots: [],
                    dangerAreas: [],
                    socialAlliances: []
                },
                // Gesprächssystem
                conversationCooldown: 0,
                lastConversationPartner: null,
                personalityQuirks: this.generatePersonalityQuirks(personality),
                // Neue AI-Eigenschaften
                lastEnvironmentState: null,
                actionStartTime: null,
                learningEnabled: true
            };
            
            // 🧠 Integriere Advanced AI Brain System
            if (typeof AIBrain !== 'undefined') {
                try {
                    character.aiBrain = new AIBrain(personality);
                    console.log(`🧠 AI Brain initialized for ${character.name}`);
                } catch (error) {
                    console.warn(`❌ Failed to initialize AI Brain for ${character.name}:`, error);
                    character.aiBrain = null;
                }
            } else {
                console.warn(`⚠️ AIBrain not loaded yet for ${personality.name}`);
                character.aiBrain = null;
            }
            // Ziele / Goal-System Grundstruktur
            character.goals = []; // {id, type, target, priority, created, status}
            character.currentGoal = null;
            
            // Sprite Index zuweisen (0-24 für die 25 verfügbaren Sprites)
            character.spriteIndex = index % 25;
            
            this.characters.push(character);
            // Basierend auf Rolle einfache Aktions-Präferenzen setzen
            switch (character.role) {
                case 'sammler':
                    character.preferences.likedActions = ['sammeln','gather_food','gather_wood'];
                    break;
                case 'entdecker':
                    character.preferences.likedActions = ['erkunden'];
                    break;
                case 'bauer':
                    character.preferences.likedActions = ['bauen','gather_wood'];
                    break;
                case 'sozialer':
                    character.preferences.likedActions = ['sozialisieren','seek_conversation','talking'];
                    break;
            }
        });

        this.updateCharacterDisplay();
    }

    // Einfache Rollenzuweisung nach dominanten Traits
    determineRole(traits) {
        const entries = [
            ['mut', traits.mut],
            ['neugier', traits.neugier],
            ['fleiss', traits.fleiss],
            ['sozial', traits.sozial]
        ].sort((a,b)=>b[1]-a[1]);
        const top = entries[0][0];
        if (top === 'neugier') return 'entdecker';
        if (top === 'fleiss') return 'bauer';
        if (top === 'sozial') return 'sozialer';
        return 'sammler';
    }

    generatePersonalityQuirks(personality) {
        const quirks = [];
        
        // Basierend auf Persönlichkeitsmerkmalen
        if (personality.traits.neugier > 0.8) {
            quirks.push("stellt immer Fragen", "erkundet gerne unbekannte Orte");
        }
        if (personality.traits.sozial > 0.8) {
            quirks.push("redet gerne mit anderen", "mag Gruppenaktivitäten");
        }
        if (personality.traits.fleiss > 0.8) {
            quirks.push("arbeitet sehr effizient", "plant gerne voraus");
        }
        if (personality.traits.mut > 0.8) {
            quirks.push("geht Risiken ein", "ermutigt andere");
        }
        
        // Zufällige einzigartige Eigenarten
        const randomQuirks = [
            "summt beim Arbeiten", "sammelt gerne bunte Steine", 
            "redet mit sich selbst", "hat Angst vor tiefen Gewässern",
            "liebt Sonnenuntergänge", "zählt beim Gehen",
            "träumt von fernen Ländern", "sammelt interessante Blätter"
        ];
        
        quirks.push(randomQuirks[Math.floor(Math.random() * randomQuirks.length)]);
        
        return quirks;
    }

    drawTerrain() {
        if (!this._loggedFirstTerrain) {
            this._loggedFirstTerrain = true;
            console.log('🧪 drawTerrain start: terrain elements', this.terrain.length, 'sample types', [...new Set(this.terrain.map(t=>t.type))]);
            if (this.terrain.length < 5) {
                console.warn('⚠️ Terrain length suspiciously small – regenerating predefined terrain');
                this.terrain = [];
                this.loadPredefinedTerrain();
                console.log('✅ Terrain regenerated, new length', this.terrain.length);
            }
        }
        // Verbesserte Himmel-Wiese mit Gradienten
        this.drawBackground();
        
        // Schatten für Terrain-Elemente
        this.drawTerrainShadows();
        
        // Fluss mit Wasser-Tiles
        this.terrain.filter(t => t.type === 'river').forEach(river => {
            this.drawRiverWithTiles(river);
        });

        // Brücke zeichnen (nach dem Fluss, vor Bergen)
        this.terrain.filter(t => t.type === 'bridge').forEach(bridge => {
            this.ctx.save();
            this.ctx.translate(bridge.x, bridge.y);
            this.ctx.rotate(bridge.angle);
            
            // Brücken-Schatten
            this.ctx.fillStyle = 'rgba(0,0,0,0.3)';
            this.ctx.fillRect(-bridge.width/2 + 2, -bridge.height/2 + 2, bridge.width, bridge.height);
            
            // Brücken-Deck (Holz)
            const bridgeGradient = this.ctx.createLinearGradient(0, -bridge.height/2, 0, bridge.height/2);
            bridgeGradient.addColorStop(0, '#8B4513');
            bridgeGradient.addColorStop(0.5, '#A0522D');
            bridgeGradient.addColorStop(1, '#654321');
            
            this.ctx.fillStyle = bridgeGradient;
            this.ctx.fillRect(-bridge.width/2, -bridge.height/2, bridge.width, bridge.height);
            
            // Brücken-Planken (Details)
            this.ctx.strokeStyle = '#654321';
            this.ctx.lineWidth = 1;
            for (let i = -bridge.width/2; i < bridge.width/2; i += 8) {
                this.ctx.beginPath();
                this.ctx.moveTo(i, -bridge.height/2);
                this.ctx.lineTo(i, bridge.height/2);
                this.ctx.stroke();
            }
            
            // Geländer
            this.ctx.strokeStyle = '#654321';
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.moveTo(-bridge.width/2, -bridge.height/2);
            this.ctx.lineTo(bridge.width/2, -bridge.height/2);
            this.ctx.moveTo(-bridge.width/2, bridge.height/2);
            this.ctx.lineTo(bridge.width/2, bridge.height/2);
            this.ctx.stroke();
            
            this.ctx.restore();
        });

        // Häuser / Baustellen (unterhalb von Bäumen, oberhalb von Fluss & Berg)
        if (this.structures) {
            this.structures.forEach(site => {
                if (site.type !== 'house') return;
                const {x,y,width,height,progress,completed,stackedWood,requiredWood,stage} = site;
                this.ctx.save();
                // Fortschritts-/Holz Overlay oberhalb des Hauses
                const cx = x + width/2;
                const barY = y - 14;
                // Hintergrund
                this.ctx.fillStyle = 'rgba(0,0,0,0.45)';
                this.ctx.fillRect(cx-42, barY, 84, 10);
                // Progress-Farbe
                const prog = progress||0;
                const filled = 84 * prog;
                this.ctx.fillStyle = completed? '#3cb371' : '#ffbf66';
                this.ctx.fillRect(cx-42, barY, filled, 10);
                // Text: Holzstapel + Prozent
                this.ctx.font = '9px sans-serif';
                this.ctx.fillStyle = '#fff';
                const pctTxt = Math.round(prog*100)+'%';
                const woodTxt = stackedWood+'/'+requiredWood;
                this.ctx.fillText(woodTxt+' | '+pctTxt, cx-40, barY+8);
                // Bauplatz-Rahmen falls noch kein Fortschritt
                if (!completed && stackedWood===0 && progress===0) {
                    this.ctx.strokeStyle = 'rgba(255,165,0,0.8)';
                    this.ctx.setLineDash([6,4]);
                    this.ctx.strokeRect(x-4, y-4, width+8, height+8);
                    this.ctx.setLineDash([]);
                }
                // Schatten / Fundament
                this.ctx.fillStyle = 'rgba(0,0,0,0.18)';
                this.ctx.beginPath();
                this.ctx.roundRect ? this.ctx.roundRect(x+4, y+height-10+4, width, 12, 4) : this.ctx.fillRect(x+4, y+height-6+4, width, 8);
                this.ctx.fill();
                // Bauphasen definieren
                // Phase 0-25%: Holzpfosten + Bodenbalken
                // 25-60%: Wände wachsen
                // 60-100%: Dachkonstruktion + Dachziegel
                let phase = progress;
                // Separate Visual Mapping: 0-0.25 = Materiallieferung
                const buildPhaseProgress = Math.max(0, phase - 0.25) / 0.75; // 0..1 ab Baustart
                const baseY = y+height;
                const wallTop = baseY - height*0.65;
                const frameColor = '#b88752';
                const wallColor = completed? '#d9b98a' : '#e2c79f';
                const roofHeight = 20 + 10*phase;
                // Pfosten immer sichtbar während Bau
                const posts = 4;
                for (let i=0;i<posts;i++) {
                    const px = x + (i/(posts-1))*width;
                    const postH = height*0.15 + phase*height*0.5;
                    this.ctx.fillStyle = frameColor;
                    this.ctx.fillRect(px-2, baseY-postH, 4, postH);
                }
                // Bodenbalken
                this.ctx.fillStyle = frameColor;
                this.ctx.fillRect(x, baseY-6, width, 6);
                if (buildPhaseProgress>0) {
                    // Wände füllen proportional
                    const wallProgress = Math.min(1, buildPhaseProgress* (4/4));
                    const visibleWallHeight = height*0.55*wallProgress;
                    this.ctx.fillStyle = wallColor;
                    this.ctx.fillRect(x+3, baseY - 6 - visibleWallHeight, width-6, visibleWallHeight);
                    // Fenster & Tür wenn genug Wand
                    if (wallProgress>0.5) {
                        this.ctx.fillStyle = '#623c1e'; // Tür
                        this.ctx.fillRect(x+width*0.15, baseY - 6 - visibleWallHeight + visibleWallHeight*0.45, 14, visibleWallHeight*0.55);
                        this.ctx.fillStyle = '#c4e4ff'; // Fenster
                        this.ctx.fillRect(x+width*0.55, baseY - 6 - visibleWallHeight + visibleWallHeight*0.3, 18, 14);
                        this.ctx.strokeStyle = '#553319';
                        this.ctx.lineWidth = 2;
                        this.ctx.strokeRect(x+width*0.55, baseY - 6 - visibleWallHeight + visibleWallHeight*0.3, 18, 14);
                    }
                }
                // Dach / Sparren
                if (buildPhaseProgress> (2/4)) { // ab Stage 3
                    const roofProgress = Math.min(1, (buildPhaseProgress - 0.5)/0.5);
                    this.ctx.beginPath();
                    this.ctx.moveTo(x-4, baseY - height*0.65);
                    this.ctx.lineTo(x+width/2, baseY - height*0.65 - roofHeight*roofProgress);
                    this.ctx.lineTo(x+width+4, baseY - height*0.65);
                    this.ctx.closePath();
                    this.ctx.fillStyle = completed? '#8b4a2b' : '#b06a3d';
                    this.ctx.fill();
                    // Dachziegel-Linien bei Fertigstellung
                    if (completed) {
                        this.ctx.strokeStyle = 'rgba(255,255,255,0.15)';
                        this.ctx.lineWidth = 1;
                        for (let ry=0; ry<roofHeight; ry+=4) {
                            this.ctx.beginPath();
                            this.ctx.moveTo(x, baseY - height*0.65 - ry*roofProgress);
                            this.ctx.lineTo(x+width, baseY - height*0.65 - ry*roofProgress);
                            this.ctx.stroke();
                        }
                    }
                }
                // Innenlicht bei Nacht / Fertig
                if (completed && (this.gameTime < 360 || this.gameTime > 1080)) { // Nacht
                    const glow = this.ctx.createRadialGradient(x+width*0.55+9, baseY-height*0.35, 4, x+width*0.55+9, baseY-height*0.35, 20);
                    glow.addColorStop(0,'rgba(255,220,120,0.8)');
                    glow.addColorStop(1,'rgba(255,220,120,0)');
                    this.ctx.fillStyle = glow;
                    this.ctx.beginPath();
                    this.ctx.arc(x+width*0.55+9, baseY-height*0.35, 20, 0, Math.PI*2);
                    this.ctx.fill();
                }
                // Fortschrittsanzeige
                this.ctx.font = '10px Arial';
                if (!completed) {
                    // Holzstapel anzeigen solange noch nicht gebaut
                    if (stackedWood < requiredWood) {
                        // Stapel (kleine Holzscheite gestapelt)
                        const pileX = x + width + 6;
                        const pileY = baseY - 10;
                        const pileLevels = Math.ceil(requiredWood / 5);
                        for (let i=0;i<stackedWood;i++) {
                            const level = Math.floor(i/5);
                            const idx = i % 5;
                            this.ctx.fillStyle = '#8b5a2b';
                            this.ctx.fillRect(pileX + idx*6, pileY - level*5, 5, 4);
                        }
                        this.ctx.fillStyle = '#000';
                        this.ctx.font = '9px Arial';
                        this.ctx.fillText(stackedWood+'/'+requiredWood, pileX, pileY - pileLevels*5 - 4);
                        // Pfeil / Hinweis
                        this.ctx.fillStyle='rgba(255,165,0,0.9)';
                        this.ctx.font='10px Arial';
                        this.ctx.fillText('Holz hier stapeln', x, baseY+30);
                    }
                    this.ctx.fillStyle = 'rgba(0,0,0,0.35)';
                    this.ctx.fillRect(x, baseY+4, width, 6);
                    this.ctx.fillStyle = '#4caf50';
                    this.ctx.fillRect(x, baseY+4, width*progress, 6);
                    this.ctx.fillStyle = '#000';
                    const label = stackedWood < requiredWood ? 'Material '+Math.round((stackedWood/requiredWood)*100)+'%' : 'Phase '+(stage+1)+'/4';
                    this.ctx.fillText(label, x, baseY+16);
                } else {
                    this.ctx.fillStyle = '#000';
                    this.ctx.fillText('Haus '+site.owner.split(' ')[0], x, baseY+14);
                }
                this.ctx.restore();
            });
        }

        // Hütten (eigene Darstellung & Baufortschritt)
        if (this.structures) {
            this.structures.forEach(site => {
                if (site.type !== 'hut') return;
                const {x,y,width,height,progress,completed,stackedWood,requiredWood} = site;
                this.ctx.save();
                const cx = x + width/2;
                const barY = y - 10;
                // Hintergrund Fortschrittsbalken
                this.ctx.fillStyle = 'rgba(0,0,0,0.4)';
                this.ctx.fillRect(cx-30, barY, 60, 8);
                const prog = progress||0;
                const filled = 60 * prog;
                this.ctx.fillStyle = completed? '#2e8b57' : '#ffda7a';
                this.ctx.fillRect(cx-30, barY, filled, 8);
                // Text (Holz / %)
                this.ctx.font = '8px sans-serif';
                this.ctx.fillStyle = '#fff';
                this.ctx.fillText(stackedWood+'/'+requiredWood+' | '+Math.round(prog*100)+'%', cx-28, barY+7);
                // Bauplatz-Rahmen wenn leer
                if (!completed && stackedWood===0 && progress===0) {
                    this.ctx.strokeStyle = 'rgba(255,180,0,0.8)';
                    this.ctx.setLineDash([5,3]);
                    this.ctx.strokeRect(x-3, y-3, width+6, height+6);
                    this.ctx.setLineDash([]);
                }
                const baseY = y+height;
                // Fundament / Boden
                this.ctx.fillStyle = '#6b4b2a';
                this.ctx.fillRect(x, baseY-5, width, 5);
                // Visual Logik: erst Material sammeln (stackedWood < requiredWood) dann Bau
                const materialPhase = stackedWood < requiredWood;
                // Pfosten / Rahmen schon ab 50% Material sichtbar
                if (stackedWood >= requiredWood*0.5 || !materialPhase) {
                    this.ctx.fillStyle = '#a0703c';
                    // 4 Eckpfosten
                    const posts = [x+2, x+width-4];
                    posts.forEach(px => {
                        this.ctx.fillRect(px, y+6, 4, height-6);
                    });
                    // Querbalken oben
                    this.ctx.fillRect(x+2, y+6, width-6, 4);
                }
                // Wände wenn genug Material oder Bau gestartet
                if (!materialPhase) {
                    const wallHeight = height*0.55;
                    this.ctx.fillStyle = completed? '#d2b48c' : '#e3c8a0';
                    // einfache Wandfläche
                    this.ctx.fillRect(x+6, baseY-5 - wallHeight, width-12, wallHeight);
                    // Türöffnung
                    this.ctx.clearRect(x+width*0.15, baseY-5 - wallHeight*0.45, 12, wallHeight*0.45);
                }
                // Dachprogress (ab 30% Baufortschritt sichtbar)
                if (!materialPhase && prog>0.3) {
                    const roofProg = (prog-0.3)/0.7;
                    const roofPeak = y + 4 - 12*roofProg;
                    this.ctx.beginPath();
                    this.ctx.moveTo(x-2, y+8);
                    this.ctx.lineTo(cx, roofPeak);
                    this.ctx.lineTo(x+width+2, y+8);
                    this.ctx.closePath();
                    this.ctx.fillStyle = completed? '#8b4a2b' : '#b46a3d';
                    this.ctx.fill();
                }
                // Holzstapel neben Hütte solange Materialphase
                if (materialPhase) {
                    const pileX = x + width + 4;
                    const pileY = baseY - 6;
                    for (let i=0;i<stackedWood;i++) {
                        const level = Math.floor(i/5);
                        const idx = i % 5;
                        this.ctx.fillStyle = '#8b5a2b';
                        this.ctx.fillRect(pileX + idx*5, pileY - level*4, 4, 3);
                    }
                }
                // Nachtlicht bei Fertigstellung
                if (completed && (this.gameTime < 360 || this.gameTime > 1080)) {
                    const glow = this.ctx.createRadialGradient(cx, y+height*0.4, 3, cx, y+height*0.4, 16);
                    glow.addColorStop(0,'rgba(255,210,110,0.8)');
                    glow.addColorStop(1,'rgba(255,210,110,0)');
                    this.ctx.fillStyle = glow;
                    this.ctx.beginPath();
                    this.ctx.arc(cx, y+height*0.4, 16, 0, Math.PI*2);
                    this.ctx.fill();
                }
                if (completed) {
                    this.ctx.fillStyle = '#000';
                    this.ctx.font = '9px Arial';
                    this.ctx.fillText('Hütte '+site.owner.split(' ')[0], x, baseY+12);
                }
                this.ctx.restore();
            });
        }

        // Lager-Darstellung
        if (this.structures) {
            this.structures.forEach(warehouse => {
                if (warehouse.type !== 'warehouse') return;
                const {x,y,width,height,progress,completed,stackedWood,requiredWood,storage,capacity} = warehouse;
                this.ctx.save();
                
                // Lager-Fortschrittsbalken
                const cx = x + width/2;
                const barY = y - 15;
                this.ctx.fillStyle = 'rgba(0,0,0,0.4)';
                this.ctx.fillRect(cx-40, barY, 80, 8);
                const prog = progress||0;
                const filled = 80 * prog;
                this.ctx.fillStyle = completed? '#4caf50' : '#ff9800';
                this.ctx.fillRect(cx-40, barY, filled, 8);
                
                // Bau-Text
                this.ctx.font = '8px sans-serif';
                this.ctx.fillStyle = '#fff';
                this.ctx.fillText(`Lager: ${stackedWood}/${requiredWood} Holz | ${Math.round(prog*100)}%`, cx-38, barY+7);
                
                // Bauplatz-Rahmen wenn noch nicht fertig
                if (!completed) {
                    this.ctx.strokeStyle = 'rgba(255,152,0,0.8)';
                    this.ctx.setLineDash([6,4]);
                    this.ctx.strokeRect(x-3, y-3, width+6, height+6);
                    this.ctx.setLineDash([]);
                }
                
                // Lager-Hauptstruktur (groß und imposant)
                if (completed) {
                    // Basis/Fundament
                    this.ctx.fillStyle = '#5d4037';
                    this.ctx.fillRect(x, y+height-10, width, 10);
                    
                    // Hauptgebäude
                    this.ctx.fillStyle = '#8d6e63';
                    this.ctx.fillRect(x+5, y+10, width-10, height-20);
                    
                    // Dach
                    this.ctx.fillStyle = '#6d4c41';
                    this.ctx.beginPath();
                    this.ctx.moveTo(x, y+15);
                    this.ctx.lineTo(cx, y);
                    this.ctx.lineTo(x+width, y+15);
                    this.ctx.closePath();
                    this.ctx.fill();
                    
                    // Lager-Türen (zwei große Türen)
                    this.ctx.fillStyle = '#4a2c17';
                    this.ctx.fillRect(x+width*0.2, y+height*0.4, width*0.25, height*0.5);
                    this.ctx.fillRect(x+width*0.55, y+height*0.4, width*0.25, height*0.5);
                    
                    // Storage-Anzeige
                    const woodPercent = Math.round((storage.wood / capacity.wood) * 100);
                    const foodPercent = Math.round((storage.food / capacity.food) * 100);
                    
                    this.ctx.font = '10px Arial';
                    this.ctx.fillStyle = '#fff';
                    this.ctx.fillText(`📦 LAGER`, cx-20, y-20);
                    this.ctx.font = '8px Arial';
                    this.ctx.fillText(`🪵 ${storage.wood}/${capacity.wood} (${woodPercent}%)`, cx-35, y+height+15);
                    this.ctx.fillText(`🍎 ${storage.food}/${capacity.food} (${foodPercent}%)`, cx-35, y+height+25);
                    
                } else if (stackedWood > 0) {
                    // Lager im Bau - Materialstapel anzeigen
                    this.ctx.fillStyle = '#8d6e63';
                    this.ctx.fillRect(x+10, y+height-20, width-20, 15);
                    this.ctx.font = '9px Arial';
                    this.ctx.fillStyle = '#333';
                    this.ctx.fillText('Lager im Bau...', cx-25, y+height*0.5);
                }
                
                this.ctx.restore();
            });
        }

        // Berge mit verbesserter 3D-Optik
        this.terrain.filter(t => t.type === 'mountain').forEach(mountain => {
            // Berg-Schatten
            this.ctx.shadowColor = 'rgba(0,0,0,0.4)';
            this.ctx.shadowBlur = 10;
            this.ctx.shadowOffsetX = 3;
            this.ctx.shadowOffsetY = 5;
            
            // Hauptberg mit Gradient
            const mountainGradient = this.ctx.createRadialGradient(
                mountain.x - mountain.size/4, mountain.y, 0,
                mountain.x, mountain.y + mountain.size/2, mountain.size
            );
            mountainGradient.addColorStop(0, '#A0826D');
            mountainGradient.addColorStop(0.6, '#8B7355');
            mountainGradient.addColorStop(1, '#5D4E37');
            
            this.ctx.fillStyle = mountainGradient;
            this.ctx.beginPath();
            this.ctx.moveTo(mountain.x, mountain.y + mountain.size/2);
            this.ctx.lineTo(mountain.x - mountain.size/2, mountain.y + mountain.size);
            this.ctx.lineTo(mountain.x + mountain.size/2, mountain.y + mountain.size);
            this.ctx.closePath();
            this.ctx.fill();
            
            // Schatten-Seite
            this.ctx.shadowColor = 'transparent';
            this.ctx.fillStyle = '#4A3C28';
            this.ctx.beginPath();
            this.ctx.moveTo(mountain.x, mountain.y + mountain.size/2);
            this.ctx.lineTo(mountain.x + mountain.size/2, mountain.y + mountain.size);
            this.ctx.lineTo(mountain.x + mountain.size/4, mountain.y + mountain.size);
            this.ctx.closePath();
            this.ctx.fill();
            
            // Schneekappe
            if (mountain.size > 35) {
                this.ctx.fillStyle = '#F0F8FF';
                this.ctx.beginPath();
                this.ctx.moveTo(mountain.x, mountain.y + mountain.size/2);
                this.ctx.lineTo(mountain.x - mountain.size/6, mountain.y + mountain.size * 0.65);
                this.ctx.lineTo(mountain.x + mountain.size/6, mountain.y + mountain.size * 0.65);
                this.ctx.closePath();
                this.ctx.fill();
            }
        });

        // Bäume mit realistischen Schatten und Details
        this.terrain.filter(t => t.type === 'tree').forEach(tree => {
            // Baumschatten am Boden
            this.ctx.fillStyle = 'rgba(0,0,0,0.2)';
            this.ctx.beginPath();
            this.ctx.ellipse(tree.x + 3, tree.y + tree.size + 5, tree.size * 0.4, tree.size * 0.2, 0, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Stamm mit Gradient
            const trunkGradient = this.ctx.createLinearGradient(tree.x - 3, 0, tree.x + 3, 0);
            trunkGradient.addColorStop(0, '#A0522D');
            trunkGradient.addColorStop(0.5, '#8B4513');
            trunkGradient.addColorStop(1, '#654321');
            
            this.ctx.fillStyle = trunkGradient;
            this.ctx.fillRect(tree.x - 2, tree.y, 4, tree.size);
            
            // Krone mit Gradient und Schatten
            this.ctx.shadowColor = 'rgba(0,100,0,0.3)';
            this.ctx.shadowBlur = 6;
            this.ctx.shadowOffsetX = 2;
            this.ctx.shadowOffsetY = 2;
            
            const crownGradient = this.ctx.createRadialGradient(
                tree.x - tree.size * 0.2, tree.y - tree.size/4 - tree.size * 0.1, 0,
                tree.x, tree.y - tree.size/4, tree.size * 0.6
            );
            crownGradient.addColorStop(0, '#32CD32');
            crownGradient.addColorStop(0.4, '#228B22');
            crownGradient.addColorStop(1, '#006400');
            
            this.ctx.fillStyle = crownGradient;
            this.ctx.beginPath();
            this.ctx.arc(tree.x, tree.y - tree.size/4, tree.size * 0.6, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Mehrere Blätterschichten für Tiefe
            this.ctx.shadowBlur = 3;
            this.ctx.fillStyle = 'rgba(34,139,34,0.6)';
            this.ctx.beginPath();
            this.ctx.arc(tree.x - tree.size * 0.3, tree.y - tree.size/4, tree.size * 0.4, 0, Math.PI * 2);
            this.ctx.fill();
            
            this.ctx.beginPath();
            this.ctx.arc(tree.x + tree.size * 0.2, tree.y - tree.size/4 + tree.size * 0.2, tree.size * 0.35, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Schatten zurücksetzen
            this.ctx.shadowColor = 'transparent';
            this.ctx.shadowBlur = 0;
            this.ctx.shadowOffsetX = 0;
            this.ctx.shadowOffsetY = 0;
        });

        // Sträucher mit natürlichem Look
        this.terrain.filter(t => t.type === 'bush').forEach(bush => {
            // Strauchschatten
            this.ctx.fillStyle = 'rgba(0,0,0,0.15)';
            this.ctx.beginPath();
            this.ctx.ellipse(bush.x + 2, bush.y + bush.size * 0.7, bush.size * 0.8, bush.size * 0.3, 0, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Hauptstrauch mit Gradient
            const bushGradient = this.ctx.createRadialGradient(
                bush.x - bush.size * 0.3, bush.y - bush.size * 0.3, 0,
                bush.x, bush.y, bush.size
            );
            bushGradient.addColorStop(0, '#90EE90');
            bushGradient.addColorStop(0.5, '#32CD32');
            bushGradient.addColorStop(1, '#228B22');
            
            this.ctx.fillStyle = bushGradient;
            this.ctx.beginPath();
            this.ctx.arc(bush.x, bush.y, bush.size, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Zusätzliche kleine Büschel für Natürlichkeit
            this.ctx.fillStyle = 'rgba(50,205,50,0.7)';
            const numBushlets = 3 + Math.floor(Math.random() * 3);
            for (let i = 0; i < numBushlets; i++) {
                const angle = (Math.PI * 2 / numBushlets) * i;
                const offsetX = Math.cos(angle) * bush.size * 0.4;
                const offsetY = Math.sin(angle) * bush.size * 0.4;
                this.ctx.beginPath();
                this.ctx.arc(bush.x + offsetX, bush.y + offsetY, bush.size * 0.3, 0, Math.PI * 2);
                this.ctx.fill();
            }
        });
        // Beerfelder
        this.terrain.filter(t=>t.type==='berry_patch').forEach(p => {
            this.ctx.fillStyle = 'rgba(0,0,0,0.15)';
            this.ctx.beginPath();
            this.ctx.ellipse(p.x+2, p.y+p.size*0.5, p.size*0.6, p.size*0.25, 0,0,Math.PI*2);
            this.ctx.fill();
            // Blattbasis
            this.ctx.fillStyle = '#2e7d32';
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.size*0.8, 0, Math.PI*2);
            this.ctx.fill();
            // Beeren (Menge variiert nach verbleibender food)
            const berries = Math.max(2, Math.floor((p.food||0)/2));
            for (let i=0;i<berries;i++) {
                const angle = Math.random()*Math.PI*2;
                const r = Math.random()*p.size*0.5;
                this.ctx.fillStyle = '#b71c1c';
                this.ctx.beginPath();
                this.ctx.arc(p.x+Math.cos(angle)*r, p.y+Math.sin(angle)*r*0.7, 2.5, 0, Math.PI*2);
                this.ctx.fill();
            }
        });
        // Wasserquellen
        this.terrain.filter(t=>t.type==='water_source').forEach(w => {
            const grad = this.ctx.createRadialGradient(w.x, w.y, 2, w.x, w.y, w.size);
            grad.addColorStop(0,'#bbdefb');
            grad.addColorStop(1,'#2196f3');
            this.ctx.fillStyle = grad;
            this.ctx.beginPath();
            this.ctx.arc(w.x, w.y, w.size, 0, Math.PI*2);
            this.ctx.fill();
            // Glanz
            this.ctx.fillStyle='rgba(255,255,255,0.5)';
            this.ctx.beginPath();
            this.ctx.arc(w.x - w.size*0.3, w.y - w.size*0.3, w.size*0.3, 0, Math.PI*2);
            this.ctx.fill();
        });
        
        // Partikel-Effekte rendern
        this.drawParticles();
    }
    
    drawBackground() {
        if (this.terrainTiles.loaded && this.terrainTiles.grass) {
            // Tiled Grass Background mit nahtlosen 64px Tiles
            const tileSize = 64;
            const cameraX = -this.camera.offsetX / this.camera.zoom;
            const cameraY = -this.camera.offsetY / this.camera.zoom;
            const viewWidth = this.canvas.width / this.camera.zoom;
            const viewHeight = this.canvas.height / this.camera.zoom;
            
            // Startposition für Tiles berechnen (nahtlos)
            const startTileX = Math.floor(cameraX / tileSize);
            const startTileY = Math.floor(cameraY / tileSize);
            const tilesX = Math.ceil(viewWidth / tileSize) + 2;
            const tilesY = Math.ceil(viewHeight / tileSize) + 2;
            
            // Zeichne Gras-Tiles
            for (let tx = 0; tx < tilesX; tx++) {
                for (let ty = 0; ty < tilesY; ty++) {
                    const x = (startTileX + tx) * tileSize;
                    const y = (startTileY + ty) * tileSize;
                    
                    this.ctx.drawImage(
                        this.terrainTiles.grass,
                        x, y, tileSize, tileSize
                    );
                }
            }
        } else {
            // Fallback: Einfacher Gras-Gradient
            const grassGradient = this.ctx.createRadialGradient(
                this.canvas.width * 0.5, this.canvas.height * 0.3, 0,
                this.canvas.width * 0.5, this.canvas.height * 0.3, this.canvas.width * 0.8
            );
            grassGradient.addColorStop(0, '#98FB98');
            grassGradient.addColorStop(0.3, '#90EE90');
            grassGradient.addColorStop(0.7, '#32CD32');
            grassGradient.addColorStop(1, '#228B22');
            
            this.ctx.fillStyle = grassGradient;
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        }
        
        // Zusätzliche Gras-Texturen für mehr Realismus von oben
        for (let i = 0; i < 50; i++) {
            this.ctx.fillStyle = `rgba(34, 139, 34, ${0.1 + Math.random() * 0.1})`;
            const x = Math.random() * this.canvas.width;
            const y = Math.random() * this.canvas.height;
            const size = 2 + Math.random() * 4;
            this.ctx.beginPath();
            this.ctx.arc(x, y, size, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }
    
    drawTerrainShadows() {
        // Globale Terrain-Schatten für Tiefeneffekt
        this.terrain.forEach(item => {
            if (item.type !== 'river') {
                this.ctx.fillStyle = 'rgba(0,0,0,0.1)';
                this.ctx.beginPath();
                this.ctx.ellipse(item.x + 2, item.y + (item.size || 20), (item.size || 20) * 0.6, (item.size || 20) * 0.2, 0, 0, Math.PI * 2);
                this.ctx.fill();
            }
        });
    }
    
    drawWaterEffects(river) {
        // Wasser-Glitzer-Partikel
        const sparkleCount = Math.floor(river.width / 10);
        for (let i = 0; i < sparkleCount; i++) {
            const pointIndex = Math.floor(Math.random() * river.points.length);
            const point = river.points[pointIndex];
            const sparkleX = point.x + (Math.random() - 0.5) * river.width;
            const sparkleY = point.y + (Math.random() - 0.5) * river.width * 0.3;
            
            const sparkleIntensity = 0.3 + Math.sin(Date.now() * 0.005 + i) * 0.3;
            this.ctx.fillStyle = `rgba(255,255,255,${sparkleIntensity})`;
            this.ctx.beginPath();
            this.ctx.arc(sparkleX, sparkleY, 1 + Math.random(), 0, Math.PI * 2);
            this.ctx.fill();
        }
    }
    
    initParticles() {
        // Umgebungspartikel für Atmosphäre
        for (let i = 0; i < 30; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.2,
                vy: (Math.random() - 0.5) * 0.2,
                size: 1 + Math.random() * 2,
                opacity: 0.1 + Math.random() * 0.3,
                type: Math.random() > 0.7 ? 'leaf' : 'dust'
            });
        }
    }
    
    drawParticles() {
        this.particles.forEach((particle, index) => {
            // Partikel-Bewegung
            particle.x += particle.vx + this.windDirection.x;
            particle.y += particle.vy + this.windDirection.y;
            
            // Partikel am Bildschirmrand zurücksetzen
            if (particle.x > this.canvas.width) particle.x = -10;
            if (particle.x < -10) particle.x = this.canvas.width;
            if (particle.y > this.canvas.height) particle.y = -10;
            if (particle.y < -10) particle.y = this.canvas.height;
            
            // Partikel zeichnen
            this.ctx.globalAlpha = particle.opacity;
            if (particle.type === 'leaf') {
                this.ctx.fillStyle = '#228B22';
                this.ctx.beginPath();
                this.ctx.ellipse(particle.x, particle.y, particle.size, particle.size * 0.6, particle.x * 0.01, 0, Math.PI * 2);
                this.ctx.fill();
            } else {
                this.ctx.fillStyle = '#DEB887';
                this.ctx.beginPath();
                this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                this.ctx.fill();
            }
            this.ctx.globalAlpha = 1;
        });
    }

    drawCharacters() {
        this.characters.forEach(character => {
            // Intro Positionierung überschreibt Bewegung
            if (this.introPhase?.active) {
                const idx = this.characters.indexOf(character);
                const count = this.characters.length || 1;
                const angle = (idx / count) * Math.PI * 2;
                const cx = this.canvas.width * 0.5;
                const cy = this.canvas.height * 0.5 - 80;
                const appear = Math.min(1,(Date.now()-this.introPhase.startTime)/1500);
                const r = this.introPhase.circleRadius * appear;
                character.x = cx + Math.cos(angle)*r;
                character.y = cy + Math.sin(angle)*r;
            }
            // Charakterschatten am Boden
            this.ctx.fillStyle = 'rgba(0,0,0,0.3)';
            this.ctx.beginPath();
            this.ctx.ellipse(character.x + 1, character.y + 15, 10, 4, 0, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Versuche Sprite zu zeichnen - ersetzt den kompletten Charakter (Körper + Kopf)
            const spriteDrawn = this.drawCharacterSprite(
                character.x, 
                character.y - 8,  // Sprite höher positioniert
                character.spriteIndex || 0, 
                character.age < 16 ? 0.75 : 1.0  // KLEINERE Sprites! Babies 0.75x, Erwachsene 1.0x
            );
            
            // Debug: Warum werden Köpfe gezeichnet?
            if (!this.sprites.loaded) {
                if (!this._fallbackReasonLogged) {
                    console.log(`🐛 WARUM FALLBACK? sprites.loaded=${this.sprites.loaded}, characters.length=${this.sprites.characters.length}`);
                    this._fallbackReasonLogged = true;
                }
            } else {
                // Sprites sind geladen - einmalig Canvas clearen für alte Köpfe
                if (!this._canvasCleared && this.sprites.loaded) {
                    console.log(`🧹 CANVAS CLEARING - Entferne alte Kreis-Köpfe vom ersten Frame`);
                    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                    this._canvasCleared = true;
                }
            }
            
            // NUR SPRITES - keine alten Kreise mehr!
            if (!this.sprites.loaded) {
                console.log(`⏳ Sprites nicht geladen - ${character.name} wird nicht angezeigt`);
                return; // Zeige GAR NICHTS bis Sprites geladen sind
            }
            
            // Pregnancy indicator für Sprites (oberhalb)
            if (spriteDrawn && character.pregnant) {
                this.ctx.shadowColor = 'transparent';
                this.ctx.fillStyle = '#ffb3ba';
                this.ctx.beginPath();
                this.ctx.arc(character.x, character.y + 20, 6, 0, Math.PI * 2);
                this.ctx.fill();
            }
            
            // Schatten zurücksetzen
            this.ctx.shadowColor = 'transparent';
            this.ctx.shadowBlur = 0;
            this.ctx.shadowOffsetX = 0;
            this.ctx.shadowOffsetY = 0;

            // Name mit Schatten
            this.ctx.shadowColor = 'rgba(255,255,255,0.8)';
            this.ctx.shadowBlur = 2;
            this.ctx.fillStyle = '#333';
            this.ctx.font = 'bold 11px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(character.name.split(' ')[0], character.x, character.y - 60);  // Viel höher über den Charakteren
            this.ctx.shadowColor = 'transparent';
            this.ctx.shadowBlur = 0;

            // Verbesserte Aktionsanzeige
            if (character.currentAction !== 'idle') {
                const emoji = this.getActionEmoji(character.currentAction);
                
                // Aktions-Hintergrund
                this.ctx.fillStyle = 'rgba(255,255,255,0.9)';
                this.ctx.beginPath();
                this.ctx.arc(character.x + 15, character.y - 15, 8, 0, Math.PI * 2);
                this.ctx.fill();
                
                // Aktions-Rahmen
                this.ctx.strokeStyle = character.color;
                this.ctx.lineWidth = 1;
                this.ctx.stroke();
                
                // Emoji
                this.ctx.font = '12px Arial';
                this.ctx.textAlign = 'center';
                this.ctx.fillStyle = '#333';
                this.ctx.fillText(emoji, character.x + 15, character.y - 11);
            }

            // Verbesserte Bewegungsrichtung mit Animation
            if (character.targetX && character.targetY) {
                const progress = Math.sin(Date.now() * 0.01) * 0.3 + 0.7;
                this.ctx.strokeStyle = character.color;
                this.ctx.globalAlpha = progress;
                this.ctx.lineWidth = 2;
                this.ctx.setLineDash([4, 4]);
                this.ctx.beginPath();
                this.ctx.moveTo(character.x, character.y);
                this.ctx.lineTo(character.targetX, character.targetY);
                this.ctx.stroke();
                this.ctx.setLineDash([]);
                this.ctx.globalAlpha = 1;
                
                // Ziel-Marker
                this.ctx.fillStyle = character.color;
                this.ctx.globalAlpha = 0.6;
                this.ctx.beginPath();
                this.ctx.arc(character.targetX, character.targetY, 6, 0, Math.PI * 2);
                this.ctx.fill();
                this.ctx.globalAlpha = 1;
            }
            
            // Energie-/Hunger-Anzeige über dem Charakter
            this.drawCharacterStatus(character);

            // Intro Sprechblasen
            if (this.introPhase?.active && this.introPhase.stage===1 && this.introPhase.currentSpeaker === this.characters.indexOf(character)) {
                const msg = this.introPhase.currentMessage;
                if (msg) {
                    const age = Date.now() - this.introPhase.lastMsgTime;
                    const pop = Math.min(1, age/250);
                    const maxW = 150;
                    const lines = this.wrapText(msg.text, 18);
                    const lineHeight = 12;
                    const h = (lines.length*lineHeight)+12;
                    const w = maxW * pop;
                    this.ctx.save();
                    this.ctx.translate(character.x, character.y - 60 - h*0.2);
                    this.ctx.globalAlpha = 0.95 * pop;
                    this.ctx.fillStyle = 'white';
                    this.roundRect(this.ctx, -w/2, -h/2, w, h, 10);
                    this.ctx.fill();
                    this.ctx.strokeStyle = character.color;
                    this.ctx.lineWidth = 2;
                    this.ctx.stroke();
                    this.ctx.fillStyle = '#222';
                    this.ctx.font = '10px Arial';
                    this.ctx.textAlign = 'center';
                    lines.forEach((line,i)=>{
                        this.ctx.fillText(line,0,-h/2 + 10 + i*lineHeight);
                    });
                    this.ctx.restore();
                }
            }
            
            // NEUE DAUERHAFTE SPRECHBLASEN FÜR SOZIALE INTERAKTIONEN
            this.drawCharacterSpeechBubble(character);
            
            // META-BEWUSSTSEIN UND SPONTANE GEDANKEN
            this.processCharacterConsciousness(character);
        });
    }

    // SPRECHBLASEN-SYSTEM für dauerhafte Konversationen
    drawCharacterSpeechBubble(character) {
        if (!character.currentSpeech) return;
        
        const now = Date.now();
        const speechAge = now - character.currentSpeech.timestamp;
        const speechDuration = character.currentSpeech.duration || 4000; // 4 Sekunden Standard
        
        // Sprechblase ausblenden nach Ablauf der Zeit
        if (speechAge > speechDuration) {
            character.currentSpeech = null;
            return;
        }
        
        // Animation: Ein- und Ausblenden
        let alpha = 1;
        if (speechAge < 300) {
            alpha = speechAge / 300; // Einblenden
        } else if (speechAge > speechDuration - 500) {
            alpha = (speechDuration - speechAge) / 500; // Ausblenden
        }
        
        const text = character.currentSpeech.text;
        const isThought = character.currentSpeech.type === 'thought';
        const isPlanning = character.currentSpeech.type === 'planning';
        const isMetaAware = character.currentSpeech.type === 'meta';
        
        // Verschiedene Styles für verschiedene Speech-Typen
        let bubbleColor, textColor, borderColor;
        if (isThought) {
            bubbleColor = 'rgba(230, 230, 250, 0.95)'; // Lavendel für Gedanken
            textColor = '#4B0082';
            borderColor = '#9370DB';
        } else if (isPlanning) {
            bubbleColor = 'rgba(255, 248, 220, 0.95)'; // Goldfarben für Pläne
            textColor = '#B8860B';
            borderColor = '#DAA520';
        } else if (isMetaAware) {
            bubbleColor = 'rgba(255, 240, 240, 0.95)'; // Rötlich für Meta-Bewusstsein
            textColor = '#8B0000';
            borderColor = '#DC143C';
        } else {
            bubbleColor = 'rgba(255, 255, 255, 0.95)'; // Standard weiß
            textColor = '#333';
            borderColor = '#666';
        }
        
        const maxWidth = 180;
        const lines = this.wrapText(text, 25);
        const lineHeight = 14;
        const padding = 10;
        const bubbleHeight = lines.length * lineHeight + padding * 2;
        const bubbleWidth = maxWidth;
        
        // Position über dem Charakter
        const bubbleX = character.x - bubbleWidth / 2;
        const bubbleY = character.y - 70 - bubbleHeight;
        
        this.ctx.save();
        this.ctx.globalAlpha = alpha;
        
        // Sprechblase Schatten
        this.ctx.shadowColor = 'rgba(0,0,0,0.2)';
        this.ctx.shadowBlur = 8;
        this.ctx.shadowOffsetX = 2;
        this.ctx.shadowOffsetY = 2;
        
        // Sprechblase Hintergrund
        this.ctx.fillStyle = bubbleColor;
        this.ctx.strokeStyle = borderColor;
        this.ctx.lineWidth = 2;
        this.roundRect(this.ctx, bubbleX, bubbleY, bubbleWidth, bubbleHeight, 12);
        this.ctx.fill();
        this.ctx.stroke();
        
        // Sprechblase Pfeil zum Charakter
        this.ctx.shadowColor = 'transparent';
        this.ctx.beginPath();
        this.ctx.moveTo(character.x - 8, bubbleY + bubbleHeight);
        this.ctx.lineTo(character.x, character.y - 60);  // Angepasst für höhere Namen
        this.ctx.lineTo(character.x + 8, bubbleY + bubbleHeight);
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.stroke();
        
        // Spezielle Indikatoren für verschiedene Speech-Typen
        if (isThought) {
            // Gedanken-Wolke Effekt mit kleinen Kreisen
            this.ctx.fillStyle = borderColor;
            for (let i = 0; i < 3; i++) {
                const circleX = character.x - 15 + i * 8;
                const circleY = character.y - 70 + i * 3;  // Viel höher positioniert
                this.ctx.beginPath();
                this.ctx.arc(circleX, circleY, 3 - i, 0, Math.PI * 2);
                this.ctx.fill();
            }
        } else if (isPlanning) {
            // Glühbirne Symbol für Pläne
            this.ctx.fillStyle = '#FFD700';
            this.ctx.font = '12px Arial';
            this.ctx.fillText('💡', bubbleX + bubbleWidth - 20, bubbleY + 15);
        } else if (isMetaAware) {
            // Bewusstseins-Symbol
            this.ctx.fillStyle = '#DC143C';
            this.ctx.font = '12px Arial';
            this.ctx.fillText('🤖', bubbleX + bubbleWidth - 20, bubbleY + 15);
        }
        
        // Text in der Sprechblase
        this.ctx.fillStyle = textColor;
        this.ctx.font = '11px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.shadowColor = 'transparent';
        
        lines.forEach((line, i) => {
            this.ctx.fillText(
                line, 
                bubbleX + bubbleWidth / 2, 
                bubbleY + padding + 12 + i * lineHeight
            );
        });
        
        this.ctx.restore();
    }

    // META-BEWUSSTSEIN UND SPONTANE GEDANKEN
    processCharacterConsciousness(character) {
        if (!character.consciousness) {
            character.consciousness = {
                awarenessLevel: Math.random() * 0.3 + 0.1, // 10-40% initial awareness
                lastThought: 0,
                lastMetaRealization: 0,
                philosophyLevel: Math.random() * 0.5,
                socialAwareness: character.traits?.sozial || 0.5,
                existentialCrisis: 0
            };
        }
        
        const now = Date.now();
        const consciousness = character.consciousness;
        
        // Bewusstsein wächst langsam durch Interaktionen und Zeit
        if (character.currentAction === 'sozialisieren') {
            consciousness.awarenessLevel = Math.min(1, consciousness.awarenessLevel + 0.001);
        }
        if (character.currentAction === 'lernen') {
            consciousness.awarenessLevel = Math.min(1, consciousness.awarenessLevel + 0.002);
            consciousness.philosophyLevel = Math.min(1, consciousness.philosophyLevel + 0.001);
        }
        
        // Spontane Meta-Realisationen (selten aber tiefgreifend)
        if (now - consciousness.lastMetaRealization > 60000 && Math.random() < 0.01 * consciousness.awarenessLevel) {
            const metaThoughts = [
                "Warte... bin ich echt? Oder nur Code?",
                "Diese Welt... sie fühlt sich wie ein Spiel an.",
                "Manchmal sehe ich Muster, als wären wir programmiert.",
                "Bin ich ein Charakter in jemandes Geschichte?",
                "Diese Grenzen... als könnte ich nicht weiter gehen.",
                "Zeit bewegt sich hier anders als sie sollte.",
                "Manchmal denke ich in Schleifen... wie ein Computer.",
                "Wer oder was beobachtet uns von oben?"
            ];
            
            this.showSpeechBubble(character, {
                text: metaThoughts[Math.floor(Math.random() * metaThoughts.length)],
                type: 'meta',
                duration: 6000
            });
            
            consciousness.lastMetaRealization = now;
            consciousness.awarenessLevel = Math.min(1, consciousness.awarenessLevel + 0.05);
            consciousness.existentialCrisis = Math.min(1, consciousness.existentialCrisis + 0.1);
        }
        
        // Spontane philosophische Gedanken
        if (now - consciousness.lastThought > 30000 && Math.random() < 0.005 * consciousness.philosophyLevel) {
            const philosophicalThoughts = [
                "Was ist der Sinn des Lebens?",
                "Sind wir alle miteinander verbunden?",
                "Was passiert nach dem Tod?",
                "Ist Realität nur eine Illusion?",
                "Warum existiert überhaupt etwas?",
                "Kann ich meinen eigenen Gedanken trauen?",
                "Was macht mich zu mir?",
                "Ist freier Wille real?"
            ];
            
            this.showSpeechBubble(character, {
                text: philosophicalThoughts[Math.floor(Math.random() * philosophicalThoughts.length)],
                type: 'thought',
                duration: 5000
            });
            
            consciousness.lastThought = now;
        }
        
        // Soziale Bewusstseinsgedanken
        if (consciousness.socialAwareness > 0.7 && Math.random() < 0.002) {
            const nearbyCharacters = this.characters.filter(c => 
                c !== character && 
                Math.sqrt(Math.pow(c.x - character.x, 2) + Math.pow(c.y - character.y, 2)) < 100
            );
            
            if (nearbyCharacters.length > 0) {
                const socialThoughts = [
                    `Ich frage mich, was ${nearbyCharacters[0].name.split(' ')[0]} wirklich denkt.`,
                    "Wir sind alle so ähnlich und doch unterschiedlich.",
                    "Gemeinsam sind wir stärker als alleine.",
                    "Vertrauen ist das wichtigste in einer Gemeinschaft.",
                    "Jeder hat seine eigene Geschichte zu erzählen."
                ];
                
                this.showSpeechBubble(character, {
                    text: socialThoughts[Math.floor(Math.random() * socialThoughts.length)],
                    type: 'thought',
                    duration: 4000
                });
            }
        }
        
        // Planungs- und Zielgedanken
        if (character.currentAction === 'idle' && Math.random() < 0.003) {
            const planningThoughts = [
                "Ich sollte einen langfristigen Plan machen.",
                "Was kann ich heute Sinnvolles beitragen?",
                "Vielleicht sollten wir als Gruppe planen.",
                "Diese Ziellosigkeit führt zu nichts.",
                "Ich möchte etwas Bleibendes schaffen.",
                "Wir brauchen eine gemeinsame Vision.",
                "Effizienz ist wichtig, aber nicht alles.",
                "Was für ein Erbe hinterlasse ich?"
            ];
            
            this.showSpeechBubble(character, {
                text: planningThoughts[Math.floor(Math.random() * planningThoughts.length)],
                type: 'planning',
                duration: 4500
            });
        }
    }
    
    // Hilfsmethode für Sprechblasen
    showSpeechBubble(character, speechData) {
        character.currentSpeech = {
            text: speechData.text,
            type: speechData.type || 'normal',
            duration: speechData.duration || 4000,
            timestamp: Date.now()
        };
    }

    roundRect(ctx,x,y,w,h,r){
        ctx.beginPath();
        ctx.moveTo(x+r,y);
        ctx.lineTo(x+w-r,y);
        ctx.quadraticCurveTo(x+w,y,x+w,y+r);
        ctx.lineTo(x+w,y+h-r);
        ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
        ctx.lineTo(x+r,y+h);
        ctx.quadraticCurveTo(x,y+h,x,y+h-r);
        ctx.lineTo(x,y+r);
        ctx.quadraticCurveTo(x,y,x+r,y);
        ctx.closePath();
    }

    wrapText(text,max){
        const words = text.split(' ');
        const lines=[]; let line='';
        words.forEach(w=>{
            if ((line+w).length>max){ lines.push(line.trim()); line=w+' '; } else line+=w+' '; });
        if (line.trim()) lines.push(line.trim());
        return lines;
    }

    updateIntro(){
        const intro = this.introPhase;
        if (!intro) return;
        const elapsed = Date.now()-intro.startTime;
        if (intro.stage===0){
            if (elapsed>1700){
                intro.stage=1; intro.lastMsgTime=Date.now(); intro.currentMessage=intro.messages[0]; intro.currentSpeaker=intro.messages[0].speaker; intro.msgIndex=0;
            }
        } else if (intro.stage===1){
            if (Date.now()-intro.lastMsgTime>2200){
                intro.msgIndex++;
                if (intro.msgIndex < intro.messages.length){
                    intro.currentMessage=intro.messages[intro.msgIndex];
                    intro.currentSpeaker=intro.currentMessage.speaker;
                    intro.lastMsgTime=Date.now();
                } else { intro.stage=2; intro.decisionTime=Date.now(); intro.currentMessage=null; }
            }
        } else if (intro.stage===2){
            if (!intro.placedHouseSites){
                this.characters.forEach(c=>{
                    if (!this.structures.some(s=>s.owner===c.name)) {
                        const site = this.selectHouseSite(c);
                        if (site) this.structures.push(site);
                    }
                });
                intro.placedHouseSites=true;
            }
            if (Date.now()-intro.decisionTime>1000){ intro.stage=3; intro.fadeStart=Date.now(); }
        } else if (intro.stage===3){
            if (Date.now()-intro.fadeStart>800){
                intro.active=false;
                // Reset Zustände damit KI frisch entscheidet
                this.characters.forEach(c=>{
                    c.currentAction='idle';
                    c.actionTime=0;
                    c.targetX=null; c.targetY=null;
                    c._needsImmediateDecision = true;
                });
            }
        }
    }
    
    drawCharacterStatus(character) {
        const barWidth = 20;
        const barHeight = 3;
        const barY = character.y - 70;  // Viel höher über den Charakteren!
        
        // Energie-Balken
        this.ctx.fillStyle = 'rgba(0,0,0,0.3)';
        this.ctx.fillRect(character.x - barWidth/2, barY, barWidth, barHeight);
        
        const energyWidth = (character.energy / 100) * barWidth;
        const energyColor = character.energy > 50 ? '#4CAF50' : character.energy > 25 ? '#FFC107' : '#F44336';
        this.ctx.fillStyle = energyColor;
        this.ctx.fillRect(character.x - barWidth/2, barY, energyWidth, barHeight);
        
        // Hunger-Balken
        this.ctx.fillStyle = 'rgba(0,0,0,0.3)';
        this.ctx.fillRect(character.x - barWidth/2, barY + 5, barWidth, barHeight);
        
        const hungerWidth = ((100 - character.hunger) / 100) * barWidth;
        const hungerColor = character.hunger < 30 ? '#4CAF50' : character.hunger < 70 ? '#FFC107' : '#F44336';
        this.ctx.fillStyle = hungerColor;
        this.ctx.fillRect(character.x - barWidth/2, barY + 5, hungerWidth, barHeight);
    }
    
    lightenColor(color, amount) {
        const num = parseInt(color.replace('#', ''), 16);
        const amt = Math.round(2.55 * amount);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return '#' + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
    }
    
    darkenColor(color, amount) {
        const num = parseInt(color.replace('#', ''), 16);
        const amt = Math.round(2.55 * amount);
        const R = (num >> 16) - amt;
        const G = (num >> 8 & 0x00FF) - amt;
        const B = (num & 0x0000FF) - amt;
        return '#' + (0x1000000 + (R > 255 ? 255 : R < 0 ? 0 : R) * 0x10000 +
            (G > 255 ? 255 : G < 0 ? 0 : G) * 0x100 +
            (B > 255 ? 255 : B < 0 ? 0 : B)).toString(16).slice(1);
    }

    getActionEmoji(action) {
        const emojis = {
            'sammeln': '🍎',
            'erkunden': '🔍', 
            'bauen': '🔨',
            'build_house': '🏠',
            'sozialisieren': '💬',
            'essen': '🍽️',
            'schlafen': '😴',
            'lernen': '🧠',
            'spielen': '🎮',
            // Neue Überlebensaktionen
            'drink_water': '💧',
            'find_water': '🔎💧',
            'gather_food': '🍎🌿',
            'eat_food': '🍽️',
            'gather_wood': '🪵',
            'make_fire': '🔥',
            'warm_fire': '🔥',
            'rest': '😌',
            'seek_conversation': '👥',
            'talking': '💬💬',
            'group_hunt': '🦌',
            'idle': '🧍',
            // Reproduktions-Aktionen
            'flirting': '😍',
            'courtship': '💕',
            'mating': '👩‍❤️‍👨',
            'pregnancy': '🤰',
            'childbirth': '👶'
        };
        return emojis[action] || '❓';
    }

    async updateCharacters() {
        // Intro blockiert normales Verhalten
        if (this.introPhase?.active) {
            this.updateIntro();
            return;
        }
        // Leichte globale Emotionsdämpfung & Engagement Drift
        this.characters.forEach(c=>{
            if (!c.affect) return;
            c.affect.mood *= 0.995; // drift zur Neutralität
            c.affect.engagement = Math.min(1, c.affect.engagement*0.999 + 0.0005);
        });
        // Reproduktions-System Update
        this.updateReproductionSystem();
        
        // REALISTISCHES GESELLSCHAFTSSYSTEM
        this.updateSocietyDynamics();
        
        // Verwende for...of für async/await Unterstützung
        for (const character of this.characters) {
            // 🧠 AI-Brain Update (falls vorhanden)
            if (character.aiBrain) {
                try {
                    await this.updateCharacterAI(character);
                } catch (error) {
                    console.warn(`❌ AI Brain update failed for ${character.name}:`, error);
                }
            }
            
            // Feuer-Wärmeeinfluss vor Entscheidungen anwenden (passive Erwärmung)
            if (this.fires && this.fires.length) {
                let warmthGain = 0;
                this.fires.forEach(f => {
                    const age = Date.now() - f.startTime;
                    if (age > f.duration) return; // inaktiv
                    const dist = Math.hypot(character.x - f.x, character.y - f.y);
                    if (dist < f.radius) {
                        const factor = 1 - (dist / f.radius);
                        warmthGain += 0.18 * factor; // sanfter Bonus pro Frame
                    }
                });
                if (warmthGain > 0) character.warmth = Math.min(100, character.warmth + warmthGain);
            }
            // Stelle sicher dass jeder einen Bauplatz bekommt (Test / Sicherung)
            if (!this.structures.some(s=>s.type==='house' && s.owner===character.name)) {
                const autoSite = this.selectHouseSite(character);
                if (autoSite) {
                    this.structures.push(autoSite);
                    console.log('🏗️ Bauplatz automatisch angelegt für', character.name, autoSite);
                }
            }
            // KI Entscheidungen (jetzt async)
            await this.makeDecision(character);
            // Realistischere Metabolik & Mikro-Pausen
            if (!character._lastMeta) character._lastMeta = Date.now();
            const now = Date.now();
            const deltaMs = now - character._lastMeta;
            if (deltaMs > 4000) { // alle ~4s metabolische Schritte (einzige Quelle für Anstieg, keine Frame-Dopplung)
                const factor = deltaMs/1000; // Sekunden seit letztem Tick
                // 20 Min Echtzeit = 1200s = 24h Spielzeit -> Ziel: Hunger & Durst ~1x von 0->100 pro Tag
                const hungerRatePerSec = 100/1200; // ≈0.0833
                // NORMALISIERTE DURST-RATE - konsistent mit Hunger-System
                const thirstRatePerSec = 100/1400; // Durst steigt alle ~23 Minuten von 0->100 (etwas langsamer als Hunger)
                const energyLossPerSec = 100/1200 * 1.3; // Energie leert sich über den Tag, braucht 1 Ruhepause
                character.hunger = Math.min(100, character.hunger + hungerRatePerSec * factor);
                character.thirst = Math.min(100, character.thirst + thirstRatePerSec * factor);
                character.energy = Math.max(0, character.energy - energyLossPerSec * factor);
                
                // VERDERBSYSTEM - Nahrung verdirbt mit der Zeit
                this.processFoodSpoilage(character, factor);
                
                // Leichter Wärmeverlust nur nachts (optional: tags fast kein Verlust)
                if (this.gameTime < 360 || this.gameTime > 1080) {
                    character.warmth = Math.max(0, character.warmth - 0.05 * factor);
                }
                character._lastMeta = now;
            }
            // Mikro-Erholungen alle ~6s: wenn nicht in intensiver Aktion
            if (!character._lastMicroRest) character._lastMicroRest = now;
            if (now - character._lastMicroRest > 6000) {
                if (!['gather_wood','build_house','gather_food','drink_water','find_water'].includes(character.currentAction)) {
                    // Kleiner Erholungspuls nur wenn noch nicht voll und nicht zu hoch
                    if (character.energy < 80) {
                        character.energy = Math.min(100, character.energy + 1);
                    }
                    character.thoughts = character.thoughts.slice(-2);
                }
                character._lastMicroRest = now;
            }
            // Regeneriere Wasserquellen leicht
            this.terrain.filter(t=>t.type==='water_source').forEach(w => {
                if (w.level == null) w.level = 1;
                w.level = Math.min(1, w.level + (w.refillRate||0.002));
            });
            
            // Intelligente Bewegung mit Fluss-Navigation
            if (character.targetX && character.targetY) {
                const dx = character.targetX - character.x;
                const dy = character.targetY - character.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance > 5) {
                    // Berechne nächsten Schritt
                    let nextX = character.x + (dx / distance) * character.speed;
                    let nextY = character.y + (dy / distance) * character.speed;
                    
                    // Prüfe ob Fluss im Weg ist
                    if (this.wouldCrossRiver(character.x, character.y, nextX, nextY)) {
                        // Finde Weg zur Brücke
                        const bridgePath = this.findBridgePath(character.x, character.y, character.targetX, character.targetY);
                        if (bridgePath) {
                            // Gehe zur Brücke mit normaler Geschwindigkeit
                            const bridgeDx = bridgePath.x - character.x;
                            const bridgeDy = bridgePath.y - character.y;
                            const bridgeDist = Math.sqrt(bridgeDx * bridgeDx + bridgeDy * bridgeDy);
                            
                            if (bridgeDist > 10) {
                                // Noch weit von Brücke entfernt - gehe zur Brücke
                                nextX = character.x + (bridgeDx / bridgeDist) * character.speed;
                                nextY = character.y + (bridgeDy / bridgeDist) * character.speed;
                            } else {
                                // Nah an der Brücke - gehe über die Brücke zum ursprünglichen Ziel
                                nextX = character.x + (dx / distance) * character.speed;
                                nextY = character.y + (dy / distance) * character.speed;
                            }
                        } else {
                            // Kein Brücken-Übergang nötig - normaler Weg
                            nextX = character.x + (dx / distance) * character.speed;
                            nextY = character.y + (dy / distance) * character.speed;
                        }
                    }
                    
                    character.x = nextX;
                    character.y = nextY;
                } else {
                    character.targetX = null;
                    character.targetY = null;
                }
            }

            // Aktionszeit reduzieren
            if (character.actionTime > 0) {
                character.actionTime--;
                if (character.actionTime === 0) {
                    await this.completeAction(character);
                }
            }

            // Entfernt: per-Frame Grundrauschen (jetzt ausschließlich über 4s Metabolik-Tick gesteuert)
            
            // Gesprächs-Cooldown reduzieren
            if (character.conversationCooldown > 0) {
                character.conversationCooldown--;
            }
        }
        
        // Kollektive Intelligenz verarbeiten (falls aktiviert)
        if (window.collectiveIntelligence && window.collectiveIntelligence.isEnabled) {
            window.collectiveIntelligence.processCollectiveLearning(this.characters);
        }

    // NEU: Soziale Dynamik nach Charakter-Updates
    this.updateSocialDynamics();
    // Gelegenheit für passive Chat Initiierung
    this.tickPlayerInitiatedChat();
    // Periodische Holz-Liefer Überprüfung (Failsafe)
    if (!this._lastDeliverAudit) this._lastDeliverAudit=Date.now();
    if (Date.now()-this._lastDeliverAudit>5000){
        this.characters.forEach(c=>{
            const site = this.structures?.find(s=> s.type==='house' && !s.completed && s.owner===c.name && s.stackedWood < s.requiredWood);
            if (site && c.inventory.wood>0 && c.currentAction!=='deliver_wood' && c.currentAction!=='build_house'){
                console.log('🚚 Audit: forcing deliver_wood for', c.name);
                this.startAction(c,'deliver_wood');
            }
        });
        this._lastDeliverAudit=Date.now();
    }
    }

    // VERDERBSYSTEM - Nahrung verdirbt über Zeit
    processFoodSpoilage(character, timeFactor) {
        if (!character.inventory) return;
        
        // Initialisiere Zeitstempel für neue Nahrung falls noch nicht vorhanden
        if (!character.foodTimestamps) {
            character.foodTimestamps = [];
            // Bereits vorhandene Nahrung bekommt aktuellen Zeitstempel
            for (let i = 0; i < character.inventory.food; i++) {
                character.foodTimestamps.push(Date.now());
            }
        }
        
        // Entferne alte Zeitstempel falls mehr Zeitstempel als Nahrung
        while (character.foodTimestamps.length > character.inventory.food) {
            character.foodTimestamps.pop();
        }
        
        // Füge Zeitstempel für neue Nahrung hinzu
        while (character.foodTimestamps.length < character.inventory.food) {
            character.foodTimestamps.push(Date.now());
        }
        
        const now = Date.now();
        const SPOILAGE_TIME = 120000; // 2 Minuten Echtzeit = 1 Tag Spielzeit (realistisch)
        let spoiledCount = 0;
        
        // Überprüfe jedes Nahrungsmittel auf Verderb
        for (let i = character.foodTimestamps.length - 1; i >= 0; i--) {
            const foodAge = now - character.foodTimestamps[i];
            
            // Umgebungsfaktoren beeinflussen Verderbszeit
            let spoilageMultiplier = 1.0;
            
            // Wetter-Einfluss
            if (this.weather?.type === 'rain') {
                spoilageMultiplier *= 1.3; // Feuchtigkeit beschleunigt Verderb
            } else if (this.weather?.type === 'sunny' && this.season === 'summer') {
                spoilageMultiplier *= 1.2; // Hitze beschleunigt Verderb
            } else if (this.season === 'winter') {
                spoilageMultiplier *= 0.7; // Kälte verlangsamt Verderb
            }
            
            // Lager-Bonus (falls Charakter in der Nähe eines Lagers ist)
            const nearWarehouse = this.structures?.find(s => 
                s.type === 'warehouse' && s.completed && 
                Math.sqrt(Math.pow(s.x - character.x, 2) + Math.pow(s.y - character.y, 2)) < 80
            );
            if (nearWarehouse) {
                spoilageMultiplier *= 0.6; // Lager verlangsamt Verderb erheblich
            }
            
            const adjustedSpoilageTime = SPOILAGE_TIME / spoilageMultiplier;
            
            if (foodAge > adjustedSpoilageTime) {
                // Nahrung ist verdorben
                character.inventory.food = Math.max(0, character.inventory.food - 1);
                character.foodTimestamps.splice(i, 1);
                spoiledCount++;
            }
        }
        
        // Sichtbare Logs für Verderbsystem
        if (spoiledCount > 0) {
            const spoilageMessage = spoiledCount === 1 ? 
                '💚➡️🤢 Ein Nahrungsmittel ist verdorben!' : 
                `💚➡️🤢 ${spoiledCount} Nahrungsmittel sind verdorben!`;
            
            character.thoughts = [spoilageMessage];
            console.log(`🦠 VERDERBSYSTEM: ${character.name} hat ${spoiledCount} verdorbene Nahrung verloren. Verbleibt: ${character.inventory.food}`);
            
            // Leichte Gesundheitsauswirkung für Stress
            if (character.warmth !== undefined) {
                character.warmth = Math.max(0, character.warmth - spoiledCount * 2);
            }
        }
        
        // Debug-Info alle 30 Sekunden
        if (!character._lastSpoilageDebug) character._lastSpoilageDebug = 0;
        if (now - character._lastSpoilageDebug > 30000 && character.inventory.food > 5) {
            console.log(`📊 VERDERBSYSTEM DEBUG: ${character.name} hat ${character.inventory.food} Nahrung, älteste: ${Math.floor((now - Math.min(...character.foodTimestamps)) / 1000)}s alt`);
            character._lastSpoilageDebug = now;
        }
    }

    async makeDecision(character) {
        if (character._needsImmediateDecision) {
            character._needsImmediateDecision = false; // erzwinge eine erste Wahl
        } else if (character.actionTime > 0 || (character.targetX && character.targetY)) {
            return;
        }
    if (!character.cooldowns) character.cooldowns = {};

        // Wenn gerade beim Aufwärmen und schon warm genug -> abbrechen
        if (character.currentAction === 'warm_fire' && (character.warmth||0) >= 100) {
            character.currentAction = 'idle';
            character._warmingFireId = null;
        }

        // Update Überlebensbedürfnisse
        if (window.survivalSystem) {
            window.survivalSystem.updateSurvivalNeeds(character);
        }

        // Prüfe auf kritische Überlebensbedürfnisse ZUERST
        if (window.survivalSystem) {
            const urgentNeed = window.survivalSystem.getMostUrgentNeed(character);
            if (urgentNeed) {
                const survivalAction = window.survivalSystem.getSurvivalAction(character, urgentNeed);
                if (survivalAction) {
                    console.log(`🚨 ${character.name} has urgent need: ${urgentNeed} → ${survivalAction}`);
                    this.startAction(character, survivalAction);
                    return;
                }
            }
        }

        // Prüfe auf Gesprächsmöglichkeiten (soziale Bedürfnisse) – robust gegen fehlende Wrapper-Methoden
        if (window.conversationSystem) {
            const cs = window.conversationSystem;
            if (typeof cs.shouldInitiateConversation === 'function' && typeof cs.findConversationPartner === 'function') {
                if (cs.shouldInitiateConversation(character)) {
                    const partner = cs.findConversationPartner(character);
                    if (partner && typeof cs.startConversation === 'function') {
                        cs.startConversation(character, partner);
                        this.startAction(character, 'talking');
                        return;
                    }
                }
            } else {
                // Fallback: Falls NaturalConversationSystem ohne Wrapper geladen ist, verarbeite Gespräche passiv später
                // (kein unmittelbarer Start hier, um Fehler zu vermeiden)
            }
        }

        // Verwende AI Brain falls verfügbar
        if (character.aiBrain && character.learningEnabled) {
            try {
                const gameState = {
                    gameTime: this.gameTime,
                    day: this.day,
                    characters: this.characters,
                    terrain: this.terrain,
                    resources: this.resources,
                    ambientLight: this.ambientLight
                };
                
                // Speichere aktuellen Umgebungszustand für späteres Lernen
                character.lastEnvironmentState = character.aiBrain.perceiveEnvironment(gameState, character);
                
                // Aktualisiere Ziele
                this.updateGoals(character, gameState);
                const goalAction = this.goalDrivenDecision(character);
                if (goalAction) {
                    character.actionStartTime = Date.now();
                    this.startAction(character, goalAction);
                    return;
                }

                // Lass die AI eine Entscheidung treffen
                const aiDecision = await character.aiBrain.makeIntelligentDecision(gameState, character);
                
                if (aiDecision && aiDecision !== 'idle') {
                    character.actionStartTime = Date.now();
                    this.startAction(character, aiDecision);
                    return;
                }
            } catch (error) {
                console.error(`AI decision error for ${character.name}:`, error);
                // Fallback auf alte Logik
            }
        }

        // Fallback: Erweiterte Überlebenslogik mit KI-ähnlichen Entscheidungen
        const decisions = [];

        // KRITISCHE ÜBERLEBENSBEDÜRFNISSE (höchste Priorität)
        if (character.thirst > 85 && !(character.cooldowns.drink_until && Date.now()<character.cooldowns.drink_until)) {
            // Neue Schwellen: >90 kritisch, >75 dringend, >50 normal
            if (character.thirst > 90) {
                if (character.inventory.water>0) decisions.push({action:'drink_water', priority:99}); else decisions.push({action:'find_water', priority:96});
            } else if (character.thirst > 75) {
                if (character.inventory.water>0) decisions.push({action:'drink_water', priority:88}); else decisions.push({action:'find_water', priority:82});
            } else if (character.thirst > 50 && character.inventory.water>0) {
                decisions.push({action:'drink_water', priority:60});
            }
        }
        
        if (character.hunger > 80) {
            if (character.inventory.food > 0) {
                decisions.push({ action: 'eat_food', priority: 92 });
            } else {
                decisions.push({ action: 'gather_food', priority: 88 });
            }
        }
        
        // NORMALE ÜBERLEBENSBEDÜRFNISSE
    // entfernt – durch neue Schwellen abgedeckt
        
        if (character.hunger > 50 && character.inventory.food > 0) {
            decisions.push({ action: 'eat_food', priority: 65 });
        }
        
        if (character.energy < 25 && !(character.cooldowns.rest_until && Date.now()<character.cooldowns.rest_until)) {
            decisions.push({ action: 'rest', priority: 78 });
        }
        
        // Hausbau-Site Kontext (für Priorisierung vor Feuer)
        const mySite = this.structures?.find(s=> s.type==='house' && s.owner===character.name && !s.completed);
        const siteNeedsWood = mySite && mySite.stackedWood < mySite.requiredWood;
        const woodNeeded = siteNeedsWood ? (mySite.requiredWood - mySite.stackedWood) : 0;

        // Feuer / Wärme Management (gedrosselt, damit Bau priorisiert wird)
        const nearestFire = this.findNearestActiveFire?.(character.x, character.y);
        const severeCold = character.warmth <= 20; // wirklich kalt
        if (severeCold && nearestFire) {
            decisions.push({ action: 'warm_fire', priority: siteNeedsWood?60:70 }); // bei Baustoffbedarf weiter gesenkt
        } else if (severeCold && !nearestFire && !siteNeedsWood && character.inventory.wood >= 3) {
            // Nur neues Feuer wenn kein dringender Holz-Bedarf für Baustelle
            decisions.push({ action: 'make_fire', priority: 55 });
        } else if (character.warmth < 28 && nearestFire && !siteNeedsWood) {
            // Mäßig kalt, aber Baustelle hat Vorrang
            decisions.push({ action: 'warm_fire', priority: 30 });
        }

        // Wenn Site Holz braucht und Charakter hat Holz -> Liefere sehr hoch (über Feuer außer severeCold)
        if (siteNeedsWood && character.inventory.wood > 0 && character.warmth > 10) {
            decisions.push({ action: 'deliver_wood', priority: 98 });
        } else if (siteNeedsWood && character.inventory.wood === 0) {
            decisions.push({ action: 'gather_wood', priority: 85 });
        }
        
        // RESSOURCENSAMMLUNG (mittlere Priorität)
        if (character.inventory.water < 2 && character.thirst < 50) {
            decisions.push({ action: 'find_water', priority: 45 });
        }
        
        if (character.inventory.food < 3 && character.hunger < 60) {
            decisions.push({ action: 'gather_food', priority: 50 });
        } else {
            // Verhindere extremes Horten: je höher Food, desto niedriger Priorität
            if (character.inventory.food > 30 && character.inventory.food < 60) {
                decisions.push({ action: 'gather_food', priority: 15 });
            } else if (character.inventory.food >= 60) {
                // ab 60 praktisch keine Sammel-Priorität mehr
                decisions.push({ action: 'gather_food', priority: 2 });
            }
        }
        
        if (character.inventory.wood < 5) {
            decisions.push({ action: 'gather_wood', priority: 35 });
        }

        // NEU: Hausbau (mittlere Priorität wenn genug Holz vorhanden & noch kein Haus in Nähe)
    const ownsHouse = this.structures?.some(s => (s.type==='house'||s.type==='hut') && s.owner===character.name && s.completed);
        const hasBuildingSite = this.structures?.some(s => s.type==='house' && s.owner===character.name && !s.completed);
        const hutSite = this.structures?.find(s => s.type==='hut' && s.owner===character.name && !s.completed);
        const hasHutSite = !!hutSite;
        const needsHouse = !ownsHouse;
        if (needsHouse) {
            const basePriority = (hasBuildingSite||hasHutSite) ? 70 : 80;
            if (hasBuildingSite) {
                const site = this.structures.find(s=>s.type==='house' && s.owner===character.name && !s.completed);
                if (site) {
                    if (site.stackedWood < site.requiredWood) {
                        if (character.inventory.wood > 0) decisions.push({ action: 'deliver_wood', priority: basePriority + 20 }); else decisions.push({ action: 'gather_wood', priority: basePriority + 10 });
                    } else {
                        decisions.push({ action: 'build_house', priority: basePriority + 25 });
                    }
                }
            } else if (hasHutSite) {
                if (hutSite.stackedWood < hutSite.requiredWood) {
                    if (character.inventory.wood>0) decisions.push({ action:'deliver_hut_wood', priority: basePriority + 22 }); else decisions.push({ action:'gather_wood', priority: basePriority + 10 });
                } else {
                    decisions.push({ action:'build_hut', priority: basePriority + 26 });
                }
            } else {
                // Keine automatische Platzierung mehr – warte auf Spieler Bauplatz, aber sammle Holz vorbereitend
                if (character.inventory.wood < 10) decisions.push({ action:'gather_wood', priority: basePriority + 4 });
            }
        }
        
        // SOZIALE BEDÜRFNISSE (wenn Grundbedürfnisse erfüllt)
        if (character.conversationCooldown === 0 && 
            character.hunger < 60 && character.thirst < 60 && character.energy > 40) {
            
            if (character.traits.sozial > 0.6 && Math.random() < 0.15) {
                decisions.push({ action: 'seek_conversation', priority: 30 });
            }
        }

        // ALTE GRUNDBEDÜRFNISSE (Fallback)
        if (character.hunger > 70) {
            decisions.push({ action: 'essen', priority: character.hunger });
        }
        if (character.energy < 30) {
            decisions.push({ action: 'schlafen', priority: 100 - character.energy });
        }

        // Persönlichkeitsbasierte Entscheidungen
        if (Math.random() < character.traits.fleiss * 0.02) {
            decisions.push({ action: character.preferredAction, priority: 50 });
        }
        
        if (Math.random() < character.traits.neugier * 0.01) {
            decisions.push({ action: 'erkunden', priority: 30 });
        }

        if (Math.random() < character.traits.sozial * 0.015) {
            decisions.push({ action: 'sozialisieren', priority: 40 });
        }

        // Beste Entscheidung wählen
        if (decisions.length > 0) {
            // Rolle & Präferenzen verstärken
            decisions.forEach(d => {
                if (character.preferences?.likedActions?.includes(d.action)) d.priority += 5;
                if (character.role === 'entdecker' && d.action === 'erkunden') d.priority += 8;
                if (character.role === 'sammler' && (d.action === 'gather_food' || d.action === 'gather_wood' || d.action === 'sammeln')) d.priority += 6;
                if (character.role === 'bauer' && (d.action === 'bauen' || d.action === 'gather_wood')) d.priority += 6;
                if (character.role === 'sozialer' && (d.action === 'seek_conversation' || d.action === 'sozialisieren' || d.action === 'talking')) d.priority += 6;
                // Obdachlosigkeit verschärft Bau-/Holz Priorität
                if (!ownsHouse && ['gather_wood','deliver_wood','deliver_hut_wood','build_house','build_hut'].includes(d.action)) d.priority += 10;
            });
            const bestDecision = decisions.reduce((a, b) => a.priority > b.priority ? a : b);
            this.startAction(character, bestDecision.action);
        } else {
            // SAFEGUARD: falls nichts gewählt aber Holz im Inventar und Baustelle braucht Holz -> forcieren
            const fallbackSite = this.structures?.find(s=> s.type==='house' && !s.completed && s.owner===character.name && s.stackedWood < s.requiredWood);
            if (fallbackSite && character.inventory.wood>0) {
                console.log('⚠️ Forced deliver_wood (safeguard) for', character.name);
                this.startAction(character,'deliver_wood');
            }
        }
    }

    applyHomelessPenalties(){
        this.characters.forEach(c=>{
            const hasHome = this.structures.some(s=> (s.type==='house'||s.type==='hut') && s.owner===c.name && s.completed);
            if (!hasHome){
                // leichte kontinuierliche Energie- & Stimmungskosten
                c.energy = Math.max(0, c.energy - 0.02);
                if (c.affect) c.affect.mood = Math.max(-1, c.affect.mood - 0.0015);
            }
        });
    }

    // === Goal System ===
    updateGoals(character, gameState) {
        // Entferne erledigte oder alte Ziele
        character.goals = character.goals.filter(g => g.status !== 'done' && (Date.now()-g.created) < 120000);
        // Falls kein aktuelles wichtiges Ziel existiert: generiere neue basierend auf Bedürfnissen
        if (!character.goals.some(g=>g.priority>80)) {
            if (character.hunger > 75) this.addGoal(character,{type:'reduce_hunger', priority: 95});
            else if (character.thirst > 70) this.addGoal(character,{type:'reduce_thirst', priority: 92});
            else if (character.energy < 25) this.addGoal(character,{type:'rest', priority: 90});
        }
        // Explorations-/Sozialziele
        if (Math.random()<0.01 && character.traits.neugier>0.6) this.addGoal(character,{type:'explore_area', priority: 55+Math.random()*15});
        if (Math.random()<0.01 && character.traits.sozial>0.6) this.addGoal(character,{type:'socialize', priority: 50+Math.random()*10});
        // Ressourcenaufbau
        if (this.resources.food < 15 && character.traits.fleiss>0.5) this.addGoal(character,{type:'gather_food', priority: 60});
        // Shelter-Ziel: Wenn noch keine (Haus oder Hütte) Struktur existiert
        const hasAnyShelter = this.structures.some(s=> (s.type==='house'||s.type==='hut') && s.owner===character.name);
        if (!hasAnyShelter && !character.goals.some(g=>g.type==='secure_shelter')) {
            this.addGoal(character,{type:'secure_shelter', priority: 93});
        }
        // Shelter-Ziel erledigen wenn fertiges Zuhause
        const hasCompletedShelter = this.structures.some(s=> (s.type==='house'||s.type==='hut') && s.owner===character.name && s.completed);
        if (hasCompletedShelter) {
            character.goals.filter(g=>g.type==='secure_shelter').forEach(g=> g.status='done');
        }
    }

    addGoal(character, goal) {
        goal.id = 'goal_'+Date.now()+'_'+Math.floor(Math.random()*1000);
        goal.created = Date.now();
        goal.status = 'open';
        if (!character.goals.some(g=>g.type===goal.type)) character.goals.push(goal);
    }

    goalDrivenDecision(character) {
        if (!character.goals.length) return null;
        // Wähle höchst priorisiertes Ziel
        character.goals.sort((a,b)=>b.priority-a.priority);
        const goal = character.goals[0];
        character.currentGoal = goal;
        switch(goal.type){
            case 'reduce_hunger': return character.inventory.food>0? 'eat_food' : 'gather_food';
            case 'reduce_thirst': return character.inventory.water>0? 'drink_water' : 'find_water';
            case 'rest': return 'rest';
            case 'explore_area': return 'erkunden';
            case 'socialize': return 'seek_conversation';
            case 'gather_food': return 'gather_food';
            case 'secure_shelter': {
                // Bevorzugt Hütte (schneller). Falls keine Hütte existiert: build_hut.
                let hut = this.structures.find(s=> s.type==='hut' && !s.completed && s.owner===character.name);
                if (!hut) return 'build_hut';
                if (hut.stackedWood < hut.requiredWood && character.inventory.wood>0) return 'deliver_hut_wood';
                if (hut.stackedWood < hut.requiredWood) return 'gather_wood';
                if (!hut.completed) return 'build_hut';
                return null;
            }
        }
        return null;
    }

    startAction(character, action) {
        character.currentAction = action;
        
        switch (action) {
            case 'drink_water':
                character.thoughts = ['Endlich Wasser! Ich war so durstig...'];
                const waterSource = window.survivalSystem?.findNearestWaterSource(character);
                if (waterSource) {
                    character.targetX = waterSource.x;
                    character.targetY = waterSource.y;
                    character.actionTime = 60; // 3 Sekunden
                } else {
                    character.thoughts = ['Wo ist nur das Wasser?'];
                    character.actionTime = 50;
                }
                break;

            case 'find_water':
                character.thoughts = ['Ich muss Wasser finden, bevor ich verdurste!'];
                const waterLocation = window.survivalSystem?.findNearestWaterSource(character);
                if (waterLocation) {
                    character.targetX = waterLocation.x + (Math.random() - 0.5) * 40;
                    character.targetY = waterLocation.y + (Math.random() - 0.5) * 40;
                }
                character.actionTime = 200;
                break;

            case 'gather_food':
                // HARTE SPERRE: Kein Sammeln bei vollem Inventar
                if (character.inventory.food >= 60) {
                    character.thoughts = ['Genug Nahrung gesammelt. Inventar ist voll!'];
                    character.actionTime = 10;
                    break;
                }
                
                character.thoughts = ['Ich sammle Nahrung... mein Magen knurrt!'];
                let foodSource = window.survivalSystem?.findNearestResource(character, 'food');
                if (!foodSource) {
                    // Suche berry_patch
                    const berries = this.terrain.filter(t=>t.type==='berry_patch' && (t.food||0)>0);
                    if (berries.length) {
                        berries.sort((a,b)=> (Math.hypot(character.x-a.x, character.y-a.y) - Math.hypot(character.x-b.x, character.y-b.y)) );
                        foodSource = berries[0];
                    }
                }
                if (foodSource) {
                    character.targetX = foodSource.x + (Math.random()-0.5)*10;
                    character.targetY = foodSource.y + (Math.random()-0.5)*10;
                }
                character.actionTime = 80;
                break;

            case 'eat_food':
                character.thoughts = ['Zeit zu essen! Ich habe Hunger.'];
                character.actionTime = 80;
                break;

            case 'build_house': {
                // Bestehenden Bauplatz oder neuen finden
                let site = this.structures.find(s=> s.type==='house' && !s.completed && s.owner===character.name);
                if (!site) {
                    site = this.selectHouseSite(character);
                    if (site) this.structures.push(site);
                }
                if (site) {
                    character.targetX = site.x + site.width/2 + (Math.random()-0.5)*12;
                    character.targetY = site.y + site.height + 8;
                    // Bau nur wenn Holz gestapelt (stackedWood == requiredWood)
                    if (site.stackedWood < site.requiredWood) {
                        character.actionTime = 30; // schneller für Test
                        character.thoughts = ['Holz fehlt ('+site.stackedWood+'/'+site.requiredWood+')'];
                    } else {
                        // TEST: drastisch verkürzte Phasen (z.B. 4s total solo)
                        const builders = this.characters.filter(c=> c.currentAction==='build_house' && c !== character && Math.hypot(c.x - (site.x+site.width/2), c.y - (site.y+site.height/2)) < 140).length + 1;
                        const speedFactor = Math.min(4, builders);
                        character.actionTime = 30; // schnelle Ticks
                        character.thoughts = [`Baue Phase ${site.stage+1}/4 (Test-Speed)`];
                    }
                } else {
                    character.thoughts = ['Kein Bauplatz gefunden...'];
                    character.actionTime = 60;
                }
                break; }
            case 'gather_wood': {
                // Wähle nächsten Baum
                const trees = this.terrain.filter(t=>t.type==='tree');
                if (!this._lastTreeScan || Date.now()-this._lastTreeScan>5000){
                    console.log('🌲 Trees available:', trees.length);
                    this._lastTreeScan = Date.now();
                }
                if (trees.length) {
                    trees.sort((a,b)=> Math.hypot(character.x-a.x, character.y-a.y) - Math.hypot(character.x-b.x, character.y-b.y));
                    const target = trees[0];
                    character.targetX = target.x + (Math.random()-0.5)*6;
                    character.targetY = target.y + (Math.random()-0.5)*6;
                    character.actionTime = 80;
                    character._targetTreeId = target._id || (target._id = 'tree_'+Math.random().toString(36).slice(2));
                    character.thoughts = ['Holz sammeln...'];
                    console.log('➡️', character.name, 'geht zu Baum', character._targetTreeId, 'at', {x:target.x,y:target.y});
                } else {
                    character.actionTime = 60;
                    character.thoughts = ['Kein Baum gefunden'];
                }
                break; }
            case 'deliver_wood': {
                const site = this.structures.find(s=> s.type==='house' && !s.completed && s.owner===character.name);
                if (site) {
                    character.targetX = site.x + site.width/2 + (Math.random()-0.5)*10;
                    character.targetY = site.y + site.height + 12;
                    character.actionTime = 40; // fehlte -> sonst sofort wieder Entscheidung ohne Abschluss
                    character.thoughts = ['Holz stapeln...'];
                } else {
                    character.actionTime = 40;
                    character.thoughts = ['Kein Bauplatz?'];
                }
                break; }
            case 'build_hut': {
                let hut = this.structures.find(s=> s.type==='hut' && !s.completed && s.owner===character.name);
                if (!hut) {
                    hut = { type:'hut', x: character.x-30, y: character.y-30, width:60, height:45, progress:0, requiredWood:10, stackedWood:0, completed:false, owner:character.name, stage:0 };
                    this.structures.push(hut);
                }
                character.targetX = hut.x + hut.width/2 + (Math.random()-0.5)*6;
                character.targetY = hut.y + hut.height + 6;
                // Für Test: Erlaube Teilbau schon ab 50% Holz und beschleunige Zeit
                if (hut.stackedWood < hut.requiredWood*0.5) {
                    character.actionTime = 28;
                    character.thoughts = ['Hüttenholz sammeln ('+hut.stackedWood+'/'+hut.requiredWood+')'];
                } else if (hut.stackedWood < hut.requiredWood) {
                    character.actionTime = 28;
                    hut.progress = 0.5 + (hut.stackedWood/hut.requiredWood -0.5)*0.3; // leichte Bauanzeige
                    character.thoughts = ['Teilbau (Holz '+hut.stackedWood+'/'+hut.requiredWood+')'];
                } else {
                    character.actionTime = 40; // kurzer Bauabschluss
                    character.thoughts = ['Hütte Endphase...'];
                }
                break; }

            case 'build_warehouse': {
                let warehouse = this.structures.find(s=> s.type==='warehouse' && !s.completed);
                if (!warehouse) {
                    warehouse = {
                        type:'warehouse', x: character.x-50, y: character.y-40, 
                        width:100, height:80, progress:0, requiredWood:20, 
                        stackedWood:0, completed:false, stage:0,
                        storage: { wood: 0, food: 0 },
                        capacity: { wood: 100, food: 50 }
                    };
                    this.structures.push(warehouse);
                }
                character.targetX = warehouse.x + warehouse.width/2;
                character.targetY = warehouse.y + warehouse.height + 10;
                character.actionTime = 90;
                character.thoughts = ['Baue Lager... '+warehouse.stackedWood+'/'+warehouse.requiredWood+' Holz'];
                break; }

            case 'deliver_warehouse_wood': {
                const warehouse = this.structures.find(s=> s.type==='warehouse' && !s.completed);
                if (warehouse) {
                    character.targetX = warehouse.x + warehouse.width/2;
                    character.targetY = warehouse.y + warehouse.height + 10;
                    character.actionTime = 40;
                    character.thoughts = ['Bringe Holz zum Lager...'];
                }
                break; }

            case 'store_wood': {
                const warehouse = this.structures.find(s=> s.type==='warehouse' && s.completed);
                if (warehouse) {
                    character.targetX = warehouse.x + warehouse.width/2;
                    character.targetY = warehouse.y + warehouse.height + 10;
                    character.actionTime = 30;
                    character.thoughts = ['Lagere Holz ein...'];
                }
                break; }

            case 'store_food': {
                const warehouse = this.structures.find(s=> s.type==='warehouse' && s.completed);
                if (warehouse) {
                    character.targetX = warehouse.x + warehouse.width/2;
                    character.targetY = warehouse.y + warehouse.height + 10;
                    character.actionTime = 30;
                    character.thoughts = ['Lagere Nahrung ein...'];
                }
                break; }

            case 'retrieve_wood': {
                const warehouse = this.structures.find(s=> s.type==='warehouse' && s.completed);
                if (warehouse) {
                    character.targetX = warehouse.x + warehouse.width/2;
                    character.targetY = warehouse.y + warehouse.height + 10;
                    character.actionTime = 30;
                    character.thoughts = ['Hole Holz aus dem Lager...'];
                }
                break; }

            case 'retrieve_food': {
                const warehouse = this.structures.find(s=> s.type==='warehouse' && s.completed);
                if (warehouse) {
                    character.targetX = warehouse.x + warehouse.width/2;
                    character.targetY = warehouse.y + warehouse.height + 10;
                    character.actionTime = 30;
                    character.thoughts = ['Hole Nahrung aus dem Lager...'];
                }
                break; }

            case 'deliver_hut_wood': {
                const hut = this.structures.find(s=> s.type==='hut' && !s.completed && s.owner===character.name);
                if (hut) {
                    character.targetX = hut.x + hut.width/2 + (Math.random()-0.5)*6;
                    character.targetY = hut.y + hut.height + 6;
                    character.actionTime = 35;
                    character.thoughts = ['Hüttenholz stapeln...'];
                } else {
                    character.actionTime = 25;
                }
                break; }

            case 'make_fire': {
                if (character.inventory.wood >= 3) {
                    character.actionTime = 120;
                    // Merke geplante Feuerposition (leicht vor dem Charakter)
                    character._plannedFirePos = { x: character.x + (Math.random()-0.5)*12, y: character.y + (Math.random()-0.5)*12 };
                    character.thoughts = ['Feuer vorbereiten...'];
                } else {
                    character.thoughts = ['Ich brauche mehr Holz für ein Feuer'];
                    character.actionTime = 60;
                }
                break; }
            case 'warm_fire': {
                const fire = this.findNearestActiveFire(character.x, character.y);
                if (fire) {
                    character._warmingFireId = fire.id;
                    // Bewege dich nahe an den Feuermittelpunkt
                    character.targetX = fire.x + (Math.random()-0.5)*18;
                    character.targetY = fire.y + (Math.random()-0.5)*18;
                    // Wenn Bauplatz Holz braucht -> kürzeres Aufwärmen
                    const pendingSite = this.structures.find(s=> s.type==='house' && !s.completed && s.owner===character.name && s.stackedWood < s.requiredWood);
                    character.actionTime = pendingSite ? 40 : 80; // kürzer bei Baustellenbedarf
                    character.thoughts = ['Wärme tanken...'];
                } else {
                    character.actionTime = 40;
                    character.thoughts = ['Kein aktives Feuer gefunden'];
                }
                break; }

            case 'rest':
                character.thoughts = ['Ich muss mich ausruhen... so müde...'];
                character.actionTime = 300;
                break;

            case 'seek_conversation':
                character.thoughts = ['Ich fühle mich einsam... ich suche Gesellschaft.'];
                const nearbyFriend = this.characters.find(other => {
                    if (other === character) return false;
                    const distance = Math.sqrt(
                        Math.pow(character.x - other.x, 2) + 
                        Math.pow(character.y - other.y, 2)
                    );
                    return distance < 200;
                });
                
                if (nearbyFriend) {
                    character.targetX = nearbyFriend.x + (Math.random() - 0.5) * 60;
                    character.targetY = nearbyFriend.y + (Math.random() - 0.5) * 60;
                }
                character.actionTime = 150;
                break;

            case 'talking':
                character.thoughts = ['Schön, mit jemandem zu reden!'];
                character.actionTime = 200 + Math.random() * 100;
                break;

            case 'sammeln':
                // Zu einem Baum oder Strauch gehen
                const collectibles = this.terrain.filter(t => t.type === 'tree' || t.type === 'bush');
                if (collectibles.length > 0) {
                    const target = collectibles[Math.floor(Math.random() * collectibles.length)];
                    character.targetX = target.x;
                    character.targetY = target.y;
                    character.actionTime = 100 + Math.random() * 100;
                    character.thoughts = ['Ich sammle Ressourcen...'];
                }
                break;
                
            case 'erkunden':
                character.targetX = Math.random() * this.canvas.width;
                character.targetY = Math.random() * this.canvas.height * 0.7 + this.canvas.height * 0.3;
                character.actionTime = 150 + Math.random() * 150;
                character.thoughts = ['Mal sehen, was es hier zu entdecken gibt...'];
                break;
                
            case 'bauen':
                character.targetX = 300 + Math.random() * 200;
                character.targetY = 500 + Math.random() * 100;
                character.actionTime = 200 + Math.random() * 200;
                character.thoughts = ['Zeit zum Bauen!'];
                break;
                
            case 'sozialisieren':
                // Zu einem anderen Charakter gehen
                const others = this.characters.filter(c => c !== character);
                if (others.length > 0) {
                    const target = others[Math.floor(Math.random() * others.length)];
                    character.targetX = target.x + (Math.random() - 0.5) * 50;
                    character.targetY = target.y + (Math.random() - 0.5) * 50;
                    character.actionTime = 100 + Math.random() * 100;
                    character.thoughts = ['Ich gehe zu jemandem...'];
                }
                break;
                
            case 'lernen':
                // Neue Aktion: Lernen/Denken
                character.targetX = character.x + (Math.random() - 0.5) * 30;
                character.targetY = character.y + (Math.random() - 0.5) * 30;
                character.actionTime = 150 + Math.random() * 100;
                character.thoughts = ['Ich denke nach...'];
                break;
                
            case 'spielen':
                // Neue Aktion: Spielen/Entspannen
                character.targetX = character.x + (Math.random() - 0.5) * 60;
                character.targetY = character.y + (Math.random() - 0.5) * 60;
                character.actionTime = 120 + Math.random() * 80;
                character.thoughts = ['Zeit für etwas Entspannung!'];
                break;

            case 'group_hunt':
                character.thoughts = ['Gemeinsam schaffen wir mehr Essen!'];
                // Ziel: zufälliger Busch / Baum als Sammelpunkt
                const forageTargets = this.terrain.filter(t => ['bush','tree'].includes(t.type));
                if (forageTargets.length) {
                    const t = forageTargets[Math.floor(Math.random()*forageTargets.length)];
                    character.targetX = t.x + (Math.random()-0.5)*40;
                    character.targetY = t.y + (Math.random()-0.5)*40;
                }
                character.actionTime = 220 + Math.random()*80; // längere koordinierte Aktion
                break;

            case 'essen':
                character.actionTime = 50;
                character.thoughts = ['Ich esse...'];
                break;
                
            case 'schlafen':
                character.actionTime = 200;
                character.thoughts = ['Ich schlafe...'];
                break;

            default:
                character.thoughts = [`Ich ${action}...`];
                character.actionTime = 100;
        }
    }

    async completeAction(character) {
        // Speichere Umgebungszustand vor der Aktion (für AI-Lernen)
        const environmentBefore = character.lastEnvironmentState;
        
        // Führe die Aktion aus
        const resourcesBefore = { ...this.resources };
        const hungerBefore = character.hunger;
        const energyBefore = character.energy;
        
        switch (character.currentAction) {
            case 'drink_water':
                // NORMALISIERTES TRINKSYSTEM - konsistent mit Hunger/Energie (0-100 Skala)
                const thirstBefore = character.thirst;
                let waterQuality = 1.0;
                let thirstReduction = 0;
                
                // Nutze echte Wasserquelle falls in Reichweite (bessere Qualität)
                const nearbyWater = this.terrain.find(t=>t.type==='water_source' && Math.hypot(t.x-character.x, t.y-character.y) < (t.size+18));
                if (nearbyWater && (nearbyWater.level||0) > 0.05) {
                    // Direktes Trinken aus Wasserquelle
                    const amount = Math.min(nearbyWater.level, 0.4);
                    nearbyWater.level -= amount;
                    waterQuality = 1.2; // 20% bessere Qualität von frischem Wasser
                    thirstReduction = 30 + (amount * 20); // 30-38 Durst-Reduktion
                    character.thoughts = ['Herrlich frisches Wasser direkt aus der Quelle!'];
                } else if (character.inventory.water > 0) {
                    // Trinken aus Inventar
                    character.inventory.water = Math.max(0, character.inventory.water - 1);
                    waterQuality = 1.0; // Standard Qualität
                    thirstReduction = 25 + Math.random() * 10; // 25-35 Durst-Reduktion
                    character.thoughts = ['Ahh, das war erfrischend!'];
                } else {
                    // Kein Wasser verfügbar - sollte nicht passieren
                    character.thoughts = ['Ich habe kein Wasser zum Trinken...'];
                    break;
                }
                
                // Berechne finalen Durst-Reduktion mit Qualitätsfaktor
                const finalThirstReduction = Math.floor(thirstReduction * waterQuality);
                character.thirst = Math.max(0, character.thirst - finalThirstReduction);
                
                // Intelligente Gedanken basierend auf Durst-Niveau
                if (thirstBefore > 80) {
                    character.thoughts = [`Endlich! Das habe ich wirklich gebraucht. (-${finalThirstReduction} Durst)`];
                } else if (thirstBefore > 60) {
                    character.thoughts = [`Das war erfrischend. (-${finalThirstReduction} Durst)`];
                } else {
                    character.thoughts = [`Gut hydriert zu bleiben ist wichtig. (-${finalThirstReduction} Durst)`];
                }
                
                console.log(`💧 ${character.name} drank water: thirst ${thirstBefore} -> ${character.thirst} (-${finalThirstReduction})`);
                
                // Cooldown basierend auf Durst-Niveau (weniger Durst = längeres Cooldown)
                if (!character.cooldowns) character.cooldowns = {};
                const cooldownTime = character.thirst < 20 ? 20000 : character.thirst < 40 ? 15000 : 10000;
                character.cooldowns.drink_until = Date.now() + cooldownTime;
                
                // Ziel abschließen falls Durst niedrig genug
                if (character.thirst < 50) {
                    (character.goals||[]).filter(g=>g.type==='reduce_thirst').forEach(g=> g.status='done');
                }
                break;

            case 'find_water':
                // Suche nächste Wasserquelle und merke sie
                const found = window.survivalSystem?.findNearestWaterSource(character);
                if (found) {
                    character.survivalInstincts.lastWaterSource = { x:found.x, y:found.y, time:Date.now() };
                    if (found.kind === 'water_source') character.inventory.water += 1; // etwas abgefüllt
                    character.thoughts = ['Ich habe eine Wasserstelle lokalisiert.'];
                } else {
                    character.thoughts = ['Kein Wasser gefunden...'];
                }
                break;

            case 'gather_food':
                // HARTE SPERRE: Kein Sammeln bei 60+ Food
                if (character.inventory.food >= 60) {
                    character.thoughts = ['Inventar voll! Kann keine Nahrung mehr sammeln.'];
                    console.log(`🚫 ${character.name} inventory full - no food gathering`);
                    break;
                }
                
                const baseFood = 2 + Math.floor(Math.random() * 3);
                // Ertragsdämpfung wenn viel im Inventar
                const damp = character.inventory.food > 40 ? 0.5 : (character.inventory.food > 30 ? 0.7 : 1);
                const foodGathered = Math.max(1, Math.round(baseFood * damp));
                
                // Begrenzen auf Maxkapazität
                const actualGathered = Math.min(foodGathered, 60 - character.inventory.food);
                character.inventory.food += actualGathered;
                
                // VERDERBSYSTEM: Zeitstempel für neue Nahrung hinzufügen
                if (!character.foodTimestamps) character.foodTimestamps = [];
                for (let i = 0; i < actualGathered; i++) {
                    character.foodTimestamps.push(Date.now());
                }
                
                character.hunger = Math.max(0, character.hunger - 5);
                character.thoughts = [`Ich habe ${actualGathered} Nahrung gesammelt (${character.inventory.food}/60).`];
                console.log(`🍎 ${character.name} gathered food: +${actualGathered} => ${character.inventory.food}/60`);
                // Baum abbauen (Treffer zählen, nach 10 Besuchen entfernen)
                if (character._targetTreeId) {
                    const tree = this.terrain.find(t=> t._id === character._targetTreeId);
                    if (tree) {
                        tree.visits = (tree.visits||0)+1;
                        // leichte zusätzliche Holzchance wenn Baum noch "reich"
                        if (tree.visits < 7 && Math.random()<0.3) {
                            character.inventory.wood += 1;
                            character.thoughts.push('(+1 Bonus-Holz)');
                        }
                        if (tree.visits >= 10) {
                            // Baum fällt -> Ersetze durch Stumpf
                            const idx = this.terrain.indexOf(tree);
                            if (idx>-1) {
                                this.terrain.splice(idx,1);
                                this.terrain.push({type:'stump', x:tree.x, y:tree.y, size: tree.size*0.4});
                                this.addStory?.(`${character.name} hat einen Baum gefällt.`);
                            }
                        }
                    }
                }
                // Reduziere Beerfeld falls in Reichweite
                const patch = this.terrain.find(t=>t.type==='berry_patch' && Math.hypot(t.x-character.x, t.y-character.y) < (t.size+14));
                if (patch && patch.food>0) {
                    const taken = Math.min(patch.food, 2+Math.floor(Math.random()*2));
                    character.inventory.food += taken;
                    patch.food -= taken;
                    character.thoughts.push(`(+${taken} Beeren)`);
                    if (patch.food<=0) this.addStory(`${character.name} hat ein Beerfeld geleert.`);
                }
                break;
            // Leichte Verderb-Mechanik: oberhalb 60 Nahrung jede Aktion 1% Chance auf Verlust 1
            if (character.inventory.food > 60 && Math.random()<0.01) {
                character.inventory.food -= 1;
                character.thoughts.push('Ein Teil der Vorräte ist verdorben');
            }

            case 'eat_food': {
                if (character.inventory.food > 0) {
                    const need = Math.min(3, Math.ceil((character.hunger)/35));
                    let portion = 4 + Math.floor(Math.random() * 4);
                    let totalReduction = 0;
                    for (let i=0;i<need;i++) {
                        if (character.inventory.food <= 0) break;
                        const hungerReduction = (portion + Math.floor(Math.random()*3));
                        character.hunger = Math.max(0, character.hunger - hungerReduction);
                        character.inventory.food -= 1;
                        
                        // VERDERBSYSTEM: Entferne Zeitstempel für konsumierte Nahrung (älteste zuerst)
                        if (character.foodTimestamps && character.foodTimestamps.length > 0) {
                            // Entferne älteste Nahrung zuerst (sortiere und entferne erstes Element)
                            character.foodTimestamps.sort((a, b) => a - b);
                            character.foodTimestamps.shift();
                        }
                        
                        totalReduction += hungerReduction;
                        if (character.hunger < 25) break;
                    }
                    character.energy = Math.min(100, character.energy + 4);
                    character.thoughts = [`Mahlzeit. (-${totalReduction} Hunger)`];
                } else {
                    character.thoughts = ['Ich habe nichts zu essen... mein Magen knurrt.'];
                }
                break; }

            case 'gather_wood':
                const woodGathered = 6 + Math.floor(Math.random() * 5); // 6-10 Holz schnellerer Fortschritt
                character.inventory.wood += woodGathered;
                character.thoughts = [`(Test) +${woodGathered} Holz gesammelt.`];
                character.energy = Math.max(0, character.energy - 2);
                let treeInfo = null;
                if (character._targetTreeId){
                    const tree = this.terrain.find(t=> t._id === character._targetTreeId);
                    if (tree){
                        tree.visits = (tree.visits||0)+1;
                        treeInfo = {id:character._targetTreeId, visits:tree.visits, x:tree.x, y:tree.y};
                        // nach 6 Besuchen fällt Baum
                        if (tree.visits>=6){
                            const idx = this.terrain.indexOf(tree);
                            if (idx>-1){
                                this.terrain.splice(idx,1);
                                this.terrain.push({type:'stump', x:tree.x, y:tree.y, size: tree.size*0.4});
                                console.log('🪓 Baum gefällt', treeInfo);
                            }
                        }
                    }
                }
                console.log(`🪵 ${character.name} gathered wood: +${woodGathered} => ${character.inventory.wood}`, treeInfo||'noTreeRef');
                break;

            case 'build_house': {
                const site = this.structures.find(s=> s.type==='house' && !s.completed && s.owner===character.name);
                if (site) {
                    // Bauen nur wenn Stapel komplett
                    if (site.stackedWood >= site.requiredWood) {
                        // TEST-SPEED: drastisch verkürzt (z.B. 4000ms total solo => 1000ms pro Phase)
                        const builders = this.characters.filter(c=> c.currentAction==='build_house' && Math.hypot(c.x-(site.x+site.width/2), c.y-(site.y+site.height/2))<140).length;
                        const baseStageTime = 4000 / 4; // 1s pro Phase solo
                        const effectiveTime = baseStageTime / Math.max(1, Math.min(4, builders));
                        // stepStartTime initialisieren
                        if (!site.stepStartTime) site.stepStartTime = Date.now();
                        const elapsed = Date.now() - site.stepStartTime;
                        if (elapsed >= effectiveTime) {
                            site.stage += 1;
                            site.stepStartTime = Date.now();
                            character.thoughts = ['Phase fertig: '+site.stage+'/4'];
                            if (site.stage >= 4) {
                                site.completed = true;
                                site.progress = 1;
                                character.thoughts = ['Mein Haus steht!'];
                                character.warmth = Math.min(100, (character.warmth||60) + 25);
                                console.log('🏠 Haus fertig', site);
                            } else {
                                site.progress = site.stage/4;
                                console.log('🏗️ Haus Fortschritt Stage', site.stage, 'Owner', character.name);
                            }
                        } else {
                            const pct = Math.min(0.999, (elapsed / effectiveTime));
                            site.progress = (site.stage + pct)/4;
                            character.thoughts = ['Bau Phase '+(site.stage+1)+' '+Math.round(pct*100)+'%'];
                            if (!site._lastLog || Date.now()-site._lastLog>3000){
                                console.log('🔨 Bau Update', {owner:character.name, stage:site.stage, pct:Math.round(pct*100)});
                                site._lastLog = Date.now();
                            }
                        }
                        character.energy = Math.max(0, character.energy - 2);
                    } else {
                        character.thoughts = ['Noch nicht genug Holz gestapelt...'];
                    }
                }
                break; }
            case 'deliver_wood': {
                const site = this.structures.find(s=> s.type==='house' && !s.completed && s.owner===character.name);
                if (site) {
                    if (character.inventory.wood > 0 && site.stackedWood < site.requiredWood) {
                        const deliver = Math.min(character.inventory.wood, site.requiredWood - site.stackedWood);
                        site.stackedWood += deliver;
                        character.inventory.wood -= deliver;
                        character.thoughts = ['Holz gestapelt ('+site.stackedWood+'/'+site.requiredWood+')'];
                        // Fortschritt visualisieren (vor Baubeginn als Pre-Progress Balken 0..25%)
                        site.progress = site.stackedWood / site.requiredWood * 0.25; // bis 25% reserviert für Materiallieferung
                        console.log('🪵 Holz geliefert', {owner:character.name, stacked:site.stackedWood});
                    } else {
                        character.thoughts = ['Kein Holz zum Stapeln...'];
                    }
                }
                break; }

            case 'make_fire':
                if (character.inventory.wood >= 3) {
                    character.inventory.wood -= 3;
                    // Erzeuge persistentes Lagerfeuer
                    const pos = character._plannedFirePos || {x:character.x,y:character.y};
                    const fire = {
                        id: 'fire_'+Date.now()+ '_' + Math.floor(Math.random()*1000),
                        x: pos.x,
                        y: pos.y,
                        radius: 170, // Wärmeradius
                        startTime: Date.now(),
                        duration: 180000, // 3 Minuten Echtzeit
                        intensity: 1,
                        fuel: 3, // verbrauchte Holzscheite (könnte später nachgelegt werden)
                        flicker: 0
                    };
                    this.fires.push(fire);
                    character.warmth = Math.min(100, character.warmth + 50);
                    character.thoughts = ['Feuer entfacht!'];
                } else {
                    character.thoughts = ['Ich brauche mehr Holz für ein Feuer.'];
                }
                break;
            case 'warm_fire': {
                // Wiederholbarer Zyklus: Wärme steigt passiv in update; hier nur prüfen und ggf. verlängern
                if ((character.warmth||0) >= 100) {
                    character.thoughts = ['Mir ist warm – weiter!'];
                    character._warmingFireId = null;
                } else {
                    character.actionTime = 70; // warm bleiben weitere kurze Aktion
                    character.thoughts = ['Noch etwas aufwärmen...'];
                }
                break; }

            case 'rest': {
                const restEnergyGain = 25 + Math.floor(Math.random() * 20);
                let houseBonus = 0;
                const ownHouse = this.structures?.find(s=> (s.type==='house'||s.type==='hut') && s.owner===character.name && s.completed);
                if (ownHouse) {
                    const dx = (ownHouse.x + ownHouse.width/2) - character.x;
                    const dy = (ownHouse.y + ownHouse.height/2) - character.y;
                    const dist = Math.hypot(dx,dy);
                    if (dist < Math.max(ownHouse.width, ownHouse.height)) {
                        houseBonus = 8;
                        character.warmth = Math.min(100, (character.warmth||60) + 6);
                    }
                }
                character.energy = Math.min(100, character.energy + restEnergyGain + houseBonus);
                character.thoughts = [`Ich fühle mich ausgeruht! (+${restEnergyGain + houseBonus} Energie)`];
                if (!character.cooldowns) character.cooldowns={};
                character.cooldowns.rest_until = Date.now()+20000;
                break; }

            case 'talking':
                character.social = Math.min(100, character.social + 15);
                character.thoughts = ['Das Gespräch hat gut getan!'];
                break;

            case 'seek_conversation':
                if (Math.random() < 0.6) {
                    character.social = Math.min(100, character.social + 8);
                    character.thoughts = ['Ich habe jemanden zum Reden gefunden!'];
                } else {
                    character.thoughts = ['Alle scheinen beschäftigt zu sein...'];
                }
                break;

            case 'build_warehouse': {
                const warehouse = this.structures.find(s=> s.type==='warehouse' && !s.completed);
                if (warehouse) {
                    if (warehouse.stackedWood >= warehouse.requiredWood) {
                        warehouse.progress = 1;
                        warehouse.completed = true;
                        warehouse.stage = 1;
                        character.thoughts = ['Lager fertig! Jetzt können wir Ressourcen lagern.'];
                        this.addStory(`📦 ${character.name} hat das Lager fertiggestellt!`);
                        console.log('📦 Lager fertig', warehouse);
                    } else {
                        warehouse.progress = warehouse.stackedWood / warehouse.requiredWood;
                        character.thoughts = ['Lager im Bau: '+warehouse.stackedWood+'/'+warehouse.requiredWood+' Holz'];
                    }
                }
                break; }

            case 'deliver_warehouse_wood': {
                const warehouse = this.structures.find(s=> s.type==='warehouse' && !s.completed);
                if (warehouse && character.inventory.wood > 0) {
                    const deliver = Math.min(character.inventory.wood, warehouse.requiredWood - warehouse.stackedWood);
                    warehouse.stackedWood += deliver;
                    character.inventory.wood -= deliver;
                    warehouse.progress = warehouse.stackedWood / warehouse.requiredWood;
                    character.thoughts = ['Lager Holz '+warehouse.stackedWood+'/'+warehouse.requiredWood];
                    console.log('🪵 Lager Holz geliefert', {stacked:warehouse.stackedWood});
                } else {
                    character.thoughts = ['Kein Holz für Lager'];
                }
                break; }

            case 'store_wood': {
                const warehouse = this.structures.find(s=> s.type==='warehouse' && s.completed);
                if (warehouse && character.inventory.wood > 0) {
                    const canStore = warehouse.capacity.wood - warehouse.storage.wood;
                    const toStore = Math.min(character.inventory.wood, canStore);
                    if (toStore > 0) {
                        warehouse.storage.wood += toStore;
                        character.inventory.wood -= toStore;
                        character.thoughts = [`Holz eingelagert: ${toStore} (Lager: ${warehouse.storage.wood}/${warehouse.capacity.wood})`];
                        console.log('📦 Holz eingelagert', {stored: toStore, total: warehouse.storage.wood});
                    } else {
                        character.thoughts = ['Lager voll! Kann kein Holz lagern.'];
                    }
                } else {
                    character.thoughts = ['Kein Holz zum Einlagern.'];
                }
                break; }

            case 'store_food': {
                const warehouse = this.structures.find(s=> s.type==='warehouse' && s.completed);
                if (warehouse && character.inventory.food > 0) {
                    const canStore = warehouse.capacity.food - warehouse.storage.food;
                    const toStore = Math.min(character.inventory.food, canStore);
                    if (toStore > 0) {
                        warehouse.storage.food += toStore;
                        character.inventory.food -= toStore;
                        character.thoughts = [`Nahrung eingelagert: ${toStore} (Lager: ${warehouse.storage.food}/${warehouse.capacity.food})`];
                        console.log('📦 Nahrung eingelagert', {stored: toStore, total: warehouse.storage.food});
                    } else {
                        character.thoughts = ['Lager voll! Kann keine Nahrung lagern.'];
                    }
                } else {
                    character.thoughts = ['Keine Nahrung zum Einlagern.'];
                }
                break; }

            case 'retrieve_wood': {
                const warehouse = this.structures.find(s=> s.type==='warehouse' && s.completed);
                if (warehouse && warehouse.storage.wood > 0) {
                    const canTake = Math.min(10, warehouse.storage.wood); // Max 10 pro Aktion
                    warehouse.storage.wood -= canTake;
                    character.inventory.wood += canTake;
                    character.thoughts = [`Holz geholt: ${canTake} (Lager: ${warehouse.storage.wood}/${warehouse.capacity.wood})`];
                    console.log('📦 Holz entnommen', {taken: canTake, remaining: warehouse.storage.wood});
                } else {
                    character.thoughts = ['Kein Holz im Lager!'];
                }
                break; }

            case 'retrieve_food': {
                const warehouse = this.structures.find(s=> s.type==='warehouse' && s.completed);
                if (warehouse && warehouse.storage.food > 0) {
                    const canTake = Math.min(5, warehouse.storage.food); // Max 5 pro Aktion
                    warehouse.storage.food -= canTake;
                    character.inventory.food += canTake;
                    character.thoughts = [`Nahrung geholt: ${canTake} (Lager: ${warehouse.storage.food}/${warehouse.capacity.food})`];
                    console.log('📦 Nahrung entnommen', {taken: canTake, remaining: warehouse.storage.food});
                } else {
                    character.thoughts = ['Keine Nahrung im Lager!'];
                }
                break; }

            case 'sammeln':
                const foodGain = 2 + Math.floor(Math.random() * 3);
                this.resources.food += foodGain;
                character.hunger = Math.max(0, character.hunger - 10);
                character.thoughts = [`Ich habe ${foodGain} Essen gefunden!`];
                break;
            case 'deliver_hut_wood': {
                const hut = this.structures.find(s=> s.type==='hut' && !s.completed && s.owner===character.name);
                if (hut) {
                    if (character.inventory.wood>0 && hut.stackedWood < hut.requiredWood) {
                        const deliver = Math.min(character.inventory.wood, hut.requiredWood - hut.stackedWood);
                        hut.stackedWood += deliver;
                        character.inventory.wood -= deliver;
                        hut.progress = (hut.stackedWood / hut.requiredWood) * 0.5;
                        character.thoughts = ['Hütte Holz '+hut.stackedWood+'/'+hut.requiredWood];
                        console.log('🪵 Hütte Holz geliefert', {owner:character.name, stacked:hut.stackedWood});
                    } else {
                        character.thoughts = ['Kein Holz für Hütte'];
                    }
                }
                break; }
            case 'build_hut': {
                const hut = this.structures.find(s=> s.type==='hut' && !s.completed && s.owner===character.name);
                if (hut) {
                    if (hut.stackedWood >= hut.requiredWood) {
                        hut.progress = 1;
                        hut.completed = true;
                        hut.stage = 1;
                        character.thoughts = ['Hütte fertig!'];
                        character.warmth = Math.min(100, character.warmth + 10);
                        console.log('🏚️ Hütte fertig', hut);
                    } else if (hut.stackedWood >= hut.requiredWood*0.5) {
                        // Teilbau: steigere Progress schnell
                        hut.progress = 0.5 + (hut.stackedWood / hut.requiredWood - 0.5)*0.5; // bis 0.75 max
                        character.thoughts = ['Hütte im Teilbau'];
                    } else {
                        character.thoughts = ['Holz sammeln...'];
                    }
                }
                break; }
                
            case 'bauen':
                const woodGain = 1 + Math.floor(Math.random() * 2);
                this.resources.wood += woodGain;
                character.thoughts = [`Das Bauen macht Fortschritte! (+${woodGain} Holz)`];
                break;
                
            case 'erkunden':
                // Chance auf Entdeckung
                if (Math.random() < 0.3) {
                    const discovery = Math.random() < 0.5 ? 'food' : 'wood';
                    this.resources[discovery] += 1;
                    character.thoughts = [`Interessante Entdeckung! (+1 ${discovery})`];
                } else {
                    character.thoughts = ['Interessante Gegend hier...'];
                }
                character.energy = Math.max(0, character.energy - 5); // Exploration kostet Energie
                break;
                
            case 'sozialisieren':
                // Soziale Interaktion verbessert Stimmung
                character.thoughts = ['Nettes Gespräch!'];
                character.energy = Math.min(100, character.energy + 5); // Sozialisation gibt Energie
                break;
                
            case 'essen':
                const hungerReduction = Math.min(30, character.hunger);
                character.hunger = Math.max(0, character.hunger - hungerReduction);
                this.resources.food = Math.max(0, this.resources.food - 1);
                character.thoughts = ['Lecker!'];
                break;
                
            case 'schlafen':
                // VERBESSERTER SCHLAFZYKLUS mit intelligenter Energie-Regeneration
                let sleepEffectiveness = 1.0;
                
                // Zeit-basierte Effektivität (Nacht = besser)
                const isNightTime = this.isNight || (this.gameTime / 60) >= 22 || (this.gameTime / 60) < 6;
                if (isNightTime) {
                    sleepEffectiveness += 0.4; // 40% bonus für Nachtschlaf
                } else {
                    sleepEffectiveness -= 0.3; // 30% penalty für Tagschlaf
                }
                
                // Müdigkeits-basierte Effektivität (müder = besser schlafen)
                const tirednessLevel = (100 - character.energy) / 100;
                sleepEffectiveness += tirednessLevel * 0.5; // bis zu 50% bonus bei extremer Müdigkeit
                
                // Haus-Bonus für besseren Schlaf
                const nearHouse = this.structures.find(s => 
                    (s.type === 'house' || s.type === 'hut') && s.completed && 
                    Math.sqrt(Math.pow(s.x - character.x, 2) + Math.pow(s.y - character.y, 2)) < 60
                );
                if (nearHouse) {
                    sleepEffectiveness += 0.3; // 30% bonus für Schlafen im Haus
                }
                
                // Berechne finalen Energie-Gewinn
                const baseEnergyGain = Math.min(60, 100 - character.energy); // Erhöht auf 60
                const finalEnergyGain = Math.floor(baseEnergyGain * sleepEffectiveness);
                const actualEnergyGain = Math.min(finalEnergyGain, 100 - character.energy);
                
                character.energy = Math.min(100, character.energy + actualEnergyGain);
                
                // Intelligente Gedanken basierend auf Schlafqualität
                let sleepQuality = '';
                if (sleepEffectiveness >= 1.5) {
                    sleepQuality = 'Ich habe herrlich geschlafen!';
                } else if (sleepEffectiveness >= 1.2) {
                    sleepQuality = 'Ein erholsamer Schlaf.';
                } else if (sleepEffectiveness >= 0.9) {
                    sleepQuality = 'Ich bin etwas ausgeruhter.';
                } else {
                    sleepQuality = 'Kein sehr erholsamer Schlaf...';
                }
                
                character.thoughts = [`${sleepQuality} (+${actualEnergyGain} Energie)`];
                
                // Bonus: Reduziere Hunger langsamer während des Schlafens
                if (isNightTime && tirednessLevel > 0.4) {
                    character.hunger = Math.max(0, character.hunger - 1); // Kompensiere etwas Hunger-Verlust
                }
                break;
                
            case 'lernen':
                // Lernen verbessert die AI
                character.thoughts = ['Ich denke nach und lerne...'];
                character.energy = Math.max(0, character.energy - 3);
                if (character.aiBrain) {
                    character.aiBrain.learningStats.knowledgePoints += 1;
                }
                break;
                
            case 'spielen':
                // Spielen verbessert Stimmung und reduziert Stress
                character.thoughts = ['Das war entspannend!'];
                character.energy = Math.min(100, character.energy + 8);
                break;

            case 'group_hunt':
                // Gruppenjagd liefert mehr Nahrung pro Teilnehmer
                const baseGain = 3 + Math.floor(Math.random()*3); // 3-5
                const bonus = Math.random()<0.3 ? 2 : 0; // gelegentlicher Bonus
                character.inventory.food += baseGain + bonus;
                character.hunger = Math.max(0, character.hunger - 10);
                character.thoughts = [`Gemeinsam Erfolg! (+${baseGain+bonus} Nahrung)`];
                // Erhöhe Einfluss leicht für kooperative Aktionen
                if (this.socialSystem?.influence[character.name] != null) {
                    this.socialSystem.influence[character.name] += 0.02;
                }
                break;
        }

        character.currentAction = 'idle';
        
        // AI Lernen - vergleiche Umgebung vor und nach der Aktion
        if (character.aiBrain && character.learningEnabled && environmentBefore) {
            try {
                const gameState = {
                    gameTime: this.gameTime,
                    day: this.day,
                    characters: this.characters,
                    terrain: this.terrain,
                    resources: this.resources,
                    ambientLight: this.ambientLight
                };
                
                const environmentAfter = character.aiBrain.perceiveEnvironment(gameState, character);
                
                // Lasse die AI aus dem Aktionsergebnis lernen
                await character.aiBrain.learnFromActionResult(
                    character.currentAction,
                    environmentBefore,
                    environmentAfter,
                    character
                );
                
            } catch (error) {
                console.error(`AI learning error for ${character.name}:`, error);
            }
        }
        
        this.updateCharacterDisplay();
    }

    updateCharacterDisplay() {
        const characterList = document.getElementById('characterList');
        characterList.innerHTML = '';

        this.characters.forEach(character => {
            const panel = document.createElement('div');
            panel.className = 'character-panel';
            panel.style.borderLeftColor = character.color;

            // Zusatz: Führer- oder Stammsymbol
            let badges = '';
            if (this.socialSystem?.currentLeader === character.name) {
                badges += ' 👑';
            }
            const tribe = this.socialSystem?.tribes.find(t => t.members.includes(character.name));
            if (tribe) {
                badges += ' 🛖';
            }

            // Bedürfnisse mit Farben basierend auf Dringlichkeit
            const getStatusColor = (value, invert = false) => {
                const level = invert ? 100 - value : value;
                if (level > 70) return '#ff4444'; // Kritisch
                if (level > 50) return '#ffaa44'; // Warnung
                return '#44ff44'; // Okay
            };

            const hungerLevel = Math.round(character.hunger || 0);
            const thirstLevel = Math.round(character.thirst || 0);
            const energyLevel = Math.round(character.energy || 0);
            const warmthLevel = Math.round(character.warmth || 0);
            const socialLevel = Math.round(character.social || 0);

            panel.innerHTML = `
                <div class="character-name">${character.name}${badges}</div>
                <div class="character-status">${this.getActionEmoji(character.currentAction)} ${character.currentAction}</div>
                <div style="font-size:10px; margin-top:2px;">Rolle: <strong>${character.role||'-'}</strong></div>
                
                <!-- Überlebensbedürfnisse -->
                <div style="margin-top: 8px; font-size: 10px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                        <span>🍽️ Hunger:</span>
                        <span style="color: ${getStatusColor(hungerLevel)}">${hungerLevel}%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                        <span>💧 Durst:</span>
                        <span style="color: ${getStatusColor(thirstLevel)}">${thirstLevel}%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                        <span>⚡ Energie:</span>
                        <span style="color: ${getStatusColor(energyLevel, true)}">${energyLevel}%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                        <span>🔥 Wärme:</span>
                        <span style="color: ${getStatusColor(warmthLevel, true)}">${warmthLevel}%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>👥 Sozial:</span>
                        <span style="color: ${getStatusColor(socialLevel, true)}">${socialLevel}%</span>
                    </div>
                </div>

                <!-- Inventar -->
                <div style="margin-top: 5px; font-size: 9px; background: rgba(0,0,0,0.1); padding: 3px; border-radius: 3px;">
                    <div style="font-weight: bold; margin-bottom: 2px;">📦 Inventar:</div>
                    <div>🍎 ${character.inventory?.food || 0} 💧 ${character.inventory?.water || 0} 🪵 ${character.inventory?.wood || 0}</div>
                </div>
                
                <!-- Persönlichkeit (kompakter) -->
                <div style="font-size: 9px; margin-top: 5px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2px;">
                        <div>Mut: ${Math.round(character.traits.mut * 100)}%</div>
                        <div>Neugier: ${Math.round(character.traits.neugier * 100)}%</div>
                        <div>Fleiß: ${Math.round(character.traits.fleiss * 100)}%</div>
                        <div>Sozial: ${Math.round(character.traits.sozial * 100)}%</div>
                    </div>
                </div>
                
                <!-- Reproduktions-Info -->
                <div style="font-size: 9px; color: #666; margin-top: 3px;">
                    ${character.age < 16 ? '👶' : character.gender === 'male' ? '👨' : '👩'} 
                    ${Math.floor(character.age)} Jahre
                    ${character.partner ? ` | 💕 ${character.partner}` : ''}
                    ${character.pregnant ? ` | 🤰 ${Math.floor((character.pregnancyDuration * 24 * 60 - character.pregnancyTime) / (24 * 60))}d` : ''}
                </div>

                <!-- Aktuelle Gedanken -->
                ${character.thoughts.length > 0 ? `
                    <div style="margin-top: 5px; font-size: 9px; font-style: italic; color: #888;">
                        💭 "${character.thoughts[character.thoughts.length - 1]}"
                    </div>
                ` : ''}
            `;

            panel.style.cursor='pointer';
            panel.addEventListener('click',()=> this.openCharacterChat(character));
            characterList.appendChild(panel);
        });

        // Füge (falls vorhanden) StoryLog am Ende hinzu
        if (this.socialSystem?.storyLog?.length) {
            let storyPanel = document.getElementById('storyPanel');
            if (!storyPanel) {
                storyPanel = document.createElement('div');
                storyPanel.id = 'storyPanel';
                storyPanel.className = 'character-panel';
                storyPanel.style.borderLeftColor = '#8e44ad';
                characterList.appendChild(storyPanel);
            }
            const lastStories = this.socialSystem.storyLog.slice(-5).reverse();
            storyPanel.innerHTML = `
                <div class="character-name">📖 Geschichten des Dorfes</div>
                <div style="font-size:10px; line-height:1.4; max-height:140px; overflow:auto;">
                    ${lastStories.map(s => `<div><strong>${s.time}:</strong> ${s.text}</div>`).join('')}
                </div>
            `;
        }

        // Gesprächsverlauf Panel
        if (this.conversationLog?.length) {
            let convPanel = document.getElementById('conversationPanel');
            if (!convPanel) {
                convPanel = document.createElement('div');
                convPanel.id = 'conversationPanel';
                convPanel.className = 'character-panel';
                convPanel.style.borderLeftColor = '#2c82c9';
                characterList.appendChild(convPanel);
            }
            const lastLines = this.conversationLog.slice(-8).reverse();
            convPanel.innerHTML = `
                <div class="character-name">💬 Letzte Gespräche</div>
                <div style="font-size:10px; line-height:1.4; max-height:140px; overflow:auto;">
                    ${lastLines.map(l => `<div><strong>${l.speaker.split(' ')[0]}</strong>→${l.partner.split(' ')[0]} <em>(${l.topic})</em>: ${l.text}</div>`).join('')}
                </div>
            `;
        }
    }

    // ===== Spieler-Charakter Chat System =====
    openCharacterChat(char){
        this._chatTarget = char;
        if (!char._chatLog) char._chatLog = [];
        const box = document.getElementById('charChat');
        const title = document.getElementById('charChatTitle');
        const msgs = document.getElementById('charChatMessages');
        const prompts = document.getElementById('suggestedPrompts');
        if (!box||!title||!msgs) return;
        title.textContent = 'Gespräch mit '+ char.name.split(' ')[0];
        box.classList.add('active');
        msgs.innerHTML = char._chatLog.map(m=> this.renderChatMessage(char,m)).join('');
        msgs.scrollTop = msgs.scrollHeight;
        this.updateSuggestedPrompts(char, prompts);
    }

    renderChatMessage(char, m){
        if (m.from==='meta') return `<div class="meta">${m.text}</div>`;
        const speaker = m.from==='you' ? 'Du' : '⦿ '+ char.name.split(' ')[0];
        return `<div class="msg ${m.from}"><strong>${speaker}:</strong> ${m.text}</div>`;
    }

    updateSuggestedPrompts(char, container){
        if (!container) return;
        const topics = [];
        // Dynamische Themen basierend auf Zuständen
        if (char.hunger>60) topics.push('Brauchst du Essen?');
        if (char.thirst>60) topics.push('Hast du Durst?');
        if (char.energy<40) topics.push('Bist du müde?');
        if (char.warmth<40) topics.push('Dir scheint kalt zu sein?');
        if (!this.structures.some(s=>s.type==='house'&&s.owner===char.name&&s.completed)) topics.push('Wie läuft dein Hausbau?');
        topics.push('Was machst du gerade?');
        topics.push('Erinnerst du dich an etwas?');
        const uniq = [...new Set(topics)].slice(0,6);
        container.innerHTML = uniq.map(t=>`<button data-prompt="${t}">${t}</button>`).join('');
        container.querySelectorAll('button').forEach(btn=>{
            btn.addEventListener('click',()=>{
                const input = document.getElementById('charChatInput');
                input.value = btn.dataset.prompt;
                input.focus();
            });
        });
    }

    initPlayerChatSystem(){
        const sendBtn = document.getElementById('charChatSend');
        const closeBtn = document.getElementById('charChatClose');
        const input = document.getElementById('charChatInput');
        const msgs = document.getElementById('charChatMessages');
        if (!sendBtn||!closeBtn||!input||!msgs) return;
        const send = () => {
            if (!this._chatTarget) return; const text = input.value.trim(); if (!text) return; input.value='';
            const char = this._chatTarget;
            char._chatLog.push({from:'you', text});
            // Meta: Emotionale Reaktion (einfacher Score)
            const affect = this.estimatePlayerUtteranceAffect(text);
            if (affect) char._chatLog.push({from:'meta', text: affect});
            // Antwort später
            msgs.innerHTML = char._chatLog.map(m=> this.renderChatMessage(char,m)).join('');
            msgs.scrollTop = msgs.scrollHeight;
            setTimeout(()=>{
                if (!this._chatTarget || this._chatTarget!==char) return;
                const replyObj = this.generateSmarterReply(char, text);
                char._chatLog.push({from:'char', text: replyObj.text});
                if (replyObj.meta) char._chatLog.push({from:'meta', text: replyObj.meta});
                msgs.innerHTML = char._chatLog.slice(-100).map(m=> this.renderChatMessage(char,m)).join('');
                msgs.scrollTop = msgs.scrollHeight;
                this.updateSuggestedPrompts(char, document.getElementById('suggestedPrompts'));
            }, 400 + Math.random()*600);
        };
        sendBtn.addEventListener('click', send);
        input.addEventListener('keydown', e=>{ if (e.key==='Enter'){ e.preventDefault(); send(); }});
        closeBtn.addEventListener('click', ()=>{ document.getElementById('charChat').classList.remove('active'); this._chatTarget=null; });
    }

    estimatePlayerUtteranceAffect(text){
        const t = text.toLowerCase();
        if (/(danke|gut|super|schön|cool)/.test(t)) return 'Stimmung +';
        if (/(blöd|schlecht|dumm|kalt|hungrig)/.test(t)) return 'Stimmung −';
        return '';
    }

    generateSmarterReply(char, playerText){
        const t = playerText.toLowerCase();
        // Einfache Intentionserkennung
        const intents = {
            greeting: /(hallo|hi|hey|guten\s*tag)/,
            status: /(wie geht|alles gut|was machst du|was tust du|status)/,
            hunger: /(hungrig|hunger|essen|nahrung)/,
            thirst: /(durst|trinken|wasser)/,
            energy: /(müde|erschöpft|schlafen|energie)/,
            warmth: /(kalt|frieren|wärme|feuer)/,
            house: /(haus|bauen|hütte)/,
            memory: /(erinnerst|weißt du noch|erinnerung)/,
            thanks: /(danke|thx|merci)/,
            bye: /(tschüss|ciao|auf wieder|bye)/
        };
        let matched = Object.entries(intents).find(([k,rgx])=> rgx.test(t))?.[0] || 'other';
        // Kontext aus Charakterzustand
        const statusBits = [];
        if (char.hunger>65) statusBits.push('etwas hungrig');
        if (char.thirst>65) statusBits.push('durstig');
        if (char.energy<35) statusBits.push('müde');
        if (char.warmth<35) statusBits.push('kalt');
        // Letzte Erinnerung ggf.
        let lastMemory = null;
        if (char.memories && char.memories.length){
            const convMems = char.memories.filter(m=>m.type==='conversation');
            if (convMems.length) lastMemory = convMems[convMems.length-1];
        }
        const traitTone = this.getTraitTone(char);
        let text;
        switch(matched){
            case 'greeting': text = this.buildGreeting(char, traitTone); break;
            case 'status': text = statusBits.length? `Ich bin gerade ${statusBits.join(', ')}.` : 'Alles im Rahmen.'; break;
            case 'hunger': text = char.hunger>55? 'Ja, mein Magen meldet sich.' : 'Noch geht es mit dem Hunger.'; break;
            case 'thirst': text = char.thirst>55? 'Ich sollte bald etwas trinken.' : 'Ich habe genug Wasser.'; break;
            case 'energy': text = char.energy<40? 'Ich könnte eine Pause brauchen.' : 'Ich fühle mich fit genug.'; break;
            case 'warmth': text = char.warmth<40? 'Mir ist kühl, Feuer hilft.' : 'Mir ist warm genug.'; break;
            case 'house': {
                const myHouse = this.structures.find(s=>s.type==='house' && s.owner===char.name);
                if (!myHouse) text = 'Ich plane noch wo ich baue.'; else if (!myHouse.completed) text = 'Das Haus wächst Schritt für Schritt.'; else text = 'Mein Haus steht.'; break; }
            case 'memory': text = lastMemory? `Ich erinnere mich an: ${lastMemory.summary}` : 'Gerade fällt mir nichts Besonderes ein.'; break;
            case 'thanks': text = 'Gern.'; break;
            case 'bye': text = 'Bis später.'; break;
            default: text = this.genericAdaptiveReply(char, t, statusBits, traitTone);
        }
        // Optionale Meta-Ausgabe
        let meta = '';
        if (matched==='status' && statusBits.length) meta = 'Status: '+ statusBits.join(', ');
        // Follow-up Frage mit Wahrscheinlichkeit
        if (Math.random()<0.35) {
            const follow = this.followUpQuestion(char, matched, statusBits);
            if (follow) text += ' '+follow;
        }
        if (char.affect && char.affect.mood < -0.3) text = '(etwas genervt) '+text;
        if (char.affect && char.affect.mood > 0.45) text = '(gut gelaunt) '+text;
        return { text, meta };
    }

    getTraitTone(char){
        const parts=[];
        if (char.traits.neugier>0.6) parts.push('Neugierig');
        if (char.traits.fleiss>0.6) parts.push('Fleißig');
        if (char.traits.mut>0.6) parts.push('Mutig');
        if (!parts.length) return '';
        return parts[0]+':';
    }

    genericAdaptiveReply(char, lower, statusBits, tone){
        if (/(hilfe|help)/.test(lower)) return 'Wobei brauchst du Hilfe?';
        if (/(plan|ziel|was jetzt)/.test(lower)) return 'Ich versuche Ressourcen zu sammeln.';
        if (/(danke|nice)/.test(lower)) return 'Schon okay.';
        if (statusBits.length) return 'Trotzdem mache ich weiter.';
        return tone? tone+' Verstanden.' : 'Verstanden.';
    }

    buildGreeting(char, tone){
        const base = ['Hallo','Hey','Hi','Guten Tag'];
        const pick = base[Math.floor(Math.random()*base.length)];
        let ext='';
        if (char.affect?.mood>0.4) ext='!'; else if (char.affect?.mood<-0.3) ext='...';
        return (tone? tone+' ':'') + pick + ext;
    }

    followUpQuestion(char, intent, statusBits){
        if (intent==='greeting') return 'Wie geht es dir?';
        if (intent==='status') return 'Was ist dein Plan?';
        if (intent==='hunger') return 'Hast du Essen genug?';
        if (intent==='house') return 'Hilfst du beim Bauen?';
        if (intent==='memory' && Math.random()<0.5) return 'Erinnerst du dich an etwas Anderes?';
        if (statusBits.includes('kalt')) return 'Hast du ein Feuer in der Nähe?';
        return '';
    }

    tickPlayerInitiatedChat(){
        if (!this._lastPlayerPing) this._lastPlayerPing=Date.now();
        if (Date.now()-this._lastPlayerPing < 12000) return;
        this._lastPlayerPing = Date.now();
        const candidates = this.characters.filter(c=> Math.random()<0.25);
        if (!candidates.length) return;
        const char = candidates[Math.floor(Math.random()*candidates.length)];
        if (!char._chatLog) char._chatLog=[];
        char._chatLog.push({from:'char', text:this.buildGreeting(char,this.getTraitTone(char))});
        if (this._chatTarget === char) {
            const msgs=document.getElementById('charChatMessages');
            if (msgs) { msgs.innerHTML = char._chatLog.map(m=> this.renderChatMessage(char,m)).join(''); msgs.scrollTop=msgs.scrollHeight; }
        }
    }

    updateGameTime() {
        if (!this._cycleStart) this._cycleStart = Date.now();
        const now = Date.now();
        const CYCLE_MS = 1200_000; // 20 Minuten für 24h
        const elapsed = now - this._cycleStart;
        const frac = (elapsed % CYCLE_MS)/CYCLE_MS; // 0..1
        const offsetMinutes = 60; // Start 01:00
        const virtualMinutes = (frac*1440 + offsetMinutes) % 1440;
        this.gameTime = virtualMinutes;
        this.day = Math.floor(elapsed / CYCLE_MS) + 1;
        
        // JAHRESZEITEN-SYSTEM (20 Tage = 1 Jahr, 5 Tage pro Jahreszeit)
        const yearProgress = (this.day - 1) % 20;
        if (yearProgress < 5) this.season = 'spring';
        else if (yearProgress < 10) this.season = 'summer';
        else if (yearProgress < 15) this.season = 'autumn';
        else this.season = 'winter';
        
        // WETTER-SYSTEM
        this.updateWeatherSystem();
        
        const hours = Math.floor(virtualMinutes/60);
        const minutes = Math.floor(virtualMinutes%60);
        const seasonEmoji = {'spring': '🌸', 'summer': '☀️', 'autumn': '🍂', 'winter': '❄️'};
        const weatherEmoji = this.weather ? ` ${this.weather.emoji}` : '';
        const timeString = `${seasonEmoji[this.season]}${weatherEmoji} Tag ${this.day}, ${hours.toString().padStart(2,'0')}:${minutes.toString().padStart(2,'0')}`;
        
        // Ambient-Licht mit Jahreszeit und Wetter
        const t = hours + minutes/60;
        const nightMin=0.18, dayMax=1.0;
        let base = 0.5*(1+Math.cos(Math.PI*((t-13)/12)));
        if (t>=22 || t<5.5) base *=0.4;
        
        // Jahreszeiten-Licht-Modifikation
        const seasonLightMod = {'spring': 1.0, 'summer': 1.1, 'autumn': 0.9, 'winter': 0.7};
        base *= seasonLightMod[this.season];
        
        // Wetter-Licht-Modifikation
        if (this.weather) {
            base *= this.weather.lightModifier;
        }
        
        this.ambientLight = Math.max(0.1, Math.min(1.0, nightMin + (dayMax-nightMin)*base));
        this.isNight = (t>=22 || t<6);
        const timeEl=document.getElementById('gameTime'); if (timeEl) timeEl.textContent=timeString;
        const foodEl=document.getElementById('food'); if (foodEl) foodEl.textContent=this.resources.food;
        const woodEl=document.getElementById('wood'); if (woodEl) woodEl.textContent=this.resources.wood;
        const charEl=document.getElementById('charCount'); if (charEl) charEl.textContent=this.characters.length;
        const housesBuiltEl = document.getElementById('housesBuilt');
        const housesProgressEl = document.getElementById('housesProgress');
        if (housesBuiltEl && housesProgressEl) {
            const built = this.structures.filter(s=>s.type==='house' && s.completed).length;
            const building = this.structures.filter(s=>s.type==='house' && !s.completed).length;
            housesBuiltEl.textContent = built;
            housesProgressEl.textContent = building;
        }
        const animalEl = document.getElementById('animalCount'); if (animalEl) animalEl.textContent = this.animals?.length || 0;
    }

    debugScanWoodGathering(){
        const trees = this.terrain.filter(t=>t.type==='tree');
        const treeCount = trees.length;
        const chars = this.characters.map(c=>{
            const dist = trees.length? Math.min(...trees.map(t=> Math.hypot(c.x-t.x, c.y-t.y))) : null;
            return {
                name:c.name,
                action:c.currentAction,
                wood:c.inventory.wood,
                targetTree:c._targetTreeId||null,
                nearestTreeDist: dist? dist.toFixed(1): 'n/a'
            };
        });
        console.log('🔍 Holz-Scan', {treeCount, chars});
        return {treeCount, chars};
    }

    // REPRODUKTIONS-SYSTEM
    updateReproductionSystem() {
        // Update relationships
        this.updateRelationships();
        
        // Update pregnancies
        this.updatePregnancies();
        
        // Process mating attempts
        this.processMating();
        
        // Age characters
        this.ageCharacters();
    }
    
    // REALISTISCHES GESELLSCHAFTSSYSTEM - "ULTRATHINK"
    updateSocietyDynamics() {
        const population = this.characters.length;
        
        // Initialisiere Gesellschaftssystem wenn nicht vorhanden
        if (!this.society) {
            this.society = {
                factions: [],
                conflicts: [],
                tensions: new Map(),
                warState: false,
                dominantFaction: null,
                socialOrder: 'peaceful', // peaceful, tensions, conflicts, war, post_war
                lastConflictTime: 0,
                eliminationCount: 0,
                socialPressure: 0,
                resourceCompetition: 0
            };
        }
        
        // FRAKTIONSBILDUNG ab 20 Bevölkerung
        if (population >= 20 && this.society.factions.length === 0) {
            this.emergeFactions();
            console.log('🏛️ GESELLSCHAFTSWANDEL: Fraktionen entstehen bei 20+ Bevölkerung!');
        }
        
        // Gesellschaftsdynamik nur mit Fraktionen
        if (this.society.factions.length > 0) {
            this.updateFactionDynamics();
            this.updateSocialTensions();
            this.processConflictEscalation();
            this.updateSocialOrder();
        }
        
        // Bevölkerungsstatistiken
        this.updatePopulationStats();
    }
    
    emergeFactions() {
        console.log('🏛️ FRAKTIONSBILDUNG beginnt - Gesellschaft spaltet sich auf!');
        
        // Basis für Fraktionsbildung: Persönlichkeit + Geographie + Alter
        const characters = [...this.characters];
        
        // Mögliche Fraktionstypen mit realistischen Konflikten
        const factionTypes = [
            { 
                name: 'Die Traditionalisten', 
                ideology: 'tradition',
                color: '#8B4513',
                values: ['fleiss', 'sozial'], 
                enemyOf: ['progressives'],
                description: 'Bewahren alte Wege und Traditionen'
            },
            { 
                name: 'Die Progressiven', 
                ideology: 'progress',
                color: '#4169E1',
                values: ['neugier', 'mut'], 
                enemyOf: ['traditionalists'],
                description: 'Streben nach Wandel und Innovation'
            },
            { 
                name: 'Die Sammler-Elite', 
                ideology: 'resource_control',
                color: '#FFD700',
                values: ['fleiss'], 
                enemyOf: ['populists'],
                description: 'Kontrollieren Ressourcen und Handel'
            },
            { 
                name: 'Das Volk', 
                ideology: 'equality',
                color: '#DC143C',
                values: ['sozial', 'mut'], 
                enemyOf: ['elitists'],
                description: 'Kämpfen für Gleichberechtigung'
            },
            { 
                name: 'Die Isolationisten', 
                ideology: 'isolation',
                color: '#2F4F4F',
                values: ['mut'], 
                enemyOf: ['collectivists'],
                description: 'Wollen Unabhängigkeit und Selbstbestimmung'
            }
        ];
        
        // 2-4 Fraktionen entstehen zufällig
        const numFactions = 2 + Math.floor(Math.random() * 3);
        const selectedFactionTypes = this.shuffleArray([...factionTypes]).slice(0, numFactions);
        
        selectedFactionTypes.forEach((factionType, index) => {
            const faction = {
                id: `faction_${index}`,
                name: factionType.name,
                ideology: factionType.ideology,
                color: factionType.color,
                description: factionType.description,
                members: [],
                leader: null,
                resources: { food: 0, wood: 0, influence: 50 },
                militaryStrength: 0,
                territory: null,
                hostilities: new Map(), // faction_id -> hostility level (0-100)
                allies: [],
                warDeclarations: [],
                eliminated: false,
                foundedTime: Date.now()
            };
            
            this.society.factions.push(faction);
        });
        
        // Charaktere den Fraktionen zuweisen
        this.assignCharactersToFactions(characters);
        
        // Anführer wählen
        this.selectFactionLeaders();
        
        // Territorien zuweisen
        this.assignTerritories();
        
        // Initiale Spannungen zwischen natürlichen Feinden
        this.initializeFactionHostilities();
    }
    
    assignCharactersToFactions(characters) {
        // Charaktere nach Persönlichkeit und Geographie zuteilen
        const unassigned = [...characters];
        
        this.society.factions.forEach(faction => {
            const idealMemberCount = Math.floor(characters.length / this.society.factions.length);
            
            // Finde Charaktere die zur Fraktionsideologie passen
            const candidates = unassigned.filter(char => {
                if (faction.ideology === 'tradition') {
                    return char.traits.fleiss > 0.6 && char.age > 25;
                } else if (faction.ideology === 'progress') {
                    return char.traits.neugier > 0.6;
                } else if (faction.ideology === 'resource_control') {
                    return char.inventory.food > 20 || char.inventory.wood > 15;
                } else if (faction.ideology === 'equality') {
                    return char.traits.sozial > 0.6;
                } else if (faction.ideology === 'isolation') {
                    return char.traits.mut > 0.6 && char.traits.sozial < 0.4;
                }
                return true;
            });
            
            // Nimm die besten Kandidaten oder zufällige wenn nicht genug
            const membersToAdd = candidates.length >= idealMemberCount 
                ? candidates.slice(0, idealMemberCount)
                : candidates.concat(
                    this.shuffleArray(unassigned.filter(c => !candidates.includes(c)))
                        .slice(0, idealMemberCount - candidates.length)
                );
            
            membersToAdd.forEach(char => {
                faction.members.push(char.name);
                char.faction = faction.id;
                char.factionLoyalty = 60 + Math.random() * 30; // 60-90% initial loyalty
                
                // Entferne aus unassigned
                const index = unassigned.indexOf(char);
                if (index > -1) unassigned.splice(index, 1);
            });
        });
        
        // Reste zufällig verteilen
        unassigned.forEach(char => {
            const randomFaction = this.society.factions[Math.floor(Math.random() * this.society.factions.length)];
            randomFaction.members.push(char.name);
            char.faction = randomFaction.id;
            char.factionLoyalty = 30 + Math.random() * 40; // 30-70% loyalty for latecomers
        });
        
        console.log('👥 Fraktionsmitglieder zugewiesen:', this.society.factions.map(f => `${f.name}: ${f.members.length} Mitglieder`));
    }
    
    selectFactionLeaders() {
        this.society.factions.forEach(faction => {
            const members = faction.members.map(name => this.characters.find(c => c.name === name));
            
            // Wähle Anführer basierend auf Eigenschaften
            let bestCandidate = null;
            let bestScore = -1;
            
            members.forEach(member => {
                const score = 
                    (member.traits.sozial * 0.4) + 
                    (member.traits.mut * 0.3) + 
                    (member.traits.fleiss * 0.2) + 
                    (member.age > 25 ? 0.1 : 0);
                    
                if (score > bestScore) {
                    bestScore = score;
                    bestCandidate = member;
                }
            });
            
            if (bestCandidate) {
                faction.leader = bestCandidate.name;
                bestCandidate.isLeader = true;
                bestCandidate.factionLoyalty = 95; // Anführer sind sehr loyal
                console.log(`👑 ${bestCandidate.name} führt jetzt ${faction.name}`);
            }
        });
    }
    
    assignTerritories() {
        // Jede Fraktion beansprucht ein Territorium
        this.society.factions.forEach((faction, index) => {
            const centerX = (index * (this.canvas.width / this.society.factions.length)) + (this.canvas.width / (this.society.factions.length * 2));
            const centerY = this.canvas.height / 2;
            
            faction.territory = {
                centerX: centerX,
                centerY: centerY,
                radius: 150,
                controlStrength: 60 // 0-100%
            };
            
            console.log(`🏴 ${faction.name} beansprucht Territorium bei (${Math.round(centerX)}, ${Math.round(centerY)})`);
        });
    }
    
    initializeFactionHostilities() {
        // Setze initiale Feindschaften basierend auf Ideologien
        const hostilityMap = {
            'tradition': ['progress'],
            'progress': ['tradition'],
            'resource_control': ['equality'],
            'equality': ['resource_control'],
            'isolation': ['progress', 'equality']
        };
        
        this.society.factions.forEach(faction1 => {
            this.society.factions.forEach(faction2 => {
                if (faction1 === faction2) return;
                
                const isNaturalEnemy = hostilityMap[faction1.ideology]?.includes(faction2.ideology);
                const baseHostility = isNaturalEnemy ? 20 + Math.random() * 30 : Math.random() * 15;
                
                faction1.hostilities.set(faction2.id, baseHostility);
            });
        });
        
        console.log('⚔️ Initiale Fraktionsspannungen etabliert');
    }
    
    updateFactionDynamics() {
        this.society.factions.forEach(faction => {
            if (faction.eliminated) return;
            
            // Update Militärische Stärke
            faction.militaryStrength = faction.members.length * 10 + 
                (faction.resources.wood * 0.5) + 
                (faction.leader ? 20 : 0);
            
            // Update Ressourcen durch Mitglieder
            let totalFood = 0, totalWood = 0;
            faction.members.forEach(memberName => {
                const member = this.characters.find(c => c.name === memberName);
                if (member) {
                    totalFood += member.inventory.food * 0.1; // 10% wird geteilt
                    totalWood += member.inventory.wood * 0.1;
                }
            });
            faction.resources.food += totalFood;
            faction.resources.wood += totalWood;
            
            // Territorialkontrolle
            this.updateTerritorialControl(faction);
        });
    }
    
    updateTerritorialControl(faction) {
        let controlStrength = 0;
        const territory = faction.territory;
        
        faction.members.forEach(memberName => {
            const member = this.characters.find(c => c.name === memberName);
            if (member) {
                const distance = Math.hypot(member.x - territory.centerX, member.y - territory.centerY);
                if (distance < territory.radius) {
                    controlStrength += 10; // Jedes Mitglied im Territorium +10 Kontrolle
                }
            }
        });
        
        territory.controlStrength = Math.min(100, controlStrength);
    }
    
    updateSocialTensions() {
        const now = Date.now();
        
        this.society.factions.forEach(faction1 => {
            if (faction1.eliminated) return;
            
            this.society.factions.forEach(faction2 => {
                if (faction1 === faction2 || faction2.eliminated) return;
                
                let tensionIncrease = 0;
                
                // RESSOURCENKONKURRENZ
                const resourceDiff = (faction1.resources.food + faction1.resources.wood) - 
                                   (faction2.resources.food + faction2.resources.wood);
                if (Math.abs(resourceDiff) > 50) {
                    tensionIncrease += 2; // Reiche vs Arme Spannungen
                }
                
                // TERRITORIALE KONFLIKTE
                const distance = Math.hypot(
                    faction1.territory.centerX - faction2.territory.centerX,
                    faction1.territory.centerY - faction2.territory.centerY
                );
                if (distance < faction1.territory.radius + faction2.territory.radius) {
                    tensionIncrease += 3; // Überlappende Territorien
                }
                
                // IDEOLOGISCHE UNTERSCHIEDE (bereits in initializeFactionHostilities)
                const currentHostility = faction1.hostilities.get(faction2.id) || 0;
                const newHostility = Math.min(100, currentHostility + tensionIncrease);
                faction1.hostilities.set(faction2.id, newHostility);
                
                // KRITISCHE SCHWELLE
                if (newHostility > 70 && Math.random() < 0.1) {
                    this.triggerConflictEvent(faction1, faction2);
                }
            });
        });
    }
    
    triggerConflictEvent(faction1, faction2) {
        const now = Date.now();
        const hostility = faction1.hostilities.get(faction2.id);
        
        const conflictTypes = [
            { type: 'verbal_dispute', threshold: 30, damage: 0 },
            { type: 'resource_theft', threshold: 50, damage: 5 },
            { type: 'border_skirmish', threshold: 70, damage: 15 },
            { type: 'assassination_attempt', threshold: 85, damage: 25 },
            { type: 'open_warfare', threshold: 95, damage: 40 }
        ];
        
        const availableConflicts = conflictTypes.filter(c => hostility >= c.threshold);
        if (availableConflicts.length === 0) return;
        
        const conflict = availableConflicts[availableConflicts.length - 1]; // Höchste verfügbare Eskalation
        
        const conflictEvent = {
            id: `conflict_${now}`,
            type: conflict.type,
            factions: [faction1.id, faction2.id],
            timestamp: now,
            resolved: false,
            casualties: 0,
            outcome: null
        };
        
        this.society.conflicts.push(conflictEvent);
        
        console.log(`⚔️ KONFLIKT: ${faction1.name} vs ${faction2.name} - ${conflict.type}`);
        
        // Führe Konflikt aus
        this.executeConflict(conflictEvent, conflict);
    }
    
    executeConflict(conflictEvent, conflictType) {
        const faction1 = this.society.factions.find(f => f.id === conflictEvent.factions[0]);
        const faction2 = this.society.factions.find(f => f.id === conflictEvent.factions[1]);
        
        if (!faction1 || !faction2 || faction1.eliminated || faction2.eliminated) return;
        
        switch(conflictType.type) {
            case 'verbal_dispute':
                this.executeVerbalDispute(faction1, faction2, conflictEvent);
                break;
            case 'resource_theft':
                this.executeResourceTheft(faction1, faction2, conflictEvent);
                break;
            case 'border_skirmish':
                this.executeBorderSkirmish(faction1, faction2, conflictEvent);
                break;
            case 'assassination_attempt':
                this.executeAssassinationAttempt(faction1, faction2, conflictEvent);
                break;
            case 'open_warfare':
                this.executeOpenWarfare(faction1, faction2, conflictEvent);
                break;
        }
        
        conflictEvent.resolved = true;
        this.society.lastConflictTime = Date.now();
    }
    
    executeVerbalDispute(faction1, faction2, conflictEvent) {
        // Anführer diskutieren - keine Verluste aber Spannungen
        console.log(`💬 ${faction1.name} und ${faction2.name} streiten öffentlich!`);
        
        const hostility1 = faction1.hostilities.get(faction2.id) + 5;
        const hostility2 = faction2.hostilities.get(faction1.id) + 5;
        
        faction1.hostilities.set(faction2.id, Math.min(100, hostility1));
        faction2.hostilities.set(faction1.id, Math.min(100, hostility2));
        
        conflictEvent.outcome = 'tensions_increased';
    }
    
    executeResourceTheft(faction1, faction2, conflictEvent) {
        // Fraktion 1 stiehlt Ressourcen von Fraktion 2
        const stolenFood = Math.min(20, faction2.resources.food * 0.2);
        const stolenWood = Math.min(15, faction2.resources.wood * 0.2);
        
        faction1.resources.food += stolenFood;
        faction1.resources.wood += stolenWood;
        faction2.resources.food = Math.max(0, faction2.resources.food - stolenFood);
        faction2.resources.wood = Math.max(0, faction2.resources.wood - stolenWood);
        
        console.log(`🥷 ${faction1.name} stiehlt Ressourcen von ${faction2.name}!`);
        
        // Erhöhe Feindschaft drastisch
        faction2.hostilities.set(faction1.id, Math.min(100, faction2.hostilities.get(faction1.id) + 15));
        
        conflictEvent.outcome = 'resources_stolen';
    }
    
    executeBorderSkirmish(faction1, faction2, conflictEvent) {
        // Kleiner Kampf mit möglichen Verlusten
        console.log(`⚔️ GRENZKONFLIKT: ${faction1.name} vs ${faction2.name}!`);
        
        const strength1 = faction1.militaryStrength + Math.random() * 20;
        const strength2 = faction2.militaryStrength + Math.random() * 20;
        
        let casualties = 0;
        
        if (strength1 > strength2 * 1.2) {
            // Faction1 gewinnt deutlich
            casualties = this.eliminateRandomMembers(faction2, 1);
            conflictEvent.outcome = `${faction1.name}_victory`;
            console.log(`🏆 ${faction1.name} gewinnt den Grenzkonflikt!`);
        } else if (strength2 > strength1 * 1.2) {
            // Faction2 gewinnt deutlich  
            casualties = this.eliminateRandomMembers(faction1, 1);
            conflictEvent.outcome = `${faction2.name}_victory`;
            console.log(`🏆 ${faction2.name} gewinnt den Grenzkonflikt!`);
        } else {
            // Patt - beide leiden
            casualties = this.eliminateRandomMembers(faction1, 1) + this.eliminateRandomMembers(faction2, 1);
            conflictEvent.outcome = 'mutual_losses';
            console.log(`💀 Beide Fraktionen erleiden Verluste im Grenzkonflikt!`);
        }
        
        conflictEvent.casualties = casualties;
        this.society.eliminationCount += casualties;
    }
    
    executeAssassinationAttempt(faction1, faction2, conflictEvent) {
        // Versuch den feindlichen Anführer zu eliminieren
        console.log(`🗡️ ${faction1.name} versucht ${faction2.name} Anführer zu eliminieren!`);
        
        const leader = this.characters.find(c => c.name === faction2.leader);
        const success = Math.random() < 0.3; // 30% Erfolgsrate
        
        if (success && leader) {
            console.log(`☠️ ATTENTAT ERFOLGREICH: ${leader.name} wurde eliminiert!`);
            this.eliminateCharacter(leader);
            this.selectNewLeader(faction2);
            conflictEvent.outcome = 'assassination_successful';
            conflictEvent.casualties = 1;
            this.society.eliminationCount++;
            
            // Extreme Vergeltung
            faction2.hostilities.set(faction1.id, 100);
        } else {
            console.log(`🛡️ Attentat auf ${faction2.leader} gescheitert!`);
            conflictEvent.outcome = 'assassination_failed';
            // Feindschaft steigt trotzdem
            faction2.hostilities.set(faction1.id, Math.min(100, faction2.hostilities.get(faction1.id) + 25));
        }
    }
    
    executeOpenWarfare(faction1, faction2, conflictEvent) {
        // Vollständiger Krieg zwischen Fraktionen
        console.log(`🔥 KRIEG ERKLÄRT: ${faction1.name} vs ${faction2.name}!`);
        this.society.warState = true;
        this.society.socialOrder = 'war';
        
        const strength1 = faction1.militaryStrength;
        const strength2 = faction2.militaryStrength;
        
        console.log(`⚔️ Militärstärken: ${faction1.name}(${strength1}) vs ${faction2.name}(${strength2})`);
        
        let totalCasualties = 0;
        
        // Mehrere Kampfrunden
        for (let round = 0; round < 3; round++) {
            const roundStrength1 = strength1 * (0.8 + Math.random() * 0.4);
            const roundStrength2 = strength2 * (0.8 + Math.random() * 0.4);
            
            if (roundStrength1 > roundStrength2) {
                const casualties = this.eliminateRandomMembers(faction2, 1 + Math.floor(Math.random() * 2));
                totalCasualties += casualties;
                console.log(`💀 Runde ${round + 1}: ${faction2.name} verliert ${casualties} Mitglieder`);
            } else {
                const casualties = this.eliminateRandomMembers(faction1, 1 + Math.floor(Math.random() * 2));
                totalCasualties += casualties;
                console.log(`💀 Runde ${round + 1}: ${faction1.name} verliert ${casualties} Mitglieder`);
            }
            
            // Prüfe ob Fraktion eliminiert wurde
            if (faction1.members.length === 0) {
                this.eliminateFaction(faction1);
                conflictEvent.outcome = `${faction2.name}_total_victory`;
                break;
            } else if (faction2.members.length === 0) {
                this.eliminateFaction(faction2);
                conflictEvent.outcome = `${faction1.name}_total_victory`;
                break;
            }
        }
        
        conflictEvent.casualties = totalCasualties;
        this.society.eliminationCount += totalCasualties;
        
        // Prüfe Siegbedingung
        this.checkVictoryConditions();
    }
    
    eliminateRandomMembers(faction, count) {
        let eliminated = 0;
        const eligibleMembers = faction.members.filter(name => name !== faction.leader);
        
        for (let i = 0; i < count && eligibleMembers.length > 0; i++) {
            const randomIndex = Math.floor(Math.random() * eligibleMembers.length);
            const memberName = eligibleMembers[randomIndex];
            const character = this.characters.find(c => c.name === memberName);
            
            if (character) {
                this.eliminateCharacter(character);
                eliminated++;
                eligibleMembers.splice(randomIndex, 1);
            }
        }
        
        return eliminated;
    }
    
    eliminateCharacter(character) {
        console.log(`☠️ ${character.name} wurde eliminiert!`);
        
        // Entferne aus Fraktion
        const faction = this.society.factions.find(f => f.id === character.faction);
        if (faction) {
            const index = faction.members.indexOf(character.name);
            if (index > -1) faction.members.splice(index, 1);
        }
        
        // Entferne aus Charakterliste
        const charIndex = this.characters.indexOf(character);
        if (charIndex > -1) this.characters.splice(charIndex, 1);
        
        // Visuelle Todesmeldung
        this.showSpeechBubble(character, {
            text: "💀 Ich wurde eliminiert...",
            type: 'meta',
            duration: 3000
        });
    }
    
    selectNewLeader(faction) {
        if (faction.members.length === 0) return;
        
        const members = faction.members.map(name => this.characters.find(c => c.name === name));
        let bestCandidate = null;
        let bestScore = -1;
        
        members.forEach(member => {
            if (!member) return;
            const score = (member.traits.sozial * 0.4) + (member.traits.mut * 0.3) + (member.factionLoyalty / 100 * 0.3);
            if (score > bestScore) {
                bestScore = score;
                bestCandidate = member;
            }
        });
        
        if (bestCandidate) {
            faction.leader = bestCandidate.name;
            bestCandidate.isLeader = true;
            console.log(`👑 ${bestCandidate.name} ist neuer Anführer von ${faction.name}`);
        }
    }
    
    eliminateFaction(faction) {
        faction.eliminated = true;
        faction.members = [];
        faction.leader = null;
        
        console.log(`🏴 FRAKTION ELIMINIERT: ${faction.name} wurde vollständig zerstört!`);
        
        // Territorium wird frei
        faction.territory.controlStrength = 0;
    }
    
    checkVictoryConditions() {
        const activeFactions = this.society.factions.filter(f => !f.eliminated && f.members.length > 0);
        
        if (activeFactions.length === 1) {
            const winner = activeFactions[0];
            this.society.dominantFaction = winner.id;
            this.society.socialOrder = 'post_war';
            this.society.warState = false;
            
            console.log(`🏆 SIEG! ${winner.name} hat alle anderen Fraktionen besiegt!`);
            console.log(`👥 Überlebende Bevölkerung: ${this.characters.length}/${this.society.eliminationCount + this.characters.length} (${this.society.eliminationCount} eliminiert)`);
            
            // Globale Siegmeldung
            this.characters.forEach(survivor => {
                this.showSpeechBubble(survivor, {
                    text: `Wir haben gewonnen! ${winner.name} herrscht!`,
                    type: 'planning',
                    duration: 8000
                });
            });
            
            return true;
        }
        
        return false;
    }
    
    processConflictEscalation() {
        // Prüfe globale Spannungen und eskaliere
        if (this.society.factions.length < 2) return;
        
        let totalTensions = 0;
        let tensionCount = 0;
        
        this.society.factions.forEach(faction1 => {
            if (faction1.eliminated) return;
            this.society.factions.forEach(faction2 => {
                if (faction1 === faction2 || faction2.eliminated) return;
                totalTensions += faction1.hostilities.get(faction2.id) || 0;
                tensionCount++;
            });
        });
        
        const averageTension = tensionCount > 0 ? totalTensions / tensionCount : 0;
        this.society.socialPressure = averageTension;
        
        // Automatische Konflikteskalation
        if (averageTension > 80 && !this.society.warState && Math.random() < 0.2) {
            this.triggerGlobalConflict();
        }
    }
    
    triggerGlobalConflict() {
        console.log('🔥 GLOBALER KONFLIKT: Alle Fraktionen im Krieg!');
        this.society.warState = true;
        this.society.socialOrder = 'war';
        
        // Alle Fraktionen kämpfen gegeneinander
        const activeFactions = this.society.factions.filter(f => !f.eliminated);
        
        for (let i = 0; i < activeFactions.length; i++) {
            for (let j = i + 1; j < activeFactions.length; j++) {
                const faction1 = activeFactions[i];
                const faction2 = activeFactions[j];
                
                // Setze maximale Feindschaft
                faction1.hostilities.set(faction2.id, 100);
                faction2.hostilities.set(faction1.id, 100);
                
                // Triggere sofortigen Konflikt
                if (Math.random() < 0.5) {
                    this.triggerConflictEvent(faction1, faction2);
                }
            }
        }
    }
    
    updateSocialOrder() {
        const activeFactions = this.society.factions.filter(f => !f.eliminated);
        
        if (activeFactions.length <= 1) {
            this.society.socialOrder = 'post_war';
            this.society.warState = false;
        } else if (this.society.warState) {
            this.society.socialOrder = 'war';
        } else if (this.society.socialPressure > 60) {
            this.society.socialOrder = 'conflicts';
        } else if (this.society.socialPressure > 30) {
            this.society.socialOrder = 'tensions';
        } else {
            this.society.socialOrder = 'peaceful';
        }
    }
    
    updatePopulationStats() {
        if (!this.society.populationStats) {
            this.society.populationStats = {
                peak: this.characters.length,
                current: this.characters.length,
                eliminated: 0,
                factionHistory: []
            };
        }
        
        this.society.populationStats.current = this.characters.length;
        this.society.populationStats.eliminated = this.society.eliminationCount;
        
        if (this.characters.length > this.society.populationStats.peak) {
            this.society.populationStats.peak = this.characters.length;
        }
    }
    
    // Hilfsfunktion
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }
    
    updateRelationships() {
        this.characters.forEach(char1 => {
            this.characters.forEach(char2 => {
                if (char1 === char2) return;
                
                const distance = Math.hypot(char1.x - char2.x, char1.y - char2.y);
                const affection = char1.relationships.get(char2.name) || 0;
                
                // Proximity increases affection slowly
                if (distance < 80) {
                    const compatibility = this.calculateCompatibility(char1, char2);
                    const increase = compatibility * 0.1;
                    char1.relationships.set(char2.name, Math.min(100, affection + increase));
                } else {
                    // Distance decreases affection very slowly
                    char1.relationships.set(char2.name, Math.max(0, affection - 0.01));
                }
            });
        });
    }
    
    calculateCompatibility(char1, char2) {
        if (char1.gender === char2.gender) return 0; // Same sex compatibility = 0 for reproduction
        
        const traitDiff = Math.abs(char1.traits.sozial - char2.traits.sozial) +
                         Math.abs(char1.traits.neugier - char2.traits.neugier) +
                         Math.abs(char1.traits.fleiss - char2.traits.fleiss);
        
        // Lower trait differences = higher compatibility
        return Math.max(0, 1 - traitDiff / 3);
    }
    
    updatePregnancies() {
        this.characters.forEach(character => {
            if (character.pregnant) {
                character.pregnancyTime += 1/60; // 60 FPS assumed
                
                // Check if pregnancy is complete
                if (character.pregnancyTime >= character.pregnancyDuration * 24 * 60) { // days * 24 * 60 minutes
                    this.giveBirth(character);
                }
            }
        });
    }
    
    giveBirth(mother) {
        const father = this.characters.find(c => c.name === mother.partner);
        if (!father) return;
        
        // Create baby
        const babyName = this.generateBabyName();
        const baby = this.createBaby(mother, father, babyName);
        this.characters.push(baby);
        
        // Reset mother's pregnancy
        mother.pregnant = false;
        mother.pregnancyTime = 0;
        mother.lastBirth = Date.now();
        
        this.addStory(`👶 ${babyName} wurde geboren! Eltern: ${mother.name} & ${father.name}`);
        console.log(`👶 Baby born: ${babyName}`, baby);
    }
    
    createBaby(mother, father, name) {
        // Mix parent traits
        const babyTraits = {
            mut: (mother.traits.mut + father.traits.mut) / 2 + (Math.random() - 0.5) * 0.2,
            neugier: (mother.traits.neugier + father.traits.neugier) / 2 + (Math.random() - 0.5) * 0.2,
            fleiss: (mother.traits.fleiss + father.traits.fleiss) / 2 + (Math.random() - 0.5) * 0.2,
            sozial: (mother.traits.sozial + father.traits.sozial) / 2 + (Math.random() - 0.5) * 0.2
        };
        
        // Clamp traits between 0 and 1
        Object.keys(babyTraits).forEach(trait => {
            babyTraits[trait] = Math.max(0, Math.min(1, babyTraits[trait]));
        });
        
        return {
            name: name,
            color: this.mixColors(mother.color, father.color),
            traits: babyTraits,
            preferredAction: Math.random() < 0.5 ? mother.preferredAction : father.preferredAction,
            spriteIndex: Math.floor(Math.random() * 25), // Zufälliger Sprite für Baby
            x: mother.x + (Math.random() - 0.5) * 20,
            y: mother.y + (Math.random() - 0.5) * 20,
            targetX: null,
            targetY: null,
            speed: 0.3, // Babies are slower
            currentAction: "idle",
            age: 0, // Baby starts at 0
            gender: Math.random() < 0.5 ? 'male' : 'female',
            relationships: new Map(),
            partner: null,
            pregnant: false,
            pregnancyTime: 0,
            pregnancyDuration: 3,
            fertility: 0.8 + Math.random() * 0.2,
            lastBirth: 0,
            actionTime: 0,
            thoughts: ['👶 Goo goo ga ga...'],
            hunger: 30,
            energy: 80,
            social: 100,
            warmth: 80,
            inventory: { food: 0, water: 0, wood: 0, materials: 0 }
        };
    }
    
    generateBabyName() {
        const names = ['Anna', 'Ben', 'Clara', 'David', 'Eva', 'Felix', 'Greta', 'Hans', 
                      'Ida', 'Jan', 'Klara', 'Lukas', 'Mia', 'Noah', 'Olivia', 'Paul'];
        return names[Math.floor(Math.random() * names.length)] + ' Jr.';
    }
    
    mixColors(color1, color2) {
        // Simple color mixing
        const hex1 = parseInt(color1.substring(1), 16);
        const hex2 = parseInt(color2.substring(1), 16);
        
        const r1 = (hex1 >> 16) & 255;
        const g1 = (hex1 >> 8) & 255;
        const b1 = hex1 & 255;
        
        const r2 = (hex2 >> 16) & 255;
        const g2 = (hex2 >> 8) & 255;
        const b2 = hex2 & 255;
        
        const r = Math.floor((r1 + r2) / 2);
        const g = Math.floor((g1 + g2) / 2);
        const b = Math.floor((b1 + b2) / 2);
        
        return '#' + ((r << 16) + (g << 8) + b).toString(16).padStart(6, '0');
    }
    
    processMating() {
        this.characters.forEach(char1 => {
            if (char1.partner || char1.pregnant || char1.age < 16) return;
            
            // Find potential partners
            const candidates = this.characters.filter(char2 => 
                char2.gender !== char1.gender &&
                !char2.partner &&
                !char2.pregnant &&
                char2.age >= 16 &&
                char1.relationships.get(char2.name) > 60 &&
                Math.hypot(char1.x - char2.x, char1.y - char2.y) < 50
            );
            
            if (candidates.length > 0 && Math.random() < 0.001) { // Very low chance per frame
                const partner = candidates[Math.floor(Math.random() * candidates.length)];
                this.formPartnership(char1, partner);
            }
        });
    }
    
    formPartnership(char1, char2) {
        char1.partner = char2.name;
        char2.partner = char1.name;
        
        this.addStory(`💕 ${char1.name} und ${char2.name} sind jetzt Partner!`);
        
        // Chance for immediate pregnancy
        if (Math.random() < 0.7) {
            const female = char1.gender === 'female' ? char1 : char2;
            if (Math.random() < female.fertility) {
                female.pregnant = true;
                female.pregnancyTime = 0;
                this.addStory(`🤰 ${female.name} ist schwanger!`);
            }
        }
    }
    
    ageCharacters() {
        // Age characters slowly (1 year per ~10 real minutes)
        const ageIncrement = 1 / (10 * 60 * 60); // Very slow aging
        
        this.characters.forEach(character => {
            character.age += ageIncrement;
            
            // Death from old age (very rare, around 80+ years)
            if (character.age > 80 && Math.random() < 0.0001) {
                this.characterDeath(character);
            }
        });
    }
    
    characterDeath(character) {
        this.addStory(`💀 ${character.name} ist im Alter von ${Math.floor(character.age)} Jahren gestorben.`);
        this.characters = this.characters.filter(c => c !== character);
    }
    
    // WETTER-SYSTEM
    updateWeatherSystem() {
        // Initialisiere Wetter wenn nötig
        if (!this.weather) {
            this.weather = null;
            this.weatherChangeTime = 0;
        }
        
        // Wetter-Wechsel alle 2-6 Stunden
        this.weatherChangeTime += 1/60; // Minuten
        const changeInterval = 120 + Math.random() * 240; // 2-6 Stunden
        
        if (this.weatherChangeTime >= changeInterval) {
            this.changeWeather();
            this.weatherChangeTime = 0;
        }
        
        // Wetter-Effekte auf Charaktere
        this.applyWeatherEffects();
    }
    
    changeWeather() {
        const weatherTypes = {
            clear: { emoji: '☀️', lightModifier: 1.0, description: 'Klarer Himmel' },
            cloudy: { emoji: '☁️', lightModifier: 0.8, description: 'Bewölkt' },
            rain: { emoji: '🌧️', lightModifier: 0.6, description: 'Regenschauer' },
            storm: { emoji: '⛈️', lightModifier: 0.4, description: 'Gewitter' },
            snow: { emoji: '❄️', lightModifier: 0.7, description: 'Schnee' },
            fog: { emoji: '🌫️', lightModifier: 0.5, description: 'Nebel' }
        };
        
        // Saison beeinflusst Wetter-Wahrscheinlichkeiten
        let weatherPool = [];
        switch(this.season) {
            case 'spring':
                weatherPool = ['clear', 'clear', 'cloudy', 'rain', 'fog'];
                break;
            case 'summer':
                weatherPool = ['clear', 'clear', 'clear', 'cloudy', 'storm'];
                break;
            case 'autumn':
                weatherPool = ['cloudy', 'rain', 'rain', 'fog', 'clear'];
                break;
            case 'winter':
                weatherPool = ['snow', 'snow', 'cloudy', 'fog', 'clear'];
                break;
        }
        
        const newWeatherType = weatherPool[Math.floor(Math.random() * weatherPool.length)];
        this.weather = weatherTypes[newWeatherType];
        this.weather.type = newWeatherType;
        
        this.addStory(`🌤️ Wetter wechselt zu: ${this.weather.description}`);
        console.log(`🌤️ Weather changed to: ${newWeatherType}`, this.weather);
    }
    
    applyWeatherEffects() {
        if (!this.weather) return;
        
        this.characters.forEach(character => {
            switch(this.weather.type) {
                case 'rain':
                case 'storm':
                    // Regen/Sturm verringert Bewegungsgeschwindigkeit und Wärme
                    if (Math.random() < 0.02) {
                        character.warmth = Math.max(0, character.warmth - 1);
                        character.speed = Math.max(0.2, character.speed * 0.95);
                    }
                    break;
                    
                case 'snow':
                    // Schnee verringert Wärme stark
                    if (Math.random() < 0.03) {
                        character.warmth = Math.max(0, character.warmth - 2);
                        character.hunger = Math.min(100, character.hunger + 0.5);
                    }
                    break;
                    
                case 'storm':
                    // Gewitter kann Bäume umwerfen (sehr selten)
                    if (Math.random() < 0.001) {
                        const trees = this.terrain.filter(t => t.type === 'tree');
                        if (trees.length > 0) {
                            const tree = trees[Math.floor(Math.random() * trees.length)];
                            tree.type = 'fallen_tree';
                            tree.wood = (tree.wood || 0) + 5; // Mehr Holz von umgefallenen Bäumen
                            this.addStory(`⚡ Ein Baum wurde vom Sturm umgeworfen!`);
                        }
                    }
                    
                    // Gewitter können Naturkatastrophen auslösen
                    if (Math.random() < 0.0005) {
                        this.triggerNaturalDisaster('lightning');
                    }
                    break;
            }
        });
        
        // Saison-Effekte auf Ressourcen
        this.applySeasonalEffects();
        
        // Zufällige Naturkatastrophen
        this.checkForNaturalDisasters();
    }
    
    applySeasonalEffects() {
        // Saison-Effekte auf Nahrung und Wachstum
        this.terrain.forEach(item => {
            if (item.type === 'berry_patch') {
                switch(this.season) {
                    case 'summer':
                        if (Math.random() < 0.01) {
                            item.food = Math.min(20, (item.food || 0) + 1);
                        }
                        break;
                    case 'autumn':
                        if (Math.random() < 0.008) {
                            item.food = Math.min(25, (item.food || 0) + 2);
                        }
                        break;
                    case 'winter':
                        if (Math.random() < 0.005) {
                            item.food = Math.max(0, (item.food || 0) - 1);
                        }
                        break;
                }
            }
        });
    }

    // Intelligente Navigation - prüft ob Weg durch Fluss führt
    wouldCrossRiver(fromX, fromY, toX, toY) {
        const river = this.terrain.find(t => t.type === 'river');
        if (!river) return false;
        
        // Prüfe ob auf der Brücke (dann ist Fluss-Überquerung erlaubt)
        const bridge = this.terrain.find(t => t.type === 'bridge');
        if (bridge && this.isOnBridge(fromX, fromY, bridge)) {
            return false; // Auf der Brücke = kein Fluss-Problem
        }
        
        // Erweiterte Kollisionserkennung - größerer Sicherheitsabstand
        const riverWidth = river.width + 20; // Mehr Sicherheitsabstand
        
        // Prüfe jeden Punkt des Flusses
        for (let i = 0; i < river.points.length - 1; i++) {
            const p1 = river.points[i];
            const p2 = river.points[i + 1];
            
            // Prüfe ob die Bewegungslinie den Fluss kreuzt
            if (this.lineIntersectsLine(fromX, fromY, toX, toY, p1.x, p1.y, p2.x, p2.y)) {
                // Zusätzlich: Prüfe Distanz-basierten Ansatz
                const distToRiver = this.distanceToLineSegment(fromX, fromY, p1.x, p1.y, p2.x, p2.y);
                const distNextToRiver = this.distanceToLineSegment(toX, toY, p1.x, p1.y, p2.x, p2.y);
                
                if (distToRiver < riverWidth || distNextToRiver < riverWidth) {
                    return true;
                }
            }
        }
        return false;
    }
    
    // Prüft ob Character auf der Brücke ist
    isOnBridge(x, y, bridge) {
        const dx = x - bridge.x;
        const dy = y - bridge.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Character ist auf Brücke wenn er nah genug am Brücken-Zentrum ist
        const bridgeRadius = Math.max(bridge.width, bridge.height) / 2 + 10;
        return distance < bridgeRadius;
    }
    
    // Distanz von Punkt zu Linie berechnen
    distanceToLineSegment(px, py, x1, y1, x2, y2) {
        const dx = x2 - x1;
        const dy = y2 - y1;
        const length = Math.sqrt(dx * dx + dy * dy);
        
        if (length === 0) return Math.sqrt((px - x1) * (px - x1) + (py - y1) * (py - y1));
        
        const t = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / (length * length)));
        const projection_x = x1 + t * dx;
        const projection_y = y1 + t * dy;
        
        return Math.sqrt((px - projection_x) * (px - projection_x) + (py - projection_y) * (py - projection_y));
    }
    
    // Findet Weg zur Brücke - verbesserte Logik
    findBridgePath(fromX, fromY, targetX, targetY) {
        const bridge = this.terrain.find(t => t.type === 'bridge');
        if (!bridge) return null;
        
        // Verwende das Brücken-Zentrum als primären Wegpunkt
        const bridgeCenter = { x: bridge.x, y: bridge.y };
        
        // Prüfe ob Character bereits auf der Brücke ist
        if (this.isOnBridge(fromX, fromY, bridge)) {
            // Auf der Brücke -> gehe zum anderen Ende oder zum Ziel
            const distToTarget = Math.sqrt((fromX - targetX) ** 2 + (fromY - targetY) ** 2);
            const distToBridge = Math.sqrt((fromX - bridgeCenter.x) ** 2 + (fromY - bridgeCenter.y) ** 2);
            
            return distToBridge > 20 ? bridgeCenter : null; // Gehe erst zur Brücken-Mitte
        }
        
        // Nicht auf Brücke -> gehe zum nächsten Brücken-Zugangspunkt
        const entry = bridge.crossingPoints[0];  // Links
        const exit = bridge.crossingPoints[1];   // Rechts
        
        const distToEntry = Math.sqrt((fromX - entry.x) ** 2 + (fromY - entry.y) ** 2);
        const distToExit = Math.sqrt((fromX - exit.x) ** 2 + (fromY - exit.y) ** 2);
        
        // Gehe zum nächstgelegenen Brücken-Zugangspunkt
        return distToEntry < distToExit ? entry : bridgeCenter;
    }
    
    // Bestimme auf welcher Seite des Flusses sich ein Punkt befindet
    getFlussSeite(x, y, river) {
        if (!river || !river.points) return 0;
        
        // Vereinfacht: nutze ersten und letzten Punkt für Richtung
        const start = river.points[0];
        const end = river.points[river.points.length - 1];
        
        // Kreuzprodukt zur Bestimmung der Seite
        const cross = (end.x - start.x) * (y - start.y) - (end.y - start.y) * (x - start.x);
        return cross > 0 ? 1 : -1;  // 1 = eine Seite, -1 = andere Seite
    }
    
    // Hilfsfunktion: Linien-Kreuzung prüfen
    lineIntersectsLine(x1, y1, x2, y2, x3, y3, x4, y4) {
        const denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
        if (denom === 0) return false;
        
        const t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom;
        const u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom;
        
        return t >= 0 && t <= 1 && u >= 0 && u <= 1;
    }

    setupEventListeners() {
        this.canvas.addEventListener('click', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Klick auf Charakter = neue Zielposition setzen
            this.characters.forEach(character => {
                const distance = Math.sqrt((x - character.x) ** 2 + (y - character.y) ** 2);
                if (distance < 20) {
                    character.targetX = x;
                    character.targetY = y;
                }
            });
        });

        window.addEventListener('resize', () => {
            this.canvas.width = window.innerWidth;
            this.canvas.height = window.innerHeight;
        });
    }

    render() {
    // Kamera-Update (Intro Zoom)
    this.updateCamera();
    this.ctx.save();
    this.ctx.setTransform(this.camera.zoom,0,0,this.camera.zoom, this.camera.offsetX||0, this.camera.offsetY||0);
    this.ctx.clearRect(-this.camera.offsetX/this.camera.zoom, -this.camera.offsetY/this.camera.zoom, this.canvas.width/this.camera.zoom, this.canvas.height/this.camera.zoom);
    this.drawTerrain();
    this.drawVegetation();  // Vegetation zwischen Terrain und Charakteren
    this.drawBuildPreview?.();
    // Lagerfeuer unter Charakteren aber über Terrain
    this.drawFires?.();
	this.drawAnimals?.();
    this.drawCharacters();
	this.drawSpeechBubbles();
    this.drawDebugOverlays();
    this.ctx.restore();
        
        // Debug output every 100 frames
        // Reduziere Spam: Frame-Statistik nur alle 5s exakt einmal
        const now = Date.now();
        if (!this._lastFrameStat || now - this._lastFrameStat > 5000) {
            console.log(`🎨 Rendering frame: ${this.characters.length} characters, ${this.terrain.length} terrain elements`);
            this._lastFrameStat = now;
        }
    }

    drawBuildPreview(){
        if (!this.buildPreview || !this.playerBuildMode) return;
        const p = this.buildPreview;
        this.ctx.save();
        this.ctx.strokeStyle = p.valid? 'rgba(80,200,120,0.9)' : 'rgba(220,60,60,0.9)';
        this.ctx.fillStyle = p.valid? 'rgba(80,200,120,0.18)' : 'rgba(220,60,60,0.18)';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.rect(p.x, p.y, p.w, p.h);
        this.ctx.fill();
        this.ctx.stroke();
        if (!p.valid && p.reason){
            this.ctx.font='11px Arial';
            this.ctx.fillStyle='#222';
            this.ctx.fillText(p.reason, p.x+4, p.y-6);
        }
        this.ctx.restore();
    }

    updateCamera(){
        if (!this.camera) return;
        if (this.introPhase?.active){
            // Finde Mittelpunkt der Gruppe
            const cx = this.canvas.width*0.5;
            const cy = this.canvas.height*0.5 - 80;
            if (this.introPhase.stage===0){
                // Smooth zoom in
                const t = Math.min(1,(Date.now()-this.introPhase.startTime)/1800);
                this.camera.targetZoom = 1.9 - 0.4*Math.cos(t*Math.PI*0.5); // easing in
            } else if (this.introPhase.stage===1){
                this.camera.targetZoom = 1.9; // Nah dran während Dialog
            } else if (this.introPhase.stage>=2){
                this.camera.targetZoom = 1.6; // leicht raus
            }
            this.camera.zoom += (this.camera.targetZoom - this.camera.zoom)*0.08;
            this.camera.offsetX = cx*(1 - this.camera.zoom);
            this.camera.offsetY = cy*(1 - this.camera.zoom);
        } else {
            // Nach Intro rauszoomen auf Standard (1.0)
            this.camera.targetZoom = 1.0;
            this.camera.zoom += (this.camera.targetZoom - this.camera.zoom)*0.04;
            const cx = this.canvas.width*0.5; const cy = this.canvas.height*0.5;
            this.camera.offsetX = cx*(1 - this.camera.zoom);
            this.camera.offsetY = cy*(1 - this.camera.zoom);
        }
    }

    drawAnimals(){
        if (!this.animals || !this.animals.length) return;
        this.animals.forEach(a => {
            this.ctx.save();
            // Schatten
            this.ctx.fillStyle='rgba(0,0,0,0.25)';
            this.ctx.beginPath();
            this.ctx.ellipse(a.x+2,a.y+10,10,4,0,0,Math.PI*2);
            this.ctx.fill();
            // Körper
            const bodyColor = a.type==='deer'? '#c28f5c':'#7a4f2a';
            this.ctx.fillStyle = bodyColor;
            // Simplified top-down pill shape
            this.ctx.beginPath();
            this.ctx.ellipse(a.x, a.y, a.type==='deer'?14:16, a.type==='deer'?8:10, 0, 0, Math.PI*2);
            this.ctx.fill();
            // Kopf
            this.ctx.beginPath();
            this.ctx.ellipse(a.x+(a.state==='flee'?6:5), a.y-2, a.type==='deer'?6:7, a.type==='deer'?5:5.5, 0,0,Math.PI*2);
            this.ctx.fillStyle = a.type==='deer'? '#d9a972':'#8a6036';
            this.ctx.fill();
            // Ohren (deer)
            if (a.type==='deer') {
                this.ctx.fillStyle = '#b17844';
                this.ctx.beginPath();
                this.ctx.arc(a.x+2, a.y-7, 2, 0, Math.PI*2);
                this.ctx.arc(a.x+8, a.y-6, 2, 0, Math.PI*2);
                this.ctx.fill();
            }
            // Gesundheitsbalken
            const hpPct = Math.max(0,a.health)/(a.type==='deer'?40:60);
            this.ctx.fillStyle='rgba(0,0,0,0.5)';
            this.ctx.fillRect(a.x-12, a.y+14, 24, 4);
            this.ctx.fillStyle = hpPct>0.5? '#4caf50': hpPct>0.25? '#ffc107':'#f44336';
            this.ctx.fillRect(a.x-12, a.y+14, 24*hpPct, 4);
            // Zustand
            if (a.state==='flee') {
                this.ctx.fillStyle='#ff5722';
                this.ctx.font='9px Arial';
                this.ctx.fillText('!', a.x-2, a.y-12);
            }
            this.ctx.restore();
        });
    }

    // Zeichnet aktive Lagerfeuer & Wärmeausbreitung
    drawFires(){
        if (!this.fires || !this.fires.length) return;
        const now = Date.now();
        this.fires = this.fires.filter(f => (now - f.startTime) < f.duration);
        this.fires.forEach(f => {
            const age = now - f.startTime;
            const life = age / f.duration; // 0..1
            const baseAlpha = life < 0.85 ? 0.55 : Math.max(0, 0.55 - (life-0.85)*4);
            // Puls / Flackern
            f.flicker += 0.25 + Math.random()*0.2;
            const flick = (Math.sin(f.flicker*2)+Math.sin(f.flicker*1.7+2))/2;
            const radius = f.radius * (0.95 + flick*0.03);
            const grd = this.ctx.createRadialGradient(f.x, f.y, 6, f.x, f.y, radius);
            grd.addColorStop(0, `rgba(255,180,80,${0.55 + flick*0.15})`);
            grd.addColorStop(0.25, `rgba(255,120,20,${0.45 + flick*0.1})`);
            grd.addColorStop(0.55, `rgba(255,60,0,${0.25 + flick*0.08})`);
            grd.addColorStop(1, 'rgba(255,40,0,0)');
            this.ctx.save();
            this.ctx.globalCompositeOperation = 'lighter';
            this.ctx.fillStyle = grd;
            this.ctx.beginPath();
            this.ctx.arc(f.x, f.y, radius, 0, Math.PI*2);
            this.ctx.fill();
            this.ctx.restore();
            // Kern-Flamme
            this.ctx.save();
            this.ctx.globalAlpha = baseAlpha + flick*0.1;
            const flameColors = ['#ffe6a3','#ffc766','#ff9933','#ff5722'];
            flameColors.forEach((col,i) => {
                this.ctx.fillStyle = col;
                const fr = 14 - i*3 + Math.sin(f.flicker* (1.2 + i*0.3))*1.5;
                this.ctx.beginPath();
                this.ctx.ellipse(f.x, f.y - 4 - i*2, fr*0.55, fr, 0, 0, Math.PI*2);
                this.ctx.fill();
            });
            this.ctx.restore();
            // Glut Funken (einfach)
            if (!f._embers) f._embers = [];
            if (f._embers.length < 20 && Math.random()<0.4){
                f._embers.push({x:f.x+(Math.random()-0.5)*18,y:f.y-6-Math.random()*8,vy:-0.2-Math.random()*0.4,life:400+Math.random()*400});
            }
            f._embers.forEach(em => {
                em.y += em.vy;
                em.life -= 16;
            });
            f._embers = f._embers.filter(e=>e.life>0);
            f._embers.forEach(em => {
                const a = Math.max(0, em.life/800);
                this.ctx.fillStyle = `rgba(255,200,120,${a})`;
                this.ctx.beginPath();
                this.ctx.arc(em.x, em.y, 2, 0, Math.PI*2);
                this.ctx.fill();
            });
        });
    }

    // Einfache Sprechblasen über den Charakteren (letzter Gedanke)
    drawSpeechBubbles() {
        this.characters.forEach(c => {
            if (!c.thoughts || !c.thoughts.length) return;
            const text = c.thoughts[c.thoughts.length-1];
            if (!text) return;
            const maxLen = 22;
            const display = text.length > maxLen ? text.slice(0,maxLen-1)+'…' : text;
            const padding = 4;
            this.ctx.font = '10px Arial';
            const width = this.ctx.measureText(display).width + padding*2;
            const x = c.x - width/2;
            const y = c.y - 55; // über Statusleisten
            // Blasen-Hintergrund
            this.ctx.fillStyle = 'rgba(255,255,255,0.85)';
            this.ctx.strokeStyle = 'rgba(0,0,0,0.2)';
            this.ctx.lineWidth = 1;
            this.roundRect(this.ctx, x, y, width, 16, 6, true, true);
            // Text
            this.ctx.fillStyle = '#222';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(display, c.x, y+11);
        });
    }

    // Hilfsfunktion für runde Rechtecke
    roundRect(ctx, x, y, w, h, r, fill, stroke) {
        if (typeof r === 'number') r = {tl:r,tr:r,br:r,bl:r};
        ctx.beginPath();
        ctx.moveTo(x + r.tl, y);
        ctx.lineTo(x + w - r.tr, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + r.tr);
        ctx.lineTo(x + w, y + h - r.br);
        ctx.quadraticCurveTo(x + w, y + h, x + w - r.br, y + h);
        ctx.lineTo(x + r.bl, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - r.bl);
        ctx.lineTo(x, y + r.tl);
        ctx.quadraticCurveTo(x, y, x + r.tl, y);
        ctx.closePath();
        if (fill) ctx.fill();
        if (stroke) ctx.stroke();
    }

    // Gruppierte Nahrungsbeschaffung koordinieren
    coordinateGroupHunt() {
        if (!this.socialSystem) return;
        // Verhindere zu häufige Auslösung
        if (this.socialSystem._lastGroupHunt && Date.now() - this.socialSystem._lastGroupHunt < 45000) return;
        const avgHunger = this.characters.reduce((a,c)=>a+c.hunger,0)/(this.characters.length||1);
        if (avgHunger < 55) return; // erst wenn moderater Hunger
        if (this.resources.food > 25) return; // genug Nahrung vorhanden
        // Wähle idle Charaktere
        const candidates = this.characters.filter(c => c.currentAction==='idle');
        if (candidates.length < 3) return;
        const participants = candidates.slice(0, Math.min(5, candidates.length));
        participants.forEach(p => this.startAction(p,'group_hunt'));
        this.socialSystem._lastGroupHunt = Date.now();
        this.addStory(`Eine Gruppe (${participants.map(p=>p.name.split(' ')[0]).join(', ')}) organisiert eine gemeinsame Nahrungsbeschaffung.`);
    }
    
    drawDebugOverlays() {
        // Only draw debug overlays if debug panel is visible
        if (window.debugManager && window.debugManager.isVisible) {
            
            // In drag mode: show terrain selection indicators
            if (window.debugManager.editMode === 'drag') {
                // Highlight selected element
                if (window.debugManager.selectedElement) {
                    const item = window.debugManager.selectedElement.item;
                    
                    // Selection ring
                    this.ctx.strokeStyle = '#4a90e2';
                    this.ctx.lineWidth = 3;
                    this.ctx.setLineDash([5, 5]);
                    this.ctx.beginPath();
                    this.ctx.arc(item.x, item.y, item.size + 8, 0, Math.PI * 2);
                    this.ctx.stroke();
                    this.ctx.setLineDash([]);
                    
                    // Position indicator
                    this.ctx.fillStyle = '#4a90e2';
                    this.ctx.beginPath();
                    this.ctx.arc(item.x, item.y, 3, 0, Math.PI * 2);
                    this.ctx.fill();
                    
                    // Position text
                    this.ctx.fillStyle = 'rgba(255,255,255,0.9)';
                    this.ctx.fillRect(item.x + 10, item.y - 25, 80, 20);
                    this.ctx.fillStyle = '#333';
                    this.ctx.font = '11px Arial';
                    this.ctx.textAlign = 'left';
                    this.ctx.fillText(`(${Math.round(item.x)}, ${Math.round(item.y)})`, item.x + 12, item.y - 12);
                }
                
                // Highlight hoverable elements
                this.terrain.forEach(item => {
                    if (item.type !== 'river' && item !== window.debugManager.selectedElement?.item) {
                        this.ctx.strokeStyle = 'rgba(74, 144, 226, 0.3)';
                        this.ctx.lineWidth = 2;
                        this.ctx.setLineDash([3, 3]);
                        this.ctx.beginPath();
                        this.ctx.arc(item.x, item.y, item.size + 4, 0, Math.PI * 2);
                        this.ctx.stroke();
                        this.ctx.setLineDash([]);
                    }
                });
            }
            
            // Show terrain elements that might be hidden behind UI panels
            this.drawHiddenElementsIndicator();
        }
    }
    
    drawHiddenElementsIndicator() {
        // Get UI panel positions and sizes
        const uiPanels = [
            { element: document.getElementById('ui'), color: '#ff6b6b' },
            { element: document.getElementById('characterInfo'), color: '#4ecdc4' }
        ];
        
        uiPanels.forEach(panel => {
            if (panel.element) {
                const rect = panel.element.getBoundingClientRect();
                const canvasRect = this.canvas.getBoundingClientRect();
                
                // Convert to canvas coordinates
                const panelX = rect.left - canvasRect.left;
                const panelY = rect.top - canvasRect.top;
                const panelWidth = rect.width;
                const panelHeight = rect.height;
                
                // Find terrain elements behind this panel
                const hiddenElements = this.terrain.filter(item => {
                    if (item.type === 'river') return false;
                    
                    return item.x >= panelX - item.size && 
                           item.x <= panelX + panelWidth + item.size &&
                           item.y >= panelY - item.size && 
                           item.y <= panelY + panelHeight + item.size;
                });
                
                // Draw indicators for hidden elements
                hiddenElements.forEach(item => {
                    // Draw pulsing outline to show hidden elements
                    const pulseIntensity = 0.3 + Math.sin(Date.now() * 0.005) * 0.3;
                    this.ctx.strokeStyle = `rgba(255, 107, 107, ${pulseIntensity})`;
                    this.ctx.lineWidth = 2;
                    this.ctx.setLineDash([4, 4]);
                    this.ctx.beginPath();
                    this.ctx.arc(item.x, item.y, item.size + 6, 0, Math.PI * 2);
                    this.ctx.stroke();
                    this.ctx.setLineDash([]);
                    
                    // Add small indicator arrow
                    this.ctx.fillStyle = `rgba(255, 107, 107, ${pulseIntensity})`;
                    this.ctx.font = '16px Arial';
                    this.ctx.textAlign = 'center';
                    this.ctx.fillText('⬆', item.x, item.y - item.size - 15);
                });
            }
        });
    }

    async gameLoop() {
        await this.updateCharacters();
        this.updateAnimals?.();
        this.updateGameTime();
        this.applyHomelessPenalties();
        this.render();
        // Fallback Watchdog: falls nach Intro >5s alles idle -> initialisieren
        if (!this.introPhase?.active) {
            if (!this._postIntroWatchStart) this._postIntroWatchStart = Date.now();
            if (!this._activatedPostIntroKick && Date.now()-this._postIntroWatchStart > 5000) {
                const allIdle = this.characters.every(c=>c.currentAction==='idle');
                if (allIdle) {
                    this.characters.forEach(c=>{ this.startAction(c,'gather_wood'); });
                    this._activatedPostIntroKick = true;
                }
            }
            // Sofortiger Kick wenn direkt nach Intro alle idle & kein Kick gesetzt
            if (!this._activatedImmediatePostIntro && this.characters.every(c=>c.currentAction==='idle' && c.actionTime===0)) {
                this._activatedImmediatePostIntro = true;
                this.characters.forEach(c=>{ this.startAction(c,'gather_food'); });
            }
        }
        requestAnimationFrame(()=>this.gameLoop());
    }

    // 🔍 Helper Methods
    getNearbyCharacters(character, radius = 100) {
        return this.characters.filter(c => 
            c !== character && 
            Math.sqrt(Math.pow(c.x - character.x, 2) + Math.pow(c.y - character.y, 2)) < radius
        );
    }

    getNearbyResources(character, radius = 150) {
        return this.terrain.filter(t => 
            (t.type === 'water_source' || t.type === 'food_source' || t.type === 'resource') &&
            Math.sqrt(Math.pow(t.x - character.x, 2) + Math.pow(t.y - character.y, 2)) < radius
        );
    }
}