# Product Requirements Document (PRD)
## XCoin Scalping Bot - Pattern Recognition & Technical Analysis (v5.0)

**Version:** 5.0 (Pattern Recognition Update)  
**Last Updated:** October 21, 2025  
**Focus:** Candlestick Patterns, Chart Patterns, Technical Analysis Integration  
**Design Philosophy:** "Recognize patterns, trade with confidence"

---

## 1. Executive Summary

### 1.1 Vision Statement
Integrate comprehensive **pattern recognition capabilities** into XCoin, enabling traders to identify 50+ candlestick patterns, 15+ chart patterns, and combine them with 40+ technical indicators for intelligent, automated trading decisions.

### 1.2 Core Objectives
1. **Candlestick Pattern Recognition** - Detect 50+ patterns (engulfing, hammer, doji, etc.)
2. **Chart Pattern Recognition** - Identify 15+ formations (head & shoulders, flags, triangles)
3. **Technical Indicators** - Implement 40+ indicators (RSI, MACD, Bollinger Bands, etc.)
4. **Pattern-Based Strategies** - Auto-generate strategies from pattern combinations
5. **Real-Time Detection** - Scan live market data for patterns as they form
6. **Open-Source Integration** - Leverage proven libraries (TA-Lib, PatternPy, chart_patterns)

### 1.3 Success Metrics
- **Pattern Detection Accuracy:** >85% for candlestick patterns, >75% for chart patterns
- **Detection Latency:** <100ms for real-time pattern recognition
- **Strategy Performance:** Pattern-based strategies outperform baseline by >15%
- **User Adoption:** 70%+ of users enable pattern-based features
- **Library Integration:** 3+ open-source libraries successfully integrated

---

## 2. Candlestick Pattern Recognition System

### 2.1 Pattern Catalog (50+ Patterns)

**Based on video: "The Only Candlestick Pattern Trading Video You'll Ever Need"**

#### 2.1.1 Reversal Patterns (Bullish)
1. **Hammer** - Small body, long lower wick at bottom of downtrend
2. **Inverted Hammer** - Small body, long upper wick at bottom of downtrend
3. **Bullish Engulfing** - Green candle engulfs previous red candle
4. **Piercing Pattern** - Green candle closes above midpoint of previous red candle
5. **Morning Star** - 3-candle pattern (red → small → strong green)
6. **Three White Soldiers** - 3 consecutive strong green candles

#### 2.1.2 Reversal Patterns (Bearish)
1. **Shooting Star** - Small body, long upper wick at top of uptrend
2. **Hanging Man** - Small body, long lower wick at top of uptrend
3. **Bearish Engulfing** - Red candle engulfs previous green candle
4. **Dark Cloud Cover** - Red candle closes below midpoint of previous green candle
5. **Evening Star** - 3-candle pattern (green → small → strong red)
6. **Three Black Crows** - 3 consecutive strong red candles

#### 2.1.3 Continuation Patterns
1. **Bullish/Bearish Momentum Candles** - Large body, minimal wicks, continues trend
2. **Rising Three Methods** - Uptrend → 3 small pullback candles → continuation
3. **Falling Three Methods** - Downtrend → 3 small pullback candles → continuation
4. **Bull/Bear Flags** - Strong move → tight consolidation → breakout
5. **Runaway Gaps** - Gap in direction of trend signals strong momentum

#### 2.1.4 Indecision Patterns
1. **Doji** - Open = Close (4 types: classic, long-legged, dragonfly, gravestone)
2. **Spinning Top** - Small body with equal upper/lower wicks
3. **Harami** - Small candle inside previous candle's body

### 2.2 Technical Implementation Using TA-Lib

**TA-Lib Integration** (Most Popular Library)[277]

