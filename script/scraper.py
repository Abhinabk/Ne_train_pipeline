import requests
from fake_useragent import UserAgent


# create a session with fake headers
def create_session():
    ua = UserAgent()
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://etrain.info/",
        }
    )
    return session


# make a get request
def fetch(train_info="Dbrt-Ndls-Rajdhani-12423", time="1y"):
    url = f"https://etrain.info/train/{train_info}/history?d={time}"
    try:
        session = create_session()
        response = session.get(url, timeout=15)
        response.raise_for_status()  # will raise the exception if bad status
        # Save the raw HTML
        with open(
            f"data/raw/etrain_raw_{train_info.split('-')[-1]}.html",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(response.text)
        print(f"HTML successfully saved to data/raw/etrain_raw_{train_info.split('-')[-1]}.html")

    except Exception as e:
        print(f"Error fetching {e}")
        exit()


if __name__ == "__main__":
    html = fetch("Dbrt-Ndls-Rajdhani-12423", "1y")
    if html:
        print("\n✅ Fetch completed successfully. Ready for parsing!")
