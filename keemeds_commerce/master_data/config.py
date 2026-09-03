"""
Master Data Configuration

Dataclass-based, centralized configuration for the KeeMeds master data
generator. This is the single source of truth for every setting the
foundation and its future generators rely on.

Responsibilities
----------------
- Define the logging configuration (level, format, timestamping)
- Define the source directory that holds the master files
- Define each master data entity (Brands, Manufacturers, Item Groups, UOMs)
- Define the Medicine generation rules
- Define the Excel export configuration and ERPNext item import columns
- Provide a single, immutable ``MasterDataConfig`` value object

New entities can be added to the tuple returned by
:func:`default_entities` without touching any other module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

#: The repository root of the ``master_data`` package. Used to resolve the
#: default source directory relative to the package itself.
PACKAGE_DIR = Path(__file__).resolve().parent

#: Default directory that holds the raw (un-normalized) master source files.
DEFAULT_SOURCE_DIR = PACKAGE_DIR / "source"


def default_bench_root() -> Path:
    """
    Resolve the default Bench workspace root.

    The package lives at ``<bench>/apps/<app>/<app>/master_data``, so the Bench
    root sits three directories above the package. This mirrors how
    :func:`default_image_output_dir` derives the site path. The returned path is
    validated later by the Bench runtime; it is a best-effort default here.
    """
    return PACKAGE_DIR.parents[3]


def default_image_output_dir() -> Path:
    """
    Resolve the default directory for the generated item images.

    The images are stored as public static files under the ERPNext site so the
    running application can serve them at ``/files/item_images``. The path is
    derived from the package location (``<bench>/apps/keemeds_commerce``) and
    falls back to the configured KeeMeds site directory, mirroring the path the
    :class:`ImageMappingConfig` uses for its ``Image Path`` field.
    """
    bench_root = PACKAGE_DIR.parents[3]
    return bench_root / "sites" / "keemeds-commerce.local" / "public" / "files" / "item_images"


class FileType(StrEnum):
    """
    The supported source file formats.

    Adding a new member here only requires registering a matching reader in
    the reader registry; the loader itself stays unchanged.
    """

    CSV = "csv"
    EXCEL = "excel"


@dataclass(frozen=True)
class LoggingConfig:
    """
    Logging settings for the master data generator.
    """

    level: str = "INFO"
    format: str = "{asctime} | {levelname:7s} | {module:<24s} | {message}"
    style: str = "{"
    date_format: str = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class MedicineConfig:
    """
    Generation rules for the Medicine generator (Phase 2).

    These rules are centralized here so they can be tuned without touching
    generator logic. New generators add their own config dataclass and expose
    it on :class:`MasterDataConfig` in the same way.

    Attributes
    ----------
    target_count:
        Exact number of unique medicine items to generate.
    batch_size:
        Number of items per internally-split batch.
    item_code_prefix:
        Prefix prepended to every generated item code.
    item_code_width:
        Zero-padded width of the numeric portion of the item code.
    countries_of_origin:
        Ordered list of countries cycled through when assigning the
        ``country_of_origin`` field (must be non-empty).
    shelf_life_min_days:
        Lower bound (inclusive) of the deterministic shelf-life range.
    shelf_life_max_days:
        Upper bound (inclusive) of the deterministic shelf-life range.
    """

    target_count: int = 300
    batch_size: int = 100
    item_code_prefix: str = "MED"
    item_code_width: int = 3
    countries_of_origin: tuple[str, ...] = ("India",)
    shelf_life_min_days: int = 730
    shelf_life_max_days: int = 1825


@dataclass(frozen=True)
class ExportColumn:
    """
    A single column of the ERPNext Item Import template.

    Attributes
    ----------
    name:
        The exact ERPNext Item Import column header.
    attribute:
        The corresponding attribute on the :class:`~master_data.item_models.Item`
        model, by which the export value is resolved.
    """

    name: str
    attribute: str


#: The ERPNext Item Import template columns, in the exact required order.
#: The same, order-stable set is shared by every generator so any
#: :class:`~master_data.item_models.Item` can be exported without modification.
ITEM_IMPORT_COLUMNS: tuple[ExportColumn, ...] = (
    ExportColumn("Item Code", "item_code"),
    ExportColumn("Item Group", "item_group"),
    ExportColumn("Default Unit of Measure", "default_uom"),
    ExportColumn("Item Name", "item_name"),
    ExportColumn("Brand", "brand"),
    ExportColumn("Description", "description"),
    ExportColumn("Maintain Stock", "maintain_stock"),
    ExportColumn("Allow Sales", "allow_sales"),
    ExportColumn("Allow Purchase", "allow_purchase"),
    ExportColumn("Has Batch No", "has_batch_no"),
    ExportColumn("Has Expiry Date", "has_expiry_date"),
    ExportColumn("Shelf Life In Days", "shelf_life_in_days"),
    ExportColumn("Country of Origin", "country_of_origin"),
    ExportColumn("Default Item Manufacturer", "default_item_manufacturer"),
    ExportColumn("Has Variants", "has_variants"),
)

#: Attribute names that must hold a non-blank value for a record to be exported.
REQUIRED_ITEM_ATTRIBUTES: tuple[str, ...] = (
    "item_code",
    "item_name",
    "item_group",
    "default_uom",
    "brand",
    "default_item_manufacturer",
    "country_of_origin",
)


#: The ERPNext Item Price import template columns, in export order.
ITEM_PRICE_COLUMNS: tuple[ExportColumn, ...] = (
    ExportColumn("Item Code", "item_code"),
    ExportColumn("Price List", "price_list"),
    ExportColumn("Price List Rate", "rate"),
    ExportColumn("Currency", "currency"),
)

#: The ERPNext Opening Stock import template columns, in export order.
OPENING_STOCK_COLUMNS: tuple[ExportColumn, ...] = (
    ExportColumn("Item Code", "item_code"),
    ExportColumn("Warehouse", "warehouse"),
    ExportColumn("Opening Quantity", "opening_quantity"),
    ExportColumn("Valuation Rate", "valuation_rate"),
)

#: The Item Image Mapping template columns, in export order.
IMAGE_MAPPING_COLUMNS: tuple[ExportColumn, ...] = (
    ExportColumn("Item Code", "item_code"),
    ExportColumn("Image Path", "image_path"),
)

#: Attribute names that must be non-blank for an Item Price record to export.
REQUIRED_PRICE_ATTRIBUTES: tuple[str, ...] = ("item_code", "price_list", "rate", "currency")

#: Attribute names that must be non-blank for an Opening Stock record to export.
REQUIRED_STOCK_ATTRIBUTES: tuple[str, ...] = (
    "item_code",
    "warehouse",
    "opening_quantity",
    "valuation_rate",
)

#: Attribute names that must be non-blank for an Image Mapping record to export.
REQUIRED_IMAGE_ATTRIBUTES: tuple[str, ...] = ("item_code", "image_path")


#: The ERPNext Brand import template columns, in export order.
BRAND_IMPORT_COLUMNS: tuple[ExportColumn, ...] = (
    ExportColumn("Brand Name", "name"),
)

#: Attribute names that must be non-blank for a Brand record to export.
REQUIRED_BRAND_ATTRIBUTES: tuple[str, ...] = ("name",)

#: The ERPNext Manufacturer import template columns, in export order.
MANUFACTURER_IMPORT_COLUMNS: tuple[ExportColumn, ...] = (
    ExportColumn("Short Name", "short_name"),
    ExportColumn("Full Name", "full_name"),
)

#: Attribute names that must be non-blank for a Manufacturer record to export.
REQUIRED_MANUFACTURER_ATTRIBUTES: tuple[str, ...] = ("short_name", "full_name")

#: The ERPNext Item Group import template columns, in export order.
ITEM_GROUP_IMPORT_COLUMNS: tuple[ExportColumn, ...] = (
    ExportColumn("Item Group Name", "name"),
    ExportColumn("Parent Item Group", "parent_item_group"),
    ExportColumn("Is Group", "is_group"),
)

#: Attribute names that must be non-blank for an Item Group record to export.
REQUIRED_ITEM_GROUP_ATTRIBUTES: tuple[str, ...] = ("name", "parent_item_group")

#: The ERPNext UOM import template columns, in export order.
UOM_IMPORT_COLUMNS: tuple[ExportColumn, ...] = (
    ExportColumn("UOM Name", "name"),
)

#: Attribute names that must be non-blank for a UOM record to export.
REQUIRED_UOM_ATTRIBUTES: tuple[str, ...] = ("name",)

#: The ERPNext Item Attribute import template columns, in export order.
ITEM_ATTRIBUTE_IMPORT_COLUMNS: tuple[ExportColumn, ...] = (
    ExportColumn("Attribute Name", "name"),
)

#: Attribute names that must be non-blank for an Item Attribute record to export.
REQUIRED_ITEM_ATTRIBUTE_ATTRIBUTES: tuple[str, ...] = ("name",)

#: The ERPNext Item Attribute Value import template columns, in export order.
#: These nest the child Item Attribute Values rows under the parent
#: ``Attribute Name`` using the standard ``Label (Table Field Label)`` headers.
ITEM_ATTRIBUTE_VALUE_IMPORT_COLUMNS: tuple[ExportColumn, ...] = (
    ExportColumn("Attribute Name", "attribute"),
    ExportColumn("Attribute Value (Item Attribute Values)", "attribute_value"),
    ExportColumn("Abbreviation (Item Attribute Values)", "abbr"),
)

#: Attribute names that must be non-blank for an Item Attribute Value row to export.
REQUIRED_ITEM_ATTRIBUTE_VALUE_ATTRIBUTES: tuple[str, ...] = (
    "attribute",
    "attribute_value",
    "abbr",
)


@dataclass(frozen=True)
class ExportConfig:
    """
    Centralized export rules for the Excel exporter.

    Attributes
    ----------
    output_dir:
        Base directory under which generated files are written.
    subdirectory:
        Sub-directory under ``output_dir`` that receives the files.
    filename_prefix:
        Leading token of the generated file names (e.g. ``Item_Master``).
    file_extension:
        File extension, including the leading dot.
    sheet_title:
        Title of the worksheet written by the exporter.
    freeze_header_row:
        Whether the header row is frozen (``A2`` panes).
    bold_header:
        Whether the header row is rendered in bold.
    auto_size_columns:
        Whether column widths are auto-sized to their content.
    columns:
        The ERPNext Item Import template columns, in export order.
    required_attributes:
        Item attributes that must be non-blank before a record is exported.
    """

    output_dir: Path = Path(PACKAGE_DIR) / "output"
    subdirectory: str = "items"
    filename_prefix: str = "Item_Master"
    file_extension: str = ".xlsx"
    sheet_title: str = "Item Import"
    freeze_header_row: bool = True
    bold_header: bool = True
    auto_size_columns: bool = True
    columns: tuple[ExportColumn, ...] = ITEM_IMPORT_COLUMNS
    required_attributes: tuple[str, ...] = REQUIRED_ITEM_ATTRIBUTES


@dataclass(frozen=True)
class PriceConfig:
    """
    Generation rules for item prices (Phase 4 catalog enrichment).

    Attributes
    ----------
    price_lists:
        The price lists for which a price record is generated per item.
    currency:
        Currency assigned to every price record.
    base_rate:
        Lowest selling rate used to seed the deterministic price series.
    rate_step:
        Increment applied to the selling rate for each successive item.
    buying_factor:
        Multiplier applied to the selling rate to derive the buying rate.
    """

    price_lists: tuple[str, ...] = ("Standard Selling", "Standard Buying")
    currency: str = "INR"
    base_rate: float = 20.0
    rate_step: float = 5.0
    buying_factor: float = 0.8


@dataclass(frozen=True)
class StockConfig:
    """
    Generation rules for opening stock (Phase 4 catalog enrichment).

    Attributes
    ----------
    warehouses:
        Warehouses cycled through when assigning opening stock records.
    quantity_min:
        Lower bound (inclusive) of the deterministic opening quantity.
    quantity_max:
        Upper bound (inclusive) of the deterministic opening quantity.
    """

    warehouses: tuple[str, ...] = ("Finished Goods",)
    quantity_min: int = 10
    quantity_max: int = 100


@dataclass(frozen=True)
class ImageMappingConfig:
    """
    Generation rules for item image mappings (Phase 4 catalog enrichment).

    Attributes
    ----------
    image_dir:
        Directory scanned for available item image filenames.
    image_url_root:
        ERPNext URL prefix prepended to every image filename.
    extension:
        Expected image file extension (including the leading dot).
    placeholder_extension:
        Extension used for deterministic placeholder image paths.
    """

    image_dir: Path = PACKAGE_DIR / "item_images"
    image_url_root: str = "/files/item_images"
    extension: str = ".webp"
    placeholder_extension: str = ".webp"


@dataclass(frozen=True)
class ImageGeneratorConfig:
    """
    Generation rules for the Phase 7 placeholder image generator.

    The generator creates one professional placeholder medicine image and then
    produces every item image file required by the current catalog, either as a
    symbolic link or a file copy of that placeholder. Files that already exist
    (real product images) are never overwritten.

    Attributes
    ----------
    name:
        Human-readable display name of the generator.
    placeholder_name:
        File stem of the shared placeholder image (e.g. that yields
        ``medicine-placeholder.svg`` and ``medicine-placeholder.webp``).
    extension:
        The output image file extension (including the leading dot) for the
        per-item files, e.g. ``".webp"``.
    svg_suffix:
        File suffix of the vector placeholder source, including the dot.
    output_dir:
        Directory that receives the generated item image files. Defaults to the
        ERPNext site's public ``files/item_images`` directory.
    catalog_workbook:
        Sub-directory (relative to the export ``output_dir``) of the Item Image
        Mapping workbook whose rows list the expected item image filenames.
    catalog_filename:
        File name of the Item Image Mapping workbook within ``catalog_workbook``.
    """

    name: str = "Placeholder Images"
    placeholder_name: str = "medicine-placeholder"
    extension: str = ".webp"
    svg_suffix: str = ".svg"
    output_dir: Path = field(default_factory=default_image_output_dir)
    catalog_subdirectory: str = "images"
    catalog_filename: str = "Item_Image_Mapping.xlsx"

    @property
    def svg_filename(self) -> str:
        """File name of the vector placeholder source."""
        return f"{self.placeholder_name}{self.svg_suffix}"

    @property
    def webp_filename(self) -> str:
        """File name of the converted webp placeholder."""
        return f"{self.placeholder_name}{self.extension}"

    def placeholder_source(self) -> Path:
        """The placeholder file used as the source for item image copies."""
        return self.output_dir / self.svg_filename


@dataclass(frozen=True)
class EnrichmentExportConfig:
    """
    Centralized export rules for a single catalog-enrichment Excel file.

    Attributes
    ----------
    key:
        The generator key whose records this spec exports (e.g. ``"price"``).
        Used by the pipeline to associate an enrichment generator with its
        export specification without orchestration changes.
    subdirectory:
        Sub-directory under ``output_dir`` that receives the file.
    filename:
        Exact file name of the generated workbook.
    sheet_title:
        Title of the worksheet written by the exporter.
    columns:
        The ERPNext import template columns, in export order.
    required_attributes:
        Record attributes that must be non-blank to be exported.
    """

    key: str
    subdirectory: str
    filename: str
    sheet_title: str
    columns: tuple[ExportColumn, ...]
    required_attributes: tuple[str, ...]


@dataclass(frozen=True)
class ReportConfig:
    """
    Centralized rules for writing the Phase 5 execution reports.

    Attributes
    ----------
    subdirectory:
        Sub-directory under the export ``output_dir`` that receives the reports.
    summary_json_filename:
        File name of the JSON generation summary.
    summary_xlsx_filename:
        File name of the Excel generation summary.
    report_log_filename:
        File name of the human-readable execution log.
    """

    subdirectory: str = "reports"
    summary_json_filename: str = "generation_summary.json"
    summary_xlsx_filename: str = "generation_summary.xlsx"
    report_log_filename: str = "generation_report.log"


@dataclass(frozen=True)
class ImporterConfig:
    """
    Centralized rules for a single ERPNext importer (Phase 6).

    Each catalog export has an importer that feeds its generated file(s) into
    ERPNext through the standard Frappe Data Import API. The rules here are
    resolved against the generated ``master_data/output`` tree.

    Attributes
    ----------
    key:
        Stable, machine-readable importer identifier (e.g. ``"item"``).
    name:
        Human-readable display name (e.g. ``"Item Master"``).
    doctype:
        The ERPNext DocType the generated file imports into.
    import_type:
        ``"insert"`` for new records or ``"update"`` for existing records.
    subdirectory:
        Sub-directory under the export ``output_dir`` that holds the source
        file(s), relative to ``output_dir``.
    filenames:
        The exact generated file name(s), or glob pattern(s) to match, under
        ``subdirectory``.
    required_columns:
        Column headers that must be present in each source file.
    is_required:
        Whether the importer's files must exist for the pipeline to run.
    """

    key: str
    name: str
    doctype: str
    import_type: str
    subdirectory: str
    filenames: tuple[str, ...]
    required_columns: tuple[str, ...]
    is_required: bool = True


@dataclass(frozen=True)
class ImportConfig:
    """
    Centralized rules for the Phase 6 ERPNext import framework.

    Attributes
    ----------
    import_report_filename:
        File name of the JSON import report under the reports directory.
    import_log_filename:
        File name of the human-readable import log.
    default_import_type:
        The import type assumed by importers that do not declare one.
    submit_after_import:
        Whether imported documents are submitted after import.
    """

    import_report_filename: str = "import_report.json"
    import_log_filename: str = "import_report.log"
    default_import_type: str = "insert"
    submit_after_import: bool = False

    def importers(self) -> tuple["ImporterConfig", ...]:
        """
        Return the ordered importers in ERPNext dependency order.

        The master entities (UOM, Item Group, Brand, Manufacturer, Item
        Attribute, Item Attribute Value) must precede the Item Master because
        items reference them. Item Master must precede Item Prices / Opening
        Stock / Image Mapping because the latter reference Item records. The
        order here is the canonical execution order for the data import
        pipeline.
        """
        return (
            ImporterConfig(
                key="uom",
                name="UOM",
                doctype="UOM",
                import_type="insert",
                subdirectory="uoms",
                filenames=("UOMs.xlsx",),
                required_columns=("UOM Name",),
            ),
            ImporterConfig(
                key="item_group",
                name="Item Group",
                doctype="Item Group",
                import_type="insert",
                subdirectory="item_groups",
                filenames=("Item_Groups.xlsx",),
                required_columns=("Item Group Name",),
            ),
            ImporterConfig(
                key="brand",
                name="Brand",
                doctype="Brand",
                import_type="insert",
                subdirectory="brands",
                filenames=("Brands.xlsx",),
                required_columns=("Brand Name",),
            ),
            ImporterConfig(
                key="manufacturer",
                name="Manufacturer",
                doctype="Manufacturer",
                import_type="insert",
                subdirectory="manufacturers",
                filenames=("Manufacturers.xlsx",),
                required_columns=("Short Name",),
            ),
            ImporterConfig(
                key="item_attribute",
                name="Item Attribute",
                doctype="Item Attribute",
                import_type="insert",
                subdirectory="item_attributes",
                filenames=("Item_Attributes.xlsx",),
                required_columns=("Attribute Name",),
            ),
            ImporterConfig(
                key="item_attribute_value",
                name="Item Attribute Value",
                doctype="Item Attribute",
                import_type="insert",
                subdirectory="item_attribute_values",
                filenames=("Item_Attribute_Values.xlsx",),
                required_columns=("Attribute Name",),
            ),
            ImporterConfig(
                key="item",
                name="Item Master",
                doctype="Item",
                import_type="insert",
                subdirectory="items",
                filenames=("*Item_Master*.xlsx",),
                required_columns=("Item Code",),
            ),
            ImporterConfig(
                key="price",
                name="Item Price",
                doctype="Item Price",
                import_type="insert",
                subdirectory="prices",
                filenames=("Item_Prices.xlsx",),
                required_columns=("Item Code", "Price List", "Price List Rate"),
            ),
            ImporterConfig(
                key="stock",
                name="Opening Stock",
                doctype="Stock Ledger Entry",
                import_type="insert",
                subdirectory="stock",
                filenames=("Opening_Stock.xlsx",),
                required_columns=("Item Code", "Warehouse", "Opening Quantity"),
            ),
            ImporterConfig(
                key="image",
                name="Image Mapping",
                doctype="Item",
                import_type="update",
                subdirectory="images",
                filenames=("Item_Image_Mapping.xlsx",),
                required_columns=("Item Code", "Image Path"),
            ),
        )


@dataclass(frozen=True)
class BenchConfig:
    """
    Rules for locating and booting the active ERPNext Bench runtime (Phase 8).

    The import pipeline runs inside the Bench via the standard Frappe Data Import
    API. This configuration drives the Bench runtime integration without changing
    the import executor.

    Attributes
    ----------
    bench_root:
        The Bench workspace root. Defaults to the directory that contains the
        ``sites`` and ``env`` directories, derived from the package location.
    site:
        The ERPNext site to connect to. When unset (empty string) the active
        site is discovered from the Bench ``default_site`` configuration.
    """

    bench_root: Path = field(default_factory=default_bench_root)
    site: str = ""


@dataclass(frozen=True)
class EntityConfig:
    """
    Definition of a single master data entity and its source file.

    Attributes
    ----------
    key:
        Stable, machine-readable identifier (e.g. ``"brand"``).
    name:
        Human-readable display name (e.g. ``"Brands"``).
    filename:
        Name of the source file, relative to the source directory.
    file_type:
        Format of the source file (CSV or Excel).
    required_columns:
        Columns that must be present in the source file header.
    value_column:
        The column whose values are extracted and normalized.
    """

    key: str
    name: str
    filename: str
    file_type: FileType
    required_columns: tuple[str, ...]
    value_column: str


def default_entities() -> tuple[EntityConfig, ...]:
    """
    Return the default master data entity definitions.

    This is intentionally a function so the tuple is constructed fresh for
    each configuration and future phases can register additional entities
    without modifying existing ones.
    """

    return (
        EntityConfig(
            key="brand",
            name="Brands",
            filename="brands.csv",
            file_type=FileType.CSV,
            required_columns=("brand",),
            value_column="brand",
        ),
        EntityConfig(
            key="manufacturer",
            name="Manufacturers",
            filename="manufacturers.csv",
            file_type=FileType.CSV,
            required_columns=("manufacturer",),
            value_column="manufacturer",
        ),
        EntityConfig(
            key="item_group",
            name="Item Groups",
            filename="item_groups.csv",
            file_type=FileType.CSV,
            required_columns=("item_group",),
            value_column="item_group",
        ),
        EntityConfig(
            key="uom",
            name="UOMs",
            filename="uoms.csv",
            file_type=FileType.CSV,
            required_columns=("uom",),
            value_column="uom",
        ),
        EntityConfig(
            key="item_attribute",
            name="Item Attributes",
            filename="item_attributes.csv",
            file_type=FileType.CSV,
            required_columns=("attribute",),
            value_column="attribute",
        ),
        EntityConfig(
            key="item_attribute_value",
            name="Item Attribute Values",
            filename="item_attribute_values.csv",
            file_type=FileType.CSV,
            required_columns=("attribute", "attribute_value", "abbr"),
            value_column="attribute_value",
        ),
    )


@dataclass(frozen=True)
class MasterDataConfig:
    """
    Immutable, centralized configuration for the whole generator.

    Attributes
    ----------
    source_dir:
        Directory that contains the raw master source files.
    logging:
        Logging configuration.
    entities:
        Tuple of configured master data entity definitions.
    medicine:
        Generation rules for the Medicine generator.
    price:
        Generation rules for the Item Price generator.
    stock:
        Generation rules for the Opening Stock generator.
    image_mapping:
        Generation rules for the Image Mapping generator.
    image_generator:
        Generation rules for the Phase 7 placeholder image generator.
    export:
        Export rules for the Excel exporter.
    reports:
        Rules for writing the Phase 5 execution reports.
        Rules for writing the Phase 5 execution reports.
    price_export:
        Export rules for the Item Price workbook.
    stock_export:
        Export rules for the Opening Stock workbook.
    image_mapping_export:
        Export rules for the Image Mapping workbook.
    uom_export:
        Export rules for the UOM workbook.
    item_group_export:
        Export rules for the Item Group workbook.
    brand_export:
        Export rules for the Brand workbook.
    manufacturer_export:
        Export rules for the Manufacturer workbook.
    item_attribute_export:
        Export rules for the Item Attribute workbook.
    item_attribute_value_export:
        Export rules for the Item Attribute Value workbook.
    import_config:
        Rules for the Phase 6 ERPNext import framework.
    bench:
        Rules for locating and booting the active Bench runtime (Phase 8).

    price_lists:
        Alias for :attr:`price.price_lists` for CLI display convenience.
    """

    source_dir: Path = DEFAULT_SOURCE_DIR
    logging: LoggingConfig = LoggingConfig()
    entities: tuple[EntityConfig, ...] = field(default_factory=default_entities)
    medicine: MedicineConfig = MedicineConfig()
    price: PriceConfig = PriceConfig()
    stock: StockConfig = StockConfig()
    image_mapping: ImageMappingConfig = ImageMappingConfig()
    image_generator: ImageGeneratorConfig = ImageGeneratorConfig()
    export: ExportConfig = ExportConfig()
    reports: ReportConfig = ReportConfig()
    import_config: ImportConfig = ImportConfig()
    bench: BenchConfig = BenchConfig()
    price_export: EnrichmentExportConfig = EnrichmentExportConfig(
        key="price",
        subdirectory="prices",
        filename="Item_Prices.xlsx",
        sheet_title="Item Price Import",
        columns=ITEM_PRICE_COLUMNS,
        required_attributes=REQUIRED_PRICE_ATTRIBUTES,
    )
    stock_export: EnrichmentExportConfig = EnrichmentExportConfig(
        key="stock",
        subdirectory="stock",
        filename="Opening_Stock.xlsx",
        sheet_title="Opening Stock Import",
        columns=OPENING_STOCK_COLUMNS,
        required_attributes=REQUIRED_STOCK_ATTRIBUTES,
    )
    image_mapping_export: EnrichmentExportConfig = EnrichmentExportConfig(
        key="image_mapping",
        subdirectory="images",
        filename="Item_Image_Mapping.xlsx",
        sheet_title="Item Image Mapping",
        columns=IMAGE_MAPPING_COLUMNS,
        required_attributes=REQUIRED_IMAGE_ATTRIBUTES,
    )
    uom_export: EnrichmentExportConfig = EnrichmentExportConfig(
        key="uom",
        subdirectory="uoms",
        filename="UOMs.xlsx",
        sheet_title="UOM Import",
        columns=UOM_IMPORT_COLUMNS,
        required_attributes=REQUIRED_UOM_ATTRIBUTES,
    )
    item_group_export: EnrichmentExportConfig = EnrichmentExportConfig(
        key="item_group",
        subdirectory="item_groups",
        filename="Item_Groups.xlsx",
        sheet_title="Item Group Import",
        columns=ITEM_GROUP_IMPORT_COLUMNS,
        required_attributes=REQUIRED_ITEM_GROUP_ATTRIBUTES,
    )
    brand_export: EnrichmentExportConfig = EnrichmentExportConfig(
        key="brand",
        subdirectory="brands",
        filename="Brands.xlsx",
        sheet_title="Brand Import",
        columns=BRAND_IMPORT_COLUMNS,
        required_attributes=REQUIRED_BRAND_ATTRIBUTES,
    )
    manufacturer_export: EnrichmentExportConfig = EnrichmentExportConfig(
        key="manufacturer",
        subdirectory="manufacturers",
        filename="Manufacturers.xlsx",
        sheet_title="Manufacturer Import",
        columns=MANUFACTURER_IMPORT_COLUMNS,
        required_attributes=REQUIRED_MANUFACTURER_ATTRIBUTES,
    )
    item_attribute_export: EnrichmentExportConfig = EnrichmentExportConfig(
        key="item_attribute",
        subdirectory="item_attributes",
        filename="Item_Attributes.xlsx",
        sheet_title="Item Attribute Import",
        columns=ITEM_ATTRIBUTE_IMPORT_COLUMNS,
        required_attributes=REQUIRED_ITEM_ATTRIBUTE_ATTRIBUTES,
    )
    item_attribute_value_export: EnrichmentExportConfig = EnrichmentExportConfig(
        key="item_attribute_value",
        subdirectory="item_attribute_values",
        filename="Item_Attribute_Values.xlsx",
        sheet_title="Item Attribute Value Import",
        columns=ITEM_ATTRIBUTE_VALUE_IMPORT_COLUMNS,
        required_attributes=REQUIRED_ITEM_ATTRIBUTE_VALUE_ATTRIBUTES,
    )

    def entity(self, key: str) -> EntityConfig | None:
        """
        Return the entity definition for ``key`` or ``None`` if unknown.
        """

        for candidate in self.entities:
            if candidate.key == key:
                return candidate
        return None

    def source_file_for(self, entity: EntityConfig) -> Path:
        """
        Resolve the absolute source file path for an entity definition.
        """

        return self.source_dir / entity.filename

    def enrichment_exports(self) -> tuple[EnrichmentExportConfig, ...]:
        """
        Return all configured catalog-enrichment export specifications.

        Each spec is tagged with the generator key whose records it exports.
        The pipeline uses this to associate a registered enrichment generator
        with its export spec, so adding a new generator + export spec requires
        no orchestration change.
        """

        return (self.price_export, self.stock_export, self.image_mapping_export)

    def master_exports(self) -> tuple[EnrichmentExportConfig, ...]:
        """
        Return all configured ERPNext master export specifications.

        These drive both the Phase 7 master exporters and importers and follow
        the ERPNext dependency order (UOM before Item Group before Brand before
        Manufacturer before Item Attribute before Item Attribute Value).
        """

        return (
            self.uom_export,
            self.item_group_export,
            self.brand_export,
            self.manufacturer_export,
            self.item_attribute_export,
            self.item_attribute_value_export,
        )

    def master_export_for(self, key: str) -> EnrichmentExportConfig | None:
        """
        Return the export specification for a master key, or ``None``.
        """

        for spec in self.master_exports():
            if spec.key == key:
                return spec
        return None

    def enrichment_export_for(self, key: str) -> EnrichmentExportConfig | None:
        """
        Return the export specification for an enrichment generator key.

        Returns ``None`` when no export is configured for the key (the records
        are still generated but not exported).
        """

        for spec in self.enrichment_exports():
            if spec.key == key:
                return spec
        return None

    @property
    def price_lists(self) -> tuple[str, ...]:
        """
        The configured item price lists.
        """

        return self.price.price_lists

    def importer_configs(self) -> tuple[ImporterConfig, ...]:
        """
        Return the ordered ERPNext importer configurations.

        The order returned is the canonical dependency order for the data
        import pipeline (Item Master before the enrichment imports).
        """

        return self.import_config.importers()

    def importer_config_for(self, key: str) -> ImporterConfig | None:
        """
        Return the importer configuration for ``key`` or ``None``.
        """

        for candidate in self.import_config.importers():
            if candidate.key == key:
                return candidate
        return None
