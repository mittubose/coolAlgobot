/**
 * Achievement System
 * Gamification for trading bot - rewards user milestones
 *
 * Features:
 * - 20+ achievements with rarity levels (common, rare, epic, legendary)
 * - Unlock animations with confetti
 * - Points system
 * - Progress tracking
 * - Achievement page UI
 */

// Achievement Definitions
const ACHIEVEMENTS = [
    // ========== Beginner Achievements (Common) ==========
    {
        id: 'first_trade',
        name: 'First Trade',
        description: 'Placed your first order',
        icon: '🎯',
        rarity: 'common',
        points: 10,
        category: 'milestones',
        condition: (stats) => stats.totalTrades >= 1
    },
    {
        id: 'first_profit',
        name: 'In the Green',
        description: 'Made your first profitable trade',
        icon: '💰',
        rarity: 'common',
        points: 20,
        category: 'performance',
        condition: (stats) => stats.profitableTrades >= 1
    },
    {
        id: 'config_complete',
        name: 'Setup Complete',
        description: 'Configured all trading parameters',
        icon: '⚙️',
        rarity: 'common',
        points: 25,
        category: 'setup',
        condition: (stats) => stats.configComplete === true
    },
    {
        id: 'first_strategy',
        name: 'Strategy Creator',
        description: 'Created your first trading strategy',
        icon: '📝',
        rarity: 'common',
        points: 30,
        category: 'milestones',
        condition: (stats) => stats.strategiesCreated >= 1
    },
    {
        id: 'early_bird',
        name: 'Early Bird',
        description: 'Placed trades within 15 minutes of market open',
        icon: '🌅',
        rarity: 'common',
        points: 30,
        category: 'trading',
        condition: (stats) => stats.earlyTrades >= 1
    },

    // ========== Strategy Achievements (Rare) ==========
    {
        id: 'strategy_master',
        name: 'Strategy Master',
        description: 'Created 5 different strategies',
        icon: '🧠',
        rarity: 'rare',
        points: 50,
        category: 'milestones',
        condition: (stats) => stats.strategiesCreated >= 5
    },
    {
        id: 'backtest_guru',
        name: 'Backtest Guru',
        description: 'Ran 20 backtests',
        icon: '📊',
        rarity: 'rare',
        points: 75,
        category: 'analysis',
        condition: (stats) => stats.backtests >= 20
    },
    {
        id: 'strategy_optimizer',
        name: 'Strategy Optimizer',
        description: 'Improved a strategy win rate by 10%+',
        icon: '🔧',
        rarity: 'rare',
        points: 100,
        category: 'performance',
        condition: (stats) => stats.strategyOptimizations >= 1
    },

    // ========== Performance Achievements (Rare/Epic) ==========
    {
        id: 'profit_streak_5',
        name: 'Hot Streak',
        description: '5 profitable trades in a row',
        icon: '🔥',
        rarity: 'rare',
        points: 100,
        category: 'performance',
        condition: (stats) => stats.longestWinStreak >= 5
    },
    {
        id: 'profit_streak_10',
        name: 'Unstoppable',
        description: '10 profitable trades in a row',
        icon: '⚡',
        rarity: 'epic',
        points: 250,
        category: 'performance',
        condition: (stats) => stats.longestWinStreak >= 10
    },
    {
        id: 'win_rate_70',
        name: 'Consistent Trader',
        description: 'Achieved 70%+ win rate over 20 trades',
        icon: '🎯',
        rarity: 'rare',
        points: 150,
        category: 'performance',
        condition: (stats) => stats.totalTrades >= 20 && stats.winRate >= 70
    },
    {
        id: 'win_rate_80',
        name: 'Sniper',
        description: 'Achieved 80%+ win rate over 50 trades',
        icon: '🎯',
        rarity: 'epic',
        points: 300,
        category: 'performance',
        condition: (stats) => stats.totalTrades >= 50 && stats.winRate >= 80
    },

    // ========== Milestone Achievements (Rare/Epic) ==========
    {
        id: 'trades_10',
        name: 'Getting Started',
        description: 'Executed 10 trades',
        icon: '📈',
        rarity: 'common',
        points: 40,
        category: 'milestones',
        condition: (stats) => stats.totalTrades >= 10
    },
    {
        id: 'trades_50',
        name: 'Active Trader',
        description: 'Executed 50 trades',
        icon: '💹',
        rarity: 'rare',
        points: 100,
        category: 'milestones',
        condition: (stats) => stats.totalTrades >= 50
    },
    {
        id: 'trades_100',
        name: 'Centurion',
        description: 'Executed 100 trades',
        icon: '💯',
        rarity: 'epic',
        points: 200,
        category: 'milestones',
        condition: (stats) => stats.totalTrades >= 100
    },
    {
        id: 'profit_1000',
        name: 'Four Figures',
        description: 'Earned ₹1,000 in total profit',
        icon: '💵',
        rarity: 'rare',
        points: 150,
        category: 'milestones',
        condition: (stats) => stats.totalProfit >= 1000
    },
    {
        id: 'profit_10000',
        name: 'Five Figures',
        description: 'Earned ₹10,000 in total profit',
        icon: '💰',
        rarity: 'epic',
        points: 500,
        category: 'milestones',
        condition: (stats) => stats.totalProfit >= 10000
    },
    {
        id: 'profit_100000',
        name: 'Six Figures',
        description: 'Earned ₹1,00,000 in total profit',
        icon: '💎',
        rarity: 'legendary',
        points: 2000,
        category: 'milestones',
        condition: (stats) => stats.totalProfit >= 100000
    },

    // ========== Risk Management Achievements (Rare/Epic) ==========
    {
        id: 'stop_loss_saver',
        name: 'Risk Manager',
        description: 'Stop-loss saved you from a larger loss',
        icon: '🛡️',
        rarity: 'rare',
        points: 100,
        category: 'risk',
        condition: (stats) => stats.stopLossSaves >= 1
    },
    {
        id: 'no_loss_day',
        name: 'Perfect Day',
        description: 'Completed a trading day with zero losses',
        icon: '✨',
        rarity: 'epic',
        points: 200,
        category: 'performance',
        condition: (stats) => stats.perfectDays >= 1
    },
    {
        id: 'week_streak',
        name: 'Weekly Warrior',
        description: 'Traded profitably for 7 consecutive days',
        icon: '📅',
        rarity: 'epic',
        points: 300,
        category: 'performance',
        condition: (stats) => stats.consecutiveProfitDays >= 7
    },

    // ========== Special Achievements (Epic/Legendary) ==========
    {
        id: 'comeback_king',
        name: 'Comeback King',
        description: 'Recovered from a -5% day to end positive',
        icon: '👑',
        rarity: 'epic',
        points: 250,
        category: 'special',
        condition: (stats) => stats.comebacks >= 1
    },
    {
        id: 'diamond_hands',
        name: 'Diamond Hands',
        description: 'Held a winning position through a drawdown',
        icon: '💎',
        rarity: 'rare',
        points: 125,
        category: 'trading',
        condition: (stats) => stats.diamondHands >= 1
    },
    {
        id: 'master_trader',
        name: 'Master Trader',
        description: 'Achieved 75%+ win rate over 200 trades',
        icon: '🏆',
        rarity: 'legendary',
        points: 1000,
        category: 'performance',
        condition: (stats) => stats.totalTrades >= 200 && stats.winRate >= 75
    }
];

