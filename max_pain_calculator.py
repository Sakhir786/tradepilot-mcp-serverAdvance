"""
Max Pain Calculator for TradePilot Engine
Calculates the strike price where maximum options value expires worthless
Uses real Polygon.io options data
"""

import os
import requests
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MaxPainCalculator:
    """Calculate Max Pain from real options chain data"""
    
    def __init__(self):
        self.api_key = os.getenv("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        
    def get_options_chain(self, symbol: str, expiration_date: str = None) -> Optional[List[Dict]]:
        """
        Fetch options chain for a symbol
        
        Args:
            symbol: Stock ticker (e.g., "SPY")
            expiration_date: Optional specific expiration (YYYY-MM-DD)
                           If None, uses nearest weekly expiration
        
        Returns:
            List of options contracts with OI data
        """
        try:
            # Get nearest expiration if not provided
            if not expiration_date:
                expiration_date = self._get_nearest_expiration(symbol)
            
            logger.info(f"Fetching options chain for {symbol} expiring {expiration_date}")
            
            # Fetch options contracts
            url = f"{self.base_url}/v3/reference/options/contracts"
            params = {
                "underlying_ticker": symbol,
                "expiration_date": expiration_date,
                "limit": 1000,
                "apiKey": self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"):
                logger.warning(f"No options contracts found for {symbol}")
                return None
            
            contracts = data["results"]
            
            # Get current prices and OI for each contract
            enriched_contracts = []
            for contract in contracts:
                contract_ticker = contract.get("ticker")
                if not contract_ticker:
                    continue
                
                # Get latest snapshot for this contract
                snapshot = self._get_contract_snapshot(contract_ticker)
                if snapshot:
                    contract["last_quote"] = snapshot.get("last_quote", {})
                    contract["open_interest"] = snapshot.get("open_interest", 0)
                    contract["implied_volatility"] = snapshot.get("implied_volatility")
                    enriched_contracts.append(contract)
            
            logger.info(f"Retrieved {len(enriched_contracts)} contracts with OI data")
            return enriched_contracts
            
        except Exception as e:
            logger.error(f"Error fetching options chain: {e}")
            return None
    
    def _get_contract_snapshot(self, contract_ticker: str) -> Optional[Dict]:
        """Get latest snapshot for an options contract"""
        try:
            url = f"{self.base_url}/v3/snapshot/options/{contract_ticker.split(':')[0]}/{contract_ticker}"
            params = {"apiKey": self.api_key}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get("results")
            
        except Exception as e:
            logger.debug(f"Could not get snapshot for {contract_ticker}: {e}")
            return None
    
    def _get_nearest_expiration(self, symbol: str) -> str:
        """Get the nearest Friday expiration date"""
        today = datetime.now()
        
        # Find next Friday
        days_ahead = 4 - today.weekday()  # Friday is 4
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_friday = today + timedelta(days=days_ahead)
        return next_friday.strftime("%Y-%m-%d")
    
    def calculate_max_pain(self, symbol: str, current_price: float = None, 
                          expiration_date: str = None) -> Optional[Dict]:
        """
        Calculate Max Pain strike price
        
        Max Pain Theory: Options sellers (market makers) manipulate stock price
        toward the strike where most options expire worthless, maximizing their profit.
        
        Formula:
        For each strike price S:
            Call Pain = Sum of [(S - Strike) * OI] for all ITM calls
            Put Pain = Sum of [(Strike - S) * OI] for all ITM puts
            Total Pain at S = Call Pain + Put Pain
        
        Max Pain = Strike with MAXIMUM total pain
        
        Args:
            symbol: Stock ticker
            current_price: Current stock price (fetched if not provided)
            expiration_date: Target expiration (uses nearest if not provided)
        
        Returns:
            Dict with max pain analysis or None if error
        """
        try:
            # Get options chain
            contracts = self.get_options_chain(symbol, expiration_date)
            if not contracts:
                return None
            
            # Get current price if not provided
            if not current_price:
                current_price = self._get_current_price(symbol)
                if not current_price:
                    logger.error(f"Could not get current price for {symbol}")
                    return None
            
            # Separate calls and puts
            calls = [c for c in contracts if c.get("contract_type") == "call"]
            puts = [c for c in contracts if c.get("contract_type") == "put"]
            
            if not calls or not puts:
                logger.warning(f"Incomplete options chain for {symbol}")
                return None
            
            # Get all unique strikes
            strikes = sorted(set([c.get("strike_price") for c in contracts 
                                if c.get("strike_price")]))
            
            logger.info(f"Analyzing {len(strikes)} strikes with {len(calls)} calls and {len(puts)} puts")
            
            # Calculate pain for each strike
            max_pain_strike = None
            max_pain_value = 0
            pain_by_strike = {}
            
            for strike in strikes:
                call_pain = 0
                put_pain = 0
                
                # Calculate call pain (calls ITM if strike < S)
                for call in calls:
                    call_strike = call.get("strike_price")
                    oi = call.get("open_interest", 0)
                    if strike > call_strike:  # Call is ITM
                        call_pain += (strike - call_strike) * oi * 100  # 100 shares per contract
                
                # Calculate put pain (puts ITM if strike > S)
                for put in puts:
                    put_strike = put.get("strike_price")
                    oi = put.get("open_interest", 0)
                    if strike < put_strike:  # Put is ITM
                        put_pain += (put_strike - strike) * oi * 100
                
                total_pain = call_pain + put_pain
                pain_by_strike[strike] = {
                    "call_pain": call_pain,
                    "put_pain": put_pain,
                    "total_pain": total_pain
                }
                
                if total_pain > max_pain_value:
                    max_pain_value = total_pain
                    max_pain_strike = strike
            
            # Get expiration date used
            exp_date = expiration_date or self._get_nearest_expiration(symbol)
            
            # Calculate metrics
            distance_to_max_pain = current_price - max_pain_strike
            distance_pct = (distance_to_max_pain / current_price) * 100
            
            # Determine bias
            if distance_to_max_pain > 0:
                bias = "BEARISH"  # Price above max pain, likely to get pulled down
                signal = "PUTS"
            elif distance_to_max_pain < 0:
                bias = "BULLISH"  # Price below max pain, likely to get pulled up
                signal = "CALLS"
            else:
                bias = "NEUTRAL"
                signal = "WAIT"
            
            # Calculate total OI
            total_call_oi = sum(c.get("open_interest", 0) for c in calls)
            total_put_oi = sum(p.get("open_interest", 0) for p in puts)
            put_call_oi_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            
            result = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "expiration": exp_date,
                "current_price": round(current_price, 2),
                "max_pain_strike": max_pain_strike,
                "distance_to_max_pain": round(distance_to_max_pain, 2),
                "distance_pct": round(distance_pct, 2),
                "max_pain_value": round(max_pain_value, 2),
                "bias": bias,
                "signal": signal,
                "total_call_oi": total_call_oi,
                "total_put_oi": total_put_oi,
                "put_call_oi_ratio": round(put_call_oi_ratio, 2),
                "strikes_analyzed": len(strikes),
                "pain_by_strike": pain_by_strike  # Full breakdown
            }
            
            logger.info(f"Max Pain for {symbol}: ${max_pain_strike} (current: ${current_price}, bias: {bias})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating max pain: {e}")
            return None
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price"""
        try:
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/prev"
            params = {"apiKey": self.api_key}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                return data["results"][0].get("c")  # Close price
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    calc = MaxPainCalculator()
    result = calc.calculate_max_pain("SPY")
    
    if result:
        print("\n" + "="*60)
        print("MAX PAIN ANALYSIS")
        print("="*60)
        print(f"Symbol: {result['symbol']}")
        print(f"Expiration: {result['expiration']}")
        print(f"Current Price: ${result['current_price']}")
        print(f"Max Pain Strike: ${result['max_pain_strike']}")
        print(f"Distance: ${result['distance_to_max_pain']} ({result['distance_pct']}%)")
        print(f"Bias: {result['bias']}")
        print(f"Signal: {result['signal']}")
        print(f"Put/Call OI Ratio: {result['put_call_oi_ratio']}")
        print("="*60)
