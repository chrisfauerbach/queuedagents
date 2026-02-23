"""Tests for backend.app.model_catalog — CATALOG structure and content."""

from backend.app.model_catalog import CATALOG, CatalogModel, CatalogVariant


def test_catalog_is_nonempty():
    assert len(CATALOG) > 0


def test_catalog_has_expected_categories():
    categories = {m.category for m in CATALOG}
    assert "General Purpose" in categories
    assert "Code" in categories
    assert "Reasoning" in categories


def test_every_model_has_variants():
    for model in CATALOG:
        assert len(model.variants) >= 1, f"{model.name} has no variants"


def test_variant_structure():
    for model in CATALOG:
        for v in model.variants:
            assert isinstance(v, CatalogVariant)
            assert v.tag  # non-empty
            assert v.parameter_size  # non-empty


def test_model_names_unique():
    names = [m.name for m in CATALOG]
    assert len(names) == len(set(names)), "Duplicate model names in catalog"
