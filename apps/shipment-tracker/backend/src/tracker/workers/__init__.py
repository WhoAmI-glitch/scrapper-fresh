"""Background worker tasks using asyncio.

Each worker runs as a long-lived asyncio Task, polling external services
or running periodic checks on configurable intervals.
"""
