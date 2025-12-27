# Quick Start - Research Notebook (M5.5)

This guide helps you quickly set up and run the research notebook for Mission M5.5.

## For Your Professor (First Time Setup)

### Step 1: Clone and Install

```bash
# Clone repository
git clone <repository-url>
cd LLM_Agent_Orchestration_HW7

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### Step 2: Verify Installation

```bash
# Run verification script
python verify_installation.py
```

Expected output: All research packages marked with ✅

### Step 3: View the Notebook

**Option A: View Pre-rendered HTML (No Jupyter needed)**
```bash
open doc/research_notes/experiments.html
```

**Option B: Run Interactive Notebook**
```bash
jupyter notebook doc/research_notes/experiments.ipynb
```

## For Quick Testing

If you just want to verify the notebook works:

```bash
# Execute notebook and generate fresh HTML
.venv/bin/jupyter nbconvert --to html --execute doc/research_notes/experiments.ipynb

# View the output
open doc/research_notes/experiments.html
```

## Troubleshooting

### Problem: `pip: command not found`

**Solution:**
```bash
python3 -m pip install -r requirements.txt
```

### Problem: `jupyter: command not found`

**Solution:** Ensure virtual environment is activated
```bash
source .venv/bin/activate  # Activate first
which jupyter  # Should show .venv/bin/jupyter
```

### Problem: Packages not found when running notebook

**Solution:** Install packages in virtual environment
```bash
# Activate venv
source .venv/bin/activate

# Install research dependencies
pip install jupyter numpy pandas matplotlib seaborn scipy ipykernel nbconvert

# Or install from requirements.txt
pip install -r requirements.txt
```

### Problem: Notebook kernel error

**Solution:** Register the kernel
```bash
source .venv/bin/activate
python -m ipykernel install --user --name=even-odd-league --display-name="Even/Odd League"
```

Then in Jupyter: Kernel → Change Kernel → "Even/Odd League"

## What's Included in the Notebook

- **10 Cells** (requirement: ≥8)
- **3 LaTeX Formulas** (requirement: ≥2)
  - Win Rate Calculation
  - Expected Value Formula
  - Wilson Confidence Interval
- **7 Plots** (requirement: ≥4)
  - Strategy Win Rate Comparison
  - Expected Points by Strategy
  - Match Completion Rate vs Timeout
  - Move Latency Distribution
  - Retry Configuration Comparison
  - Match Outcome Distribution
  - Parity Choice Distribution
- **4 Academic References** (requirement: ≥3)
- **Statistical Analysis** with 95% confidence intervals
- **Actionable Recommendations** for optimal configuration

## File Locations

```
doc/research_notes/
├── experiments.ipynb          # Main notebook
├── experiments.html           # Pre-rendered version (601 KB)
├── README.md                  # Detailed documentation
├── plot1_strategy_comparison.png
├── plot2_timeout_impact.png
└── plot3_4_retry_outcomes.png
```

## Dependencies

All dependencies are listed in:
- `requirements.txt` - For pip install
- `pyproject.toml` - For modern Python packaging

Research packages installed:
- jupyter>=1.1.0
- numpy>=2.0.0
- pandas>=2.0.0
- matplotlib>=3.8.0
- seaborn>=0.13.0
- scipy>=1.13.0
- ipykernel>=7.0.0
- nbconvert>=7.0.0

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python verify_installation.py

# Start Jupyter
jupyter notebook

# Execute notebook from command line
jupyter nbconvert --to html --execute doc/research_notes/experiments.ipynb

# View HTML output
open doc/research_notes/experiments.html
```

## For Development

If you want to modify the notebook:

1. Start Jupyter: `jupyter notebook`
2. Open: `doc/research_notes/experiments.ipynb`
3. Make changes
4. Run all cells: Cell → Run All
5. Save: File → Save
6. Generate HTML: File → Download as → HTML

## Support

For detailed installation instructions, see:
- `INSTALL.md` - Comprehensive installation guide
- `doc/research_notes/README.md` - Notebook documentation
- `requirements.txt` - Exact package versions

For questions about the research methodology, see the notebook itself - it includes:
- Introduction & Methodology
- Mathematical Formulation
- Statistical Analysis
- Recommendations & Conclusions
