"""
GEX Module Test Script
Tests GEX calculator independently
"""

import os
from dotenv import load_dotenv
from gex_calculator import GEXCalculator, format_gex_summary

load_dotenv()

def test_gex():
    """Test GEX analysis"""
    print("="*70)
    print("TESTING GEX MODULE")
    print("="*70)
    
    API_KEY = os.getenv("POLYGON_API_KEY")
    
    if not API_KEY:
        print("ERROR: POLYGON_API_KEY not set")
        print("Please add your API key to .env file")
        return
    
    print(f"API Key loaded: {API_KEY[:10]}...")
    
    calculator = GEXCalculator(API_KEY)
    
    print("\nAnalyzing AAPL gamma exposure...")
    print("This may take 30-60 seconds (fetching options data)...\n")
    
    try:
        profile = calculator.analyze_ticker("AAPL", max_expiry_days=45)
        
        print(format_gex_summary(profile))
        
        print("\nTOP 10 GEX LEVELS:")
        print(f"{'Strike':<10} {'Call OI':<10} {'Put OI':<10} {'Net GEX':<12} {'Type'}")
        print("="*60)
        
        for level in profile.all_levels[:10]:
            gex_type = "CALL WALL" if level.call_gex > abs(level.put_gex) else "PUT WALL"
            print(f"${level.strike:<9.2f} {level.call_oi:<10} {level.put_oi:<10} ${level.net_gex:<11.2f} {gex_type}")
        
        print("\n" + "="*70)
        print("GEX ANALYSIS COMPLETE!")
        print("="*70)
        print(f"Net GEX: ${profile.net_gex:.2f}M")
        print(f"Regime: {profile.regime}")
        print(f"Call Wall: ${profile.largest_call_wall.strike:.2f}")
        print(f"Put Wall: ${profile.largest_put_wall.strike:.2f}")
        print(f"Zero Gamma: ${profile.zero_gamma_level:.2f}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gex()
