# Contributing to thenvoi-cli

Thank you for your interest in contributing to thenvoi-cli!

## Getting Started

### Development Setup

```bash
# Clone the repository
git clone https://github.com/bacedia/thenvoi-cli
cd thenvoi-cli

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Verify installation
thenvoi-cli --version
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=thenvoi_cli --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_config_manager.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Lint with ruff
ruff check src/ tests/

# Auto-fix linting issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/

# Type checking
mypy src/
```

## Making Changes

### Branching Strategy

1. Fork the repository
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   ```
3. Make your changes
4. Commit with clear messages (see below)
5. Push and open a Pull Request

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

Examples:
```
feat(config): add config export command
fix(run): handle graceful shutdown on SIGTERM
docs(readme): add troubleshooting section
test(config): add tests for UUID validation
```

### Pull Request Guidelines

1. **Title**: Clear, concise description of the change
2. **Description**: Explain what and why, not just how
3. **Tests**: Include tests for new functionality
4. **Documentation**: Update docs if needed
5. **CI**: All checks must pass

## Project Structure

```
thenvoi-cli/
├── src/thenvoi_cli/
│   ├── __init__.py           # Package version
│   ├── cli.py                # Main CLI entry point
│   ├── commands/             # Command implementations
│   │   ├── config.py
│   │   ├── run.py
│   │   ├── status.py
│   │   ├── rooms.py
│   │   ├── participants.py
│   │   ├── peers.py
│   │   ├── adapters.py
│   │   └── test.py
│   ├── config_manager.py     # Configuration handling
│   ├── adapter_registry.py   # Adapter management
│   ├── sdk_client.py         # SDK wrapper
│   ├── process_manager.py    # Background process management
│   ├── output.py             # Output formatting
│   ├── exceptions.py         # Custom exceptions
│   └── logging_config.py     # Logging setup
├── tests/
│   ├── conftest.py           # Shared fixtures
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── docs/                     # Documentation
├── .github/workflows/        # CI/CD
└── pyproject.toml            # Package configuration
```

## Adding New Features

### Adding a New Command

1. Create command module in `src/thenvoi_cli/commands/`
2. Implement using Typer
3. Register in `cli.py`
4. Add tests in `tests/unit/`
5. Update documentation

Example:
```python
# src/thenvoi_cli/commands/mycommand.py
import typer
from rich.console import Console

app = typer.Typer(help="My new command group.")
console = Console()

@app.command()
def subcommand(
    name: str = typer.Argument(..., help="Name argument."),
    flag: bool = typer.Option(False, "--flag", "-f", help="A flag."),
) -> None:
    """Do something useful."""
    console.print(f"Hello, {name}!")
```

### Adding a New Adapter

1. Add adapter info to `adapter_registry.py`
2. Add optional dependency in `pyproject.toml`
3. Test adapter creation in `commands/run.py`
4. Add documentation in `docs/adapters/`

## Code Style

- **Line length**: 100 characters
- **Quotes**: Double quotes for strings
- **Imports**: Sorted with isort (via ruff)
- **Type hints**: Required for all public functions
- **Docstrings**: Google style

Example:
```python
def my_function(
    name: str,
    count: int = 1,
    *,
    verbose: bool = False,
) -> list[str]:
    """Do something with the name.

    Args:
        name: The name to process.
        count: Number of times to repeat.
        verbose: Enable verbose output.

    Returns:
        List of processed strings.

    Raises:
        ValueError: If name is empty.
    """
    if not name:
        raise ValueError("Name cannot be empty")
    return [name] * count
```

## Questions?

- Open a discussion on GitHub
- Check existing issues for similar questions

Thank you for contributing!
