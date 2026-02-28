from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import uuid4
from datetime import datetime
import os
import gzip
import io

from app.database import engine, Base, AsyncSessionLocal, get_db
from app.models import User, Export
from app.export_service import process_export, cancel_job

app = FastAPI(title="Large-Scale CSV Export Service")

@app.on_event("startup")
async def startup():
    # Tables are created by the init.sql script in the container, 
    # but we can keep this for safety if running locally outside docker.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/exports/csv", status_code=202)
async def initiate_export(
    background_tasks: BackgroundTasks,
    country_code: str = Query(None),
    subscription_tier: str = Query(None),
    min_ltv: float = Query(None),
    columns: str = Query(None),
    delimiter: str = Query(","),
    quoteChar: str = Query('"'),
    db: AsyncSession = Depends(get_db)
):
    export_id = str(uuid4())
    
    new_export = Export(
        id=export_id,
        status="pending",
        filters=f"country_code={country_code},tier={subscription_tier},min_ltv={min_ltv}",
        columns=columns
    )
    
    db.add(new_export)
    await db.commit()
    
    background_tasks.add_task(
        process_export,
        export_id=export_id,
        country_code=country_code,
        subscription_tier=subscription_tier,
        min_ltv=min_ltv,
        columns=columns,
        delimiter=delimiter,
        quotechar=quoteChar
    )
    
    return {"exportId": export_id, "status": "pending"}

@app.get("/exports/{export_id}/status")
async def get_export_status(export_id: str, db: AsyncSession = Depends(get_db)):
    export = await db.get(Export, export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    return {
        "exportId": str(export.id),
        "status": export.status,
        "progress": {
            "totalRows": export.total_rows,
            "processedRows": export.processed_rows,
            "percentage": export.percentage
        },
        "error": export.error,
        "createdAt": export.created_at.isoformat() if export.created_at else None,
        "completedAt": export.completed_at.isoformat() if export.completed_at else None
    }

@app.get("/exports/{export_id}/download")
async def download_export(export_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    # Basic validation for path safety
    import uuid
    try:
        uuid.UUID(export_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid export ID format")

    export = await db.get(Export, export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    
    if export.status != "completed":
        raise HTTPException(status_code=425, detail="Export is not completed yet")
    
    file_path = export.file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="CSV file not found on disk")

    # Check for Gzip
    accept_encoding = request.headers.get("Accept-Encoding", "")
    
    if "gzip" in accept_encoding:
        import zlib
        def gzip_stream():
            compressor = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    compressed = compressor.compress(chunk)
                    if compressed:
                        yield compressed
                yield compressor.flush()

        return StreamingResponse(
            gzip_stream(),
            media_type="text/csv",
            headers={
                "Content-Encoding": "gzip",
                "Content-Disposition": f'attachment; filename="export_{export_id}.csv.gz"',
            }
        )
    
    # Standard FileResponse handles Ranges automatically
    return FileResponse(
        path=file_path,
        filename=f"export_{export_id}.csv",
        media_type="text/csv"
    )

@app.delete("/exports/{export_id}", status_code=204)
async def cancel_export(export_id: str, db: AsyncSession = Depends(get_db)):
    export = await db.get(Export, export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    # Attempt to stop the background job if it's running
    stopped = await cancel_job(export_id)
    
    # Cleanup files
    if export.file_path and os.path.exists(export.file_path):
        os.remove(export.file_path)
    
    # Update status or delete record
    # Requirement says "status updated to cancelled or record removed"
    # I'll update to cancelled for tracking
    export.status = "cancelled"
    await db.commit()
    
    return Response(status_code=204)