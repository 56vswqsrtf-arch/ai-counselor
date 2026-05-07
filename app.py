import streamlit as st
from openai import OpenAI
import io
import os
import PyPDF2

# ================= 从 Secrets 读取配置 =================
API_KEY = st.secrets["API_KEY"]
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL_NAME = "glm-4-flash"
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")  # 默认密码，记得在 Secrets 里改掉

# ================= 页面设置 =================
st.set_page_config(page_title="AI辅导员", page_icon="🎓")
st.title("🎓 AI辅导员——你身边的校园智能助手")
st.markdown("你好！我是你的专属AI辅导员。学业压力、心理困惑、生涯规划……随时和我聊聊吧。")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ================= 知识库存储 =================
if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = ""

# ================= 管理员面板（侧边栏底部） =================
with st.sidebar:
    # ----- 常用场景（对所有人可见）-----
    st.header("📌 常用场景")
    scenes = {
        "📚 学业压力大，学不进去": "最近学业压力很大，总学不进去，怎么办？",
        "💼 对就业方向很迷茫": "马上要毕业了，但完全不知道自己喜欢什么工作，很迷茫。",
        "😟 和室友关系紧张": "我和室友因为作息问题总是闹矛盾，心里很烦，该怎么处理？",
        "📝 考研还是工作？": "大三了，家里让考研，但自己想早点工作，特别纠结。"
    }
    for label, text in scenes.items():
        if st.button(label):
            st.session_state.messages.append({"role": "user", "content": text})
            st.rerun()

    st.markdown("---")

    # ----- 管理员入口（密码保护）-----
    with st.expander("🔐 管理员后台"):
        password = st.text_input("请输入管理员密码", type="password")
        if password == ADMIN_PASSWORD:
            st.success("✅ 管理员身份验证通过")
            st.header("📄 上传学校资料 (PDF)")
            uploaded_file = st.file_uploader("选择 PDF 文件", type="pdf", key="admin_upload")
            if uploaded_file is not None:
                try:
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    text_parts = []
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    st.session_state.knowledge_base = "\n".join(text_parts)
                    st.success(f"✅ 已成功读取 {len(pdf_reader.pages)} 页资料，AI辅导员现在将依据这份资料回答。")
                    st.info("⚠️ 注意：上传的资料仅在当前会话有效。如需永久保存，请将内容复制到 GitHub 仓库的 `knowledge_base.txt` 文件中。")
                except Exception as e:
                    st.error(f"读取PDF时出错: {e}")

            st.markdown("---")
            st.header("📝 手动编辑知识库")
            manual_kb = st.text_area("直接粘贴文本作为知识库内容", height=200)
            if st.button("更新知识库"):
                st.session_state.knowledge_base = manual_kb
                st.success("知识库已更新！")
                st.info("⚠️ 手动编辑的内容仅在当前会话有效。")

        elif password != "":
            st.error("密码错误")

    # ----- 知识库状态提示（对所有人可见）-----
    st.markdown("---")
    if st.session_state.knowledge_base:
        st.info(f"📚 当前知识库已加载，共 {len(st.session_state.knowledge_base)} 个字符")
    else:
        st.info("📚 尚未加载知识库，AI将使用通用知识回答")

    st.caption("✨ 创新创业比赛演示版 | AI辅导员团队")

# ================= 初始化消息 =================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "我是经验丰富、亲切温暖的大学辅导员。我擅长解答学生的学业、心理、就业、校园生活等问题。我的回答要有条理、有同理心，并提供实用的建议。我会使用自然流畅的中文。"},
        {"role": "assistant", "content": "同学你好！我是你的AI辅导员，有什么想聊的随时告诉我～"}
    ]

# ================= 显示历史消息 =================
for msg in st.session_state.messages:
    avatar = "🎓" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ================= 处理用户输入 =================
if prompt := st.chat_input("请输入你的问题或困惑……"):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="🎓"):
        with st.spinner("AI辅导员正在思考……"):
            # 知识库优先
            if st.session_state.knowledge_base:
                system_with_kb = {"role": "system", "content": f"请严格根据以下资料回答学生的问题。如果资料中没有相关信息，可以用你自己的知识补充，但请说明“资料中未提及”。\n\n【资料内容】\n{st.session_state.knowledge_base}"}
                messages_to_send = [system_with_kb] + st.session_state.messages
            else:
                messages_to_send = st.session_state.messages

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages_to_send,
                temperature=0.7,
                max_tokens=2000,
            )
            reply = response.choices[0].message.content
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})