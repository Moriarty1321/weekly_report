import os
import re
import sys
import uuid
import streamlit as st
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import IMAGES_DIR, REPORTS_DIR
from models import Experiment, get_session
from report_generator import generate_weekly_report

st.set_page_config(page_title="实验周报系统", page_icon="🔬", layout="wide")

MARKDOWN_EXAMPLE = """\
## 实验目的

测试不同学习率对 Dodge 场景下 agent 表现的影响。

## 实验参数

| 参数 | 值 |
|------|-----|
| learning_rate | 3e-4 |
| batch_size | 64 |
| network | CNN |

## 实验过程

第一阶段训练 100 epoch，loss 曲线如下：

![loss曲线](此处粘贴上方复制的图片引用)

## 实验结果

最终成功率达到 87.3%，对比如图：

![对比图](此处粘贴上方复制的图片引用)

## 结论

CNN + lr=3e-4 是目前最优的参数组合。\
"""


def save_uploaded_images(uploaded_files) -> list[str]:
    os.makedirs(IMAGES_DIR, exist_ok=True)
    saved = []
    for f in uploaded_files:
        filename = f"{uuid.uuid4().hex[:8]}_{f.name}"
        filepath = os.path.join(IMAGES_DIR, filename)
        with open(filepath, "wb") as out:
            out.write(f.getbuffer())
        saved.append(filename)
    return saved


def render_markdown_with_local_images(md_text: str):
    """渲染 Markdown，将本地图片路径转为 st.image 调用"""
    img_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    parts = img_pattern.split(md_text)

    i = 0
    while i < len(parts):
        if i + 2 < len(parts):
            text_before = parts[i]
            alt_text = parts[i + 1]
            img_src = parts[i + 2]

            if text_before.strip():
                st.markdown(text_before)

            img_path = img_src.strip()
            if not img_path.startswith("http"):
                abs_path = os.path.join(IMAGES_DIR, os.path.basename(img_path))
                if os.path.exists(abs_path):
                    st.image(abs_path, caption=alt_text or None)
                else:
                    st.warning(f"图片未找到: {img_path}")
            else:
                st.image(img_path, caption=alt_text or None)

            i += 3
        else:
            if parts[i].strip():
                st.markdown(parts[i])
            i += 1


def page_add_record():
    st.header("📝 新增实验记录")

    # ---- 步骤 1: 上传图片 ----
    st.subheader("① 上传图片")
    st.caption("先上传图片，获取 Markdown 引用语法，再粘贴到下方内容中对应位置。")

    uploaded = st.file_uploader(
        "选择图片文件",
        type=["png", "jpg", "jpeg", "gif", "bmp", "webp"],
        accept_multiple_files=True,
        key="img_uploader",
    )

    saved_images = []
    if uploaded:
        saved_images = save_uploaded_images(uploaded)
        st.success(f"已上传 {len(saved_images)} 张图片，请复制下方引用插入到 Markdown 内容中：")
        for img_name in saved_images:
            ref = f"![{img_name}]({img_name})"
            st.code(ref, language=None)

        if "all_images" not in st.session_state:
            st.session_state.all_images = []
        st.session_state.all_images.extend(saved_images)

    st.markdown("---")

    # ---- 步骤 2: 编写 Markdown ----
    st.subheader("② 编写实验记录（Markdown）")

    with st.expander("📖 查看 Markdown 示例模板", expanded=False):
        st.code(MARKDOWN_EXAMPLE, language="markdown")

    with st.form("experiment_form", clear_on_submit=True):
        title = st.text_input("实验名称 *", placeholder="例如: Dodge-CNN-lr3e4")
        content = st.text_area(
            "实验内容（Markdown 格式，图文混排）",
            height=400,
            placeholder="在此用 Markdown 自由编写，可穿插图片引用 ![描述](文件名)...",
        )
        tags = st.text_input("标签", placeholder="逗号分隔，例如: RL, HollowKnight, PPO")
        submitted = st.form_submit_button("💾 保存记录", use_container_width=True)

    if submitted:
        if not title.strip():
            st.error("请填写实验名称！")
            return

        all_imgs = st.session_state.get("all_images", [])

        session = get_session()
        exp = Experiment(
            title=title.strip(),
            content=content,
            tags=tags.strip(),
        )
        exp.set_images(all_imgs)
        session.add(exp)
        session.commit()
        session.close()

        st.session_state.all_images = []
        st.success(f"实验 **{title}** 已保存！")

    # ---- 实时预览 ----
    if content_preview := st.session_state.get("experiment_form", {}).get("content"):
        st.markdown("---")
        st.subheader("预览")
        render_markdown_with_local_images(content_preview)


