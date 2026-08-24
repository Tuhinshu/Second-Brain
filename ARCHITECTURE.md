  Technical Architecture & Design Document

 1. System Overview

The *Second Brain Execution Engine* is a highperformance productivity cockpit built to eliminate cognitive friction and decision fatigue. Unlike standard todo applications that merely list items, this system acts as an algorithmic triage system that pulls active tasks from Notion, prioritizes them via a weighted scoring formula, and surfaces a laserfocused top3 execution queue.

mermaid
graph TD
    User([User / Browser]) <> UI[Streamlit Frontend App<br>app.py]
    UI <> Logic[Scoring & Ranking Engine<br>scoring_engine.py]
    UI <> Service[Notion Service Layer<br>notion_service.py]
    Logic <> Models[Pydantic Models<br>Models.py]
    Service <> Models
    Service <> Config[Config Loader<br>config.py]
    Config <> Env[Environment .env]
    Service <> NotionAPI[(Notion REST API v2)]
    
    subgraph Notion Workspace
        TasksDB[(Tasks Database)]
        AssetsDB[(Asset Vault Database)]
    end
    
    NotionAPI <> TasksDB
    NotionAPI <> AssetsDB




 2. Core Architectural Components

 2.1 Presentation & State Management Layer (app.py)
 *Framework*: Streamlit (wide layout, responsive containers).
 *Custom UI System*: Vanilla CSS injecting tailored amber/slate themes (B45309), custom hero headers with base64 encoded background imagery, button state microtransitions, and dialog modals.
 *Session State*: Manages active_page, active_domain, and pause_prompt_id dynamically across hotreloads and reruns.
 *Modal Dialogs*: Uses Streamlit @st.dialog for nondisruptive task capture without losing context.

 2.2 Domain & Data Validation Layer (Models.py)
 Built on *Pydantic v2* (BaseModel, Field, Literal).
 Ensures runtime validation, strict bounds on numerical inputs (e.g. 1 <= impact <= 5, 0.25 <= estimated_hours <= 12.0), and standardized types across Notion API serialization/deserialization.
 *TaskModel*: Encapsulates task attributes, status, domain, impact, urgency, blockers, state anchor notes, and computed priority scores.
 *AssetModel*: Encapsulates reusable knowledge items, tags, URLs, and categorical domains.

 2.3 Algorithmic Scoring Engine (scoring_engine.py)
 Pure, sideeffectfree functional module.
 Calculates an objective *Priority Score* for each task using multifactor weighted parameters:
  
$$\text{Priority Score} = (\text{Impact} \times 2.0) + \text{Urgency} + \text{Blocker Bonus} + (\text{Estimated Hours} \times 1.5)$$

Where:
 $\text{Blocker Bonus} = 5.0$ if $\text{Someone Waiting?} = \text{True}$, else $0.0$.
 *Sorting Rule*: Tasks with status In progress are always pinned to the top of the queue. Remaining tasks are sorted descending by priority_score.

 2.4 Notion Integration Service Layer (notion_service.py)
 Implements the adapter pattern over the official notionclient SDK.
 Translates Notion's nested property structures (Title, Select, Status, Number, Checkbox, Rich Text) into stronglytyped Pydantic models and viceversa.
 *Dynamic Block Injection*: Automatically generates and appends default execution scope checklists (Execution Scope & Checklist) into newly started Notion task pages when body blocks are empty.
 *Domainbased Filtering*: Generates structured compound query payloads to filter tasks by lifecycle state and operational domain.



 3. Data Flow & Execution Pipeline

mermaid
sequenceDiagram
    autonumber
    actor User
    participant App as Streamlit UI (app.py)
    participant Engine as Scoring Engine
    participant Notion as Notion Service
    participant API as Notion API

    User>>App: Opens Dashboard / Selects Domain Filter
    App>>Notion: fetch_active_tasks(domain)
    Notion>>API: databases.query(filter: status != 'Done')
    API>>Notion: Raw JSON Pages
    Notion>>App: List[TaskModel]
    App>>Engine: rank_tasks(tasks)
    Engine>>App: Sorted & Pinned Task Queue
    App>>User: Renders Top 3 Arena + Backlog Drawer

    opt User clicks "Start Task"
        User>>App: Click 'Start'
        App>>Notion: update_task_status(id, 'In progress')
        App>>Notion: inject_template_blocks_if_empty(id)
        Notion>>API: pages.update() & blocks.children.append()
        App>>User: Refresh with task pinned in focus
    end

    opt User clicks "Pause Task" (State Anchor Protocol)
        User>>App: Click 'Pause'
        App>>User: Display State Anchor Prompt
        User>>App: Inputs next physical action note & submits
        App>>Notion: update_task_status(id, 'Not started', state_anchor)
        Notion>>API: pages.update()
        App>>User: Task paused with state anchor preserved
    end




 4. The State Anchor Protocol

Cognitive science shows that task interruption causes severe attention residue. When returning to a paused task, users waste significant energy figuring out where they left off.

The *State Anchor Protocol* solves this:
1. When a user clicks *Pause*, the application intercepts the action.
2. It prompts: *"What is the exact next 15minute physical action to take when resuming?"*
3. The answer is committed directly to the Notion page's State Anchor property.
4. When the task appears again in the Execution Arena, the anchor note is prominently surfaced in an information badge.



 5. Security & Deployment Architecture

 *Zero Hardcoded Secrets*: Secrets are loaded through standard .env configuration using dotenv.
 *Database Decoupling*: Database schema alterations in Notion are isolated to the parser functions in notion_service.py.
 *Stateless Execution*: The application holds no persistent local database; Notion acts as the authoritative source of truth.