"""Debug script to test HarteSettings startup"""

import sys
import os
import traceback

print("[DEBUG] Starting HarteSettings V3...")
print(f"[DEBUG] Python version: {sys.version}")
print(f"[DEBUG] Current directory: {os.getcwd()}")

try:
    print("[DEBUG] Importing src.main...")
    from src.main import main
    
    print("[DEBUG] Calling main()...")
    main()
    
except Exception as e:
    print(f"[ERROR] Exception occurred:")
    print(f"[ERROR] {type(e).__name__}: {str(e)}")
    traceback.print_exc()
    
    print("\n[DEBUG] Press Enter to close...")
    input()
