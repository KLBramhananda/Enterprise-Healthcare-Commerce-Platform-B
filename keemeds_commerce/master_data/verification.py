"""
Catalog Verification

Implements the ``--verify`` workflow: a reusable, offline end-to-end validation
that checks the generated ERPNext import files form a consistent product
catalog before they are trusted for import.

The verifier is deliberately DB-free: it treats the generated ``master_data/output``
workbooks and the normalized master source files (Brands, Manufacturers, Item
Groups, UOMs) as the ground truth, and checks that the catalog is internally
consistent and that every record references a master that is defined.

What is verified
----------------
- Every expected output file (items, prices, stock, images) exists.
- Every generated workbook contains the required ERPNext column headers.
- Generated item codes are unique.
- Generated item names are unique.
- Brands / Manufacturers / Item Groups / UOMs referenced by items exist in the
  master source files (the offline proxy for "exists in ERPNext").
- Item-attribute master references resolve to defined masters.
- Price / Opening Stock / Image Mapping records reference valid (generated)
  item codes.
- Image mappings reference an image file that is actually present.

Reusability
-----------
File discovery is driven by the centralized importer/exporter configuration
(:class:`~master_data.config.ImporterConfig` and the enrichment export specs),
so the verifier is key-agnostic. A future OTC, Wellness, Devices, Baby Care,
Surgical or Accessories generator requires only its importer/export
registration in configuration; no verifier change is needed.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from .config import ExportConfig, MasterDataConfig, ReportConfig
from .logging_setup import get_logger
from .master_loader import MasterDataLoader
from .models import MasterDataResult
from .readers import build_default_registry

_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"
_DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S"

#: File names of the verification reports written under the reports directory.
VERIFICATION_JSON_FILENAME = "verification_report.json"
VERIFICATION_LOG_FILENAME = "verification_report.log"


@dataclass(frozen=True)
class FileCheck:
    """
    The outcome of validating a single generated workbook.
    """

    path: str
    exists: bool
    row_count: int
    has_required_columns: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class VerificationReport:
    """
    Mutable aggregator for the outcome of a catalog verification run.
    """

    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None
    expected_records: int = 0
    generated_records: int = 0
    files: list[FileCheck] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    missing_masters: list[str] = field(default_factory=list)
    duplicate_records: list[str] = field(default_factory=list)
    invalid_references: list[str] = field(default_factory=list)
    missing_images: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Duration of the run in seconds, or ``0`` before completion."""
        if self.finished_at is None:
            return 0.0
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def found_files(self) -> int:
        """Number of expected files that exist."""
        return sum(1 for file_check in self.files if file_check.exists)

    @property
    def expected_files(self) -> int:
        """Total number of expected files."""
        return len(self.files)

    @property
    def is_valid(self) -> bool:
        """
        ``True`` when the catalog is consistent.

        The run is invalid if any expected file is missing, any required column
        is absent, there are duplicate records, invalid references, missing
        masters or missing images.
        """
        return not (
            self.missing_files
            or self._column_errors()
            or self.duplicate_records
            or self.invalid_references
            or self.missing_masters
            or self.missing_images
        )

    @property
    def status(self) -> str:
        """Human-readable verification status."""
        return "PASSED" if self.is_valid else "FAILED"

    def add_note(self, message: str) -> None:
        """Record a free-text note about the verification run."""
        self.notes.append(message)

    def _column_errors(self) -> bool:
        return any(file_check.has_required_columns is False for file_check in self.files)


