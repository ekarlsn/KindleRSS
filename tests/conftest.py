"""pytest configuration and shared fixtures for KindleRSS tests."""

from pathlib import Path

import pytest

SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"


def pytest_addoption(parser):
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Overwrite existing HTML snapshot files with current output.",
    )


@pytest.fixture
def html_snapshot(request):
    """File-based HTML snapshot fixture.

    Writes one plain .html file per call, named after the test by default.
    Files land in tests/snapshots/ and can be opened directly in a browser.

    Usage::

        def test_something(html_snapshot):
            result = my_function()
            html_snapshot(result)               # uses test name as filename
            html_snapshot(result, "custom_name")  # explicit filename (no .html)

    Workflow:
        # First run / regenerate:
        uv run pytest tests/ --update-snapshots

        # Normal CI verification:
        uv run pytest tests/
    """
    update = request.config.getoption("--update-snapshots")

    def assert_matches_snapshot(html: str, name: str | None = None) -> None:
        if name is None:
            name = request.node.name
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        snapshot_path = SNAPSHOTS_DIR / f"{name}.html"

        if update or not snapshot_path.exists():
            snapshot_path.write_text(html, encoding="utf-8")
            if update:
                pytest.fail(
                    f"Snapshot updated: {snapshot_path.relative_to(Path(__file__).parent)}",
                    pytrace=False,
                )
            else:
                # First-time creation: write and pass so the test acts as a baseline run.
                return

        expected = snapshot_path.read_text(encoding="utf-8")
        assert html == expected, (
            f"\nSnapshot mismatch: {snapshot_path}\n"
            "Run  uv run pytest tests/ --update-snapshots  to accept new output."
        )

    return assert_matches_snapshot
