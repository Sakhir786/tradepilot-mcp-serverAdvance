# GEX Module Integration Guide

## Files Created

1. **gex_calculator.py** - Core GEX calculation engine
2. **gex_router.py** - FastAPI routes for GEX endpoints
3. **layer_11_gex.py** - GEX as Layer 11 for TradePilot Engine
4. **test_gex.py** - Standalone test script
5. **This guide** - Integration instructions

---

## Quick Start

### Step 1: Copy Files to Your TradePilot Directory

```bash
# Copy these files to your TradePilot root directory:
cp gex_calculator.py /path/to/tradepilot/
cp gex_router.py /path/to/tradepilot/
cp test_gex.py /path/to/tradepilot/

# Copy Layer 11 to engine layers directory:
cp layer_11_gex.py /path/to/tradepilot/tradepilot_engine/layers/
```

### Step 2: Test GEX Module Standalone

```bash
cd /path/to/tradepilot/
source venv/bin/activate
python test_gex.py
```

You should see GEX analysis for AAPL!

---

## Integration with TradePilot

### Option 1: Add GEX API Endpoints Only

Edit `main.py` and add:

```python
# At the top with imports
from gex_router import router as gex_router

# After engine_router include
app.include_router(gex_router)
```

Restart server:
```bash
uvicorn main:app --reload --port 10000
```

Test it:
```bash
curl "http://localhost:10000/gex/quick/AAPL"
```

### Option 2: Add GEX as Engine Layer 11

**Edit `tradepilot_engine/layers/__init__.py`:**

```python
from .layer_1_momentum import Layer1Momentum
from .layer_2_volume import Layer2Volume
# ... other layers ...
from .layer_11_gex import Layer11GEX

__all__ = [
    "Layer1Momentum",
    "Layer2Volume",
    # ... other layers ...
    "Layer11GEX"
]
```

**Edit `tradepilot_engine/engine_core.py`:**

Add import:
```python
from .layers import (
    Layer1Momentum,
    Layer2Volume,
    # ... other layers ...
    Layer11GEX
)
```

Add to layers dict in `__init__`:
```python
def __init__(self):
    self.data_processor = DataProcessor()
    self.layers = {
        "layer_1_momentum": Layer1Momentum(),
        # ... other layers ...
        "layer_11_gex": Layer11GEX()
    }
```

Add to analyze method:
```python
# In analyze() method, after other layers
if "layer_11_gex" in self.layers:
    results["layers"]["layer_11_gex"] = self.layers["layer_11_gex"].analyze(df, symbol)
```

---

## API Endpoints

Once integrated, you'll have:

### 1. Full GEX Analysis
```bash
POST http://localhost:10000/gex/analyze
Content-Type: application/json

{
  "ticker": "AAPL",
  "max_expiry_days": 60,
  "min_oi": 100
}
```

### 2. Quick GEX Summary
```bash
GET http://localhost:10000/gex/quick/AAPL
```

### 3. Health Check
```bash
GET http://localhost:10000/gex/health
```

### 4. Engine Analysis (if Layer 11 added)
```bash
GET http://localhost:10000/engine/analyze?symbol=AAPL
```

---

## Response Examples

### Quick GEX Response
```json
{
  "ticker": "AAPL",
  "price": 237.51,
  "net_gex": "$1234.56M",
  "regime": "Positive Gamma",
  "zero_gamma": "$235.00",
  "call_wall": "$240.00",
  "put_wall": "$230.00",
  "resistance": ["$240.00", "$245.00", "$250.00"],
  "support": ["$230.00", "$225.00", "$220.00"]
}
```

### Full Analysis Response
```json
{
  "ticker": "AAPL",
  "current_price": 237.51,
  "net_gex": 1234.56,
  "regime": "Positive Gamma",
  "dealer_positioning": "Long Gamma (Stabilizing)",
  "zero_gamma_level": 235.00,
  "largest_call_wall": 240.00,
  "largest_put_wall": 230.00,
  "resistance_levels": [240.00, 245.00, 250.00],
  "support_levels": [230.00, 225.00, 220.00],
  "total_call_gex": 2500.00,
  "total_put_gex": -1265.44,
  "top_10_levels": [...]
}
```

