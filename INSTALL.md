# Installation Guide - Even/Odd League

This guide covers installation for the Even/Odd League project, including dependencies for the research notebook (Mission M5.5).

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd LLM_Agent_Orchestration_HW7
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

You have several installation options:

#### Option A: Install from requirements.txt (Recommended)

```bash
pip install -r requirements.txt
```

This installs ALL dependencies including:
- Core framework (FastAPI, Pydantic, Uvicorn)
- HTTP clients (httpx, requests)
- Testing tools (pytest, pytest-cov)
- Code quality tools (black, flake8, mypy)
- **Data science packages (jupyter, numpy, pandas, matplotlib, seaborn, scipy)**

#### Option B: Install from pyproject.toml

```bash
pip install -e .
```

This installs the project in editable mode with all dependencies.

#### Option C: Install Only Research Dependencies

If you only need the research notebook dependencies:

```bash
pip install -e .[research]
```

This installs:
- jupyter
- numpy
- pandas
- matplotlib
- seaborn
- scipy
- ipykernel
- nbconvert

#### Option D: Install Dev Dependencies

For development work:

```bash
pip install -e .[dev]
```

## Verify Installation

### 1. Verify Core Installation

```bash
python -c "import fastapi, uvicorn, pydantic; print('✅ Core packages installed')"
```

### 2. Verify Research Packages

```bash
python -c "import jupyter, numpy, pandas, matplotlib, seaborn, scipy; print('✅ Research packages installed')"
```

### 3. Test Jupyter Notebook

```bash
# Start Jupyter
jupyter notebook

# Or directly open the experiments notebook
jupyter notebook doc/research_notes/experiments.ipynb
```

### 4. Execute Research Notebook

```bash
# Execute and generate HTML
jupyter nbconvert --to html --execute doc/research_notes/experiments.ipynb
```

Expected output:
- `doc/research_notes/experiments.html` (rendered notebook)
- 3 PNG plot files in the same directory

## Package Versions

The following major packages are installed:

### Core Framework
- fastapi >= 0.100.0
- uvicorn >= 0.20.0
- pydantic >= 2.0.0
- httpx >= 0.28.0

### Data Science (for M5.5 Research Notebook)
- jupyter >= 1.1.0
- numpy >= 2.0.0
- pandas >= 2.0.0
- matplotlib >= 3.8.0
- seaborn >= 0.13.0
- scipy >= 1.13.0
- ipykernel >= 7.0.0
- nbconvert >= 7.0.0

### Testing
- pytest >= 7.0.0
- pytest-cov >= 4.0.0
- pytest-asyncio >= 0.21.0
- pytest-timeout >= 2.1.0

### Code Quality
- black >= 23.0.0
- flake8 >= 6.0.0
- mypy >= 1.0.0
- pylint >= 2.17.0

## Troubleshooting

### Issue: pip install fails with "externally-managed-environment"

**Solution 1:** Use virtual environment (recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Solution 2:** Use --user flag (not recommended)
```bash
pip install --user -r requirements.txt
```

### Issue: Jupyter not found after installation

**Solution:** Ensure virtual environment is activated
```bash
source .venv/bin/activate  # Activate venv first
which jupyter  # Should point to .venv/bin/jupyter
```

### Issue: Module not found when running notebook

**Solution:** Install ipykernel and register the kernel
```bash
pip install ipykernel
python -m ipykernel install --user --name=even-odd-league
```

Then select the "even-odd-league" kernel in Jupyter.

### Issue: Plots not displaying in notebook

**Solution:** Install matplotlib backend
```bash
pip install ipympl
```

And add to notebook:
```python
%matplotlib inline
```

## Running the System

After installation:

### 1. Start League Manager
```bash
cd agents/league_manager
python main.py
```

### 2. Start Referees
```bash
# Terminal 2
cd agents/referee_REF01
python server.py

# Terminal 3
cd agents/referee_REF02
python server.py
```

### 3. Start Players
```bash
# Terminal 4-7
cd agents/player_P01 && python main.py
cd agents/player_P02 && python main.py
cd agents/player_P03 && python main.py
cd agents/player_P04 && python main.py
```

### 4. Run Research Notebook

```bash
jupyter notebook doc/research_notes/experiments.ipynb
```

## Updating Dependencies

### Update all packages
```bash
pip install --upgrade -r requirements.txt
```

### Update specific package
```bash
pip install --upgrade jupyter
```

### Generate current requirements
```bash
pip freeze > requirements-freeze.txt
```

## Uninstall

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf .venv

# Or just deactivate and delete the directory
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Jupyter Documentation](https://jupyter.org/documentation)
- [NumPy Documentation](https://numpy.org/doc/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Documentation](https://matplotlib.org/stable/contents.html)

## Support

For issues related to:
- **Core framework**: See `PRD_EvenOddLeague.md`
- **Research notebook**: See `doc/research_notes/README.md`
- **Testing**: See `tests/README.md`
- **Missions**: See `Missions_EvenOddLeague.md`
