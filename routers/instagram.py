import tempfile
from contextlib import ExitStack
from threading import Thread

from fastapi import APIRouter, File, Form, Query, UploadFile
from pydantic import BaseModel

from . import (WaitingException, add_photos, check_url, do_nothing_coro,
               get_last_post, get_links_by_scroll, prepare_chrome,
               write_temp_files)

insta_router = APIRouter()


class GetPhotosResponse(BaseModel):
    urls: list[str]


@insta_router.get("/getPhotos")
async def get_photos(
    username: str = Query(..., description="Insta user we want to get photo urls"),
    max_count: int = Query(
        ..., description="Number of last photos we want to get urls"
    ),
    login_username: str = Query(
        ..., description="We need to login Instagram, it's username for our account"
    ),
    login_password: str = Query(
        ..., description="We need to login Instagram, it's password for our account"
    ),
) -> GetPhotosResponse:
    chrome = await prepare_chrome(login_username, login_password)
    url = f"https://www.instagram.com/{username}"
    chrome.get(url)
    if not await check_url(chrome, url):
        raise WaitingException
    links = await get_links_by_scroll(chrome, max_count)
    chrome.close()
    chrome.quit()
    return {"urls": links}


class PostPhotosResponse(BaseModel):
    postURL: str


@insta_router.post("/postPhotos")
async def post_photos(
    login_username: str = Form(
        ..., description="We need to login Instagram, it's username for our account"
    ),
    login_password: str = Form(
        ..., description="We need to login Instagram, it's password for our account"
    ),
    caption: str = Form(..., description="Caption for new post"),
    files: list[UploadFile] = File(..., description="List of images for new post"),
) -> PostPhotosResponse:
    files_bytes = [await file.read() for file in files]
    with ExitStack() as stack:
        images = [
            stack.enter_context(
                tempfile.NamedTemporaryFile(suffix="." + file.filename.split(".")[-1])
            )
            for file in files
        ]
        thread = Thread(target=write_temp_files, args=(images, files_bytes))
        thread.start()
        chrome = await prepare_chrome(login_username, login_password)
        while thread.is_alive():
            await do_nothing_coro()
        await add_photos(chrome, caption, [image.name for image in images])
        result = await get_last_post(chrome)
        chrome.close()
        chrome.quit()
    return {"postURL": result}
