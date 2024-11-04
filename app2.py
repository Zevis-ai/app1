import streamlit as st
import requests
import time
import random
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os
import json

# קונפיגורציה בסיסית של streamlit
st.set_page_config(
    page_title="מערכת מזמור לתודה",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.google.com',
        'About': 'מערכת מזמור לתודה - גרסה 2.0'
    }
)

# סטיילינג משופר
st.markdown("""
    <style>
        /* עיצוב כללי */
        .main {
            direction: rtl;
            text-align: right;
            background-color: #f8f9fa;
        }
        
        /* כפתורים */
        .stButton>button {
            width: 100%;
            margin: 5px 0;
            border-radius: 15px;
            background: linear-gradient(45deg, #2196F3, #4CAF50);
            color: white;
            border: none;
            padding: 15px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 8px rgba(0,0,0,0.2);
        }
        
        /* כרטיסי מידע */
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            text-align: center;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        
        /* טיימר */
        .timer-display {
            font-size: 2.5em;
            font-weight: bold;
            color: #2196F3;
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 10px 0;
        }
        
        /* כותרות */
        h1, h2, h3 {
            color: #1a237e;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# טעינת משתני הסביה
load_dotenv()

# קבועים
API_URL = os.getenv("WHATSAPP_API_URL")
GROUP_ID = os.getenv("WHATSAPP_GROUP_ID")
DEFAULT_MESSAGES = ["אני אוהב אותך אבא", "נושעתי", "הישועה קרובה", "תודה לה׳"]
HEADERS = {'Content-Type': 'application/json'}

# הגדרת מצב התחלתי
if 'messages' not in st.session_state:
    st.session_state.messages = DEFAULT_MESSAGES
if 'current_day' not in st.session_state:
    st.session_state.current_day = 1
if 'last_sent' not in st.session_state:
    st.session_state.last_sent = None
if 'poll_responses' not in st.session_state:
    st.session_state.poll_responses = {}
if 'message_history' not in st.session_state:
    st.session_state.message_history = []
if 'system_active' not in st.session_state:
    st.session_state.system_active = False
if 'next_send_time' not in st.session_state:
    st.session_state.next_send_time = None

def save_to_file():
    """שמירת נתוני המערכת לקובץ"""
    data = {
        'current_day': st.session_state.current_day,
        'last_sent': st.session_state.last_sent.isoformat() if st.session_state.last_sent else None,
        'poll_responses': st.session_state.poll_responses,
        'message_history': st.session_state.message_history,
        'messages': st.session_state.messages,
        'system_active': st.session_state.system_active,
        'next_send_time': st.session_state.next_send_time.isoformat() if st.session_state.next_send_time else None
    }
    with open('mizmor_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def load_from_file():
    """טעינת נתוני המערכת מקובץ"""
    try:
        with open('mizmor_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            st.session_state.current_day = data['current_day']
            st.session_state.last_sent = datetime.fromisoformat(data['last_sent']) if data['last_sent'] else None
            st.session_state.poll_responses = data['poll_responses']
            st.session_state.message_history = data['message_history']
            st.session_state.messages = data['messages']
            st.session_state.system_active = data.get('system_active', False)
            st.session_state.next_send_time = datetime.fromisoformat(data['next_send_time']) if data.get('next_send_time') else None
    except FileNotFoundError:
        pass


def send_text_message(message):
    """שליחת הודעת טקסט פשוטה"""
    payload = {
        "chatId": GROUP_ID,
        "message": message
    }
    
    # שימוש בנקודת קצה שונה לשליחת הודעת טקסט
    text_api_url = API_URL.replace("sendPoll", "sendMessage")
    response = requests.post(text_api_url, json=payload, headers=HEADERS)
    return response

def send_message(message_type="regular", custom_message=None):
    """שליחת הודעה לקבוצה"""
    current_time = datetime.now()
    base_message = custom_message if custom_message else f"מזמור לתודה יום {st.session_state.current_day}"
    
    if message_type == "reminder":
        base_message += " - תזכורת"
    
    # שליחת הודעת טקסט לפני הסקר
    intro_message = f"""בס"ד
יום {st.session_state.current_day}
-----------------

א  מִזְמוֹר לְתוֹדָה: הָרִיעוּ לַיהוָה, כָּל-הָאָרֶץ.
ב  עִבְדוּ אֶת-יְהוָה בְּשִׂמְחָה; בֹּאוּ לְפָנָיו, בִּרְנָנָה.
ג  דְּעוּ כִּי יְהוָה, הוּא אֱלֹהִים: הוּא-עָשָׂנוּ,
 ולא (וְלוֹ) אֲנַחְנוּ עַמּוֹ,
 וְצֹאן מַרְעִיתוֹ.
ד  בֹּאוּ שְׁעָרָיו, בְּתוֹדָה--חֲצֵרֹתָיו בִּתְהִלָּה; הוֹדוּ-לוֹ, בָּרְכוּ שְׁמוֹ.
ה  כִּי-טוֹב יְהוָה, לְעוֹלָם חַסְדּוֹ; וְעַד-דֹּר וָדֹר, אֱמוּנָתוֹ.

-----------------

🌟 הלל בן חמדה
📚 הצלחה בלימודים

🌟 נתנאל איתמר בן מירה
📚 הצלחה מרובה בלימודי תכנות ובישוב הדעת

🌟 נחום זאב בן מרים
📚 הצלחה בלימודים

🌟 אריאל בן סיגלית
💍 זיווג טוב ומתאים

🌟 שי בן שירה
💍 זיווג טוב ומתאים

🌟 משה בן רֵנָה
💵 פרנסה בשפע בקלות ובשמחה

🌟 רונן בן מירה
💵 פרנסה בשפע בקלות ובשמחה

🌟 נועם יששכר בן שולמית
💍 זיווג טוב ומתאים

🌟 חגי שמעון בן שרית
💪 בריאות איתנה

🌟 מנחם בן אסתר
🏠 פרנסה טובה

🌟 איתמר בן נורית
🎓 הצלחה בכל

🌟 דוד בונים בן יעל עקא
💪 רפואה שלימה ובריאות איתנה

🌟 נתנאל (נתי) בן רונית עליזה
💵 פרנסה בשפע בקלות ובשמחה

בתוך שאר בית ישראל הזקוקים לישועה בחן בחסד וברחמים בקרוב.
-----------------"""
    send_text_message(intro_message)
    
    # המתנה קצרה בין ההודעות
    time.sleep(1)
    
    random_message = random.choice(st.session_state.messages)
    
    payload = {
        "chatId": GROUP_ID,
        "message": base_message,
        "multipleAnswers": False,
        "options": [
            {"optionName": f"קראתי {random_message}"},
            {"optionName": "עדיין לא"}
        ]
    }
    
    response = requests.post(API_URL, json=payload, headers=HEADERS)
    
    if response.status_code == 200:
        st.session_state.last_sent = current_time
        st.session_state.message_history.append({
            'timestamp': current_time.isoformat(),
            'message': base_message,
            'type': message_type
        })
        save_to_file()
    
    return response

# טעינת נתונים בהפעלה
load_from_file()

# כותרת ראשית
st.title("🙏 מערכת מזמור-לתודה")

# סרגל צד משופר
with st.sidebar:
    st.header("⚙️ הגדרות המערכת")
    
    with st.expander("🕒 הגדרות זמנים", expanded=True):
        scheduled_time = st.time_input("זמן שליחה יומי", value=datetime.strptime("07:30", "%H:%M").time())
        reminder_delay = st.number_input("שעות המתנה לתזכורת", min_value=1, value=5)
    
    with st.expander("📝 ניהול הודעות", expanded=True):
        messages_text = st.text_area("רשימת הודעות (כל שורה הודעה חדשה)", 
                                   value="\n".join(st.session_state.messages))
        if st.button("עדכון רשימת ההודעות"):
            st.session_state.messages = [msg.strip() for msg in messages_text.split("\n") if msg.strip()]
            save_to_file()
            st.success("רשימת ההודעות עודכנה!")
    
    with st.expander("⚡ פעולות מערכת", expanded=True):
        new_day = st.number_input("עדכון יום נוכחי", 
                                 min_value=1, 
                                 max_value=40, 
                                 value=st.session_state.current_day)
        
        if new_day != st.session_state.current_day:
            st.session_state.current_day = new_day
            save_to_file()
            st.success(f"היום עודכן ל-{new_day}")
        
        if st.button("איפוס המערכת"):
            st.session_state.current_day = 1
            st.session_state.last_sent = None
            st.session_state.poll_responses = {}
            st.session_state.message_history = []
            save_to_file()
            st.success("המערכת אופסה בהצלחה!")
    
    with st.expander("🤖 הפעלת מערכת", expanded=True):
        system_status = "פעילה ✅" if st.session_state.system_active else "כבויה ❌"
        st.write(f"סטטוס מערכת: {system_status}")
        
        if st.button("הפעלת/כיבוי מערכת"):
            st.session_state.system_active = not st.session_state.system_active
            if st.session_state.system_active:
                now = datetime.now()
                target_time = now.replace(hour=scheduled_time.hour, minute=scheduled_time.minute, second=0, microsecond=0)
                if now.time() >= scheduled_time:
                    target_time += timedelta(days=1)
                st.session_state.next_send_time = target_time
            else:
                st.session_state.next_send_time = None
            save_to_file()
            st.rerun()

# תצוגה ראשית
tab1, tab2, tab3 = st.tabs(["📊 סטטיסטיקה", "✉️ שליחת הודעות", "📜 היסטוריה"])

with tab1:
    # מטריקות בעיצוב משופר
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="metric-card">
                <h3>יום נוכחי</h3>
                <h2>{}/{}</h2>
            </div>
        """.format(st.session_state.current_day, 40), unsafe_allow_html=True)
    
    with col2:
        if st.session_state.last_sent:
            next_send = st.session_state.last_sent + timedelta(days=1)
            time_until = next_send - datetime.now()
            hours = int(time_until.total_seconds() // 3600)
            minutes = int((time_until.total_seconds() % 3600) // 60)
            time_display = f"{hours}:{minutes:02d}"
        else:
            time_display = "לא נשלח עדיין"
        
        st.markdown(f"""
            <div class="metric-card">
                <h3>זמן עד השליחה הבאה</h3>
                <h2>{time_display}</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        response_rate = len([r for r in st.session_state.poll_responses.values() if r == "קראתי"]) / len(st.session_state.poll_responses) * 100 if st.session_state.poll_responses else 0
        st.markdown(f"""
            <div class="metric-card">
                <h3>אחוז המשיבים</h3>
                <h2>{response_rate:.1f}%</h2>
            </div>
        """, unsafe_allow_html=True)
    
    # גרף התקדמות משופר
    progress_data = pd.DataFrame({
        'יום': range(1, st.session_state.current_day + 1),
        'משיבים': [len([r for r in st.session_state.poll_responses.values() if r == "קראתי"])] * st.session_state.current_day
    })
    
    fig = px.line(progress_data, 
                  x='יום', 
                  y='משיבים',
                  title='התקדמות המשיבים לאורך זמן',
                  template='plotly_white')
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_family="Arial",
        font_size=14
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("📤 שליחת הודעות")
    
    custom_message = st.text_area("הודעה מותאמת אישית (אופציונלי)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("שליחת הודעה מיידית"):
            response = send_message(custom_message=custom_message if custom_message else None)
            st.success(f"ההודעה נשלחה בהצלחה! תגובת השרת: {response.text}")
    
    with col2:
        if st.button("שליחת תזכורת"):
            response = send_message("reminder", custom_message=custom_message if custom_message else None)
            st.success(f"תזכורת נשלחה בהצלחה! תגובת השרת: {response.text}")

with tab3:
    st.subheader("📋 היסטוריית הודעות")
    
    if st.session_state.message_history:
        history_df = pd.DataFrame(st.session_state.message_history)
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        history_df = history_df.sort_values('timestamp', ascending=False)
        
        for _, row in history_df.iterrows():
            with st.container():
                st.markdown(f"""
                    <div style='background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin: 5px 0;'>
                        <small>{row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</small><br>
                        <strong>{row['message']}</strong><br>
                        <small>סוג: {row['type']}</small>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("אין היסטוריית הודעות")

# טבלת משיבים בתחתית
if st.session_state.poll_responses:
    st.header("📊 סטטוס משיבים")
    responses_df = pd.DataFrame(st.session_state.poll_responses.items(), columns=['משתמש', 'סטטוס'])
    st.dataframe(responses_df, use_container_width=True)

def calculate_time_until_next_send():
    """חישוב הזמן עד השליחה הבאה"""
    now = datetime.now()
    target_time = datetime.now().replace(hour=7, minute=30, second=0, microsecond=0)
    
    if now.time() >= target_time.time():
        target_time += timedelta(days=1)
    
    time_diff = target_time - now
    hours = int(time_diff.total_seconds() // 3600)
    minutes = int((time_diff.total_seconds() % 3600) // 60)
    seconds = int(time_diff.total_seconds() % 60)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

if st.session_state.system_active and st.session_state.next_send_time:
    time_until = st.session_state.next_send_time - datetime.now()
    if time_until.total_seconds() > 0:
        hours = int(time_until.total_seconds() // 3600)
        minutes = int((time_until.total_seconds() % 3600) // 60)
        seconds = int(time_until.total_seconds() % 60)
        st.markdown(f"""
            <div class="timer-display">
                זמן עד השליחה הבאה: {hours:02d}:{minutes:02d}:{seconds:02d}
            </div>
        """, unsafe_allow_html=True)
        time.sleep(1)
        st.rerun()
    else:
        # הגיע זמן השליחה
        send_message()
        # עדכון הזמן הבא
        st.session_state.next_send_time += timedelta(days=1)
        save_to_file()  # שמירת הזמן החדש
        st.rerun()