<div align="center">

  Second Brain Execution Engine
 *Algorithmic Task Scoring, State Anchoring & Frictionless Notion Cockpit*

<br />

<p align="center">
  <b>A highleverage execution cockpit that eliminates decision fatigue by mathematically ranking tasks, automating Notion workflows, and eliminating taskswitching friction through State Anchoring.</b>
</p>

[Key Features](keyfeatures) •
[Architecture](systemarchitecture) •
[Priority Formula](dynamicpriorityscoringalgorithm) •
[Quickstart](quickstartguide) •
[Notion Setup](notiondatabasesetup) •
[Documentation](documentation)



</div>

  Why Second Brain Execution Engine?

Standard todo lists fail because they present flat, overwhelming backlogs that lead to analysis paralysis. 

The <i>Second Brain Execution Engine</i> transforms your Notion task database into an active <b>24Hour Execution Arena</b>:
 <b>Zero Ambiguity</b>: Always know the top 3 highestleverage tasks to execute right now.
 <b>Mathematical Triage</b>: Prioritization based on impact, urgency, estimated duration, and blocker status.
 <b>Context Preservation</b>: Pausing a task requires defining a "State Anchor" so you can resume immediately without lost momentum.
 <b>Automated Scoping</b>: Notion pages automatically receive execution templates and checklists upon starting.



  Key Features

| Feature | Description |
| : | : |
|  <b>24Hour Execution Arena</b> <br> Surfaces and pins the Top 3 highestpriority tasks. Active ("In Progress") tasks are always pinned at the top. |
|  <b>Algorithmic Scoring</b> <br> Dynamically calculates weighted priority scores based on strategic impact, urgency, estimated hours, and teammate blocker flags. |
|  <b>State Anchor Protocol</b> <br> When pausing a task, captures the exact next 15minute physical action into Notion to eliminate restart friction. |
|  <b>Automatic Template Injection</b> <br> Injects an Execution Scope & Checklist block structure into empty Notion task pages the moment a task begins. |
|  <b>Backlog Drawer</b> <br> An expandable overflow queue for lowerranked items with oneclick <b>Promote</b> and <b>Delete</b> actions. |
|  <b>Reusable Asset Vault</b> <br> Searchable knowledge vault to quickly retrieve documents, guides, templates, and bookmarks filtered by operational domain. |
|  <b>Quick Task Capture</b> <br> Lowfriction modal dialog and dedicated tab for instant capture with customized domain and weighting parameters. |
|  <b>Domain Filtering</b> <br> Oneclick context switching across <b>Global HUD</b>, <b>AIESEC</b>, <b>Academics</b>, <b>Clients</b>, and <b>Personal</b> workspaces. |



  System Architecture

mermaid
flowchart TD
    subgraph UI_Layer [" Streamlit Presentation Layer (app.py)"]
        Arena["24Hour Execution Arena"]
        Capture["Quick Task Capture Dialog"]
        Vault["Reusable Asset Vault"]
        DomainFilter["Domain Switcher (Global / AIESEC / Academics / Clients / Personal)"]
    end

    subgraph Core_Engine [" Core Logic & Validation"]
        Models["Pydantic Models (Models.py)"]
        Scoring["Dynamic Scoring Engine (scoring_engine.py)"]
        Config["Environment Configuration (config.py)"]
    end

    subgraph Notion_Bridge [" Notion Service Layer (notion_service.py)"]
        Parser["Page & Property Parsers"]
        BlockInjector["Template Block Injector"]
        QueryEngine["Compound Database Query Engine"]
    end

    subgraph Notion_Cloud [" Notion Workspace (Authoritative Backend)"]
        TasksDB[("Tasks Database")]
        AssetsDB[("Asset Vault Database")]
    end

    UI_Layer <> Core_Engine
    Core_Engine <> Notion_Bridge
    Notion_Bridge <> Notion_Cloud




  Dynamic Priority Scoring Algorithm

Every task is evaluated using the following weighting formula:

$$\mathbf{Priority\ Score} = (\text{Impact} \times 2.0) + \text{Urgency} + \mathbf{Blocker\ Bonus} + (\text{Estimated\ Hours} \times 1.5)$$

 Variable Weights & Rationale:
 **$\text{Impact}$ (1 – 5)**: Weighted at **$2.0\times$**. Highleverage, revenuegenerating, or strategic deliverables heavily dominate the ranking.
 **$\text{Urgency}$ (1 – 5)**: Added directly to factor in deadlines and time sensitivity.
 **$\text{Blocker Bonus}$ ($+5.0$)**: If Someone Waiting? is **True**, an automatic $+5.0$ boost is applied to unblock team members or clients immediately.
 **$\text{Estimated Hours}$ ($0.25  12.0\text{h}$)**: Weighted at **$1.5\times$** to account for dedicated deepwork sessions.

 Ranking & Pinning Rule:
