def test_grid(grid):
    assert str(grid) == f"{grid.title}"


def test_grid_package(grid_package):
    assert (
        str(grid_package) == f"{grid_package.grid.slug} : {grid_package.package.slug}"
    )


def test_feature(feature):
    assert str(feature) == f"{feature.grid.slug} : {feature.title}"


def test_element(element):
    assert (
        str(element)
        == f"{element.grid_package.grid.slug} : {element.grid_package.package.slug} : {element.feature.title}"
    )
