"""Job status endpoint (/api/jobs/*) — publish と scan の両方のジョブを返す。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from db import get_db
from core.auth import _require_admin

router = APIRouter(tags=["jobs"])


@router.get("/api/jobs/{job_id}", response_model=None)
def get_job_status(request: Request, job_id: str):
    """publish_jobs → scan_jobs の順に job の現在状態を返す。見つからなければ 404。

    DD-CYN-0142 §5-B: 走査も公開と同じ「開始だけを返す口 + 進み具合を取りに行く口」に
    揃えたため、この口が両方のジョブの進み具合を返す。kind で区別する。
    """
    _require_admin(request)
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM publish_jobs WHERE id = ?", (job_id,)).fetchone()
        kind = "publish"
        if not row:
            row = conn.execute("SELECT * FROM scan_jobs WHERE id = ?", (job_id,)).fetchone()
            kind = "scan"
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Job not found")
    out = dict(row)
    out["kind"] = kind
    return out
