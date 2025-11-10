import requests
import threading
import time
from telegram import Bot
from telegram.error import TelegramError

# إعدادات البوت - تم التحديث بالبيانات الجديدة
TELEGRAM_BOT_TOKEN = '7738659128:AAGK6Xv0q-4hh3S1mRPzSc7Ye7iDNC-_uhU'
TELEGRAM_CHAT_ID = '6371768226'

# تهيئة بوت التليجرام
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def test_proxy(proxy, proxy_type='http'):
    """
    فحص البروكسي للتأكد من عمله
    """
    try:
        # تنظيف البروكسي من أي فراغات
        proxy = proxy.strip()
        
        proxies = {
            'http': f'{proxy_type}://{proxy}',
            'https': f'{proxy_type}://{proxy}'
        }
        
        # اختبار الاتصال بموقع موثوق
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxies,
            timeout=15
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, None
            
    except Exception as e:
        return False, None

def read_proxies_from_file(filename):
    """
    قراءة البروكسيات من ملف txt
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            proxies = [line.strip() for line in file if line.strip() and not line.startswith('#')]
        return proxies
    except Exception as e:
        print(f"خطأ في قراءة الملف: {e}")
        return []

def send_telegram_message(message):
    """
    إرسال رسالة عبر تليجرام
    """
    try:
        # إذا كانت الرسالة طويلة، نقسمها
        if len(message) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for part in parts:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=part)
                time.sleep(1)
        else:
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        return True
    except TelegramError as e:
        print(f"خطأ في إرسال الرسالة: {e}")
        return False

def check_proxy_with_retry(proxy, max_retries=2):
    """
    فحص البروكسي مع إعادة المحاولة
    """
    for attempt in range(max_retries):
        is_working, info = test_proxy(proxy)
        if is_working:
            return True, info
        time.sleep(1)
    return False, None

def check_and_report_proxies():
    """
    فحص البروكسيات وإرسال التقرير
    """
    try:
        proxies = read_proxies_from_file('proxies.txt')
        
        if not proxies:
            send_telegram_message("❌ لم يتم العثور على بروكسيات في الملف proxies.txt")
            return
        
        working_proxies = []
        total_count = len(proxies)
        
        send_telegram_message(f"🚀 بدء فحص {total_count} بروكسي...")
        
        current = 0
        for proxy in proxies:
            current += 1
            print(f"🔍 فحص البروكسي {current}/{total_count}: {proxy}")
            
            # فحص البروكسي
            is_working, info = check_proxy_with_retry(proxy)
            
            if is_working:
                working_proxies.append(proxy)
                status_msg = f"✅ {current}/{total_count} - يعمل: {proxy}"
            else:
                status_msg = f"❌ {current}/{total_count} - لا يعمل: {proxy}"
            
            print(status_msg)
            
            # إرسال تحديث كل 10 بروكسيات
            if current % 10 == 0:
                send_telegram_message(f"📊 التقدم: {current}/{total_count} - عاملة: {len(working_proxies)}")
            
            # وقت انتظار بين كل فحص
            time.sleep(2)
        
        # إرسال التقرير النهائي
        report = f"""
📊 **تقرير فحص البروكسيات**

✅ **البروكسيات العاملة:** {len(working_proxies)}
❌ **البروكسيات غير العاملة:** {total_count - len(working_proxies)}
📈 **نسبة النجاح:** {(len(working_proxies)/total_count)*100:.1f}%

📋 **البروكسيات العاملة:**
{' | '.join(working_proxies) if working_proxies else 'لا توجد بروكسيات عاملة'}
        """
        
        send_telegram_message(report)
        
        # حفظ البروكسيات العاملة في ملف
        if working_proxies:
            with open('working_proxies.txt', 'w', encoding='utf-8') as file:
                for proxy in working_proxies:
                    file.write(proxy + '\n')
            
            # إرسال ملف البروكسيات العاملة
            with open('working_proxies.txt', 'rb') as file:
                bot.send_document(
                    chat_id=TELEGRAM_CHAT_ID,
                    document=file,
                    filename='working_proxies.txt',
                    caption='📁 ملف البروكسيات العاملة'
                )
        
        send_telegram_message("🎉 تم الانتهاء من الفحص بنجاح!")
        
    except Exception as e:
        error_msg = f"❌ حدث خطأ أثناء الفحص: {str(e)}"
        send_telegram_message(error_msg)
        print(error_msg)

def main_menu():
    """
    القائمة الرئيسية
    """
    while True:
        print("\n" + "="*50)
        print("🛠️ نظام فحص البروكسيات")
        print("="*50)
        print("1 - بدء فحص البروكسيات")
        print("2 - اختبار اتصال التليجرام")
        print("3 - الخروج")
        
        choice = input("اختر الخيار: ").strip()
        
        if choice == '1':
            check_and_report_proxies()
        elif choice == '2':
            try:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="✅ اختبار اتصال ناجح!")
                print("✅ تم إرسال رسالة الاختبار بنجاح")
            except Exception as e:
                print(f"❌ فشل اختبار الاتصال: {e}")
        elif choice == '3':
            print("👋 مع السلامة!")
            break
        else:
            print("❌ خيار غير صحيح")

if __name__ == "__main__":
    print("🔧 تم تحميل الإعدادات:")
    print(f"🤖 بوت التليجرام: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"💬 آيدي المحادثة: {TELEGRAM_CHAT_ID}")
    
    # اختبار الاتصال الأولي
    try:
        bot_info = bot.get_me()
        print(f"✅ البوت يعمل: @{bot_info.username}")
    except Exception as e:
        print(f"❌ خطأ في الاتصال بالبوت: {e}")
        exit()
    
    main_menu()