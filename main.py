import streamlit as st
from google import genai

# إعداد الصفحة والعنوان
st.set_page_config(page_title="Diaa AI", page_icon="🤖")
st.title("Diaa AI")
st.caption("A conversational assistant powered by Diaa Wesam.")

# جلب API Key من Secrets
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("مفتاح GEMINI_API_KEY غير موجود في Streamlit Secrets.")
    st.stop()

# تهيئة العميل
client = genai.Client(api_key=api_key)

# حفظ سجل المحادثة
if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض الرسائل السابقة
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# استقبال مدخلات المستخدم
if prompt := st.chat_input("اكتب رسالتك هنا..."):
    # إضافة ورسم رسالة المستخدم
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # تجهيز آخر 6 رسائل فقط لسرعة معالجة قصوى
    recent_messages = st.session_state.messages[-6:]
    contents = []
    for msg in recent_messages:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    # الحصول على الرد بأسرع طريقة تدفق
    with st.chat_message("assistant"):
        try:
            response = client.models.generate_content_stream(
                model="gemini-3.8-flash",
                contents=contents
            )
            
            # عرض النص فور وصوله بدون أي تأخير
            full_response = st.write_stream(chunk.text for chunk in response if chunk.text)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"حدث خطأ أثناء الاتصال: {e}")