def page_history():
    st.header("📋 实验记录历史")

    session = get_session()
    experiments = (
        session.query(Experiment).order_by(Experiment.created_at.desc()).all()
    )

    if not experiments:
        st.info("暂无实验记录，请先添加实验。")
        session.close()
        return

    st.write(f"共 **{len(experiments)}** 条记录")

    for exp in experiments:
        with st.expander(
            f"🔬 {exp.title}  —  {exp.created_at.strftime('%Y-%m-%d %H:%M')}",
            expanded=False,
        ):
            if exp.tags:
                tag_list = [t.strip() for t in exp.tags.split(",") if t.strip()]
                st.markdown(" ".join(f"`{t}`" for t in tag_list))

            if exp.content:
                render_markdown_with_local_images(exp.content)

            if st.button("🗑️ 删除", key=f"del_{exp.id}"):
                for img_name in exp.get_images():
                    img_path = os.path.join(IMAGES_DIR, img_name)
                    if os.path.exists(img_path):
                        os.remove(img_path)
                session.delete(exp)
                session.commit()
                st.rerun()

    session.close()


def page_generate_report():
    st.header("📊 生成周报")

    st.markdown("汇总本周实验记录，并调用 AI 生成智能总结。")

    col1, col2 = st.columns(2)
    with col1:
        use_date = st.date_input(
            "选择日期（生成该日期所在周的周报）",
            value=datetime.now().date(),
        )
    with col2:
        st.markdown("")
        st.markdown("")
        generate = st.button("🚀 生成周报", use_container_width=True)

    if generate:
        with st.spinner("正在生成周报，AI 正在分析实验数据..."):
            target = datetime.combine(use_date, datetime.min.time())
            filepath = generate_weekly_report(target)

        st.success(f"周报已生成！保存至：`{filepath}`")

        with open(filepath, "r", encoding="utf-8") as f:
            report_content = f.read()

        st.markdown("---")
        render_markdown_with_local_images(report_content)

        st.download_button(
            label="📥 下载周报 (Markdown)",
            data=report_content,
            file_name=os.path.basename(filepath),
            mime="text/markdown",
        )

    st.markdown("---")
    st.subheader("历史周报")

    if os.path.exists(REPORTS_DIR):
        reports = sorted(
            [f for f in os.listdir(REPORTS_DIR) if f.endswith(".md")],
            reverse=True,
        )
        if reports:
            for report_name in reports:
                report_path = os.path.join(REPORTS_DIR, report_name)
                with st.expander(f"📄 {report_name}"):
                    with open(report_path, "r", encoding="utf-8") as f:
                        render_markdown_with_local_images(f.read())
        else:
            st.info("暂无历史周报。")
    else:
        st.info("暂无历史周报。")


# ===== 侧边栏导航 =====
st.sidebar.title("🔬 实验周报系统")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "导航",
    ["📝 新增实验", "📋 实验历史", "📊 生成周报"],
    label_visibility="collapsed",
)

if page == "📝 新增实验":
    page_add_record()
elif page == "📋 实验历史":
    page_history()
elif page == "📊 生成周报":
    page_generate_report()
