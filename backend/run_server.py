"""
Local Development Server Runner for Martian Map Backend.
Runs Uvicorn on 0.0.0.0:8000.
"""

import sys
import os
import uvicorn

# Ensure package directory is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 NASA SPACE APPS 2026: JEZERO CRATER SURVIVAL ROUTING BACKEND")
    print("=" * 70)
    print("• Interactive Swagger UI: http://127.0.0.1:8000/docs")
    print("• ReDoc API Explorer:     http://127.0.0.1:8000/redoc")
    print("• Terrain Grid API:       http://127.0.0.1:8000/api/terrain/grid")
    print("• Route Calculation API:  http://127.0.0.1:8000/api/route/calculate")
    print("=" * 70)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
