"""
DEMO: Complete Options Trading System
Shows GEX + IV + Options Flow working together
"""

print("=" * 70)
print("🚀 COMPLETE OPTIONS TRADING SYSTEM DEMO")
print("=" * 70)
print()
print("Your TradePilot indicators working together:")
print()

# Simulated indicator responses
def simulate_complete_analysis(symbol):
    """Simulate what all indicators return"""
    
    # Example: AMZN analysis
    if symbol == "AMZN":
        return {
            "gex": {
                "gamma_exposure": 5000000,  # Positive = dealers want stability
                "signal": "STABLE_MARKET"
            },
            "iv": {
                "iv_percentile": 28.5,  # Low = options cheap
                "signal": "BUY_PREMIUM"
            },
            "flow": {
                "put_call_ratio": 0.85,  # More calls
                "call_premium_pct": 74.3,  # Money flowing to calls
                "unusual_call_contracts": 12,  # Institutions buying calls
                "overall_signal": "BULLISH",
                "signal_strength": "STRONG"
            }
        }
    
    # Example: TSLA analysis
    elif symbol == "TSLA":
        return {
            "gex": {
                "gamma_exposure": -2000000,  # Negative = volatile market
                "signal": "VOLATILE_MARKET"
            },
            "iv": {
                "iv_percentile": 88.2,  # High = options expensive
                "signal": "SELL_PREMIUM"
            },
            "flow": {
                "put_call_ratio": 1.45,  # More puts
                "call_premium_pct": 35.2,  # Money flowing to puts
                "unusual_put_contracts": 18,  # Institutions buying puts
                "overall_signal": "BEARISH",
                "signal_strength": "STRONG"
            }
        }
    
    # Example: SPY analysis
    else:
        return {
            "gex": {
                "gamma_exposure": 15000000,  # Very positive
                "signal": "VERY_STABLE"
            },
            "iv": {
                "iv_percentile": 52.1,  # Neutral
                "signal": "NEUTRAL"
            },
            "flow": {
                "put_call_ratio": 0.95,  # Balanced
                "call_premium_pct": 51.2,  # Balanced
                "unusual_call_contracts": 3,  # Normal activity
                "overall_signal": "NEUTRAL",
                "signal_strength": "WEAK"
            }
        }


def make_trading_decision(symbol, indicators):
    """Combine all indicators to make trading decision"""
    
    gex = indicators["gex"]
    iv = indicators["iv"]
    flow = indicators["flow"]
    
    print(f"Analyzing {symbol}...")
    print()
    
    # Display all indicators
    print("📊 INDICATOR READINGS:")
    print(f"   GEX: {gex['gamma_exposure']:,} ({gex['signal']})")
    print(f"   IV Percentile: {iv['iv_percentile']}% ({iv['signal']})")
    print(f"   Options Flow: {flow['overall_signal']} ({flow['signal_strength']})")
    print(f"   Put/Call Ratio: {flow['put_call_ratio']}")
    print(f"   Call Premium: {flow['call_premium_pct']}%")
    print()
    
    # Decision logic
    print("🎯 TRADING DECISION:")
    
    # Bullish setup
    if (flow["overall_signal"] == "BULLISH" and 
        gex["gamma_exposure"] > 0 and 
        iv["iv_percentile"] < 50):
        
        print("   ✅ STRONG BUY SETUP")
        print(f"   Strategy: BUY CALL DEBIT SPREADS")
        print(f"   Edge:")
        print(f"      • Bullish flow ({flow['call_premium_pct']}% premium in calls)")
        print(f"      • Stable market (positive GEX)")
        print(f"      • Cheap options (IV {iv['iv_percentile']}%)")
        print(f"   Confidence: HIGH")
    
    # Bearish setup
    elif (flow["overall_signal"] == "BEARISH" and 
          iv["iv_percentile"] > 75):
        
        print("   ✅ STRONG SELL SETUP")
        print(f"   Strategy: SELL CALL CREDIT SPREADS")
        print(f"   Edge:")
        print(f"      • Bearish flow ({flow['unusual_put_contracts']} unusual puts)")
        print(f"      • Expensive options (IV {iv['iv_percentile']}%)")
        print(f"   Confidence: HIGH")
    
    # Neutral / conflicting
    else:
        print("   ⚠️  NO CLEAR EDGE")
        print(f"   Strategy: WAIT FOR BETTER SETUP")
        print(f"   Reason: Conflicting signals or neutral conditions")
        print(f"   Confidence: LOW")
    
    print()


# Demo analysis
symbols = ["AMZN", "TSLA", "SPY"]

for symbol in symbols:
    print("=" * 70)
    indicators = simulate_complete_analysis(symbol)
    make_trading_decision(symbol, indicators)

print("=" * 70)
print()
print("✅ THIS IS YOUR COMPLETE SYSTEM:")
print()
print("   Layer 11: GEX → Market structure & dealer positioning")
print("   Layer 12: IV  → Options pricing (cheap vs expensive)")
print("   Layer 13: FLOW → Smart money tracking")
print()
print("   All 3 together → High-probability options trades!")
print()
print("=" * 70)
