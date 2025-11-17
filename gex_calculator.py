"""
GEX Calculator - Gamma Exposure Analysis
Calculates real gamma exposure from Polygon.io options data
Integrates with TradePilot MCP Server
"""

import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GEXLevel:
    """Gamma exposure level at a specific strike"""
    strike: float
    call_oi: int
    put_oi: int
    call_gamma: float
    put_gamma: float
    call_gex: float
    put_gex: float
    net_gex: float
    expiration: str


@dataclass
class GEXProfile:
    """Complete gamma exposure profile"""
    ticker: str
    current_price: float
    analysis_date: str
    largest_call_wall: GEXLevel
    largest_put_wall: GEXLevel
    zero_gamma_level: float
    resistance_levels: List[float]
    support_levels: List[float]
    total_call_gex: float
    total_put_gex: float
    net_gex: float
    regime: str
    dealer_positioning: str
    all_levels: List[GEXLevel]
    total_strikes_analyzed: int
    expirations_included: List[str]


class GEXCalculator:
    """
    Real Gamma Exposure Calculator using Polygon.io
    
    GEX Formula:
    - Call GEX = OI × Gamma × 100 × Spot Price / 1M
    - Put GEX = OI × Gamma × 100 × Spot Price × (-1) / 1M
    
    Market Mechanics:
    - Positive Net GEX = Dealers long gamma (stabilizing)
    - Negative Net GEX = Dealers short gamma (volatility amplifier)
    """
    
    def __init__(self, polygon_api_key: str):
        self.api_key = polygon_api_key
        self.base_url = "https://api.polygon.io"
        
    def get_current_price(self, ticker: str) -> float:
        """Get current stock price"""
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/prev"
        params = {"apiKey": self.api_key}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                return data["results"][0]["c"]
            else:
                raise ValueError(f"No price data for {ticker}")
                
        except Exception as e:
            logger.error(f"Error fetching price for {ticker}: {e}")
            raise
    
    def get_options_chain(self, ticker: str, min_expiry_days: int = 0, max_expiry_days: int = 60) -> pd.DataFrame:
        """Fetch complete options chain"""
        url = f"{self.base_url}/v3/reference/options/contracts"
        
        today = datetime.now()
        min_expiry = (today + timedelta(days=min_expiry_days)).strftime("%Y-%m-%d")
        max_expiry = (today + timedelta(days=max_expiry_days)).strftime("%Y-%m-%d")
        
        params = {
            "underlying_ticker": ticker,
            "expiration_date.gte": min_expiry,
            "expiration_date.lte": max_expiry,
            "limit": 1000,
            "apiKey": self.api_key
        }
        
        all_contracts = []
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                all_contracts.extend(data["results"])
                
                while data.get("next_url"):
                    next_url = data["next_url"] + f"&apiKey={self.api_key}"
                    response = requests.get(next_url)
                    data = response.json()
                    if data.get("results"):
                        all_contracts.extend(data["results"])
                    else:
                        break
            
            if not all_contracts:
                raise ValueError(f"No options contracts found for {ticker}")
            
            df = pd.DataFrame(all_contracts)
            logger.info(f"Fetched {len(df)} options contracts for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching options chain: {e}")
            raise
    
    def get_option_snapshot(self, option_ticker: str) -> Dict:
        """Get snapshot with Greeks and OI"""
        url = f"{self.base_url}/v3/snapshot/options/{option_ticker}"
        params = {"apiKey": self.api_key}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                result = data["results"]
                return {
                    "oi": result.get("open_interest", 0),
                    "gamma": result.get("greeks", {}).get("gamma", 0),
                    "delta": result.get("greeks", {}).get("delta", 0)
                }
            return {"oi": 0, "gamma": 0, "delta": 0}
                
        except Exception as e:
            logger.warning(f"Error fetching snapshot for {option_ticker}: {e}")
            return {"oi": 0, "gamma": 0, "delta": 0}
    
    def calculate_gex_for_strike(self, strike: float, call_oi: int, put_oi: int, call_gamma: float, put_gamma: float, spot_price: float) -> Tuple[float, float, float]:
        """Calculate GEX at a strike"""
        call_gex = (call_oi * call_gamma * 100 * spot_price) / 1_000_000
        put_gex = (put_oi * put_gamma * 100 * spot_price * -1) / 1_000_000
        net_gex = call_gex + put_gex
        
        return call_gex, put_gex, net_gex
    
    def analyze_ticker(self, ticker: str, min_expiry_days: int = 0, max_expiry_days: int = 60, min_oi: int = 100) -> GEXProfile:
        """Complete GEX analysis"""
        logger.info(f"Starting GEX analysis for {ticker}")
        
        spot_price = self.get_current_price(ticker)
        logger.info(f"Current price for {ticker}: ${spot_price:.2f}")
        
        chain = self.get_options_chain(ticker, min_expiry_days, max_expiry_days)
        
        strikes = chain.groupby(['strike_price', 'expiration_date'])
        
        gex_levels: List[GEXLevel] = []
        
        for (strike, expiry), group in strikes:
            calls = group[group['contract_type'] == 'call']
            puts = group[group['contract_type'] == 'put']
            
            if len(calls) == 0 or len(puts) == 0:
                continue
            
            call_ticker = calls.iloc[0]['ticker'] if len(calls) > 0 else None
            put_ticker = puts.iloc[0]['ticker'] if len(puts) > 0 else None
            
            call_data = self.get_option_snapshot(call_ticker) if call_ticker else {"oi": 0, "gamma": 0}
            put_data = self.get_option_snapshot(put_ticker) if put_ticker else {"oi": 0, "gamma": 0}
            
            call_oi = call_data["oi"]
            put_oi = put_data["oi"]
            
            if call_oi < min_oi and put_oi < min_oi:
                continue
            
            call_gamma = call_data["gamma"]
            put_gamma = put_data["gamma"]
            
            call_gex, put_gex, net_gex = self.calculate_gex_for_strike(strike, call_oi, put_oi, call_gamma, put_gamma, spot_price)
            
            level = GEXLevel(
                strike=strike,
                call_oi=call_oi,
                put_oi=put_oi,
                call_gamma=call_gamma,
                put_gamma=put_gamma,
                call_gex=call_gex,
                put_gex=put_gex,
                net_gex=net_gex,
                expiration=str(expiry)
            )
            
            gex_levels.append(level)
        
        if not gex_levels:
            raise ValueError(f"No valid GEX levels found for {ticker}")
        
        gex_levels.sort(key=lambda x: abs(x.net_gex), reverse=True)
        
        total_call_gex = sum(level.call_gex for level in gex_levels)
        total_put_gex = sum(level.put_gex for level in gex_levels)
        net_gex = total_call_gex + total_put_gex
        
        call_levels = sorted(gex_levels, key=lambda x: x.call_gex, reverse=True)
        put_levels = sorted(gex_levels, key=lambda x: abs(x.put_gex), reverse=True)
        
        largest_call_wall = call_levels[0]
        largest_put_wall = put_levels[0]
        
        resistance_levels = [level.strike for level in call_levels[:3]]
        support_levels = [level.strike for level in put_levels[:3]]
        
        sorted_by_strike = sorted(gex_levels, key=lambda x: x.strike)
        zero_gamma_level = spot_price
        
        for i in range(len(sorted_by_strike) - 1):
            if (sorted_by_strike[i].net_gex * sorted_by_strike[i+1].net_gex) < 0:
                zero_gamma_level = (sorted_by_strike[i].strike + sorted_by_strike[i+1].strike) / 2
                break
        
        if net_gex > 1000:
            regime = "Positive Gamma"
            dealer_positioning = "Long Gamma (Stabilizing)"
        elif net_gex < -1000:
            regime = "Negative Gamma"
            dealer_positioning = "Short Gamma (Volatility Amplifier)"
        else:
            regime = "Neutral Gamma"
            dealer_positioning = "Balanced"
        
        expirations = sorted(list(set(level.expiration for level in gex_levels)))
        
        profile = GEXProfile(
            ticker=ticker,
            current_price=spot_price,
            analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            largest_call_wall=largest_call_wall,
            largest_put_wall=largest_put_wall,
            zero_gamma_level=zero_gamma_level,
            resistance_levels=resistance_levels,
            support_levels=support_levels,
            total_call_gex=total_call_gex,
            total_put_gex=total_put_gex,
            net_gex=net_gex,
            regime=regime,
            dealer_positioning=dealer_positioning,
            all_levels=gex_levels,
            total_strikes_analyzed=len(gex_levels),
            expirations_included=expirations
        )
        
        logger.info(f"GEX analysis complete for {ticker}")
        return profile