// Achievement Manager Class
class AchievementManager {
    constructor() {
        this.achievements = ACHIEVEMENTS;
        this.unlockedAchievements = this.loadUnlocked();
        this.checkQueue = [];
        this.isChecking = false;
        this.init();
    }

    init() {
        console.log('Achievement Manager initialized');
        console.log(`Total achievements: ${this.achievements.length}`);
        console.log(`Unlocked: ${this.unlockedAchievements.length}`);
    }

    loadUnlocked() {
        try {
            const stored = localStorage.getItem('unlockedAchievements');
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.error('Error loading unlocked achievements:', error);
            return [];
        }
    }

    saveUnlocked() {
        try {
            localStorage.setItem('unlockedAchievements', JSON.stringify(this.unlockedAchievements));
        } catch (error) {
            console.error('Error saving unlocked achievements:', error);
        }
    }

    async checkAchievements(stats) {
        if (this.isChecking) {
            this.checkQueue.push(stats);
            return [];
        }

        this.isChecking = true;
        const newUnlocks = [];

        try {
            for (const achievement of this.achievements) {
                // Skip already unlocked
                if (this.unlockedAchievements.includes(achievement.id)) {
                    continue;
                }

                // Check condition
                try {
                    if (achievement.condition(stats)) {
                        await this.unlockAchievement(achievement);
                        newUnlocks.push(achievement);
                    }
                } catch (error) {
                    console.error(`Error checking achievement ${achievement.id}:`, error);
                }
            }
        } finally {
            this.isChecking = false;

            // Process queued checks
            if (this.checkQueue.length > 0) {
                const nextStats = this.checkQueue.shift();
                setTimeout(() => this.checkAchievements(nextStats), 500);
            }
        }

        return newUnlocks;
    }

