"""
pandas-based exporter: CSV, Excel (.xlsx), and JSON.
"""
import io
import json
import logging
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


class Exporter:
    """Export a list of record dicts to CSV, Excel, or JSON."""

    # ── File export ────────────────────────────────────────────────────────────

    def export(
        self,
        records: List[Dict],
        output_path: str,
        fmt: str = "csv",
    ) -> str:
        """
        Write *records* to *output_path* in the given *fmt*.

        Returns the final output path (may differ for xlsx).
        """
        if not records:
            raise ValueError("No records to export — nothing to write.")

        df = pd.json_normalize(records)
        fmt = fmt.lower().strip()

        if fmt == "csv":
            df.to_csv(output_path, index=False, encoding="utf-8-sig")

        elif fmt in ("excel", "xlsx"):
            if not output_path.endswith(".xlsx"):
                output_path = (
                    output_path.rsplit(".", 1)[0] + ".xlsx"
                    if "." in output_path
                    else output_path + ".xlsx"
                )
            df.to_excel(output_path, index=False, engine="openpyxl")

        elif fmt == "json":
            with open(output_path, "w", encoding="utf-8") as fh:
                json.dump(records, fh, indent=2, ensure_ascii=False)

        else:
            raise ValueError(
                f"Unsupported format '{fmt}'. Choose: csv, excel, json."
            )

        logger.info("Exported %d records → %s", len(records), output_path)
        return output_path

    # ── In-memory bytes (for Streamlit download) ───────────────────────────────

    def to_bytes(self, records: List[Dict], fmt: str = "csv") -> bytes:
        """
        Serialise *records* to raw bytes without touching the filesystem.
        Used by Streamlit's ``st.download_button``.
        """
        if not records:
            return b""

        df = pd.json_normalize(records)
        fmt = fmt.lower().strip()

        if fmt == "csv":
            return df.to_csv(index=False, encoding="utf-8").encode("utf-8")

        if fmt == "json":
            return json.dumps(records, indent=2, ensure_ascii=False).encode("utf-8")

        if fmt in ("excel", "xlsx"):
            buf = io.BytesIO()
            df.to_excel(buf, index=False, engine="openpyxl")
            return buf.getvalue()

        raise ValueError(f"Unsupported format '{fmt}'. Choose: csv, excel, json.")
