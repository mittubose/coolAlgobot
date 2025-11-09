/**
 * Stats Tracker
 * Tracks trading statistics and triggers achievement checks
 *
 * Integrates with:
 * - Achievement System
 * - Streak Tracker
 * - Celebration System
 */

class StatsTracker {
    constructor() {
        this.stats = this.loadStats();
        this.init();
    }

    init() {
        console.log('Stats Tracker initialized');

        // Listen for trade updates
        window.addEventListener('tradeExecuted', (event) => {
            this.onTradeExecuted(event.detail);
        });

        // Listen for strategy events
        window.addEventListener('strategyCreated', (event) => {
            this.onStrategyCreated(event.detail);
        });

        window.addEventListener('backtestCompleted', (event) => {
            this.onBacktestCompleted(event.detail);
        });
    }

    loadStats() {
        try {
            const stored = localStorage.getItem('tradingStats');
            if (stored) {
                return JSON.parse(stored);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }

        // Default stats
        return {
            // Trade metrics
            totalTrades: 0,
            profitableTrades: 0,
            losingTrades: 0,
            totalProfit: 0,
            totalLoss: 0,
            winRate: 0,

            // Streak tracking
            currentWinStreak: 0,
            longestWinStreak: 0,
            currentLossStreak: 0,
            longestLossStreak: 0,

            // Daily tracking
            consecutiveProfitDays: 0,
            longestProfitDayStreak: 0,
            perfectDays: 0,

            // Strategy metrics
            strategiesCreated: 0,
            strategiesActive: 0,
            backtests: 0,
            strategyOptimizations: 0,

            // Special achievements
            earlyTrades: 0,
            stopLossSaves: 0,
            diamondHands: 0,
            comebacks: 0,

            // Configuration
            configComplete: false,

            // Last update
            lastUpdated: new Date().toISOString()
        };
    }

    saveStats() {
        try {
            this.stats.lastUpdated = new Date().toISOString();
            localStorage.setItem('tradingStats', JSON.stringify(this.stats));
        } catch (error) {
            console.error('Error saving stats:', error);
        }
    }

    async onTradeExecuted(trade) {
        console.log('Trade executed:', trade);

        // Update basic trade counts
        this.stats.totalTrades++;

        // Check if profitable
        const isProfitable = trade.pnl > 0;

        if (isProfitable) {
            this.stats.profitableTrades++;
            this.stats.totalProfit += trade.pnl;

            // Update win streak
            this.stats.currentWinStreak++;
            this.stats.currentLossStreak = 0;

            if (this.stats.currentWinStreak > this.stats.longestWinStreak) {
                this.stats.longestWinStreak = this.stats.currentWinStreak;
            }

            // Check for celebration moments
            this.checkCelebrations(trade);

        } else {
            this.stats.losingTrades++;
            this.stats.totalLoss += Math.abs(trade.pnl);

            // Update loss streak
            this.stats.currentLossStreak++;
            this.stats.currentWinStreak = 0;

            if (this.stats.currentLossStreak > this.stats.longestLossStreak) {
                this.stats.longestLossStreak = this.stats.currentLossStreak;
            }
        }

        // Calculate win rate
        this.stats.winRate = (this.stats.profitableTrades / this.stats.totalTrades) * 100;

        // Check if early trade (within 15 minutes of market open)
        if (this.isEarlyTrade(trade.time)) {
            this.stats.earlyTrades++;
        }

        // Check for stop loss save
        if (trade.exitReason === 'stop_loss' && trade.potentialLoss) {
            if (Math.abs(trade.pnl) < trade.potentialLoss) {
                this.stats.stopLossSaves++;
            }
        }

        // Check for diamond hands (held through drawdown)
        if (trade.maxDrawdown && trade.maxDrawdown > 2 && isProfitable) {
            this.stats.diamondHands++;
        }

        // Save stats
        this.saveStats();

        // Check achievements
        if (typeof achievementManager !== 'undefined') {
            const newUnlocks = await achievementManager.checkAchievements(this.stats);
            console.log(`Checked achievements: ${newUnlocks.length} new unlocks`);
        }

        // Update UI
        this.updateStatsDisplay();
    }

    isEarlyTrade(tradeTime) {
        const date = new Date(tradeTime);
        const hours = date.getHours();
        const minutes = date.getMinutes();

        // Market opens at 9:15, early trade is before 9:30
        if (hours === 9 && minutes >= 15 && minutes <= 30) {
            return true;
        }

        return false;
    }

    async onStrategyCreated(strategy) {
        console.log('Strategy created:', strategy);

        this.stats.strategiesCreated++;
        this.stats.strategiesActive++;

        // Save stats
        this.saveStats();

        // Check achievements
        if (typeof achievementManager !== 'undefined') {
            await achievementManager.checkAchievements(this.stats);
        }

        // Update UI
        this.updateStatsDisplay();
    }

    async onBacktestCompleted(backtest) {
        console.log('Backtest completed:', backtest);

        this.stats.backtests++;

        // Check if this is an optimization (improved win rate)
        if (backtest.previousWinRate && backtest.winRate) {
            const improvement = backtest.winRate - backtest.previousWinRate;
            if (improvement >= 10) {
                this.stats.strategyOptimizations++;
            }
        }

        // Save stats
        this.saveStats();

        // Check achievements
        if (typeof achievementManager !== 'undefined') {
            await achievementManager.checkAchievements(this.stats);
        }

        // Update UI
        this.updateStatsDisplay();
    }

    checkCelebrations(trade) {
        // First profit
        if (this.stats.profitableTrades === 1) {
            this.celebrate('first_profit', { amount: trade.pnl });
        }

        // Profit milestones
        const milestones = [1000, 5000, 10000, 25000, 50000, 100000];
        milestones.forEach(milestone => {
            const previousProfit = this.stats.totalProfit - trade.pnl;
            if (previousProfit < milestone && this.stats.totalProfit >= milestone) {
                this.celebrate(`milestone_${milestone}`, { amount: this.stats.totalProfit });
            }
        });

        // Win streaks
        if (this.stats.currentWinStreak === 5) {
            this.celebrate('win_streak_5', { count: 5 });
        }

        if (this.stats.currentWinStreak === 10) {
            this.celebrate('win_streak_10', { count: 10 });
        }

        // Personal best
        if (trade.pnl > (this.stats.bestTrade || 0)) {
            this.stats.bestTrade = trade.pnl;
            this.celebrate('personal_best', { amount: trade.pnl });
        }
    }

    celebrate(type, data) {
        console.log(`🎉 Celebration: ${type}`, data);

        // Trigger celebration if celebration system is loaded
        if (typeof celebrate !== 'undefined') {
            celebrate(type, data);
        }
    }

    updateDailyStats(date = new Date()) {
        // This would be called at end of trading day
        const todayPnl = this.getDailyPnL(date);

        // Check for perfect day (no losses)
        if (todayPnl > 0 && this.getDailyLosses(date) === 0) {
            this.stats.perfectDays++;
        }

        // Update consecutive profit days
        if (todayPnl > 0) {
            this.stats.consecutiveProfitDays++;

            if (this.stats.consecutiveProfitDays > this.stats.longestProfitDayStreak) {
                this.stats.longestProfitDayStreak = this.stats.consecutiveProfitDays;
            }
        } else {
            this.stats.consecutiveProfitDays = 0;
        }

        // Check for comeback (was down -5%, ended positive)
        const dailyDrawdown = this.getDailyDrawdown(date);
        if (dailyDrawdown <= -5 && todayPnl > 0) {
            this.stats.comebacks++;
        }

        this.saveStats();
    }

    getDailyPnL(date) {
        // This would fetch from actual trade data
        // For now, return mock data
        return 0;
    }

    getDailyLosses(date) {
        // This would fetch from actual trade data
        // For now, return mock data
        return 0;
    }

    getDailyDrawdown(date) {
        // This would fetch from actual trade data
        // For now, return mock data
        return 0;
    }

    markConfigComplete() {
        if (!this.stats.configComplete) {
            this.stats.configComplete = true;
            this.saveStats();

            if (typeof achievementManager !== 'undefined') {
                achievementManager.checkAchievements(this.stats);
            }
        }
    }

    getStats() {
        return { ...this.stats };
    }

    updateStatsDisplay() {
        // Update any displayed stats in the UI
        const event = new CustomEvent('statsUpdated', {
            detail: this.getStats()
        });
        window.dispatchEvent(event);
    }

    // Manual trigger for testing
    simulateTrade(pnl) {
        const trade = {
            pnl: pnl,
            time: new Date().toISOString(),
            exitReason: pnl < 0 ? 'stop_loss' : 'target',
            potentialLoss: pnl < 0 ? Math.abs(pnl) * 1.5 : null,
            maxDrawdown: Math.random() * 5
        };

        this.onTradeExecuted(trade);
        Toast.info(`Simulated trade: ₹${pnl.toFixed(2)}`);
    }

    // Reset stats (for testing)
    reset() {
        if (confirm('Are you sure you want to reset all stats? This cannot be undone.')) {
            localStorage.removeItem('tradingStats');
            this.stats = this.loadStats();
            this.updateStatsDisplay();
            Toast.info('Stats reset');
        }
    }
}

// Initialize global stats tracker
const statsTracker = new StatsTracker();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StatsTracker;
}

// Helper functions to trigger events from trading engine

/**
 * Call this when a trade is executed
 * @param {Object} trade - Trade details { pnl, time, symbol, exitReason, etc }
 */
function notifyTradeExecuted(trade) {
    window.dispatchEvent(new CustomEvent('tradeExecuted', { detail: trade }));
}

/**
 * Call this when a strategy is created
 * @param {Object} strategy - Strategy details { id, name, type, etc }
 */
function notifyStrategyCreated(strategy) {
    window.dispatchEvent(new CustomEvent('strategyCreated', { detail: strategy }));
}

/**
 * Call this when a backtest completes
 * @param {Object} backtest - Backtest results { winRate, previousWinRate, etc }
 */
function notifyBacktestCompleted(backtest) {
    window.dispatchEvent(new CustomEvent('backtestCompleted', { detail: backtest }));
}