---

## What GEX Tells You

### Market Regimes

**Positive Net GEX (> $1000M)**
- Market makers are LONG gamma
- Price tends to STABILIZE near current levels
- Dealers sell rallies, buy dips (dampening)
- Lower volatility expected

**Negative Net GEX (< -$1000M)**
- Market makers are SHORT gamma
- Price volatility AMPLIFIED
- Dealers buy rallies, sell dips (momentum)
- Higher volatility expected

**Neutral (-$1000M to +$1000M)**
- Balanced positioning
- Normal volatility

### Key Levels

**Call Walls (Resistance)**
- Strikes with high call open interest
- Dealers sell stock to hedge as price rises
- Acts as resistance

**Put Walls (Support)**
- Strikes with high put open interest
- Dealers buy stock to hedge as price falls
- Acts as support

**Zero Gamma Level**
- Price where net GEX crosses zero
- Pivot point between regimes
- Often strong support/resistance

---

## Trading Strategy Examples

### Strategy 1: Mean Reversion (Positive Gamma)
```
If Net GEX > $1000M:
  - Price bounces between call/put walls
  - Sell rallies near call wall
  - Buy dips near put wall
  - Expect range-bound behavior
```

### Strategy 2: Momentum (Negative Gamma)
```
If Net GEX < -$1000M:
  - Breakouts accelerate
  - Trend following works better
  - Use wider stops
  - Expect bigger moves
```

### Strategy 3: Gamma Flip
```
Watch Zero Gamma Level:
  - Break above = bullish regime change
  - Break below = bearish regime change
  - High probability reversal zones
```

---

## Performance Tips

### API Rate Limits
- **Free Tier**: 5 calls/min (very slow for GEX)
- **Starter ($30/mo)**: 100 calls/min (recommended)
- **Developer ($100/mo)**: Unlimited

Each GEX analysis makes ~20-50 API calls.

### Caching
Add caching to avoid repeated calls:

```python
# In gex_router.py
from cachetools import TTLCache

cache = TTLCache(maxsize=100, ttl=300)  # 5 min cache

@router.get("/quick/{ticker}")
async def quick_gex(ticker: str):
    if ticker in cache:
        return cache[ticker]
    
    profile = gex_calc.analyze_ticker(ticker)
    result = {...}
    cache[ticker] = result
    return result
```

---

## Troubleshooting

### "No options contracts found"
- Check ticker symbol is correct
- Stock may not have options
- Try increasing `max_expiry_days`

### "Insufficient data"
- Not enough contracts with OI > min_oi
- Lower `min_oi` parameter
- Try major tickers (AAPL, SPY, TSLA)

### API Rate Limit Errors
- Upgrade Polygon.io plan
- Add caching
- Reduce `max_expiry_days`

### Slow Performance
- Normal on free tier (5 calls/min)
- Each analysis takes 2-5 minutes on free tier
- Upgrade to Starter tier for speed

---

## Advanced Configuration

### Adjust Expiry Window
```python
# Only near-term (0-30 days)
profile = gex_calc.analyze_ticker("AAPL", max_expiry_days=30)

# Include longer dated (0-90 days)
profile = gex_calc.analyze_ticker("AAPL", max_expiry_days=90)
```

### Change OI Threshold
```python
# Only major strikes (OI > 500)
profile = gex_calc.analyze_ticker("AAPL", min_oi=500)

# Include more strikes (OI > 50)
profile = gex_calc.analyze_ticker("AAPL", min_oi=50)
```

---

## Next Steps

1. ✅ Test standalone: `python test_gex.py`
2. ✅ Add API routes to main.py
3. ✅ Test endpoints: `curl http://localhost:10000/gex/quick/AAPL`
4. ✅ (Optional) Add as Layer 11
5. ✅ Check `/docs` endpoint for interactive testing

---

## Support

- **Documentation**: This guide + code comments
- **Test Script**: `python test_gex.py`
- **API Docs**: `http://localhost:10000/docs`

**You're all set! Start analyzing gamma exposure!** 🚀
