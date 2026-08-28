"""utils.metadata.enrich — チャンクメタデータ強化。

薄いラッパー。実体は後日移植する。
"""

from typing import Any


def enrich_chunk_metadata(chunk: dict[str, Any]) -> dict[str, Any]:
    """チャンクに分類・感度メタデータを付与する。

    現状は minimal stub。classification + sensitivity の結合実装は後日移植する。
    """
    text = chunk.get("content", "") or chunk.get("text", "")
    if not text:
        return chunk

    from utils.metadata.classification import classify_document_type
    from utils.metadata.sensitivity import score_sensitivity

    enriched = dict(chunk)
    try:
        enriched["classification"] = classify_document_type(text)
    except Exception:
        pass
    try:
        enriched["sensitivity"] = score_sensitivity(text)
    except Exception:
        pass
    return enriched


__all__ = ["enrich_chunk_metadata"]
