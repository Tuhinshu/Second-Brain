import logging
import random
import threading
import time
from typing import Any, Callable, List, Optional, TypeVar

import streamlit as st
from notion_client import Client
from notion_client.errors import APIResponseError, RequestTimeoutError

import config
from Models import (
    AssetModel,
    InvalidStateTransitionError,
    NotionServiceError,
    TaskDomain,
    TaskLimitError,
    TaskModel,
    TaskStatus,
    TaskValidationError,
    VALID_STATE_TRANSITIONS,
)

logger = logging.getLogger("second_brain.service")

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
    page_id = str(page.get("id", ""))
    props = page.get("properties", {})
    if not isinstance(props, dict):
        props = {}

    task_name = _extract_plain_text(props.get("Task Name"), key="title")
    if not task_name:
        logger.warning("Task page %s is missing title property; defaulting to 'Untitled Task'.", page_id)
        task_name = "Untitled Task"

    status_prop = props.get("Status")
    status_obj = None
    if isinstance(status_prop, dict):
        status_obj = status_prop.get("status") or status_prop.get("select")
    raw_status = status_obj.get("name") if isinstance(status_obj, dict) else None
    if raw_status in VALID_STATUSES:
        status: TaskStatus = raw_status
    else:
        logger.warning(
            "Task page %s ('%s') has invalid or missing status '%s'; defaulting to 'Not started'.",
            page_id,
            task_name,
            raw_status,
        )
        status = "Not started"

    domain_prop = props.get("Domain")
    domain_obj = domain_prop.get("select") if isinstance(domain_prop, dict) else None
    raw_domain = domain_obj.get("name") if isinstance(domain_obj, dict) else None
    if raw_domain in VALID_DOMAINS:
        domain: TaskDomain = raw_domain
    else:
        logger.warning(
            "Task page %s ('%s') has invalid or missing domain '%s'; defaulting to 'Personal'.",
            page_id,
            task_name,
            raw_domain,
        )
        domain = "Personal"

    impact = _parse_int_prop(props.get("Impact"), default=3, min_val=1, max_val=5)
    urgency = _parse_int_prop(props.get("Urgency"), default=3, min_val=1, max_val=5)
    estimated_hours = _parse_float_prop(props.get("Estimated Hours"), default=1.0, min_val=0.25, max_val=12.0)

    waiting_prop = props.get("Someone Waiting?")
    someone_waiting = bool(waiting_prop.get("checkbox", False)) if isinstance(waiting_prop, dict) else False

    state_anchor_text = _extract_plain_text(props.get("State Anchor"), key="rich_text")
    state_anchor = state_anchor_text if state_anchor_text else None

    return TaskModel(
        id=page_id,
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
    page_id = str(page.get("id", ""))
    props = page.get("properties", {})
    if not isinstance(props, dict):
        props = {}

    title = _extract_plain_text(props.get("Title"), key="title")
    if not title:
        logger.warning("Asset page %s is missing title property; defaulting to 'Untitled Asset'.", page_id)
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


class TaskCapacityCoordinator:
    """
    Backend concurrency coordinator implementing thread-safe synchronization
    and atomic task reservation to eliminate read-then-create race conditions
    across concurrent sessions.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def reserve_and_create(
        self,
        create_fn: Callable[[], TaskModel],
        count_fn: Callable[[], int],
        max_limit: int,
    ) -> TaskModel:
        """
        Acquires mutual exclusion lock, checks active task count atomically,
        and creates the task if capacity is available.
        """
        with self._lock:
            current_count = count_fn()
            if current_count >= max_limit:
                raise TaskLimitError(
                    f"Active task limit reached ({max_limit} tasks). "
                    "Please complete or delete existing tasks before adding a new one."
                )
            return create_fn()


capacity_coordinator = TaskCapacityCoordinator()


def create_new_task(
    task_name: str,
    domain: TaskDomain,
    impact: int = 3,
    urgency: int = 3,
    estimated_hours: float = 1.0,
    someone_waiting: bool = False,
) -> TaskModel:
    """
    Validates business rules and executes task creation in Notion using
    a backend-controlled atomic counter strategy.

    Concurrency Control:
        Uses TaskCapacityCoordinator to serialize concurrent session requests,
        eliminating read-then-create race conditions.

    Raises:
        TaskValidationError: If task title is empty.
        TaskLimitError: If active task capacity is reached.
        NotionServiceError: If Notion API persistence fails.

    Returns:
        TaskModel: The created and initialized task model.
    """
    clean_name = (task_name or "").strip()
    if not clean_name:
        raise TaskValidationError("Please provide a task title.")

    def _count() -> int:
        active_tasks = fetch_active_tasks("Global")
        return len(active_tasks)

    def _create() -> TaskModel:
        task_payload = TaskModel(
            task_name=clean_name,
            domain=domain,
            status="Not started",
            impact=impact,
            urgency=urgency,
            estimated_hours=estimated_hours,
            someone_waiting=someone_waiting,
        )
        page_id = create_task(task_payload)
        task_payload.id = page_id
        fetch_active_tasks.clear()
        return task_payload

    try:
        return capacity_coordinator.reserve_and_create(
            create_fn=_create,
            count_fn=_count,
            max_limit=config.MAX_ACTIVE_TASKS,
        )
    except (TaskValidationError, TaskLimitError):
        raise
    except Exception as e:
        logger.exception(
            "Unexpected error while creating task '%s' in Notion: %s", clean_name, str(e)
        )
        raise NotionServiceError(f"Failed to create task '{clean_name}' in Notion.") from e


def validate_state_transition(current_status: TaskStatus, new_status: TaskStatus) -> bool:
    """Validates whether transitioning from current_status to new_status is allowed."""
    allowed = VALID_STATE_TRANSITIONS.get(current_status, set())
    return new_status in allowed


def update_task_status(
    page_id: str,
    new_status: TaskStatus,
    state_anchor: Optional[str] = None,
    current_status: Optional[TaskStatus] = None,
) -> None:
    """
    Updates the status and optional state anchor of a Notion task page,
    enforcing VALID_STATE_TRANSITIONS rules before persisting.

    Raises:
        InvalidStateTransitionError: If the transition is illegal.
        NotionServiceError: If the Notion update API call fails.
    """
    if current_status is None:
        try:
            page = execute_with_retry(lambda: notion.pages.retrieve(page_id=page_id))
            status_prop = page.get("properties", {}).get("Status", {})
            status_obj = status_prop.get("status") or status_prop.get("select") or {}
            raw_status = status_obj.get("name") if isinstance(status_obj, dict) else None
            current_status = raw_status if raw_status in VALID_STATUSES else "Not started"
        except Exception as e:
            logger.exception("Failed to retrieve task %s from Notion: %s", page_id, str(e))
            raise NotionServiceError(f"Failed to retrieve task {page_id} from Notion.") from e

    if not validate_state_transition(current_status, new_status):
        allowed = VALID_STATE_TRANSITIONS.get(current_status, set())
        raise InvalidStateTransitionError(
            f"Invalid task state transition from '{current_status}' to '{new_status}'. "
            f"Allowed transitions: {sorted(allowed)}"
        )

    properties = {
        "Status": {"status": {"name": new_status}}
    }

    if state_anchor is not None:
        properties["State Anchor"] = {
            "rich_text": [{"text": {"content": state_anchor}}]
        }

    try:
        execute_with_retry(lambda: notion.pages.update(page_id=page_id, properties=properties))
    except Exception as e:
        logger.exception("Failed to update status for task %s in Notion: %s", page_id, str(e))
        raise NotionServiceError(f"Failed to update task status in Notion.") from e


def delete_task(page_id: str) -> None:
    """Archive/delete a task page in Notion."""
    try:
        execute_with_retry(lambda: notion.pages.update(page_id=page_id, archived=True))
    except Exception as e:
        logger.exception("Failed to delete task %s in Notion: %s", page_id, str(e))
        raise NotionServiceError(f"Failed to delete task in Notion.") from e


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


def start_task(
    page_id: str,
    current_status: Optional[TaskStatus] = None,
    inject_template: bool = True,
    max_template_retries: int = 3,
) -> None:
    """
    Transitions a task to 'In progress' and conditionally injects execution template blocks.

    Resilience & Compensating Rollback:
        If template injection fails, it retries up to `max_template_retries` with exponential
        backoff. If all attempts fail, it executes a compensating rollback on the task status
        (restoring it to its original status, e.g. 'Not started') and raises NotionServiceError
        so the task is never left orphaned in 'In progress' without its checklist template.

    Performance & Network Optimization:
        If current_status is 'Paused', template block inspection is bypassed to eliminate
        redundant Notion API network roundtrips, since paused tasks have already been
        initialized with checklist content.
    """
    update_task_status(page_id, "In progress", current_status=current_status)

    if current_status != "Paused" and inject_template:
        template_injected = False
        template_error: Optional[Exception] = None

        for attempt in range(1, max_template_retries + 1):
            try:
                inject_template_blocks_if_empty(page_id)
                template_injected = True
                break
            except Exception as exc:
                template_error = exc
                logger.warning(
                    "Template injection attempt %d/%d failed for task %s: %s",
                    attempt,
                    max_template_retries,
                    page_id,
                    str(exc),
                )
                if attempt < max_template_retries:
                    time.sleep(0.25 * (2 ** (attempt - 1)))

        if not template_injected and template_error is not None:
            rollback_status: TaskStatus = (
                current_status
                if current_status and current_status in VALID_STATUSES and current_status != "In progress"
                else "Not started"
            )
            logger.error(
                "Template injection failed after %d attempts for task %s. Rolling back status to '%s'.",
                max_template_retries,
                page_id,
                rollback_status,
            )
            try:
                update_task_status(page_id, rollback_status, current_status="In progress")
            except Exception as rollback_err:
                logger.critical(
                    "Compensating rollback failed for task %s: %s",
                    page_id,
                    str(rollback_err),
                )

            raise NotionServiceError(
                f"Failed to initialize checklist template for task. "
                f"Status was safely rolled back to '{rollback_status}'."
            ) from template_error


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