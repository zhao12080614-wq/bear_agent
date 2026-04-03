import os
import re
import json
from openai import OpenAI
from dotenv import load_dotenv
from bearing_tools import BearingDiagnosisTools

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL") 
)
MODEL = os.getenv("MODEL", "qwen-plus") 

def call_llm(prompt_history: str) -> str: 
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant following the ReAct framework."},
        {"role": "user", "content": prompt_history}
    ]
    try: 
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.1,  # 工业诊断需要严谨，温度调低
            stop=["\nObservation:"]
        )
        return response.choices[0].message.content
    except Exception as e: 
        return f"LLM API调用失败: {e}"

def run_agent(question: str, max_iterations: int=10):
    """
    适配前端的 ReAct Agent 主流程 (生成器版本)
    """
    tools = BearingDiagnosisTools("./data")
    with open("prompt_template.txt", 'r', encoding='utf-8') as f:
        # 加载工具描述
        prompt_history = f.read().replace("{tool_description}", tools.get_tool_description())
    
    prompt_history = prompt_history.replace("{user_query}", question)
    
    # 告知前端：Agent 正式启动
    yield {"type": "info", "content": f"🚀 工业诊断 Agent 启动，正在分析问题: {question}"}
    
    for i in range(max_iterations):
        # 1. 调用 LLM 获取推理
        llm_output = call_llm(prompt_history)
        
        # 2. 解析 Thought 和 Action
        thought_match = re.search(r"Thought: (.*?)\nAction: (.*)", llm_output, re.DOTALL)
        if not thought_match:
            yield {"type": "error", "content": f"LLM 输出格式异常，解析失败。\n原始输出: {llm_output}"}
            return

        thought = thought_match.group(1).strip()
        action = thought_match.group(2).strip()
        
        # 【核心改动】：将思考和动作 yield 给前端显示
        yield {"type": "thought", "content": thought}
        yield {"type": "action", "content": action}
        
        prompt_history += f"\nThought: {thought}\nAction: {action}"
        
        # 3. 解析并执行工具
        action_match = re.search(r"(\w+)\((.*?)\)", action)
        if not action_match:
            observation = "格式错误：必须严格使用 工具名({\"key\": \"value\"}) 的格式。"
        else:
            tool_name = action_match.group(1)
            args_str = action_match.group(2).strip()
            
            if hasattr(tools, tool_name): 
                try: 
                    # 解析参数
                    args_dict = json.loads(args_str) 
                    tool_method = getattr(tools, tool_name)
                    
                    # 执行工具逻辑
                    observation = tool_method(**args_dict)
                    
                    # 【核心改动】：如果执行了 finish，返回最终答案并结束
                    if tool_name == "finish": 
                        yield {"type": "final_answer", "content": observation}
                        return
                        
                except json.JSONDecodeError:
                    observation = f"Action执行失败: '{args_str}' 不是合法的JSON格式。请检查单双引号是否正确。"
                except Exception as e:
                    observation = f"Action执行报错: {str(e)}。请修正参数后重试。"
            else:
                observation = f"工具库中不存在：{tool_name}"
        
        # 【核心改动】：将观察结果 yield 给前端显示
        yield {"type": "observation", "content": observation}
        prompt_history += f"\nObservation: {observation}"
        
    yield {"type": "error", "content": "达到最大推理次数，未能在规定步骤内完成诊断。"}

if __name__ == "__main__":
    # 模拟现场工人报错
    query = "今天用M_102机床生产的批次B202410的深沟球轴承6204被质检退回了，帮我查查是什么原因导致的？"
    result = run_agent(query)
    
    print(f"\n{'='*40}\n✅ 最终诊断报告:\n{result}\n{'='*40}")