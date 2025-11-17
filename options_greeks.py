"""
Options Greeks Analyzer for TradePilot Engine
Extracts and analyzes options Greeks from Polygon.io
Delta, Gamma, Theta, Vega, Rho
"""

import os
import requests
from typing import Dict, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OptionsGreeksAnalyzer:
    """Analyze Options Greeks from real options data"""
    
    def __init__(self):
        self.api_key = os.getenv("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
    
    def get_atm_greeks(self, symbol: str, current_price: float = None) -> Optional[Dict]:
        """
        Get Greeks for At-The-Money (ATM) options
        
        ATM options have the highest gamma and are most sensitive to price changes.
        These are the most important Greeks for trading decisions.
        
        Args:
            symbol: Stock ticker
            current_price: Current stock price (fetched if not provided)
        
        Returns:
            Dict with ATM call and put Greeks
        """
        try:
            # Get current price if needed
            if not current_price:
                current_price = self._get_current_price(symbol)
                if not current_price:
                    return None
            
            logger.info(f"Finding ATM Greeks for {symbol} at ${current_price}")
            
            # Get options chain
            contracts = self._get_options_snapshot(symbol)
            if not contracts:
                return None
            
            # Find ATM strike (closest to current price)
            calls = [c for c in contracts if c.get("details", {}).get("contract_type") == "call"]
            puts = [c for c in contracts if c.get("details", {}).get("contract_type") == "put"]
            
            # Find ATM call
            atm_call = self._find_atm_contract(calls, current_price)
            atm_put = self._find_atm_contract(puts, current_price)
            
            if not atm_call or not atm_put:
                logger.warning(f"Could not find ATM contracts for {symbol}")
                return None
            
            # Extract Greeks
            call_greeks = atm_call.get("greeks", {})
            put_greeks = atm_put.get("greeks", {})
            
            result = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "current_price": round(current_price, 2),
                "atm_strike": atm_call.get("details", {}).get("strike_price"),
                "call_greeks": {
                    "delta": call_greeks.get("delta"),
                    "gamma": call_greeks.get("gamma"),
                    "theta": call_greeks.get("theta"),
                    "vega": call_greeks.get("vega"),
                    "rho": call_greeks.get("rho")
                },
                "put_greeks": {
                    "delta": put_greeks.get("delta"),
                    "gamma": put_greeks.get("gamma"),
                    "theta": put_greeks.get("theta"),
                    "vega": put_greeks.get("vega"),
                    "rho": put_greeks.get("rho")
                },
                "implied_volatility": {
                    "call": atm_call.get("implied_volatility"),
                    "put": atm_put.get("implied_volatility")
                }
            }
            
            logger.info(f"ATM Greeks retrieved: Call Delta={result['call_greeks']['delta']}, Gamma={result['call_greeks']['gamma']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting ATM Greeks: {e}")
            return None
    
    def get_portfolio_greeks(self, positions: List[Dict]) -> Optional[Dict]:
        """
        Calculate portfolio-level Greeks
        
        Args:
            positions: List of positions with format:
                [
                    {"symbol": "SPY", "strike": 580, "type": "call", "quantity": 10},
                    {"symbol": "AAPL", "strike": 230, "type": "put", "quantity": -5}
                ]
        
        Returns:
            Dict with aggregated portfolio Greeks
        """
        try:
            total_delta = 0
            total_gamma = 0
            total_theta = 0
            total_vega = 0
            total_rho = 0
            
            position_greeks = []
            
            for position in positions:
                symbol = position["symbol"]
                strike = position["strike"]
                contract_type = position["type"]
                quantity = position["quantity"]
                
                # Get contract Greeks
                contract = self._get_contract_by_strike(symbol, strike, contract_type)
                if not contract:
                    logger.warning(f"Could not find contract: {symbol} {strike} {contract_type}")
                    continue
                
                greeks = contract.get("greeks", {})
                
                # Multiply by quantity (negative for short positions)
                pos_delta = greeks.get("delta", 0) * quantity * 100  # 100 shares per contract
                pos_gamma = greeks.get("gamma", 0) * quantity * 100
                pos_theta = greeks.get("theta", 0) * quantity
                pos_vega = greeks.get("vega", 0) * quantity
                pos_rho = greeks.get("rho", 0) * quantity
                
                total_delta += pos_delta
                total_gamma += pos_gamma
                total_theta += pos_theta
                total_vega += pos_vega
                total_rho += pos_rho
                
                position_greeks.append({
                    "symbol": symbol,
                    "strike": strike,
                    "type": contract_type,
                    "quantity": quantity,
                    "delta": round(pos_delta, 2),
                    "gamma": round(pos_gamma, 4),
                    "theta": round(pos_theta, 2),
                    "vega": round(pos_vega, 2),
                    "rho": round(pos_rho, 2)
                })
            
            # Classify portfolio
            delta_regime = self._classify_delta(total_delta)
            gamma_regime = self._classify_gamma(total_gamma)
            theta_regime = self._classify_theta(total_theta)
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "portfolio_greeks": {
                    "delta": round(total_delta, 2),
                    "gamma": round(total_gamma, 4),
                    "theta": round(total_theta, 2),
                    "vega": round(total_vega, 2),
                    "rho": round(total_rho, 2)
                },
                "regime": {
                    "delta": delta_regime,
                    "gamma": gamma_regime,
                    "theta": theta_regime
                },
                "positions": position_greeks
            }
            
            logger.info(f"Portfolio Greeks: Delta={total_delta}, Gamma={total_gamma}, Theta={total_theta}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating portfolio Greeks: {e}")
            return None
    
    def _find_atm_contract(self, contracts: List[Dict], current_price: float) -> Optional[Dict]:
        """Find the contract closest to current price (ATM)"""
        if not contracts:
            return None
        
        atm_contract = min(contracts, 
                          key=lambda c: abs(c.get("details", {}).get("strike_price", 0) - current_price))
        return atm_contract
    
    def _get_options_snapshot(self, symbol: str) -> Optional[List[Dict]]:
        """Get options chain snapshot"""
        try:
            url = f"{self.base_url}/v3/snapshot/options/{symbol}"
            params = {"apiKey": self.api_key}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get("results", [])
            
        except Exception as e:
            logger.error(f"Error getting options snapshot: {e}")
            return None
    
    def _get_contract_by_strike(self, symbol: str, strike: float, 
                                contract_type: str) -> Optional[Dict]:
        """Get specific contract by strike and type"""
        try:
            contracts = self._get_options_snapshot(symbol)
            if not contracts:
                return None
            
            for contract in contracts:
                details = contract.get("details", {})
                if (details.get("strike_price") == strike and 
                    details.get("contract_type") == contract_type):
                    return contract
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting contract: {e}")
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
                return data["results"][0].get("c")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
    
    def _classify_delta(self, delta: float) -> str:
        """Classify portfolio delta exposure"""
        if delta > 100:
            return "LONG_BIASED"
        elif delta < -100:
            return "SHORT_BIASED"
        else:
            return "DELTA_NEUTRAL"
    
    def _classify_gamma(self, gamma: float) -> str:
        """Classify portfolio gamma exposure"""
        if gamma > 0.5:
            return "POSITIVE_GAMMA"  # Long options, profit from volatility
        elif gamma < -0.5:
            return "NEGATIVE_GAMMA"  # Short options, hurt by volatility
        else:
            return "GAMMA_NEUTRAL"
    
    def _classify_theta(self, theta: float) -> str:
        """Classify portfolio theta exposure"""
        if theta > 50:
            return "POSITIVE_THETA"  # Time decay helps (short options)
        elif theta < -50:
            return "NEGATIVE_THETA"  # Time decay hurts (long options)
        else:
            return "THETA_NEUTRAL"


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    analyzer = OptionsGreeksAnalyzer()
    
    # Test ATM Greeks
    print("\n" + "="*60)
    print("Testing ATM Greeks...")
    print("="*60)
    
    result = analyzer.get_atm_greeks("SPY")
    if result:
        print(f"Symbol: {result['symbol']}")
        print(f"ATM Strike: ${result['atm_strike']}")
        print(f"Call Delta: {result['call_greeks']['delta']}")
        print(f"Call Gamma: {result['call_greeks']['gamma']}")
        print(f"Call Theta: {result['call_greeks']['theta']}")
        print(f"Call Vega: {result['call_greeks']['vega']}")
    
    # Test Portfolio Greeks
    print("\n" + "="*60)
    print("Testing Portfolio Greeks...")
    print("="*60)
    
    test_positions = [
        {"symbol": "SPY", "strike": 580, "type": "call", "quantity": 10},
        {"symbol": "SPY", "strike": 575, "type": "put", "quantity": -5}
    ]
    
    portfolio = analyzer.get_portfolio_greeks(test_positions)
    if portfolio:
        print(f"Portfolio Delta: {portfolio['portfolio_greeks']['delta']}")
        print(f"Portfolio Gamma: {portfolio['portfolio_greeks']['gamma']}")
        print(f"Portfolio Theta: {portfolio['portfolio_greeks']['theta']}")
        print(f"Delta Regime: {portfolio['regime']['delta']}")
        print(f"Gamma Regime: {portfolio['regime']['gamma']}")
    
    print("="*60)
