# Coverage Reporting

Complete guide for measuring and reporting test coverage with pytest.

## Installation

```bash
pip install pytest-cov
```

## Basic Usage

### Terminal Report

```bash
# Show coverage in terminal
pytest --cov=app

# With verbose output
pytest -v --cov=app

# Multiple modules
pytest --cov=app --cov=tests
```

### HTML Report

```bash
# Generate HTML report
pytest --cov=app --cov-report=html

# Open report
# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# Windows
start htmlcov/index.html
```

### XML Report

```bash
# For CI/CD integration
pytest --cov=app --cov-report=xml
```

### JSON Report

```bash
# For programmatic access
pytest --cov=app --cov-report=json
```

### Multiple Reports

```bash
# Generate multiple report formats
pytest --cov=app --cov-report=html --cov-report=term --cov-report=xml
```

## Configuration

### pyproject.toml

```toml
[tool.coverage.run]
source = ["app"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
    "*/site-packages/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
precision = 2
fail_under = 80

[tool.coverage.html]
directory = "htmlcov"
```

### .coveragerc

```ini
[run]
source = app
omit =
    */tests/*
    */test_*.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
fail_under = 80

[html]
directory = htmlcov
```

### pytest.ini

```ini
[pytest]
addopts = --cov=app --cov-report=html --cov-report=term
```

## Coverage Options

### Branch Coverage

Measure both line and branch coverage:

```bash
pytest --cov=app --cov-branch
```

### Coverage for Specific Module

```bash
pytest --cov=app.module
```

### Combine Coverage from Multiple Runs

```bash
# Run tests and save coverage data
pytest --cov=app --cov-context=test

# Combine coverage files
coverage combine

# Generate report
coverage report
```

### Parallel Execution Coverage

With `pytest-xdist`:

```bash
pip install pytest-xdist

# Run tests in parallel
pytest -n auto --cov=app

# Combine coverage from workers
pytest -n auto --cov=app --cov-context=test
```

## Filtering Coverage

### Include Specific Files

```bash
pytest --cov=app.models --cov=app.views
```

### Exclude Files

```bash
pytest --cov=app --cov-ignore-globals='*/migrations/*'
```

### Omit Patterns

In `.coveragerc` or `pyproject.toml`:

```toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__init__.py",
    "*/conftest.py",
]
```

## Coverage Thresholds

### Fail Below Threshold

```bash
# Fail if coverage below 80%
pytest --cov=app --cov-fail-under=80
```

### Per-File Threshold

```bash
# Check each file meets threshold
pytest --cov=app --cov-fail-under=80 --cov-branch
```

### Configuration

In `pyproject.toml`:

```toml
[tool.coverage.report]
fail_under = 80
```

## Excluding Lines from Coverage

### Pragma Comments

```python
def complex_function():
    # pragma: no cover
    # This line is excluded from coverage
    pass

if some_condition:  # pragma: no cover
    pass
```

### Partial Exclusion

```python
def function_with_partial_exclusion():
    # Lines covered
    result = calculate()

    # This specific line excluded
    if some_rare_case:  # pragma: no cover
        handle_rare_case()

    return result
```

### Configuration Exclusion

In `pyproject.toml`:

```toml
[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
    "@abc.abstractmethod",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
```

## Coverage Reports

### Terminal Report Options

```bash
# Show missing lines
pytest --cov=app --cov-report=term-missing

# Show branch coverage
pytest --cov=app --cov-branch --cov-report=term-missing

# Skip covered files
pytest --cov=app --cov-report=term-missing:skip-covered
```

### HTML Report Customization

In `pyproject.toml`:

```toml
[tool.coverage.html]
directory = "htmlcov"
title = "Coverage Report"
```

### XML Report for CI/CD

```bash
# Generate XML for various tools
pytest --cov=app --cov-report=xml:cov.xml
```

### JSON Report

```bash
pytest --cov=app --cov-report=json:cov.json
```

## Coverage Data Files

### Combine Coverage Data

```bash
# Run tests with separate coverage files
pytest --cov=app --cov-context=test

# Combine coverage files
coverage combine

# Generate report
coverage report
```

### Parallel Coverage

```bash
# Run with pytest-xdist
pytest -n auto --cov=app --cov-context=test

# Combine automatically
coverage combine
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -e .
      - run: pip install pytest pytest-cov
      - run: pytest --cov=app --cov-report=xml --cov-report=term
      - uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### GitLab CI

```yaml
test:
  script:
    - pip install pytest pytest-cov
    - pytest --cov=app --cov-report=xml --cov-report=term
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

## Coverage Badges

### Generate Badge

```bash
pip install coverage-badge

# Generate badge from coverage data
coverage-badge -o docs/coverage.svg -f
```

### GitHub Actions Badge

```yaml
- name: Generate coverage badge
  run: |
    pip install coverage-badge
    coverage-badge -o coverage.svg
```

Add to README:

```markdown
![Coverage](coverage.svg)
```

## Interpreting Coverage

### Line Coverage

Percentage of executable lines that were executed:

```
Name                 Stmts   Miss  Cover
----------------------------------------
app/__init__            2      0   100%
app/main               20      5    75%
app/models             10      0   100%
----------------------------------------
TOTAL                  32      5    84%
```

### Branch Coverage

Percentage of conditional branches taken:

```bash
pytest --cov=app --cov-branch --cov-report=term-missing
```

### Missing Lines Report

```bash
pytest --cov=app --cov-report=term-missing
```

Output:

```
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
app/main               20      4    80%   23-24, 45-46
```

## Best Practices

1. **Aim for 80%+ coverage** - Reasonable balance of effort and value
2. **Focus on critical paths** - Higher coverage for core business logic
3. **Don't chase 100%** - Diminishing returns for last few percent
4. **Use branch coverage** - More meaningful than line coverage
5. **Review missing coverage** - Understand what tests don't cover
6. **Exclude appropriate lines** - Use `pragma: no cover` for untestable code
7. **Set thresholds** - Use `fail_under` to enforce minimum coverage
8. **Combine with code review** - Coverage is a metric, not a goal

## Common Issues

### Import Errors

If you get import errors:

```bash
# Set PYTHONPATH
export PYTHONPATH=${PYTHONPATH}:.
pytest --cov=app

# Or use pytest's pythonpath
pytest --pythonpath=. --cov=app
```

### Module Not Found

```bash
# Install package in development mode
pip install -e .

# Then run coverage
pytest --cov=app
```

### Multiprocessing Issues

For code using multiprocessing:

```bash
# Enable coverage for subprocesses
export COVERAGE_PROCESS_START=.coveragerc
pytest --cov=app --parallel-mode
```

## Coverage Tools Comparison

| Tool | Pros | Cons |
|------|------|------|
| **pytest-cov** | Easy pytest integration | Requires pytest |
| **coverage.py** | Standalone, powerful | More configuration needed |
| **py-cov** | Simple | Less features |

For most pytest projects, `pytest-cov` is the recommended choice.
