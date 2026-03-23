# backend/tests/test_migration_runner.py
"""
Unit tests for the one-shot migration runner.

Verifies that:
- run_once() executes a function exactly once
- run_once() skips when already applied
- run_once() does NOT mark as applied on failure (allows retry)
- run_migrations() registers and runs known migrations
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from datetime import datetime

import pytest

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_collection(already_applied: bool = False):
    """Return a mock MongoDB collection that simulates applied/unapplied state."""
    col = MagicMock()
    col.find_one.return_value = {"name": "test"} if already_applied else None
    col.update_one.return_value = MagicMock(modified_count=1)
    return col


# ---------------------------------------------------------------------------
# run_once
# ---------------------------------------------------------------------------

class TestRunOnce:
    def test_runs_function_when_not_applied(self):
        mock_col = _make_mock_collection(already_applied=False)
        fn = MagicMock()

        with patch("app.services.migrations.runner.migrations_collection", mock_col):
            from app.services.migrations.runner import run_once
            result = run_once("test_migration_v1", fn)

        fn.assert_called_once()
        assert result is True

    def test_marks_applied_after_success(self):
        mock_col = _make_mock_collection(already_applied=False)
        fn = MagicMock()

        with patch("app.services.migrations.runner.migrations_collection", mock_col):
            from app.services.migrations.runner import run_once
            run_once("test_migration_v1", fn)

        # update_one should have been called to mark it applied
        mock_col.update_one.assert_called_once()
        call_kwargs = mock_col.update_one.call_args
        # The $set should contain success=True
        assert call_kwargs[0][1]["$set"]["success"] is True

    def test_skips_when_already_applied(self):
        mock_col = _make_mock_collection(already_applied=True)
        fn = MagicMock()

        with patch("app.services.migrations.runner.migrations_collection", mock_col):
            from app.services.migrations.runner import run_once
            result = run_once("test_migration_v1", fn)

        fn.assert_not_called()
        assert result is False

    def test_does_not_mark_applied_on_failure(self):
        mock_col = _make_mock_collection(already_applied=False)

        def failing_fn():
            raise RuntimeError("Something went wrong")

        with patch("app.services.migrations.runner.migrations_collection", mock_col):
            from app.services.migrations.runner import run_once
            result = run_once("failing_migration_v1", failing_fn)

        # update_one should NOT be called on failure
        mock_col.update_one.assert_not_called()
        assert result is False

    def test_different_names_run_independently(self):
        call_order = []

        def make_fn(name):
            def fn():
                call_order.append(name)
            return fn

        # First migration applied, second not
        def find_one_side_effect(query):
            return {"name": query["name"]} if query["name"] == "migration_a" else None

        mock_col = MagicMock()
        mock_col.find_one.side_effect = find_one_side_effect
        mock_col.update_one.return_value = MagicMock()

        with patch("app.services.migrations.runner.migrations_collection", mock_col):
            from app.services.migrations.runner import run_once
            run_once("migration_a", make_fn("a"))
            run_once("migration_b", make_fn("b"))

        # Only "b" should have run
        assert call_order == ["b"]


# ---------------------------------------------------------------------------
# run_migrations (integration-level)
# ---------------------------------------------------------------------------

class TestRunMigrations:
    def test_run_migrations_calls_registered_migrations(self):
        """run_migrations should attempt to run the embedded wallets migration."""
        mock_col = _make_mock_collection(already_applied=False)

        with (
            patch("app.services.migrations.runner.migrations_collection", mock_col),
            patch(
                "app.services.wallet_service.migrate_all_users",
                return_value={"total_wallets_migrated": 0},
            ) as mock_migrate,
        ):
            from app.services.migrations.runner import run_migrations
            run_migrations()

        # The wallet migration function should have been invoked
        mock_migrate.assert_called_once()

    def test_run_migrations_skips_if_already_applied(self):
        """run_migrations is idempotent — won't re-run applied migrations."""
        mock_col = _make_mock_collection(already_applied=True)

        with (
            patch("app.services.migrations.runner.migrations_collection", mock_col),
            patch(
                "app.services.wallet_service.migrate_all_users",
                return_value={"total_wallets_migrated": 0},
            ) as mock_migrate,
        ):
            from app.services.migrations.runner import run_migrations
            run_migrations()

        mock_migrate.assert_not_called()