    async unlockAchievement(achievement) {
        this.unlockedAchievements.push(achievement.id);
        this.saveUnlocked();

        // Show unlock animation
        this.showUnlockAnimation(achievement);

        // Update UI
        this.updateUI();

        // Log unlock
        console.log(`🏆 Achievement Unlocked: ${achievement.name} (+${achievement.points} points)`);
    }

    showUnlockAnimation(achievement) {
        const modal = document.createElement('div');
        modal.className = 'achievement-unlock-modal';
        modal.innerHTML = `
            <div class="achievement-unlock achievement-unlock--${achievement.rarity}">
                <div class="achievement-unlock__header">
                    <div class="achievement-unlock__badge achievement-unlock__badge--${achievement.rarity}">
                        ${achievement.rarity.toUpperCase()}
                    </div>
                    <h3 class="achievement-unlock__title">Achievement Unlocked!</h3>
                </div>
                <div class="achievement-unlock__icon">${achievement.icon}</div>
                <h2 class="achievement-unlock__name">${achievement.name}</h2>
                <p class="achievement-unlock__description">${achievement.description}</p>
                <div class="achievement-unlock__points">
                    +${achievement.points} points
                </div>
                <button class="achievement-unlock__close" onclick="this.closest('.achievement-unlock-modal').remove()">
                    <i data-lucide="x" style="width: 20px; height: 20px;"></i>
                </button>
            </div>
        `;

        document.body.appendChild(modal);

        // Initialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        // Trigger confetti
        this.triggerConfetti(achievement.rarity);

        // Play sound
        this.playUnlockSound(achievement.rarity);

        // Auto-remove after 5 seconds (or click)
        setTimeout(() => {
            if (modal.parentElement) {
                modal.classList.add('achievement-unlock-modal--fadeout');
                setTimeout(() => {
                    if (modal.parentElement) {
                        modal.remove();
                    }
                }, 500);
            }
        }, 5000);
    }

    triggerConfetti(rarity) {
        // Check if confetti library is available
        if (typeof confetti === 'undefined') {
            console.warn('Confetti library not loaded');
            return;
        }

        const colors = {
            common: ['#3B82F6', '#60A5FA', '#93C5FD'],
            rare: ['#7C3AED', '#A78BFA', '#C4B5FD'],
            epic: ['#F59E0B', '#FBBF24', '#FCD34D'],
            legendary: ['#EF4444', '#F87171', '#FCA5A5', '#FBBF24', '#A78BFA']
        };

        const particleCount = {
            common: 50,
            rare: 100,
            epic: 150,
            legendary: 300
        };

        confetti({
            particleCount: particleCount[rarity],
            spread: 70,
            origin: { y: 0.6 },
            colors: colors[rarity],
            ticks: 200,
            gravity: 1,
            decay: 0.94,
            startVelocity: 30
        });

        // Extra burst for legendary
        if (rarity === 'legendary') {
            setTimeout(() => {
                confetti({
                    particleCount: 150,
                    angle: 60,
                    spread: 55,
                    origin: { x: 0 },
                    colors: colors[rarity]
                });
                confetti({
                    particleCount: 150,
                    angle: 120,
                    spread: 55,
                    origin: { x: 1 },
                    colors: colors[rarity]
                });
            }, 250);
        }
    }

