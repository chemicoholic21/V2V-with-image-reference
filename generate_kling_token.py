import time
import jwt

# Keys provided by user
ACCESS_KEY = "A3G4tbHnHYDyaTeQETbLYJH9RmFT8fmJ"
SECRET_KEY = "TTFdbLynPLdGgAGpQFtA9gGMmgydbart"

def generate_jwt(ak, sk):
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": ak,
        "exp": int(time.time()) + 1800, # 30 mins validity
        "nbf": int(time.time()) - 5
    }
    token = jwt.encode(payload, sk, algorithm="HS256", headers=headers)
    return token

if __name__ == "__main__":
    token = generate_jwt(ACCESS_KEY, SECRET_KEY)
    print("\n" + "="*60)
    print("KLING AI JWT TOKEN (Valid for 30 mins)")
    print("="*60)
    print(token)
    print("="*60 + "\n")
