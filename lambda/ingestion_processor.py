import os
import json
import gzip
import io
from datetime import datetime, timezone
import boto3

s3_client = boto3.client("s3")

S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
S3_PREFIX_ROOT = os.environ.get("S3_PREFIX_ROOT", "raw")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "50"))
COMPRESS_GZIP = os.environ.get("COMPRESS_GZIP", "true").lower() == "true"


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_s3_key(records_count: int) -> str:
    now = datetime.now(timezone.utc)
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    hour = now.strftime("%H")
    minute = now.strftime("%M")
    second = now.strftime("%S")
    epoch_ms = int(now.timestamp() * 1000)
    filename = f"batch_{epoch_ms}_{records_count}.jsonl"
    if COMPRESS_GZIP:
        filename += ".gz"
    return f"{S3_PREFIX_ROOT}/year={year}/month={month}/day={day}/hour={hour}/{filename}"


def _serialize_records_to_bytes(records: list[dict]) -> bytes:
    # Usa JSON Lines para facilitar a ingestão posterior
    lines = []
    for rec in records:
        lines.append(json.dumps(rec, separators=(",", ":")))
    payload = "\n".join(lines).encode("utf-8")

    if COMPRESS_GZIP:
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
            gz.write(payload)
        return buf.getvalue()

    return payload


def handler(event, context):
    # O IoT Core envia o payload original dentro de event; dependendo da regra, pode ser objeto único ou lista
    # Normalizamos para uma lista de registros
    raw_records = []

    if isinstance(event, dict):
        # Mensagem única
        raw_records = [event]
    elif isinstance(event, list):
        raw_records = event
    else:
        raw_records = [{"message": event}]

    # Enriquecimento com metadados e bufferização
    enriched_records: list[dict] = []
    ingestion_ts = _now_utc_iso()

    for rec in raw_records:
        try:
            if isinstance(rec, str):
                rec_obj = json.loads(rec)
            else:
                rec_obj = dict(rec)
        except Exception:
            rec_obj = {"_unparsed": rec}

        rec_obj["ingestion_ts"] = ingestion_ts
        enriched_records.append(rec_obj)

    # Divide em lotes e salva cada um
    total = len(enriched_records)
    if total == 0:
        return {"status": "no-data"}

    start = 0
    results = []
    while start < total:
        end = min(start + BATCH_SIZE, total)
        batch = enriched_records[start:end]
        body = _serialize_records_to_bytes(batch)
        key = _build_s3_key(len(batch))

        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=body,
            ContentType="application/json",
            ContentEncoding="gzip" if COMPRESS_GZIP else None,
            ServerSideEncryption="AES256",
        )

        results.append({"s3_key": key, "records": len(batch)})
        start = end

    return {
        "status": "ok",
        "written_batches": len(results),
        "details": results,
    } 