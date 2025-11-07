from fastapi import FastAPI, HTTPException
from app.schemas import PostCreate
from app.db import Posts, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager


# --- Startup / Shutdown lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


# ✅ Attach lifespan to FastAPI
app = FastAPI(lifespan=lifespan)


# --- In-memory placeholder (for now) ---
text_posts = {1: {"title": "New Post", "content": "cool test post"}}


@app.get("/posts")
def get_all_posts():
    return text_posts


@app.get("/posts/{id}")
def get_post(id: int):
    # ❌ status_Code → ✅ status_code
    if id not in text_posts:
        raise HTTPException(status_code=404, detail="Post not found")
    return text_posts.get(id)


@app.post("/posts")
def create_post(post: PostCreate):
    new_post = {"title": post.title, "content": post.content}
    text_posts[max(text_posts.keys()) + 1] = new_post
    return new_post
