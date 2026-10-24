from grid.scoring import FALLBACK_SCORE_MIN, cutoff_from_scores


def test_bar_holds_when_anything_clears_it():
    assert cutoff_from_scores([0, 12, 50], 50) == 50
    assert cutoff_from_scores([80], 50) == 50


def test_falls_back_to_above_zero_when_nothing_clears_it():
    assert cutoff_from_scores([0, 12, 3], 50) == FALLBACK_SCORE_MIN


def test_single_package_and_empty_grids_get_no_fallback():
    assert cutoff_from_scores([12], 50) == 50
    assert cutoff_from_scores([], 50) == 50
