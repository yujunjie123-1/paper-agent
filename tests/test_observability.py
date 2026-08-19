from paper_agents.observability import TraceEvent, TraceRecorder


def test_trace_recorder_redacts_nested_secrets() -> None:
    recorder = TraceRecorder()
    event = recorder.record(
        TraceEvent(
            trace_id="a" * 32,
            run_id="run-1",
            event_name="browser.call",
            attributes={
                "authorization": "Bearer secret",
                "nested": {"cookie": "session", "domain": "example.org"},
            },
        )
    )

    assert event.attributes["authorization"] == "[REDACTED]"
    assert event.attributes["nested"]["cookie"] == "[REDACTED]"
    assert event.attributes["nested"]["domain"] == "example.org"
