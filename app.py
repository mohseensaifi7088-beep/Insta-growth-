import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Auto InstaGrowth Reel Analyzer", layout="wide")

st.title("🚀 Instagram Reel Auto-Auditor & Growth Engine")
st.caption("Instagram Graph API से रील्स का डेटा सीधे फेच करें और वायरल पोटेंशियल चेक करें")

# --- साइडबार: API सेटिंग्स ---
st.sidebar.header("🔑 API Credentials")
access_token = st.sidebar.text_input("User Access Token", type="password", help="Meta Developer Console से प्राप्त टोकन")
instagram_account_id = st.sidebar.text_input("Instagram Account ID", help="Instagram Business Account ID")

# --- API से रील्स और इनसाइट्स निकालने का फंक्शन ---
def fetch_reels_data(token, account_id):
    # 1. अकाउंट की मीडिया (Reels / Videos) निकालना
    media_url = f"https://graph.facebook.com/v19.0/{account_id}/media"
    params = {
        'fields': 'id,caption,media_type,media_product_type,timestamp,like_count,comments_count,permalink',
        'access_token': token,
        'limit': 10
    }
    response = requests.get(media_url, params=params)
    if response.status_code != 200:
        st.error(f"Error fetching media: {response.json().get('error', {}).get('message', 'Unknown Error')}")
        return []
    
    media_list = response.json().get('data', [])
    reels = [item for item in media_list if item.get('media_product_type') == 'REELS']
    
    detailed_data = []

    # 2. प्रत्येक रील के इनसाइट्स (Plays, Shares, Saves, Reach) फेच करना
    for reel in reels:
        media_id = reel['id']
        insights_url = f"https://graph.facebook.com/v19.0/{media_id}/insights"
        # रील्स के मान्य मैट्रिक्स
        insights_params = {
            'metric': 'plays,reach,saved,shares,total_interactions',
            'access_token': token
        }
        ins_res = requests.get(insights_url, params=insights_params)
        
        metrics = {'plays': 0, 'reach': 0, 'saved': 0, 'shares': 0}
        if ins_res.status_code == 200:
            ins_data = ins_res.json().get('data', [])
            for item in ins_data:
                name = item['name']
                val = item['values'][0]['value']
                if name in metrics:
                    metrics[name] = val

        caption_preview = reel.get('caption', 'No Caption')[:40] + "..." if reel.get('caption') else "No Caption"

        detailed_data.append({
            'ID': media_id,
            'Caption': caption_preview,
            'Link': reel.get('permalink'),
            'Plays (Views)': metrics['plays'] if metrics['plays'] > 0 else reel.get('like_count', 0) * 10, # fallback if zero
            'Likes': reel.get('like_count', 0),
            'Comments': reel.get('comments_count', 0),
            'Shares': metrics['shares'],
            'Saves': metrics['saved'],
            'Timestamp': reel.get('timestamp')
        })
        
    return detailed_data

# --- डेटा फेच बटन ---
if st.sidebar.button("Fetch My Reels"):
    if not access_token or not instagram_account_id:
        st.warning("कृपया Access Token और Instagram Account ID दोनों दर्ज करें।")
    else:
        with st.spinner("रील्स और एनालिटिक्स लोड हो रहे हैं..."):
            data = fetch_reels_data(access_token, instagram_account_id)
            if data:
                st.session_state['reels_data'] = data
                st.success(f"{len(data)} रील्स का डेटा सफलतापूर्वक लोड हो गया!")
            else:
                st.info("कोई रील्स नहीं मिलीं या टोकन अमान्य है।")

# --- डेटा विज़ुअलाइज़ेशन और ऑडिट ---
if 'reels_data' in st.session_state and st.session_state['reels_data']:
    df = pd.DataFrame(st.session_state['reels_data'])
    
    st.subheader("📋 हालिया रील्स का ओवरव्यू")
    st.dataframe(df[['Caption', 'Plays (Views)', 'Likes', 'Comments', 'Shares', 'Saves', 'Link']], use_container_width=True)
    
    # विश्लेषण के लिए रील सेलेक्ट करें
    st.divider()
    st.subheader("🔍 किसी विशिष्ट रील का डीप-डाइव ऑडिट")
    
    selected_reel_idx = st.selectbox(
        "विश्लेषण के लिए रील चुनें:",
        options=range(len(df)),
        format_func=lambda i: f"{df.iloc[i]['Caption']} (Views: {df.iloc[i]['Plays (Views)']})"
    )
    
    selected = df.iloc[selected_reel_idx]
    
    views = max(selected['Plays (Views)'], 1)
    shares = selected['Shares']
    saves = selected['Saves']
    likes = selected['Likes']
    comments = selected['Comments']
    
    # रेश्यो कैलकुलेशन
    share_ratio = (shares / views) * 100
    save_ratio = (saves / views) * 100
    eng_rate = ((likes + comments + shares + saves) / views) * 100
    
    # स्कोरिंग
    score = 0
    if share_ratio >= 1.5:
        score += 40
    elif share_ratio >= 0.7:
        score += 25
    else:
        score += 10
        
    if save_ratio >= 1.0:
        score += 30
    elif save_ratio >= 0.5:
        score += 15
    else:
        score += 5
        
    if eng_rate >= 5.0:
        score += 30
    elif eng_rate >= 2.5:
        score += 15
    else:
        score += 5

    # परिणाम दिखाना
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("वायरल स्कोर", f"{score} / 100")
    c2.metric("शेयर अनुपात (Share Ratio)", f"{share_ratio:.2f}%")
    c3.metric("सेव अनुपात (Save Ratio)", f"{save_ratio:.2f}%")
    c4.metric("एंगेजमेंट रेट", f"{eng_rate:.2f}%")
    
    st.divider()
    st.subheader("📌 इस रील के लिए सुझाव:")
    
    if share_ratio < 0.7:
        st.warning("⚠️ **कम शेयर्स:** रील में री-शेयर करने लायक एलिमेंट (रिलेटेबल जोक्स, चौंकाने वाली जानकारी या ट्रेंडिंग ओपिनियन) कम है। सीटीए (Call To Action) दें: *'अपने उस दोस्त को शेयर करें जिसे इसकी ज़रूरत है' ।*")
    else:
        st.success("✅ **मजबूत शेयर पोटेंशियल:** इस रील को लोग दूसरों को भेज रहे हैं, जिससे इंस्टाग्राम इसे गैर-फॉलोअर्स को रिकमेंड करेगा।")
        
    if save_ratio < 0.5:
        st.warning("⚠️ **कम सेव्स:** यह रील 'वन-टाइम वॉच' जैसी है। इसमें ऐसी वैल्यू जोड़ें (जैसे गाइड, लिस्ट या रेसिपी) जिसे लोग भविष्य के लिए सेव करना चाहें।")
    else:
        st.success("✅ **हाई वैल्यू कंटेंट:** अच्छा सेव रेट यह संकेत देता है कि कंटेंट बहुत काम का है।")
      
