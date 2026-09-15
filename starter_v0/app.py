from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from chat import (
    run_model_tool_loop,
    write_transcript,
    safe_slug,
    now_iso,
    trim_history,
)
from versioning import build_artifact_version, artifact_version_dict

ROOT = Path(__file__).parent
load_lab_env(ROOT)

st.set_page_config(
    page_title="IT Helpdesk Agent — Northstar Labs",
    page_icon="🛠️",
    layout="wide",
)

# ---------------------------------------------------------
# Sidebar: Artifact & Runtime Configuration
# ---------------------------------------------------------
st.sidebar.title("⚙️ Cấu hình Hệ thống")

# 1. Artifacts & Prompts selection
PROMPT_OPTIONS: dict[str, Path] = {
    "v3 (Khuyên dùng - Đầy đủ nhất)": ROOT / "artifacts" / "system_prompt_v3.md",
    "v2": ROOT / "artifacts" / "system_prompt_v2.md",
    "v1": ROOT / "artifacts" / "system_prompt_v1.md",
    "Baseline (v0)": ROOT / "artifacts" / "system_prompt.md",
}

# Lọc chỉ lấy các file thực sự tồn tại
available_prompts = {k: v for k, v in PROMPT_OPTIONS.items() if v.exists()}
if not available_prompts:
    available_prompts["Default"] = ROOT / "artifacts" / "system_prompt.md"

selected_prompt_label = st.sidebar.selectbox(
    "Phiên bản System Prompt:",
    options=list(available_prompts.keys()),
    index=0,
)
system_prompt_path = available_prompts[selected_prompt_label]
tools_path = ROOT / "artifacts" / "tools.yaml"

# Suy ra version label đơn giản (v3, v2, v1, v0)
version_label = selected_prompt_label.split()[0].lower()

system_prompt = system_prompt_path.read_text(encoding="utf-8")
tool_decls = load_tool_declarations(tools_path)
openai_tools = to_openai_tools(tool_decls)

artifact_ver = build_artifact_version(version_label, system_prompt_path, tools_path)

# 2. Provider & Model Selection
provider_options = ["openrouter", "openai", "gemini", "anthropic"]
selected_provider_name = st.sidebar.selectbox("Model Provider:", options=provider_options, index=0)

default_model_val = os.getenv("OPENROUTER_MODEL", "") if selected_provider_name == "openrouter" else ""
model_override = st.sidebar.text_input(
    "Model ID (để trống để dùng mặc định):",
    value=default_model_val,
    placeholder="ví dụ: inclusionai/ling-3.0-flash-vl:free",
)
selected_model = model_override.strip() or None

history_window = st.sidebar.slider("Ngữ cảnh hội thoại (History Window):", min_value=1, max_value=10, value=5)
max_tool_rounds = st.sidebar.slider("Số vòng lặp Tool tối đa (Max Tool Rounds):", min_value=1, max_value=8, value=4)

# Hiển thị thông tin Artifact Hashes (Mục 9 LAB-GUIDE)
with st.sidebar.expander("📦 Artifact Version & Hashes", expanded=True):
    st.markdown(f"**Version:** `{artifact_ver.artifact_version}`")
    st.markdown(f"**Prompt File:** `{system_prompt_path.name}`")
    st.markdown(f"**Prompt Hash:** `{artifact_ver.prompt_hash}`")
    st.markdown(f"**Tools Hash:** `{artifact_ver.tools_hash}`")

# Reset / New conversation button
if st.sidebar.button("🔄 Bắt đầu phiên chat mới (New Session)", use_container_width=True):
    # Invalidate the session configuration so initialization rebuilds all chat
    # state together, including transcript, history and turn numbering.
    st.session_state.pop("current_config", None)
    st.rerun()

# ---------------------------------------------------------
# Session & Transcript Initialization
# ---------------------------------------------------------
config_key = (version_label, selected_provider_name, selected_model, str(system_prompt_path))

if "current_config" not in st.session_state or st.session_state.current_config != config_key:
    st.session_state.current_config = config_key
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([
        safe_slug(version_label),
        safe_slug(selected_provider_name),
        timestamp,
    ])
    transcripts_dir = ROOT / "transcripts"
    transcript_path = transcripts_dir / f"{transcript_id}.transcript.json"

    st.session_state.transcript_id = transcript_id
    st.session_state.transcript_path = str(transcript_path)
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_ver),
        "provider": selected_provider_name,
        "model": selected_model,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    st.session_state.messages = []
    st.session_state.raw_history = []
    st.session_state.turn_index = 0

st.sidebar.caption(f"📝 **Transcript Log:**\n`{st.session_state.transcript_path}`")

