import time
import random
from typing import List, Optional, Callable, TypeVar, Any
import streamlit as st
from notion_client import Client
from notion_client.errors import APIResponseError, RequestTimeoutError, HTTPResponseError
import config
from Models import TaskModel, AssetModel, TaskStatus, TaskDomain

T = TypeVar("T")
RETRYABLE_STATUS_CODES: set[int] = {429, 500, 502, 503, 504}

notion = Client(auth=config.NOTION_API_KEY)

def execute_with_retry(
    operation: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 4.0
) -> T:
    """
    Executes a Notion API call with bounded exponential backoff and jitter
    for transient HTTP and rate-limit errors (429, 5xx, timeouts).
    """
    attempt = 0
    while True:
        try:
            return operation()
        except APIResponseError as err:
            status = getattr(err, "status", None)
            if status not in RETRYABLE_STATUS_CODES or attempt >= max_retries:
                raise
            attempt += 1
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.1))
            time.sleep(delay)
        except (RequestTimeoutError, ConnectionError, TimeoutError):
            if attempt >= max_retries:
                raise
            attempt += 1
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.1))
            time.sleep(delay)
        except Exception as err:
            status = getattr(err, "status", getattr(err, "status_code", None))
            if status in RETRYABLE_STATUS_CODES and attempt < max_retries:
                attempt += 1
                delay = min(max_delay, base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.1))
                time.sleep(delay)
            else:
                raise


VALID_STATUSES: set[str] = {"Backlog", "Not started", "In progress", "Paused", "Done"}
VALID_DOMAINS: set[str] = {"AIESEC", "Academics", "Clients", "Personal"}

def _extract_plain_text(prop: Optional[dict], key: str = "title") -> str:
    if not isinstance(prop, dict):
        return ""
    items = prop.get(key)
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict):
            return str(first.get("plain_text", "")).strip()
    return ""

def _parse_int_prop(prop: Optional[dict], default: int = 3, min_val: int = 1, max_val: int = 5) -> int:
    """Explicitly extracts and bounds an integer property, checking `is None` rather than relying on truthiness."""
    if not isinstance(prop, dict):
        return default
    val = prop.get("number")
    if val is None:
        return default
    try:
        num = int(val)
        return max(min_val, min(max_val, num))
    except (ValueError, TypeError):
        return default

def _parse_float_prop(prop: Optional[dict], default: float = 1.0, min_val: float = 0.25, max_val: float = 12.0) -> float:
    """Explicitly extracts and bounds a float property, checking `is None` rather than relying on truthiness."""
    if not isinstance(prop, dict):
        return default
    val = prop.get("number")
    if val is None:
        return default
    try:
        num = float(val)
        return max(min_val, min(max_val, num))
    except (ValueError, TypeError):
        return default

def parse_task_page(page: dict) -> TaskModel:
    if not isinstance(page, dict):
        page = {}
    props = page.get("properties", {})
    if not isinstance(props, dict):
        props = {}

    task_name = _extract_plain_text(props.get("Task Name"), key="title")
    if not task_name:
        task_name = "Untitled Task"

    status_prop = props.get("Status")
    status_obj = None
    if isinstance(status_prop, dict):
        status_obj = status_prop.get("status") or status_prop.get("select")
    raw_status = status_obj.get("name") if isinstance(status_obj, dict) else None
    status: TaskStatus = raw_status if raw_status in VALID_STATUSES else "Not started"

    domain_prop = props.get("Domain")
    domain_obj = domain_prop.get("select") if isinstance(domain_prop, dict) else None
    raw_domain = domain_obj.get("name") if isinstance(domain_obj, dict) else None
    domain: TaskDomain = raw_domain if raw_domain in VALID_DOMAINS else "Personal"

    impact = _parse_int_prop(props.get("Impact"), default=3, min_val=1, max_val=5)
    urgency = _parse_int_prop(props.get("Urgency"), default=3, min_val=1, max_val=5)
    estimated_hours = _parse_float_prop(props.get("Estimated Hours"), default=1.0, min_val=0.25, max_val=12.0)

    waiting_prop = props.get("Someone Waiting?")
    someone_waiting = bool(waiting_prop.get("checkbox", False)) if isinstance(waiting_prop, dict) else False

    state_anchor_text = _extract_plain_text(props.get("State Anchor"), key="rich_text")
    state_anchor = state_anchor_text if state_anchor_text else None

    return TaskModel(
        id=str(page.get("id", "")),
        task_name=task_name,
        status=status,
        domain=domain,
        impact=impact,
        urgency=urgency,
        estimated_hours=estimated_hours,
        someone_waiting=someone_waiting,
        state_anchor=state_anchor
    )

