<div align="center">

# Second Brain Execution Engine
### Algorithmic Task Scoring, State Anchoring and Frictionless Notion Cockpit

<p align="center">
  <b>A high-leverage execution cockpit that eliminates decision fatigue by mathematically ranking tasks, automating Notion workflows, and eliminating task-switching friction through State Anchoring.</b>
</p>

[Key Features](#key-features) •
[Architecture](#system-architecture) •
[Priority Formula](#dynamic-priority-scoring-algorithm) •
[Quickstart](#quickstart-guide) •
[Notion Setup](#notion-database-setup) •
[Documentation](#documentation)

---

</div>

## Why Second Brain Execution Engine?

Standard to-do lists fail because they present flat, overwhelming backlogs that lead to analysis paralysis. 

The **Second Brain Execution Engine** transforms your Notion task database into an active **24-Hour Execution Arena**:
- **Zero Ambiguity:** Always surfaces the top 3 highest-leverage tasks to execute right now.
- **Mathematical Triage:** Dynamic prioritization based on impact, urgency, estimated duration, and blocker status.
- **Context Preservation:** Pausing a task forces you to capture a "State Anchor" to resume immediately without mental friction.
- **Automated Scoping:** Notion pages automatically receive execution checklists the moment a task begins.

---

## Key Features

| Feature | Description |
| :--- | :--- |
| **24-Hour Execution Arena** | Surfaces and pins the **Top 3** highest-priority tasks. Active (`In Progress`) tasks are always pinned at the top. |
| **Algorithmic Scoring** | Dynamically calculates weighted priority scores based on strategic impact, urgency, estimated hours, and team blockers. |
| **State Anchor Protocol** | When pausing, captures the exact next 15-minute physical action into Notion to eliminate restart inertia. |
| **Template Injection** | Injects an `Execution Scope & Checklist` structure into empty Notion pages the moment a task starts. |
| **Backlog Drawer** | An expandable overflow queue for lower-ranked items with one-click **Promote** actions. |
| **Reusable Asset Vault** | Searchable knowledge vault to retrieve guides, templates, and links filtered by operational domain. |
| **Quick Task Capture** | Low-friction in-app form for instant capture with customized domain and weighting parameters. |
| **Domain Filtering** | One-click context switching across **Global HUD**, **AIESEC**, **Academics**, **Clients**, and **Personal** workspaces. |

---

## System Architecture

```mermaid
flowchart TD
    subgraph UI_Layer ["Streamlit Presentation Layer (app.py)"]
        Arena["24-Hour Execution Arena"]
        Capture["Quick Task Capture Dialog"]
        Vault["Reusable Asset Vault"]
        DomainFilter["Domain Switcher (Global / AIESEC / Academics / Clients / Personal)"]
    end

    subgraph Core_Engine ["Core Logic & Validation"]
        Models["Pydantic Models (models.py)"]
        Scoring["Dynamic Scoring Engine (scoring_engine.py)"]
        Config["Environment Configuration (config.py)"]
    end

    subgraph Notion_Bridge ["Notion Service Layer (notion_service.py)"]
        Parser["Page & Property Parsers"]
        BlockInjector["Template Block Injector"]
        QueryEngine["Compound Database Query Engine"]
    end

    subgraph Notion_Cloud ["Notion Workspace (Authoritative Backend)"]
        TasksDB[("Tasks Database")]
        AssetsDB[("Asset Vault Database")]
    end

    UI_Layer <--> Core_Engine
    Core_Engine <--> Notion_Bridge
    Notion_Bridge <--> Notion_Cloud