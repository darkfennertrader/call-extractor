"""
Shared state for callback tools and other MCP tools.
"""

from typing import Dict, List

# Store task results and registered callbacks
task_results: Dict[str, str] = {}
task_callbacks: Dict[str, List[dict]] = {}
