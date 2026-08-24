from typing import List, Optional
from datetime import datetime
from notion_client import Client
import config
from Models import TaskModel, AssetModel

notion = Client(auth=config.NOTION_API_KEY)

def parse_task_page(page: dict) -> TaskModel:
    props = page.get("properties", {})
    title_list = props.get("Task Name", {}).get("title", [])
    task_name = title_list[0]["plain_text"] if title_list else "Untitled Task"

    status_obj = props.get("Status", {}).get("select") or props.get("Status", {}).get("status")
    status = status_obj.get("name", "Not started") if status_obj else "Not started"

    domain_obj = props.get("Domain", {}).get("select")
    domain = domain_obj.get("name", "Personal") if domain_obj else "Personal"

    impact = props.get("Impact", {}).get("number") or 3
    urgency = props.get("Urgency", {}).get("number") or 3
    estimated_hours = props.get("Estimated Hours", {}).get("number") or 1.0
    someone_waiting = props.get("Someone Waiting?", {}).get("checkbox", False)

    anchor_list = props.get("State Anchor", {}).get("rich_text", [])
    state_anchor = anchor_list[0]["plain_text"] if anchor_list else None

    return TaskModel(
        id=page["id"],
        task_name=task_name,
        status=status,
        domain=domain,
        impact=impact,
        urgency=urgency,
        estimated_hours=float(estimated_hours),
        someone_waiting=someone_waiting,
        state_anchor=state_anchor
    )

def parse_asset_page(page: dict) -> AssetModel:
    props = page.get("properties", {})
    
    title_list = props.get("Title", {}).get("title", [])
    title = title_list[0]["plain_text"] if title_list else "Untitled Asset"

    type_obj = props.get("Type", {}).get("select")
    asset_type = type_obj.get("name", "Doc/Guide") if type_obj else "Doc/Guide"

    domain_obj = props.get("Domain", {}).get("select")
    domain = domain_obj.get("name", "General") if domain_obj else "General"

    custom_url = props.get("URL", {}).get("url")
    url = custom_url if custom_url else page.get("url")

    tags_list = props.get("Tags", {}).get("multi_select", [])
    tags = [t["name"] for t in tags_list]

    return AssetModel(
        id=page["id"],
        title=title,
        type=asset_type,
        domain=domain,
        url=url,
        tags=tags
    )

def fetch_active_tasks(domain_filter: Optional[str] = None) -> List[TaskModel]:
    filter_conditions = [
        {"property": "Status", "status": {"does_not_equal": "Done"}}
    ]

    if domain_filter and domain_filter != "Global":
        filter_conditions.append(
            {"property": "Domain", "select": {"equals": domain_filter}}
        )

    query_payload = {
        "database_id": config.NOTION_TASKS_DB_ID,
        "filter": {"and": filter_conditions} if len(filter_conditions) > 1 else filter_conditions[0]
    }

    response = notion.databases.query(**query_payload)
    return [parse_task_page(page) for page in response.get("results", [])]


def create_task(task: TaskModel) -> str:
    properties = {
        "Task Name": {"title": [{"text": {"content": task.task_name}}]},
        "Status": {"status": {"name": task.status}},
        "Domain": {"select": {"name": task.domain}},
        "Impact": {"number": task.impact},
        "Urgency": {"number": task.urgency},
        "Estimated Hours": {"number": task.estimated_hours},
        "Someone Waiting?": {"checkbox": task.someone_waiting},
    }
    
    if task.state_anchor:
        properties["State Anchor"] = {
            "rich_text": [{"text": {"content": task.state_anchor}}]
        }

    response = notion.pages.create(
        parent={"database_id": config.NOTION_TASKS_DB_ID},
        properties=properties
    )
    return response["id"]


def update_task_status(page_id: str, new_status: str, state_anchor: Optional[str] = None) -> None:
    properties = {
        "Status": {"status": {"name": new_status}}
    }

    if state_anchor is not None:
        properties["State Anchor"] = {
            "rich_text": [{"text": {"content": state_anchor}}]
        }

    notion.pages.update(page_id=page_id, properties=properties)


def delete_task(page_id: str) -> None:
    """Archive/delete a task page in Notion."""
    notion.pages.update(page_id=page_id, archived=True)


def inject_template_blocks_if_empty(page_id: str) -> None:
    blocks = notion.blocks.children.list(block_id=page_id)
    if not blocks.get("results"):
        default_blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Execution Scope & Checklist"}}]
                }
            },
            {
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": "Initial breakdown & setup"}}]
                }
            },
            {
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": "Core deliverable execution"}}]
                }
            }
        ]
        notion.blocks.children.append(block_id=page_id, children=default_blocks)

def fetch_assets(domain_filter: Optional[str] = None, search_query: Optional[str] = None) -> List[AssetModel]:
    if not config.NOTION_ASSETS_DB_ID:
        return []

    filter_conditions = []
    if domain_filter and domain_filter not in ["Global", "All"]:
        filter_conditions.append(
            {"property": "Domain", "select": {"equals": domain_filter}}
        )

    query_payload = {"database_id": config.NOTION_ASSETS_DB_ID}
    if filter_conditions:
        query_payload["filter"] = filter_conditions[0]

    response = notion.databases.query(**query_payload)
    assets = [parse_asset_page(page) for page in response.get("results", [])]

    if search_query:
        query_lower = search_query.lower()
        assets = [
            a for a in assets 
            if query_lower in a.title.lower() or any(query_lower in t.lower() for t in a.tags)
        ]

    return assets