import machine, onewire, ds18x20, time #匯入類別、函式...等， onewire == 協議連接器件
import sh1106
import network #匯入網路模組
import urequests as requests #匯入模組並別名，以便更好呼叫
from machine import Pin, ADC, I2C #machine.Pin -> Pin ，machine.ADC -> ADC，machine.I2C -> I2C

# 設定可變電阻腳位
hear_beat = ADC(Pin(34))
blood_oxygen = ADC(Pin(35))
body_temperature = ADC(Pin(36))
hear_beat.atten(ADC.ATTN_11DB) #減弱ADC為11分貝 用以適應電壓
blood_oxygen.atten(ADC.ATTN_11DB) 
body_temperature.atten(ADC.ATTN_11DB) 

# 設定 OLED 顯示器
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000) #建立SoftI2C類別物件
display = sh1106.SH1106_I2C(128, 64, i2c, Pin(16), 0x3c) #建立display物件，1、2為OLED模組的像素，3為I2C的物件名稱，4為顯示器編號。
display.sleep(False) #禁止休眠
display.fill(0) #清除螢幕資訊
display.text('Connected', 0, 0, 1) #(連接的將欲輸入文字存入記憶體
display.show() #將存入的文字輸出在螢幕上

# 設定 ThingSpeak 網址、金鑰
url = "http://api.thingspeak.com/update"
api_key = ""

# 設定 wifi SSID 名稱、wifi 密碼與伺服器網址
WIFI_SSID = ''
WIFI_PASSWORD = ''

# 建立 wifi 連線
wifi = network.WLAN(network.STA_IF) #創建站內WiFi接口，此接口為network.STA_IF
wifi.active(True) #True 來激活網絡接口
wifi.connect(WIFI_SSID, WIFI_PASSWORD) #連接到 WiFi 網絡，網路名稱與密碼
while True: #無限迴圈
    if not wifi.isconnected(): #是否成功連接WIFI(回傳布林值)
        # print('connecting to wifi...')
        display.fill(0)   #清除螢幕資訊
        display.text('Connecting', 10, 10)   #(正在連接)將欲輸入文字存入記憶體
        display.text('Wifi...', 10, 20)      #(Wifi...)將欲輸入文字存入記憶體
        display.show() #將存入的文字輸出在螢幕上
        time.sleep(1) #延遲()秒
    else:
        # print('wifi connected!')
        display.fill(0)   #清除螢幕資訊
        display.text('Wifi...', 10, 10)   #()Wifi...將欲輸入文字存入記憶體(字串、X的起始位置、Y的起始位置)
        display.show() #將存入的文字輸出在螢幕上

start_time = time.time()  #傳回開機後秒數
last_write_time = 0 
while True: #無限迴圈
  ds_sensor.convert_temp() #獲取溫度量值並轉換單位'
  time.sleep_ms(4250) #延遲()毫秒
  time.sleep_ms(750) #延遲()毫秒 
  for rom in roms: #roms == 掃描結果陣列
    tempture = ds_sensor.read_temp(rom) #回傳溫度量值
    current_time = time.time() - start_time
    print(f"{current_time} sec\n  {tempture}") #輸出格式化
    
    hb = hear_beat.read() / 3200 * 80 #讀取內容後解析為字典
    bo = blood_oxygen.read() / 3000 * 117
    bt = body_temperature.read() / 2300 * 38
    print(f"beat: {hb},    oxygen: {bo},    temperature: {bt}") #回傳格式化心跳、血液、溫度
    
    display.fill(0) #清除螢幕資訊
    display.text(str(current_time) + " sec", 5, 5, 1) #將欲輸入文字存入記憶體
    display.text(str(tempture) + "C", 5, 20, 1) #將欲輸入文字存入記憶體 
    display.show() #將存入的文字輸出在螢幕上
    
    if last_write_time == 0 or current_time - last_write_time >= 15:
        query = f"{url}?api_key={api_key}&field1={tempture}" #格式化連結中內容
        display.text("sending data...", 5, 35, 1) #(發送資料...)將欲輸入文字存入記憶體
        display.show() #將存入的文字輸出在螢幕上
        resp = requests.get(query) #函數發送並請求到指定連結
        print("debug: query", query, resp.text) #輸出(調試：查詢)(格式化連結中內容)(提取http協定處理後訊息)
        if resp.status_code == 200: #獲取網頁狀態碼，並看是否為200(正常)
            print(resp.text) #輸出(提取http協定處理後訊息)
            display.text("OK", 5, 50, 1) #將欲輸入文字存入記憶體
            last_write_time = time.time() - start_time
        else:
            print('status_code', resp.status_code) #輸出狀碼為...
            display.text(f"ERROR: {resp.status_code}", 5, 50, 1) #將欲輸入文字存入記憶體(格式化(error:{網頁狀態碼}))
        display.show() #將存入的文字輸出在螢幕上
  time.sleep_ms(4250) #延遲()毫秒
