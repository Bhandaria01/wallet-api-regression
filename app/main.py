"""A small wallet API used as the system under test.

FastAPI generates the Swagger / OpenAPI spec automatically:
  - Swagger UI:   http://127.0.0.1:8000/docs
  - OpenAPI JSON: http://127.0.0.1:8000/openapi.json
"""
import os
import sqlite3
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB_PATH = os.environ.get("WALLET_DB", "wallet.db")

app = FastAPI(title="Wallet API", version="1.0.0")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, balance REAL NOT NULL DEFAULT 0)")
        db.execute("CREATE TABLE IF NOT EXISTS transactions (txn_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, type TEXT NOT NULL, amount REAL NOT NULL, status TEXT NOT NULL)")


init_db()


class UserIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class User(BaseModel):
    user_id: int
    name: str
    balance: float


class TransactionIn(BaseModel):
    type: Literal["DEPOSIT", "WITHDRAW"]
    amount: float = Field(gt=0)


class Transaction(BaseModel):
    txn_id: int
    user_id: int
    type: str
    amount: float
    status: str


@app.post("/users", response_model=User, status_code=201)
def create_user(body: UserIn):
    with get_db() as db:
        cur = db.execute("INSERT INTO users (name, balance) VALUES (?, 0)", (body.name,))
        return User(user_id=cur.lastrowid, name=body.name, balance=0)


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    with get_db() as db:
        row = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**dict(row))


@app.post("/users/{user_id}/transactions", response_model=Transaction, status_code=201)
def create_transaction(user_id: int, body: TransactionIn):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if body.type == "WITHDRAW" and body.amount > user["balance"]:
            db.execute("INSERT INTO transactions (user_id, type, amount, status) VALUES (?, ?, ?, 'FAILED')",
                       (user_id, body.type, body.amount))
            db.commit()  # save the FAILED record before raising (an exception would roll it back)
            raise HTTPException(status_code=400, detail="Insufficient balance")
        change = body.amount if body.type == "DEPOSIT" else -body.amount
        db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (change, user_id))
        cur = db.execute("INSERT INTO transactions (user_id, type, amount, status) VALUES (?, ?, ?, 'SUCCESS')",
                         (user_id, body.type, body.amount))
        return Transaction(txn_id=cur.lastrowid, user_id=user_id, type=body.type, amount=body.amount, status="SUCCESS")


@app.get("/users/{user_id}/transactions", response_model=list[Transaction])
def list_transactions(user_id: int):
    with get_db() as db:
        rows = db.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY txn_id", (user_id,)).fetchall()
    return [Transaction(**dict(r)) for r in rows]
