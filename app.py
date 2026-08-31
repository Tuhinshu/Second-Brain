import base64
import logging
import os
import re
from collections.abc import Callable

import streamlit as st

import streamlit as st

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        pwd = st.text_input("Enter Passcode to Access HUD:", type="password")
        if st.button("Authenticate"):
            if pwd == st.secrets.get("APP_PASSWORD", "my_secret_pass"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access Denied")
        return False
    return True

if not check_password():
    st.stop()


from Models import (
    InvalidStateTransitionError,
    NotionServiceError,
    TaskLimitError,
    TaskValidationError,
)
from notion_service import (
    create_new_task,
    delete_task,
    fetch_active_tasks,
    fetch_assets,
    start_task,
    update_task_status,
)
from scoring_engine import rank_tasks

logger = logging.getLogger("second_brain.app")
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def escape_markdown(text: str) -> str:
    """Escapes Markdown metacharacters in external text to prevent injection or formatting breaks."""
    if not text:
        return ""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|~<>])", r"\\\1", str(text))


def run_notion_action(
    action_fn: Callable[[], None],
    success_msg: str | None = None,
    error_prefix: str = "Operation failed",
) -> None:
    """Unified handler for executing Notion API mutations with error handling, cache clearing, and UI reruns."""
    try:
        action_fn()
        fetch_active_tasks.clear()
        if success_msg:
            st.toast(success_msg)
        st.rerun()
    except (TaskValidationError, InvalidStateTransitionError) as e:
        logger.warning("%s validation error: %s", error_prefix, str(e))
        st.warning(f"{error_prefix}: {str(e)}")
    except TaskLimitError as e:
        logger.warning("%s task limit error: %s", error_prefix, str(e))
        st.warning(f"⚠️ {str(e)}")
    except NotionServiceError as e:
        logger.error("%s Notion service error: %s", error_prefix, str(e))
        st.error(f"{error_prefix}. Please check your connection or try again.")
    except Exception as e:
        logger.exception("%s unexpected error: %s", error_prefix, str(e))
        st.error(f"{error_prefix}. Please check your connection or try again.")


@st.cache_data
def get_base64_of_bin_file(bin_file: str) -> str:
    """Reads and base64-encodes binary assets with caching."""
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


