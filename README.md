# 🏭 Bearing-Fault-Diagnosis-Agent (工业级轴承异常诊断智能体)

基于 ReAct 框架的工业设备故障根因分析 Agent。本项目通过融合大语言模型 (LLM) 与现场 OT (操作技术) 数据，实现了从“人工经验排障”到“数据驱动自动诊断”的业务闭环。

## 📑 项目背景

在高端轴承磨加工车间，当出现尺寸超差、表面烧伤或振纹等异常时，传统的排查方式高度依赖高级工艺员的人工经验，需跨系统核对质检报告、MES机床状态与工艺标准SOP，平均单次排查耗时 >30 分钟，导致高昂的设备待机成本。

本项目将标准的工业排障逻辑转化为大模型可执行的 Agent 任务链，通过自动化 API 调用获取底层现场数据，在 5 分钟内自动输出根因分析报告。

## 💡 核心技术特性 (Core Features)

* **OT-IT 数据深度融合：** 将非结构化的自然语言报错（如“102机床生产的批次退回了”）解析为结构化的 SQL/API 查询指令，打通质检数据库 (QMS) 与制造执行系统 (MES)。
* **Pydantic 强类型拦截机制：** 针对 LLM 工具调用 (Tool Calling) 过程中常见的“参数幻觉”和“JSON 格式错误”问题，废弃高风险的 `eval()` 解析，采用 `Pydantic BaseModel` 进行强类型数据校验，从内存层级切断脏数据污染。
* **Self-Correction 上下文自修复工程：** 实现异常回传闭环。当底层工具调用抛出 `Exception`（如机床ID不存在、JSON漏加引号）时，系统不会中断，而是将报错 Traceback 包装为新的 `Observation` 动态注入 `Prompt` 历史，引导模型基于报错信息自主纠正参数并重试。

## 🔄 系统架构与数据流向

1.  **Input (输入)：** 接收车间异常文本描述。
2.  **LLM Routing (路由思考)：** 基于 ReAct 框架，模型输出下一步需要查询的数据动作 (`Thought` & `Action`)。
3.  **Validation (契约校验)：** `Action` 参数进入 Python 环境，使用 `Pydantic` 进行 Schema 验证。
4.  **Execution (工具执行)：** 校验通过后，执行模拟的 MySQL 数据库查询，获取机床实时转速、进给、冷却液流量等数据。
5.  **Feedback (反馈闭环)：** 查询结果或程序报错作为 `Observation` 返回给大模型，循环执行直至得出诊断结论 (`finish`)。

## 🚀 快速开始 (Quick Start)

### 环境依赖
* Python 3.8+
* 申请通义千问或其他兼容 OpenAI SDK 格式的 API_KEY

### 安装与运行
```bash
# 1. 克隆仓库
git clone [https://github.com/yourusername/Bearing-Fault-Diagnosis-Agent.git](https://github.com/yourusername/Bearing-Fault-Diagnosis-Agent.git)
cd Bearing-Fault-Diagnosis-Agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
# 在根目录创建 .env 文件，并填入您的 API_KEY
echo "DASHSCOPE_API_KEY=your_api_key_here" > .env
echo "DASHSCOPE_BASE_URL=[https://dashscope.aliyuncs.com/compatible-mode/v1](https://dashscope.aliyuncs.com/compatible-mode/v1)" >> .env
echo "MODEL=qwen-plus" >> .env

# 4. 运行诊断主程序
python run_agent.py