import streamlit as st
import asyncio
import json
import re
from twikit import Client
from datetime import datetime

# --- د پاڼې تنظیمات ---
st.set_page_config(
    page_title="د الیاس سکریپر - آنلاین نسخه",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- مرستندویه فنکشنونه ---
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
    # کوکیز تنظیمول
    client.set_cookies({"ct0": ct0, "auth_token": auth_token})
    
    all_results = []
    seen_content_hashes = set()
    global_count = 0
    status_text = st.empty()
    progress_bar = st.progress(0)

    try:
        for q_idx, query in enumerate(queries):
            if global_count >= limit: break
            
            status_text.text(f"🔍 لټون روان دی: {query}...")
            
            try:
                tweets = await client.search_tweet(query, product=post_type, count=limit)
            except Exception as e:
                st.error(f"Error searching {query}: {e}")
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
                        "PostNo": str(global_count),
                        "MyPost": clean_text,
                        "Tags": ", ".join(tags)
                    }
                    all_results.append(post_obj)
                    
                    # پرمختګ ښودل
                    progress = min(global_count / limit, 1.0)
                    progress_bar.progress(progress)

                if global_count >= limit: break
                
                if hasattr(tweets, 'next'):
                    try: tweets = await tweets.next()
                    except: break
                else: break
        
        # ترتیب (Sorting)
        if sort_mode == "Shortest First":
            all_results.sort(key=lambda x: len(x["MyPost"]))
        elif sort_mode == "Longest First":
            all_results.sort(key=lambda x: len(x["MyPost"]), reverse=True)
            
        # شمېرې سمول
        for idx, item in enumerate(all_results):
            item["PostNo"] = str(idx + 1)
            
        status_text.text("✅ پروسه بشپړه شوه!")
        progress_bar.progress(100)
        return all_results

    except Exception as e:
        st.error(f"ستره تېروتنه: {e}")
        return []

# --- د ویبپاڼې ډیزاین (GUI) ---
st.title("🚀 د الیاس د سکریپ کولو آنلاین سیسټم")

# سایډبار (کیڼ اړخ ته تنظیمات)
with st.sidebar:
    st.header("🔑 د کوکیز مدیریت")
    ct0_val = st.text_input("CT0 کوډ:", value="", type="password")
    auth_val = st.text_input("Auth Token:", value="", type="password")
    
    st.markdown("---")
    st.header("⚙️ تنظیمات")
    search_type = st.selectbox("د پلټنې ډول", ["Latest", "Top"])
    sort_algo = st.selectbox("ترتیب (Sort)", ["None", "Shortest First", "Longest First"])
    limit_count = st.number_input("د پوسټونو تعداد", min_value=10, max_value=500, value=50)

# اصلي برخه
st.subheader("🔎 دلته خپل هشټاګونه ولیکئ")
query_text = st.text_area("هر هشټاګ په نوې کرښه کې ولیکئ:", "#خلافت_یوازینی_انتخاب\n#افغانستان")

col1, col2 = st.columns([1, 2])

with col1:
    start_btn = st.button("پیل کړئ (Start Scraping)", type="primary")

# کله چې بټن ووهل شي
if start_btn:
    if not ct0_val or not auth_val:
        st.warning("مهرباني وکړئ لومړی CT0 او Auth Token دننه کړئ!")
    else:
        queries = [q.strip() for q in query_text.split('\n') if q.strip()]
        
        # د Async فنکشن چلول
        results = asyncio.run(scrape_process(queries, limit_count, ct0_val, auth_val, search_type, sort_algo))
        
        if results:
            st.success(f"مبارک! {len(results)} پوسټونه پیدا شول.")
            
            # ډیټا ښودل
            st.dataframe(results)
            
            # د ډاونلوډ بټن جوړول
            json_str = json.dumps(results, ensure_ascii=False, indent=4)
            st.download_button(
                label="📥 فایل ډاونلوډ کړئ (JSON)",
                data=json_str,
                file_name="scraped_data.json",
                mime="application/json"
            )
        else:
            st.warning("هیڅ معلومات ونه موندل شول یا تېروتنه رامنځته شوه.")
