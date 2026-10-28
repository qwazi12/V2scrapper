from scos.config import ROOT


def test_root_points_to_independent_project():
    assert (ROOT / "pyproject.toml").is_file()
    assert (ROOT / "docs/blueprint/03_DATABASE_SCHEMA.sql").is_file()
