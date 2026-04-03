import json
import os
from pydantic import BaseModel, Field, ValidationError

# 1. 定义严格的数据校验模型 (面试加分项)
class QualityQuery(BaseModel):
    batch_no: str = Field(..., description="生产批次号，必须以B开头，例如 B202410")

class MesQuery(BaseModel):
    device_id: str = Field(..., description="机床编号，必须以M_开头，例如 M_102")

class SopQuery(BaseModel):
    model: str = Field(..., description="轴承型号，例如 深沟球轴承6204")

class FinishQuery(BaseModel):
    answer: str = Field(..., description="最终诊断结论")

# 2. 工具类实现
class BearingDiagnosisTools:
    def __init__(self, data_dir="./data"):
        self.data_dir = data_dir
        self.quality_db = self._load_json("quality_db.json")
        self.mes_db = self._load_json("mes_db.json")
        self.standard_sop = self._load_json("standard_sop.json")
        
    def _load_json(self, filename):
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def query_quality_log(self, **kwargs) -> str:
        # 【新增：可视化感知点】
        print(f"\n>>>> [系统动作]：正在接入 QMS 质量管理系统，查询批次 {kwargs.get('batch_no')} 的质检历史...")
        try:
            # 使用 Pydantic 校验大模型传来的参数
            params = QualityQuery(**kwargs)
        except ValidationError as e:
            return f"参数错误，请检查格式: {e}"
            
        data = self.quality_db.get(params.batch_no)
        if not data: return f"数据库中未找到批次 {params.batch_no} 的记录。"
        return f"批次{params.batch_no}质检异常: {data['defect_type']}, 偏差值: {data['deviation']}"

    def query_mes_params(self, **kwargs) -> str:
        # 【新增：可视化感知点】
        print(f"\n>>>> [系统动作]：正在通过 OPC UA 协议连接机床 {kwargs.get('device_id')}，抓取实时加工参数...")
        try:
            params = MesQuery(**kwargs)
        except ValidationError as e:
            return f"参数错误，请检查格式: {e}"
            
        data = self.mes_db.get(params.device_id)
        if not data: return f"未找到机床 {params.device_id} 的参数。"
        return f"机床{params.device_id}实时参数: 转速 {data['rpm']} RPM, 进给 {data['feed_rate']} mm/s"

    def query_standard_sop(self, **kwargs) -> str:
        # 【新增：可视化感知点】
        print(f"\n>>>> [系统动作]：正在检索《轴承专家知识库》，提取型号 {kwargs.get('model')} 的法定技术要求与历史经验点...")
        
        try:
            params = SopQuery(**kwargs)
        except ValidationError as e:
            # 如果 AI 传来的型号不对，这里会拦截并反馈
            return f"参数错误: {e}"
            
        data = self.standard_sop.get(params.model)
        if not data: 
            return f"警告：未找到型号 {params.model} 的工艺标准，建议人工查阅纸质手册。"
            
        return f"标准参数: 建议转速 {data['std_rpm']} RPM, 进给 {data['std_feed']} mm/s。工艺提示：{data['notice']}"
    
    def finish(self, **kwargs) -> str:
        return kwargs.get("answer", "未能生成答案")

    def get_tool_description(self) -> str:
        return """
        1. query_quality_log(json_args)
           - 功能: 查询批次尺寸超差的具体数据
           - 参数示例: {"batch_no": "B202410"}
        2. query_mes_params(json_args)
           - 功能: 查询故障机床的实际加工参数
           - 参数示例: {"device_id": "M_102"}
        3. query_standard_sop(json_args)
           - 功能: 查询轴承的标准加工工艺和易错点提示
           - 参数示例: {"model": "深沟球轴承6204"}
        4. finish(json_args)
           - 功能: 输出最终诊断报告结束任务
           - 参数示例: {"answer": "由于转速过高导致..."}
        """