```python
# Install TA-Lib
# pip install TA-Lib

import talib
import pandas as pd
import numpy as np

class CandlestickPatternDetector:
    """
    Detect 50+ candlestick patterns using TA-Lib
    """
    
    def __init__(self, ohlc_data):
        """
        Initialize with OHLC data
        
        Args:
            ohlc_data (pd.DataFrame): Must have columns: open, high, low, close
        """
        self.df = ohlc_data
        self.open = ohlc_data['open'].values
        self.high = ohlc_data['high'].values
        self.low = ohlc_data['low'].values
        self.close = ohlc_data['close'].values
        
    def detect_all_patterns(self):
        """
        Detect all available candlestick patterns
        
        Returns:
            dict: Pattern name → array of detection signals (0, 100, -100)
        """
        patterns = {}
        
        # Bullish Reversal Patterns
        patterns['hammer'] = talib.CDLHAMMER(self.open, self.high, self.low, self.close)
        patterns['inverted_hammer'] = talib.CDLINVERTEDHAMMER(self.open, self.high, self.low, self.close)
        patterns['bullish_engulfing'] = talib.CDLENGULFING(self.open, self.high, self.low, self.close)
        patterns['piercing'] = talib.CDLPIERCING(self.open, self.high, self.low, self.close)
        patterns['morning_star'] = talib.CDLMORNINGSTAR(self.open, self.high, self.low, self.close)
        patterns['three_white_soldiers'] = talib.CDL3WHITESOLDIERS(self.open, self.high, self.low, self.close)
        
        # Bearish Reversal Patterns
        patterns['shooting_star'] = talib.CDLSHOOTINGSTAR(self.open, self.high, self.low, self.close)
        patterns['hanging_man'] = talib.CDLHANGINGMAN(self.open, self.high, self.low, self.close)
        patterns['bearish_engulfing'] = talib.CDLENGULFING(self.open, self.high, self.low, self.close)
        patterns['dark_cloud_cover'] = talib.CDLDARKCLOUDCOVER(self.open, self.high, self.low, self.close)
        patterns['evening_star'] = talib.CDLEVENINGSTAR(self.open, self.high, self.low, self.close)
        patterns['three_black_crows'] = talib.CDL3BLACKCROWS(self.open, self.high, self.low, self.close)
        
        # Doji Patterns
        patterns['doji'] = talib.CDLDOJI(self.open, self.high, self.low, self.close)
        patterns['dragonfly_doji'] = talib.CDLDRAGONFLYDOJI(self.open, self.high, self.low, self.close)
        patterns['gravestone_doji'] = talib.CDLGRAVESTONEDOJI(self.open, self.high, self.low, self.close)
        patterns['long_legged_doji'] = talib.CDLLONGLEGGEDDOJI(self.open, self.high, self.low, self.close)
        
        # Continuation Patterns
        patterns['rising_three'] = talib.CDLRISEFALL3METHODS(self.open, self.high, self.low, self.close)
        patterns['falling_three'] = talib.CDLRISEFALL3METHODS(self.open, self.high, self.low, self.close)
        
        # Additional Patterns (TA-Lib supports 61 total patterns)
        patterns['harami'] = talib.CDLHARAMI(self.open, self.high, self.low, self.close)
        patterns['harami_cross'] = talib.CDLHARAMICROSS(self.open, self.high, self.low, self.close)
        patterns['spinning_top'] = talib.CDLSPINNINGTOP(self.open, self.high, self.low, self.close)
        patterns['marubozu'] = talib.CDLMARUBOZU(self.open, self.high, self.low, self.close)
        patterns['belt_hold'] = talib.CDLBELTHOLD(self.open, self.high, self.low, self.close)
        patterns['kicking'] = talib.CDLKICKING(self.open, self.high, self.low, self.close)
        patterns['three_inside'] = talib.CDL3INSIDE(self.open, self.high, self.low, self.close)
        patterns['three_outside'] = talib.CDL3OUTSIDE(self.open, self.high, self.low, self.close)
        
        return patterns
    
    def get_active_patterns(self, index=-1):
        """
        Get all patterns active at a specific candle
        
        Args:
            index (int): Candle index (-1 = latest)
            
        Returns:
            list: [{'name': 'hammer', 'signal': 100, 'type': 'bullish_reversal'}, ...]
        """
        all_patterns = self.detect_all_patterns()
        active = []
        
        for pattern_name, signals in all_patterns.items():
            signal = signals[index]
            if signal != 0:
                active.append({
                    'name': pattern_name,
                    'signal': int(signal),  # 100 = bullish, -100 = bearish
                    'type': self._get_pattern_type(pattern_name, signal),
                    'confidence': self._calculate_confidence(pattern_name, index),
                    'description': self._get_pattern_description(pattern_name)
                })
        
        return active
    
    def _get_pattern_type(self, pattern_name, signal):
        """Classify pattern type"""
        bullish_reversal = ['hammer', 'inverted_hammer', 'bullish_engulfing', 
                           'piercing', 'morning_star', 'three_white_soldiers']
        bearish_reversal = ['shooting_star', 'hanging_man', 'bearish_engulfing',
                           'dark_cloud_cover', 'evening_star', 'three_black_crows']
        continuation = ['rising_three', 'falling_three', 'marubozu']
        indecision = ['doji', 'dragonfly_doji', 'gravestone_doji', 'spinning_top']
        
        if pattern_name in bullish_reversal and signal > 0:
            return 'bullish_reversal'
        elif pattern_name in bearish_reversal and signal < 0:
            return 'bearish_reversal'
        elif pattern_name in continuation:
            return 'continuation'
        elif pattern_name in indecision:
            return 'indecision'
        else:
            return 'other'
    
    def _calculate_confidence(self, pattern_name, index):
        """
        Calculate confidence score (0-100) for pattern
        
        Considers:
        - Pattern strength (body/wick ratio)
        - Volume confirmation
        - Support/resistance proximity
        - Trend context
        """
        confidence = 50  # Base confidence
        
        # Check candle strength (body size)
        candle_range = self.high[index] - self.low[index]
        candle_body = abs(self.close[index] - self.open[index])
        body_ratio = candle_body / candle_range if candle_range > 0 else 0
        
        if body_ratio > 0.7:  # Strong candle
            confidence += 15
        elif body_ratio < 0.3:  # Weak candle
            confidence -= 10
        
        # Check trend context (using 20-period SMA)
        if index >= 20:
            sma_20 = np.mean(self.close[index-20:index])
            if self.close[index] > sma_20:  # Uptrend
                # Bullish patterns in uptrend = higher confidence
                if 'bullish' in self._get_pattern_type(pattern_name, 100):
                    confidence += 10
            else:  # Downtrend
                # Bearish patterns in downtrend = higher confidence
                if 'bearish' in self._get_pattern_type(pattern_name, -100):
                    confidence += 10
        
        return min(100, max(0, confidence))
    
    def _get_pattern_description(self, pattern_name):
        """Get human-readable description"""
        descriptions = {
            'hammer': 'Bullish reversal - small body with long lower wick at downtrend bottom',
            'shooting_star': 'Bearish reversal - small body with long upper wick at uptrend top',
            'bullish_engulfing': 'Bullish reversal - large green candle engulfs previous red candle',
            'doji': 'Indecision - open equals close, signals potential reversal',
            # Add all 50+ pattern descriptions
        }
        return descriptions.get(pattern_name, 'No description available')

# Usage Example
if __name__ == '__main__':
    # Load OHLC data
    df = pd.read_csv('btc_usdt_5m.csv')
    
    # Initialize detector
    detector = CandlestickPatternDetector(df)
    
    # Get all active patterns on latest candle
    active_patterns = detector.get_active_patterns(index=-1)
    
    print(f"Detected {len(active_patterns)} patterns:")
    for pattern in active_patterns:
        print(f"  {pattern['name']}: {pattern['type']} (confidence: {pattern['confidence']}%)")
        print(f"    {pattern['description']}")
```

