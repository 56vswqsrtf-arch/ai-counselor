import streamlit as st
from openai import OpenAI
import io
import PyPDF2

# ================= 配置区（务必替换为你的真实 Key）=================
API_KEY = "c841c492cf0d4211af971b2fcced5830.yQNNk43Ahre9PK84"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL_NAME = "glm-4-flash"

# ================= 页面设置 =================
st.set_page_config(page_title="AI辅导员", page_icon="🎓")
st.title("🎓 AI辅导员——你身边的校园智能助手")
st.markdown("你好！我是你的专属AI辅导员。学业压力、心理困惑、生涯规划……随时和我聊聊吧。")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ---------- 知识库存储 ----------
if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = ""

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一位经验丰富、亲切温暖的大学辅导员。你擅长解答学生的学业、心理、就业、校园生活等问题。你的回答要有条理、有同理心，并提供实用的建议。请使用自然流畅的中文。"},
        {"role": "assistant", "content": "同学你好！我是你的AI辅导员，有什么想聊的随时告诉我～"}
    ]

for msg in st.session_state.messages:
    avatar = "🎓" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if prompt := st.chat_input("请输入你的问题或困惑……"):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="🎓"):
        with st.spinner("AI辅导员正在思考……"):
            # ---- 知识库优先 ----
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

# ================= 侧边栏 =================
with st.sidebar:
    # ---------- PDF 上传 ----------
    st.header("📄 上传学校资料 (PDF)")
    uploaded_file = st.file_uploader("选择 PDF 文件", type="pdf")
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
        except Exception as e:
            st.error(f"读取PDF时出错，请确认文件未被加密且不是扫描图片: {e}")

    if st.session_state.knowledge_base:
        st.info(f"当前已加载资料，共 {len(st.session_state.knowledge_base)} 个字符")
    else:
        st.info("尚未上传资料，AI将使用通用知识回答")

    st.markdown("---")

    # ---------- 常用场景 ----------
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
    st.caption("✨ 创新创业比赛演示版 | AI辅导员团队")