# ---------------------------------------------------------
# Main Chat Header & Body
# ---------------------------------------------------------
st.title("🛠️ IT Helpdesk Agent — Northstar Labs")
col_info1, col_info2 = st.columns([1, 1])
with col_info1:
    st.caption(f"🏷️ **Active Artifact:** `{artifact_ver.artifact_version}`")
with col_info2:
    st.caption(f"📝 **Transcript:** `{Path(st.session_state.transcript_path).name}`")

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Nếu là assistant, hiển thị audit trail (Status, Rounds, Tool Calls)
        if msg["role"] == "assistant":
            status = msg.get("status")
            rounds = msg.get("rounds_count", 0)
            
            # Badge trạng thái
            badge_color = "green" if status == "answered" else ("orange" if status == "waiting_for_user" else "red")
            st.markdown(
                f"<small>Trạng thái: :{badge_color}[**{status}**] | Vòng lặp Tools: **{rounds}**</small>",
                unsafe_allow_html=True,
            )
            
            tool_events = msg.get("tools", [])
            if tool_events:
                with st.expander(f"🔍 Chi tiết Tool Traces ({len(tool_events)} tool calls)"):
                    for idx, event in enumerate(tool_events, 1):
                        tool_name = event.get("tool", "unknown")
                        st.markdown(f"**#{idx} Tool: `{tool_name}`**")
                        st.markdown("**Arguments:**")
                        st.json(event.get("args", {}))
                        
                        result = event.get("result")
                        if isinstance(result, dict) and "error" in result:
                            st.error(f"Error: {result['error']} — {result.get('message', '')}")
                        else:
                            st.markdown("**Result:**")
                            st.json(result)
                        st.divider()

# ---------------------------------------------------------
# User Input & Execution Loop
# ---------------------------------------------------------
if prompt := st.chat_input("Nhập yêu cầu hỗ trợ IT... (ví dụ: kiểm tra vpn cho user USR-001)"):
    # 1. Hiển thị User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.raw_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Chuẩn bị Context cho Agent
    st.session_state.turn_index += 1
    turn_index = st.session_state.turn_index
    
    # Context gồm system prompt + history window gần nhất
    active_history = trim_history(st.session_state.raw_history[:-1], history_window)
    messages_for_model = [
        {"role": "system", "content": system_prompt},
        *active_history,
        {"role": "user", "content": prompt},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": turn_index,
        "started_at": now_iso(),
        "user": prompt,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    # 3. Chạy Agent Loop
    with st.chat_message("assistant"):
        with st.spinner("Agent đang suy luận và tương tác tools..."):
            try:
                provider = make_provider(selected_provider_name)
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages_for_model,
                    tools=openai_tools,
                    model=selected_model,
                    max_tool_rounds=max_tool_rounds,
                )
                turn_record.update(result)
                reply = result.get("assistant_text", "")
                tool_events = result.get("tool_events", [])
                status = result.get("status", "answered")
                rounds_count = len(result.get("rounds", []))
            except Exception as exc:
                status = "provider_error"
                rounds_count = 0
                error_msg = f"{type(exc).__name__}: {str(exc)}"
                turn_record.update({
                    "status": status,
                    "error": error_msg,
                })
                reply = f"⚠️ Gặp lỗi khi gọi mô hình: `{error_msg}`"
                tool_events = []

            # 4. Hiển thị phản hồi và audit trace
            st.markdown(reply)
            
            badge_color = "green" if status == "answered" else ("orange" if status == "waiting_for_user" else "red")
            st.markdown(
                f"<small>Trạng thái: :{badge_color}[**{status}**] | Vòng lặp Tools: **{rounds_count}**</small>",
                unsafe_allow_html=True,
            )

            if tool_events:
                with st.expander(f"🔍 Chi tiết Tool Traces ({len(tool_events)} tool calls)"):
                    for idx, event in enumerate(tool_events, 1):
                        tool_name = event.get("tool", "unknown")
                        st.markdown(f"**#{idx} Tool: `{tool_name}`**")
                        st.markdown("**Arguments:**")
                        st.json(event.get("args", {}))
                        
                        result_data = event.get("result")
                        if isinstance(result_data, dict) and "error" in result_data:
                            st.error(f"Error: {result_data['error']} — {result_data.get('message', '')}")
                        else:
                            st.markdown("**Result:**")
                            st.json(result_data)
                        st.divider()

    # 5. Lưu vào Transcript JSON (chuẩn chat.py)
    turn_record["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn_record)
    transcript_file = Path(st.session_state.transcript_path)
    write_transcript(transcript_file, st.session_state.transcript)

    # 6. Cập nhật session state messages
    st.session_state.raw_history.append({"role": "assistant", "content": reply})
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
        "status": status,
        "rounds_count": rounds_count,
        "tools": tool_events,
        "transcript_path": str(transcript_file),
    })
