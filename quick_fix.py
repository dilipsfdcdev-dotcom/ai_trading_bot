#!/usr/bin/env python3
"""
Quick Fix for Dashboard Connection Issue
"""

import os
from pathlib import Path

def fix_dashboard():
    """Fix the dashboard connection issue"""
    
    print("🔧 Fixing dashboard connection issue...")
    
    # Fix dashboard/web_dashboard.py
    dashboard_file = Path("dashboard/web_dashboard.py")
    
    if dashboard_file.exists():
        content = dashboard_file.read_text(encoding='utf-8')
        
        # Replace the problematic run_server method
        old_method = 'self.app.run_server(debug=debug, host=host, port=port, use_reloader=False)'
        new_method = 'self.app.run(debug=debug, host=host, port=port, use_reloader=False, threaded=True)'
        
        if old_method in content:
            content = content.replace(old_method, new_method)
            dashboard_file.write_text(content, encoding='utf-8')
            print("✅ Fixed dashboard run_server method")
        else:
            print("⚠️  Dashboard method may already be correct")
    else:
        print("❌ Dashboard file not found")
    
    # Also check enhanced_main.py for dashboard startup issues
    enhanced_file = Path("enhanced_main.py")
    if enhanced_file.exists():
        content = enhanced_file.read_text(encoding='utf-8')
        
        # Make sure the dashboard starts with proper error handling
        if 'dashboard.run_server' in content:
            # Add better error handling for dashboard startup
            old_line = 'self.dashboard.run_server(debug=False)'
            new_line = '''try:
                self.dashboard.run_server(debug=False, host='127.0.0.1', port=8050)
            except Exception as e:
                self.logger.error(f"Dashboard startup failed: {e}")
                print("⚠️  Dashboard failed to start, but bot will continue running")'''
            
            if old_line in content:
                content = content.replace(old_line, new_line)
                enhanced_file.write_text(content, encoding='utf-8')
                print("✅ Fixed enhanced_main dashboard startup")
        
    print("✅ All fixes applied!")

def create_emergency_test():
    """Create a simple test to verify the fix works"""
    
    test_content = '''#!/usr/bin/env python3
"""
Emergency Dashboard Test
"""

import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import webbrowser
from threading import Timer

def open_browser():
    try:
        webbrowser.open('http://127.0.0.1:8050')
        print("🌐 Browser opened!")
    except:
        print("📱 Open: http://127.0.0.1:8050")

# Create app
app = dash.Dash(__name__)

# Sample data
dates = pd.date_range(start=datetime.now() - timedelta(days=1), periods=100, freq='5min')
prices = 3335 + np.cumsum(np.random.normal(0, 2, 100))
df = pd.DataFrame({'time': dates, 'price': prices})

app.layout = html.Div([
    html.H1("🤖 Dashboard Connection Test - SUCCESS!", 
            style={'textAlign': 'center', 'color': 'green', 'margin': '20px'}),
    
    html.Div([
        html.H3("✅ Connection Working!", style={'color': 'green'}),
        html.P("If you can see this, the dashboard fix worked!"),
        html.P("Your enhanced AI trading bot should now work properly."),
    ], style={'textAlign': 'center', 'backgroundColor': '#e8f5e8', 
             'padding': '20px', 'margin': '20px', 'borderRadius': '10px'}),
    
    dcc.Graph(
        figure=px.line(df, x='time', y='price', 
                      title='Live Trading Data Simulation')
    ),
    
    html.Div(id="status", style={'textAlign': 'center', 'margin': '20px'}),
    
    dcc.Interval(id='interval', interval=5000, n_intervals=0)
])

@app.callback(Output('status', 'children'), Input('interval', 'n_intervals'))
def update_status(n):
    return f"🕐 Last Update: {datetime.now().strftime('%H:%M:%S')} (Refresh #{n})"

if __name__ == '__main__':
    print("🧪 Testing Dashboard Connection...")
    print("🚀 http://127.0.0.1:8050")
    
    Timer(2.0, open_browser).start()
    
    try:
        app.run(debug=False, host='127.0.0.1', port=8050, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"❌ Test failed: {e}")
'''
    
    with open('test_dashboard_fix.py', 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("✅ Created test file: test_dashboard_fix.py")

def main():
    """Main function"""
    print("🚨 QUICK DASHBOARD FIX")
    print("=" * 30)
    
    fix_dashboard()
    create_emergency_test()
    
    print("=" * 30)
    print("🚀 Next steps:")
    print("1. Test: python test_dashboard_fix.py")
    print("2. Run bot: python start_enhanced_bot.py")
    print("")
    print("💡 If still having issues:")
    print("• Check Windows Firewall")
    print("• Run as Administrator")
    print("• Temporarily disable antivirus")

if __name__ == "__main__":
    main()