def format_gex_summary(profile: GEXProfile) -> str:
    """Format GEX profile as readable summary"""
    
    summary = f"""
GAMMA EXPOSURE ANALYSIS - {profile.ticker}

MARKET DATA:
   Current Price: ${profile.current_price:.2f}
   Analysis Date: {profile.analysis_date}
   Strikes Analyzed: {profile.total_strikes_analyzed}

GAMMA EXPOSURE TOTALS:
   Total Call GEX: ${profile.total_call_gex:,.2f}M
   Total Put GEX:  ${profile.total_put_gex:,.2f}M
   Net GEX:        ${profile.net_gex:,.2f}M

MARKET REGIME:
   Regime: {profile.regime}
   Dealer Position: {profile.dealer_positioning}

GAMMA WALLS:
   Largest Call Wall: ${profile.largest_call_wall.strike:.2f} (${profile.largest_call_wall.call_gex:.2f}M)
   Largest Put Wall:  ${profile.largest_put_wall.strike:.2f} (${abs(profile.largest_put_wall.put_gex):.2f}M)

KEY LEVELS:
   Zero Gamma Level: ${profile.zero_gamma_level:.2f}
   
   Resistance (Call Walls):
   - ${profile.resistance_levels[0]:.2f}
   - ${profile.resistance_levels[1]:.2f}
   - ${profile.resistance_levels[2]:.2f}
   
   Support (Put Walls):
   - ${profile.support_levels[0]:.2f}
   - ${profile.support_levels[1]:.2f}
   - ${profile.support_levels[2]:.2f}
"""
    return summary


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    API_KEY = os.getenv("POLYGON_API_KEY")
    
    calculator = GEXCalculator(API_KEY)
    profile = calculator.analyze_ticker("AAPL", max_expiry_days=45)
    
    print(format_gex_summary(profile))
    
    print("\nTOP 10 GEX LEVELS:")
    print(f"{'Strike':<10} {'Call OI':<10} {'Put OI':<10} {'Net GEX':<12} {'Type'}")
    print("="*60)
    
    for level in profile.all_levels[:10]:
        gex_type = "CALL WALL" if level.call_gex > abs(level.put_gex) else "PUT WALL"
        print(f"${level.strike:<9.2f} {level.call_oi:<10} {level.put_oi:<10} ${level.net_gex:<11.2f} {gex_type}")
