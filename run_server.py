import sys
import asyncio
import uvicorn

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    # We must explicitly disable Uvicorn's internal loop setup by passing loop="none"
    # because even when running programmatically, it tries to override the loop policy!
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True, loop="none")
