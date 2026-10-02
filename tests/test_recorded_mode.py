from __future__ import annotations

import uuid

import pytest

from arp import m1


@pytest.mark.parametrize("extra", [[], ["--image", "sha256:fixture"]])
def test_recorded_mode_requires_complete_source_configuration(monkeypatch, capsys, extra):
    calls = []
    monkeypatch.setattr(m1.subprocess, "run", lambda *a, **kw: calls.append((a, kw)))
    output = str(m1.ROOT / "artifacts/private" / ("test-uncreated-" + uuid.uuid4().hex))
    monkeypatch.setattr("sys.argv", ["arp.m1", "--output", output, "--recorded-only", *extra])
    with pytest.raises(SystemExit) as error:
        m1.main()
    assert error.value.code == 2
    assert "requires --reuse-evidence" in capsys.readouterr().err
    assert calls == []
