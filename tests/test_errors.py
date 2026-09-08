from __future__ import annotations

import pytest

from rill.errors import Halted, Invalid, Late, Missing, RillError


class TestTheFamily:
    def test_every_refusal_is_a_rill_error(self):
        for kind in (Invalid, Missing, Late, Halted):
            assert issubclass(kind, RillError)

    def test_the_kinds_are_catchable_apart(self):
        with pytest.raises(Late):
            try:
                raise Late("behind the watermark")
            except Invalid:
                pytest.fail("Late is not Invalid")

    def test_messages_survive_the_raise(self):
        with pytest.raises(Halted) as caught:
            raise Halted("the stream closed at tick 40")
        assert "closed at tick 40" in str(caught.value)
