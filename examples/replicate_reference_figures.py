from __future__ import annotations

import shutil
import sys
from argparse import ArgumentParser
from pathlib import Path

PROJECT_ROOT = Path("E:/多软件协作/ai-diagram-factory")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_diagram_factory.io import write_manifest
from ai_diagram_factory.templates import reference_workflow_manifest
from ai_diagram_factory.workflow import render_workflow_manifest


MANIFEST_PATH = PROJECT_ROOT / "examples" / "reference_multisoftware_workflow.yaml"
WORKFLOW_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "reference_workflow"
COMPAT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "reference_replicas"


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


def copy_master_outputs() -> None:
    COMPAT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for workflow_id, names in COMPAT_EXPORTS.items():
        workflow_dir = WORKFLOW_OUTPUT_DIR / workflow_id
        for suffix in [".png", ".svg", ".drawio"]:
            source = workflow_dir / f"{names['master']}{suffix}"
            if source.exists():
                shutil.copy2(source, COMPAT_OUTPUT_DIR / f"{names['compat']}{suffix}")


def parse_args():
    parser = ArgumentParser(description="Run the multi-software reference figure replication workflow.")
    parser.add_argument("--reference-1", default="", help="Absolute path to the original first reference image.")
    parser.add_argument("--reference-2", default="", help="Absolute path to the original second reference image.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reference_1 = str(Path(args.reference_1).expanduser().resolve()) if args.reference_1 else None
    reference_2 = str(Path(args.reference_2).expanduser().resolve()) if args.reference_2 else None
    write_manifest(MANIFEST_PATH, reference_workflow_manifest(reference_1, reference_2))
    index = render_workflow_manifest(MANIFEST_PATH, WORKFLOW_OUTPUT_DIR)
    copy_master_outputs()
    print(f"workflow_manifest={MANIFEST_PATH}")
    print(f"workflow_index={WORKFLOW_OUTPUT_DIR / 'workflow_index.json'}")
    print(f"compat_output_dir={COMPAT_OUTPUT_DIR}")
    for result in index["results"]:
        assembly = result["assembly"]
        print(f"{result['id']}:")
        print(f"  png={assembly['png']}")
        print(f"  svg={assembly['svg']}")
        print(f"  drawio={assembly['drawio']}")
        print(f"  report={result['report']}")


if __name__ == "__main__":
    main()
