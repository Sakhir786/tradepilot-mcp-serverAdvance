"""
Layer 11: Gamma Exposure (GEX) Engine
Options gamma exposure analysis as a TradePilot layer
"""

import pandas as pd
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()


class Layer11GEX:
    """GEX analysis integrated as TradePilot layer"""
    
    def __init__(self):
        try:
            from gex_calculator import GEXCalculator
            api_key = os.getenv("POLYGON_API_KEY")
            self.gex_calc = GEXCalculator(api_key)
            self.enabled = True
        except Exception as e:
            print(f"GEX Layer disabled: {e}")
            self.enabled = False
    
    def analyze(self, df: pd.DataFrame, symbol: str = None) -> Dict:
        """Run GEX analysis"""
        
        if not self.enabled:
            return {
                "error": "GEX module not available",
                "signal": "NEUTRAL",
                "enabled": False
            }
        
        if symbol is None:
            return {
                "error": "Symbol required for GEX analysis",
                "signal": "NEUTRAL"
            }
        
        try:
            profile = self.gex_calc.analyze_ticker(symbol, max_expiry_days=45)
            
            current_price = float(df["close"].iloc[-1])
            
            # Determine signal based on GEX positioning
            call_wall = profile.largest_call_wall.strike
            put_wall = profile.largest_put_wall.strike
            zero_gamma = profile.zero_gamma_level
            
            # Price relative to gamma walls
            if current_price < put_wall:
                position = "BELOW_SUPPORT"
                signal = "BULLISH"
            elif current_price > call_wall:
                position = "ABOVE_RESISTANCE"
                signal = "BEARISH"
            elif current_price < zero_gamma:
                position = "BELOW_ZERO_GAMMA"
                signal = "NEUTRAL_BEARISH"
            elif current_price > zero_gamma:
                position = "ABOVE_ZERO_GAMMA"
                signal = "NEUTRAL_BULLISH"
            else:
                position = "AT_ZERO_GAMMA"
                signal = "NEUTRAL"
            
            # Regime impact
            if profile.regime == "Positive Gamma":
                regime_signal = "STABILIZING"
            elif profile.regime == "Negative Gamma":
                regime_signal = "VOLATILE"
            else:
                regime_signal = "NEUTRAL"
            
            return {
                "net_gex": round(profile.net_gex, 2),
                "regime": profile.regime,
                "dealer_positioning": profile.dealer_positioning,
                "zero_gamma_level": round(zero_gamma, 2),
                "largest_call_wall": round(call_wall, 2),
                "largest_put_wall": round(put_wall, 2),
                "resistance_levels": [round(r, 2) for r in profile.resistance_levels],
                "support_levels": [round(s, 2) for s in profile.support_levels],
                "price_position": position,
                "regime_signal": regime_signal,
                "signal": signal,
                "enabled": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "signal": "NEUTRAL",
                "enabled": True
            }
