# Project Memory: AI Diagram Factory

Version name: 初始

## Goal

Build a Codex-friendly diagram production pipeline that can turn user-provided text or reference images into editable diagram source files and PNG previews. The project is intended for academic papers, thesis figures, AI architecture diagrams, technical blogs, and presentation graphics.

## Completed Work

- Installed and configured the `cli-anything` Codex skill at `C:\Users\86180\.codex\skills\cli-anything\SKILL.md`.
- Cloned `HKUDS/CLI-Anything` into `E:\多软件协作\CLI-Anything`.
- Cloned PlotNeuralNet into `E:\多软件协作\PlotNeuralNet`.
- Built a CLI-Anything harness for PlotNeuralNet at `E:\多软件协作\PlotNeuralNet\agent-harness`.
- Verified the PlotNeuralNet CLI entrypoint `cli-anything-plotneuralnet`.
- Reused the existing draw.io CLI-Anything harness at `C:\Users\86180\Desktop\drawio\agent-harness`.
- Verified the draw.io CLI entrypoint `cli-anything-drawio`.
- Installed and verified Graphviz at `C:\Program Files\Graphviz\bin\dot.exe`.
- Installed and verified MiKTeX LaTeX at `C:\Users\86180\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe`.
- Created the multi-backend Python package at `E:\多软件协作\ai-diagram-factory`.
- Added an example manifest at `E:\多软件协作\ai-diagram-factory\examples\gallery.yaml`.
- Generated local sample outputs under `E:\多软件协作\ai-diagram-factory\outputs`.

## Default Entry Point

`replicate` is the default one-command entry point. The user gives Claude an image or a text description; Claude writes a `component_plan.json` (see `examples/component_plan_schema.md` and `examples/replication_prompt.md`) with at most 12 semantic modules and an explicit `backend` per module, then runs:

```powershell
python -m ai_diagram_factory.cli replicate --plan ABS_PLAN.json --reference ABS_IMAGE.png --out-dir ABS_OUT
```

Deliverables under `<out_dir>/<workflow_id>/deliverables/` always include PNG plus `.drawio`, `.svg`, and `.vsdx` (vsdx degrades gracefully when draw.io Desktop is missing). Module-by-module assets and `tool_plan.json` live alongside for audit and partial regeneration.

## Tool Roles

- `plotneuralnet_cnn`: Use this for 3D CNN / VGG / AlexNet style layer stacks with perspective blocks, feature-map sizes, and channel-depth labels. Output includes PNG preview plus PlotNeuralNet source files.
- `nn_svg_network`: Use this for FCNN, LeNet-style CNN, or AlexNet-style neural-network schematics when a direct publication-style SVG with native internal links is enough. Output includes SVG and PNG.
- `drawio_architecture`: Use this for complex flat block diagrams, multi-branch neural networks, MMoE-like systems, recommender architectures, and dense module connection diagrams. Output includes PNG preview plus `.drawio` source.
- `drawio_flow`: Use this for algorithm flows, training pipelines, data processing chains, and decision workflows. Output includes PNG preview plus `.drawio` source.
- `tikz_lstm`: Use this for LSTM, GRU, gated cells, math-heavy unit structures, and paper-style vector diagrams. Output includes `.tex`, PDF when LaTeX is available, and PNG preview.
- `graphviz_graph`: Use this for probabilistic graphical models, computation graphs, tree structures, hierarchical node-link networks, and automatically laid-out dependency diagrams. Output includes `.dot`, Graphviz-owned edges, and PNG/SVG when available.
- `workflow render`: Use this when one figure needs multiple tools. It renders staged assets first, then imports them into a Draw.io master assembly that controls global layout, cross-module or missing-arrow connectors, labels, legends, SVG, and PNG export.
- `vsdx` export: The workflow attempts Visio `.vsdx` export through `cli-anything-drawio`, but this requires draw.io Desktop to be installed. If unavailable, the report records the failure and still keeps `.drawio`, `.svg`, and `.png`.

## Daily Commands

Use Python 3.12 directly if the terminal has not refreshed PATH:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli catalog
```

Create the gallery manifest:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli init --preset deep-learning-gallery -o E:\多软件协作\ai-diagram-factory\examples\gallery.yaml
```

Render a manifest into PNG previews and editable sources:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli render E:\多软件协作\ai-diagram-factory\examples\gallery.yaml --out-dir E:\多软件协作\ai-diagram-factory\outputs
```

Generate a starter manifest from a written brief:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli brief --text "Create a VGG-style CNN and a multi-branch training architecture" --out E:\多软件协作\ai-diagram-factory\examples\brief.yaml
```

Create and render the multi-software reference workflow:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow init-reference -o E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow render E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml --out-dir E:\多软件协作\ai-diagram-factory\outputs\reference_workflow
```

For pixel-aligned replication, pass the original reference images and use the generated `_trace.drawio` files:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow init-reference --reference-1 ABSOLUTE_REFERENCE_1_PATH --reference-2 ABSOLUTE_REFERENCE_2_PATH -o E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow render E:\多软件协作\ai-diagram-factory\examples\reference_multisoftware_workflow.yaml --out-dir E:\多软件协作\ai-diagram-factory\outputs\reference_workflow
```

