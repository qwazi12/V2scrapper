import json
from pathlib import Path
import yaml
from openapi_spec_validator import validate
from scos.app import app

root = Path(__file__).resolve().parents[1]
reference = yaml.safe_load((root / "packages/contracts/blueprint.openapi.yaml").read_text())
validate(reference)
runtime = app.openapi()
validate(runtime)
(root / "packages/contracts/runtime.openapi.json").write_text(json.dumps(runtime, indent=2))
reference_paths = set(reference["paths"])
runtime_paths = set(runtime["paths"])
report = {
    "reference_valid": True,
    "runtime_valid": True,
    "implemented_matching_paths": sorted(reference_paths & runtime_paths),
    "not_yet_implemented_paths": sorted(reference_paths - runtime_paths),
    "local_extension_paths": sorted(runtime_paths - reference_paths),
    "full_blueprint_conformance": False,
    "note": "Matching paths do not imply exact response-schema conformance. Local commands are explicit version-0.1 extensions.",
}
(root / "docs/architecture/contract-coverage.json").write_text(json.dumps(report, indent=2))
print(
    f"Both OpenAPI schemas valid. {len(reference_paths & runtime_paths)}/{len(reference_paths)} blueprint paths present; exact full-contract conformance remains incomplete."
)
