/**
 * Chinese Word Hunt - Game Logic
 * 
 * Core game mechanics for radical-based Chinese character puzzle game.
 */

class ChineseWordHunt {
    constructor() {
        this.database = null;
        this.grid = [];
        this.selectedTiles = [];
        this.foundWords = new Set();
        this.score = 0;
        this.timeRemaining = 80;
        this.timerInterval = null;
        this.isPlaying = false;
        this.validCharsOnBoard = new Map();
        this.visualAliases = {};  // Maps semantic radicals to visual display forms
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.renderEmptyGrid();  // Show placeholder while loading
        await this.loadDatabase();
    }

    async loadDatabase() {
        try {
            const response = await fetch('radical_database.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.database = await response.json();
            this.visualAliases = this.database.visual_aliases || {};
            console.log(`Loaded ${this.database.metadata.total_characters} characters`);
            // Pre-generate the board so it's ready when user clicks
            this.generateBoard();
            this.renderGrid();
        } catch (error) {
            console.error('Failed to load database:', error);
        }
    }

    setupEventListeners() {
        document.getElementById('new-game-btn').addEventListener('click', () => this.startGame());
        document.getElementById('play-again-btn').addEventListener('click', () => {
            document.getElementById('gameover-modal').style.display = 'none';
            this.startGame();
        });
        
        document.getElementById('help-btn').addEventListener('click', () => {
            document.getElementById('help-modal').style.display = 'flex';
        });
        
        document.getElementById('close-help').addEventListener('click', () => {
            document.getElementById('help-modal').style.display = 'none';
        });
        
        document.getElementById('help-modal').addEventListener('click', (e) => {
            if (e.target.id === 'help-modal') {
                document.getElementById('help-modal').style.display = 'none';
            }
        });

        const grid = document.getElementById('game-grid');
        
        grid.addEventListener('mousedown', (e) => this.handlePointerStart(e));
        grid.addEventListener('mousemove', (e) => this.handlePointerMove(e));
        document.addEventListener('mouseup', () => this.handlePointerEnd());
        
        grid.addEventListener('touchstart', (e) => this.handlePointerStart(e), { passive: false });
        grid.addEventListener('touchmove', (e) => this.handlePointerMove(e), { passive: false });
        document.addEventListener('touchend', () => this.handlePointerEnd());
    }

    handlePointerStart(e) {
        e.preventDefault();
        
        const tile = this.getTileFromEvent(e);
        if (tile === null) return;
        
        // Auto-start game on first tile interaction
        if (!this.isPlaying && this.database) {
            this.startGame();
        }
        
        if (!this.isPlaying) return;
        
        this.selectedTiles = [tile];
        this.updateTileSelection();
        this.updateSelectionDisplay();
    }

    handlePointerMove(e) {
        if (!this.isPlaying || this.selectedTiles.length === 0) return;
        e.preventDefault();
        
        const tile = this.getTileFromEvent(e);
        if (tile !== null && !this.selectedTiles.includes(tile)) {
            const lastTile = this.selectedTiles[this.selectedTiles.length - 1];
            if (this.isAdjacent(lastTile, tile)) {
                this.selectedTiles.push(tile);
                this.updateTileSelection();
                this.updateSelectionDisplay();
            }
        }
    }

    handlePointerEnd() {
        if (!this.isPlaying || this.selectedTiles.length === 0) return;
        
        this.checkWord();
        this.selectedTiles = [];
        this.updateTileSelection();
        this.updateSelectionDisplay();
    }

    getTileFromEvent(e) {
        let clientX, clientY;
        
        if (e.touches) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }
        
        const element = document.elementFromPoint(clientX, clientY);
        if (element && element.classList.contains('tile')) {
            return parseInt(element.dataset.index);
        }
        return null;
    }

