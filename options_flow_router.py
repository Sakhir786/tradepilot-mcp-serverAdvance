"""
OPTIONS FLOW API ROUTER FOR TRADEPILOT

Endpoints:
    GET /indicators/flow/{symbol} - Complete flow analysis
    GET /indicators/flow/{symbol}/pcr - Put/Call Ratio only
    GET /indicators/flow/{symbol}/premium - Premium flow only
    GET /indicators/flow/{symbol}/unusual - Unusual activity only
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

from options_flow_indicator import OptionsFlowIndicator

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/indicators/flow", tags=["Options Flow"])

# Singleton indicator
_flow_indicator: Optional[OptionsFlowIndicator] = None


def get_indicator() -> OptionsFlowIndicator:
    """Get or create indicator instance"""
    global _flow_indicator
    if _flow_indicator is None:
        _flow_indicator = OptionsFlowIndicator()
        logger.info("✅ Options Flow Indicator initialized")
    return _flow_indicator


# ═══════════════════════════════════════════════════════════════════
# RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════

class UnusualContract(BaseModel):
    """Unusual activity contract data"""
    type: str
    strike: float
    volume: int
    oi: int
    volume_oi_ratio: Optional[float]


class OptionsFlowResponse(BaseModel):
    """Complete options flow response"""
    symbol: str
    timestamp: str
    
    # Put/Call Ratio
    put_call_ratio: Optional[float]
    put_volume: Optional[int]
    call_volume: Optional[int]
    pcr_signal: Optional[str]
    
    # Premium Flow
    call_premium: Optional[float]
    put_premium: Optional[float]
    call_premium_pct: Optional[float]
    put_premium_pct: Optional[float]
    premium_ratio: Optional[float]
    premium_signal: Optional[str]
    
    # Unusual Activity
    unusual_call_contracts: Optional[int]
    unusual_put_contracts: Optional[int]
    unusual_activity_detected: bool
    unusual_signal: Optional[str]
    
    # Overall
    overall_signal: Optional[str]
    signal_strength: Optional[str]
    interpretation: str


class PCRResponse(BaseModel):
    """Put/Call Ratio response"""
    symbol: str
    put_call_ratio: Optional[float]
    call_volume: Optional[int]
    put_volume: Optional[int]
    signal: Optional[str]
    timestamp: str


class PremiumFlowResponse(BaseModel):
    """Premium flow response"""
    symbol: str
    call_premium: Optional[float]
    put_premium: Optional[float]
    call_premium_pct: Optional[float]
    put_premium_pct: Optional[float]
    premium_ratio: Optional[float]
    signal: Optional[str]
    timestamp: str


class UnusualActivityResponse(BaseModel):
    """Unusual activity response"""
    symbol: str
    detected: bool
    unusual_call_contracts: Optional[int]
    unusual_put_contracts: Optional[int]
    signal: Optional[str]
    timestamp: str


# ═══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/{symbol}", response_model=OptionsFlowResponse)
async def get_options_flow(
    symbol: str = Query(..., description="Stock symbol"),
    lookback: int = Query(20, ge=5, le=60, description="Lookback days for unusual activity")
):
    """
    Get complete options flow analysis
    
    Returns:
        - Put/Call Ratio (PCR)
        - Premium Flow (money in calls vs puts)
        - Unusual Activity detection
        - Overall signal
        
    Returns None values if data not available
    
    Example:
        GET /indicators/flow/AMZN
    """
    try:
        indicator = get_indicator()
        result = indicator.analyze(symbol.upper(), lookback)
        return OptionsFlowResponse(**result)
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return OptionsFlowResponse(
            symbol=symbol.upper(),
            timestamp=datetime.now().isoformat(),
            put_call_ratio=None,
            put_volume=None,
            call_volume=None,
            pcr_signal=None,
            call_premium=None,
            put_premium=None,
            call_premium_pct=None,
            put_premium_pct=None,
            premium_ratio=None,
            premium_signal=None,
            unusual_call_contracts=None,
            unusual_put_contracts=None,
            unusual_activity_detected=False,
            unusual_signal=None,
            overall_signal=None,
            signal_strength=None,
            interpretation="Error analyzing options flow"
        )


@router.get("/{symbol}/pcr", response_model=PCRResponse)
async def get_put_call_ratio(
    symbol: str = Query(..., description="Stock symbol")
):
    """
    Get Put/Call Ratio only
    
    PCR > 1.0 = More puts (bearish)
    PCR < 0.7 = More calls (bullish)
    
    Returns None if data not available
    
    Example:
        GET /indicators/flow/SPY/pcr
    """
    try:
        indicator = get_indicator()
        result = indicator.analyze(symbol.upper())
        
        return PCRResponse(
            symbol=symbol.upper(),
            put_call_ratio=result["put_call_ratio"],
            call_volume=result["call_volume"],
            put_volume=result["put_volume"],
            signal=result["pcr_signal"],
            timestamp=result["timestamp"]
        )
    except Exception as e:
        logger.error(f"Error getting PCR for {symbol}: {e}")
        return PCRResponse(
            symbol=symbol.upper(),
            put_call_ratio=None,
            call_volume=None,
            put_volume=None,
            signal=None,
            timestamp=datetime.now().isoformat()
        )


@router.get("/{symbol}/premium", response_model=PremiumFlowResponse)
async def get_premium_flow(
    symbol: str = Query(..., description="Stock symbol")
):
    """
    Get Premium Flow only
    
    Shows where money is flowing (calls vs puts)
    Follow the money!
    
    Returns None if data not available
    
    Example:
        GET /indicators/flow/AMZN/premium
    """
    try:
        indicator = get_indicator()
        result = indicator.analyze(symbol.upper())
        
        return PremiumFlowResponse(
            symbol=symbol.upper(),
            call_premium=result["call_premium"],
            put_premium=result["put_premium"],
            call_premium_pct=result["call_premium_pct"],
            put_premium_pct=result["put_premium_pct"],
            premium_ratio=result["premium_ratio"],
            signal=result["premium_signal"],
            timestamp=result["timestamp"]
        )
    except Exception as e:
        logger.error(f"Error getting premium flow for {symbol}: {e}")
        return PremiumFlowResponse(
            symbol=symbol.upper(),
            call_premium=None,
            put_premium=None,
            call_premium_pct=None,
            put_premium_pct=None,
            premium_ratio=None,
            signal=None,
            timestamp=datetime.now().isoformat()
        )


@router.get("/{symbol}/unusual", response_model=UnusualActivityResponse)
async def get_unusual_activity(
    symbol: str = Query(..., description="Stock symbol"),
    lookback: int = Query(20, ge=5, le=60, description="Lookback days")
):
    """
    Get Unusual Activity detection only
    
    Detects large institutional orders and sweeps
    
    Returns None if data not available
    
    Example:
        GET /indicators/flow/TSLA/unusual
    """
    try:
        indicator = get_indicator()
        result = indicator.analyze(symbol.upper(), lookback)
        
        return UnusualActivityResponse(
            symbol=symbol.upper(),
            detected=result["unusual_activity_detected"],
            unusual_call_contracts=result["unusual_call_contracts"],
            unusual_put_contracts=result["unusual_put_contracts"],
            signal=result["unusual_signal"],
            timestamp=result["timestamp"]
        )
    except Exception as e:
        logger.error(f"Error getting unusual activity for {symbol}: {e}")
        return UnusualActivityResponse(
            symbol=symbol.upper(),
            detected=False,
            unusual_call_contracts=None,
            unusual_put_contracts=None,
            signal=None,
            timestamp=datetime.now().isoformat()
        )


# ═══════════════════════════════════════════════════════════════════
# INTEGRATION EXAMPLE
# ═══════════════════════════════════════════════════════════════════

"""
Add to your main.py:

from options_flow_router import router as flow_router
app.include_router(flow_router)

Then use in your trading system:

# Get complete flow analysis
flow = requests.get("http://localhost:8000/indicators/flow/AMZN").json()

if flow["put_call_ratio"] is not None:
    # Check Put/Call Ratio
    if flow["pcr_signal"] == "EXTREME_FEAR_BUY":
        print("Extreme fear - contrarian buy signal")
    
    # Check Premium Flow
    if flow["call_premium_pct"] > 70:
        print("Heavy money flowing into calls - bullish")
    
    # Check Unusual Activity
    if flow["unusual_activity_detected"]:
        print("Institutional activity detected")
    
    # Overall signal
    if flow["overall_signal"] == "BULLISH":
        print("Bullish options flow - institutions buying calls")
else:
    # No options flow data - skip this indicator
    pass

# Or get individual metrics
pcr = requests.get("http://localhost:8000/indicators/flow/SPY/pcr").json()
premium = requests.get("http://localhost:8000/indicators/flow/SPY/premium").json()
unusual = requests.get("http://localhost:8000/indicators/flow/SPY/unusual").json()
"""