def apply_custom_styles() -> None:
    """Injects high-level container background and button styling into the application."""
    try:
        bg_page_b64 = get_base64_of_bin_file(os.path.join(CURRENT_DIR, "bg.jpg"))
        page_bg_css = (
            f"linear-gradient(135deg, rgba(255, 253, 247, 0.82) 0%, rgba(245, 239, 225, 0.86) 100%), "
            f"url('data:image/jpeg;base64,{bg_page_b64}')"
        )
    except Exception:
        page_bg_css = "linear-gradient(135deg, rgba(255, 253, 247, 0.95), rgba(245, 239, 225, 0.95))"

    st.markdown(
        f"""
        <style>
            .stApp {{
                background-image: {page_bg_css};
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}

            header {{
                background: transparent !important;
            }}

            .stButton > button {{
                padding: 0.25rem 0.6rem;
                font-size: 0.85rem;
                min-height: 2.2rem;
                border-radius: 6px;
                transition: all 0.2s ease-in-out;
            }}

            .stButton > button:hover {{
                opacity: 0.92;
                transform: translateY(-1px);
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero_banner() -> None:
    """Renders the top hero banner with cover image."""
    try:
        img_b64 = get_base64_of_bin_file(os.path.join(CURRENT_DIR, "Cover.jpg"))
        bg_style = (
            f"background: linear-gradient(rgba(0, 0, 0, 0.45), rgba(0, 0, 0, 0.55)), "
            f"url('data:image/jpeg;base64,{img_b64}') center/cover no-repeat;"
        )
    except Exception:
        bg_style = "background: #1e293b;"

    st.html(
        f"""
        <div style="
            {bg_style}
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 3.5rem 1.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            text-align: center;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
        ">
            <h1 style="
                margin: 0;
                color: #ffffff;
                font-size: 2.2rem;
                font-weight: 800;
                text-shadow: 0 3px 12px rgba(0, 0, 0, 0.8);
                text-align: center;
            ">Second Brain Execution Engine</h1>
        </div>
        """
    )


def render_add_task_form(key_suffix: str = "") -> None:
    """Reusable task capture form component."""
    default_domain_idx = 0
    valid_domains = ["AIESEC", "Academics", "Clients", "Personal"]
    if st.session_state.active_domain in valid_domains:
        default_domain_idx = valid_domains.index(st.session_state.active_domain)

    with st.form(f"quick_add_task_form{key_suffix}", clear_on_submit=True):
        new_task_name = st.text_input(
            "Task Title / Deliverable",
            placeholder="e.g., Draft AIESEC Q3 Strategy Document",
            key=f"name{key_suffix}",
        )

        col_f1, col_f2, col_f3 = st.columns(3)
        new_domain = col_f1.selectbox(
            "Domain", valid_domains, index=default_domain_idx, key=f"domain{key_suffix}"
        )
        new_hours = col_f2.number_input(
            "Estimated Hours",
            min_value=0.25,
            max_value=12.0,
            value=1.0,
            step=0.25,
            key=f"hours{key_suffix}",
        )
        new_waiting = col_f3.checkbox(
            "Someone waiting on this? (Blocker)", value=False, key=f"wait{key_suffix}"
        )

        col_f4, col_f5 = st.columns(2)
        new_impact = col_f4.slider(
            "Strategic Impact (1 = Low, 5 = High/Revenue)",
            min_value=1,
            max_value=5,
            value=3,
            key=f"imp{key_suffix}",
        )
        new_urgency = col_f5.slider(
            "Urgency / Deadline (1 = Later, 5 = Immediate)",
            min_value=1,
            max_value=5,
            value=3,
            key=f"urg{key_suffix}",
        )

        submitted = st.form_submit_button(
            "Add Task to Second Brain", use_container_width=True, type="primary"
        )

        if submitted:
            try:
                task = create_new_task(
                    task_name=new_task_name,
                    domain=new_domain,
                    impact=new_impact,
                    urgency=new_urgency,
                    estimated_hours=new_hours,
                    someone_waiting=new_waiting,
                )
                st.success(f"Task '{task.task_name}' successfully added to Notion!")
                st.rerun()
            except TaskValidationError as e:
                st.warning(str(e))
            except TaskLimitError as e:
                st.warning(f"⚠️ {str(e)}")
            except NotionServiceError:
                st.error("Failed to create task in Notion. Please check your connection or try again.")
            except Exception as e:
                logger.exception("Unexpected error creating task: %s", str(e))
                st.error("An unexpected error occurred while adding the task.")


@st.dialog("Quick Task Capture")
def add_task_dialog() -> None:
    render_add_task_form(key_suffix="_dialog")


@st.dialog("Confirm Task Deletion")
def confirm_delete_dialog(task_id: str, task_name: str) -> None:
    """Confirmation modal for destructive delete/archive actions."""
    st.write(f"Are you sure you want to archive/delete **{escape_markdown(task_name)}** from Notion?")
    st.caption("This action will remove the task from your active queue.")
    c_yes, c_no = st.columns(2)
    if c_yes.button("Yes, Delete", type="primary", use_container_width=True):
        run_notion_action(
            lambda: delete_task(task_id),
            f"Deleted: {task_name}",
            "Failed to delete task",
        )
    if c_no.button("Cancel", use_container_width=True):
        st.rerun()


def render_navigation() -> None:
    """Renders page tabs, domain selector, and quick add action."""
    page_cols = st.columns(3)
    pages = ["24-Hour Execution Arena", "Reusable Asset Vault", "Quick Task Capture"]

    for idx, page in enumerate(pages):
        if page_cols[idx].button(
            page,
            use_container_width=True,
            type="primary" if st.session_state.active_page == page else "secondary",
        ):
            st.session_state.active_page = page
            st.rerun()

    st.divider()

    cols = st.columns(5)
    domains = [
        ("Global HUD", "Global"),
        ("AIESEC", "AIESEC"),
        ("Academics", "Academics"),
        ("Clients", "Clients"),
        ("Personal", "Personal"),
    ]

    for idx, (label, domain_key) in enumerate(domains):
        is_active = st.session_state.active_domain == domain_key
        if cols[idx].button(
            label,
            key=f"nav_btn_{domain_key}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.active_domain = domain_key
            st.rerun()

    st.caption(f"Current Execution Filter: **{st.session_state.active_domain}**")

    _, c_add = st.columns([8, 2])
    with c_add:
        if st.button("➕ Add Task", use_container_width=True, type="primary"):
            add_task_dialog()

    st.divider()


def render_state_anchor_modal() -> None:
    """Renders the state anchor capture card when pausing a task."""
    if not st.session_state.pause_prompt_id:
        return

    with st.container(border=True):
        st.subheader("Save State Anchor")
        st.info("What is the exact next 15-minute physical action to take when resuming?")
        anchor_text = st.text_input("State Anchor Note", key="anchor_input")
        c1, c2 = st.columns([1, 4])
        if c1.button("Save & Pause", type="primary"):
            if anchor_text.strip():

                def _pause_action():
                    update_task_status(
                        st.session_state.pause_prompt_id,
                        "Paused",
                        state_anchor=anchor_text.strip(),
                        current_status="In progress",
                    )
                    st.session_state.pause_prompt_id = None

                run_notion_action(
                    _pause_action,
                    "State anchor recorded & task paused!",
                    "Failed to pause task",
                )
            else:
                st.warning("Please provide a brief anchor note before pausing.")
        if c2.button("Cancel"):
            st.session_state.pause_prompt_id = None
            st.rerun()


def render_execution_arena() -> None:
    """Renders the 24-Hour Execution Arena with Top 3 priority tasks and Backlog Drawer."""
    try:
        raw_tasks = fetch_active_tasks(st.session_state.active_domain)
        ranked_tasks = rank_tasks(raw_tasks)
    except Exception as e:
        logger.exception("Error fetching active tasks from Notion: %s", str(e))
        st.error("Error fetching tasks from Notion. Please check your connection or try again.")
        ranked_tasks = []

    if not ranked_tasks:
        st.success("No active tasks in this view. Add a task or switch focus modes!")
        return

    top_3_tasks = ranked_tasks[:3]
    backlog_tasks = ranked_tasks[3:]

    render_state_anchor_modal()

    st.subheader("24-Hour Execution Priority")
    for idx, task in enumerate(top_3_tasks):
        is_active = task.status == "In progress"
        card_border = is_active or (idx == 0)

        with st.container(border=card_border):
            c_info, c_actions = st.columns([1.6, 1.4])

            with c_info:
                status_badge = f"**[{task.status.upper()}]**" if is_active else f"[{task.status}]"
                st.markdown(f"### {idx + 1}. {escape_markdown(task.task_name)}")
                st.markdown(
                    f"{status_badge} `{escape_markdown(task.domain)}` | "
                    f"**Score:** `{task.priority_score}` | "
                    f"**Est:** `{task.estimated_hours}h` | "
                    f"**Blocker:** `{'YES' if task.someone_waiting else 'NO'}`"
                )
                if task.state_anchor:
                    st.info(f"State Anchor: {escape_markdown(task.state_anchor)}")

            with c_actions:
                st.write("")
                col_b1, col_b2, col_b3 = st.columns([1.1, 1.2, 0.9])
                if task.status != "In progress":
                    btn_label = "Resume" if task.status == "Paused" else "Start"
                    toast_label = "Resumed" if task.status == "Paused" else "Started"
                    if col_b1.button(btn_label, key=f"start_{task.id}", use_container_width=True):

                        def _start_action(t_id=task.id, t_status=task.status):
                            start_task(t_id, current_status=t_status)

                        run_notion_action(
                            _start_action,
                            f"{toast_label}: {task.task_name}",
                            "Failed to start task",
                        )
                else:
                    if col_b1.button("Pause", key=f"pause_{task.id}", use_container_width=True):
                        st.session_state.pause_prompt_id = task.id
                        st.rerun()

                if col_b2.button(
                    "Complete",
                    key=f"done_{task.id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    run_notion_action(
                        lambda t_id=task.id, t_status=task.status: update_task_status(
                            t_id, "Done", current_status=t_status
                        ),
                        f"Completed: {task.task_name}",
                        "Failed to complete task",
                    )

                if col_b3.button("🗑️ Delete", key=f"del_{task.id}", use_container_width=True):
                    confirm_delete_dialog(task.id, task.task_name)

    if backlog_tasks:
        st.write("")
        with st.expander(f"Backlog Drawer ({len(backlog_tasks)} Remaining Tasks)"):
            for b_task in backlog_tasks:
                b_col1, b_col2, b_col3 = st.columns([4, 1.2, 0.9])
                with b_col1:
                    st.markdown(
                        f"• **{escape_markdown(b_task.task_name)}** (`{escape_markdown(b_task.domain)}`) — "
                        f"Score: `{b_task.priority_score}` | Est: `{b_task.estimated_hours}h`"
                    )
                with b_col2:
                    if st.button("Promote", key=f"promote_{b_task.id}", use_container_width=True):
                        run_notion_action(
                            lambda bt_id=b_task.id, bt_status=b_task.status: update_task_status(
                                bt_id, "Not started", current_status=bt_status
                            ),
                            f"Promoted {b_task.task_name} to active queue!",
                            "Failed to promote task",
                        )
                with b_col3:
                    if st.button("🗑️ Delete", key=f"del_{b_task.id}", use_container_width=True):
                        confirm_delete_dialog(b_task.id, b_task.task_name)


def render_asset_vault() -> None:
    """Renders the Reusable Asset Vault page."""
    st.subheader("Resources")
    col_q, col_d = st.columns([3, 1])
    search_q = col_q.text_input("Search snippets, templates, or docs...", "")
    vault_domain = col_d.selectbox(
        "Filter Domain",
        ["All", "AIESEC", "Academics", "Clients", "Personal", "General"],
    )
    try:
        assets = fetch_assets(domain_filter=vault_domain, search_query=search_q)
        if not assets:
            st.info("No assets found matching the filter criteria.")
        else:
            for asset in assets:
                with st.container(border=True):
                    a_info, a_link = st.columns([4, 1])
                    with a_info:
                        st.markdown(
                            f"**{escape_markdown(asset.title)}**  `{escape_markdown(asset.type)}` `{escape_markdown(asset.domain)}`"
                        )
                        if asset.tags:
                            escaped_tags = ", ".join(escape_markdown(t) for t in asset.tags)
                            st.caption(f"Tags: {escaped_tags}")
                    with a_link:
                        if asset.url:
                            st.link_button("Open Resources", asset.url, use_container_width=True)
                        else:
                            st.caption("No URL attached")
    except Exception as e:
        logger.exception("Error querying Asset Vault from Notion: %s", str(e))
        st.error("Error querying Asset Vault. Please check your connection or try again.")


def render_quick_task_page() -> None:
    """Renders the full-page Quick Task Capture tab."""
    st.markdown(
        "<h2 style='text-align: center; color: #1C1917; margin-bottom: 1.25rem;'>Add Task</h2>",
        unsafe_allow_html=True,
    )
    _, col_form_center, _ = st.columns([1, 6, 1])
    with col_form_center:
        render_add_task_form(key_suffix="_tab")


def main() -> None:
    st.set_page_config(
        page_title="Second Brain Execution Engine",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    if "active_domain" not in st.session_state:
        st.session_state.active_domain = "Global"
    if "pause_prompt_id" not in st.session_state:
        st.session_state.pause_prompt_id = None
    if "active_page" not in st.session_state:
        st.session_state.active_page = "24-Hour Execution Arena"

    apply_custom_styles()
    render_hero_banner()
    render_navigation()

    if st.session_state.active_page == "24-Hour Execution Arena":
        render_execution_arena()
    elif st.session_state.active_page == "Reusable Asset Vault":
        render_asset_vault()
    elif st.session_state.active_page == "Quick Task Capture":
        render_quick_task_page()


if __name__ == "__main__":
    main()
