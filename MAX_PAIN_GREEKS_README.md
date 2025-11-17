# Max Pain + Options Greeks Calculators

**Real Polygon.io data | Production-ready | FastAPI integrated**

---

## 🎯 WHAT THIS IS

Two sophisticated options analysis modules for TradePilot Engine:

### 1. **Max Pain Calculator**
- Calculates the strike where maximum options value expires worthless
- Uses real open interest data from Polygon.io
- Returns bias (BULLISH/BEARISH/NEUTRAL) and signal (CALLS/PUTS/WAIT)
- Analyzes entire options chain for any symbol

### 2. **Options Greeks Analyzer**
- Extracts Delta, Gamma, Theta, Vega, Rho from Polygon data
- ATM Greeks (most important for trading)
- Portfolio-level Greeks aggregation
- Greek regime classification

---

## 📁 FILES

```
max_pain_calculator.py    # Core Max Pain logic
options_greeks.py          # Core Greeks logic
max_pain_router.py         # FastAPI endpoints for Max Pain
greeks_router.py           # FastAPI endpoints for Greeks
```

---

## 🔧 INTEGRATION

### Step 1: Add to TradePilot Engine

Place files in your project:
```
tradepilot-engine/
├── indicators/
│   ├── max_pain_calculator.py  ✅
│   └── options_greeks.py        ✅
├── routers/
│   ├── max_pain_router.py       ✅
│   └── greeks_router.py         ✅
```

### Step 2: Register Routers

In your `main.py` or `app.py`:

```python
from fastapi import FastAPI
from routers.max_pain_router import router as max_pain_router
from routers.greeks_router import router as greeks_router

app = FastAPI()

# Register routers
app.include_router(max_pain_router)
app.include_router(greeks_router)
```

### Step 3: Set Environment Variable

```bash
export POLYGON_API_KEY="your_polygon_api_key"
```

### Step 4: Install Dependencies

```bash
pip install requests fastapi pydantic --break-system-packages
```

---

## 🚀 API ENDPOINTS

### Max Pain Endpoints

#### 1. Get Full Max Pain Analysis
```bash
GET /max-pain/{symbol}

# Examples:
curl http://localhost:8000/max-pain/SPY
curl http://localhost:8000/max-pain/AAPL?current_price=230.50
curl http://localhost:8000/max-pain/TSLA?expiration_date=2025-01-17
```

**Response:**
```json
{
  "symbol": "SPY",
  "timestamp": "2025-11-15T00:00:00",
  "expiration": "2025-11-15",
  "current_price": 575.50,
  "max_pain_strike": 580.0,
  "distance_to_max_pain": -4.50,
  "distance_pct": -0.78,
  "max_pain_value": 125000000.0,
  "bias": "BULLISH",
  "signal": "CALLS",
  "total_call_oi": 450000,
  "total_put_oi": 520000,
  "put_call_oi_ratio": 1.16,
  "strikes_analyzed": 45
}
```

#### 2. Get Just Bias/Signal (Quick Decision)
```bash
GET /max-pain/{symbol}/bias

curl http://localhost:8000/max-pain/SPY/bias
```

**Response:**
```json
{
  "symbol": "SPY",
  "bias": "BULLISH",
  "signal": "CALLS",
  "distance_to_max_pain": -4.50,
  "distance_pct": -0.78,
  "max_pain_strike": 580.0,
  "current_price": 575.50
}
```

#### 3. Get Pain by Strike (Full Breakdown)
```bash
GET /max-pain/{symbol}/strikes

curl http://localhost:8000/max-pain/SPY/strikes
```

---

### Greeks Endpoints

#### 1. Get ATM Greeks
```bash
GET /greeks/{symbol}

# Examples:
curl http://localhost:8000/greeks/SPY
curl http://localhost:8000/greeks/AAPL?current_price=230.50
```

**Response:**
```json
{
  "symbol": "SPY",
  "timestamp": "2025-11-15T00:00:00",
  "current_price": 575.50,
  "atm_strike": 575.0,
  "call_greeks": {
    "delta": 0.52,
    "gamma": 0.035,
    "theta": -45.20,
    "vega": 120.50,
    "rho": 25.30
  },
  "put_greeks": {
    "delta": -0.48,
    "gamma": 0.035,
    "theta": -42.80,
    "vega": 118.20,
    "rho": -23.10
  },
  "implied_volatility": {
    "call": 0.18,
    "put": 0.19
  }
}
```

#### 2. Calculate Portfolio Greeks
```bash
POST /greeks/portfolio
Content-Type: application/json

{
  "positions": [
    {"symbol": "SPY", "strike": 580, "type": "call", "quantity": 10},
    {"symbol": "SPY", "strike": 575, "type": "put", "quantity": -5},
    {"symbol": "AAPL", "strike": 230, "type": "call", "quantity": 20}
  ]
}
```

**Response:**
```json
{
  "timestamp": "2025-11-15T00:00:00",
  "portfolio_greeks": {
    "delta": 1250.50,
    "gamma": 2.45,
    "theta": -850.30,
    "vega": 5420.10,
    "rho": 450.20
  },
  "regime": {
    "delta": "LONG_BIASED",
    "gamma": "POSITIVE_GAMMA",
    "theta": "NEGATIVE_THETA"
  },
  "positions": [...]
}
```

#### 3. Quick Greek Endpoints
```bash
# Just Delta
GET /greeks/{symbol}/delta

# Just Gamma
GET /greeks/{symbol}/gamma

# Just Theta
GET /greeks/{symbol}/theta
```

---

## 💡 USAGE IN TRADEPILOT

### Layer Integration

Add to your Layer 16 (IV/Options Analysis):

```python
from indicators.max_pain_calculator import MaxPainCalculator
from indicators.options_greeks import OptionsGreeksAnalyzer

class Layer16Engine:
    def __init__(self):
        self.max_pain_calc = MaxPainCalculator()
        self.greeks_analyzer = OptionsGreeksAnalyzer()
    
    def analyze(self, symbol: str):
        # Get Max Pain
        max_pain = self.max_pain_calc.calculate_max_pain(symbol)
        
        # Get Greeks
        greeks = self.greeks_analyzer.get_atm_greeks(symbol)
        
        # Make decision
        if max_pain and greeks:
            signal = self._combine_signals(max_pain, greeks)
            return signal
        
        return None
    
    def _combine_signals(self, max_pain, greeks):
        """
        Combine Max Pain bias with Greeks data
        
        Example logic:
        - If BULLISH bias + Positive Gamma → Strong BUY signal
        - If BEARISH bias + Negative Theta → Strong SELL signal
        """
        bias = max_pain["bias"]
        call_delta = greeks["call_greeks"]["delta"]
        gamma = greeks["call_greeks"]["gamma"]
        
        if bias == "BULLISH" and gamma > 0.03 and call_delta > 0.5:
            return "STRONG_BULLISH"
        elif bias == "BEARISH" and gamma > 0.03 and call_delta < 0.4:
            return "STRONG_BEARISH"
        else:
            return "NEUTRAL"
```

---

## 🧪 TESTING

### Test Max Pain
```bash
cd /path/to/indicators
python max_pain_calculator.py
```

Expected output:
```
============================================================
MAX PAIN ANALYSIS
============================================================
Symbol: SPY
Expiration: 2025-11-15
Current Price: $575.50
Max Pain Strike: $580.0
Distance: $-4.50 (-0.78%)
Bias: BULLISH
Signal: CALLS
Put/Call OI Ratio: 1.16
============================================================
```

### Test Greeks
```bash
cd /path/to/indicators
python options_greeks.py
```

Expected output:
```
============================================================
Testing ATM Greeks...
============================================================
Symbol: SPY
ATM Strike: $575.0
Call Delta: 0.52
Call Gamma: 0.035
Call Theta: -45.20
Call Vega: 120.50
============================================================
```

---

## 📊 THEORY & CALCULATIONS

### Max Pain Theory

**Concept:**
Options market makers have massive positions and can influence stock price. They profit most when options expire worthless (max pain for buyers).

**Calculation:**
For each strike price S:
1. **Call Pain** = Σ[(S - Strike) × OI] for all ITM calls
2. **Put Pain** = Σ[(Strike - S) × OI] for all ITM puts
3. **Total Pain** = Call Pain + Put Pain
4. **Max Pain** = Strike with MAXIMUM total pain

**Trading Signal:**
- Price > Max Pain → **BEARISH** (expect pulldown to max pain)
- Price < Max Pain → **BULLISH** (expect pullup to max pain)
- Price = Max Pain → **NEUTRAL** (already at equilibrium)

### Options Greeks

**Delta (Δ):**
- How much option price changes per $1 move in stock
- Calls: 0 to 1 (ATM ≈ 0.50)
- Puts: -1 to 0 (ATM ≈ -0.50)
- Use: Position sizing, hedging

**Gamma (Γ):**
- Rate of change in Delta
- ATM options have highest gamma
- High gamma = high risk/reward
- Use: Gamma scalping, volatility plays

**Theta (Θ):**
- Time decay per day
- Always negative for long options
- Accelerates closer to expiration
- Use: Time-based strategies, theta decay trades

**Vega (ν):**
- IV sensitivity
- $1 change in option price per 1% IV change
- High vega = high IV exposure
- Use: Volatility trades, straddles

**Rho (ρ):**
- Interest rate sensitivity
- Usually minimal impact
- Use: Long-term LEAPS only

---

## 🎯 TRADING STRATEGIES

### 1. Max Pain + IV Regime
```
IF Max Pain Bias = BULLISH
   AND IV Percentile < 30
   → BUY CALLS (cheap premium + bullish catalyst)

IF Max Pain Bias = BEARISH
   AND IV Percentile > 70
   → BUY PUTS (expensive but strong signal)
```

### 2. Greeks-Based Position Sizing
```
Target Delta: 1000 (moderate bullish)
Current Call Delta: 0.52
Contracts Needed: 1000 / (0.52 × 100) = 19 contracts
```

### 3. Delta-Neutral Strategy
```
Long 100 shares SPY ($575)
Delta exposure: +100

Buy ATM Puts (Delta -0.48)
Contracts needed: 100 / 48 = 2 contracts
Result: Portfolio delta ≈ 0 (neutral)
```

### 4. Gamma Scalping
```
Buy ATM Straddle (high gamma)
As stock moves:
  - Delta becomes positive → Sell shares to neutralize
  - Delta becomes negative → Buy shares to neutralize
Profit from volatility while staying delta-neutral
```

---

## ⚠️ LIMITATIONS

1. **Market Hours**: Options data best during market hours
2. **Liquidity**: Works best with high-volume symbols (SPY, QQQ, AAPL, etc.)
3. **Expiration**: Max Pain most accurate near expiration (Fri close)
4. **API Limits**: Polygon has rate limits on options endpoints
5. **Data Delay**: Polygon free tier may have 15-min delay

---

## 🔥 PRO TIPS

1. **Combine with GEX**: Max Pain + Gamma Walls = powerful confluence
2. **Weekly Expirations**: Most accurate for 0DTE and weekly options
3. **ATM Focus**: ATM Greeks are most important - ignore deep ITM/OTM
4. **Portfolio View**: Track portfolio Greeks daily for risk management
5. **Pin Risk**: Price often pins to max pain on expiration Friday
6. **Hedging**: Use Greeks to build perfect hedges (delta-neutral)

---

## 📈 INTEGRATION CHECKLIST

- [ ] Files copied to correct directories
- [ ] Routers registered in main.py
- [ ] POLYGON_API_KEY environment variable set
- [ ] Dependencies installed
- [ ] Test scripts run successfully
- [ ] API endpoints responding
- [ ] Layer 16 integration complete
- [ ] Trading logic implemented

---

## 🆘 TROUBLESHOOTING

**Issue: "No options contracts found"**
- Check if symbol has options (most stocks do)
- Try different expiration date
- Verify Polygon API key is valid

**Issue: "Could not get snapshot"**
- Polygon free tier may have delays
- Try during market hours
- Check API rate limits

**Issue: "Greeks returning None"**
- Symbol may have low liquidity
- Try high-volume stocks (SPY, QQQ, AAPL)
- Check options chain has data

---

## 🚀 NEXT STEPS

1. **Test with live data** during market hours
2. **Add to Layer 16** in TradePilot Engine
3. **Combine with IV/GEX** for confluence
4. **Build dashboards** to visualize Greeks
5. **Backtest strategies** using historical max pain data

---

**Built for TradePilot Engine | Real Polygon.io Data | Production Ready**
