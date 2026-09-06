import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from models.config import LocalSession
from models.catalog import CatalogTemplate, CatalogItem


VALID_UNITS = {"piece", "kg", "g", "litre", "ml", "pack", "carton", "dozen", "bag"}


async def seed_catalog():
    json_path = Path(__file__).parent.parent / "catalog.json"
    if not json_path.exists():
        print(f"Error: Could not find catalog.json at {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    print(f"Loaded {len(catalog_data)} catalog groups from {json_path.name}\n")

    async with LocalSession() as db:
        total_created_templates = 0
        total_created_items = 0
        total_skipped_items = 0

        for idx, group in enumerate(catalog_data):
            group_name = group.get("group")
            slug = group.get("slug")
            description = group.get("description")
            icon = group.get("icon", "shopping-cart")
            items = group.get("items", [])

            if not slug or not group_name:
                continue

            # Check if template already exists
            template = await db.scalar(
                select(CatalogTemplate).where(CatalogTemplate.slug == slug)
            )

            if not template:
                template = CatalogTemplate(
                    name=group_name,
                    slug=slug,
                    description=description,
                    icon=icon,
                    is_active=True,
                    sort_order=idx,
                )
                db.add(template)
                await db.flush()
                await db.refresh(template)
                total_created_templates += 1
                print(f"[+] Created Template: '{group_name}' (slug: {slug}, id: {template.id})")
            else:
                print(f"[=] Found Existing Template: '{group_name}' (slug: {slug}, id: {template.id})")

            # Process items for this template
            group_created = 0
            group_skipped = 0

            for item in items:
                name = item.get("name")
                barcode = item.get("barcode")
                category = item.get("category", "General")
                unit_in = item.get("unit_in", "piece")
                if unit_in not in VALID_UNITS:
                    unit_in = "piece"

                # Prices stored in kobo (e.g. 250 Naira = 25000 kobo)
                raw_suggested = item.get("suggested_price", 0)
                raw_cost = item.get("cost_price", 0)
                suggested_price = int(round(float(raw_suggested) * 100))
                cost_price = int(round(float(raw_cost) * 100))
                desc = item.get("description")

                # Check if item exists in catalog_items for this template
                if barcode:
                    existing_item = await db.scalar(
                        select(CatalogItem).where(
                            CatalogItem.template_id == template.id,
                            CatalogItem.barcode == barcode,
                        )
                    )
                else:
                    existing_item = await db.scalar(
                        select(CatalogItem).where(
                            CatalogItem.template_id == template.id,
                            CatalogItem.name == name,
                        )
                    )

                if existing_item:
                    group_skipped += 1
                    total_skipped_items += 1
                    continue

                new_item = CatalogItem(
                    template_id=template.id,
                    name=name,
                    barcode=barcode,
                    category=category,
                    suggested_price=suggested_price,
                    cost_price=cost_price,
                    unit_in=unit_in,
                    description=desc,
                    is_active=True,
                )
                db.add(new_item)
                group_created += 1
                total_created_items += 1

            await db.flush()
            print(f"    -> Items: {group_created} added, {group_skipped} skipped\n")

        await db.commit()
        print("=========================================")
        print(f"Seeding Complete!")
        print(f"Templates Created: {total_created_templates}")
        print(f"Items Added:       {total_created_items}")
        print(f"Items Skipped:     {total_skipped_items}")
        print("=========================================")


if __name__ == "__main__":
    asyncio.run(seed_catalog())
