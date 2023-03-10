from model_bakery import baker

from grid.models import Grid
from package.models import Category, Package


def category():
    return baker.make(Category)


def grid():
    return baker.make(Grid)


def package():
    return baker.make(Package)
