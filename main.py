import sys
from os import environ as env
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "app"))

from app import con_app

if __name__ == "__main__":
    port = int(env.get("PORT", 5000))
    con_app.run(host="0.0.0.0", port=port)
