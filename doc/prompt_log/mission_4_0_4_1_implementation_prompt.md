lets proceed to mission 4.0 and 4.1. i want you to read all the subsections in those missions and implement all. you must create and implement those missiond with the awareness of all the code and architecture and all the code files we build until now. you have also the knowledge of all the already existing tests we have and you need to pt them in the correct right place they need to be in the tests folder structure so all will be connected and will correctly work according to our whole project structure including the integration with the pytest.ini or pyproject.toml we build and with the coverage settings we want )85%) and with all the needed markers for each unit test we have for the tests we already built (you need to set correctly which unit test or any other type). you need also to make sure all is working also and copatible with our sdk package we will use later but also can run in our project, so make sure the overll folder location for all the tests is the best pratise. i want you to implement now just missiosn 4.0 and 4.1 (if we already built unit tests for some of the submissions sections than use the existing tests). after you finish run all tests and verify all passes, tests that didnt pass debug and fix what is needed. before all these implementation, add new file inside the doc folder inside the prompt log folder with this full prompt i wrote you and add under it what did you undestand what you need to do and how this prompt helped you to implement this mission, dont write all your plan just the full prompt and how it helped you.

---

### Understanding & Implementation Plan

**Objective:** Implement Missions 4.0 (Pytest Configuration) and 4.1 (Unit Test Templates/Organization).

**Understanding:**
The user wants to formalize the testing infrastructure. Although we have been running tests, they are currently scattered in the root of the `tests/` directory. This task involves:
1.  **Configuration (M4.0):** Establishing a robust `pytest.ini` with coverage settings (85% target), test markers (unit, integration, e2e, slow), and correct test paths.
2.  **Structure (M4.1):** Moving existing SDK-related tests from `tests/` to `tests/unit/test_sdk/` to match best practices and the project structure.
3.  **Fixtures:** Creating a `tests/conftest.py` with shared fixtures (specifically a mock MCP server as required by M4.0).
4.  **Verification:** Ensuring all tests pass in their new locations and coverage is reported correctly.

**How this prompt helped:**
This prompt explicitly directed the reorganization of the test suite, which was previously flat. It enforced the creation of specific configuration files (`pytest.ini`, `conftest.py`) and defined the markers needed (`unit`, `integration`, etc.), ensuring the project scales maintainably rather than just having a loose collection of test scripts. It also emphasized maintaining the high coverage standard we've already achieved.
