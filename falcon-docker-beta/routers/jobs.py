"""Publish job status endpoint (/api/jobs/*)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from db import get_db
from core.auth import _require_admin

router = APIRouter(tags=["jobs"])


@router.get("/api/jobs/{job_id}", response_model=None)
def get_job_status(request: Request, job_id: str):
    """publish_jobs から job の現在状態を返す。見つからなければ 404。"""
    _require_admin(request)
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM publish_jobs WHERE id = ?", (job_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Job not found")
    return dict(row)
