from fastapi import FastAPI
import sqlite3

app = FastAPI()

# Create database connection
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/user/{id}")
def get_user(id):
    cursor.execute(f"SELECT * FROM users WHERE id = {id}")
    return cursor.fetchone() 