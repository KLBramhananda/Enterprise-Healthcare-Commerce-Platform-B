"""
Commerce Configuration

Centralized, immutable configuration for the Phase 10 Commerce (Product
Catalog) API layer.

Following Clean Architecture, all tunables for the commerce API live here so
the controllers and services never hard-code limits or URLs.

Attributes
----------
default_page_size:
    Default number of products returned per page when none is supplied.
max_page_size:
    Upper bound enforced on any requested page size (defensive ceiling).
item_image_url_prefix:
    Public URL prefix (under the ERPNext site URL) where the Phase 9.5 product
    gallery images are served. The gallery file names (``MED-001-1.webp`` ...)
    are appended to this prefix to build public URLs. Never a filesystem path.
selling_price_list:
    Name of the ERPNext price list used as the storefront selling price.
published_item_groups:
    Optional allow-list of Item Group names considered "published". When empty,
    every enabled item is considered published. Enables future catalog scoping.
reserved_item_group_suffixes:
    Item-group names that must never be surfaced (an empty default).
warehouses:
    Optional allow-list of Warehouse names whose stock is aggregated for stock
    availability. When empty every (non-group) warehouse is included.
image_gallery_slots:
    Number of gallery images per product (mirrors the Phase 9.5 ``images_per_item``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True)
class CommerceConfig:
    """
    Immutable configuration for the commerce product-catalog API.
    """

    default_page_size: int = 20
    max_page_size: int = 100
    item_image_url_prefix: str = "/files/item_images"
    selling_price_list: str = "Standard Selling"
    published_item_groups: tuple[str, ...] = ()
    warehouses: tuple[str, ...] = ()
    image_gallery_slots: int = 3
    image_extension: str = ".webp"

    #: Valid ``sort`` values accepted by the listing API.
    sort_options: Final[tuple[str, ...]] = ("item_name", "item_code", "price", "newest")
    #: Default sort when none supplied.
    default_sort: Final[str] = "item_name"
    #: The ERPNext Item base URL fragment used to build public gallery URLs.
    _gallery_filename_prefix: Final[str] = ""

    def gallery_filenames(self, item_code: str) -> list[str]:
        """
        Return the ordered public-file gallery names for an item code.

        Mirrors the deterministic Phase 9.5 naming (``MED-001-1.webp`` ...
        ``MED-001-<slots>.webp``) so the storefront images match the generated
        gallery without any filesystem dependency.
        """
        return [
            f"{item_code}-{slot + 1}{self.image_extension}"
            for slot in range(self.image_gallery_slots)
        ]
