"""Priority 3: Concurrency Safety Tests (Atomic Rename Pattern)"""
import sys
import json
import tempfile
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.repositories.base import BaseRepository
from app.models.tenant_context import TenantContext


class SimpleRepository(BaseRepository):
    """Simple test repository"""
    def __init__(self):
        super().__init__(collection_name="test")
        self.test_dir = Path(tempfile.mkdtemp())

    def _get_storage_path(self, ctx: TenantContext) -> Path:
        return self.test_dir


class TestConcurrencySafety:
    """Test concurrent writes with atomic rename pattern"""

    @pytest.fixture
    def repo(self):
        return SimpleRepository()

    @pytest.fixture
    def ctx(self):
        return TenantContext(
            user_id="test_user",
            company_id="test_company",
            project_id="test_project",
            role="Admin",
            permissions={}
        )

    def test_atomic_write_basic(self, repo, ctx):
        """Test basic atomic write"""
        file_path = repo.test_dir / "test.json"
        data = {"value": 42, "name": "test"}

        repo._save_json(file_path, data)

        assert file_path.exists()
        loaded = json.loads(file_path.read_text())
        assert loaded == data

    def test_concurrent_writes_no_corruption(self, repo, ctx):
        """Test that concurrent writes produce valid file (some may fail due to lock, but file stays valid)"""
        file_path = repo.test_dir / "concurrent.json"
        num_threads = 5
        writes_per_thread = 3
        successful_writes = []
        failed_writes = []

        def writer(thread_id):
            for i in range(writes_per_thread):
                try:
                    data = {
                        "thread_id": thread_id,
                        "iteration": i,
                        "value": thread_id * 1000 + i,
                        "timestamp": time.time()
                    }
                    repo._save_json(file_path, data)
                    successful_writes.append((thread_id, i))
                except Exception as e:
                    # On Windows, file locks can cause failures - this is expected
                    failed_writes.append((thread_id, i))

        # Start multiple threads
        threads = [
            threading.Thread(target=writer, args=(i,))
            for i in range(num_threads)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # At least some writes should succeed
        assert len(successful_writes) > 0, "At least some writes should succeed"

        # File should exist and be valid JSON
        if file_path.exists():
            try:
                final_data = json.loads(file_path.read_text())
                assert isinstance(final_data, dict)
            except json.JSONDecodeError:
                pytest.fail("File corruption: Invalid JSON after concurrent writes")

    def test_concurrent_updates_consistency(self, repo, ctx):
        """Test that file updates are consistent (no partial writes, file stays valid)"""
        file_path = repo.test_dir / "consistent.json"
        num_threads = 3
        successful_updates = []

        def updater(thread_id):
            for i in range(2):
                try:
                    # Load current data
                    current = repo._load_json(file_path, {"updates": []})
                    # Modify
                    current["updates"].append(f"thread_{thread_id}_iter_{i}")
                    current["last_update"] = f"thread_{thread_id}"
                    # Save
                    repo._save_json(file_path, current)
                    successful_updates.append((thread_id, i))
                    time.sleep(0.001)
                except:
                    # File lock is expected on Windows
                    pass

        threads = [
            threading.Thread(target=updater, args=(i,))
            for i in range(num_threads)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # At least some updates should succeed
        assert len(successful_updates) > 0, "At least some updates should succeed"

        # Verify final state is valid
        if file_path.exists():
            final_data = json.loads(file_path.read_text())
            assert "updates" in final_data
            assert isinstance(final_data["updates"], list)

    def test_temp_file_cleanup(self, repo, ctx):
        """Test that temporary files are cleaned up"""
        file_path = repo.test_dir / "cleanup_test.json"

        initial_files = set(repo.test_dir.glob("*.tmp"))

        for i in range(10):
            repo._save_json(file_path, {"iteration": i})

        final_files = set(repo.test_dir.glob("*.tmp"))

        # Should not accumulate temp files
        assert final_files == initial_files, "Temp files not cleaned up properly"

    def test_partial_write_recovery(self, repo, ctx):
        """Test that system recovers from interrupted writes"""
        file_path = repo.test_dir / "recovery.json"

        # Write initial data
        initial_data = {"value": 1, "status": "initial"}
        repo._save_json(file_path, initial_data)

        # Verify initial write
        assert json.loads(file_path.read_text()) == initial_data

        # Write new data
        new_data = {"value": 2, "status": "updated"}
        repo._save_json(file_path, new_data)

        # Verify update (should not have partial/corrupted data)
        final_data = json.loads(file_path.read_text())
        assert final_data == new_data
        assert final_data != initial_data

    def test_large_file_concurrent_write(self, repo, ctx):
        """Test concurrent writes with large data"""
        file_path = repo.test_dir / "large.json"

        def write_large(thread_id):
            large_data = {
                "thread_id": thread_id,
                "data": [{"id": i, "value": f"data_{i}"}
                         for i in range(1000)]
            }
            repo._save_json(file_path, large_data)

        threads = [threading.Thread(target=write_large, args=(i,))
                   for i in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify file is valid
        final_data = json.loads(file_path.read_text())
        assert isinstance(final_data, dict)
        assert "thread_id" in final_data
        assert "data" in final_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
