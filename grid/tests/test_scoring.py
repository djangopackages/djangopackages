from grid.scoring import cutoff_from_scores


def test_bar_holds_when_anything_clears_it():
    assert cutoff_from_scores([0, 12, 50], 50) == 50
    assert cutoff_from_scores([80], 50) == 50


def test_everything_shows_when_nothing_clears_it():
    # The cutoff drops to the lowest score, so every package is listed.
    assert cutoff_from_scores([0, 12, 3], 50) == 0
    assert cutoff_from_scores([12], 50) == 12
    assert cutoff_from_scores([30, 12], 50) == 12


def test_an_empty_grid_keeps_the_bar():
    assert cutoff_from_scores([], 50) == 50
