from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
from app.db import Posts, create_db_and_tables, get_async_session
from app.images import imagekit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
import shutil
import os
import tempfile


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    session: AsyncSession = Depends(get_async_session)
):
    temp_file_path = None
    try:
        # Create temp file for upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        # Upload to ImageKit
        upload_result = imagekit.upload_file(
            file=open(temp_file_path, "rb"),
            file_name=file.filename,
            options=UploadFileRequestOptions(
                use_unique_file_name=True,
                tags=["backend-upload"]
            )
        )

        # Check upload success
        if upload_result.response.http_status_code == 200:
            uploaded_url = upload_result.response.url
            uploaded_name = upload_result.response.name

            post = Posts(
                caption=caption,
                url=uploaded_url,
                file_type="video" if file.content_type.startswith("video/") else "image",
                file_name=uploaded_name
            )

            session.add(post)
            await session.commit()
            await session.refresh(post)
            return post
        else:
            raise HTTPException(status_code=500, detail="ImageKit upload failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        file.file.close()


@app.get("/feed")
async def get_feed(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Posts).order_by(Posts.created_at.desc()))
    posts = [row[0] for row in result.all()]

    posts_data = [
        {
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat()
        }
        for post in posts
    ]

    return {"posts": posts_data}
