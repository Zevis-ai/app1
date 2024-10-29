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
        .main {
            direction: rtl;
            text-align: right;
        }
        .stButton>button {
            width: 100%;
            margin: 5px 0;
            border-radius: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #45a049;
            transform: scale(1.02);
        }
        .css-1d391kg {
            padding: 2rem 1rem;
        }
        .metric-card {
            background-color: #f1f1f1;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .st-emotion-cache-1wivap2 {
            direction: rtl;
        }
        .custom-tab {
            background-color: #e6f3ff;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# טעינת משתני הסביבה
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

# הוספת משתנה מצב למערכת
if 'system_active' not in st.session_state:
    st.session_state.system_active = False
if 'next_scheduled_time' not in st.session_state:
    st.session_state.next_scheduled_time = None

# בתחילת האפליקציה, נאתחל את הערך אם הוא לא קיים
if 'scheduled_time' not in st.session_state:
    st.session_state.scheduled_time = datetime.strptime("00:00:00", "%H:%M:%S").time()

def calculate_next_run():
    """חישוב הזמן הבא לשליחה"""
    now = datetime.now()
    scheduled_time = datetime.strptime(str(st.session_state.scheduled_time), "%H:%M:%S").time()
    next_run = datetime.combine(now.date(), scheduled_time)
    
    if now.time() >= scheduled_time:
        next_run += timedelta(days=1)
    
    return next_run

def check_and_send():
    """בדיקה ושליחת הודעות אוטומטית"""
    if not st.session_state.system_active:
        return
    
    now = datetime.now()
    if st.session_state.next_scheduled_time and now >= st.session_state.next_scheduled_time:
        send_message()
        st.session_state.next_scheduled_time = calculate_next_run()
        save_to_file()


def save_to_file():
    data = {
        'next_scheduled_time': st.session_state.next_scheduled_time.strftime("%Y-%m-%d %H:%M:%S") if st.session_state.next_scheduled_time else None,
        'scheduled_time': st.session_state.scheduled_time.strftime("%H:%M:%S") if st.session_state.scheduled_time else None
    }
    with open('schedule_data.json', 'w', encoding='utf-8') as f:
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
            st.session_state.next_scheduled_time = datetime.fromisoformat(data['next_scheduled_time']) if data.get('next_scheduled_time') else None
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

🌟 הלל בן חמדה
📚 הצלחה בלימודים

🌟 נתנאל איתמר בן מירה
💍 זיווג טוב ומתאים

🌟 נחום זאב בן מרים
📚 הצלחה בלימודים

🌟 אריאל בן סיגלית
💍 זיווג טוב ומתאים

🌟 שי בן שירה
💍 זיווג טוב ומתאים

🌟 משה בן רֵנָה
💍 זיווג טוב ומתאים

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
st.title("🙏 מערכת מזמור לתודה")

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
            st.success(f"ההודעה נשלה בהצלחה! תגובת השרת: {response.text}")
    
    with col2:
        if st.button("שליחת תזכורת"):
            response = send_message("reminder", custom_message=custom_message if custom_message else None)
            st.success(f"תזכורת נשלחה בהצלח! תגובת השרת: {response.text}")

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