    isAdjacent(index1, index2) {
        const row1 = Math.floor(index1 / 4);
        const col1 = index1 % 4;
        const row2 = Math.floor(index2 / 4);
        const col2 = index2 % 4;
        
        const rowDiff = Math.abs(row1 - row2);
        const colDiff = Math.abs(col1 - col2);
        
        return rowDiff <= 1 && colDiff <= 1 && !(rowDiff === 0 && colDiff === 0);
    }

    updateTileSelection() {
        const tiles = document.querySelectorAll('.tile');
        tiles.forEach((tile, index) => {
            tile.classList.toggle('selected', this.selectedTiles.includes(index));
        });
    }

    updateSelectionDisplay() {
        const radicalsDiv = document.getElementById('current-radicals');
        const charDiv = document.getElementById('current-char');
        
        if (this.selectedTiles.length === 0) {
            radicalsDiv.innerHTML = '';
            charDiv.textContent = '';
            charDiv.className = 'current-char';
            return;
        }
        
        const radicals = this.selectedTiles.map(i => this.grid[i]);
        // Display visual forms in the selection display
        radicalsDiv.innerHTML = radicals.map(r => `<span class="radical">${this.getDisplayForm(r)}</span>`).join('');
        
        // Normalize to semantic forms for matching
        const semanticRadicals = this.normalizeForMatching(radicals);
        const key = [...semanticRadicals].sort().join(',');
        const matches = this.database.radical_combinations[key] || [];
        
        if (matches.length > 0 && radicals.length >= 2) {
            const unfound = matches.filter(c => !this.foundWords.has(c));
            if (unfound.length > 0) {
                charDiv.textContent = unfound[0];
                charDiv.className = 'current-char';
            } else {
                // All matches already found - show yellow
                charDiv.textContent = matches[0];
                charDiv.className = 'current-char already-found';
            }
        } else {
            charDiv.textContent = radicals.length >= 2 ? '?' : '';
            charDiv.className = 'current-char invalid';
        }
    }

    checkWord() {
        if (this.selectedTiles.length < 2) return;
        
        const radicals = this.selectedTiles.map(i => this.grid[i]);
        // Normalize to semantic forms for matching
        const semanticRadicals = this.normalizeForMatching(radicals);
        const key = [...semanticRadicals].sort().join(',');
        const matches = this.database.radical_combinations[key] || [];
        
        for (const char of matches) {
            if (!this.foundWords.has(char)) {
                this.foundWords.add(char);
                const charData = this.database.characters[char];
                const points = charData.complexity;
                this.score += points;
                
                this.addFoundWord(char, points);
                this.updateStats();
                
                const lastTile = document.querySelector(`.tile[data-index="${this.selectedTiles[this.selectedTiles.length - 1]}"]`);
                if (lastTile) {
                    lastTile.classList.add('pop');
                    setTimeout(() => lastTile.classList.remove('pop'), 200);
                }
                
                return;
            }
        }
    }

    addFoundWord(char, points) {
        const container = document.getElementById('found-words');
        const wordEl = document.createElement('div');
        wordEl.className = 'found-word';
        wordEl.innerHTML = `${char} <span class="points">+${points}</span>`;
        container.insertBefore(wordEl, container.firstChild);
    }

    updateStats() {
        document.getElementById('score').textContent = this.score;
        document.getElementById('found-count').textContent = this.foundWords.size;
        document.getElementById('found-total').textContent = `(${this.foundWords.size}/${this.validCharsOnBoard.size})`;
    }

    startGame() {
        this.selectedTiles = [];
        this.foundWords = new Set();
        this.score = 0;
        this.timeRemaining = 80;
        this.isPlaying = true;
        
        document.getElementById('found-words').innerHTML = '';
        document.getElementById('new-game-btn').style.display = 'inline-block';
        
        // Only regenerate board if starting a new game (not first start)
        if (this.grid.length === 0) {
            this.generateBoard();
        } else {
            // New game - regenerate
            this.grid = [];
            this.generateBoard();
        }
        this.renderGrid();
        this.updateStats();
        this.startTimer();
    }