1. Tasks in **In progress** status are always pinned to the top of the queue.
2. Remaining tasks are sorted descending by their computed **$\mathbf{Priority\ Score}$**.



  Quickstart Guide

 Prerequisites
 Python 3.10 or higher
 A Notion account with an Integration API Key ([Setup Guide](NOTION_SETUP.md))

 1. Clone the Repository
bash
git clone https://github.com/yourusername/SecondBrain.git
cd SecondBrain


 2. Create and Activate a Virtual Environment
bash
 Windows (PowerShell):
python m venv .venv
.venv\Scripts\Activate.ps1

 macOS / Linux:
python3 m venv .venv
source .venv/bin/activate


 3. Install Dependencies
bash
pip install r requirements.txt


 4. Configure Environment Variables
Create a .env file in the project root (or copy .env.example):
bash
cp .env.example .env


Edit .env and provide your Notion credentials:
env
NOTION_API_KEY=ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_TASKS_DB_ID=your_tasks_database_id_here
NOTION_ASSETS_DB_ID=your_assets_database_id_here


 5. Launch the Application
bash
streamlit run app.py


The app will open automatically in your browser at http://localhost:8501.



  Notion Database Setup

The execution engine connects directly to your Notion workspace via the official REST API. 

For full stepbystep instructions on setting up properties, relations, and permissions, see the <b>[Notion Setup Guide (NOTION_SETUP.md)](NOTION_SETUP.md)</b>.

 Quick Database Properties Reference

  Tasks Database
| Property | Type | Description |
| : | : | : |
| Task Name | <b>Title</b> | Name of the task / deliverable |
| Status | <b>Status / Select</b> | Not started, In progress, Paused, Done, Backlog |
| Domain | <b>Select</b> | AIESEC, Academics, Clients, Personal |
| Impact | <b>Number</b> | Rating from 1 (low) to 5 (high) |
| Urgency | <b>Number</b> | Rating from 1 (low) to 5 (immediate) |
| Estimated Hours| <b>Number</b> | Float duration (e.g. 1.5) |
| Someone Waiting? | <b>Checkbox</b> | Checked if blocking someone else |
| State Anchor | <b>Text</b> | Next physical 15minute action when paused |

  Asset Vault Database 
| Property | Type | Description |
| : | : | : |
| Title | <b>Title</b> | Resource / document name |
| Type | <b>Select</b> | Doc/Guide, Template, Snippet, Tool |
| Domain | <b>Select</b> | General, AIESEC, Academics, Clients, Personal |
| URL | <b>URL</b> | External link or internal page link |
| Tags | <b>Multiselect</b> | Categorical tags for search |



  Project Structure

text
SecondBrain/
 .streamlit/
    config.toml           Streamlit theme & UI configurations
 .env.example              Example template for environment variables
 .gitignore                Ignored files, virtual environments, and secrets
 app.py                    Main Streamlit execution dashboard & UI
 config.py                 Environment loader & credential validator
 Models.py                 Pydantic v2 schemas (TaskModel, AssetModel)
 notion_service.py         Notion API service layer & block automation
 scoring_engine.py         Algorithmic scoring & ranking engine
 requirements.txt          Project dependencies
 ARCHITECTURE.md           Indepth technical architecture document
 NOTION_SETUP.md           Complete Notion database setup instructions
 CONTRIBUTING.md           Opensource contribution guidelines
 LICENSE                   MIT License
 README.md                 Repository documentation & guide
 Cover.jpg                 Dashboard header visual asset
 bg.jpg                    Dashboard backdrop visual asset




  Documentation

 [Notion Setup Guide](NOTION_SETUP.md) — Detailed instructions for database schemas and API connection.
 [Architecture & Design](ARCHITECTURE.md) — Indepth breakdown of components, sequences, and state handling.
 [Contributing Guidelines](CONTRIBUTING.md) — Guidelines for issues, feature requests, and pull requests.
 [License](LICENSE) — MIT License details.



  License

This project is licensed under the [MIT License](LICENSE).



<div align="center">
  <b>Built for high performers who value execution over organization.</b>
</div>
