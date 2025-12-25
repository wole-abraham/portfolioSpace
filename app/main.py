from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from .auth import get_current_user
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import HTTPException
from .supabase_client import create_supabase
from .auth import get_current_user
from pydantic import BaseModel
from urllib.parse import unquote

from typing import List, Optional


app = FastAPI()

# Open up CORS for browser clients (JS running elsewhere)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class signup(BaseModel):
    email: str
    password: str


class Project(BaseModel):
    title: Optional[str] = None
    type:Optional[str] = None
    stack: List[str] = None
    status: Optional[str] = None
    repo: Optional[str] = None
    description: Optional[str] = None
    live_url: Optional[str] = None
    image_url: Optional[str] = None


class Profile(BaseModel):
    username: str
    first_name: str
    last_name: str
    id: str


@app.on_event("startup")
async def startup_event():
    app.state.supabase = await create_supabase()



@app.post("/add-project")
async def add_project(request: Request, project: Project, user=Depends(get_current_user)):
    supabase = request.app.state.supabase
    payload = project.model_dump()
    payload['user'] =  user
    try:
        res = await supabase.table("portfolio").insert(payload).execute()
    except Exception as e:  
        raise HTTPException(status_code=405, detail="supabase error")
    return JSONResponse(status_code=200, content={"id": res.data[0]['id']})

@app.get("/projects")
async def projects(request: Request, user=Depends(get_current_user)):
    supabase = request.app.state.supabase
    res = await supabase.table("portfolio").select("id, created_at, title, type, stack, repo, live_url, image_url, status, updated_at, description, project_images(image_url)").eq("user", user).execute()
    return JSONResponse(status_code=200, content=res.data)

@app.get("/portfolio/{id}")
async def projects(request: Request, id: str):
    supabase = request.app.state.supabase
    try:
        res = await supabase.table("profiles").select("profile_id").eq("profile_id", id).execute()
    except Exception:
        raise HTTPException(status_code=404, detail="user does not exist")
    res = await supabase.table("profiles").select("id").eq("profile_id", id).execute()
    print(res)
    res = await supabase.table("portfolio").select("created_at, title, type, stack, repo, live_url, image_url, status, updated_at, description, project_images(image_url)").eq("user", str(res.data[0]['id'])).execute()
    return JSONResponse(status_code=200, content=res.data)


@app.patch("/projects/{project_id}")
async def update_project(request: Request, payload: Project, project_id:str, user=Depends(get_current_user)):
    supabase = request.app.state.supabase
    payload = payload.model_dump()
    try:
        await supabase.table("portfolio").update(payload).eq("user", user).eq("id", project_id).execute()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=405, detail="supabase error")
    return Response(status_code=200)

@app.delete("/projects/{project_id}/image")
async def delete_image(request: Request, link: str, project_id:str, user=Depends(get_current_user)):
    supabase = request.app.state.supabase
    try:
        print(link)
        print(unquote(link))
        await supabase.table('project_images').delete().eq("image_url", unquote(link)).eq("user_id", user).eq("project_id",project_id).execute()
        print(link)
    except Exception:
        print("supabase error")
    return Response(status_code=200)

@app.delete("/projects/{project_id}")
async def projects(request: Request, project_id: str, user=Depends(get_current_user)):
    supabase = request.app.state.supabase
    await supabase.table("portfolio").delete().eq("id", project_id).eq("user", user).execute()
    return Response(status_code=200)

# @app.post("/create-profile")
# async def create_profile(request:Request, profile: Profile, user=Depends(get_current_user)):
#     supabase = request.app.state.supabase
#     payload = profile.model_dump()
#     await supabase.table("profiles").insert(payload).execute()

@app.get("/profile")
async def profile(request: Request, user=Depends(get_current_user)):
    supabase = request.app.state.supabase
    res = await supabase.table("profiles").select("first_name, last_name").eq(id, user).execute()
    return JSONResponse(status_code=200, content=res.data)

@app.get("/profile/track/{profile_id}")
async def track_profile(profile_id: str, request: Request):
    supabase = request.app.state.supabase
    try:
        res = await supabase.rpc("increment_profile_views",{"profile": profile_id}).execute()
        print(res)
    except Exception as e:
        raise HTTPException(status_code=404, detail=e.args)
    
    TRANSPARENT_PIXEL = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01"
    b"\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDAT"
    b"\x08\xd7c\xf8\x0f\x00\x01\x01\x01\x00"
    b"\x18\xdd\x8d\xe1"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)
    return Response(
        content=TRANSPARENT_PIXEL,
        media_type="image/png",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )
