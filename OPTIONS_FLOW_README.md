# 📊 OPTIONS FLOW INDICATOR

**Track smart money and institutional flows with 3 powerful indicators**

---

## 🎯 WHAT THIS DOES

Analyzes real options data from Polygon.io to detect:

1. **Put/Call Ratio (PCR)** - Market sentiment (fear vs greed)
2. **Premium Flow** - Where money is actually going
3. **Unusual Activity** - Large institutional orders

Returns **values or `None`** - simple indicator pattern that won't break your trading system.

---

## 🔥 THE BIG 3 INDICATORS

### **1. PUT/CALL RATIO (PCR)** 

**What it measures:**
```
PCR = Put Volume / Call Volume
```

**How to read:**
| PCR | Meaning | Signal |
|-----|---------|--------|
| > 1.5 | Extreme fear | **BUY** (contrarian) |
| 1.0 - 1.5 | Bearish | Caution |
| 0.7 - 1.0 | Neutral | No edge |
| 0.5 - 0.7 | Bullish | Caution |
| < 0.5 | Extreme greed | **SELL** (contrarian) |

**Example:**
```python
pcr = 0.45  # More calls than puts
signal = "EXTREME_GREED_SELL"
interpretation = "Too much greed - contrarian sell signal"
```

---

### **2. PREMIUM FLOW**

**What it measures:**
```
Money flowing into calls vs puts
Premium = Volume × Price × 100
```

**How to read:**
| Call Premium % | Meaning | Signal |
|----------------|---------|--------|
| > 70% | Heavy call buying | **BULLISH** |
| 60-70% | Moderate call bias | Bullish |
| 40-60% | Balanced | Neutral |
| 30-40% | Moderate put bias | Bearish |
| < 30% | Heavy put buying | **BEARISH** |

**Why this matters:**
- Volume can be misleading (lots of cheap options)
- Premium = actual dollars spent = real conviction
- **Follow the money!**

**Example:**
```python
call_premium = $5,200,000
put_premium = $1,800,000
call_pct = 74%  # 74% of money in calls
signal = "STRONG_BULLISH"
```

---

### **3. UNUSUAL ACTIVITY**

**What it detects:**
- Volume > 50% of open interest (new positions)
- Large block orders
- Institutional sweeps

**How to read:**
| Detection | Signal |
|-----------|--------|
| Unusual calls > unusual puts × 2 | **BULLISH_SWEEP** |
| Unusual puts > unusual calls × 2 | **BEARISH_SWEEP** |
| Many unusual contracts | HIGH_ACTIVITY |
| Few unusual contracts | NORMAL |

**Why this matters:**
- Catches institutions making moves
- Often happens BEFORE price moves
- Early warning system

**Example:**
```python
unusual_calls = 12  # 12 unusual call contracts
unusual_puts = 2    # 2 unusual put contracts
signal = "BULLISH_SWEEP"  # Smart money buying calls
```

---

## 🚀 QUICK START

### **1. Install:**
```bash
pip install polygon-api-client
export POLYGON_API_KEY=your_key
```

### **2. Test:**
```bash
python options_flow_indicator.py
```

### **3. Add to TradePilot:**
```python
from options_flow_router import router as flow_router
app.include_router(flow_router)
```

### **4. Use:**
```bash
curl http://localhost:8000/indicators/flow/AMZN
```

---

## 📊 API ENDPOINTS

### **Complete Analysis:**
```bash
GET /indicators/flow/AMZN
```

Returns all 3 indicators + overall signal.

### **Put/Call Ratio Only:**
```bash
GET /indicators/flow/SPY/pcr
```

### **Premium Flow Only:**
```bash
GET /indicators/flow/TSLA/premium
```

### **Unusual Activity Only:**
```bash
GET /indicators/flow/NVDA/unusual
```

---

## 💡 EXAMPLE RESPONSES

### **When Data Available:**
```json
{
  "symbol": "AMZN",
  "put_call_ratio": 0.85,
  "call_volume": 125000,
  "put_volume": 106250,
  "pcr_signal": "BULLISH",
  
  "call_premium": 5200000,
  "put_premium": 1800000,
  "call_premium_pct": 74.3,
  "put_premium_pct": 25.7,
  "premium_signal": "STRONG_BULLISH",
  
  "unusual_call_contracts": 12,
  "unusual_put_contracts": 2,
  "unusual_activity_detected": true,
  "unusual_signal": "BULLISH_SWEEP",
  
  "overall_signal": "BULLISH",
  "signal_strength": "STRONG",
  "interpretation": "Bullish options flow detected - 74% of premium in calls - Unusual call buying detected"
}
```

### **When Data NOT Available:**
```json
{
  "symbol": "INVALID",
  "put_call_ratio": null,
  "call_volume": null,
  "put_volume": null,
  "pcr_signal": null,
  "call_premium": null,
  "put_premium": null,
  "call_premium_pct": null,
  "put_premium_pct": null,
  "premium_signal": null,
  "unusual_call_contracts": null,
  "unusual_put_contracts": null,
  "unusual_activity_detected": false,
  "unusual_signal": null,
  "overall_signal": null,
  "signal_strength": null,
  "interpretation": "Options flow data not available"
}
```

---

## 🎯 INTEGRATION WITH YOUR SYSTEM

### **Combined with GEX + IV:**

```python
# Your complete options analysis
def analyze_options_trade(symbol):
    # Get all indicators
    gex = get_gex_data(symbol)
    iv = get_iv_indicator(symbol)
    flow = get_options_flow(symbol)
    
    # Check if data available
    if flow["put_call_ratio"] is None:
        # Skip options flow, use other indicators
        pass
    else:
        # Use options flow in decision
        if (flow["overall_signal"] == "BULLISH" and 
            gex["gamma_exposure"] > 0 and 
            iv["iv_percentile"] < 50):
            
            return {
                "action": "BUY_CALL_DEBIT_SPREAD",
                "edge": "Bullish flow + Stable market + Cheap IV",
                "confidence": "HIGH"
            }
```

---

## 🔥 TRADING EXAMPLES

### **Example 1: Strong Bullish Setup**
```python
flow = get_options_flow("AMZN")

# PCR: 0.45 (extreme greed but...)
# Premium: 78% in calls (money flowing to upside)
# Unusual: 15 unusual call contracts (institutions buying)
# Signal: BULLISH

→ Despite high greed (contrarian bearish), premium flow and 
  unusual activity show smart money positioning for upside
→ Action: Buy call debit spreads
```

### **Example 2: Contrarian Buy**
```python
flow = get_options_flow("SPY")

# PCR: 1.8 (extreme fear)
# Premium: 65% in puts (fear-driven put buying)
# Unusual: Normal activity
# Signal: EXTREME_FEAR_BUY

→ Too much fear = contrarian buy opportunity
→ Action: Sell put credit spreads (collect premium from fear)
```

### **Example 3: Institutional Warning**
```python
flow = get_options_flow("TSLA")

# PCR: 1.1 (slightly bearish)
# Premium: 40% calls / 60% puts (moderate put buying)
# Unusual: 20 unusual put contracts (BEARISH_SWEEP)
# Signal: BEARISH

→ Institutions loading up on puts
→ Action: Reduce long exposure, consider hedges
```

---

## 📈 WHAT POLYGON GIVES US

**Real options data:**
- ✅ Options volume (calls vs puts)
- ✅ Contract prices (for premium calculation)
- ✅ Open interest (for unusual detection)
- ✅ Strike prices & expirations
- ✅ Full options chain

**Not estimates or proxies - REAL DATA!**

---

## 🎓 SIGNAL INTERPRETATION

### **Overall Signals:**

| Signal | Strength | Meaning |
|--------|----------|---------|
| BULLISH | STRONG | All 3 indicators bullish - high confidence |
| BULLISH | MODERATE | 2/3 indicators bullish |
| NEUTRAL | WEAK | Conflicting signals |
| BEARISH | MODERATE | 2/3 indicators bearish |
| BEARISH | STRONG | All 3 indicators bearish - high confidence |

---

## ⚙️ HOW IT WORKS

### **Data Flow:**
```
1. Fetch options chain from Polygon.io
   ↓
2. Separate calls and puts
   ↓
3. Calculate PCR (volume ratio)
   ↓
4. Calculate Premium Flow (money ratio)
   ↓
5. Detect Unusual Activity (volume vs OI)
   ↓
6. Combine all signals → Overall assessment
```

### **Calculation Details:**

**PCR:**
```python
call_volume = sum(all call volumes)
put_volume = sum(all put volumes)
pcr = put_volume / call_volume
```

**Premium:**
```python
call_premium = sum(call_volume × call_price × 100)
put_premium = sum(put_volume × put_price × 100)
call_pct = call_premium / (call_premium + put_premium) × 100
```

**Unusual:**
```python
for each contract:
    if volume > (open_interest × 0.5):
        # New large position = unusual
        flag_as_unusual()
```

---

## 🚨 IMPORTANT NOTES

### **Requires Polygon Options Plan:**
- Basic plan may not include full options data
- Starter/Developer plan should work
- Business plan has all features

### **Returns None When:**
- Symbol has no options
- Insufficient options activity
- API error
- Invalid symbol

### **Always Check:**
```python
if flow["put_call_ratio"] is not None:
    # Use flow data
else:
    # Skip this indicator
```

---

## 📋 FILES

| File | Purpose |
|------|---------|
| `options_flow_indicator.py` | Core indicator - PCR, Premium, Unusual |
| `options_flow_router.py` | FastAPI endpoints |
| `OPTIONS_FLOW_README.md` | This file |

---

## ✅ YOUR COMPLETE STACK

```
Layer 11: GEX (Gamma Exposure)
Layer 12: IV Rank/Percentile  
Layer 13: Options Flow (PCR + Premium + Unusual)

= Complete options trading system!
```

---

**Built for TradePilot** 🚀  
*Track smart money, make better trades*
