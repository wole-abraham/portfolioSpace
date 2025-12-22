from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from .auth import get_current_user
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import HTTPException
from .supabase_client import create_supabase
from .auth import get_current_user
from pydantic import BaseModel
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

@app.get("/portfolio/{email}")
async def projects(request: Request, email: str):
    supabase = request.app.state.supabase
    res = await supabase.table("profiles").select("email").eq("email", email).execute()
    if not res.data:
        return JSONResponse(status=404, content={"user does not exist"})
    res = await supabase.table("profiles").select("id").eq("email", email).execute()
    print(res.data)
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