### 2.3 Real-Time Pattern Detection

```javascript
// Real-time pattern scanner
class RealTimePatternScanner {
  constructor(strategyConfig) {
    this.config = strategyConfig;
    this.detector = new CandlestickPatternDetector();
    this.lastPatterns = new Map();
  }

  async onNewCandle(candle) {
    // Get latest 500 candles for context
    const ohlcData = await this.fetchRecentCandles(500);
    
    // Detect patterns
    const patterns = this.detector.detect_all_patterns(ohlcData);
    const activePatterns = this.detector.get_active_patterns(-1);
    
    // Check for new patterns
    const newPatterns = this.getNewPatterns(activePatterns);
    
    // Trigger strategy if pattern matches
    for (const pattern of newPatterns) {
      if (this.matchesStrategy(pattern)) {
        await this.executeStrategyEntry(pattern);
        
        // Send notification
        this.notifyUser({
          title: `${pattern.name} detected!`,
          message: `${pattern.type} pattern on ${this.config.symbol}`,
          confidence: pattern.confidence,
          action: 'ENTRY_SIGNAL'
        });
      }
    }
  }

  getNewPatterns(currentPatterns) {
    const newPatterns = [];
    
    for (const pattern of currentPatterns) {
      const key = `${pattern.name}_${pattern.signal}`;
      if (!this.lastPatterns.has(key)) {
        newPatterns.push(pattern);
        this.lastPatterns.set(key, Date.now());
      }
    }
    
    // Cleanup old patterns (> 1 hour)
    const oneHourAgo = Date.now() - 3600000;
    for (const [key, timestamp] of this.lastPatterns.entries()) {
      if (timestamp < oneHourAgo) {
        this.lastPatterns.delete(key);
      }
    }
    
    return newPatterns;
  }

  matchesStrategy(pattern) {
    // Check if pattern matches strategy configuration
    const allowedPatterns = this.config.patterns || [];
    const minConfidence = this.config.minConfidence || 60;
    
    return (
      allowedPatterns.includes(pattern.name) &&
      pattern.confidence >= minConfidence
    );
  }
}
```

---

## 3. Chart Pattern Recognition System

### 3.1 Pattern Catalog (15+ Patterns)

**Based on video: "The ONLY Chart Patterns Trading Guide You'll EVER NEED"**

#### 3.1.1 Reversal Patterns
1. **Double Bottom** - 2 lows at same level, breakout above middle high
2. **Double Top** - 2 highs at same level, breakdown below middle low
3. **Head and Shoulders** - Left shoulder → Head → Right shoulder → breakdown
4. **Inverse Head and Shoulders** - Bullish version of H&S
5. **Falling Wedge** - Converging trendlines, upward breakout (bullish reversal)
6. **Rising Wedge** - Converging trendlines, downward breakdown (bearish reversal)

#### 3.1.2 Continuation Patterns
1. **Bull Flag** - Strong uptrend → tight consolidation → upward breakout
2. **Bear Flag** - Strong downtrend → tight consolidation → downward breakdown
3. **Ascending Triangle** - Flat top resistance, rising support, bullish breakout
4. **Descending Triangle** - Flat bottom support, falling resistance, bearish breakdown
5. **Symmetrical Triangle** - Converging trendlines, breakout either direction
6. **Pennant** - Small symmetrical triangle after strong move
7. **Cup and Handle** - Rounded bottom (cup) + small pullback (handle)
8. **Reverse Cup and Handle** - Bearish version

#### 3.1.3 Uncertain Patterns
1. **Broadening Range** - Expanding volatility, unpredictable direction
2. **Rectangle** - Horizontal consolidation, can break either way

### 3.2 Technical Implementation

**Using chart_patterns Library**[262]

