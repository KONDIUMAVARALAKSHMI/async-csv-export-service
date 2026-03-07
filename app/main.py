from fastapi import FastAPI
async def health():
    return {"status": "ok"}

# Include Routes
app.include_router(router)