    generateBoard() {
        const targetSolutions = 50;
        let bestBoard = null;
        let bestSolutionCount = 0;
        
        for (let attempt = 0; attempt < 20; attempt++) {
            const board = this.generateCandidateBoard();
            const solutions = this.countValidSolutions(board);
            
            if (solutions.size > bestSolutionCount) {
                bestBoard = board;
                bestSolutionCount = solutions.size;
                this.validCharsOnBoard = solutions;
                
                if (solutions.size >= targetSolutions) {
                    break;
                }
            }
        }
        
        this.grid = bestBoard || this.generateCandidateBoard();
        if (!this.validCharsOnBoard || this.validCharsOnBoard.size === 0) {
            this.validCharsOnBoard = this.countValidSolutions(this.grid);
        }
        console.log(`Generated board with ${this.validCharsOnBoard.size} valid characters`);
    }

    generateCandidateBoard() {
        const radicalFreq = this.getRadicalFrequencies();
        const weightedRadicals = [];
        
        for (const [radical, freq] of Object.entries(radicalFreq)) {
            const weight = Math.ceil(Math.sqrt(freq));
            for (let i = 0; i < weight; i++) {
                weightedRadicals.push(radical);
            }
        }
        
        const board = [];
        const usedRadicals = new Set();
        
        const seedChars = this.getRandomHighValueChars(4);
        for (const charData of seedChars) {
            for (const radical of charData.radicals) {
                if (board.length < 16 && !usedRadicals.has(radical)) {
                    board.push(radical);
                    usedRadicals.add(radical);
                }
            }
        }
        
        while (board.length < 16) {
            const radical = weightedRadicals[Math.floor(Math.random() * weightedRadicals.length)];
            if (!usedRadicals.has(radical) || board.length > 10) {
                board.push(radical);
                if (board.length <= 10) usedRadicals.add(radical);
            }
        }
        
        for (let i = board.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [board[i], board[j]] = [board[j], board[i]];
        }
        
        return board;
    }

    getRadicalFrequencies() {
        const freq = {};
        for (const charData of Object.values(this.database.characters)) {
            for (const radical of charData.radicals) {
                freq[radical] = (freq[radical] || 0) + 1;
            }
        }
        return freq;
    }

    getRandomHighValueChars(count) {
        const chars = Object.entries(this.database.characters)
            .filter(([_, data]) => data.radical_count === 2)
            .sort(() => Math.random() - 0.5)
            .slice(0, count * 3);
        
        return chars
            .sort((a, b) => b[1].complexity - a[1].complexity)
            .slice(0, count)
            .map(([char, data]) => ({ char, ...data }));
    }

    countValidSolutions(board) {
        const solutions = new Map();
        const boardSet = new Set(board);
        
        for (const [char, data] of Object.entries(this.database.characters)) {
            const radicals = data.radicals;
            
            if (!radicals.every(r => boardSet.has(r))) continue;
            
            if (this.canFormWithAdjacency(board, radicals)) {
                solutions.set(char, data);
            }
        }
        
        return solutions;
    }

