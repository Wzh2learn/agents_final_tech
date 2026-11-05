import hashlib

import pytest

from scripts.graph import research_tool_runtime as tools


def test_mount_rejects_changed_binary_before_execution(tmp_path):
    binary = tmp_path / 'rg'
    binary.write_bytes(b'not the pinned binary')
    with pytest.raises(ValueError, match='hash changed'):
        tools.ripgrep_binding(binary)


def test_mount_rejects_symlink(tmp_path):
    binary = tmp_path / 'rg'
    binary.write_bytes(b'example')
    link = tmp_path / 'rg-link'
    try:
        link.symlink_to(binary)
    except (OSError, NotImplementedError):
        pytest.skip('symlinks unavailable on this host')
    with pytest.raises(ValueError, match='regular absolute'):
        tools.ripgrep_binding(link)


def test_verified_binary_gets_readonly_binding(tmp_path, monkeypatch):
    binary = tmp_path / 'rg'
    binary.write_bytes(b'example')
    monkeypatch.setattr(tools, 'RG_SHA256', hashlib.sha256(b'example').hexdigest())
    assert tools.ripgrep_binding(binary) == [
        '--mount', f'type=bind,src={binary},dst=/usr/local/bin/rg,readonly']


def test_comma_mount_injection_is_rejected(tmp_path):
    binary = tmp_path / 'rg,readonly=false'
    binary.write_bytes(b'example')
    with pytest.raises(ValueError, match='unsafe Docker'):
        tools.ripgrep_binding(binary)
