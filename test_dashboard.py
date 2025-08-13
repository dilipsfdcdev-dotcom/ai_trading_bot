#!/usr/bin/env python3
"""
Dashboard Test and Fix
Tests if dashboard can start and fixes common issues
"""

import sys
import subprocess
import time
import webbrowser
from threading import Timer

def test_dash_installation():
    """Test if Dash is properly installed"""
    print("🧪 Testing Dash installation...")
    
    try:
        import dash
        from dash import dcc, html
        print(f"✅ Dash version: {dash.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Dash not available: {e}")
        print("📦 Installing Dash...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "dash", "plotly"], check=True)
            print("✅ Dash installed successfully")
            return True
        except Exception as install_error:
            print(f"❌ Failed to install Dash: {install_error}")
            return False

def create_simple_test_dashboard():
    """Create a simple test dashboard"""
    
    test_content = '''#!/usr/bin/env python3
"""
Simple Dashboard Test
"""

try:
    import dash
    from dash import dcc, html, Input, Output
    import plotly.express as px
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    print("📊 Starting Simple Test Dashboard...")
    
    # Create app
    app = dash.Dash(__name__)
    
    # Generate sample data
    dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='H')
    prices = 2650 + np.cumsum(np.random.normal(0, 10, len(dates)))
    df = pd.DataFrame({'date': dates, 'price': prices})
    
    # Layout
    app.layout = html.Div([
        html.H1("🤖 AI Trading Bot - Test Dashboard", 
                style={'textAlign': 'center', 'color': 'green', 'marginBottom': '30px'}),
        
        html.Div([
            html.H3("✅ Dashboard is working!", style={'color': 'green'}),
            html.P("If you can see this, the dashboard server is running correctly."),
            html.Hr(),
        ], style={'textAlign': 'center', 'margin': '20px'}),
        
        html.Div([
            html.Div([
                html.H4("💰 Balance", style={'color': '#2c3e50'}),
                html.H2("$100,000", style={'color': '#27ae60'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 
                     'borderRadius': '10px', 'margin': '10px', 'width': '200px', 'display': 'inline-block'}),
            
            html.Div([
                html.H4("📈 Signals", style={'color': '#2c3e50'}),
                html.H2("5 Active", style={'color': '#3498db'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 
                     'borderRadius': '10px', 'margin': '10px', 'width': '200px', 'display': 'inline-block'}),
            
            html.Div([
                html.H4("🎯 Accuracy", style={'color': '#2c3e50'}),
                html.H2("78%", style={'color': '#e74c3c'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 
                     'borderRadius': '10px', 'margin': '10px', 'width': '200px', 'display': 'inline-block'})
        ], style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        # Chart
        dcc.Graph(
            figure=px.line(df, x='date', y='price', 
                          title='Sample Trading Data (Demo)',
                          labels={'price': 'Price ($)', 'date': 'Time'})
        ),
        
        html.Div([
            html.H3("📝 Test Results:"),
            html.Ul([
                html.Li("✅ Dash framework working"),
                html.Li("✅ Plotly charts working"), 
                html.Li("✅ Web server running"),
                html.Li("✅ Browser can connect"),
                html.Li("🚀 Ready for full AI dashboard!")
            ])
        ], style={'margin': '30px', 'padding': '20px', 'backgroundColor': '#e8f5e8', 'borderRadius': '10px'}),
        
        # Auto-refresh
        dcc.Interval(
            id='interval-component',
            interval=5*1000,  # Update every 5 seconds
            n_intervals=0
        )
    ], style={'fontFamily': 'Arial, sans-serif', 'margin': '20px'})
    
    # Callback for updates
    @app.callback(
        Output('interval-component', 'n_intervals'),
        Input('interval-component', 'n_intervals')
    )
    def update_data(n):
        return n
    
    # Run server
    if __name__ == '__main__':
        print("🚀 Test Dashboard URL: http://127.0.0.1:8050")
        print("✅ If this works, your dashboard setup is correct!")
        print("🔄 Press Ctrl+C to stop")
        
        try:
            app.run_server(debug=True, host='127.0.0.1', port=8050, use_reloader=False)
        except Exception as e:
            print(f"❌ Dashboard failed to start: {e}")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📦 Please install: pip install dash plotly pandas numpy")
except Exception as e:
    print(f"❌ Error: {e}")
'''
    
    with open('test_simple_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("✅ Created test_simple_dashboard.py")

def test_port_availability():
    """Test if ports are available"""
    import socket
    
    ports_to_test = [8050, 8051, 8052]
    available_ports = []
    
    print("🔍 Testing port availability...")
    
    for port in ports_to_test:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('127.0.0.1', port))
            if result != 0:
                available_ports.append(port)
                print(f"✅ Port {port}: Available")
            else:
                print(f"❌ Port {port}: In use")
        except Exception as e:
            print(f"⚠️  Port {port}: Error testing - {e}")
        finally:
            sock.close()
    
    if available_ports:
        print(f"🎯 Recommended port: {available_ports[0]}")
        return available_ports[0]
    else:
        print("⚠️  All common ports in use")
        return 8050

def check_firewall_and_antivirus():
    """Check for common firewall/antivirus issues"""
    print("🛡️  Firewall/Antivirus Check:")
    print("   • Windows Defender might be blocking the connection")
    print("   • Corporate firewall might restrict local servers")
    print("   • Antivirus might scan/block Python web servers")
    print("   • VPN might interfere with localhost connections")
    print()
    print("💡 Solutions:")
    print("   1. Temporarily disable antivirus")
    print("   2. Add Python to firewall exceptions")
    print("   3. Try different ports (8052, 8053)")
    print("   4. Run as administrator")

def create_flask_fallback():
    """Create a simple Flask fallback dashboard"""
    
    flask_content = '''#!/usr/bin/env python3
"""
Simple Flask Dashboard Fallback
"""

try:
    from flask import Flask, render_template_string
    import webbrowser
    from threading import Timer
    
    app = Flask(__name__)
    
    @app.route('/')
    def dashboard():
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Trading Bot - Simple Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { text-align: center; color: #2c3e50; margin-bottom: 40px; }
                .metrics { display: flex; justify-content: space-around; margin-bottom: 40px; }
                .metric-card { background: white; padding: 20px; border-radius: 10px; 
                             box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
                .status { background: #e8f5e8; padding: 20px; border-radius: 10px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 AI Trading Bot Dashboard</h1>
                    <p>Simple Flask Fallback Version</p>
                </div>
                
                <div class="metrics">
                    <div class="metric-card">
                        <h3>💰 Balance</h3>
                        <h2 style="color: #27ae60;">$100,000</h2>
                    </div>
                    <div class="metric-card">
                        <h3>📊 Signals</h3>
                        <h2 style="color: #3498db;">5 Active</h2>
                    </div>
                    <div class="metric-card">
                        <h3>🎯 Accuracy</h3>
                        <h2 style="color: #e74c3c;">78%</h2>
                    </div>
                </div>
                
                <div class="status">
                    <h3>✅ Dashboard Status</h3>
                    <ul>
                        <li>✅ Flask server running</li>
                        <li>✅ Web interface accessible</li>
                        <li>✅ No dependency issues</li>
                        <li>🚀 Ready for full dashboard upgrade!</li>
                    </ul>
                </div>
                
                <script>
                    // Auto-refresh every 30 seconds
                    setTimeout(function(){ location.reload(); }, 30000);
                </script>
            </div>
        </body>
        </html>
        """
        return render_template_string(html_template)
    
    def open_browser():
        webbrowser.open('http://127.0.0.1:5000')
    
    if __name__ == '__main__':
        print("🚀 Flask Dashboard: http://127.0.0.1:5000")
        Timer(2.0, open_browser).start()
        app.run(debug=False, host='127.0.0.1', port=5000)

except ImportError:
    print("❌ Flask not available")
    print("📦 Install with: pip install flask")
'''
    
    with open('flask_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(flask_content)
    
    print("✅ Created flask_dashboard.py (simple fallback)")

def open_browser_test():
    """Open browser to test if it can connect"""
    try:
        webbrowser.open('http://127.0.0.1:8050')
        print("🌐 Browser opened to test dashboard")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")

def main():
    """Main test function"""
    print("🧪 Dashboard Connection Test & Fix")
    print("=" * 40)
    
    # Test Dash installation
    if not test_dash_installation():
        return
    
    # Test port availability
    available_port = test_port_availability()
    
    # Create test files
    create_simple_test_dashboard()
    create_flask_fallback()
    
    print("=" * 40)
    print("🔧 Troubleshooting Steps:")
    print()
    print("1. 🧪 Test simple dashboard:")
    print("   python test_simple_dashboard.py")
    print()
    print("2. 🔄 If that fails, try Flask version:")
    print("   python flask_dashboard.py")
    print()
    print("3. 🔍 Check for issues:")
    check_firewall_and_antivirus()
    print()
    print("4. 📱 Manual browser test:")
    print("   Start dashboard, then go to: http://127.0.0.1:8050")
    print()
    print("💡 Most likely issues:")
    print("   • Antivirus blocking local server")
    print("   • Port already in use")
    print("   • Dash not properly installed")
    print("   • Firewall blocking Python")

if __name__ == "__main__":
    main()