    canFormWithAdjacency(board, radicals) {
        const radicalPositions = new Map();
        for (let i = 0; i < board.length; i++) {
            const r = board[i];
            if (!radicalPositions.has(r)) {
                radicalPositions.set(r, []);
            }
            radicalPositions.get(r).push(i);
        }
        
        for (const r of radicals) {
            if (!radicalPositions.has(r)) return false;
        }
        
        // For 2-radical characters (most common), just check if any pair is adjacent
        if (radicals.length === 2) {
            const pos1List = radicalPositions.get(radicals[0]) || [];
            const pos2List = radicalPositions.get(radicals[1]) || [];
            
            for (const p1 of pos1List) {
                for (const p2 of pos2List) {
                    if (p1 !== p2 && this.isAdjacent(p1, p2)) {
                        return true;
                    }
                }
            }
            return false;
        }
        
        // For 3+ radicals, use simplified path finding (limit permutations)
        const findPath = (remaining, usedPositions, lastPos) => {
            if (remaining.length === 0) return true;
            
            const radical = remaining[0];
            const positions = radicalPositions.get(radical) || [];
            
            for (const pos of positions) {
                if (usedPositions.has(pos)) continue;
                
                if (lastPos === -1 || this.isAdjacent(pos, lastPos)) {
                    usedPositions.add(pos);
                    if (findPath(remaining.slice(1), usedPositions, pos)) {
                        return true;
                    }
                    usedPositions.delete(pos);
                }
            }
            
            return false;
        };
        
        // Only try a few permutations for longer radical lists
        const maxPerms = radicals.length <= 3 ? 6 : 4;
        const perms = this.getPermutations(radicals).slice(0, maxPerms);
        
        for (const perm of perms) {
            if (findPath(perm, new Set(), -1)) {
                return true;
            }
        }
        
        return false;
    }

    isAdjacentToAny(pos, usedPositions) {
        for (const used of usedPositions) {
            if (this.isAdjacent(pos, used)) {
                return true;
            }
        }
        return false;
    }

    getPermutations(arr) {
        if (arr.length <= 1) return [arr];
        if (arr.length === 2) return [arr, [arr[1], arr[0]]];
        
        const result = [];
        for (let i = 0; i < arr.length; i++) {
            const rest = [...arr.slice(0, i), ...arr.slice(i + 1)];
            for (const perm of this.getPermutations(rest)) {
                result.push([arr[i], ...perm]);
            }
        }
        return result;
    }

    renderEmptyGrid() {
        const gridEl = document.getElementById('game-grid');
        gridEl.innerHTML = '';
        
        // Show sample radicals as placeholder
        const sampleRadicals = ['一', '口', '人', '木', '水', '日', '土', '火', '山', '心', '金', '手', '女', '大', '田', '目'];
        for (let i = 0; i < 16; i++) {
            const tile = document.createElement('div');
            tile.className = 'tile disabled';
            tile.dataset.index = i;
            tile.textContent = sampleRadicals[i];
            gridEl.appendChild(tile);
        }
    }

    getDisplayForm(radical) {
        // Convert semantic radical to its visual display form
        if (this.visualAliases[radical]) {
            return this.visualAliases[radical].display;
        }
        return radical;
    }

    getSemanticForm(radical) {
        // Convert visual form back to semantic form for matching
        // Check if this radical is a visual form of another
        for (const [semantic, data] of Object.entries(this.visualAliases)) {
            if (data.display === radical) {
                return semantic;
            }
        }
        return radical;
    }

    normalizeForMatching(radicals) {
        // Normalize radicals to their semantic forms for database lookup
        return radicals.map(r => this.getSemanticForm(r));
    }

    renderGrid() {
        const gridEl = document.getElementById('game-grid');
        gridEl.innerHTML = '';
        
        for (let i = 0; i < 16; i++) {
            const tile = document.createElement('div');
            tile.className = 'tile';
            tile.dataset.index = i;
            // Display the visual form of the radical
            tile.textContent = this.getDisplayForm(this.grid[i]);
            // Store the semantic form for matching
            tile.dataset.semantic = this.grid[i];
            gridEl.appendChild(tile);
        }
    }

    startTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        
        this.updateTimerDisplay();
        
        this.timerInterval = setInterval(() => {
            this.timeRemaining--;
            this.updateTimerDisplay();
            
            if (this.timeRemaining <= 0) {
                this.endGame();
            }
        }, 1000);
    }

    updateTimerDisplay() {
        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        document.getElementById('timer').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    endGame() {
        this.isPlaying = false;
        clearInterval(this.timerInterval);
        
        document.getElementById('final-score').textContent = this.score;
        document.getElementById('final-count').textContent = this.foundWords.size;
        document.getElementById('gameover-modal').style.display = 'flex';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.game = new ChineseWordHunt();
});
