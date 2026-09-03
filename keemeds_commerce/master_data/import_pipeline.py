"""
Master Data Import Pipeline

The Phase 6 orchestrator. A single
:class:`~master_data.import_pipeline.MasterDataImportPipeline` drives the whole
import of the generated catalog into ERPNext in ERPNext dependency order:

1. Item Master
2. Item Prices
3. Opening Stock
4. Image Mapping

The pipeline detects missing files and validates required files *before* any
import is attempted, delegates each import to the registered importer (which in
turn delegates to the standard Frappe Data Import API), aggregates everything
into an :class:`~master_data.import_report.ImportReport` and writes the detailed
import reports (JSON and log).

Recoverable vs fatal failures
-----------------------------
The pipeline continues across recoverable failures (a file import reports
failed or skipped rows, or the import backend is unavailable) and records them
in the report. It stops - reporting a fatal error - only when a *required*
source file is missing before execution, because that dependency cannot be
satisfied.

Fatal is the exception; the pipeline always writes a detailed report so the
failure is fully documented.

Extensibility
-------------
The pipeline consumes the :class:`~master_data.import_manager.ImportManager`
registry and iterates over it generically (no hardcoded importer logic). A
future OTC, Wellness, Personal Care, Baby Care, Devices, Surgical or
Accessories importer requires only registration in the import manager; no
orchestration change is needed.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from .config import MasterDataConfig
from .import_manager import ImportManager, build_importers
from .import_report import ImportReport, ImportReportWriter, build_import_report_writer

#: Factory type for the import-manager registry.
ImportManagerBuilder = Callable[..., ImportManager]


class MasterDataImportPipeline:
    """
    Orchestrates file detection, validation and dependency-ordered import.
    """

    def __init__(
        self,
        config: MasterDataConfig,
        *,
        manager_builder: ImportManagerBuilder | None = None,
        report_writer: ImportReportWriter | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._manager_builder = manager_builder or build_importers
        self._report_writer = report_writer or build_import_report_writer(config)
        self._logger = logger or logging.getLogger("keemeds.master_data.import_pipeline")

    def run(
        self,
        *,
        manager: ImportManager | None = None,
        output_dir: Path | None = None,
    ) -> tuple[ImportReport, ImportManager]:
        """
        Execute the import pipeline in dependency order.

        Returns the populated :class:`~master_data.import_report.ImportReport`
        and the manager used, which the caller inspects for counts, files and
        failures.
        """
        if manager is None:
            manager = self._manager_builder(config=self._config, logger=self._logger)

        report = ImportReport()

        fatal = self._preflight(manager, report)
        if fatal:
            report.add_note("Fatal pipeline failure: required import files missing.")
        else:
            self._run_importers(manager, report)

        report.finished_at = datetime.now()
        self._report_writer.write(report)
        return report, manager

    # ------------------------------------------------------------------ #
    # Orchestration steps
    # ------------------------------------------------------------------ #

    def _preflight(self, manager: ImportManager, report: ImportReport) -> bool:
        """
        Detect missing files and invalidate required importers before import.

        Returns ``True`` when a fatal condition (missing required file) is met.
        """
        fatal = False
        for importer in manager:
            missing = importer.missing_files()
            if missing:
                for path in missing:
                    report.add_missing_file(str(path))
                if importer._config.is_required:
                    fatal = True
                    report.add_fatal(
                        f"{importer.name}: required source file(s) missing "
                        f"({', '.join(str(p) for p in missing)})"
                    )
                self._logger.error(
                    "%s: missing required file(s) %s",
                    importer.name,
                    ", ".join(str(p) for p in missing),
                )
        if report.missing_files:
            self._logger.warning(
                "Pre-flight: %d required file(s) missing; skipping import execution.",
                len(report.missing_files),
            )
        return fatal

    def _run_importers(self, manager: ImportManager, report: ImportReport) -> None:
        """Run every registered importer in dependency order."""
        for importer in manager:
            try:
                importer.import_all(report)
            except Exception as exc:
                report.add_note(f"Importer {importer.name} failed: {exc}")
                self._logger.error("Importer %s failed: %s", importer.name, exc)
                continue
