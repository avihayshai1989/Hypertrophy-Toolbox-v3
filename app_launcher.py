"""
Launcher script for PyInstaller executable.
This wraps app.py and handles browser opening + clean shutdown.
"""
import sys
import os
import threading
import webbrowser
import time
import traceback


def show_error_and_wait(title: str, message: str, details: str | None = None) -> None:
    """Show error and wait for user input before closing."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)
    print(f"\n  {message}")
    if details:
        print(f"\n  Details: {details}")
    print("\n" + "="*60)
    print("  Press Enter to close this window...")
    try:
        input()
    except Exception:
        pass
    sys.exit(1)

# Handle PyInstaller paths
try:
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
except Exception as e:
    show_error_and_wait("PATH ERROR", "Failed to set up paths", str(e))

def open_browser(port: int = 5000, delay: int = 2) -> None:
    """Open browser after a short delay to let server start."""
    time.sleep(delay)
    webbrowser.open(f'http://localhost:{port}')

def main():
    port = 5000
    
    print("\n" + "="*50)
    print("  HYPERTROPHY TOOLBOX")
    print("="*50)
    print(f"\n  Working directory: {os.getcwd()}")
    print(f"  Base directory: {BASE_DIR}")
    print()
    
    try:
        # Import Flask app
        print("  Loading application...")
        from app import app
        print("  Application loaded successfully!")
        print()
        
        # Start browser opener in background thread
        browser_thread = threading.Thread(target=open_browser, args=(port, 2))
        browser_thread.daemon = True
        browser_thread.start()
        
        print(f"  Server running at: http://127.0.0.1:{port}")
        print("  Browser will open automatically...")
        print("\n  Press Ctrl+C to stop the server")
        print("="*50 + "\n")
        
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
    except Exception as e:
        print("\n" + "="*50)
        print("  ERROR: Application failed to start!")
        print("="*50)
        print(f"\n  {type(e).__name__}: {e}")
        print("\n  Full error details:")
        traceback.print_exc()
        print("\n" + "="*50)
        print("  Press Enter to close this window...")
        input()
        sys.exit(1)


if __name__ == '__main__':
    main()