def parse_asset_page(page: dict) -> AssetModel:
    if not isinstance(page, dict):
        page = {}
    props = page.get("properties", {})
    if not isinstance(props, dict):
        props = {}

    title = _extract_plain_text(props.get("Title"), key="title")
    if not title:
        title = "Untitled Asset"

    type_prop = props.get("Type")
    type_obj = type_prop.get("select") if isinstance(type_prop, dict) else None
    asset_type = type_obj.get("name", "Doc/Guide") if isinstance(type_obj, dict) else "Doc/Guide"

    domain_prop = props.get("Domain")
    domain_obj = domain_prop.get("select") if isinstance(domain_prop, dict) else None
    domain = domain_obj.get("name", "General") if isinstance(domain_obj, dict) else "General"

    url_prop = props.get("URL")
    custom_url = url_prop.get("url") if isinstance(url_prop, dict) else None
    url = custom_url if custom_url else page.get("url")

    tags_prop = props.get("Tags")
    tags_list = tags_prop.get("multi_select", []) if isinstance(tags_prop, dict) else []
    tags = [t.get("name", "") for t in tags_list if isinstance(t, dict) and t.get("name")]

    return AssetModel(
        id=str(page.get("id", "")),
        title=title,
        type=asset_type,
        domain=domain,
        url=url,
        tags=tags
    )

@st.cache_data(ttl=60)
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

    response = execute_with_retry(lambda: notion.databases.query(**query_payload))
    return [parse_task_page(page) for page in response.get("results", [])]


def create_task(task: TaskModel) -> str:
    """Creates a new task page in the Notion Tasks database with exponential backoff retry."""
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

    response = execute_with_retry(
        lambda: notion.pages.create(
            parent={"database_id": config.NOTION_TASKS_DB_ID},
            properties=properties
        )
    )
    return response["id"]


def create_new_task(
    task_name: str,
    domain: TaskDomain,
    impact: int = 3,
    urgency: int = 3,
    estimated_hours: float = 1.0,
    someone_waiting: bool = False,
) -> tuple[bool, str]:
    """
    Validates business rules and executes task creation in Notion.
    Returns (success: bool, message: str).
    """
    clean_name = (task_name or "").strip()
    if not clean_name:
        return False, "Please provide a task title."

    try:
        active_tasks = fetch_active_tasks("Global")
        if len(active_tasks) >= config.MAX_ACTIVE_TASKS:
            return False, f"⚠️ Active task limit reached ({config.MAX_ACTIVE_TASKS} tasks). Please complete or delete existing tasks before adding a new one."

        task_payload = TaskModel(
            task_name=clean_name,
            domain=domain,
            status="Not started",
            impact=impact,
            urgency=urgency,
            estimated_hours=estimated_hours,
            someone_waiting=someone_waiting,
        )
        create_task(task_payload)
        fetch_active_tasks.clear()
        return True, f"Task '{clean_name}' successfully added to Notion!"
    except Exception as e:
        return False, f"Failed to create task in Notion: {str(e)}"



def update_task_status(page_id: str, new_status: TaskStatus, state_anchor: Optional[str] = None) -> None:
    properties = {
        "Status": {"status": {"name": new_status}}
    }

    if state_anchor is not None:
        properties["State Anchor"] = {
            "rich_text": [{"text": {"content": state_anchor}}]
        }

    execute_with_retry(lambda: notion.pages.update(page_id=page_id, properties=properties))


def delete_task(page_id: str) -> None:
    """Archive/delete a task page in Notion."""
    execute_with_retry(lambda: notion.pages.update(page_id=page_id, archived=True))


TEMPLATE_MARKER_HEADING = "Execution Scope & Checklist"

def inject_template_blocks_if_empty(page_id: str) -> bool:
    """
    Idempotently injects execution checklist template blocks into a task page.
    Checks for existing content and the marker heading before inserting to prevent duplicates.
    Returns True if template blocks were injected, False otherwise.
    """
    response = execute_with_retry(lambda: notion.blocks.children.list(block_id=page_id))
    existing_blocks = response.get("results", [])

    # If any block already contains the template marker, skip injection
    for block in existing_blocks:
        b_type = block.get("type", "")
        if b_type == "heading_2":
            heading_text = _extract_plain_text(block.get("heading_2"), key="rich_text")
            if TEMPLATE_MARKER_HEADING.lower() in heading_text.lower():
                return False

    if not existing_blocks:
        default_blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": TEMPLATE_MARKER_HEADING}}]
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
        execute_with_retry(lambda: notion.blocks.children.append(block_id=page_id, children=default_blocks))
        return True

    return False

@st.cache_data(ttl=60)
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

    response = execute_with_retry(lambda: notion.databases.query(**query_payload))
    assets = [parse_asset_page(page) for page in response.get("results", [])]

    if search_query:
        query_lower = search_query.lower()
        assets = [
            a for a in assets 
            if query_lower in a.title.lower() or any(query_lower in t.lower() for t in a.tags)
        ]

    return assets