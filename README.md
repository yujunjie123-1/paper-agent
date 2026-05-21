# AI Diagram Factory

`ai-diagram-factory` is a manifest-driven batch tool for making academic and AI-industry diagrams from text specs or Codex-interpreted reference images.

It coordinates these backends:

- `cli-anything-plotneuralnet` for 3D CNN / stacked feature-map sources.
- `cli-anything-drawio` for flowcharts, system architecture diagrams, and complex block topologies.
- Graphviz `.dot` for probabilistic graph models and node-link computation graphs.
- NN-SVG-style `.svg` for FCNN, LeNet-style CNN, and AlexNet-style neural-network schematics.
- TikZ-style `.tex` templates for LSTM / gated cell diagrams.
- A Python/Pillow fallback renderer so PNG previews are still produced when optional desktop exporters are unavailable.

## Quick Start

Use absolute paths on Windows:

```powershell
cd E:\多软件协作\ai-diagram-factory
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m pip install -e E:\多软件协作\ai-diagram-factory
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli catalog
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli init --preset deep-learning-gallery -o E:\多软件协作\ai-diagram-factory\examples\gallery.yaml
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli render E:\多软件协作\ai-diagram-factory\examples\gallery.yaml --out-dir E:\多软件协作\ai-diagram-factory\outputs
```

Each rendered figure gets:

- a PNG preview.
- its source file, such as `.drawio`, `.tex`, `.dot`, or PlotNeuralNet project `.json`.
- a small metadata JSON file describing the renderer path used.

## One-Command Replicate Workflow

`replicate` is the end-to-end entry point. Hand it a component plan that I (Claude) write after reading your image or text, and it does everything else: per-module backend rendering, tool plan logging, Draw.io master assembly, and deliverables packaging with PNG plus vector/source formats (`.drawio`, `.svg`, `.pdf`, `.vsdx`).

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli replicate `
  --plan      ABSOLUTE_PATH\component_plan.json `
  --reference ABSOLUTE_PATH\source_image.png ^
  --out-dir   ABSOLUTE_PATH\outputs\<run_name>
```

What lives where:

- `<out_dir>/replicate_manifest.yaml` - the workflow manifest generated from the plan.
- `<out_dir>/tool_plan.json` - which backend handles which module and why.
- `<out_dir>/<workflow_id>/stages/<module_id>/` - the raw per-module renderer output (PlotNeuralNet `.json`/`.tex`, NN-SVG `.svg`, Draw.io `.drawio`, Graphviz `.dot`, TikZ `.tex`, etc.).
- `<out_dir>/<workflow_id>/<master>.{drawio,svg,png}` - the Draw.io master assembly.
- `<out_dir>/<workflow_id>/<master>_trace.{drawio,svg,png}` - the master with the reference image locked as an underlay (only if `--reference` was passed).
- `<out_dir>/<workflow_id>/deliverables/` - PNG plus `.drawio`, `.svg`, `.pdf`, and `.vsdx` (PDF/VSDX require draw.io Desktop).
- `<out_dir>/replicate_summary.json` - human-readable status, vsdx export state, warnings.

Constraints:

- The component plan must contain 1 to 12 modules. The renderer rejects more than 12 to keep the master assembly legible.
- Each module declares its `backend` explicitly. The planner records the reason in `tool_plan.json`.
- Source formats `.drawio`, `.svg`, `.pdf`, `.vsdx` are always requested by `replicate`; PDF/VSDX fall back to an `unavailable` status if draw.io Desktop is missing, without aborting the run.

See [examples/component_plan_schema.md](examples/component_plan_schema.md) for the full schema and [examples/replication_prompt.md](examples/replication_prompt.md) for the checklist I follow when writing a plan from an image or text.

## Workflow With Codex

Give Codex a paragraph or a reference image and ask it to create a manifest. Codex chooses the backend:

- 3D CNN / VGG / AlexNet layer stacks use `plotneuralnet_cnn`.
- FCNN, LeNet-style CNN, and AlexNet-style neural-network schematics use `nn_svg_network` when a direct SVG schematic is enough.
- Complex flat architectures, training flows, and multi-branch systems use `drawio_architecture` or `drawio_flow`.
- LSTM, GRU, gated cells, and formula-heavy unit diagrams use `tikz_lstm`.
- Probabilistic graphical models, computation graphs, trees, and node-link networks use `graphviz_graph`.

Then render the manifest:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli render ABSOLUTE_MANIFEST_PATH --out-dir ABSOLUTE_OUTPUT_DIR
```

