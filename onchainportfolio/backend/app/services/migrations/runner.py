# backend/app/services/migrations/runner.py
"""
One-shot migration runner.

Each migration is registered by a unique name.  The runner checks the
`migrations` collection before executing; if the name is already recorded,
the migration is skipped.  This replaces the previous pattern of running
migrate_all_users() on every application startup.

Usage (from startup code):
    from app.services.migrations.runner import run_migrations
    run_migrations()
"""
import logging
from datetime import datetime, timezone
from typing import Callable

from app.services.db import migrations_collection

logger = logging.getLogger(__name__)


def _is_applied(name: str) -> bool:
    return migrations_collection.find_one({"name": name}) is not None


def _mark_applied(name: str) -> None:
    migrations_collection.update_one(
        {"name": name},
        {"$set": {"name": name, "applied_at": datetime.now(timezone.utc), "success": True}},
        upsert=True,
    )


def run_once(name: str, fn: Callable[[], None]) -> bool:
    """
    Run `fn` exactly once (identified by `name`).

    Returns True if the migration ran, False if it was already applied.
    Any exception from `fn` is logged but does NOT crash the app — the
    migration will be retried on the next startup.
    """
    if _is_applied(name):
        logger.info(f"[MIGRATION] '{name}' already applied, skipping")
        return False

    logger.info(f"[MIGRATION] Running '{name}'...")
    try:
        fn()
        _mark_applied(name)
        logger.info(f"[MIGRATION] '{name}' completed successfully")
        return True
    except Exception as e:
        logger.error(f"[MIGRATION] '{name}' failed: {e}", exc_info=True)
        # Don't mark as applied — allow retry on next boot
        return False


def run_migrations() -> None:
    """
    Execute all registered one-shot migrations in order.
    Safe to call on every startup — each migration is idempotent via the DB record.
    """
    logger.info("[MIGRATION] Starting migration runner...")

    # ── Migration 1: Move embedded wallets to the wallets collection ──────────
    def migrate_wallets():
        from app.services.wallet_service import migrate_all_users
        stats = migrate_all_users()
        migrated = stats.get("total_wallets_migrated", 0)
        if migrated > 0:
            logger.info(f"[MIGRATION] migrate_wallets: {migrated} wallets migrated")
        else:
            logger.info("[MIGRATION] migrate_wallets: nothing to migrate")

    run_once("migrate_embedded_wallets_to_collection_v1", migrate_wallets)

    # ── Migration 2: Backfill is_active + deleted_at on existing wallet docs ──
    def backfill_wallet_is_active():
        """
        Wallets created before the soft-delete upgrade lack is_active / deleted_at.
        Set is_active=True and deleted_at=None for every wallet that has no value
        for these fields.  Idempotent: documents already containing is_active are
        untouched by the $exists filter.
        """
        from app.services.db import wallets_collection
        result = wallets_collection.update_many(
            {"is_active": {"$exists": False}},
            {"$set": {"is_active": True, "deleted_at": None}}
        )
        logger.info(
            f"[MIGRATION] backfill_wallet_is_active: {result.modified_count} wallets updated"
        )

    run_once("backfill_wallet_is_active_v1", backfill_wallet_is_active)

    logger.info("[MIGRATION] Migration runner finished")
