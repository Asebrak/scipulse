"""
SciPulse — Upload des données ArXiv vers MinIO
"""
import json
import os
import io
import boto3
from botocore.client import Config

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS   = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET   = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET         = "arxiv-raw"

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS,
    aws_secret_access_key=MINIO_SECRET,
    config=Config(signature_version="s3v4"),
)

def upload_file(local_path: str, object_name: str = None):
    object_name = object_name or os.path.basename(local_path)
    s3.upload_file(local_path, BUCKET, object_name)
    print(f"  ✅ {object_name} → s3://{BUCKET}/{object_name}")

def _upload_chunk(lines: list, object_name: str):
    content = "".join(lines).encode("utf-8")
    s3.put_object(Bucket=BUCKET, Key=object_name, Body=io.BytesIO(content))
    print(f"  ✅ {object_name} ({len(lines)} articles)")

def split_and_upload(source_file: str, chunk_size: int = 10_000, prefix: str = "chunks/"):
    print(f"\n📦 Découpage en chunks de {chunk_size} articles...")
    chunk, chunk_num = [], 0
    with open(source_file, "r") as f:
        for line in f:
            chunk.append(line)
            if len(chunk) == chunk_size:
                _upload_chunk(chunk, f"{prefix}arxiv-chunk-{chunk_num:04d}.json")
                chunk, chunk_num = [], chunk_num + 1
    if chunk:
        _upload_chunk(chunk, f"{prefix}arxiv-chunk-{chunk_num:04d}.json")
        chunk_num += 1
    print(f"\n🏁 {chunk_num} chunks uploadés ({chunk_num * chunk_size} articles au total)")

if __name__ == "__main__":
    import sys
    source = sys.argv[1] if len(sys.argv) > 1 else "data/arxiv-raw/arxiv-cs-subset-100k.json"

    if not os.path.exists(source):
        print(f"❌ Fichier introuvable : {source}")
        sys.exit(1)

    print(f"📤 Upload de {source} vers MinIO (bucket: {BUCKET})")
    print(f"   Endpoint: {MINIO_ENDPOINT}\n")

    upload_file(source)
    split_and_upload(source)
