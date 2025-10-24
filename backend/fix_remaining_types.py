#!/usr/bin/env python3
"""Script to fix remaining simple mypy type errors"""

import re
from pathlib import Path

# Rate limiting service fixes
rate_limiting_file = Path("src/jd_ingestion/services/rate_limiting_service.py")
content = rate_limiting_file.read_text()

# Fix Row attribute access
content = re.sub(
    r"stats_result\.scalar_one_or_none\(\)\s+",
    "stats_result.scalar_one_or_none()\n        ",
    content,
)

# Add None check before accessing attributes
old_pattern = r"""        return \{
            "total_requests": stats\.total_requests,
            "total_tokens": stats\.total_tokens,
            "total_cost": stats\.total_cost,
            "avg_response_time": stats\.avg_response_time,
        \}"""

new_pattern = """        if stats is None:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "avg_response_time": 0.0,
            }

        return {
            "total_requests": int(stats[0]) if len(stats) > 0 else 0,
            "total_tokens": int(stats[1]) if len(stats) > 1 else 0,
            "total_cost": float(stats[2]) if len(stats) > 2 else 0.0,
            "avg_response_time": float(stats[2]) if len(stats) > 2 else 0.0,
        }"""

content = re.sub(old_pattern.replace("\\", "\\\\"), new_pattern, content)
rate_limiting_file.write_text(content)

print("Fixed rate_limiting_service.py")

# Embedding service fixes
embedding_file = Path("src/jd_ingestion/services/embedding_service.py")
content = embedding_file.read_text()

# Fix Column type issues
content = re.sub(
    r"embedding_vector = await self\.generate_embedding\(chunk\.chunk_text\)",
    "embedding_vector = await self.generate_embedding(str(chunk.chunk_text))",
    content,
)

content = re.sub(
    r"chunk\.embedding = embedding_vector",
    "chunk.embedding = embedding_vector  # type: ignore[assignment]",
    content,
)

embedding_file.write_text(content)
print("Fixed embedding_service.py")

# Analytics middleware fixes
middleware_file = Path("src/jd_ingestion/middleware/analytics_middleware.py")
content = middleware_file.read_text()

# Fix Optional response parameter
content = re.sub(
    r"async def _track_request\(\s+self,\s+request: Request,\s+response: Response = None,",
    "async def _track_request(\n        self,\n        request: Request,\n        response: Optional[Response] = None,",
    content,
)

content = re.sub(
    r"await self\._track_request\(request, None\)",
    "await self._track_request(request, response=None)",
    content,
)

middleware_file.write_text(content)
print("Fixed analytics_middleware.py")

# Websocket fixes
websocket_file = Path("src/jd_ingestion/api/endpoints/websocket.py")
content = websocket_file.read_text()

content = re.sub(
    r"async def broadcast_message\(self, message: Dict\[str, Any\], exclude: WebSocket = None\):",
    "async def broadcast_message(self, message: Dict[str, Any], exclude: Optional[WebSocket] = None):",
    content,
)

websocket_file.write_text(content)
print("Fixed websocket.py")

# Performance endpoint fixes
performance_file = Path("src/jd_ingestion/api/endpoints/performance.py")
content = performance_file.read_text()

# Fix None comparison
content = re.sub(
    r"if slow_query_threshold and query_time < slow_query_threshold:",
    "if slow_query_threshold is not None and query_time < slow_query_threshold:",
    content,
)

performance_file.write_text(content)
print("Fixed performance.py")

# Preferences endpoint fixes
preferences_file = Path("src/jd_ingestion/api/endpoints/preferences.py")
content = preferences_file.read_text()

# Fix preferences Column type
content = re.sub(
    r'"preferences": user\.preferences,',
    '"preferences": dict(user.preferences) if user.preferences else {},',
    content,
)

content = re.sub(r'"key": pref\.key,', '"key": str(pref.key),', content)

preferences_file.write_text(content)
print("Fixed preferences.py")

print("\nAll fixes applied successfully!")
