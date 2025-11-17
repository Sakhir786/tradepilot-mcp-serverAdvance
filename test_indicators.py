"""
Test script for Max Pain and Greeks calculators
Run this to verify everything works before integration
"""

import os
import logging
from max_pain_calculator import MaxPainCalculator
from options_greeks import OptionsGreeksAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_max_pain():
    """Test Max Pain Calculator"""
    print("\n" + "="*70)
    print("🎯 TESTING MAX PAIN CALCULATOR")
    print("="*70)
    
    calc = MaxPainCalculator()
    
    # Test with SPY
    print("\nTesting SPY...")
    result = calc.calculate_max_pain("SPY")
    
    if result:
        print("✅ SUCCESS!")
        print(f"\nSymbol: {result['symbol']}")
        print(f"Expiration: {result['expiration']}")
        print(f"Current Price: ${result['current_price']}")
        print(f"Max Pain Strike: ${result['max_pain_strike']}")
        print(f"Distance: ${result['distance_to_max_pain']} ({result['distance_pct']}%)")
        print(f"Bias: {result['bias']}")
        print(f"Signal: {result['signal']}")
        print(f"Put/Call OI Ratio: {result['put_call_oi_ratio']}")
        print(f"Strikes Analyzed: {result['strikes_analyzed']}")
    else:
        print("❌ FAILED - Could not calculate Max Pain")
        print("Check:")
        print("  1. POLYGON_API_KEY is set")
        print("  2. API key is valid")
        print("  3. Symbol has active options")
    
    print("="*70)
    return result is not None


def test_greeks():
    """Test Options Greeks Analyzer"""
    print("\n" + "="*70)
    print("🎯 TESTING OPTIONS GREEKS ANALYZER")
    print("="*70)
    
    analyzer = OptionsGreeksAnalyzer()
    
    # Test ATM Greeks
    print("\nTesting ATM Greeks for SPY...")
    result = analyzer.get_atm_greeks("SPY")
    
    if result:
        print("✅ SUCCESS!")
        print(f"\nSymbol: {result['symbol']}")
        print(f"Current Price: ${result['current_price']}")
        print(f"ATM Strike: ${result['atm_strike']}")
        print("\nCall Greeks:")
        print(f"  Delta: {result['call_greeks']['delta']}")
        print(f"  Gamma: {result['call_greeks']['gamma']}")
        print(f"  Theta: {result['call_greeks']['theta']}")
        print(f"  Vega: {result['call_greeks']['vega']}")
        print(f"  Rho: {result['call_greeks']['rho']}")
        print("\nPut Greeks:")
        print(f"  Delta: {result['put_greeks']['delta']}")
        print(f"  Gamma: {result['put_greeks']['gamma']}")
        print(f"  Theta: {result['put_greeks']['theta']}")
        print(f"  Vega: {result['put_greeks']['vega']}")
        print(f"  Rho: {result['put_greeks']['rho']}")
        print("\nImplied Volatility:")
        print(f"  Call IV: {result['implied_volatility']['call']}")
        print(f"  Put IV: {result['implied_volatility']['put']}")
    else:
        print("❌ FAILED - Could not get Greeks")
        print("Check:")
        print("  1. POLYGON_API_KEY is set")
        print("  2. API key is valid")
        print("  3. Symbol has active options")
    
    # Test Portfolio Greeks
    print("\n" + "-"*70)
    print("Testing Portfolio Greeks...")
    print("-"*70)
    
    test_positions = [
        {"symbol": "SPY", "strike": 580, "type": "call", "quantity": 10},
        {"symbol": "SPY", "strike": 575, "type": "put", "quantity": -5}
    ]
    
    portfolio = analyzer.get_portfolio_greeks(test_positions)
    
    if portfolio:
        print("✅ SUCCESS!")
        print("\nPortfolio Greeks:")
        print(f"  Delta: {portfolio['portfolio_greeks']['delta']}")
        print(f"  Gamma: {portfolio['portfolio_greeks']['gamma']}")
        print(f"  Theta: {portfolio['portfolio_greeks']['theta']}")
        print(f"  Vega: {portfolio['portfolio_greeks']['vega']}")
        print(f"  Rho: {portfolio['portfolio_greeks']['rho']}")
        print("\nRegime:")
        print(f"  Delta: {portfolio['regime']['delta']}")
        print(f"  Gamma: {portfolio['regime']['gamma']}")
        print(f"  Theta: {portfolio['regime']['theta']}")
    else:
        print("❌ FAILED - Could not calculate portfolio Greeks")
    
    print("="*70)
    return result is not None


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🚀 MAX PAIN + GREEKS CALCULATOR TEST SUITE")
    print("="*70)
    
    # Check API key
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        print("\n❌ ERROR: POLYGON_API_KEY not set!")
        print("\nSet it with:")
        print("  export POLYGON_API_KEY='your_key_here'")
        return
    
    print(f"\n✅ API Key found: {api_key[:10]}...")
    
    # Run tests
    max_pain_ok = test_max_pain()
    greeks_ok = test_greeks()
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Max Pain Calculator: {'✅ PASS' if max_pain_ok else '❌ FAIL'}")
    print(f"Options Greeks: {'✅ PASS' if greeks_ok else '❌ FAIL'}")
    
    if max_pain_ok and greeks_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYou're ready to integrate into TradePilot Engine!")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("\nCheck the error messages above and:")
        print("  1. Verify POLYGON_API_KEY is valid")
        print("  2. Test during market hours")
        print("  3. Use high-volume symbols (SPY, QQQ)")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
