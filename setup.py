from setuptools import find_packages, setup


setup(
    name="ai-diagram-factory",
    version="0.1.0",
    description="Batch factory for academic AI architecture diagrams using Draw.io, PlotNeuralNet, Graphviz, and TikZ-style templates.",
    packages=find_packages(),
    install_requires=["click>=8.0", "Pillow>=10.0", "PyYAML>=6.0", "CairoSVG>=2.7"],
    extras_require={
        "dev": ["pytest>=8.0", "ruff>=0.8"],
    },
    entry_points={
        "console_scripts": [
            "ai-diagram-factory=ai_diagram_factory.cli:cli",
        ]
    },
    python_requires=">=3.10",
)
