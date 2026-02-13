import streamlit as st
import asyncio
import json
import re
from twikit import Client
from datetime import datetime

# 1. د پاڼې بنسټیز تنظیمات
st.set_page_config(
    page_title="د الیاس سکریپر PRO",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. مټریال ډیزاین او پښتو سټایل (Custom CSS)
st.markdown("""
<style>
    /* اصلي بګراونډ او فونټ */
    .stApp {
        background-color: #0E1117;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* د پښتو لپاره د متن لوري (RTL) */
    .element-container, .stMarkdown, .stText, .stTextArea {
        direction: rtl;
        text-align: right;
    }
    
    /* سرلیکونه */
    h1, h2, h3 {
        color: #00B4D8;
        font-weight: 700;
        text-align: center; 
        text-shadow: 0px 0px 10px rgba(0, 180, 216, 0.3);
    }
    
    /* د بټنو ډیزاین (Material Button) */
    .stButton > button {
        background: linear-gradient(90deg, #0077B6 0%, #00B4D8 100%);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 10px 24px;
        font-size: 18px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 180, 216, 0.4);
    }

    /* د انپوټ فیلډونه */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #262730;
        color: #FAFAFA;
        border-radius: 10px;
        border: 1px solid #414141;
    }
    
    /* د پایلو جدول */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #414141;
    }
</style>
""", unsafe_allow_html=True)

# 3. مرستندویه فنکشنونه (Logic)
def clean_tweet_content(text):
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def extract_hashtags(text):
    return re.findall(r'#\w+', text)

async def scrape_process(queries, limit, ct0, auth_token, post_type, sort_mode):
    client = Client('en-US')
    try:
        client.set_cookies({"ct0": ct0, "auth_token": auth_token})
    except Exception as e:
        st.error(f"د کوکیز ستونزه: {e}")
        return []
    
    all_results = []
    seen_content_hashes = set()
    global_count = 0
    
    # د پروسې ښودلو ځای
    status_area = st.empty()
    progress_bar = st.progress(0)

    try:
        for q_idx, query in enumerate(queries):
            if global_count >= limit: break
            
            # ښکلی پیغام
            status_area.markdown(f"""
            <div style="background-color: #1E3A8A; padding: 10px; border-radius: 10px; border-right: 5px solid #00B4D8; margin-bottom: 10px;">
                <h4 style="margin:0; color: white;">🔎 لټون روان دی: {query}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                tweets = await client.search_tweet(query, product=post_type, count=limit)
            except Exception as e:
                st.warning(f"تېروتنه په {query} کې: {e}")
                continue

            if not tweets:
                continue

            while tweets:
                for tweet in tweets:
                    if global_count >= limit: break
                    
                    original_text = tweet.text
                    clean_text = clean_tweet_content(original_text)
                    
                    if not clean_text or len(clean_text) < 5: continue

                    text_hash = hash(clean_text)
                    if text_hash in seen_content_hashes: continue
                    seen_content_hashes.add(text_hash)
                    
                    tags = extract_hashtags(original_text)
                    global_count += 1
                    
                    post_obj = {
                        "شمېره": str(global_count),
                        "پوسټ متن": clean_text,
                        "هشټاګونه": ", ".join(tags)
                    }
                    all_results.append(post_obj)
                    
                    # پرمختګ اپډیټ کول
                    progress = min(global_count / limit, 1.0)
                    progress_bar.progress(progress)

                if global_count >= limit: break
                
                if hasattr(tweets, 'next'):
                    try: tweets = await tweets.next()
                    except: break
                else: break
        
        # ترتیب (Sorting)
        if sort_mode == "لنډ اول (Shortest)":
            all_results.sort(key=lambda x: len(x["پوسټ متن"]))
        elif sort_mode == "اوږد اول (Longest)":
            all_results.sort(key=lambda x: len(x["پوسټ متن"]), reverse=True)
            
        status_area.success("✅ پروسه په بریالیتوب سره بشپړه شوه!")
        progress_bar.progress(100)
        return all_results

    except Exception as e:
        st.error(f"ستره تېروتنه: {e}")
        return []

# 4. د ویبپاڼې اصلي جوړښت
st.markdown("<h1>🦅 د الیاس پرمختللی سکریپر</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>ستاسو شخصي وسیله د ټویټر (X) څخه د معلوماتو راټولولو لپاره</p>", unsafe_allow_html=True)
st.divider()

# --- سایډبار (تنظیمات) ---
with st.sidebar:
    st.markdown("### ⚙️ تنظیمات او کوکیز")
    
    # دلته ستاسو کوکیز په ډیفالټ ډول ایښودل شوي دي
    ct0_val = st.text_input("CT0 کوډ:", value="2620c27ebc24a02176f8d9680beb65b99a2688b40808ffa9628a8f4bb6cc16129b56e7e3b881c7d69887b51ce9e14f735ae73372ca032cdcb9e9d938fddcaf5e7fc5fff2a9ad0ec06ce56482dc3def6f", type="password")
    
    auth_val = st.text_input("Auth Token:", value="1de0ebceee7c99e2fd6af6c8e953fd341af3478c", type="password")
    
    st.markdown("---")
    search_type = st.selectbox("د پلټنې ډول", ["Latest", "Top"], index=1)
    sort_algo = st.selectbox("د فایل ترتیب", ["نارمل", "لنډ اول (Shortest)", "اوږد اول (Longest)"])
    limit_count = st.number_input("د پوسټونو تعداد (Limit)", min_value=10, max_value=1000, value=50, step=10)

# --- اصلي برخه ---
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 🔎 کلیدي کلمې یا هشټاګونه")
    query_text = st.text_area("هر هشټاګ په نوې کرښه کې ولیکئ:", height=150, value="#خلافت_یوازینی_انتخاب\n#افغانستان\n#اسلام")

with col2:
    st.markdown("### 🚀 پیل")
    st.write("د پیل لپاره لاندې تڼۍ وهئ:")
    start_btn = st.button("سکریپ پیل کړئ")

# --- د بټن منطق ---
if start_btn:
    if not ct0_val or not auth_val:
        st.error("مهرباني وکړئ کوکیز سم چیک کړئ!")
    else:
        queries = [q.strip() for q in query_text.split('\n') if q.strip()]
        
        # د Async فنکشن چلول
        results = asyncio.run(scrape_process(queries, limit_count, ct0_val, auth_val, search_type, sort_algo))
        
        if results:
            st.canvas = results # د لنډمهاله ساتلو لپاره
            st.markdown(f"### 📊 پایلې ({len(results)} پوسټونه)")
            
            # ډیټا ښودل
            st.dataframe(results, use_container_width=True)
            
            # د ډاونلوډ بټن
            json_str = json.dumps(results, ensure_ascii=False, indent=4)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            
            st.download_button(
                label="📥 فایل ډاونلوډ کړئ (JSON)",
                data=json_str,
                file_name=f"scraped_data_{timestamp}.json",
                mime="application/json"
            )
        else:
            st.info("هیڅ معلومات ونه موندل شول.")
