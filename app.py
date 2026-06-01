import streamlit as st
from openai import OpenAI
import requests

# ================= 从 Secrets 读取配置 =================
API_KEY = st.secrets["API_KEY"]
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL_NAME = "glm-4-flash"

# ================= 从 GitHub 加载永久知识库 =================
@st.cache_data(ttl=3600)
def load_remote_knowledge_base():
    url = "https://raw.githubusercontent.com/56vswqsrtf-arch/ai-counselor/main/knowledge_base.txt"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    return ""

if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = load_remote_knowledge_base()

# ================= 页面设置 =================
st.set_page_config(page_title="汤小知", page_icon="🎓")
st.title("🎓 汤小知——把重复劳动倒给AI，把深度陪伴还给导员")
st.markdown("你好！我是你的专属AI辅导员汤小知。学业压力、心理困惑、生涯规划……随时和我聊聊吧。")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ================= 侧边栏 =================
with st.sidebar:
    st.header("📌 常用场景")
    scenes = {
        "📚 心理压力": "校园中，该去哪里咨询心理相关问题呢",
        "💼 入团入党流程": "想入团入党，但是不知道流程",
        "😟 网络诈骗": "防范电信诈骗有哪些步骤呢？",
        "📝 绩点换算": "怎么算自己上一学期的绩点呢"
    }
    for label, text in scenes.items():
        if st.button(label):
            st.session_state.messages.append({"role": "user", "content": text})
            st.rerun()

    st.markdown("---")

    # ========== 人工窗口 ==========
    with st.expander("📞 人工窗口"):
        st.markdown("""
        **如果需要更深入的帮助，欢迎联系你的辅导员老师：田老师**

        - 📧 **邮箱**：877571465@qq.com  
        - 📱 **电话/微信**：131-6464-1035  
        - 🏢 **办公地址**：群贤楼208  
        - ⏰ **工作时间**：周一至周五 8:00-17:00  

        *我们一直在这里等你，不用犹豫～*
        """)

    st.markdown("---")

    st.caption("✨ 创新创业比赛演示版 | 汤小知团队")

# ================= 初始化对话 =================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "我是经验丰富、亲切温暖的AI辅导员汤小知。我擅长解答学生的学业、心理、就业、校园生活等问题。我的回答要有条理、有同理心，并提供实用的建议。我会使用自然流畅的中文。"},
        {"role": "assistant", "content": "同学你好！我是汤小知，有什么想聊的随时告诉我～"}
    ]

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
        with st.spinner("汤小知正在思考……"):
            if st.session_state.knowledge_base:
                system_with_kb = {"role": "system", "content": f"""你是本校AI辅导员，必须严格且仅根据以下【学校资料】回答学生问题。
- 如果资料中有相关内容，请直接引用原文回答，不要添加任何其他信息。
- 如果资料中完全没有相关信息，请回答："抱歉，我暂未学习到这方面的学校规定，建议咨询辅导员老师。"
- 禁止使用你自己的常识或网络信息来补充。

【学校资料】
{st.session_state.knowledge_base}"""}
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
