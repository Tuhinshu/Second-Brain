# Notion Setup Guide

This guide walks you through setting up the required Notion databases and API integration for the **Second Brain Execution Engine**.

---

## Table of Contents
1. [Step 1: Create a Notion Integration (API Key)](#step-1-create-a-notion-integration-api-key)
2. [Step 2: Set Up the Tasks Database](#step-2-set-up-the-tasks-database)
3. [Step 3: Set Up the Assets Database (Optional)](#step-3-set-up-the-assets-database-optional)
4. [Step 4: Connect Integration to Databases](#step-4-connect-integration-to-databases)
5. [Step 5: Extract Database IDs](#step-5-extract-database-ids)
6. [Step 6: Configure `.env`](#step-6-configure-env)

---

## Step 1: Create a Notion Integration (API Key)

1. Go to [Notion Developers Integrations](https://www.notion.so/profile/integrations).
2. Click **"+ New integration"**.
3. Name your integration (e.g., `Second Brain Execution Engine`).
4. Select the associated workspace.
5. Under **Capabilities**, ensure the integration has:
   - *Read content*
   - *Update content*
   - *Insert content*
6. Click **Save** / **Submit**.
7. Copy the **Internal Integration Secret** (`secret_...` or `ntn_...`). This will be your `NOTION_API_KEY`.

---

## Step 2: Set Up the Tasks Database

Create a **Full Page Table Database** in Notion named `Tasks` (or any name you prefer).

### Database Properties Schema

Configure the database columns with the exact property names and types below:

| Property Name | Property Type | Options / Configuration | Notes |
| :--- | :--- | :--- | :--- |
| **Task Name** | **Title** *(Default)* | — | Primary task title / deliverable name |
| **Status** | **Status** | `Not started`, `In progress`, `Paused`, `Done`, `Backlog` | Track active workflow state (Notion native Status property type) |
| **Domain** | **Select** | `AIESEC`, `Academics`, `Clients`, `Personal` | Used for context switching and filtering |
| **Impact** | **Number** | Format: Number (1 to 5) | Strategic value / revenue / leverage |
| **Urgency** | **Number** | Format: Number (1 to 5) | Time-sensitivity / deadline proximity |
| **Estimated Hours** | **Number** | Format: Number (e.g. 1.0, 2.5) | Execution time required |
| **Someone Waiting?** | **Checkbox** | — | Checked if blocking a teammate or client (+5 priority bonus) |
| **State Anchor** | **Text** *(Rich text)* | — | Stores next 15-minute physical action when paused |

> [!IMPORTANT]
> Property names are case-sensitive and must match the table above exactly.

---

## Step 3: Set Up the Assets Database (Optional)

Create a second **Table Database** named `Asset Vault` for storing reusable links, templates, and guides.

### Asset Database Properties Schema

| Property Name | Property Type | Options / Configuration | Notes |
| :--- | :--- | :--- | :--- |
| **Title** | **Title** *(Default)* | — | Name of resource or document |
| **Type** | **Select** | `Doc/Guide`, `Template`, `Snippet`, `Tool` | Type of reusable asset |
| **Domain** | **Select** | `General`, `AIESEC`, `Academics`, `Clients`, `Personal` | Associated operational domain |
| **URL** | **URL** | Web link / Notion page link | External link or internal reference |
| **Tags** | **Multi-select** | e.g. `finance`, `marketing`, `strategy` | Searchable keyword tags |

---

## Step 4: Connect Integration to Databases

For **both** databases:

1. Open the database page in Notion.
2. Click the **•••** (three dots) menu in the top-right corner.
3. Scroll down and click **"Connect to"** (or **"Add connections"**).
4. Search for your integration name (e.g., `Second Brain Execution Engine`) and click to connect.
5. Confirm access when prompted.

> [!WARNING]
> If you do not connect your integration to the databases, Notion API queries will return `404 Not Found` or `401 Unauthorized`.

---

## Step 5: Extract Database IDs

To find a database ID from the Notion URL:

1. Open your database in Notion (in a web browser or copy link from the app).
2. The URL will look like:
   ```text
   https://www.notion.so/myworkspace/a8aec43384f447ed84390e8e42c2e089?v=...
   ```
3. The **Database ID** is the 32-character alphanumeric string between your workspace name and the `?v=`:
   - Example ID: `a8aec43384f447ed84390e8e42c2e089` (or with hyphens `a8aec433-84f4-47ed-8439-0e8e42c2e089`). Both formats work.

---

## Step 6: Configure `.env`

Create a `.env` file in the root of the project directory (or copy from `.env.example`):

```env
NOTION_API_KEY=ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_TASKS_DB_ID=your_tasks_database_id_here
NOTION_ASSETS_DB_ID=your_assets_database_id_here
# Optional active task limit (default: 50, allowed bounds: 1 to 500)
MAX_ACTIVE_TASKS=50
```

Run the application:
```bash
streamlit run app.py
```
