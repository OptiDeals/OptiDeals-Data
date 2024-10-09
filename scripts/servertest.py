import requests

def check_server():
    url = "http://172.30.1.6:9091"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        print(f"Server is reachable. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to reach the server: {e}")

if __name__ == "__main__":
    check_server()
