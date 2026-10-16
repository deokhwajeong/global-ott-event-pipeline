"""ADR-003: partner.<id>.* extensions are optional and can never block ingest."""

import pytest

from conftest import make_batch, make_event
from ott_ingest import partner as partner_module
from ott_ingest.partner import MAX_EXT_KEYS


def _ingest(eu, device, ext, app_id="streamco.player"):
    device_id, version = device
    return eu.ingest.handle_batch(
        make_batch(device_id, version, [make_event(app_id=app_id, ext=ext)])
    )


def test_adr003_declared_fields_are_kept(eu, device):
    ext = {"partner.streamco.cdn_pop": "fra", "partner.streamco.drm.level": "L1"}
    result = _ingest(eu, device, ext)
    assert result.accepted == 1
    assert eu.stream.events[0].ext == ext


@pytest.mark.parametrize(
    ("ext", "reason"),
    [
        ({"cdn_pop": "fra"}, "ext_bad_key"),
        ({"partner.Streamco.cdn_pop": "fra"}, "ext_bad_key"),
        ({"partner.othertv.tier": "gold"}, "ext_wrong_partner"),
        ({"partner.streamco.undeclared": 1}, "ext_undeclared"),
        ({"partner.streamco.startup_ms": "fast"}, "ext_bad_type"),
        ({"partner.streamco.startup_ms": True}, "ext_bad_type"),
        ({"partner.streamco.cdn_pop": {"nested": "obj"}}, "ext_bad_type"),
        (["not", "a", "dict"], "ext_not_object"),
    ],
)
def test_adr003_invalid_extension_is_stripped_and_event_still_stored(eu, device, ext, reason):
    result = _ingest(eu, device, ext)
    assert result.accepted == 1
    assert result.stripped_extensions == {reason: 1}
    assert eu.stream.events[0].ext == {}


def test_adr003_bad_fields_are_stripped_individually(eu, device):
    ext = {"partner.streamco.startup_ms": 850, "partner.streamco.nope": 1}
    _ingest(eu, device, ext)
    assert eu.stream.events[0].ext == {"partner.streamco.startup_ms": 850}


def test_adr003_over_budget_extension_is_stripped_whole(eu, device):
    ext = {f"partner.streamco.f{i}": i for i in range(MAX_EXT_KEYS + 1)}
    result = _ingest(eu, device, ext)
    assert result.accepted == 1
    assert result.stripped_extensions == {"ext_over_budget": 1}


def test_adr003_unexpected_failure_in_extension_code_never_blocks_ingest(eu, device, monkeypatch):
    def explode(*_args, **_kwargs):
        raise RuntimeError("bug in extension handling")

    monkeypatch.setattr(partner_module, "_sanitize", explode)

    result = _ingest(eu, device, {"partner.streamco.cdn_pop": "fra"})

    assert result.accepted == 1
    assert result.stripped_extensions == {"ext_error": 1}


def test_adr003_app_without_registered_partner_gets_core_events_only(eu, device):
    result = _ingest(eu, device, {"partner.streamco.cdn_pop": "fra"}, app_id="unregistered.app")
    assert result.accepted == 1
    assert result.stripped_extensions == {"ext_wrong_partner": 1}
