from scos.config import ROOT


def test_root_points_to_independent_project():
    assert ROOT.name == "screen-central-os"
    assert (ROOT / "docs/blueprint/03_DATABASE_SCHEMA.sql").is_file()
