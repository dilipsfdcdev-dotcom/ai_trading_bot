#!/usr/bin/env python3
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
