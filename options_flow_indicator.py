"""
OPTIONS FLOW INDICATOR FOR TRADEPILOT
Tracks smart money and institutional flows using Polygon.io

Indicators:
1. Put/Call Ratio (PCR) - Sentiment gauge
2. Premium Flow - Money direction (calls vs puts)
3. Unusual Activity - Large institutional orders

Returns values or None (simple indicator pattern)
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

try:
    from polygon import RESTClient
except ImportError:
    print("❌ polygon-api-client not installed. Run: pip install polygon-api-client")
    RESTClient = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptionsFlowIndicator:
    """
    Options Flow Indicator - Tracks smart money movements
    
    Returns:
        Values if data available, None if not available
    """
    
    def __init__(self, polygon_api_key: Optional[str] = None):
        """Initialize Options Flow indicator"""
        self.api_key = polygon_api_key or os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("❌ POLYGON_API_KEY required")
        
        if RESTClient is None:
            raise ImportError("polygon-api-client not installed")
        
        self.client = RESTClient(self.api_key)
        logger.info("✅ Options Flow Indicator initialized")
    
    def analyze(self, symbol: str, lookback_days: int = 20) -> Dict:
        """
        Analyze options flow for a symbol
        
        Returns complete flow analysis with PCR, premium flow, and unusual activity
        Or returns all None values if data not available
        
        Args:
            symbol: Stock symbol (SPY, AMZN, etc.)
            lookback_days: Days to look back for unusual activity detection
            
        Returns:
            Dict with flow metrics or None values
        """
        symbol = symbol.upper()
        logger.info(f"🔍 Analyzing options flow for {symbol}")
        
        try:
            # Get options chain
            options_chain = self._fetch_options_chain(symbol)
            
            if not options_chain or len(options_chain) < 5:
                logger.warning(f"Insufficient options data for {symbol}")
                return self._empty_response(symbol)
            
            # Separate calls and puts
            calls = [opt for opt in options_chain if opt.get('contract_type') == 'call']
            puts = [opt for opt in options_chain if opt.get('contract_type') == 'put']
            
            if not calls or not puts:
                logger.warning(f"Missing calls or puts for {symbol}")
                return self._empty_response(symbol)
            
            # Calculate Put/Call Ratio
            pcr = self._calculate_pcr(calls, puts)
            
            # Calculate Premium Flow
            premium_flow = self._calculate_premium_flow(calls, puts)
            
            # Detect Unusual Activity
            unusual_activity = self._detect_unusual_activity(options_chain, lookback_days)
            
            # Determine overall signal
            signal = self._determine_signal(pcr, premium_flow, unusual_activity)
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                
                # Put/Call Ratio
                "put_call_ratio": pcr["ratio"],
                "put_volume": pcr["put_volume"],
                "call_volume": pcr["call_volume"],
                "pcr_signal": pcr["signal"],
                
                # Premium Flow
                "call_premium": premium_flow["call_premium"],
                "put_premium": premium_flow["put_premium"],
                "call_premium_pct": premium_flow["call_pct"],
                "put_premium_pct": premium_flow["put_pct"],
                "premium_ratio": premium_flow["ratio"],
                "premium_signal": premium_flow["signal"],
                
                # Unusual Activity
                "unusual_call_contracts": len(unusual_activity["calls"]),
                "unusual_put_contracts": len(unusual_activity["puts"]),
                "unusual_activity_detected": unusual_activity["detected"],
                "unusual_signal": unusual_activity["signal"],
                
                # Overall Assessment
                "overall_signal": signal["direction"],
                "signal_strength": signal["strength"],
                "interpretation": signal["interpretation"]
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing {symbol}: {e}")
            return self._empty_response(symbol)
    
    def _fetch_options_chain(self, symbol: str) -> List[Dict]:
        """
        Fetch options chain for symbol
        Gets all active options contracts
        """
        try:
            # Get options snapshot for the underlying
            # This gets all options contracts for the symbol
            response = self.client.get_snapshot_option(
                underlying_asset=symbol,
                limit=250  # Get up to 250 contracts
            )
            
            if not response or not hasattr(response, 'results'):
                return []
            
            # Parse options data
            options = []
            for contract in response.results:
                # Extract relevant data
                opt_data = {
                    'contract_type': contract.details.contract_type if hasattr(contract, 'details') else None,
                    'strike': contract.details.strike_price if hasattr(contract, 'details') else None,
                    'expiration': contract.details.expiration_date if hasattr(contract, 'details') else None,
                    'volume': contract.day.volume if hasattr(contract, 'day') and contract.day else 0,
                    'price': contract.day.close if hasattr(contract, 'day') and contract.day else 0,
                    'open_interest': contract.open_interest if hasattr(contract, 'open_interest') else 0,
                    'ticker': contract.details.ticker if hasattr(contract, 'details') else None
                }
                
                # Only include contracts with volume
                if opt_data['volume'] and opt_data['volume'] > 0:
                    options.append(opt_data)
            
            logger.info(f"  Fetched {len(options)} active contracts for {symbol}")
            return options
            
        except Exception as e:
            logger.error(f"Error fetching options chain: {e}")
            return []
    
    def _calculate_pcr(self, calls: List[Dict], puts: List[Dict]) -> Dict:
        """
        Calculate Put/Call Ratio from volume
        
        PCR > 1.0 = More puts (bearish)
        PCR < 0.7 = More calls (bullish)
        """
        call_volume = sum(opt['volume'] for opt in calls if opt['volume'])
        put_volume = sum(opt['volume'] for opt in puts if opt['volume'])
        
        if call_volume == 0:
            return {
                "ratio": None,
                "call_volume": call_volume,
                "put_volume": put_volume,
                "signal": None
            }
        
        pcr = put_volume / call_volume
        
        # Determine signal (contrarian indicator)
        if pcr > 1.5:
            signal = "EXTREME_FEAR_BUY"  # Too much fear = buy opportunity
        elif pcr > 1.0:
            signal = "BEARISH"
        elif pcr < 0.5:
            signal = "EXTREME_GREED_SELL"  # Too much greed = sell opportunity
        elif pcr < 0.7:
            signal = "BULLISH"
        else:
            signal = "NEUTRAL"
        
        return {
            "ratio": round(pcr, 3),
            "call_volume": call_volume,
            "put_volume": put_volume,
            "signal": signal
        }
    
    def _calculate_premium_flow(self, calls: List[Dict], puts: List[Dict]) -> Dict:
        """
        Calculate where money is flowing (calls vs puts)
        Premium = Volume × Price (money spent)
        """
        # Calculate total premium (money spent)
        call_premium = sum(
            opt['volume'] * opt['price'] * 100  # *100 for contract multiplier
            for opt in calls 
            if opt['volume'] and opt['price']
        )
        
        put_premium = sum(
            opt['volume'] * opt['price'] * 100
            for opt in puts 
            if opt['volume'] and opt['price']
        )
        
        total_premium = call_premium + put_premium
        
        if total_premium == 0:
            return {
                "call_premium": 0,
                "put_premium": 0,
                "call_pct": None,
                "put_pct": None,
                "ratio": None,
                "signal": None
            }
        
        call_pct = (call_premium / total_premium) * 100
        put_pct = (put_premium / total_premium) * 100
        
        # Premium ratio (calls / puts)
        premium_ratio = call_premium / put_premium if put_premium > 0 else None
        
        # Determine signal (follow the money)
        if call_pct > 70:
            signal = "STRONG_BULLISH"
        elif call_pct > 60:
            signal = "BULLISH"
        elif put_pct > 70:
            signal = "STRONG_BEARISH"
        elif put_pct > 60:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"
        
        return {
            "call_premium": round(call_premium, 2),
            "put_premium": round(put_premium, 2),
            "call_pct": round(call_pct, 2),
            "put_pct": round(put_pct, 2),
            "ratio": round(premium_ratio, 3) if premium_ratio else None,
            "signal": signal
        }
    
    def _detect_unusual_activity(self, options: List[Dict], lookback_days: int) -> Dict:
        """
        Detect unusual options activity
        Unusual = Volume > 2x typical volume
        """
        unusual_calls = []
        unusual_puts = []
        
        for opt in options:
            volume = opt.get('volume', 0)
            oi = opt.get('open_interest', 0)
            
            # Skip if no volume
            if not volume or volume == 0:
                continue
            
            # Simple unusual detection: volume > 2x open interest
            # This catches new large positions being opened
            if oi > 0 and volume > (oi * 0.5):
                unusual_data = {
                    'type': opt.get('contract_type'),
                    'strike': opt.get('strike'),
                    'volume': volume,
                    'oi': oi,
                    'volume_oi_ratio': round(volume / oi, 2) if oi > 0 else None
                }
                
                if opt.get('contract_type') == 'call':
                    unusual_calls.append(unusual_data)
                else:
                    unusual_puts.append(unusual_data)
        
        # Sort by volume (largest first)
        unusual_calls.sort(key=lambda x: x['volume'], reverse=True)
        unusual_puts.sort(key=lambda x: x['volume'], reverse=True)
        
        # Determine signal
        if len(unusual_calls) > len(unusual_puts) * 2:
            signal = "BULLISH_SWEEP"
        elif len(unusual_puts) > len(unusual_calls) * 2:
            signal = "BEARISH_SWEEP"
        elif len(unusual_calls) > 5 or len(unusual_puts) > 5:
            signal = "HIGH_ACTIVITY"
        else:
            signal = "NORMAL"
        
        return {
            "detected": len(unusual_calls) > 0 or len(unusual_puts) > 0,
            "calls": unusual_calls[:5],  # Top 5
            "puts": unusual_puts[:5],    # Top 5
            "signal": signal
        }
    
    def _determine_signal(
        self, 
        pcr: Dict, 
        premium: Dict, 
        unusual: Dict
    ) -> Dict:
        """
        Determine overall signal from all indicators
        Combines PCR, premium flow, and unusual activity
        """
        signals = []
        
        # Weight the signals
        # PCR (contrarian)
        if pcr["signal"] in ["EXTREME_FEAR_BUY", "BULLISH"]:
            signals.append(("BULLISH", 1))
        elif pcr["signal"] in ["EXTREME_GREED_SELL", "BEARISH"]:
            signals.append(("BEARISH", 1))
        
        # Premium flow (follow money)
        if premium["signal"] in ["STRONG_BULLISH", "BULLISH"]:
            signals.append(("BULLISH", 2))  # Weight 2 (more important)
        elif premium["signal"] in ["STRONG_BEARISH", "BEARISH"]:
            signals.append(("BEARISH", 2))
        
        # Unusual activity (institutional moves)
        if unusual["signal"] == "BULLISH_SWEEP":
            signals.append(("BULLISH", 2))
        elif unusual["signal"] == "BEARISH_SWEEP":
            signals.append(("BEARISH", 2))
        
        # Count weighted signals
        bullish_weight = sum(w for s, w in signals if s == "BULLISH")
        bearish_weight = sum(w for s, w in signals if s == "BEARISH")
        
        # Determine overall direction
        if bullish_weight > bearish_weight + 1:
            direction = "BULLISH"
            strength = "STRONG" if bullish_weight >= 4 else "MODERATE"
        elif bearish_weight > bullish_weight + 1:
            direction = "BEARISH"
            strength = "STRONG" if bearish_weight >= 4 else "MODERATE"
        else:
            direction = "NEUTRAL"
            strength = "WEAK"
        
        # Generate interpretation
        interpretation = self._generate_interpretation(
            direction, strength, pcr, premium, unusual
        )
        
        return {
            "direction": direction,
            "strength": strength,
            "interpretation": interpretation
        }
    
    def _generate_interpretation(
        self, 
        direction: str, 
        strength: str,
        pcr: Dict,
        premium: Dict,
        unusual: Dict
    ) -> str:
        """Generate human-readable interpretation"""
        
        parts = []
        
        # Overall direction
        if direction == "BULLISH":
            parts.append("Bullish options flow detected")
        elif direction == "BEARISH":
            parts.append("Bearish options flow detected")
        else:
            parts.append("Neutral options flow")
        
        # Add details
        if premium["call_pct"] and premium["call_pct"] > 60:
            parts.append(f"{premium['call_pct']:.0f}% of premium in calls")
        elif premium["put_pct"] and premium["put_pct"] > 60:
            parts.append(f"{premium['put_pct']:.0f}% of premium in puts")
        
        if unusual["detected"]:
            if unusual["signal"] == "BULLISH_SWEEP":
                parts.append("Unusual call buying detected")
            elif unusual["signal"] == "BEARISH_SWEEP":
                parts.append("Unusual put buying detected")
        
        return " - ".join(parts)
    
    def _empty_response(self, symbol: str) -> Dict:
        """Return empty response when data not available"""
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "put_call_ratio": None,
            "put_volume": None,
            "call_volume": None,
            "pcr_signal": None,
            "call_premium": None,
            "put_premium": None,
            "call_premium_pct": None,
            "put_premium_pct": None,
            "premium_ratio": None,
            "premium_signal": None,
            "unusual_call_contracts": None,
            "unusual_put_contracts": None,
            "unusual_activity_detected": False,
            "unusual_signal": None,
            "overall_signal": None,
            "signal_strength": None,
            "interpretation": "Options flow data not available"
        }


# ═══════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🧪 Testing Options Flow Indicator\n")
    
    try:
        indicator = OptionsFlowIndicator()
    except ValueError as e:
        print(f"❌ {e}")
        exit(1)
    
    # Test with popular symbols
    test_symbols = ["SPY", "AMZN", "TSLA"]
    
    for symbol in test_symbols:
        print(f"{'='*70}")
        print(f"📊 Analyzing {symbol}")
        print(f"{'='*70}")
        
        result = indicator.analyze(symbol)
        
        if result["put_call_ratio"] is not None:
            print(f"✅ Options Flow Available\n")
            
            # Put/Call Ratio
            print(f"📈 PUT/CALL RATIO:")
            print(f"   PCR: {result['put_call_ratio']}")
            print(f"   Call Volume: {result['call_volume']:,}")
            print(f"   Put Volume: {result['put_volume']:,}")
            print(f"   Signal: {result['pcr_signal']}\n")
            
            # Premium Flow
            print(f"💰 PREMIUM FLOW:")
            print(f"   Call Premium: ${result['call_premium']:,.0f}")
            print(f"   Put Premium: ${result['put_premium']:,.0f}")
            print(f"   Calls: {result['call_premium_pct']:.1f}%")
            print(f"   Puts: {result['put_premium_pct']:.1f}%")
            print(f"   Signal: {result['premium_signal']}\n")
            
            # Unusual Activity
            print(f"🔥 UNUSUAL ACTIVITY:")
            print(f"   Unusual Calls: {result['unusual_call_contracts']}")
            print(f"   Unusual Puts: {result['unusual_put_contracts']}")
            print(f"   Signal: {result['unusual_signal']}\n")
            
            # Overall
            print(f"🎯 OVERALL ASSESSMENT:")
            print(f"   Direction: {result['overall_signal']}")
            print(f"   Strength: {result['signal_strength']}")
            print(f"   {result['interpretation']}")
        else:
            print(f"⚠️  No options flow data available")
        
        print()
    
    print("✅ Test complete!")
