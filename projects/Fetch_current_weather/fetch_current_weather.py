import requests

# ============ 配置区 ============
API_KEY = "557bc2e0d44e94224ed43e2dfc426c62"
COUNTRY = "CN"
# =================================

def get_weather_by_city(city_name: str):
    url = "http://api.openweathermap.org//data/2.5/weather"
    params = {
        "q": f"{city_name},{COUNTRY}",
        "appid": API_KEY,
        "units": "metric",    # 摄氏度
        "lang": "zh_cn"       # 中文天气描述
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        return data
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    city = input("请输入城市名：").strip()
    result = get_weather_by_city(city)

    if result.get("cod") == 200:
        print("\n======= 天气信息 =======")
        print(f"城市：{result['name']}")
        print(f"天气：{result['weather'][0]['description']}")
        print(f"当前温度：{result['main']['temp']} ℃")
        print(f"体感温度：{result['main']['feels_like']} ℃")
        print(f"最低温：{result['main']['temp_min']} ℃")
        print(f"最高温：{result['main']['temp_max']} ℃")
        print(f"湿度：{result['main']['humidity']} %")
        print(f"气压：{result['main']['pressure']} hPa")
        print(f"风速：{result['wind']['speed']} m/s")
    else:
        print(f"查询失败：{result}")