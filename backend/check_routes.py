#!/usr/bin/env python3
"""Check which routes are registered in the ai_suggestions router."""

from src.jd_ingestion.api.endpoints import ai_suggestions

print(f"Router has {len(ai_suggestions.router.routes)} routes:")
print()
for route in ai_suggestions.router.routes:
    methods = ",".join(route.methods) if hasattr(route, "methods") else "N/A"
    print(f"  {methods:8s} {route.path}")
