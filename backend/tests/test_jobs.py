"""Tests for job tasks — unit-level tests using mocked dependencies."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from schemas.objects import CompanyObject


class TestSyncTaskStructure:
    """Verify task signatures and basic behavior without hitting real services."""

    def test_seed_companies_not_empty(self):
        from schemas.seed import COMPANIES
        assert len(COMPANIES) == 50

    def test_seed_companies_have_required_fields(self):
        from schemas.seed import COMPANIES
        for c in COMPANIES:
            assert "name" in c
            assert "wiki" in c
            assert "github" in c

    def test_worker_settings_has_all_functions(self):
        from jobs.worker import WorkerSettings
        func_names = [f.__name__ for f in WorkerSettings.functions]
        assert "sync_wikipedia" in func_names
        assert "sync_github" in func_names
        assert "sync_yahoo_finance" in func_names
        assert "sync_hn" in func_names
        assert "sync_sec" in func_names
        assert "sync_patents" in func_names
        assert "sync_forbes" in func_names
        assert "compute_derived" in func_names
        assert "resolve_entities" in func_names

    def test_worker_settings_has_cron_jobs(self):
        from jobs.worker import WorkerSettings
        assert len(WorkerSettings.cron_jobs) >= 6

    def test_worker_settings_has_lifecycle(self):
        from jobs.worker import WorkerSettings
        assert WorkerSettings.on_startup is not None
        assert WorkerSettings.on_shutdown is not None
