import os
import re
import httpx
from datetime import datetime, timedelta

from config import REPORTS_DIR, IMAGES_DIR, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from models import Experiment, get_session


def get_week_range(target_date: datetime = None):
    if target_date is None:
        target_date = datetime.now()
    d = target_date.date()
    monday = d - timedelta(days=d.weekday())
    friday = monday + timedelta(days=4)
    return monday, friday


def fetch_weekly_experiments(monday, friday):
    session = get_session()
    sunday = friday + timedelta(days=2)
    experiments = (
        session.query(Experiment)
        .filter(
            Experiment.created_at >= datetime.combine(monday, datetime.min.time()),
            Experiment.created_at <= datetime.combine(sunday, datetime.max.time()),
        )
        .order_by(Experiment.created_at)
        .all()
    )
    session.close()
    return experiments


def strip_images_from_markdown(md_text: str) -> str:
    """去除 Markdown 中的图片引用，只保留文字部分供 LLM 分析"""
    return re.sub(r"!\[[^\]]*\]\([^)]+\)", "[图片]", md_text)


def build_experiments_text(experiments: list[Experiment]) -> str:
    """将实验列表转为纯文本摘要，送给 LLM 分析"""
    parts = []
    for i, exp in enumerate(experiments, 1):
        text_content = strip_images_from_markdown(exp.content) if exp.content else "无"
        parts.append(
            f"实验{i}: {exp.title}\n"
            f"  时间: {exp.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"  标签: {exp.tags or '无'}\n"
            f"  内容:\n{text_content}"
        )
    return "\n\n---\n\n".join(parts)


def build_raw_report(experiments: list[Experiment]) -> str:
    """将每条实验记录的原始 Markdown 拼接为周报的详情部分"""
    lines = []
    for i, exp in enumerate(experiments, 1):
        lines.append(f"### {i}. {exp.title}")
        lines.append("")
        lines.append(f"**记录时间**: {exp.created_at.strftime('%Y-%m-%d %H:%M')}  ")
        if exp.tags:
            lines.append(f"**标签**: {exp.tags}")
        lines.append("")

        if exp.content:
            lines.append(exp.content)
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def call_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "content-type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        resp = httpx.post(
            f"{LLM_BASE_URL}/v1/messages",
            headers=headers,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]
    except Exception as e:
        return f"（LLM 生成失败: {e}）"


def generate_llm_summary(experiments: list[Experiment]) -> str:
    if not experiments:
        return "本周暂无实验记录。"

    exp_text = build_experiments_text(experiments)
    prompt = (
        "你是一位 AI 科研助手。请根据以下本周实验记录，用中文生成一份结构化的周报总结。\n"
        "要求：\n"
        "1. 先写一段【本周总结】，概括本周实验的整体方向、关键发现和进展\n"
        "2. 如果有多组实验，写一段【实验对比分析】，对比不同实验的参数差异和结果差异\n"
        "3. 最后写一段【下周建议】，基于本周结果给出下周可以尝试的方向\n"
        "4. 语言简洁专业，使用 Markdown 格式\n\n"
        f"本周实验记录：\n\n{exp_text}"
    )
    return call_llm(prompt)


def generate_weekly_report(target_date: datetime = None) -> str:
    monday, friday = get_week_range(target_date)
    experiments = fetch_weekly_experiments(monday, friday)

    report_lines = [
        f"# 周报 {monday} ~ {friday}",
        "",
        f"本周共记录 **{len(experiments)}** 项实验。",
        "",
        "---",
        "",
    ]

    if experiments:
        summary = generate_llm_summary(experiments)
        report_lines.extend([
            "## AI 智能总结",
            "",
            summary,
            "",
            "---",
            "",
            "## 实验详情",
            "",
        ])
        report_lines.append(build_raw_report(experiments))
    else:
        report_lines.append("本周暂无实验记录。\n")

    report_content = "\n".join(report_lines)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    filename = f"weekly_report_{monday}_{friday}.md"
    filepath = os.path.join(REPORTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_content)

    return filepath
