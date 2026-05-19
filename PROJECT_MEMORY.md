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

## Tool Roles

- `plotneuralnet_cnn`: Use this for 3D CNN / VGG / AlexNet style layer stacks with perspective blocks, feature-map sizes, and channel-depth labels. Output includes PNG preview plus PlotNeuralNet source files.
- `drawio_architecture`: Use this for complex flat block diagrams, multi-branch neural networks, MMoE-like systems, recommender architectures, and dense module connection diagrams. Output includes PNG preview plus `.drawio` source.
- `drawio_flow`: Use this for algorithm flows, training pipelines, data processing chains, and decision workflows. Output includes PNG preview plus `.drawio` source.
- `tikz_lstm`: Use this for LSTM, GRU, gated cells, math-heavy unit structures, and paper-style vector diagrams. Output includes `.tex`, PDF when LaTeX is available, and PNG preview.
- `graphviz_graph`: Use this for probabilistic graphical models, computation graphs, tree structures, hierarchical node-link networks, and automatically laid-out dependency diagrams. Output includes `.dot` and PNG.

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

## Codex Workflow

1. The user provides a paragraph, paper figure description, or reference image.
2. Codex decides which backend or backend mix is appropriate.
3. Codex writes or edits a YAML/JSON manifest using absolute paths.
4. `ai-diagram-factory` renders the manifest.
5. The user receives PNG files plus editable source files for later refinement.

## Practical Guidance

- Use PlotNeuralNet when the target figure is mainly stacked 3D feature maps.
- Use draw.io when the figure is a complex system diagram with many rectangular modules and routed connectors.
- Use TikZ when mathematical notation, crisp vector output, or paper typography matters.
- Use Graphviz when there are many circular nodes and arrow relationships that should be auto-laid-out.
- For hybrid figures, generate multiple panels with different backends and combine them later in draw.io, PowerPoint, LaTeX, or another layout tool.

## Known Limitations

- The tool is not a one-click paper-figure reconstruction engine from screenshots. Codex still interprets the image or text and converts it into a structured manifest.
- draw.io Desktop export was not required for the current workflow; the renderer can still write `.drawio` source and PNG previews through its fallback path.
- Generated outputs under `E:\多软件协作\ai-diagram-factory\outputs` are local artifacts and are ignored by Git by default.

## Initial Version Scope

The `初始` version contains the working project scaffold, CLI entrypoint, renderer dispatcher, four backend families, a gallery example manifest, project documentation, and this memory file.
