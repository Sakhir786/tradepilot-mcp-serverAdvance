"""
FastAPI Router for Options Greeks Analyzer
Endpoints for TradePilot Engine
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict
from options_greeks import OptionsGreeksAnalyzer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/greeks", tags=["Options Greeks"])

# Initialize analyzer
analyzer = OptionsGreeksAnalyzer()


class GreeksResponse(BaseModel):
    """Response model for Greeks"""
    symbol: str
    timestamp: str
    current_price: float
    atm_strike: float
    call_greeks: Dict
    put_greeks: Dict
    implied_volatility: Dict


class PortfolioPosition(BaseModel):
    """Position for portfolio Greeks calculation"""
    symbol: str
    strike: float
    type: str  # "call" or "put"
    quantity: int  # Positive for long, negative for short


class PortfolioGreeksRequest(BaseModel):
    """Request model for portfolio Greeks"""
    positions: List[PortfolioPosition]


@router.get("/{symbol}", response_model=GreeksResponse)
async def get_atm_greeks(
    symbol: str,
    current_price: Optional[float] = None
):
    """
    Get At-The-Money (ATM) options Greeks
    
    **ATM Greeks are the most important for trading:**
    - Highest gamma (most sensitive to price changes)
    - Best proxy for overall market sentiment
    - Most liquid options
    
    **Greeks Explained:**
    - **Delta**: Price sensitivity (0-1 for calls, -1-0 for puts)
    - **Gamma**: Rate of delta change (higher = more risk)
    - **Theta**: Time decay per day (always negative for long options)
    - **Vega**: IV sensitivity (higher = more IV exposure)
    - **Rho**: Interest rate sensitivity (usually minimal)
    
    **Example:**
    ```
    GET /greeks/SPY
    GET /greeks/AAPL?current_price=230.50
    ```
    """
    try:
        logger.info(f"Greeks request for {symbol}")
        
        result = analyzer.get_atm_greeks(
            symbol=symbol.upper(),
            current_price=current_price
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Could not get Greeks for {symbol}. Check if symbol has active options."
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in greeks endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio")
async def calculate_portfolio_greeks(
    request: PortfolioGreeksRequest = Body(...)
):
    """
    Calculate portfolio-level Greeks
    
    **Aggregate Greeks across multiple positions**
    
    Perfect for:
    - Risk management
    - Portfolio hedging
    - Delta-neutral strategies
    - Position sizing
    
    **Request Body:**
    ```json
    {
        "positions": [
            {"symbol": "SPY", "strike": 580, "type": "call", "quantity": 10},
            {"symbol": "SPY", "strike": 575, "type": "put", "quantity": -5},
            {"symbol": "AAPL", "strike": 230, "type": "call", "quantity": 20}
        ]
    }
    ```
    
    **Returns:**
    - Aggregated portfolio Greeks
    - Greek regime classification
    - Position-by-position breakdown
    """
    try:
        logger.info(f"Portfolio Greeks request for {len(request.positions)} positions")
        
        # Convert Pydantic models to dicts
        positions = [pos.dict() for pos in request.positions]
        
        result = analyzer.get_portfolio_greeks(positions)
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Could not calculate portfolio Greeks"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in portfolio greeks endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/delta")
async def get_delta_only(symbol: str):
    """Get just Delta (quick endpoint for delta-neutral strategies)"""
    try:
        result = analyzer.get_atm_greeks(symbol.upper())
        if not result:
            raise HTTPException(status_code=404, detail=f"Could not get Greeks for {symbol}")
        
        return {
            "symbol": result["symbol"],
            "call_delta": result["call_greeks"]["delta"],
            "put_delta": result["put_greeks"]["delta"],
            "atm_strike": result["atm_strike"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delta endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/gamma")
async def get_gamma_only(symbol: str):
    """Get just Gamma (quick endpoint for gamma scalping)"""
    try:
        result = analyzer.get_atm_greeks(symbol.upper())
        if not result:
            raise HTTPException(status_code=404, detail=f"Could not get Greeks for {symbol}")
        
        return {
            "symbol": result["symbol"],
            "call_gamma": result["call_greeks"]["gamma"],
            "put_gamma": result["put_greeks"]["gamma"],
            "atm_strike": result["atm_strike"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in gamma endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/theta")
async def get_theta_only(symbol: str):
    """Get just Theta (quick endpoint for theta decay strategies)"""
    try:
        result = analyzer.get_atm_greeks(symbol.upper())
        if not result:
            raise HTTPException(status_code=404, detail=f"Could not get Greeks for {symbol}")
        
        return {
            "symbol": result["symbol"],
            "call_theta": result["call_greeks"]["theta"],
            "put_theta": result["put_greeks"]["theta"],
            "daily_decay": abs(result["call_greeks"]["theta"]) + abs(result["put_greeks"]["theta"]),
            "atm_strike": result["atm_strike"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in theta endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Options Greeks Analyzer",
        "version": "1.0.0"
    }