```python
# Install: git clone https://github.com/zeta-zetra/chart_patterns
# pip install -r requirements.txt

import pandas as pd
from chart_patterns.doubles import find_doubles_pattern
from chart_patterns.head_and_shoulders import find_head_and_shoulders
from chart_patterns.triangles import find_triangles
from chart_patterns.flags import find_flags
from chart_patterns.cup_and_handle import find_cup_and_handle

class ChartPatternDetector:
    """
    Detect 15+ chart patterns using multiple detection methods
    """
    
    def __init__(self, ohlc_data, window=100):
        """
        Args:
            ohlc_data (pd.DataFrame): OHLC data
            window (int): Lookback window for pattern detection
        """
        self.df = ohlc_data
        self.window = window
        
    def detect_all_patterns(self):
        """
        Detect all chart patterns
        
        Returns:
            list: [{'type': 'double_bottom', 'start': 150, 'end': 200, ...}, ...]
        """
        patterns = []
        
        # Double Tops/Bottoms
        try:
            df_doubles_bottom = find_doubles_pattern(self.df.copy(), double='bottoms')
            if 'double_bottom' in df_doubles_bottom.columns:
                for idx, row in df_doubles_bottom[df_doubles_bottom['double_bottom'] == 1].iterrows():
                    patterns.append({
                        'type': 'double_bottom',
                        'direction': 'bullish',
                        'pattern_class': 'reversal',
                        'index': idx,
                        'confidence': self._calculate_pattern_confidence('double_bottom', idx)
                    })
        except Exception as e:
            print(f"Error detecting double bottoms: {e}")
        
        try:
            df_doubles_top = find_doubles_pattern(self.df.copy(), double='tops')
            if 'double_top' in df_doubles_top.columns:
                for idx, row in df_doubles_top[df_doubles_top['double_top'] == 1].iterrows():
                    patterns.append({
                        'type': 'double_top',
                        'direction': 'bearish',
                        'pattern_class': 'reversal',
                        'index': idx,
                        'confidence': self._calculate_pattern_confidence('double_top', idx)
                    })
        except Exception as e:
            print(f"Error detecting double tops: {e}")
        
        # Head and Shoulders
        try:
            df_hs = find_head_and_shoulders(self.df.copy(), type='bearish')
            # Process results...
        except Exception as e:
            print(f"Error detecting H&S: {e}")
        
        # Triangles
        try:
            df_triangles = find_triangles(self.df.copy())
            # Process results...
        except Exception as e:
            print(f"Error detecting triangles: {e}")
        
        # Flags
        try:
            df_flags = find_flags(self.df.copy())
            # Process results...
        except Exception as e:
            print(f"Error detecting flags: {e}")
        
        # Cup and Handle
        try:
            df_cup = find_cup_and_handle(self.df.copy())
            # Process results...
        except Exception as e:
            print(f"Error detecting cup and handle: {e}")
        
        return patterns
    
    def _calculate_pattern_confidence(self, pattern_type, index):
        """
        Calculate confidence score for chart pattern
        
        Factors:
        - Pattern clarity (how well-defined)
        - Volume confirmation
        - Breakout strength
        - Risk/reward ratio
        """
        confidence = 60  # Base
        
        # Check volume at breakout
        if index < len(self.df) - 1:
            avg_volume = self.df['volume'].iloc[max(0, index-20):index].mean()
            breakout_volume = self.df['volume'].iloc[index]
            
            if breakout_volume > avg_volume * 1.5:  # High volume breakout
                confidence += 15
            elif breakout_volume < avg_volume * 0.8:  # Low volume breakout
                confidence -= 10
        
        # Check for clean pattern formation (low volatility during pattern)
        if index >= 20:
            pattern_volatility = self.df['high'].iloc[index-20:index].std()
            overall_volatility = self.df['high'].std()
            
            if pattern_volatility < overall_volatility * 0.8:  # Cleaner pattern
                confidence += 10
        
        return min(100, max(0, confidence))
    
    def detect_specific_pattern(self, pattern_type):
        """
        Detect only a specific pattern type
        
        Args:
            pattern_type (str): 'double_bottom', 'head_and_shoulders', etc.
        """
        if pattern_type == 'double_bottom':
            return find_doubles_pattern(self.df, double='bottoms')
        elif pattern_type == 'double_top':
            return find_doubles_pattern(self.df, double='tops')
        # Add all other patterns...
    
    def get_pattern_entry_exit(self, pattern):
        """
        Calculate entry, stop-loss, and take-profit for pattern
        
        Args:
            pattern (dict): Pattern info from detect_all_patterns()
            
        Returns:
            dict: {'entry': 50000, 'stop_loss': 49000, 'take_profit': 52000}
        """
        pattern_type = pattern['type']
        index = pattern['index']
        
        if pattern_type == 'double_bottom':
            # Entry: breakout above neckline
            neckline = self.df['high'].iloc[index-10:index].max()
            entry = neckline * 1.001  # 0.1% above
            
            # Stop-loss: below second bottom
            stop_loss = self.df['low'].iloc[index-5:index].min() * 0.999
            
            # Take-profit: 2:1 risk-reward
            risk = entry - stop_loss
            take_profit = entry + (risk * 2)
            
            return {
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward_ratio': 2.0
            }
        
        elif pattern_type == 'head_and_shoulders':
            # Entry: breakdown below neckline
            neckline = self.df['low'].iloc[index-10:index].min()
            entry = neckline * 0.999  # 0.1% below
            
            # Stop-loss: above right shoulder
            stop_loss = self.df['high'].iloc[index-5:index].max() * 1.001
            
            # Take-profit: height of head projected down
            head_height = self.df['high'].iloc[index-15:index-5].max() - neckline
            take_profit = entry - head_height
            
            return {
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward_ratio': head_height / (stop_loss - entry)
            }
        
        # Add all other patterns...
```

### 3.3 Custom Pattern Recognition (PatternPy)[268]

```python
# Alternative library with more flexibility
# git clone https://github.com/keithorange/PatternPy

from patternpy.tradingpatterns import (
    head_and_shoulders,
    multiple_tops_bottoms,
    horizontal_sr,  # Support/Resistance
    trendline
)

class CustomPatternDetector:
    """
    Custom pattern detection with fine-tuned parameters
    """
    
    def __init__(self, ohlc_data):
        self.df = ohlc_data
    
    def find_head_and_shoulders(self, window=50):
        """
        Find H&S pattern with adjustable sensitivity
        
        Args:
            window (int): Lookback window (higher = less sensitive)
        """
        return head_and_shoulders(
            self.df,
            window=window,
            order=5  # Peak prominence
        )
    
    def find_support_resistance(self, window=100, num_levels=5):
        """
        Identify horizontal support/resistance levels
        
        Args:
            window (int): Lookback period
            num_levels (int): Number of S/R levels to find
        """
        return horizontal_sr(
            self.df,
            window=window,
            num_touches=3,  # Minimum touches to confirm S/R
            tolerance=0.002  # 0.2% price tolerance
        )
    
    def find_trendlines(self, window=50):
        """
        Detect ascending/descending trendlines
        """
        return trendline(
            self.df,
            window=window,
            min_touches=3
        )
```

---

## 4. Technical Indicators Integration

### 4.1 Indicator Catalog (40+ Indicators)

**Using TA Library (bukosabino/ta)**[272]

