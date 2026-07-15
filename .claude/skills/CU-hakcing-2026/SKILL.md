```markdown
# CU-hakcing-2026 Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill introduces you to the development patterns and workflows used in the CU-hakcing-2026 repository. The codebase is primarily written in Python (with some C and shell scripts), and focuses on modular, test-driven development for transmitter/receiver protocols, CLI utilities, and live dashboards. The repository follows conventional commit patterns, emphasizes clear documentation, and maintains a robust suite of regression and feature tests.

## Coding Conventions

- **File Naming:**  
  All Python and script files use `snake_case` (e.g., `live_receiver.py`, `test_wake_gate.py`).

- **Import Style:**  
  Relative imports are preferred within modules.
  ```python
  from .protocol import ProtocolHandler
  from ..TTS.classifier import Classifier
  ```

- **Export Style:**  
  Named exports are used; modules define explicit public interfaces.
  ```python
  # transmitter/transmitter.py
  def transmit(data): ...
  __all__ = ["transmit"]
  ```

- **Commit Messages:**  
  Conventional commit prefixes are used: `feat`, `fix`, `docs`, `test`.
  ```
  feat: add wake gate protocol to receiver
  fix: correct edge case in event logging
  docs: update protocol specification in README
  test: add regression for transmitter edge case
  ```

## Workflows

### Feature Implementation with Tests and Docs
**Trigger:** When adding a new major feature, protocol, or module  
**Command:** `/new-feature`

1. Implement or modify core logic in main source files (e.g., `transmitter/transmitter.py`, `receiver/decoder.py`).
2. Update or create documentation files (e.g., `README.md`, `ALGORITHM.md`).
3. Add or update test files to cover the new feature (e.g., `tests/test_transmitter.py`).

**Example:**
```bash
# Implement feature
vim transmitter/transmitter.py

# Update docs
vim README.md

# Add tests
vim tests/test_transmitter.py

# Commit
git add transmitter/transmitter.py README.md tests/test_transmitter.py
git commit -m "feat: implement new transmission protocol with docs and tests"
```

---

### Hardening and Bugfix with Regression Tests
**Trigger:** When fixing bugs, addressing review findings, or hardening workflows  
**Command:** `/harden`

1. Identify and fix bugs or edge cases in implementation files.
2. Update or add regression/unit tests to verify the fix.
3. Optionally update documentation to reflect changed behavior.

**Example:**
```python
# Fix in receiver/decoder.py
def decode(data):
    if not data:
        raise ValueError("No data received")
    # ...

# Add regression test in tests/test_receiver.py
def test_decode_empty():
    with pytest.raises(ValueError):
        decode("")
```

---

### Update or Add CLI Tool or Script
**Trigger:** When adding or updating a CLI entry point or utility script  
**Command:** `/new-cli`

1. Add or update a shell script or CLI Python file (e.g., `rocko.sh`, `decode_tilde_message.py`).
2. Update documentation to describe usage or deployment.
3. Add or update test files to cover script behavior.

**Example:**
```bash
# Add new script
vim receiver/decode_tilde_message.py

# Update usage docs
vim docs/plan/rocko-deploy.md

# Add test
vim tests/test_rocko_sh.py
```

---

### Protocol or Contract Freeze and Document
**Trigger:** When finalizing or changing a protocol, data contract, or flag table  
**Command:** `/freeze-contract`

1. Update implementation files to reflect the new/frozen protocol (e.g., `protocol.py`, `classifier.c`).
2. Update or create documentation/spec files (e.g., `docs/equipment-codes.md`).
3. Update `README` or `ALGORITHM.md` to match.

**Example:**
```python
# receiver/protocol.py
FRAME_FORMAT = {
    "header": 0xAA,
    "payload_length": 16,
    # ...
}
```

---

### Test Suite Expansion or Proof
**Trigger:** When expanding test coverage or guarding new behaviors  
**Command:** `/add-tests`

1. Create or update test files (e.g., `tests/test_transmitter.py`, `tests/test_wake_gate.py`).
2. Optionally update `Makefile` or add test runner scripts.
3. Document new test coverage in commit messages or docs.

**Example:**
```python
# tests/test_photo_classify.py
def test_photo_classification():
    assert classify("test.jpg") == "expected_label"
```

---

### Receiver Dashboard or Visualization Improvement
**Trigger:** When enhancing the receiver's UI/UX or adding visualization features  
**Command:** `/improve-dashboard`

1. Update receiver visualization or dashboard code (e.g., `live_receiver.py`, `plot_receiver.py`).
2. Update event logging or status logic as needed.
3. Update `README` or docs to reflect new UI/UX.

**Example:**
```python
# receiver/live_receiver.py
def show_dashboard():
    # Improved visualization logic
    pass
```

## Testing Patterns

- **Test File Naming:**  
  All test files are named with the pattern `test_*.py` (e.g., `test_receiver.py`).

- **Test Framework:**  
  The specific framework is not specified, but tests follow standard Python conventions (likely `pytest` or `unittest`).

- **Test Structure Example:**
  ```python
  # tests/test_transmitter.py
  def test_transmit_success():
      result = transmit("hello")
      assert result == "OK"
  ```

- **Shell/C Tests:**  
  Some shell scripts and C code are tested via corresponding test scripts or Makefile targets.

## Commands

| Command           | Purpose                                                      |
|-------------------|--------------------------------------------------------------|
| /new-feature      | Start a new feature with docs and tests                      |
| /harden           | Harden or bugfix a component and add regression tests        |
| /new-cli          | Add or update a CLI tool or script                           |
| /freeze-contract  | Freeze and document a protocol or contract                   |
| /add-tests        | Expand or add new test suites                                |
| /improve-dashboard| Enhance receiver dashboard or visualization                  |
```