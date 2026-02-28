export_id = str(uuid4())

logger.info(f"New export requested: {export_id}")

# Validation
if delimiter and len(delimiter) != 1:
    raise HTTPException(
        status_code=400,
        detail="Delimiter must be a single character"
    )

if quoteChar and len(quoteChar) != 1:
    raise HTTPException(
        status_code=400,
        detail="Quote character must be a single character"
    )

new_export = Export(
    id=export_id,
    status="pending",
    filters=f"country_code={country_code},tier={subscription_tier},min_ltv={min_ltv}",
    columns=columns
)