Use `catalog` to see supported diagram kinds and detected backends.

## PlotNeuralNet vs NN-SVG

They overlap on neural-network architecture drawings, but they should not be treated as the same tool:

- Use PlotNeuralNet when the target has perspective 3D feature-map blocks, CNN layer stacks, U-Net/VGG/AlexNet-style slabs, or LaTeX/TikZ source requirements.
- Use NN-SVG when the target is a clean FCNN, LeNet-style CNN, or AlexNet-style schematic and direct SVG output with native intra-network links is enough.
- Use Draw.io only after those assets exist, mainly to place them on the final page and add cross-module or missing arrows.

## Multi-Software Workflow

For figures that need more than one tool, use the staged workflow runner instead of drawing every element in one script. The workflow pattern is:

- Generate specialist atomic assets with PlotNeuralNet, TikZ, Graphviz, Netron exports, or user-provided transparent image assets.
- Generate FCNN, LeNet-style CNN, and AlexNet-style neural-network schematics with the NN-SVG renderer when SVG-native network links are sufficient.
- Send only true Draw.io-owned work to Draw.io: 2D layouts, flat architecture blocks, flowcharts, legends, final page layout, cross-module connectors, and missing-arrow fixes.
- Export code-generated atomic assets as transparent SVG whenever possible.
- Import those assets into a Draw.io master assembly.
- Preserve the internal lines produced by PlotNeuralNet, Graphviz, NN-SVG, TikZ, or SVG modules; do not redraw those lines in Draw.io.
- Use Draw.io for global layout, asset placement, cross-module connector routing, missing arrows, labels, legends, line jumps, and final export.
- Keep intermediate source files for traceability, but final deliverables contain only PNG plus the source formats explicitly requested by the user.
- When code-generated assets cannot match the reference closely enough, use image-to-image generation with no background, then import that transparent asset into Draw.io as an external placement.
- Use image-to-image only as a fallback for raster atomic components; it should not replace Draw.io for editable 2D topology or connector work.

### Plan Before Rendering

Before rendering a high-fidelity replica, create a tool assignment plan. This makes the workflow explicit before any asset is generated:

- 3D convolution blocks, perspective feature maps, and layer stacks are assigned to PlotNeuralNet or another 3D-capable generator; its native layer arrows stay inside the asset.
- FCNN, LeNet-style CNN, and AlexNet-style neural-network schematics are assigned to NN-SVG when the built-in SVG network links are sufficient.
- 2D topology, flat modules, legends, labels, cross-module connectors, missing-arrow fixes, line jumps, and final alignment are assigned to Draw.io.
- Math-heavy cells or local insets are assigned to TikZ.
- Node-link graphs, probability graphs, trees, and dependency skeletons are assigned to Graphviz; Graphviz-owned edges remain inside the generated asset.
- Image-to-image is assigned only as a fallback for transparent component assets that cannot be matched with vector/code generation.

Create a plan JSON from a workflow manifest:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow plan E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml -o E:\多软件协作\ai-diagram-factory\outputs\reference_workflow_tool_plan.json
```

`workflow render` also writes `tool_plan.json` inside each workflow output directory before rendering the stages. Review this file first when exact replication matters.

Create and render the reference workflow:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow init-reference -o E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow render E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml --out-dir E:\多软件协作\ai-diagram-factory\outputs\reference_workflow
```

