# Contributing to Second Brain Execution Engine

Thank you for your interest in contributing to the **Second Brain Execution Engine**! We welcome bug reports, feature suggestions, architecture enhancements, and code contributions.

---

## Code of Conduct

Please maintain a welcoming, inclusive, and professional environment for everyone. Respect different viewpoints and focus on constructive feedback.

---

## Getting Started

1. **Fork the Repository** on GitHub: [https://github.com/Tuhinshu/Second-Brain](https://github.com/Tuhinshu/Second-Brain)
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/Second-Brain.git
   cd Second-Brain
   ```

3. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv

   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1

   # Windows (cmd.exe):
   .venv\Scripts\activate.bat

   # macOS / Linux:
   source .venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   # Standard installation:
   pip install -r requirements.txt

   # Deterministic production lockfile installation:
   pip install -r requirements-lock.txt
   ```

5. **Set up environment variables**:
   ```bash
   # Copy template
   cp .env.example .env

   # Populate .env with your Notion credentials:
   # NOTION_API_KEY=ntn_...
   # NOTION_TASKS_DB_ID=...
   # NOTION_ASSETS_DB_ID=...
   ```

---

## Development Workflow

1. **Create a descriptive feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Follow codebase conventions**:
   - Use strict type annotations throughout (`typing.Optional`, `typing.Literal`, `typing.Callable`).
   - Use Pydantic models in `Models.py` for data validation.
   - Maintain clear separation of concerns:
     - `notion_service.py`: Notion API interactions, retries, and data extraction.
     - `scoring_engine.py`: Pure deterministic mathematical ranking algorithms.
     - `Models.py`: Pydantic data models and state transitions.
     - `config.py`: Environment variable loading and validation.
     - `app.py`: Streamlit presentation components and user interaction flows.
   - **Never commit `.env` or sensitive API keys.**

3. **Code Quality & Verification**:
   Before submitting your changes, run static linting, formatting checks, compilation, and the test suite:
   ```bash
   # 1. Run Ruff linter and code style checks
   ruff check .
   ruff format --check .

   # Automatically format code if needed:
   ruff format .

   # 2. Verify Python syntax and bytecode compilation
   python -m py_compile app.py config.py notion_service.py Models.py scoring_engine.py

   # 3. Run the automated test suite (42 unit & integration tests)
   python -m unittest discover tests -v

   # 4. Test locally in the browser
   streamlit run app.py
   ```

4. **Controlled Dependency Upgrades**:
   To update or add dependencies deliberately:
   - Modify the pinned version in `requirements.txt`.
   - Verify the test suite passes: `python -m unittest discover tests -v`.
   - Update `requirements-lock.txt` to lock all transitive dependencies.

5. **Commit your changes with clear semantic messages**:
   ```bash
   git add .
   git commit -m "feat: add domain color coding to task cards"
   ```

6. **Push to your fork and submit a Pull Request**:
   ```bash
   git push origin feature/your-feature-name
   ```

---

## Suggestions for Contributions

- [ ] Mobile responsive layout optimizations
- [ ] Integration with Notion Calendar / Due Dates
- [ ] Time tracking stopwatch / Pomodoro timer integration
- [ ] Analytics dashboard for completed tasks & velocity trends
- [ ] Subtask / dependency tree support

---

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
