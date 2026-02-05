"""
Launcher script for PyInstaller executable.
This wraps app.py and handles browser opening + clean shutdown.
"""
import sys
import os
import threading
import webbrowser
import time

# Handle PyInstaller paths
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    # _MEIPASS is injected by PyInstaller at runtime
    BASE_DIR: str = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    os.chdir(os.path.dirname(sys.executable))
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add base directory to path
sys.path.insert(0, BASE_DIR)

def open_browser(port=5000, delay=2):
    """Open browser after a short delay to let server start."""
    time.sleep(delay)
    webbrowser.open(f'http://localhost:{port}')

def main():
    port = 5000
    
    # Start browser opener in background thread
    browser_thread = threading.Thread(target=open_browser, args=(port, 2))
    browser_thread.daemon = True
    browser_thread.start()
    
    # Import and run Flask app
    from app import app
    
    print("\n" + "="*50)
    print("  HYPERTROPHY TOOLBOX")
    print("="*50)
    print(f"\n  Server running at: http://localhost:{port}")
    print("  Browser will open automatically...")
    print("\n  Press Ctrl+C to stop the server")
    print("="*50 + "\n")
    
    try:
        # Run Flask with threading enabled for better performance
        app.run(
            host='127.0.0.1',
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)

if __name__ == '__main__':
    main()
