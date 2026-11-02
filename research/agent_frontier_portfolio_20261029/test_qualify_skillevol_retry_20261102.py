import pytest

from qualify_skillevol_retry_20261102 import embedded_verifier


def test_extracts_the_embedded_program_without_running_the_install_wrapper():
    shell = "pip install ignored\n\"$PYTHON_BIN\" - <<'PY'\nprint('ok')\nPY\nexit 0\n"
    assert embedded_verifier(shell) == "print('ok')\n"


def test_rejects_changed_or_ambiguous_wrapper():
    with pytest.raises(ValueError):
        embedded_verifier("python -c 'pass'\n")
    with pytest.raises(ValueError):
        embedded_verifier("\"$PYTHON_BIN\" - <<'PY'\npass\nPY\nexit 1\n")
