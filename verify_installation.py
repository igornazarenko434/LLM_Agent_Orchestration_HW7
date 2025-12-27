#!/usr/bin/env python3
"""
Installation Verification Script
Verifies all dependencies are correctly installed for Even/Odd League project.
"""
import sys
from typing import List, Tuple


def verify_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """
    Verify a package can be imported.

    Args:
        package_name: Display name of the package
        import_name: Actual import name (defaults to package_name)

    Returns:
        Tuple of (success: bool, version: str)
    """
    if import_name is None:
        import_name = package_name

    try:
        module = __import__(import_name)
        version = getattr(module, "__version__", "unknown")
        return (True, version)
    except ImportError as e:
        return (False, str(e))


def main():
    """Run installation verification."""
    print("=" * 80)
    print("EVEN/ODD LEAGUE - INSTALLATION VERIFICATION")
    print("=" * 80)
    print()

    # Define packages to check
    core_packages = [
        ("FastAPI", "fastapi"),
        ("Uvicorn", "uvicorn"),
        ("Pydantic", "pydantic"),
        ("httpx", "httpx"),
        ("Requests", "requests"),
    ]

    test_packages = [
        ("pytest", "pytest"),
        ("pytest-cov", "pytest_cov"),
        ("pytest-asyncio", "pytest_asyncio"),
    ]

    quality_packages = [
        ("black", "black"),
        ("flake8", "flake8"),
        ("mypy", "mypy"),
    ]

    research_packages = [
        ("Jupyter", "jupyter"),
        ("NumPy", "numpy"),
        ("Pandas", "pandas"),
        ("Matplotlib", "matplotlib"),
        ("Seaborn", "seaborn"),
        ("SciPy", "scipy"),
        ("IPyKernel", "ipykernel"),
        ("nbconvert", "nbconvert"),
    ]

    utility_packages = [
        ("python-dateutil", "dateutil"),
    ]

    all_success = True

    # Check each category
    categories = [
        ("Core Framework", core_packages),
        ("Testing", test_packages),
        ("Code Quality", quality_packages),
        ("Data Science & Research", research_packages),
        ("Utilities", utility_packages),
    ]

    for category_name, packages in categories:
        print(f"\n📦 {category_name}:")
        print("-" * 80)

        for display_name, import_name in packages:
            success, version = verify_package(display_name, import_name)

            if success:
                status = "✅"
                info = f"v{version}"
            else:
                status = "❌"
                info = f"MISSING - {version}"
                all_success = False

            print(f"  {status} {display_name:20} {info}")

    # Summary
    print()
    print("=" * 80)
    if all_success:
        print("✅ ALL PACKAGES INSTALLED SUCCESSFULLY")
        print()
        print("Next steps:")
        print("  1. Run tests: pytest tests/")
        print("  2. Start league: cd agents/league_manager && python main.py")
        print("  3. Open notebook: jupyter notebook doc/research_notes/experiments.ipynb")
    else:
        print("❌ SOME PACKAGES ARE MISSING")
        print()
        print("To install missing packages:")
        print("  pip install -r requirements.txt")
        print()
        print("Or install from pyproject.toml:")
        print("  pip install -e .")
        sys.exit(1)

    print("=" * 80)
    print()

    # Additional checks
    print("🔍 Additional Checks:")
    print("-" * 80)

    # Check Python version
    py_version = sys.version_info
    print(f"  Python Version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version.major >= 3 and py_version.minor >= 10:
        print("  ✅ Python version >= 3.10")
    else:
        print(f"  ⚠️  Python 3.10+ recommended (current: {py_version.major}.{py_version.minor})")

    # Check virtual environment
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    if in_venv:
        print(f"  ✅ Virtual environment active: {sys.prefix}")
    else:
        print("  ⚠️  Not in virtual environment (recommended to use venv)")

    # Check Jupyter kernel
    try:
        from jupyter_client.kernelspec import KernelSpecManager

        ksm = KernelSpecManager()
        kernels = ksm.get_all_specs()
        print(f"  ✅ Jupyter kernels available: {len(kernels)}")
    except Exception:
        print("  ⚠️  Could not check Jupyter kernels")

    print()
    print("=" * 80)
    print("🎉 Installation verification complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
