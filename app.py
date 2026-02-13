import streamlit as st
import asyncio
import json
import re
import random
from twikit import Client
from datetime import datetime

# ==========================================
# ۱. د پاڼې او ډیزاین تنظیمات (UI/UX)
# ==========================================
st.set_page_config(
    page_title="سکریپر پرو - الیاس عمر",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    div.stButton > button:first-child {
        background-color: #0083B8; color: white; border-radius: 12px;
        padding: 10px 24px; border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #005f85; box-shadow: 0 6px 8px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }
    .stTextInput > div > div > input { border-radius: 10px; text-align: right; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; }
    @media (prefers-color-scheme: dark) {
        [data-testid="stSidebar"] { background-color: #1e1e1e; }
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ۲. د سیشن (Session) تنظیمات
# ==========================================
DEFAULT_CT0 = "2620c27ebc24a02176f8d9680beb65b99a2688b40808ffa9628a8f4bb6cc16129b56e7e3b881c7d69887b51ce9e14f735ae73372ca032cdcb9e9d938fddcaf5e7fc5fff2a9ad0ec06ce56482dc3def6f"
DEFAULT_AUTH = "1de0ebceee7c99e2fd6af6c8e953fd341af3478c"

if 'limit_count' not in st.session_state: st.session_state.limit_count = 50
if 'search_type_label' not in st.session_state: st.session_state.search_type_label = "Latest (نوي)"
if 'sort_algo' not in st.session_state: st.session_state.sort_algo = "None"
if 'ct0' not in st.session_state: st.session_state.ct0 = DEFAULT_CT0
if 'auth' not in st.session_state: st.session_state.auth = DEFAULT_AUTH

# ==========================================
# ۳. منطقي فنکشنونه (Logic)
# ==========================================
def clean_tweet_content(text):
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def extract_hashtags(text):
    return re.findall(r'#\w+', text)

async def scrape_process(queries, limit, ct0, auth_token, post_type_label, sort_mode):
    # دلته موږ پښتو لیبل بیرته انګلیسي ته اړوو ترڅو ټویټر ونه غوسیږي
    if "Top" in post_type_label:
        real_product_type = "Top"
    else:
        real_product_type = "Latest"

    client = Client('en-US')
    try:
        client.set_cookies({"ct0": ct0, "auth_token": auth_token})
        
        all_results = []
        seen_content_hashes = set()
        global_count = 0
        
        status_placeholder = st.empty()
        bar = st.progress(0)

        for q_idx, query in enumerate(queries):
            if global_count >= limit: break
            
            status_placeholder.info(f"🔍 لټون روان دی: {query}...")
            
            # احتیاطی وقفه (Safety Delay) ترڅو 429 را نشي
            if q_idx > 0:
                await asyncio.sleep(2) 

            try:
                # دلته اوس real_product_type کاروو چې یوازې انګلیسي دی
                tweets = await client.search_tweet(query, product=real_product_type, count=limit)
            except Exception as e:
                st.error(f"Error searching {query}: {e}")
                continue

            if not tweets: continue

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
                        "PostNo": str(global_count),
                        "MyPost": clean_text,
                        "Tags": ", ".join(tags)
                    }
                    all_results.append(post_obj)
                    bar.progress(min(global_count / limit, 1.0))

                if global_count >= limit: break
                
                if hasattr(tweets, 'next'):
                    try: 
                        await asyncio.sleep(1) # بله وقفه د پاڼې اړولو پر وخت
                        tweets = await tweets.next()
                    except: break
                else: break
        
        # ترتیب (Sorting)
        if sort_mode == "Shortest First":
            all_results.sort(key=lambda x: len(x["MyPost"]))
        elif sort_mode == "Longest First":
            all_results.sort(key=lambda x: len(x["MyPost"]), reverse=True)
            
        # بیا شمېرنه
        for idx, item in enumerate(all_results):
            item["PostNo"] = str(idx + 1)
            
        status_placeholder.success("✅ پروسه بشپړه شوه!")
        bar.progress(100)
        return all_results

    except Exception as e:
        st.error(f"تېروتنه: {e}")
        return []

# ==========================================
# ۴. سایډ بار مینو
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
    st.title("د کنټرول پنل")
    st.markdown("---")
    
    selected = st.radio(
        "برخې:",
        ["📊 ډاشبورډ", "⚙️ تنظیمات", "🔐 اکاونټ/کوکیز"],
        index=0
    )
    st.markdown("---")
    st.caption("Developed by Elyas Omar")

# ==========================================
# ۵. د پاڼو محتوا
# ==========================================

# >>> لومړۍ پاڼه: ډاشبورډ <<<
if selected == "📊 ډاشبورډ":
    st.header("🚀 اصلي ډاشبورډ")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query_text = st.text_area("هشټاګونه (په هر کرښه کې یو):", "#افغانستان\n#خلافت", height=150)
    
    with col2:
        st.info(f"تعداد: {st.session_state.limit_count}")
        # یوازې د ښودلو لپاره پښتو متن، فنکشن ته به انګلیسي ځي
        display_type = "Latest (نوي)" if "Latest" in st.session_state.search_type_label else "Top (مشهور)"
        st.info(f"ډول: {display_type}")
        start_btn = st.button("پیل کړئ", use_container_width=True)

    if start_btn:
        queries = [q.strip() for q in query_text.split('\n') if q.strip()]
        results = asyncio.run(scrape_process(
            queries, 
            st.session_state.limit_count, 
            st.session_state.ct0, 
            st.session_state.auth, 
            st.session_state.search_type_label, # دلته موږ لیبل لیږو، فنکشن یې پخپله بدلوي
            st.session_state.sort_algo
        ))
        
        if results:
            st.subheader(f"📄 موندل شوي پایلې ({len(results)})")
            st.dataframe(results, use_container_width=True)
            
            json_str = json.dumps(results, ensure_ascii=False, indent=4)
            st.download_button(
                label="📥 فایل ډاونلوډ کړئ (JSON)",
                data=json_str,
                file_name=f"data_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

# >>> دوهمه پاڼه: تنظیمات <<<
elif selected == "⚙️ تنظیمات":
    st.header("⚙️ د سکریپر تنظیمات")
    
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.search_type_label = st.selectbox(
            "د لټون ډول (Search Type)",
            ["Latest (نوي)", "Top (مشهور)"],
            index=0
        )
        
        st.session_state.sort_algo = st.selectbox(
            "د پایلو ترتیب (Sort)",
            ["None (نارمل)", "Shortest First (لنډ اول)", "Longest First (اوږد اول)"],
            index=0
        )
        
    with c2:
        st.session_state.limit_count = st.number_input(
            "د پوسټونو نهایي حد (Limit)", 
            min_value=10, max_value=1000, 
            value=st.session_state.limit_count
        )

# >>> دریمه پاڼه: د اکاونټ معلومات <<<
elif selected == "🔐 اکاونټ/کوکیز":
    st.header("🔐 د ننوتلو معلومات")
    with st.expander("د کوکیز لیدل/تغیرول", expanded=True):
        st.session_state.ct0 = st.text_input("CT0 کوډ:", value=st.session_state.ct0, type="password")
        st.session_state.auth = st.text_input("Auth Token:", value=st.session_state.auth, type="password")
        if st.button("ذخیره کول"):
            st.success("معلومات تازه شول!")