Choose final source format explicitly. PNG is always included:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow render E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml --out-dir E:\多软件协作\ai-diagram-factory\outputs\reference_workflow --source-format drawio
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow render E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml --out-dir E:\多软件协作\ai-diagram-factory\outputs\reference_workflow --source-format pdf
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow render E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml --out-dir E:\多软件协作\ai-diagram-factory\outputs\reference_workflow --source-format vsdx
```

For high-fidelity replication, pass the original reference images. The renderer writes both a clean master and a `_trace` master with the original image embedded as a locked Draw.io underlay:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow init-reference --reference-1 ABSOLUTE_REFERENCE_1_PATH --reference-2 ABSOLUTE_REFERENCE_2_PATH -o E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow render E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml --out-dir E:\多软件协作\ai-diagram-factory\outputs\reference_workflow
```

The compatibility script now uses the same workflow:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe E:\多软件协作\ai-diagram-factory\examples\replicate_reference_figures.py
```

You can also pass absolute output paths explicitly:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe E:\多软件协作\ai-diagram-factory\examples\replicate_reference_figures.py --manifest E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml --out-dir E:\多软件协作\ai-diagram-factory\outputs\reference_workflow --compat-dir E:\多软件协作\ai-diagram-factory\outputs\reference_replicas
```

## Configuration

The package now derives its default project root from the installed source location. Override these paths when moving the project or using external tools in non-default locations:

```powershell
$env:AI_DIAGRAM_FACTORY_ROOT = "E:\多软件协作\ai-diagram-factory"
$env:AI_DIAGRAM_FACTORY_OUTPUT_DIR = "E:\多软件协作\ai-diagram-factory\outputs"
$env:PLOTNEURALNET_SOURCE_ROOT = "E:\多软件协作\PlotNeuralNet"
$env:AI_DIAGRAM_FACTORY_PLOTNEURALNET_HARNESS = "E:\多软件协作\PlotNeuralNet\agent-harness"
$env:AI_DIAGRAM_FACTORY_DRAWIO_HARNESS = "C:\Users\86180\Desktop\drawio\agent-harness"
$env:AI_DIAGRAM_FACTORY_LATEX_TEMP_DIR = "C:\Users\86180\Documents\ai_diagram_factory_latex_tmp"
```

## Development Checks

Install development tools and run the smoke tests:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m pip install -e "E:\多软件协作\ai-diagram-factory[dev]"
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m pytest E:\多软件协作\ai-diagram-factory\tests
```

## High-Density Reference Figures

For dense paper figures, do not ask an image model to recreate the whole picture in one pass. Use this sequence:

1. Generate a component plan from the image content; do not use a fixed region count.
2. Let the plan define however many semantic crops the image needs: layer stack, local inset, legend, connector cluster, dense node group, small label cluster, and so on.
3. Run OCR-first reading for each crop: list every word, number, symbol, colored box, arrow, dashed guide, and connector endpoint before drawing.
4. Convert each crop into a structured declaration, including exact text inventory and anchor-to-anchor line mapping.
5. Render local components with deterministic SVG, Draw.io tables, PlotNeuralNet, Graphviz, or TikZ.
6. Assemble in Draw.io only after local components are complete.
7. Run an omission pass before export: check missing text, missing colored boxes, shifted arrows, and connector endpoints that do not touch their target objects.

The LeNet-5 divide-and-conquer example uses an external component plan file. Replace that file for a different reference image; the script will crop however many components the new plan declares.

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe E:\多软件协作\ai-diagram-factory\examples\build_lenet_divide_conquer.py --reference-image ABSOLUTE_REFERENCE_IMAGE_PATH --component-plan E:\多软件协作\ai-diagram-factory\examples\lenet5_component_plan.json --out-dir E:\多软件协作\ai-diagram-factory\outputs\lenet5_divide_conquer
```

Visio export requires draw.io Desktop, because `.vsdx` is produced by the real diagrams.net exporter:

```powershell
cli-anything-drawio export check
cli-anything-drawio --project ABSOLUTE_DRAWIO_PATH export render ABSOLUTE_OUTPUT_PATH.pdf --format pdf --overwrite
cli-anything-drawio --project ABSOLUTE_DRAWIO_PATH export render ABSOLUTE_OUTPUT_PATH.vsdx --format vsdx --overwrite
```

If draw.io Desktop is missing, `workflow_report.json` records `pdf_export.status = unavailable` or `vsdx_export.status = unavailable`. If `pdf` or `vsdx` was requested as a source format, the deliverables report marks it as missing.
