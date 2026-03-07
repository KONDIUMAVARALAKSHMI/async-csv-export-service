from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
import os
import zlib
import logging

from app.database import get_db
from app.models import Export
from app.export_service import process_export, cancel_job

router = APIRouter()
logger = logging.getLogger(__name__)

# Endpoint to start the export
@router.post("/exports/csv", status_code=202)
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
    from uuid import uuid4
    export_id = str(uuid4())
    logger.info(f"New export requested: {export_id}")

    # Validate delimiter
    if delimiter and len(delimiter) != 1:
        raise HTTPException(
            status_code=400,
            detail="Delimiter must be a single character"
        )

    # Validate quote character
    if quoteChar and len(quoteChar) != 1:
        raise HTTPException(
            status_code=400,
            detail="Quote character must be a single character"
        )

    # Create export record
    new_export = Export(
        id=UUID(export_id),
        status="pending",
        created_at=datetime.now(timezone.utc),
        processed_rows=0,
        total_rows=0,
        percentage=0
    )

    db.add(new_export)
    await db.commit()

    # Start background task
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


# check progress
@router.get("/exports/{export_id}/status")
async def get_export_status(export_id: str, db: AsyncSession = Depends(get_db)):
    logger.info(f"Status checked for export: {export_id}")

    try:
        export_uuid = UUID(export_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid export ID format")

    export = await db.get(Export, export_uuid)
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


# download the actual file
@router.get("/exports/{export_id}/download")
async def download_export(export_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    logger.info(f"Download requested for export: {export_id}")

    # Validate UUID format
    try:
        export_uuid = UUID(export_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid export ID format")

    export = await db.get(Export, export_uuid)
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")

    if export.status != "completed":
        raise HTTPException(status_code=425, detail="Export is not completed yet")

    file_path = export.file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="CSV file not found on disk")

    accept_encoding = request.headers.get("Accept-Encoding", "")

    # Gzip streaming
    if "gzip" in accept_encoding:
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

    return FileResponse(
        path=file_path,
        filename=f"export_{export_id}.csv",
        media_type="text/csv"
    )


# stop the export job
@router.delete("/exports/{export_id}", status_code=204)
async def cancel_export(export_id: str, db: AsyncSession = Depends(get_db)):
    logger.info(f"Cancel requested for export: {export_id}")

    try:
        export_uuid = UUID(export_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid export ID format")

    export = await db.get(Export, export_uuid)
    if not export:
        raise HTTPException(status_code=404, detail="Export job not found")

    await cancel_job(export_id)

    if export.file_path and os.path.exists(export.file_path):
        os.remove(export.file_path)

    export.status = "cancelled"
    await db.commit()

    return Response(status_code=204)
