from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from pybitget import Client
import sqlite3

app = FastAPI()
class UserApiKey(BaseModel):
    userId: int
    apikey: str
    apisecret: str
    apiphrase: str
    risk: float
    posCount: int
    percent: int
    leverage: int
class AuthData(BaseModel):
    api_key: str
    secret_key: str
    passphrase: str
def create_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS UsersApiKey (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        userId INTEGER,
        apikey TEXT,
        apisecret TEXT,
        apiphrase TEXT,
        risk REAL,
        posCount INTEGER,
        percent INTEGER,
        leverage INTEGER
    )
    ''')
    conn.commit()
    conn.close()
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,  -- Исправлено с pass на password
            uid TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'inactive'
        )
    ''')
    conn.commit()
    conn.close()

# Инициализируем базу данных
init_db()
create_table()
@app.post("/get-balance/")
async def get_balance(auth_data: AuthData):
    try:
        client = Client(auth_data.api_key, auth_data.secret_key, auth_data.passphrase)

        balance_info = client.mix_get_accounts(productType='UMCBL')

        if not balance_info:
            raise HTTPException(status_code=404, detail="Balance information not found")

        return balance_info

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
class User(BaseModel):
    username: str
    password: str
    uid: str
class UserLogin(BaseModel):
    username: str
    password: str
# POST метод для регистрации@app.post("/register")
@app.post("/register")
def register_user(user: User):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (user.username,))
    existing_user = cursor.fetchone()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    cursor.execute("INSERT INTO users (username, password, uid, status) VALUES (?, ?, ?, ?)",
                   (user.username, user.password, user.uid, "inactive"))
    conn.commit()
    conn.close()
    return {"message": "User registered successfully. Status is inactive."}

# Авторизация пользователя
@app.post("/login")
def login_user(user: UserLogin):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, status FROM users WHERE username = ? AND password = ?", (user.username, user.password))
    db_user = cursor.fetchone()
    
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    if db_user[2] == "inactive":
        raise HTTPException(status_code=403, detail="User is inactive")
    
    conn.close()
    return {"id": db_user[0], "username": db_user[1], "status": db_user[2]}

# Получение всех неактивных пользователей
@app.get("/users/inactive")
def get_inactive_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, uid FROM users WHERE status = 'inactive'")
    inactive_users = cursor.fetchall()
    conn.close()
    
    return {"inactive_users": inactive_users}
@app.post("/add_api_key")
def add_api_key(api_key: UserApiKey):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Вставляем новый API ключ в таблицу UsersApiKey
    cursor.execute("INSERT INTO UsersApiKey (userId, apikey, apisecret, apiphrase, risk, posCount, percent, leverage) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (api_key.userId, api_key.apikey, api_key.apisecret, api_key.apiphrase, api_key.risk, api_key.posCount, api_key.percent, api_key.leverage))
    conn.commit()
    conn.close()
    
    return {"message": "API key added successfully."}
# Изменение статуса пользователя на active по ID
@app.put("/users/{user_id}/activate")
def activate_user(user_id: int):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    cursor.execute("UPDATE users SET status = 'active' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return {"message": f"User with ID {user_id} activated successfully."}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

