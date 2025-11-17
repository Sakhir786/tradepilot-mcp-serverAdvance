"""
FastAPI Router for Max Pain Calculator
Endpoints for TradePilot Engine
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from max_pain_calculator import MaxPainCalculator
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/max-pain", tags=["Max Pain"])

# Initialize calculator
calculator = MaxPainCalculator()


class MaxPainResponse(BaseModel):
    """Response model for Max Pain analysis"""
    symbol: str
    timestamp: str
    expiration: str
    current_price: float
    max_pain_strike: float
    distance_to_max_pain: float
    distance_pct: float
    max_pain_value: float
    bias: str
    signal: str
    total_call_oi: int
    total_put_oi: int
    put_call_oi_ratio: float
    strikes_analyzed: int


@router.get("/{symbol}", response_model=MaxPainResponse)
async def get_max_pain(
    symbol: str,
    current_price: Optional[float] = Query(None, description="Current stock price (auto-fetched if not provided)"),
    expiration_date: Optional[str] = Query(None, description="Target expiration date (YYYY-MM-DD, uses nearest Friday if not provided)")
):
    """
    Calculate Max Pain for a symbol
    
    **Max Pain Theory:**
    Options market makers manipulate price toward the strike where
    most options expire worthless, maximizing their profit.
    
    **Returns:**
    - Max Pain strike price
    - Distance from current price
    - Bias (BULLISH/BEARISH/NEUTRAL)
    - Signal (CALLS/PUTS/WAIT)
    - Put/Call OI ratio
    
    **Example:**
    ```
    GET /max-pain/SPY
    GET /max-pain/AAPL?current_price=230.50
    GET /max-pain/TSLA?expiration_date=2025-01-17
    ```
    """
    try:
        logger.info(f"Max Pain request for {symbol}")
        
        result = calculator.calculate_max_pain(
            symbol=symbol.upper(),
            current_price=current_price,
            expiration_date=expiration_date
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Could not calculate Max Pain for {symbol}. Check if symbol has active options."
            )
        
        # Remove full pain_by_strike breakdown from API response (too large)
        # Keep it in full calculation if needed
        result.pop("pain_by_strike", None)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in max pain endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/bias")
async def get_max_pain_bias(
    symbol: str,
    current_price: Optional[float] = None
):
    """
    Get just the Max Pain bias and signal
    
    **Quick endpoint for trading decisions**
    
    Returns:
    - BULLISH/BEARISH/NEUTRAL bias
    - CALLS/PUTS/WAIT signal
    - Distance to max pain
    """
    try:
        result = calculator.calculate_max_pain(symbol.upper(), current_price)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Could not calculate Max Pain for {symbol}")
        
        return {
            "symbol": result["symbol"],
            "bias": result["bias"],
            "signal": result["signal"],
            "distance_to_max_pain": result["distance_to_max_pain"],
            "distance_pct": result["distance_pct"],
            "max_pain_strike": result["max_pain_strike"],
            "current_price": result["current_price"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bias endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/strikes")
async def get_pain_by_strike(
    symbol: str,
    current_price: Optional[float] = None,
    expiration_date: Optional[str] = None
):
    """
    Get full pain breakdown by strike price
    
    **For advanced analysis and charting**
    
    Returns pain levels for all strikes in the chain
    """
    try:
        result = calculator.calculate_max_pain(
            symbol.upper(),
            current_price,
            expiration_date
        )
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Could not calculate Max Pain for {symbol}")
        
        return {
            "symbol": result["symbol"],
            "expiration": result["expiration"],
            "max_pain_strike": result["max_pain_strike"],
            "pain_by_strike": result["pain_by_strike"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in strikes endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Max Pain Calculator",
        "version": "1.0.0"
    }
