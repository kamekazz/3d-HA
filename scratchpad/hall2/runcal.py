"""Run the ceiling calibration, then ALWAYS restore the real ceiling piece."""
import os, sys, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import ccal3
    ccal3.run()
except Exception:
    traceback.print_exc()
finally:
    print("-- restoring real ceiling --")
    import importlib
    try:
        mod = importlib.import_module("ceiling3")
    except Exception:
        mod = importlib.import_module("ceiling2")
    mod.main()
