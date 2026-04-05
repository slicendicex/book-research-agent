# AI Boundary & Config Foundation

## Goal

Create the first reusable `core/` layer for runtime configuration and provider boundaries without any network access.

## Definition of done

- Runtime settings load from environment variables
- Embedding and generation provider boundaries exist
- Dummy providers work locally
- Unsupported real provider names fail clearly
- `doctor` prints a safe configuration summary

## Files changed

- `.env.example`
- `docs/project-map.md`
- `src/book_research_agent/cli.py`
- `src/book_research_agent/config.py`
- `src/book_research_agent/core/config/settings.py`
- `src/book_research_agent/core/providers/base.py`
- `src/book_research_agent/core/providers/dummy.py`
- `src/book_research_agent/core/providers/factory.py`

## Minimal verification

- `PYTHONPATH=src .venv/bin/python -m book_research_agent.cli`
- `PYTHONPATH=src .venv/bin/python -m book_research_agent.cli doctor`

## Notes

This layer intentionally avoids real SDK clients and external calls.
