import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from models.config import LocalSession

DEFAULT_FAQS = [
    {
        "question": "Can I use Kluda POS when my shop has no internet?",
        "answer": "Yes! Kluda is built with an offline-first mesh engine. Your counter keeps ringing up sales, scanning barcodes, calculating discounts, and issuing thermal receipts even during total internet blackouts. As soon as connectivity returns, all sales sync automatically with the cloud.",
        "category": "offline",
        "display_order": 1,
        "is_published": True,
    },
    {
        "question": "Do I need to buy expensive supermarket POS machines?",
        "answer": "Not at all. You can turn the Android phone, iPhone, tablet, or laptop you already own into a fast checkout register. Kluda uses your device camera for instant barcode scanning and pairs wirelessly with budget thermal receipt printers.",
        "category": "hardware",
        "display_order": 2,
        "is_published": True,
    },
    {
        "question": "How does Kluda prevent cashier theft and cash pocketing?",
        "answer": "Every single item that leaves your shelf requires a recorded sale, locked to the cashier on duty. Cashiers cannot edit prices, delete past sales, or alter stock counts without manager authorization. At the end of each shift, Kluda reconciles expected cash against actual drawer counts.",
        "category": "general",
        "display_order": 3,
        "is_published": True,
    },
    {
        "question": "Can I connect a physical barcode scanner and thermal receipt printer?",
        "answer": "Yes. Kluda supports both handheld USB and Bluetooth barcode scanners. It also integrates directly via WebBluetooth and WebUSB with standard 58mm and 80mm ESC/POS thermal receipt printers (such as GOOJPRT, Xprinter, and Sunmi) with zero drivers needed on Android and PC.",
        "category": "hardware",
        "display_order": 4,
        "is_published": True,
    },
    {
        "question": "How does the customer debt and credit ledger work?",
        "answer": "Instead of tracking customer credits in paper notebooks that get torn or misplaced, you can select 'Debt' at checkout. Kluda records the exact balance against the customer's profile, logs partial repayments, and shows outstanding debts directly at the counter.",
        "category": "general",
        "display_order": 5,
        "is_published": True,
    },
    {
        "question": "What happens if I have multiple branches or stores?",
        "answer": "On the Merchant Growth and Enterprise tiers, you can manage multiple store branches from a single dashboard. View live sales across all stores in real time, compare store revenues, and track stock transfers between warehouses from anywhere in the world.",
        "category": "billing",
        "display_order": 6,
        "is_published": True,
    },
    {
        "question": "Can I pay for Kluda with a daily or weekly pass?",
        "answer": "Yes. We understand cash flow flexibility for retailers. In addition to monthly and annual subscriptions, Kluda offers flexible sachet pricing (such as 24-hour daily passes and weekly plans) so you only pay for what you need.",
        "category": "billing",
        "display_order": 7,
        "is_published": True,
    },
    {
        "question": "Is my store's sales and customer data safe?",
        "answer": "Absolutely. Kluda guarantees that your sales, product prices, customer records, and financial numbers are 100% private. We NEVER sell, license, or share your store data with advertisers, competitors, or financial lenders.",
        "category": "general",
        "display_order": 8,
        "is_published": True,
    },
]


async def migrate_and_seed_faqs():
    async with LocalSession() as db:
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS faqs (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category VARCHAR(50) NOT NULL DEFAULT 'general',
                display_order INTEGER NOT NULL DEFAULT 0,
                is_published BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_faqs_category ON faqs (category)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_faqs_is_published ON faqs (is_published)"))
        await db.commit()
        print("faqs table verified/created.")

        # Seed if empty
        existing_count = await db.scalar(text("SELECT COUNT(*) FROM faqs"))
        if existing_count == 0:
            for faq in DEFAULT_FAQS:
                await db.execute(
                    text("""
                        INSERT INTO faqs (question, answer, category, display_order, is_published)
                        VALUES (:question, :answer, :category, :display_order, :is_published)
                    """),
                    faq
                )
            await db.commit()
            print(f"Seeded {len(DEFAULT_FAQS)} default FAQs.")
        else:
            print(f"faqs table already has {existing_count} records.")


if __name__ == "__main__":
    asyncio.run(migrate_and_seed_faqs())