```python
# pip install ta

import pandas as pd
from ta import add_all_ta_features
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, MFIIndicator

class TechnicalIndicators:
    """
    Comprehensive technical indicators using TA library
    """
    
    def __init__(self, ohlc_data):
        """
        Args:
            ohlc_data (pd.DataFrame): Must have open, high, low, close, volume
        """
        self.df = ohlc_data.copy()
        
    def add_all_indicators(self):
        """
        Add ALL 40+ indicators at once
        
        Returns:
            pd.DataFrame: Original data with 100+ new indicator columns
        """
        self.df = add_all_ta_features(
            self.df,
            open="open",
            high="high",
            low="low",
            close="close",
            volume="volume",
            fillna=True
        )
        return self.df
    
    def add_trend_indicators(self):
        """
        Add trend-following indicators
        """
        # Moving Averages
        self.df['ema_9'] = EMAIndicator(self.df['close'], window=9).ema_indicator()
        self.df['ema_21'] = EMAIndicator(self.df['close'], window=21).ema_indicator()
        self.df['ema_50'] = EMAIndicator(self.df['close'], window=50).ema_indicator()
        self.df['ema_200'] = EMAIndicator(self.df['close'], window=200).ema_indicator()
        
        # MACD
        macd = MACD(self.df['close'])
        self.df['macd'] = macd.macd()
        self.df['macd_signal'] = macd.macd_signal()
        self.df['macd_diff'] = macd.macd_diff()
        
        # ADX (Trend Strength)
        adx = ADXIndicator(self.df['high'], self.df['low'], self.df['close'])
        self.df['adx'] = adx.adx()
        self.df['adx_pos'] = adx.adx_pos()
        self.df['adx_neg'] = adx.adx_neg()
        
        return self.df
    
    def add_momentum_indicators(self):
        """
        Add momentum oscillators
        """
        # RSI
        rsi = RSIIndicator(self.df['close'], window=14)
        self.df['rsi'] = rsi.rsi()
        
        # Stochastic
        stoch = StochasticOscillator(self.df['high'], self.df['low'], self.df['close'])
        self.df['stoch_k'] = stoch.stoch()
        self.df['stoch_d'] = stoch.stoch_signal()
        
        return self.df
    
    def add_volatility_indicators(self):
        """
        Add volatility indicators
        """
        # Bollinger Bands
        bb = BollingerBands(self.df['close'])
        self.df['bb_upper'] = bb.bollinger_hband()
        self.df['bb_middle'] = bb.bollinger_mavg()
        self.df['bb_lower'] = bb.bollinger_lband()
        self.df['bb_width'] = bb.bollinger_wband()
        
        # ATR
        atr = AverageTrueRange(self.df['high'], self.df['low'], self.df['close'])
        self.df['atr'] = atr.average_true_range()
        
        return self.df
    
    def add_volume_indicators(self):
        """
        Add volume-based indicators
        """
        # OBV
        obv = OnBalanceVolumeIndicator(self.df['close'], self.df['volume'])
        self.df['obv'] = obv.on_balance_volume()
        
        # MFI (Money Flow Index)
        mfi = MFIIndicator(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            self.df['volume']
        )
        self.df['mfi'] = mfi.money_flow_index()
        
        return self.df
    
    def get_indicator_signals(self, index=-1):
        """
        Get buy/sell signals from all indicators
        
        Args:
            index (int): Candle index (-1 = latest)
            
        Returns:
            dict: {'rsi': 'oversold', 'macd': 'bullish_cross', ...}
        """
        signals = {}
        
        # RSI Signals
        rsi_value = self.df['rsi'].iloc[index]
        if rsi_value < 30:
            signals['rsi'] = 'oversold_buy'
        elif rsi_value > 70:
            signals['rsi'] = 'overbought_sell'
        else:
            signals['rsi'] = 'neutral'
        
        # MACD Signals
        macd_current = self.df['macd_diff'].iloc[index]
        macd_previous = self.df['macd_diff'].iloc[index-1]
        
        if macd_previous < 0 and macd_current > 0:
            signals['macd'] = 'bullish_cross_buy'
        elif macd_previous > 0 and macd_current < 0:
            signals['macd'] = 'bearish_cross_sell'
        else:
            signals['macd'] = 'neutral'
        
        # EMA Signals (Golden/Death Cross)
        ema_50 = self.df['ema_50'].iloc[index]
        ema_200 = self.df['ema_200'].iloc[index]
        ema_50_prev = self.df['ema_50'].iloc[index-1]
        ema_200_prev = self.df['ema_200'].iloc[index-1]
        
        if ema_50_prev < ema_200_prev and ema_50 > ema_200:
            signals['ema_cross'] = 'golden_cross_buy'
        elif ema_50_prev > ema_200_prev and ema_50 < ema_200:
            signals['ema_cross'] = 'death_cross_sell'
        else:
            signals['ema_cross'] = 'neutral'
        
        # Bollinger Bands Signals
        close = self.df['close'].iloc[index]
        bb_upper = self.df['bb_upper'].iloc[index]
        bb_lower = self.df['bb_lower'].iloc[index]
        
        if close < bb_lower:
            signals['bollinger'] = 'oversold_buy'
        elif close > bb_upper:
            signals['bollinger'] = 'overbought_sell'
        else:
            signals['bollinger'] = 'neutral'
        
        # ADX Trend Strength
        adx_value = self.df['adx'].iloc[index]
        if adx_value > 25:
            signals['adx'] = 'strong_trend'
        else:
            signals['adx'] = 'weak_trend_consolidation'
        
        return signals
```

---

## 5. Pattern-Based Strategy Engine

### 5.1 Strategy Builder