Check and manually export Visio format:

```powershell
cli-anything-drawio export check
cli-anything-drawio --project ABSOLUTE_DRAWIO_PATH export render ABSOLUTE_OUTPUT_PATH.vsdx --format vsdx --overwrite
```

## Codex Workflow

1. The user provides a paragraph, paper figure description, or reference image.
2. Codex first creates or reviews a tool assignment plan that decides which visual components go to PlotNeuralNet, NN-SVG, Draw.io, TikZ, Graphviz, or image-to-image fallback.
3. Codex writes a `component_plan.json` per `examples/component_plan_schema.md` (at most 12 semantic modules, each with an explicit `backend`). For a free-text input, leave `box_xyxy` off and rely on the grid placement.
4. Run `python -m ai_diagram_factory.cli replicate --plan ABS_PLAN.json [--reference ABS_IMAGE.png] --out-dir ABS_OUT`. The CLI writes `tool_plan.json` and the workflow manifest before rendering, then renders every module and assembles the Draw.io master.
5. The user receives PNG plus `.drawio`, `.svg`, and `.vsdx` source files in `<out_dir>/<workflow_id>/deliverables/`. Module-level intermediates remain under `stages/` for partial regeneration.

Planning command:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli workflow plan ABSOLUTE_WORKFLOW_MANIFEST_PATH -o ABSOLUTE_TOOL_PLAN_JSON_PATH
```

User-requested delivery rule:

1. Final output always includes PNG.
2. Source output includes only the format the user requests, such as `.drawio`, `.vsdx`, or `.svg`.
3. Internal intermediate files can still exist inside stage folders for traceability, but the `deliverables` folder should contain only the requested public deliverables.

Tool routing rule:

1. 2D architecture diagrams, flowcharts, flat modules, legends, labels, cross-module connector routing, and missing-arrow fixes should go directly into Draw.io.
2. 3D feature-map stacks and perspective convolution blocks should be generated as atomic SVG assets by PlotNeuralNet or another 3D-capable generator, then imported into Draw.io with their internal arrows preserved.
3. FCNN, LeNet-style CNN, and AlexNet-style neural-network schematics should use NN-SVG when its native SVG links cover the internal line work.
4. Math-heavy cells, graph structures, and auto-layout node networks should be generated by TikZ, Graphviz, or Netron when appropriate, then imported into Draw.io with their internal lines preserved.
5. Image-to-image generation is only a fallback for transparent raster components when code-generated/vector assets cannot visually match the requested component.

For complex paper figures, prefer staged workflows over one-shot drawing scripts:

1. Codex identifies which subparts should be made by PlotNeuralNet, NN-SVG, TikZ, Graphviz, image-to-image fallback, or Draw.io and records that decision in the workflow `planning` section or generated `tool_plan.json`.
2. 3D or code-friendly subparts should be produced as transparent SVG assets whenever possible.
3. If a code-generated component cannot visually match the reference or source file after reasonable tuning, use image-to-image generation with no background and import that transparent asset into Draw.io.
4. Draw.io owns final alignment, page-level connector routing, missing-arrow fixes, line jumps, labels, and overall composition. It should not redraw Graphviz, PlotNeuralNet, NN-SVG, TikZ, or SVG-module internal lines.
5. If an original image is provided, the workflow also emits `_trace.drawio`, `_trace.svg`, and `_trace.png` with the original image as a locked reference underlay.

## Practical Guidance

- Use PlotNeuralNet when the target figure is mainly stacked 3D feature maps.
- Use NN-SVG when the target figure is a clean FCNN, LeNet-style CNN, or AlexNet-style architecture schematic and its native SVG links are sufficient.
- Use draw.io when the figure is 2D, a complex system diagram, a flowchart, a flat architecture, or anything needing page-level placement, cross-module arrows, or missing-arrow cleanup.
- Use TikZ when mathematical notation, crisp vector output, or paper typography matters.
- Use Graphviz when there are many circular nodes and arrow relationships that should be auto-laid-out.
- For hybrid figures, generate multiple panels with different backends and combine them later in draw.io, PowerPoint, LaTeX, or another layout tool.
- Do not move renderer-native internal lines into Draw.io. Route only cross-module, missing, or page-level connectors in Draw.io.

## Known Limitations

- The tool is not a one-click paper-figure reconstruction engine from screenshots. Codex still interprets the image or text and converts it into a structured manifest.
- A 100% visual match requires the original reference image as an underlay or the original vector source. Without that file, the tool should not claim pixel-level replication.
- draw.io Desktop export was not required for the current workflow; the renderer can still write `.drawio` source and PNG previews through its fallback path.
- Generated outputs under `E:\多软件协作\ai-diagram-factory\outputs` are local artifacts and are ignored by Git by default.

## Initial Version Scope

The `初始` version contains the working project scaffold, CLI entrypoint, renderer dispatcher, four backend families, a gallery example manifest, project documentation, and this memory file.
