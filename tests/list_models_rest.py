import os
import requests

def main():
    key = os.getenv('GOOGLE_API_KEY')
    if not key:
        # try loading from .env file in project root
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('GOOGLE_API_KEY='):
                        key = line.split('=', 1)[1].strip()
                        break
        except FileNotFoundError:
            pass
    if not key:
        print('GOOGLE_API_KEY not set in environment or .env')
        return
    url = f'https://generativelanguage.googleapis.com/v1beta/models?key={key}'
    resp = requests.get(url)
    print('status', resp.status_code)
    print(resp.text)

if __name__ == '__main__':
    main()
