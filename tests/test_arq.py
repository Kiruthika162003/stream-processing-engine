from __future__ import annotations

import pytest

from rill.arq import go_back_n, selective_repeat
from rill.errors import Invalid


class TestRetransmission:
    def test_go_back_n_resends_the_whole_tail(self):
        # window of 10, loss at index 2: resend indices 2..9, ten minus two
        assert go_back_n(10, 2) == 8

    def test_selective_repeat_resends_only_the_loss(self):
        assert selective_repeat(10, 2) == 1

    def test_a_late_loss_costs_go_back_n_almost_nothing_extra(self):
        assert go_back_n(10, 9) == 1  # loss at the tail resends just one

    def test_an_early_loss_costs_go_back_n_the_most(self):
        assert go_back_n(10, 0) == 10  # loss at the head resends everything
        assert selective_repeat(10, 0) == 1


class TestRefusals:
    def test_a_nonpositive_window_is_refused(self):
        with pytest.raises(Invalid):
            go_back_n(0, 0)

    def test_a_loss_index_outside_the_window_is_refused(self):
        with pytest.raises(Invalid):
            selective_repeat(5, 9)