    playUnlockSound(rarity) {
        // Play achievement sound (different pitch for rarity)
        // Note: Sound file would need to be added to /static/sounds/
        try {
            const audio = new Audio('/static/sounds/achievement.mp3');
            audio.playbackRate = {
                common: 1.0,
                rare: 1.1,
                epic: 1.2,
                legendary: 1.3
            }[rarity];
            audio.volume = 0.5;
            audio.play().catch(() => {
                // User hasn't interacted yet, can't play sound
                console.log('Sound play blocked (user interaction required)');
            });
        } catch (error) {
            console.log('Achievement sound not available');
        }
    }

    getTotalPoints() {
        return this.unlockedAchievements.reduce((sum, id) => {
            const achievement = this.achievements.find(a => a.id === id);
            return sum + (achievement?.points || 0);
        }, 0);
    }

    getProgress() {
        return {
            unlocked: this.unlockedAchievements.length,
            total: this.achievements.length,
            percentage: Math.round((this.unlockedAchievements.length / this.achievements.length) * 100)
        };
    }

    getAchievementsByCategory() {
        const categories = {};

        this.achievements.forEach(achievement => {
            const category = achievement.category;
            if (!categories[category]) {
                categories[category] = {
                    name: this.getCategoryName(category),
                    achievements: [],
                    unlocked: 0,
                    total: 0
                };
            }

            categories[category].achievements.push(achievement);
            categories[category].total++;

            if (this.unlockedAchievements.includes(achievement.id)) {
                categories[category].unlocked++;
            }
        });

        return categories;
    }

    getCategoryName(category) {
        const names = {
            milestones: 'Milestones',
            performance: 'Performance',
            setup: 'Setup',
            trading: 'Trading',
            analysis: 'Analysis',
            risk: 'Risk Management',
            special: 'Special'
        };
        return names[category] || category;
    }

    getAchievementsByRarity() {
        const rarities = {
            common: [],
            rare: [],
            epic: [],
            legendary: []
        };

        this.achievements.forEach(achievement => {
            rarities[achievement.rarity].push(achievement);
        });

        return rarities;
    }

    isUnlocked(achievementId) {
        return this.unlockedAchievements.includes(achievementId);
    }

    getAchievement(achievementId) {
        return this.achievements.find(a => a.id === achievementId);
    }

    updateUI() {
        // Update achievement counters in UI
        const totalPointsEl = document.getElementById('totalAchievementPoints');
        if (totalPointsEl) {
            totalPointsEl.textContent = this.getTotalPoints();
        }

        const progressEl = document.getElementById('achievementProgress');
        if (progressEl) {
            const progress = this.getProgress();
            progressEl.textContent = `${progress.unlocked}/${progress.total}`;
        }

        const percentEl = document.getElementById('achievementPercent');
        if (percentEl) {
            const progress = this.getProgress();
            percentEl.textContent = `${progress.percentage}%`;
        }

        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('achievementUnlocked', {
            detail: { totalPoints: this.getTotalPoints() }
        }));
    }

    // Manual trigger for testing
    testUnlock(achievementId) {
        const achievement = this.getAchievement(achievementId);
        if (achievement && !this.isUnlocked(achievementId)) {
            this.unlockAchievement(achievement);
        }
    }

    // Reset all achievements (for testing)
    resetAll() {
        if (confirm('Are you sure you want to reset all achievements? This cannot be undone.')) {
            this.unlockedAchievements = [];
            this.saveUnlocked();
            this.updateUI();
            console.log('All achievements reset');
            if (typeof Toast !== 'undefined') {
                Toast.info('All achievements reset');
            }
        }
    }
}

// Initialize global achievement manager
const achievementManager = new AchievementManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AchievementManager, ACHIEVEMENTS };
}
