from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.outlier import mad_outliers, zscore_outliers

BULK = [10, 11, 9, 10, 12, 8, 11, 10, 9, 10]


class TestMasking:
    def test_a_cluster_of_outliers_masks_itself_from_the_sigma_test(self):
        data = [*BULK, 1000, 1000, 1000]
        assert zscore_outliers(data) == []

    def test_the_mad_test_catches_what_sigma_masks(self):
        data = [*BULK, 1000, 1000, 1000]
        assert mad_outliers(data) == [1000, 1000, 1000]


class TestAgreement:
    def test_clean_data_flags_nothing_either_way(self):
        assert zscore_outliers(BULK) == []
        assert mad_outliers(BULK) == []

    def test_a_lone_outlier_is_caught_by_both(self):
        data = [*BULK, 500]
        assert 500 in zscore_outliers(data)
        assert 500 in mad_outliers(data)


class TestRefusals:
    def test_too_few_values_is_refused(self):
        with pytest.raises(Invalid):
            zscore_outliers([1])

    def test_mad_of_too_few_is_refused(self):
        with pytest.raises(Invalid):
            mad_outliers([1])