```python
class PatternBasedStrategy:
    """
    Create strategies based on pattern + indicator combinations
    """
    
    def __init__(self, name, config):
        """
        Args:
            name (str): Strategy name
            config (dict): Strategy configuration
                {
                    'candlestick_patterns': ['hammer', 'bullish_engulfing'],
                    'chart_patterns': ['double_bottom', 'inverse_h_and_s'],
                    'indicators': {
                        'rsi': {'min': 30, 'max': 70},
                        'macd': 'bullish_cross',
                        'ema_cross': 'golden_cross'
                    },
                    'require_all': False,  # True = all conditions must match
                    'min_confidence': 70
                }
        """
        self.name = name
        self.config = config
        
        # Initialize detectors
        self.candlestick_detector = None
        self.chart_pattern_detector = None
        self.indicators = None
    
    def evaluate(self, ohlc_data):
        """
        Evaluate if strategy conditions are met
        
        Returns:
            dict: {
                'signal': 'BUY'/'SELL'/'NEUTRAL',
                'confidence': 75,
                'reasons': ['Hammer pattern detected', 'RSI oversold', ...]
            }
        """
        # Initialize detectors with latest data
        self.candlestick_detector = CandlestickPatternDetector(ohlc_data)
        self.chart_pattern_detector = ChartPatternDetector(ohlc_data)
        self.indicators = TechnicalIndicators(ohlc_data)
        self.indicators.add_all_indicators()
        
        # Get current signals
        candlestick_patterns = self.candlestick_detector.get_active_patterns()
        chart_patterns = self.chart_pattern_detector.detect_all_patterns()
        indicator_signals = self.indicators.get_indicator_signals()
        
        # Evaluate conditions
        conditions_met = []
        total_confidence = 0
        signal_type = 'NEUTRAL'
        
        # Check candlestick patterns
        for pattern in candlestick_patterns:
            if pattern['name'] in self.config.get('candlestick_patterns', []):
                conditions_met.append(f"{pattern['name']} detected (conf: {pattern['confidence']}%)")
                total_confidence += pattern['confidence']
                
                if pattern['type'] == 'bullish_reversal':
                    signal_type = 'BUY'
                elif pattern['type'] == 'bearish_reversal':
                    signal_type = 'SELL'
        
        # Check chart patterns
        for pattern in chart_patterns:
            if pattern['type'] in self.config.get('chart_patterns', []):
                conditions_met.append(f"{pattern['type']} detected (conf: {pattern['confidence']}%)")
                total_confidence += pattern['confidence']
                
                if pattern['direction'] == 'bullish':
                    signal_type = 'BUY'
                elif pattern['direction'] == 'bearish':
                    signal_type = 'SELL'
        
        # Check indicators
        indicator_config = self.config.get('indicators', {})
        
        for indicator_name, condition in indicator_config.items():
            indicator_signal = indicator_signals.get(indicator_name)
            
            if isinstance(condition, dict):  # Range condition (e.g., RSI)
                if indicator_name == 'rsi':
                    rsi_value = self.indicators.df['rsi'].iloc[-1]
                    if rsi_value < condition['min']:
                        conditions_met.append(f"RSI oversold ({rsi_value:.1f})")
                        total_confidence += 70
                        signal_type = 'BUY'
                    elif rsi_value > condition['max']:
                        conditions_met.append(f"RSI overbought ({rsi_value:.1f})")
                        total_confidence += 70
                        signal_type = 'SELL'
            
            elif isinstance(condition, str):  # Specific signal condition
                if indicator_signal == condition:
                    conditions_met.append(f"{indicator_name}: {condition}")
                    total_confidence += 60
        
        # Calculate average confidence
        avg_confidence = total_confidence / len(conditions_met) if conditions_met else 0
        
        # Check if minimum conditions met
        require_all = self.config.get('require_all', False)
        min_confidence = self.config.get('min_confidence', 60)
        
        if require_all and len(conditions_met) < self._count_total_conditions():
            signal_type = 'NEUTRAL'
        
        if avg_confidence < min_confidence:
            signal_type = 'NEUTRAL'
        
        return {
            'signal': signal_type,
            'confidence': avg_confidence,
            'reasons': conditions_met,
            'patterns_detected': len(candlestick_patterns) + len(chart_patterns),
            'indicators_aligned': len([s for s in indicator_signals.values() if 'buy' in s or 'sell' in s])
        }
    
    def _count_total_conditions(self):
        """Count total conditions in strategy"""
        count = 0
        count += len(self.config.get('candlestick_patterns', []))
        count += len(self.config.get('chart_patterns', []))
        count += len(self.config.get('indicators', {}))
        return count

# Example Strategy Definitions
STRATEGY_TEMPLATES = {
    'hammer_rsi_reversal': {
        'name': 'Hammer + RSI Oversold Reversal',
        'candlestick_patterns': ['hammer', 'inverted_hammer'],
        'indicators': {
            'rsi': {'min': 20, 'max': 40},
            'macd': 'bullish_cross'
        },
        'require_all': False,
        'min_confidence': 65
    },
    
    'double_bottom_breakout': {
        'name': 'Double Bottom Breakout with Volume',
        'chart_patterns': ['double_bottom'],
        'indicators': {
            'ema_cross': 'golden_cross',
            'adx': 'strong_trend'
        },
        'require_all': False,
        'min_confidence': 70
    },
    
    'head_and_shoulders_reversal': {
        'name': 'H&S Reversal + Bearish Indicators',
        'chart_patterns': ['head_and_shoulders'],
        'candlestick_patterns': ['shooting_star', 'bearish_engulfing'],
        'indicators': {
            'rsi': {'min': 60, 'max': 100},
            'macd': 'bearish_cross'
        },
        'require_all': False,
        'min_confidence': 75
    }
}
```

---

## 6. UI Integration - Pattern Recognition Dashboard

### 6.1 Pattern Detection Widget

