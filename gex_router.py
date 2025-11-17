"""
GEX Router - FastAPI endpoints for Gamma Exposure analysis
Integrates with TradePilot MCP Server
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from gex_calculator import GEXCalculator, GEXProfile, format_gex_summary

load_dotenv()

router = APIRouter(prefix="/gex", tags=["Gamma Exposure (GEX)"])

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
gex_calc = GEXCalculator(POLYGON_API_KEY)


class GEXRequest(BaseModel):
    ticker: str
    min_expiry_days: int = 0
    max_expiry_days: int = 60
    min_oi: int = 100


class GEXLevelResponse(BaseModel):
    strike: float
    call_oi: int
    put_oi: int
    call_gex: float
    put_gex: float
    net_gex: float


class GEXResponse(BaseModel):
    ticker: str
    current_price: float
    net_gex: float
    regime: str
    dealer_positioning: str
    zero_gamma_level: float
    largest_call_wall: float
    largest_put_wall: float
    resistance_levels: List[float]
    support_levels: List[float]
    total_call_gex: float
    total_put_gex: float
    top_10_levels: List[GEXLevelResponse]
    summary: str


@router.post("/analyze", response_model=GEXResponse)
async def analyze_gex(request: GEXRequest):
    """
    Analyze Gamma Exposure for a ticker
    
    Returns complete GEX profile with gamma walls and key levels
    """
    try:
        profile = gex_calc.analyze_ticker(
            ticker=request.ticker,
            min_expiry_days=request.min_expiry_days,
            max_expiry_days=request.max_expiry_days,
            min_oi=request.min_oi
        )
        
        top_10 = [
            GEXLevelResponse(
                strike=level.strike,
                call_oi=level.call_oi,
                put_oi=level.put_oi,
                call_gex=level.call_gex,
                put_gex=level.put_gex,
                net_gex=level.net_gex
            )
            for level in profile.all_levels[:10]
        ]
        
        return GEXResponse(
            ticker=profile.ticker,
            current_price=profile.current_price,
            net_gex=profile.net_gex,
            regime=profile.regime,
            dealer_positioning=profile.dealer_positioning,
            zero_gamma_level=profile.zero_gamma_level,
            largest_call_wall=profile.largest_call_wall.strike,
            largest_put_wall=profile.largest_put_wall.strike,
            resistance_levels=profile.resistance_levels,
            support_levels=profile.support_levels,
            total_call_gex=profile.total_call_gex,
            total_put_gex=profile.total_put_gex,
            top_10_levels=top_10,
            summary=format_gex_summary(profile)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quick/{ticker}")
async def quick_gex(ticker: str):
    """Quick GEX analysis with default parameters"""
    try:
        profile = gex_calc.analyze_ticker(ticker)
        
        return {
            "ticker": ticker,
            "price": profile.current_price,
            "net_gex": f"${profile.net_gex:.2f}M",
            "regime": profile.regime,
            "zero_gamma": f"${profile.zero_gamma_level:.2f}",
            "call_wall": f"${profile.largest_call_wall.strike:.2f}",
            "put_wall": f"${profile.largest_put_wall.strike:.2f}",
            "resistance": [f"${r:.2f}" for r in profile.resistance_levels],
            "support": [f"${s:.2f}" for s in profile.support_levels]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def gex_health():
    """GEX module health check"""
    return {
        "status": "healthy",
        "module": "Gamma Exposure Calculator",
        "api": "Polygon.io",
        "version": "1.0.0"
    }
