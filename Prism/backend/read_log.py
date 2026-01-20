
from pathlib import Path

log_path = Path(r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend\data\processing_errors.log")
if log_path.exists():
    lines = log_path.read_text(encoding="utf-8").splitlines()
    print("\n".join(lines[-20:]))
else:
    print("Log file not found")