```jsx
// src/components/organisms/PatternDetectionWidget/PatternDetectionWidget.jsx
import { Brain, TrendingUp, Activity } from 'lucide-react';
import { GlassCard } from '@/components/atoms/GlassCard';

export const PatternDetectionWidget = ({ patterns, indicators }) => {
  const candlestickPatterns = patterns.filter(p => p.source === 'candlestick');
  const chartPatterns = patterns.filter(p => p.source === 'chart');
  
  return (
    <GlassCard variant="medium" blur="medium" elevation="lg" className="pattern-widget">
      <div className="pattern-widget__header">
        <h3>
          <Brain size={20} />
          Pattern Recognition
        </h3>
        <span className="pattern-widget__count">
          {patterns.length} patterns detected
        </span>
      </div>

      {/* Candlestick Patterns */}
      <div className="pattern-widget__section">
        <h4 className="pattern-widget__section-title">Candlestick Patterns</h4>
        {candlestickPatterns.length === 0 ? (
          <p className="pattern-widget__empty">No patterns detected</p>
        ) : (
          <div className="pattern-list">
            {candlestickPatterns.map((pattern, i) => (
              <div key={i} className={`pattern-item pattern-item--${pattern.type}`}>
                <div className="pattern-item__info">
                  <span className="pattern-item__name">{pattern.name}</span>
                  <span className="pattern-item__type">{pattern.type}</span>
                </div>
                <div className="pattern-item__confidence">
                  <div 
                    className="confidence-bar"
                    style={{ width: `${pattern.confidence}%` }}
                  />
                  <span>{pattern.confidence}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Chart Patterns */}
      <div className="pattern-widget__section">
        <h4 className="pattern-widget__section-title">Chart Patterns</h4>
        {chartPatterns.length === 0 ? (
          <p className="pattern-widget__empty">No patterns detected</p>
        ) : (
          <div className="pattern-list">
            {chartPatterns.map((pattern, i) => (
              <div key={i} className={`pattern-item pattern-item--${pattern.direction}`}>
                <div className="pattern-item__info">
                  <span className="pattern-item__name">{pattern.type}</span>
                  <span className="pattern-item__class">{pattern.pattern_class}</span>
                </div>
                <div className="pattern-item__confidence">
                  <div 
                    className="confidence-bar"
                    style={{ width: `${pattern.confidence}%` }}
                  />
                  <span>{pattern.confidence}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Indicator Signals */}
      <div className="pattern-widget__section">
        <h4 className="pattern-widget__section-title">Indicator Signals</h4>
        <div className="indicator-grid">
          {Object.entries(indicators).map(([name, signal]) => (
            <div key={name} className={`indicator-chip indicator-chip--${getSignalType(signal)}`}>
              <span className="indicator-chip__name">{name.toUpperCase()}</span>
              <span className="indicator-chip__signal">{signal}</span>
            </div>
          ))}
        </div>
      </div>
    </GlassCard>
  );
};

function getSignalType(signal) {
  if (signal.includes('buy') || signal.includes('bullish')) return 'bullish';
  if (signal.includes('sell') || signal.includes('bearish')) return 'bearish';
  return 'neutral';
}
```

```css
/* PatternDetectionWidget.module.css */
.pattern-widget {
  padding: 20px;
}

.pattern-widget__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.pattern-widget__header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.pattern-widget__count {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.pattern-widget__section {
  margin-bottom: 20px;
}

.pattern-widget__section:last-child {
  margin-bottom: 0;
}

.pattern-widget__section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.pattern-widget__empty {
  font-size: 13px;
  color: var(--color-text-tertiary);
  text-align: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
}

/* Pattern List */
.pattern-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pattern-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--glass-bg-light);
  border: 1px solid var(--glass-border-light);
  border-radius: 6px;
  transition: all 200ms;
}

.pattern-item:hover {
  background: var(--glass-bg-medium);
  border-color: var(--glass-border-accent);
}

.pattern-item--bullish_reversal,
.pattern-item--bullish {
  border-left: 3px solid var(--color-success);
}

.pattern-item--bearish_reversal,
.pattern-item--bearish {
  border-left: 3px solid var(--color-error);
}

.pattern-item--indecision,
.pattern-item--neutral {
  border-left: 3px solid var(--color-warning);
}

.pattern-item__info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pattern-item__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  text-transform: capitalize;
}

.pattern-item__type,
.pattern-item__class {
  font-size: 11px;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.pattern-item__confidence {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  min-width: 80px;
}

.confidence-bar {
  height: 4px;
  background: linear-gradient(90deg, var(--color-accent-primary), var(--color-accent-secondary));
  border-radius: 2px;
  transition: width 300ms ease-out;
}

.pattern-item__confidence span {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
}

/* Indicator Grid */
.indicator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
}

.indicator-chip {
  display: flex;
  flex-direction: column;
  padding: 8px 10px;
  background: var(--glass-bg-light);
  border: 1px solid var(--glass-border-light);
  border-radius: 6px;
  transition: all 200ms;
}

.indicator-chip:hover {
  background: var(--glass-bg-medium);
}

.indicator-chip--bullish {
  border-left: 3px solid var(--color-success);
}

.indicator-chip--bearish {
  border-left: 3px solid var(--color-error);
}

.indicator-chip--neutral {
  border-left: 3px solid var(--color-text-tertiary);
}

.indicator-chip__name {
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.indicator-chip__signal {
  font-size: 11px;
  color: var(--color-text-primary);
  text-transform: capitalize;
}
```

---

## 7. Implementation Roadmap

### **Phase 1: Candlestick Pattern Recognition (Weeks 1-2)**

**Week 1: TA-Lib Integration**
- [ ] Install and configure TA-Lib
- [ ] Implement CandlestickPatternDetector class
- [ ] Test all 50+ pattern detection functions
- [ ] Calculate confidence scores for each pattern
- [ ] Unit tests for pattern detection accuracy

**Week 2: Real-Time Detection**
- [ ] Build RealTimePatternScanner
- [ ] Integrate with existing market data feed
- [ ] Add pattern notifications system
- [ ] Create PatternDetectionWidget UI component
- [ ] Test pattern detection on live data

**Deliverables:**
- 50+ candlestick patterns detected in real-time
- Pattern confidence scoring (0-100)
- Live notifications when patterns form
- Visual pattern display in dashboard

---

### **Phase 2: Chart Pattern Recognition (Weeks 3-4)**

