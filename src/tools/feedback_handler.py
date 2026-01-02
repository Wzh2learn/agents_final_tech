"""
反馈处理工具：接收反馈 → 分类 → 通知/记录
对应 Dify 工作流：WF_Feedback_Handler_v1
"""
import os
from datetime import datetime
from typing import Optional
import glob
from langchain.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from coze_coding_utils.runtime_ctx.context import Context, default_headers


def _call_llm(ctx: Context, messages: list, config: dict) -> str:
    """调用大语言模型"""
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=config.get("model", "doubao-seed-1-6-251015"),
        api_key=api_key,
        base_url=base_url,
        streaming=True,
        temperature=config.get("temperature", 0.2),
        max_completion_tokens=config.get("max_completion_tokens", 2048),
        extra_body={
            "thinking": {
                "type": config.get("thinking", "disabled")
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )

    full_response = ""
    for chunk in llm.stream(messages):
        if hasattr(chunk, 'content') and chunk.content:
            # 处理 chunk.content 可能是字符串或列表的情况
            if isinstance(chunk.content, str):
                full_response += chunk.content
            elif isinstance(chunk.content, list):
                for item in chunk.content:
                    if isinstance(item, str):
                        full_response += item

    return full_response


def _save_feedback_record(
    user_feedback: str,
    last_answer: str,
    classification: str,
    is_critical: bool,
    conversation_id: str = ""
) -> str:
    """
    保存反馈记录到本地文件

    Returns:
        保存结果
    """
    try:
        # 确保目录存在
        feedback_dir = "assets/feedback_records"
        os.makedirs(feedback_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"feedback_{timestamp}.json"
        filepath = os.path.join(feedback_dir, filename)

        # 构建记录
        record = {
            "timestamp": datetime.now().isoformat(),
            "conversation_id": conversation_id,
            "user_feedback": user_feedback,
            "last_answer": last_answer,
            "classification": classification,
            "is_critical": is_critical,
            "status": "recorded"
        }

        # 保存到文件
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        return f"✅ 反馈已保存到：{filepath}"
    except Exception as e:
        return f"❌ 保存反馈失败：{str(e)}"


@tool
def feedback_handler(
    user_feedback: str,
    last_answer: str = "",
    conversation_id: str = "",
    auto_notify: bool = False,
    runtime = None
) -> str:
    """
    反馈处理工具：分类用户反馈并处理

    Args:
        user_feedback: 用户反馈内容
        last_answer: AI上次回答
        conversation_id: 对话ID
        auto_notify: 是否自动通知关键问题

    Returns:
        处理结果
    """
    ctx = runtime.context if runtime else None

    # 1. 分类反馈
    system_prompt = """# 任务
分析用户反馈的类型和重要性。

# 反馈分类
1. **critical** - 关键问题，需要立即处理
   - 系统错误或严重bug
   - 安全性问题
   - 数据错误或丢失
   - 严重影响用户体验

2. **improvement** - 改进建议
   - 功能需求
   - 体验优化建议
   - 性能提升建议

3. **clarification** - 澄清需求
   - 对答案不满意，需要更详细解释
   - 希望从不同角度理解
   - 需要补充信息

4. **praise** - 正面反馈
   - 表扬或感谢

# 输出格式（JSON）
{
    "type": "反馈类型",
    "is_critical": true/false,
    "reason": "分类原因",
    "suggested_action": "建议的处理方式"
}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""用户反馈：{user_feedback}

AI上次回答：{last_answer}
""")
    ]

    config = {
        "model": "doubao-seed-1-6-251015",
        "temperature": 0.2,
        "thinking": "disabled"
    }

    try:
        classification_result = _call_llm(ctx, messages, config)
    except Exception as e:
        classification_result = f"分类失败：{str(e)}"

    # 2. 解析分类结果
    try:
        import json
        # 尝试从结果中提取JSON
        start_idx = classification_result.find('{')
        end_idx = classification_result.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = classification_result[start_idx:end_idx]
            classification = json.loads(json_str)
            feedback_type = classification.get("type", "unknown")
            is_critical = classification.get("is_critical", False)
            reason = classification.get("reason", "")
            suggested_action = classification.get("suggested_action", "")
        else:
            # 如果无法解析JSON，使用默认值
            feedback_type = "clarification"
            is_critical = False
            reason = classification_result
            suggested_action = "记录并跟进"
    except Exception:
        feedback_type = "clarification"
        is_critical = False
        reason = classification_result
        suggested_action = "记录并跟进"

    # 3. 保存反馈记录
    save_result = _save_feedback_record(
        user_feedback=user_feedback,
        last_answer=last_answer,
        classification=feedback_type,
        is_critical=is_critical,
        conversation_id=conversation_id
    )

    # 4. 如果是关键问题且启用了自动通知，生成通知消息
    notify_message = ""
    if is_critical and auto_notify:
        notify_message = f"\n\n🔔 **关键问题通知**\n"
        notify_message += f"- 反馈类型：{feedback_type}\n"
        notify_message += f"- 原因：{reason}\n"
        notify_message += f"- 建议操作：{suggested_action}\n"
        notify_message += f"- 对话ID：{conversation_id}\n"
        notify_message += "\n请立即处理！"

    # 5. 生成处理结果
    result = f"""📊 反馈处理结果

**反馈分类**：{feedback_type}
**是否关键**：{'是 🔴' if is_critical else '否 🟢'}
**分类原因**：{reason}
**建议操作**：{suggested_action}

{save_result}
{notify_message}
"""

    return result


@tool
def generate_summary_report(
    runtime = None
) -> str:
    """
    生成反馈汇总报告

    Returns:
        反馈统计数据和汇总信息
    """
    ctx = runtime.context if runtime else None

    try:
        feedback_dir = "assets/feedback_records"
        if not os.path.exists(feedback_dir):
            return "暂无反馈记录"

        import json
        from collections import Counter

        # 读取所有反馈文件
        feedback_files = glob.glob(os.path.join(feedback_dir, "*.json"))
        if not feedback_files:
            return "暂无反馈记录"

        records = []
        for filepath in feedback_files:
            with open(filepath, 'r', encoding='utf-8') as f:
                records.append(json.load(f))

        # 统计
        total = len(records)
        critical_count = sum(1 for r in records if r.get("is_critical", False))
        type_counter = Counter(r.get("classification", "unknown") for r in records)

        # 生成报告
        report = f"""📈 反馈汇总报告

**总计反馈数**：{total}
**关键问题数**：{critical_count}
**非关键问题数**：{total - critical_count}

**分类统计**：
"""
        for feedback_type, count in type_counter.most_common():
            report += f"- {feedback_type}：{count}\n"

        # 最近的5条关键问题
        critical_records = [r for r in records if r.get("is_critical", False)]
        if critical_records:
            report += f"\n**最近的关键问题**（最近5条）：\n\n"
            for i, record in enumerate(critical_records[-5:], 1):
                report += f"{i}. {record.get('timestamp', '')}\n"
                report += f"   {record.get('user_feedback', '')[:100]}...\n\n"

        return report

    except Exception as e:
        return f"生成报告失败：{str(e)}"
