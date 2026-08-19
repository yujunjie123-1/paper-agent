from paper_agents.config import load_agent_specs, load_workflow


def test_all_workflow_agents_exist() -> None:
    specs = load_agent_specs()
    workflow = load_workflow()
    referenced: set[str] = set()
    for stage in workflow["stages"]:
        referenced.update(stage.get("agents", []))
        if stage.get("join"):
            referenced.add(stage["join"])
    referenced.update(workflow["external_review_flow"]["agents"])
    assert referenced <= specs.keys()
    assert len(specs) >= 25


def test_agent_boundaries_are_explicit() -> None:
    for spec in load_agent_specs().values():
        assert spec.objective
        assert spec.output_kind
        assert 1 <= spec.max_steps <= 32