**Week 3: chart_patterns Library Integration**
- [ ] Clone and setup chart_patterns repo
- [ ] Implement ChartPatternDetector class
- [ ] Test double tops/bottoms, H&S, triangles
- [ ] Calculate pattern entry/exit points
- [ ] Generate pattern visualization overlays

**Week 4: Custom Pattern Detection**
- [ ] Integrate PatternPy library
- [ ] Add support/resistance detection
- [ ] Implement trendline identification
- [ ] Build pattern confidence scoring
- [ ] Create chart pattern UI cards

**Deliverables:**
- 15+ chart patterns detected
- Automatic entry/stop-loss/take-profit calculation
- Pattern overlay on charts
- Pattern-based trading signals

---

### **Phase 3: Technical Indicators (Weeks 5-6)**

**Week 5: TA Library Integration**
- [ ] Install bukosabino/ta library
- [ ] Implement TechnicalIndicators class
- [ ] Add all 40+ indicators (trend, momentum, volatility, volume)
- [ ] Create indicator signal detection
- [ ] Build indicator configuration UI

**Week 6: Indicator Visualization**
- [ ] Add indicators to chart overlays
- [ ] Create indicator panel (separate from main chart)
- [ ] Implement indicator customization (periods, thresholds)
- [ ] Add indicator alerts/notifications
- [ ] Build indicator backtesting

**Deliverables:**
- 40+ technical indicators available
- Customizable indicator parameters
- Indicator signals (buy/sell/neutral)
- Indicator-based alerts

---

### **Phase 4: Pattern-Based Strategies (Weeks 7-8)**

**Week 7: Strategy Builder**
- [ ] Implement PatternBasedStrategy class
- [ ] Create 10+ pre-built strategy templates
- [ ] Add strategy configuration UI
- [ ] Implement strategy backtesting with patterns
- [ ] Generate strategy performance reports

**Week 8: Strategy Deployment**
- [ ] Connect strategies to live trading engine
- [ ] Add pattern-triggered order execution
- [ ] Create strategy monitoring dashboard
- [ ] Implement strategy version control
- [ ] Add strategy comparison tools

**Deliverables:**
- Pattern-based strategy builder
- 10+ ready-to-use strategy templates
- Live pattern-triggered trading
- Strategy performance tracking

---

### **Phase 5: UI/UX & Polish (Weeks 9-10)**

**Week 9: Dashboard Integration**
- [ ] Integrate all pattern widgets into main dashboard
- [ ] Add pattern scanner page (scan all symbols)
- [ ] Create pattern education section (pattern library with examples)
- [ ] Build pattern alert preferences
- [ ] Implement pattern performance analytics

**Week 10: Testing & Optimization**
- [ ] Performance testing (pattern detection speed)
- [ ] Accuracy testing (false positive rate)
- [ ] User acceptance testing
- [ ] Documentation (pattern guide, API docs)
- [ ] Final bug fixes and polish

**Deliverables:**
- Fully integrated pattern recognition system
- Pattern scanner for multiple symbols
- Educational pattern library
- Comprehensive documentation

---

## 8. Open-Source Libraries Leveraged

### 8.1 Primary Libraries[261][262][264][266][267][268][272][276][277]

| Library | Purpose | GitHub | Stars | Language |
|---------|---------|--------|-------|----------|
| **TA-Lib** | 200+ indicators, candlestick patterns | https://github.com/mrjbq7/ta-lib | 9.3k | Python/C |
| **chart_patterns** | Chart pattern detection (H&S, flags, triangles) | https://github.com/zeta-zetra/chart_patterns | 100+ | Python |
| **PatternPy** | Custom pattern recognition (S/R, trendlines) | https://github.com/keithorange/PatternPy | 200+ | Python |
| **ta (bukosabino)** | 43 technical indicators, easy API | https://github.com/bukosabino/ta | 4.3k | Python |
| **candlestick (JS)** | 19 candlestick patterns for frontend | https://github.com/cm45t3r/candlestick | 50+ | JavaScript |

### 8.2 Installation & Setup

```bash
# Backend (Python)
pip install TA-Lib
pip install ta
git clone https://github.com/zeta-zetra/chart_patterns
pip install -r chart_patterns/requirements.txt
git clone https://github.com/keithorange/PatternPy

# Frontend (JavaScript)
npm install candlestick

# Additional dependencies
pip install pandas numpy matplotlib mplfinance
```

---

## 9. Success Metrics

| Category | Metric | Target | Measurement |
|----------|--------|--------|-------------|
| **Detection Accuracy** | Candlestick patterns | >85% | Backtesting vs. known patterns |
| **Detection Accuracy** | Chart patterns | >75% | Manual verification sample |
| **Performance** | Pattern detection latency | <100ms | Real-time monitoring |
| **User Adoption** | Users enabling patterns | 70%+ | Analytics tracking |
| **Strategy Performance** | Pattern strategies vs. baseline | +15% returns | 6-month backtest |
| **False Positives** | Invalid pattern alerts | <20% | User feedback + manual review |
| **Integration** | Libraries integrated | 5+ | Technical audit |
| **Coverage** | Patterns available | 65+ | Feature inventory |

---

## 10. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| **Library dependencies break** | Medium | High | Pin versions, maintain forks, test updates |
| **Pattern false positives** | High | Medium | Confidence scoring, multi-pattern confirmation |
| **Performance degradation** | Low | Medium | Async detection, worker threads, caching |
| **Overfitting to patterns** | Medium | High | Combine with fundamental analysis, position sizing |
| **User misinterpretation** | Medium | Medium | Pattern education section, disclaimer warnings |

---

## Document Control

**Version:** 5.0 (Pattern Recognition Update)  
**Date:** October 21, 2025  
**Changes:** Candlestick patterns, chart patterns, technical indicators, open-source integration

---

*End of PRD v5.0*