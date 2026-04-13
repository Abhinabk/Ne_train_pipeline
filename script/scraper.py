import requests
from fake_useragent import UserAgent
from pathlib import Path


# create a session with changing headers
def create_session():
    ua = UserAgent(platforms="desktop")
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


def fetch(train_no: str, train_name: str, time: str, path: Path) -> None:
    """Creates a request session fetches the train based on train_no then saves it to path"""
    url = f"https://etrain.info/train/{train_name}-{train_no}/history?d={time}"
    print(url)

    try:
        session = create_session()
        response = session.get(url, timeout=15, allow_redirects=False)

        print("Status:", response.status_code)  # 301/302 = redirect
        if response.status_code in (300, 301):
            print(
                "[WARN][REDIRECTION] Location:", response.headers.get("Location")
            )  # where it's sending you
        response.raise_for_status()  # will raise the exception if bad status
        # Save the raw HTML
        with open(
            f"{path}",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(response.text)

        # print(f"HTML successfully saved to {path}/{train_name}_{train_no}.html")

    except Exception as e:
        print(f"Error fetching {train_name}-{train_no}: {e}")
        raise
