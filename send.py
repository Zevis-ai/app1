import requests
import time
import random
from datetime import datetime

url = "https://7103.api.greenapi.com/waInstance7103140486/sendPoll/afde5c96290a4c3d86acb7c65837ab46014367002ba042529e"
headers = {
    'Content-Type': 'application/json'
}

# רשימת מסרים אקראיים
messages = [
    "אני אוהב אותך אבא", 
    "נושעתי", 
    "הישועה קרובה", 
    "תודה לה׳"
]

# מספר הימים לשליחה
days = 40
current_day = 1  # ספירת יום ראשונה

while current_day <= days:
    now = datetime.now()
    # נבדוק אם השעה היא 7:30 בבוקר
    if now.hour == 7 and now.minute == 30:
        # בחירת מסר אקראי
        random_message = random.choice(messages)
        
        # יצירת הודעה עם מספר היום והמסר האקראי
        payload = {
            "chatId": "120363313316832573@g.us", 
            "message": f"מזמור לתודה יום {current_day}", 
            "multipleAnswers": False, 
            "options": [
                {"optionName": f"קראתי {random_message}"},
                {"optionName": "עדיין לא"}
            ]
        }
        
        print(f"[{datetime.now()}] שולח הודעה ליום {current_day}...")
        # שליחת הבקשה
        response = requests.post(url, json=payload, headers=headers)
        print(f"[{datetime.now()}] תגובה מהשרת: {response.text.encode('utf8')}")

        # התקדמות ליום הבא
        current_day += 1
        
        # המתנה של יום שלם (24 שעות) לפני שליחה נוספת
        print(f"[{datetime.now()}] המתנה ל-24 שעות עד לשליחה הבאה.")
        time.sleep(24 * 60 * 60)  
    else:
        # הדפסת הודעה כל דקה כדי להראות שהקוד ממתין לבדיקה חוזרת של השעה
        print(f"[{datetime.now()}]  .הקד דועב תפסונ הקידבל ןיתממ .03:7 הניא העשה")
        time.sleep(60)
