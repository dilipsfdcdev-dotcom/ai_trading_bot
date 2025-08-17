#!/usr/bin/env python3
"""
Fix Indentation Error in enhanced_main.py
"""

import os
from pathlib import Path

def fix_enhanced_main():
    """Fix the indentation error in enhanced_main.py"""
    
    enhanced_file = Path("enhanced_main.py")
    
    if not enhanced_file.exists():
        print("❌ enhanced_main.py not found")
        return False
    
    try:
        content = enhanced_file.read_text(encoding='utf-8')
        
        # Find and fix the broken try block around line 314-315
        lines = content.split('\n')
        
        # Look for the problematic lines
        for i, line in enumerate(lines):
            if 'try:' in line and 'dashboard.run_server' in lines[i+1] if i+1 < len(lines) else False:
                # Fix the indentation
                lines[i] = '        try:'  # Proper indentation for try
                lines[i+1] = '            self.dashboard.run_server(debug=False, host=\'127.0.0.1\', port=8050)'
                
                # Add the except block if not present
                if i+2 < len(lines) and 'except' not in lines[i+2]:
                    lines.insert(i+2, '        except Exception as e:')
                    lines.insert(i+3, '            self.logger.error(f"Dashboard startup failed: {e}")')
                    lines.insert(i+4, '            print("⚠️  Dashboard failed to start, but bot will continue running")')
                
                break
        
        # Write back the fixed content
        fixed_content = '\n'.join(lines)
        enhanced_file.write_text(fixed_content, encoding='utf-8')
        
        print("✅ Fixed indentation error in enhanced_main.py")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing enhanced_main.py: {e}")
        return False

def create_simple_fix():
    """Create a simple replacement for the dashboard startup section"""
    
    enhanced_file = Path("enhanced_main.py")
    
    if not enhanced_file.exists():
        print("❌ enhanced_main.py not found")
        return False
    
    try:
        content = enhanced_file.read_text(encoding='utf-8')
        
        # Replace the entire problematic dashboard startup section
        old_section = '''try:
                self.dashboard.run_server(debug=False, host='127.0.0.1', port=8050)
            except Exception as e:
                self.logger.error(f"Dashboard startup failed: {e}")
                print("⚠️  Dashboard failed to start, but bot will continue running")'''
        
        new_section = '''        try:
            self.dashboard.run_server(debug=False, host='127.0.0.1', port=8050)
        except Exception as e:
            self.logger.error(f"Dashboard startup failed: {e}")
            print("⚠️  Dashboard failed to start, but bot will continue running")'''
        
        if old_section in content:
            content = content.replace(old_section, new_section)
        else:
            # Alternative approach - replace just the dashboard line
            content = content.replace(
                'self.dashboard.run_server(debug=False)',
                'self.dashboard.run_server(debug=False, host="127.0.0.1", port=8050)'
            )
        
        enhanced_file.write_text(content, encoding='utf-8')
        print("✅ Fixed dashboard startup in enhanced_main.py")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing enhanced_main.py: {e}")
        return False

def create_clean_enhanced_main():
    """Create a clean version of the dashboard startup method"""
    
    enhanced_file = Path("enhanced_main.py")
    
    if not enhanced_file.exists():
        print("❌ enhanced_main.py not found")
        return False
    
    try:
        content = enhanced_file.read_text(encoding='utf-8')
        
        # Find the start_dashboard method and replace it
        lines = content.split('\n')
        new_lines = []
        in_start_dashboard = False
        indent_level = 0
        
        for line in lines:
            if 'def start_dashboard(self):' in line:
                in_start_dashboard = True
                indent_level = len(line) - len(line.lstrip())
                new_lines.append(line)
                new_lines.append(' ' * (indent_level + 4) + '"""Start the dashboard in a separate thread"""')
                new_lines.append(' ' * (indent_level + 4) + 'def run_dashboard():')
                new_lines.append(' ' * (indent_level + 8) + 'try:')
                new_lines.append(' ' * (indent_level + 12) + 'self.dashboard.run_server(debug=False, host="127.0.0.1", port=8050)')
                new_lines.append(' ' * (indent_level + 8) + 'except Exception as e:')
                new_lines.append(' ' * (indent_level + 12) + 'self.logger.error(f"Dashboard error: {e}")')
                new_lines.append(' ' * (indent_level + 12) + 'print("⚠️  Dashboard failed to start")')
                new_lines.append('')
                new_lines.append(' ' * (indent_level + 4) + 'dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)')
                new_lines.append(' ' * (indent_level + 4) + 'dashboard_thread.start()')
                new_lines.append(' ' * (indent_level + 4) + 'self.logger.info("📊 Dashboard started at http://127.0.0.1:8050")')
                continue
            elif in_start_dashboard and line.strip() == '' and len(new_lines) > 0 and new_lines[-1].strip() != '':
                in_start_dashboard = False
                new_lines.append(line)
            elif in_start_dashboard:
                # Skip the old dashboard method content
                continue
            else:
                new_lines.append(line)
        
        # Write the fixed content
        fixed_content = '\n'.join(new_lines)
        enhanced_file.write_text(fixed_content, encoding='utf-8')
        
        print("✅ Created clean dashboard startup method")
        return True
        
    except Exception as e:
        print(f"❌ Error creating clean method: {e}")
        return False

def quick_fix():
    """Quick and dirty fix - just remove the problematic lines"""
    
    enhanced_file = Path("enhanced_main.py")
    
    if not enhanced_file.exists():
        print("❌ enhanced_main.py not found")
        return False
    
    try:
        content = enhanced_file.read_text(encoding='utf-8')
        
        # Remove problematic lines and replace with simple version
        lines = content.split('\n')
        new_lines = []
        
        skip_next = 0
        for i, line in enumerate(lines):
            if skip_next > 0:
                skip_next -= 1
                continue
                
            # Look for the problematic try block
            if 'try:' in line and i + 1 < len(lines) and 'dashboard.run_server' in lines[i + 1]:
                # Replace with simple version
                indent = len(line) - len(line.lstrip())
                new_lines.append(' ' * indent + 'try:')
                new_lines.append(' ' * (indent + 4) + 'self.dashboard.run_server(debug=False, host="127.0.0.1", port=8050)')
                new_lines.append(' ' * indent + 'except Exception as e:')
                new_lines.append(' ' * (indent + 4) + 'self.logger.error(f"Dashboard error: {e}")')
                
                # Skip the next few problematic lines
                skip_next = 3
            else:
                new_lines.append(line)
        
        # Write the fixed content
        fixed_content = '\n'.join(new_lines)
        enhanced_file.write_text(fixed_content, encoding='utf-8')
        
        print("✅ Applied quick fix to enhanced_main.py")
        return True
        
    except Exception as e:
        print(f"❌ Quick fix failed: {e}")
        return False

def main():
    """Main fix function"""
    print("🔧 FIXING INDENTATION ERROR")
    print("=" * 30)
    
    # Try different fix approaches
    if quick_fix():
        print("✅ Quick fix applied successfully!")
    elif create_simple_fix():
        print("✅ Simple fix applied successfully!")
    elif fix_enhanced_main():
        print("✅ Enhanced fix applied successfully!")
    else:
        print("❌ All fix attempts failed")
        return False
    
    print("=" * 30)
    print("🚀 Try running your bot now:")
    print("python start_enhanced_bot.py")

if __name__ == "__main__":
    main()