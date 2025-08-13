#!/usr/bin/env python3
"""
Simple test to verify AI dependencies
"""

def test_dependencies():
    """Test if AI packages are installed"""
    
    packages = {
        'dash': 'Dash web framework',
        'plotly': 'Plotly charts',
        'openai': 'OpenAI API (optional)',
        'anthropic': 'Anthropic API (optional)'
    }
    
    print("🧪 Testing AI Dependencies")
    print("=" * 30)
    
    all_good = True
    
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"✅ {package}: {description}")
        except ImportError:
            if package in ['openai', 'anthropic']:
                print(f"⚠️  {package}: {description} (optional)")
            else:
                print(f"❌ {package}: {description} (required)")
                all_good = False
    
    print("=" * 30)
    if all_good:
        print("✅ All required dependencies installed!")
        print("🚀 Ready to run AI bot!")
    else:
        print("❌ Some dependencies missing")
        print("📦 Run: pip install dash plotly")
    
    return all_good

if __name__ == "__main__":
    test_dependencies()
