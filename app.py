import streamlit as st
import base64
import os
import re
from typing import Optional, Callable
import config
from Models import TaskModel
from scoring_engine import rank_tasks
from notion_service import (
    fetch_active_tasks,
    create_task,
    update_task_status,
    delete_task,
    inject_template_blocks_if_empty,
    fetch_assets,
)

def escape_markdown(text: str) -> str:
    """Escapes Markdown metacharacters in external text to prevent injection or formatting breaks."""
    if not text:
        return ""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|~<>])", r"\\\1", str(text))


def run_notion_action(
    action_fn: Callable[[], None],
    success_msg: Optional[str] = None,
    error_prefix: str = "Operation failed"
) -> bool:
    """Unified handler for executing Notion API mutations with error handling, cache clearing, and UI updates."""
    try:
        action_fn()
        fetch_active_tasks.clear()
        if success_msg:
            st.toast(success_msg)
        st.rerun()
        return True
    except Exception as e:
        st.error(f"{error_prefix}: {str(e)}")
        return False




st.set_page_config(
    page_title="Second Brain Execution Engine",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "active_domain" not in st.session_state:
    st.session_state.active_domain = "Global"
if "pause_prompt_id" not in st.session_state:
    st.session_state.pause_prompt_id = None

def render_add_task_form(key_suffix=""):
    default_domain_idx = 0
    valid_domains = ["AIESEC", "Academics", "Clients", "Personal"]
    if st.session_state.active_domain in valid_domains:
        default_domain_idx = valid_domains.index(st.session_state.active_domain)

    with st.form(f"quick_add_task_form{key_suffix}", clear_on_submit=True):
        new_task_name = st.text_input("Task Title / Deliverable", placeholder="e.g., Draft AIESEC Q3 Strategy Document", key=f"name{key_suffix}")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        new_domain = col_f1.selectbox("Domain", valid_domains, index=default_domain_idx, key=f"domain{key_suffix}")
        new_hours = col_f2.number_input("Estimated Hours", min_value=0.25, max_value=12.0, value=1.0, step=0.25, key=f"hours{key_suffix}")
        new_waiting = col_f3.checkbox("Someone waiting on this? (Blocker)", value=False, key=f"wait{key_suffix}")

        col_f4, col_f5 = st.columns(2)
        new_impact = col_f4.slider("Strategic Impact (1 = Low, 5 = High/Revenue)", min_value=1, max_value=5, value=3, key=f"imp{key_suffix}")
        new_urgency = col_f5.slider("Urgency / Deadline (1 = Later, 5 = Immediate)", min_value=1, max_value=5, value=3, key=f"urg{key_suffix}")

        submitted = st.form_submit_button("Add Task to Second Brain", use_container_width=True, type="primary")

        if submitted:
            if not new_task_name.strip():
                st.warning("Please provide a task title.")
            else:
                try:
                    active_tasks = fetch_active_tasks("Global")
                    if len(active_tasks) >= config.MAX_ACTIVE_TASKS:
                        st.warning(
                            f"⚠️ Active task limit reached ({config.MAX_ACTIVE_TASKS} tasks). "
                            "Please complete or delete existing tasks before adding a new one."
                        )
                    else:
                        task_payload = TaskModel(
                            task_name=new_task_name.strip(),
                            domain=new_domain,
                            status="Not started",
                            impact=new_impact,
                            urgency=new_urgency,
                            estimated_hours=new_hours,
                            someone_waiting=new_waiting
                        )
                        create_task(task_payload)
                        fetch_active_tasks.clear()
                        st.success(f"Task '{new_task_name}' successfully added to Notion!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to create task in Notion: {str(e)}")

@st.dialog("Quick Task Capture")
def add_task_dialog():
    render_add_task_form(key_suffix="_dialog")


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def get_base64_of_bin_file(bin_file: str) -> str:
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


try:
    img_b64 = get_base64_of_bin_file(os.path.join(CURRENT_DIR, "Cover.jpg"))
    bg_style = f"background: linear-gradient(rgba(0, 0, 0, 0.45), rgba(0, 0, 0, 0.55)), url('data:image/jpeg;base64,{img_b64}') center/cover no-repeat;"
except Exception:
    bg_style = "background: #1e293b;"

try:
    bg_page_b64 = get_base64_of_bin_file(os.path.join(CURRENT_DIR, "bg.jpg"))
    page_bg_css = f"linear-gradient(135deg, rgba(255, 253, 247, 0.82) 0%, rgba(245, 239, 225, 0.86) 100%), url('data:image/jpeg;base64,{bg_page_b64}')"
except Exception:
    page_bg_css = "linear-gradient(135deg, rgba(255, 253, 247, 0.95), rgba(245, 239, 225, 0.95))"

st.html(f"""
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
""")

st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{
        background-image: {page_bg_css} !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }}

    [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    div.stButton > button {{
        padding: 0.25rem 0.5rem !important;
        font-size: 0.85rem !important;
        min-height: 2.2rem !important;
        height: auto !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out !important;
    }}

    div.stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button,
    button[kind="primary"],
    button[data-testid="baseButton-primary"] {{
        background-color: #B45309 !important;
        border-color: #B45309 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }}

    div.stButton > button[kind="secondary"],
    button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {{
        background-color: #F5EFE1 !important;
        border-color: #F5EFE1 !important;
        color: #1C1917 !important;
        font-weight: 500 !important;
    }}

    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {{
        opacity: 0.9 !important;
        transform: translateY(-1px) !important;
    }}

    div[data-baseweb="slider"] [role="slider"] {{
        background-color: #B45309 !important;
        border-color: #B45309 !important;
        box-shadow: 0 0 0 3px rgba(180, 83, 9, 0.2) !important;
    }}
    div[data-baseweb="slider"] > div > div:first-child {{
        background: #B45309 !important;
    }}
    div[data-testid="stSlider"] div[data-testid="stThumbValue"] {{
        color: #B45309 !important;
        font-weight: 700 !important;
    }}

    div[data-testid="stCheckbox"] input:checked + div,
    div[data-testid="stCheckbox"] [aria-checked="true"] {{
        background-color: #B45309 !important;
        border-color: #B45309 !important;
    }}

    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"] > div:focus-within {{
        border-color: #B45309 !important;
    }}
</style>
""", unsafe_allow_html=True)

if "active_page" not in st.session_state:
    st.session_state.active_page = "24-Hour Execution Arena"

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
    is_active = (st.session_state.active_domain == domain_key)
    
    if cols[idx].button(
        label,
        key=f"nav_btn_{domain_key}",
        use_container_width=True,
        type="primary" if is_active else "secondary"
    ):
        st.session_state.active_domain = domain_key
        st.rerun()

st.caption(f"Current Execution Filter: **{st.session_state.active_domain}**")

c_empty, c_add = st.columns([8, 2])
with c_add:
    if st.button("➕ Add Task", use_container_width=True, type="primary"):
        add_task_dialog()

st.divider()

if st.session_state.active_page == "24-Hour Execution Arena":
    try:
        raw_tasks = fetch_active_tasks(st.session_state.active_domain)
        ranked_tasks = rank_tasks(raw_tasks)
    except Exception as e:
        st.error(f"Error fetching tasks from Notion: {str(e)}")
        ranked_tasks = []

    if not ranked_tasks:
        st.success("No active tasks in this view. Add a task or switch focus modes!")
    else:
        top_3_tasks = ranked_tasks[:3]
        backlog_tasks = ranked_tasks[3:]
        
        if st.session_state.pause_prompt_id:
            with st.container(border=True):
                st.subheader("Save State Anchor")
                st.info("What is the exact next 15-minute physical action to take when resuming?")
                anchor_text = st.text_input("State Anchor Note", key="anchor_input")
                c1, c2 = st.columns([1, 4])
                if c1.button("Save & Pause", type="primary"):
                    if anchor_text.strip():
                        def _pause_action():
                            update_task_status(st.session_state.pause_prompt_id, "Not started", state_anchor=anchor_text.strip())
                            st.session_state.pause_prompt_id = None
                        run_notion_action(_pause_action, "State anchor recorded & task paused!", "Failed to pause task")
                    else:
                        st.warning("Please provide a brief anchor note before pausing.")
                if c2.button("Cancel"):
                    st.session_state.pause_prompt_id = None
                    st.rerun()

        st.subheader("24-Hour Execution Priority")        
        for idx, task in enumerate(top_3_tasks):
            is_active = (task.status == "In progress")
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
                        if col_b1.button("Start", key=f"start_{task.id}", use_container_width=True):
                            def _start_action(t_id=task.id):
                                update_task_status(t_id, "In progress")
                                inject_template_blocks_if_empty(t_id)
                            run_notion_action(_start_action, f"Started: {task.task_name}", "Failed to start task")
                    else:
                        if col_b1.button("Pause", key=f"pause_{task.id}", use_container_width=True):
                            st.session_state.pause_prompt_id = task.id
                            st.rerun()

                    if col_b2.button("Complete", key=f"done_{task.id}", use_container_width=True, type="primary" if is_active else "secondary"):
                        run_notion_action(
                            lambda t_id=task.id: update_task_status(t_id, "Done"),
                            f"Completed: {task.task_name}",
                            "Failed to complete task"
                        )

                    if col_b3.button("🗑️ Delete", key=f"del_{task.id}", use_container_width=True):
                        run_notion_action(
                            lambda t_id=task.id: delete_task(t_id),
                            f"Deleted: {task.task_name}",
                            "Failed to delete task"
                        )

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
                                lambda bt_id=b_task.id: update_task_status(bt_id, "Not started"),
                                f"Promoted {b_task.task_name} to active queue!",
                                "Failed to promote task"
                            )
                    with b_col3:
                        if st.button("🗑️ Delete", key=f"del_{b_task.id}", use_container_width=True):
                            run_notion_action(
                                lambda bt_id=b_task.id: delete_task(bt_id),
                                f"Deleted: {b_task.task_name}",
                                "Failed to delete task"
                            )

elif st.session_state.active_page == "Reusable Asset Vault":
    st.subheader("Resources")
    col_q, col_d = st.columns([3, 1])
    search_q = col_q.text_input("Search snippets, templates, or docs...", "")
    vault_domain = col_d.selectbox("Filter Domain", ["All", "AIESEC", "Academics", "Clients", "Personal", "General"])
    try:
        assets = fetch_assets(domain_filter=vault_domain, search_query=search_q)
        if not assets:
            st.info("No assets found matching the filter criteria.")
        else:
            for asset in assets:
                with st.container(border=True):
                    a_info, a_link = st.columns([4, 1])
                    with a_info:
                        st.markdown(f"**{escape_markdown(asset.title)}**  `{escape_markdown(asset.type)}` `{escape_markdown(asset.domain)}`")
                        if asset.tags:
                            escaped_tags = ", ".join(escape_markdown(t) for t in asset.tags)
                            st.caption(f"Tags: {escaped_tags}")
                    with a_link:
                        if asset.url:
                            st.link_button("Open Resources", asset.url, use_container_width=True)
                        else:
                            st.caption("No URL attached")
    except Exception as e:
        st.error(f"Error querying Asset Vault: {str(e)}")

elif st.session_state.active_page == "Quick Task Capture":
    st.markdown("<h2 style='text-align: center; color: #1C1917; margin-bottom: 1.25rem;'>Add Task</h2>", unsafe_allow_html=True)
    _, col_form_center, _ = st.columns([1, 6, 1])
    with col_form_center:
        render_add_task_form(key_suffix="_tab")