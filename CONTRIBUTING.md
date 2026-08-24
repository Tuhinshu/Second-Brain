  Contributing to Second Brain Execution Engine

Thank you for your interest in contributing to the *Second Brain Execution Engine*! We welcome bug reports, feature suggestions, architecture enhancements, and code contributions.



  Code of Conduct

Please maintain a welcoming, inclusive, and professional environment for everyone. Respect different viewpoints and focus on constructive feedback.



  Getting Started

1. *Fork the Repository* on GitHub.
2. *Clone your fork* locally:
   bash
   git clone https://github.com/yourusername/SecondBrain.git
   cd SecondBrain
   
3. *Create a Virtual Environment*:
   bash
   python m venv .venv
    Windows (PowerShell):
   .venv\Scripts\Activate.ps1
    macOS / Linux:
   source .venv/bin/activate
   
4. *Install Dependencies*:
   bash
   pip install r requirements.txt
   
5. *Set Up Environment Variables*:
   bash
   cp .env.example .env
    Populate .env with your Notion API credentials
   



  Development Workflow

1. Create a descriptive feature branch:
   bash
   git checkout b feature/yourfeaturename
    or
   git checkout b fix/issuedescription
   

2. Follow codebase conventions:
    Use strict type annotations wherever possible.
    Use Pydantic models for data parsing and validation.
    Maintain separation of concerns between notion_service.py, scoring_engine.py, Models.py, and app.py.
    Never commit .env or sensitive Notion tokens.

3. Test your changes locally:
   bash
   streamlit run app.py
   

4. Commit your changes with clear, semantic commit messages:
   bash
   git commit m "feat: add domain color coding to task cards"
   

5. Push to your fork and submit a Pull Request:
   bash
   git push origin feature/yourfeaturename
   



  Suggestions for Contributions

 [ ] Mobile responsive layout optimizations
 [ ] Integration with Notion Calendar / Due Dates
 [ ] Time tracking stopwatch / Pomodoro timer integration
 [ ] Analytics dashboard for completed tasks & velocity trends
 [ ] Subtask / dependency tree support



  License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
