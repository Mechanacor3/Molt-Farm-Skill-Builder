# Pytest Practical Checklist

Use these patterns when the user wants a direct pytest answer.

## TDD Order

- Red: write the failing test first.
- Green: implement the smallest change that passes it.
- Refactor: clean up only after the test is green.

## Parametrization

- Prefer `@pytest.mark.parametrize` for repeated input and expected pairs.
- Keep the case table in one test unless cases truly need different setup.

```python
@pytest.mark.parametrize("value,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
])
def test_uppercase(value, expected):
    assert value.upper() == expected
```

## Fixtures And `conftest.py`

- Use fixtures for shared setup.
- Put fixtures shared across multiple test modules in `conftest.py`.
- Choose the smallest useful scope: `function`, `module`, or `session`.

## Side Effects

- Use `monkeypatch` for environment variables and attribute overrides.
- Use `tmp_path` for file-backed tests.
- Keep side-effect tests local and isolated from real repo state.

```python
def test_writer(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_MODE", "test")
    target = tmp_path / "out.json"
    write_output(target)
    assert target.exists()
```

## Async Pytest

- Recommend `pytest-asyncio` when async test support is needed.
- Mark async tests with `@pytest.mark.asyncio`.
- Await the async function or fixture-backed client call directly.

```python
@pytest.mark.asyncio
async def test_fetch(async_client):
    response = await async_client.get("/items")
    assert response.status_code == 200
```

## Coverage

- Measure with `pytest-cov` or `pytest --cov`.
- Use coverage to find gaps in meaningful paths.
- Prefer targeted helper and boundary tests over broad setup added only for percentage gains.
