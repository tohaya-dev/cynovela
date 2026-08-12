# Contributing

## Development Setup

```bash
conda activate cynovela
cd ~/Projects/cynovela/v11
bash start.sh
```

## Running Tests

```bash
python -m pytest tests/ -q
```

## Code Standards

- No company names or proprietary product names in code, UI, or comments
- str_replace one item at a time
- Run pytest after every Python file change
- All tests must pass before committing
