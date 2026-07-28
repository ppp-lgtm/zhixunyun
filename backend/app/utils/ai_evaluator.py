import json
from openai import OpenAI

from app.config import get_settings

_settings = get_settings()

# DeepSeek 官方 API（文字评价）
DEEPSEEK_API_KEY = _settings.DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL = _settings.DEEPSEEK_BASE_URL

# 硅基流动 API（图片识别）
SILICON_API_KEY = _settings.SILICON_API_KEY
SILICON_BASE_URL = _settings.SILICON_BASE_URL


# 延迟初始化：没有 Key 时不实例化，避免启动时报错（本地开发 / CI 自测）
def _lazy_client(api_key: str, base_url: str):
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key, base_url=base_url)
    except Exception:
        return None


deepseek_client = _lazy_client(DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL)
silicon_client = _lazy_client(SILICON_API_KEY, SILICON_BASE_URL)


def evaluate(task_requirements, student_content, criteria):
    """DeepSeek 文字评价"""
    criteria_text = "、".join(criteria)

    prompt = f"""你是软件实训评价专家。请对照实训要求评价学生作业，按JSON格式返回。

实训要求：{task_requirements}

学生提交：{student_content}

评分维度：{criteria_text}

每个维度给0-100分和一句话理由，再加总分(加权平均)和总评。
只返回JSON，格式：{{"scores":[{{"name":"维度名","score":80,"reason":"理由"}}],"total":85,"comment":"总评"}}"""

    if deepseek_client is None:
        return {"scores": [], "total": 0, "comment": "AI 未配置，请联系管理员设置 DEEPSEEK_API_KEY。"}

    response = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    result = response.choices[0].message.content
    if "```" in result:
        result = result.split("```")[1].split("```")[0]
    if result.startswith("json"):
        result = result[4:]

    return json.loads(result.strip())


def evaluate_with_image(task_requirements, criteria, image_data_list=None, text_content=None):
    """支持多张图片的多模态评价"""
    criteria_text = "、".join(criteria)

    user_content = []

    # 放所有图片
    if image_data_list:
        for img in image_data_list:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": img}
            })

    content_text = f"""你是软件实训评价专家。请综合查看以下{len(image_data_list) if image_data_list else 0}张截图（可能包含代码截图、界面截图、文档截图等），按实训要求评价，返回JSON。

实训要求：{task_requirements}
{f'补充说明：{text_content}' if text_content else ''}
评分维度：{criteria_text}

请综合所有截图内容，每个维度给0-100分和理由，加总分和总评。
只返回JSON：{{"scores":[{{"name":"维度名","score":80,"reason":"理由"}}],"total":85,"comment":"总评"}}"""

    user_content.append({"type": "text", "text": content_text})

    if silicon_client is None:
        return {"scores": [], "total": 0, "comment": "图片识别服务未配置，请联系管理员设置 SILICON_API_KEY。"}

    response = silicon_client.chat.completions.create(
        model="Qwen/Qwen3.5-4B",
        messages=[{"role": "user", "content": user_content}],
        temperature=0.3,
        max_tokens=4096
    )

    result = response.choices[0].message.content
    if "```" in result:
        result = result.split("```")[1].split("```")[0]
    if result.startswith("json"):
        result = result[4:]

    return json.loads(result.strip())


def check_completeness(task_requirements, student_content):
    """DeepSeek 智能核查"""
    prompt = f"""你是软件实训核查专家。对照实训要求，检查学生作业的步骤完整性和逻辑漏洞。

实训要求：
{task_requirements}

学生提交：
{student_content[:3000]}

请返回JSON：
{{
    "steps": [
        {{"step":"实训要求中的步骤","status":"已完成/缺失/部分完成","detail":"说明"}}
    ],
    "issues": [
        {{"type":"逻辑漏洞/不规范/错误","description":"具体描述","severity":"高/中/低"}}
    ],
    "summary":"整体核查总结"
}}"""

    try:
        if deepseek_client is None:
            return {"steps": [], "issues": [], "summary": "核查暂时不可用：AI 服务未配置"}
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        result = response.choices[0].message.content
        if "```" in result:
            result = result.split("```")[1].split("```")[0]
        if result.startswith("json"):
            result = result[4:]
        return json.loads(result.strip())
    except:
        return {"steps": [], "issues": [], "summary": "核查暂时不可用"}

def is_ai_configured():
    """检查 AI API Key 是否已配置"""
    test_values = {"", "sk-your-api-key"}
    return bool(
        DEEPSEEK_API_KEY
        and DEEPSEEK_API_KEY not in test_values
        and (not DEEPSEEK_API_KEY.startswith("sk-") or len(DEEPSEEK_API_KEY) >= 16)
    )