"""
Opening Stock Importer

Imports the generated Opening Stock Excel file (``output/stock``) into ERPNext
through the standard Frappe Data Import API. The generated rows describe the
opening quantity and valuation rate per item per warehouse.
"""

from __future__ import annotations

import logging

from ..config import ImporterConfig
from .base_importer import BaseImporter, ImportExecutor


class StockImporter(BaseImporter):
    """
    Imports the generated Opening Stock workbook through the standard Frappe
    Data Import API.
    """

    DEFAULT_CONFIG = ImporterConfig(
        key="stock",
        name="Opening Stock",
        doctype="Stock Ledger Entry",
        import_type="insert",
        subdirectory="stock",
        filenames=("Opening_Stock.xlsx",),
        required_columns=("Item Code", "Warehouse", "Opening Quantity"),
    )

    def __init__(
        self,
        config: ImporterConfig,
        executor: ImportExecutor,
        *,
        export_config=None,
        import_config=None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(
            config=config,
            export_config=export_config,
            import_config=import_config,
            executor=executor,
            logger=logger,
        )
