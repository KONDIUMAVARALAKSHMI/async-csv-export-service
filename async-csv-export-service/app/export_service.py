import csv
import os
import asyncio
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Export
from app.database import AsyncSessionLocal
import gzip

# Global dictionary to track active tasks for cancellation
active_tasks = {}

async def update_status(export_id, processed_rows=None, percentage=None, status=None, error=None, file_path=None):
    """Helper to update export status in a separate session to avoid transaction issues."""
    async with AsyncSessionLocal() as db:
        export = await db.get(Export, export_id)
        if not export:
            return
        
        if processed_rows is not None:
            export.processed_rows = processed_rows
        if percentage is not None:
            export.percentage = percentage
        if status is not None:
            export.status = status
        if error is not None:
            export.error = error
        if file_path is not None:
            export.file_path = file_path
        
        if status == "completed":
            export.completed_at = datetime.utcnow()
            export.percentage = 100
            
        await db.commit()

async def process_export(
    export_id: str,
    country_code: str = None,
    subscription_tier: str = None,
    min_ltv: float = None,
    columns: str = None,
    delimiter: str = ",",
    quotechar: str = '"'
):
    active_tasks[export_id] = True
    
    try:
        async with AsyncSessionLocal() as db:
            # 1. Update status to processing
            await update_status(export_id, status="processing")

            # 2. Build query
            query = select(User)
            filters = []
            if country_code:
                filters.append(User.country_code == country_code)
            if subscription_tier:
                filters.append(User.subscription_tier == subscription_tier)
            if min_ltv is not None:
                filters.append(User.lifetime_value >= min_ltv)
            
            if filters:
                query = query.where(and_(*filters))
            
            # Resolve columns
            all_columns = ["id", "name", "email", "signup_date", "country_code", "subscription_tier", "lifetime_value"]
            if columns:
                export_columns = [c.strip() for c in columns.split(",")]
                # Validate columns
                export_columns = [c for c in export_columns if c in all_columns]
            else:
                export_columns = all_columns

            # 3. Count total rows
            count_query = select(func.count()).select_from(query.subquery())
            total_rows_result = await db.execute(count_query)
            total_rows = total_rows_result.scalar()
            
            # Update total rows in DB
            async with AsyncSessionLocal() as status_db:
                export = await status_db.get(Export, export_id)
                export.total_rows = total_rows
                await status_db.commit()

            if total_rows == 0:
                await update_status(export_id, status="completed", percentage=100)
                return

            # 4. Stream data and write to CSV
            os.makedirs("exports", exist_ok=True)
            file_path = f"exports/export_{export_id}.csv"
            
            processed_rows = 0
            
            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, 
                    fieldnames=export_columns, 
                    delimiter=delimiter, 
                    quotechar=quotechar,
                    quoting=csv.QUOTE_MINIMAL
                )
                writer.writeheader()
                
                # SQLAlchemy stream() for memory efficiency
                result = await db.stream(query)
                
                async for row in result:
                    # Check for cancellation
                    if not active_tasks.get(export_id):
                        f.close()
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        await update_status(export_id, status="cancelled")
                        return

                    user = row[0]
                    row_dict = {col: getattr(user, col) for col in export_columns}
                    writer.writerow(row_dict)
                    
                    processed_rows += 1
                    
                    # Update progress every 5000 rows to reduce DB load
                    if processed_rows % 5000 == 0 or processed_rows == total_rows:
                        await update_status(
                            export_id, 
                            processed_rows=processed_rows, 
                            percentage=int((processed_rows / total_rows) * 100)
                        )

            # 5. Finalize
            await update_status(export_id, status="completed", file_path=file_path)

    except Exception as e:
        print(f"Export Error: {e}")
        await update_status(export_id, status="failed", error=str(e))
        # Cleanup broken file
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
    finally:
        active_tasks.pop(export_id, None)

async def cancel_job(export_id: str):
    if export_id in active_tasks:
        active_tasks[export_id] = False
        return True
    return False