class CatalogVerifier:
    """
    Performs the offline catalog verification.
    """

    def __init__(
        self,
        config: MasterDataConfig,
        loader: MasterDataLoader | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._loader = loader or MasterDataLoader(
            config=config, readers=build_default_registry(), logger=logger
        )
        self._logger = logger or get_logger(self.__class__.__name__)

    def verify(self) -> VerificationReport:
        """Run the full verification and return the report."""
        report = VerificationReport()

        masters = self._loader.load()
        item_codes = self._verify_items(report, masters)
        self._verify_references(report, item_codes)
        self._verify_images(report)
        self._collect_files(report)

        report.expected_records = self._expected_records()
        report.generated_records = sum(file_check.row_count for file_check in report.files)
        report.finished_at = datetime.now()
        return report

    # ------------------------------------------------------------------ #
    # Item verification
    # ------------------------------------------------------------------ #

    def _verify_items(
        self,
        report: VerificationReport,
        masters: MasterDataResult,
    ) -> set[str]:
        """Verify uniqueness and master references of the generated items."""
        paths = self._item_files()
        rows = [row for path in paths for row in self._read_rows(path)]

        codes: set[str] = set()
        names: set[str] = set()
        for row in rows:
            code = self._clean(row.get("Item Code", ""))
            name = self._clean(row.get("Item Name", ""))
            self._assert_unique(report.duplicate_records, codes, code, "item code")
            self._assert_unique(report.duplicate_records, names, name, "item name")
            self._verify_item_masters(report, masters, row)

        return codes

    def _verify_item_masters(
        self, report: VerificationReport, masters: MasterDataResult, row
    ) -> None:
        """Check the master references carried by a single item row."""
        references = (
            ("Brand", "brand"),
            ("Default Item Manufacturer", "manufacturer"),
            ("Item Group", "item_group"),
            ("Default Unit of Measure", "uom"),
        )
        for column, master_key in references:
            expected = self._clean(row.get(column, ""))
            if not expected:
                continue
            defined = set(masters.values_for(master_key))
            if expected not in defined:
                self._dedup(
                    report.missing_masters,
                    f"Item {self._clean(row.get('Item Code',''))} references "
                    f"{column!r} = {expected!r}, which is not a defined {master_key}.",
                )

    def _assert_unique(
        self,
        target: list[str],
        seen: set[str],
        value: str,
        label: str,
    ) -> None:
        """Record a duplicate if ``value`` was already seen."""
        if not value:
            return
        if value in seen:
            self._dedup(target, f"Duplicate {label}: {value}")
        seen.add(value)

    # ------------------------------------------------------------------ #
    # Reference verification
    # ------------------------------------------------------------------ #

    def _verify_references(
        self,
        report: VerificationReport,
        item_codes: set[str],
    ) -> None:
        """Check price/stock/image records reference valid (generated) items."""
        for importer_config in self._config.importer_configs():
            if importer_config.key == "item":
                continue
            for path in self._resolved_files(importer_config):
                for row in self._read_rows(path):
                    code = self._clean(row.get("Item Code", ""))
                    if code and code not in item_codes:
                        self._dedup(
                            report.invalid_references,
                            f"{importer_config.name} row references unknown item "
                            f"code {code!r} ({path.name}).",
                        )

    def _verify_images(self, report: VerificationReport) -> None:
        """Flag image mappings whose image file is absent locally."""
        image_gen_config = self._config.image_generator
        importer_config = self._config.importer_config_for("image")
        if importer_config is None:
            return
        image_dir: Path = image_gen_config.output_dir
        available = self._available_image_files(image_dir)
        self._logger.info("Image availability checked against: %s", image_dir)
        for path in self._resolved_files(importer_config):
            for row in self._read_rows(path):
                image_path = self._clean(row.get("Image Path", ""))
                if not image_path:
                    continue
                filename = image_path.rsplit("/", 1)[-1]
                if filename not in available:
                    self._dedup(
                        report.missing_images,
                        f"Item {self._clean(row.get('Item Code',''))} references "
                        f"missing image file {filename!r}.",
                    )

    def _available_image_files(self, image_dir: Path) -> set[str]:
        """Return the file names present in the configured image directory."""
        if not image_dir.is_dir():
            return set()
        return {
            path.name
            for path in image_dir.iterdir()
            if path.is_file() or path.is_symlink()
        }

    # ------------------------------------------------------------------ #
    # File discovery and existence
    # ------------------------------------------------------------------ #

    def _collect_files(self, report: VerificationReport) -> None:
        """Validate that every expected file exists and has the required columns."""
        for importer_config in self._config.importer_configs():
            for path in self._resolved_files(importer_config):
                exists = path.is_file()
                row_count = 0
                has_columns = True
                errors: list[str] = []
                if exists:
                    headers, rows = self._read_workbook(path)
                    row_count = len(rows)
                    expected = self._expected_columns(importer_config.key)
                    missing = self._missing_columns(headers, expected)
                    if missing:
                        has_columns = False
                        errors.append(
                            f"Missing required column(s) {missing} in {path}"
                        )
                else:
                    self._dedup(report.missing_files, str(path))
                report.files.append(
                    FileCheck(
                        path=str(path),
                        exists=exists,
                        row_count=row_count,
                        has_required_columns=has_columns,
                        errors=errors,
                    )
                )

    def _resolved_files(self, importer_config) -> list[Path]:
        """Resolve the source file(s) for an importer configuration.

        Every configured file is represented as an expected path, so an exact
        (non-glob) file that is absent is still reported as missing rather than
        silently dropped. Glob patterns resolve to their matching files.
        """
        import glob

        base_dir = self._config.export.output_dir / importer_config.subdirectory
        files: list[Path] = []
        for name in importer_config.filenames:
            is_glob = any(char in name for char in "*?[")
            matches = glob.glob(str(base_dir / name))
            if matches:
                files.extend(sorted(Path(match) for match in matches))
            elif not is_glob:
                files.append(base_dir / name)
        return files

    def _item_files(self) -> list[Path]:
        importer_config = self._config.importer_config_for("item")
        if importer_config is None:
            return []
        return self._resolved_files(importer_config)

    def _expected_columns(self, key: str) -> list[str]:
        """Return the ERPNext column template for a catalog key."""
        if key == "item":
            return [column.name for column in self._config.export.columns]
        spec = self._config.enrichment_export_for(key) or self._config.master_export_for(key)
        if spec is not None:
            return [column.name for column in spec.columns]
        return []

    # ------------------------------------------------------------------ #
    # Workbook helpers
    # ------------------------------------------------------------------ #

    def _read_workbook(self, path: Path) -> tuple[list[str], list[dict[str, str]]]:
        """Return (headers, rows-as-dicts) for an xlsx file."""
        headers: list[str] = []
        rows: list[dict[str, str]] = []
        if not path.is_file():
            return headers, rows
        try:
            workbook = load_workbook(path, read_only=True)
            sheet = workbook.active
            iter_rows = sheet.iter_rows(values_only=True)
            header_row = next(iter_rows, None)
            if header_row is None:
                workbook.close()
                return headers, rows
            headers = [str(value) if value is not None else "" for value in header_row]
            for values in iter_rows:
                if values is None:
                    continue
                cells = list(values)
                row = {}
                for index, header in enumerate(headers):
                    cell = cells[index] if index < len(cells) else None
                    row[header] = "" if cell is None else str(cell)
                if any(row.values()):
                    rows.append(row)
            workbook.close()
        except Exception as exc:
            self._logger.error("Unreadable workbook %s: %s", path, exc)
        return headers, rows

    def _read_rows(self, path: Path) -> list[dict[str, str]]:
        return self._read_workbook(path)[1]

    def _missing_columns(self, headers: list[str], expected: list[str]) -> list[str]:
        present = {header.strip() for header in headers}
        return [column for column in expected if column not in present]

    def _expected_records(self) -> int:
        """Centralized expectation for the total number of item records."""
        return self._config.medicine.target_count

    # ------------------------------------------------------------------ #
    # little helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _clean(value: object) -> str:
        return str(value).strip() if value is not None else ""

    @staticmethod
    def _dedup(target: list[str], message: str) -> None:
        if message not in target:
            target.append(message)


class VerificationReportWriter:
    """
    Writes a :class:`VerificationReport` to a JSON summary and a log file.
    """

    def __init__(
        self,
        config: ReportConfig,
        export_config: ExportConfig,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._export_config = export_config
        self._logger = logger or get_logger(self.__class__.__name__)

    def resolve_dir(self) -> Path:
        target = self._export_config.output_dir / self._config.subdirectory
        target.mkdir(parents=True, exist_ok=True)
        return target

    def file_paths(self) -> tuple[Path, Path]:
        target = self.resolve_dir()
        return target / VERIFICATION_JSON_FILENAME, target / VERIFICATION_LOG_FILENAME

    def write(self, report: VerificationReport) -> tuple[Path, Path]:
        json_path, log_path = self.file_paths()
        self._write_json(report, json_path)
        self._write_log(report, log_path)
        return json_path, log_path

    def _write_json(self, report: VerificationReport, path: Path) -> None:
        payload = {
            "started_at": report.started_at.strftime(_TIMESTAMP_FORMAT),
            "finished_at": (
                report.finished_at.strftime(_TIMESTAMP_FORMAT)
                if report.finished_at
                else None
            ),
            "duration_seconds": round(report.duration_seconds, 3),
            "status": report.status,
            "expected_records": report.expected_records,
            "generated_records": report.generated_records,
            "expected_files": report.expected_files,
            "found_files": report.found_files,
            "missing_files": list(report.missing_files),
            "missing_masters": list(report.missing_masters),
            "invalid_references": list(report.invalid_references),
            "duplicate_records": list(report.duplicate_records),
            "missing_images": list(report.missing_images),
            "notes": list(report.notes),
            "files": [
                {
                    "path": file_check.path,
                    "exists": file_check.exists,
                    "row_count": file_check.row_count,
                    "has_required_columns": file_check.has_required_columns,
                    "errors": list(file_check.errors),
                }
                for file_check in report.files
            ],
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def _write_log(self, report: VerificationReport, path: Path) -> None:
        lines: list[str] = []
        lines.append("KeeMeds Catalog Verification Report")
        lines.append("=" * 40)
        lines.append(f"Started at:   {report.started_at.strftime(_DISPLAY_FORMAT)}")
        finished = (
            report.finished_at.strftime(_DISPLAY_FORMAT)
            if report.finished_at
            else "not finished"
        )
        lines.append(f"Finished at:  {finished}")
        lines.append(f"Duration (s): {report.duration_seconds:.3f}")
        lines.append(f"Status:       {report.status}")
        lines.append("")
        lines.append(f"Expected records:  {report.expected_records}")
        lines.append(f"Generated records: {report.generated_records}")
        lines.append(f"Expected files:    {report.expected_files}")
        lines.append(f"Found files:       {report.found_files}")
        lines.append("")
        lines.append("Generated/expected files:")
        for file_check in report.files:
            status = "present" if file_check.exists else "MISSING"
            columns = "ok" if file_check.has_required_columns else "COLUMNS-MISSING"
            lines.append(
                f"  - {file_check.path} [{status}] [{columns}] "
                f"rows={file_check.row_count}"
            )
        lines.append("")
        lines.append("Missing masters:")
        for entry in report.missing_masters or ["  (none)"]:
            lines.append(f"  - {entry}")
        lines.append("")
        lines.append("Invalid references:")
        for entry in report.invalid_references or ["  (none)"]:
            lines.append(f"  - {entry}")
        lines.append("")
        lines.append("Duplicate records:")
        for entry in report.duplicate_records or ["  (none)"]:
            lines.append(f"  - {entry}")
        lines.append("")
        lines.append("Missing images:")
        for entry in report.missing_images or ["  (none)"]:
            lines.append(f"  - {entry}")
        lines.append("")
        lines.append("Execution notes:")
        for note in report.notes or ["  (none)"]:
            lines.append(f"  - {note}")
        lines.append("")
        lines.append("Report generated automatically by the Catalog verifier.")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_verifier(
    config: MasterDataConfig,
    logger: logging.Logger | None = None,
) -> CatalogVerifier:
    """Build a default catalog verifier from a master data configuration."""
    return CatalogVerifier(config=config, logger=logger)


def build_verification_report_writer(
    config: MasterDataConfig,
    logger: logging.Logger | None = None,
) -> VerificationReportWriter:
    """Build a default verification report writer."""
    return VerificationReportWriter(
        config=config.reports,
        export_config=config.export,
        logger=logger,
    )
