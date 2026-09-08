from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.rwlock import RwLock


class TestSharing:
    def test_multiple_readers_share_the_lock(self):
        lock = RwLock()
        assert lock.acquire_read()
        assert lock.acquire_read()

    def test_a_writer_excludes_readers(self):
        lock = RwLock()
        lock.request_write()
        assert lock.acquire_write()
        assert not lock.acquire_read()


class TestWriterPriority:
    def test_a_waiting_writer_blocks_new_readers(self):
        lock = RwLock(writer_priority=True)
        lock.acquire_read()  # a reader holds it
        lock.request_write()  # writer now waiting
        # under writer priority, a new reader must yield and starves
        assert not lock.acquire_read()


class TestReaderPriority:
    def test_new_readers_get_in_while_a_writer_waits(self):
        lock = RwLock(writer_priority=False)
        lock.acquire_read()
        lock.request_write()  # writer waiting, but readers keep coming
        assert lock.acquire_read()
        # the writer cannot acquire while readers hold it, so it starves
        assert not lock.acquire_write()


class TestRefusals:
    def test_releasing_an_unheld_read_is_refused(self):
        with pytest.raises(Invalid):
            RwLock().release_read()

    def test_acquiring_an_unrequested_write_is_refused(self):
        with pytest.raises(Invalid):
            RwLock().acquire_write()
