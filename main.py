import os
import secrets
import string

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import create_engine, text

# 从环境变量读取配置，读不到就用本地默认值
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///shortlink.db")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

# Neon 给的地址以 postgresql:// 开头，要告诉 SQLAlchemy 用 psycopg 这个驱动
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI(title="ShortLink")
ALPHABET = string.ascii_letters + string.digits


def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS links (
                code VARCHAR(16) PRIMARY KEY,
                url TEXT NOT NULL,
                clicks INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))


init_db()


def generate_code(conn, length: int = 6) -> str:
    while True:
        code = "".join(secrets.choice(ALPHABET) for _ in range(length))
        row = conn.execute(
            text("SELECT 1 FROM links WHERE code = :code"), {"code": code}
        ).fetchone()
        if row is None:
            return code


class ShortenRequest(BaseModel):
    url: HttpUrl


@app.post("/shorten")
def shorten(req: ShortenRequest):
    with engine.begin() as conn:
        code = generate_code(conn)
        conn.execute(
            text("INSERT INTO links (code, url) VALUES (:code, :url)"),
            {"code": code, "url": str(req.url)},
        )
    return {"code": code, "short_url": f"{BASE_URL}/{code}"}


@app.get("/stats/{code}")
def stats(code: str):
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT code, url, clicks, created_at FROM links WHERE code = :code"),
            {"code": code},
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="短链接不存在")
    return dict(row._mapping)


@app.get("/{code}")
def redirect(code: str):
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT url FROM links WHERE code = :code"), {"code": code}
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="短链接不存在")
        conn.execute(
            text("UPDATE links SET clicks = clicks + 1 WHERE code = :code"),
            {"code": code},
        )
    return RedirectResponse(row.url, status_code=307)