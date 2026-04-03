import streamlit as st
import os
import time
from dotenv import load_dotenv
from run_agent import run_agent  # 确保 run_agent 是上一轮修改后的 generator 版本

# 1. 加载环境变量与初始化
load_dotenv()

# --- 网页页面配置 ---
st.set_page_config(
    page_title="轴承故障 AI 智能诊断中心",
    page_icon="🏭",
    layout="wide"
)

# --- 自定义 CSS 样式（增加工业感） ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stStatus { border-radius: 10px; border: 1px solid #d1d8e0; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 轴承生产质量异常 - AI 智能诊断中心")
st.caption("技术栈：Python / LangChain (ReAct) / Qwen-LLM / Streamlit / Pydantic")
st.markdown("---")

# --- 2. 侧边栏：工业系统监控状态 ---
with st.sidebar:
    st.header("⚙️ 工业系统实时监控")
    st.success("✅ MES 系统：已连接 (OPC UA)")
    st.success("✅ QMS 质量库：已连接 (MySQL)")
    st.success("✅ SOP 工艺库：已连接 (VectorDB)")
    
    st.divider()
    with st.expander("📝 使用指南", expanded=True):
        st.info("""
        **操作步骤：**
        1. 在对话框输入现场异常描述。
        2. AI 将自动拆解意图，跨系统调取实时参数。
        3. 系统将基于工艺标准给出诊断报告。
        
        **示例输入：**
        *“M_102机床生产的批次B202410轴承6204被退回了，帮我查下原因。”*
        """)
    
    if st.button("清除对话历史"):
        st.session_state.messages = []
        st.rerun()

# --- 3. 主界面：对话记录管理 ---

# 初始化 Session State 存储对话
if "messages" not in st.session_state:
    st.session_state.messages = []

# 渲染历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. 核心逻辑：用户输入与 Agent 推理交互 ---

if prompt := st.chat_input("请输入车间异常排查请求..."):
    # A. 展示用户输入
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B. AI 推理展示
    with st.chat_message("assistant"):
        final_report = ""
        
        # 使用 st.status 展示推理链（ReAct 循环）
        with st.status("🛠️ 正在跨系统调取数据并进行逻辑推理...", expanded=True) as status:
            # 迭代 run_agent 生成器获取每一步输出
            for step in run_agent(prompt):
                if step["type"] == "info":
                    st.write(f"ℹ️ {step['content']}")
                
                elif step["type"] == "thought":
                    st.write(f"🧠 **思考（Thought）：** {step['content']}")
                
                elif step["type"] == "action":
                    st.code(f"🛠️ 执行动作（Action）：{step['content']}", language="python")
                
                elif step["type"] == "observation":
                    st.info(f"👀 **观察结果（Observation）：** {step['content']}")
                
                elif step["type"] == "final_answer":
                    final_report = step["content"]
                    # 推理成功，自动收起状态栏并更新状态
                    status.update(label="✅ 根因诊断完成", state="complete", expanded=False)
                
                elif step["type"] == "error":
                    st.error(f"❌ 系统异常：{step['content']}")
                    status.update(label="⚠️ 诊断过程意外中断", state="error")
        
        # C. 展示最终诊断报告
        if final_report:
            st.markdown("### 📋 最终故障诊断报告")
            st.success(final_report)
            # 存入历史记录
            st.session_state.messages.append({"role": "assistant", "content": f"### 📋 最终故障诊断报告\n{final_report}"})