from __future__ import annotations

import shutil
import sys
from argparse import ArgumentParser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_diagram_factory.io import write_manifest
from ai_diagram_factory.templates import reference_workflow_manifest
from ai_diagram_factory.workflow import render_workflow_manifest


DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "examples" / "reference_multisoftware_workflow.yaml"
DEFAULT_WORKFLOW_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "reference_workflow"
DEFAULT_COMPAT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "reference_replicas"


COMPAT_EXPORTS = {
    "reference_1_unet_3d_multisoftware": {
        "master": "reference_1_unet_3d_master",
        "compat": "reference_1_unet_3d_replica",
    },
    "reference_2_cswf_attention_unet_multisoftware": {
        "master": "reference_2_cswf_attention_unet_master",
        "compat": "reference_2_cswf_attention_unet_replica",
    },
}


def copy_master_outputs(workflow_output_dir: Path, compat_output_dir: Path) -> None:
    compat_output_dir.mkdir(parents=True, exist_ok=True)
    for workflow_id, names in COMPAT_EXPORTS.items():
        workflow_dir = workflow_output_dir / workflow_id
        for suffix in [".png", ".svg", ".drawio"]:
            source = workflow_dir / f"{names['master']}{suffix}"
            if source.exists():
                shutil.copy2(source, compat_output_dir / f"{names['compat']}{suffix}")


def parse_args():
    parser = ArgumentParser(description="Run the multi-software reference figure replication workflow.")
    parser.add_argument("--reference-1", default="", help="Absolute path to the original first reference image.")
    parser.add_argument("--reference-2", default="", help="Absolute path to the original second reference image.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH), help="Absolute path for the generated workflow manifest.")
    parser.add_argument("--out-dir", default=str(DEFAULT_WORKFLOW_OUTPUT_DIR), help="Absolute output directory for workflow artifacts.")
    parser.add_argument("--compat-dir", default=str(DEFAULT_COMPAT_OUTPUT_DIR), help="Absolute directory for legacy replica copies.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reference_1 = str(Path(args.reference_1).expanduser().resolve()) if args.reference_1 else None
    reference_2 = str(Path(args.reference_2).expanduser().resolve()) if args.reference_2 else None
    manifest_path = Path(args.manifest).expanduser().resolve()
    workflow_output_dir = Path(args.out_dir).expanduser().resolve()
    compat_output_dir = Path(args.compat_dir).expanduser().resolve()
    write_manifest(manifest_path, reference_workflow_manifest(reference_1, reference_2))
    index = render_workflow_manifest(manifest_path, workflow_output_dir)
    copy_master_outputs(workflow_output_dir, compat_output_dir)
    print(f"workflow_manifest={manifest_path}")
    print(f"workflow_index={workflow_output_dir / 'workflow_index.json'}")
    print(f"compat_output_dir={compat_output_dir}")
    for result in index["results"]:
        assembly = result["assembly"]
        print(f"{result['id']}:")
        print(f"  png={assembly['png']}")
        print(f"  svg={assembly['svg']}")
        print(f"  drawio={assembly['drawio']}")
        print(f"  report={result['report']}")


if __name__ == "__main__":
    main()
