# AI Diagram Factory

`ai-diagram-factory` is a manifest-driven batch tool for making academic and AI-industry diagrams from text specs or Codex-interpreted reference images.

It coordinates these backends:

- `cli-anything-plotneuralnet` for 3D CNN / stacked feature-map sources.
- `cli-anything-drawio` for flowcharts, system architecture diagrams, and complex block topologies.
- Graphviz `.dot` for probabilistic graph models and node-link computation graphs.
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

## Workflow With Codex

Give Codex a paragraph or a reference image and ask it to create a manifest. Codex chooses the backend:

- 3D CNN / VGG / AlexNet layer stacks use `plotneuralnet_cnn`.
- Complex flat architectures, training flows, and multi-branch systems use `drawio_architecture` or `drawio_flow`.
- LSTM, GRU, gated cells, and formula-heavy unit diagrams use `tikz_lstm`.
- Probabilistic graphical models, computation graphs, trees, and node-link networks use `graphviz_graph`.

Then render the manifest:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli render ABSOLUTE_MANIFEST_PATH --out-dir ABSOLUTE_OUTPUT_DIR
```

Use `catalog` to see supported diagram kinds and detected backends.

## Multi-Software Workflow

For figures that need more than one tool, use the staged workflow runner instead of drawing every element in one script. The workflow pattern is:

- Generate specialist atomic assets with PlotNeuralNet, TikZ, Graphviz, Netron exports, or user-provided transparent image assets.
- Send 2D layouts, flat architecture blocks, flowcharts, dense connector maps, legends, and final routing directly to Draw.io.
- Export code-generated atomic assets as transparent SVG whenever possible.
- Import those assets into a Draw.io master assembly.
- Use Draw.io for global layout, routed connectors, arrow direction, labels, legends, line jumps, and final export.
- Keep intermediate source files for traceability, but final deliverables contain only PNG plus the source formats explicitly requested by the user.
- When code-generated assets cannot match the reference closely enough, use image-to-image generation with no background, then import that transparent asset into Draw.io as an external placement.
- Use image-to-image only as a fallback for raster atomic components; it should not replace Draw.io for editable 2D topology or connector work.

### Plan Before Rendering

Before rendering a high-fidelity replica, create a tool assignment plan. This makes the workflow explicit before any asset is generated:

- 3D convolution blocks, perspective feature maps, and layer stacks are assigned to PlotNeuralNet or another 3D-capable generator.
- 2D topology, flat modules, legends, labels, connectors, line jumps, and final alignment are assigned to Draw.io.
- Math-heavy cells or local insets are assigned to TikZ.
- Node-link graphs, probability graphs, trees, and dependency skeletons are assigned to Graphviz.
- Image-to-image is assigned only as a fallback for transparent component assets that cannot be matched with vector/code generation.

Create a plan JSON from a workflow manifest:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow plan E:\澶氳蒋浠跺崗浣淺ai-diagram-factory\examples\reference_multisoftware_workflow.yaml -o E:\澶氳蒋浠跺崗浣淺ai-diagram-factory\outputs\reference_workflow_tool_plan.json
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

Visio export requires draw.io Desktop, because `.vsdx` is produced by the real diagrams.net exporter:

```powershell
cli-anything-drawio export check
cli-anything-drawio --project ABSOLUTE_DRAWIO_PATH export render ABSOLUTE_OUTPUT_PATH.vsdx --format vsdx --overwrite
```

If draw.io Desktop is missing, `workflow_report.json` records `vsdx_export.status = unavailable`. If `vsdx` was requested as a source format, the deliverables report marks it as missing.
