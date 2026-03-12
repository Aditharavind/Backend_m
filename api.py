import os
import uuid
import shutil
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Form, Cookie, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

import uvicorn

# ─── Config ───────────────────────────────────────────────────────────────────

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# PostgreSQL database (Render)
SQLALCHEMY_DATABASE_URL = "postgresql://moto:RA3n9BPuoybLT56xAFqe3Bi44EQXD7fW@dpg-d6pger75gffc739cr3b0-a.oregon-postgres.render.com:5432/motorox"

ADMIN_EMAIL = "admin@moto.com"
ADMIN_PASSWORD = "vishnu@2003@moto"

COOKIE_NAME = "motorox_session"
COOKIE_SECRET = "moto_secret_2026_prod"

BASE = "https://backend-m-evpd.onrender.com"

# ─── Database ─────────────────────────────────────────────────────────────────

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    rate = Column(Integer, nullable=False)
    available = Column(Boolean, default=True)
    desc = Column(String, default="")
    image1 = Column(String, default="")
    image2 = Column(String, default="")
    image3 = Column(String, default="")

Base.metadata.create_all(bind=engine)

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="Motorox Kochi API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve uploaded images
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ─── Dependencies ─────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_admin(motorox_session: Optional[str] = Cookie(None)):
    if motorox_session == COOKIE_SECRET:
        return ADMIN_EMAIL
    return None


def save_upload(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename or "img.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return f"/uploads/{filename}"

# ─── Public API ───────────────────────────────────────────────────────────────

@app.get("/api/cars")
def api_get_cars(db: Session = Depends(get_db)):
    cars = db.query(Car).order_by(Car.id.desc()).all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "rate": c.rate,
            "available": c.available,
            "desc": c.desc,
            "images": [c.image1, c.image2, c.image3],
        }
        for c in cars
    ]

# ─── Admin Login Page ─────────────────────────────────────────────────────────

@app.get("/admin1448", response_class=HTMLResponse)
def admin_login_page(error: Optional[str] = None):

    err = f'<p class="text-rose-400 text-center mb-6 text-sm font-bold">{error}</p>' if error else ""

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motorox Admin</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-[#0a0f1a] min-h-screen flex items-center justify-center p-4">

<div class="bg-[#111827] p-10 rounded-3xl border border-gray-800 w-full max-w-md shadow-2xl">

<h1 class="text-3xl font-bold text-center mb-10 text-white">
Motorox <span class="text-blue-500">Admin</span>
</h1>

{err}

<form action="{BASE}/admin1448/login" method="post" class="space-y-6">

<div>
<label class="block text-gray-500 text-xs font-bold mb-2 uppercase tracking-widest">Email</label>
<input name="email" type="email" required
class="w-full bg-black border border-gray-700 rounded-xl p-3.5 text-white">
</div>

<div>
<label class="block text-gray-500 text-xs font-bold mb-2 uppercase tracking-widest">Password</label>
<input name="password" type="password" required
class="w-full bg-black border border-gray-700 rounded-xl p-3.5 text-white">
</div>

<button type="submit"
class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl">
Sign In
</button>

</form>
</div>
</body>
</html>
"""

# ─── Admin Auth ───────────────────────────────────────────────────────────────

@app.post("/admin1448/login")
def admin_login(email: str = Form(...), password: str = Form(...)):

    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        resp = RedirectResponse(url="/admin1448/dashboard", status_code=303)
        resp.set_cookie(
            key=COOKIE_NAME,
            value=COOKIE_SECRET,
            httponly=True,
            samesite="lax",
            secure=True,
        )
        return resp

    return RedirectResponse(url="/admin1448?error=Invalid+credentials", status_code=303)


@app.get("/admin1448/logout")
def admin_logout():

    resp = RedirectResponse(url="/admin1448", status_code=303)
    resp.delete_cookie(COOKIE_NAME)

    return resp

# ─── Admin Dashboard ──────────────────────────────────────────────────────────

@app.get("/admin1448/dashboard", response_class=HTMLResponse)
def admin_dashboard(user: str = Depends(check_admin), db: Session = Depends(get_db)):

    if not user:
        return RedirectResponse(url="/admin1448", status_code=303)

    cars = db.query(Car).order_by(Car.id.desc()).all()

    rows = ""

    for c in cars:

        imgs_preview = ""

        for img in [c.image1, c.image2, c.image3]:
            if img:
                imgs_preview += f'<img src="{img}" class="w-20 h-16 object-cover rounded-lg border border-gray-700">'

        rows += f"""
<div class="bg-[#111827] p-6 rounded-2xl border border-gray-800 mb-5">

<form action="{BASE}/admin1448/update/{c.id}" method="post" enctype="multipart/form-data">

<div class="flex flex-wrap gap-3 mb-4">{imgs_preview}</div>

<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">

<div class="md:col-span-2">
<label class="text-gray-500 text-xs font-bold block mb-1">NAME</label>
<input name="name" value="{c.name}"
class="w-full bg-black border border-gray-700 rounded-lg p-2.5 text-white text-sm">
</div>

<div>
<label class="text-gray-500 text-xs font-bold block mb-1">RATE ₹/KM</label>
<input name="rate" type="number" value="{c.rate}"
class="w-full bg-black border border-gray-700 rounded-lg p-2.5 text-white text-sm">
</div>

</div>

<div class="mb-4">
<label class="text-gray-500 text-xs font-bold block mb-1">DESCRIPTION</label>
<textarea name="desc"
class="w-full bg-black border border-gray-700 rounded-lg p-2.5 text-white text-sm h-16">{c.desc}</textarea>
</div>

<div class="grid grid-cols-3 gap-3 mb-4">

<div>
<label class="text-gray-500 text-[10px] font-bold block mb-1">REPLACE IMG 1</label>
<input name="img1" type="file" accept="image/*" class="text-xs text-gray-400">
</div>

<div>
<label class="text-gray-500 text-[10px] font-bold block mb-1">REPLACE IMG 2</label>
<input name="img2" type="file" accept="image/*" class="text-xs text-gray-400">
</div>

<div>
<label class="text-gray-500 text-[10px] font-bold block mb-1">REPLACE IMG 3</label>
<input name="img3" type="file" accept="image/*" class="text-xs text-gray-400">
</div>

</div>

<div class="flex items-center gap-3 mb-4">

<input name="available" type="checkbox" {"checked" if c.available else ""}
class="w-5 h-5 accent-blue-500">

<span class="text-sm text-gray-300">Available for Rent</span>

</div>

<div class="flex gap-3">

<button type="submit"
class="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl">
Save Changes
</button>

<a href="{BASE}/admin1448/delete/{c.id}"
onclick="return confirm('Delete this car permanently?')"
class="bg-rose-500/10 text-rose-400 hover:bg-rose-600 hover:text-white px-5 py-3 rounded-xl border border-rose-500/20 font-bold">
Delete
</a>

</div>

</form>
</div>
"""

    return f"""
<html>
<head>
<script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-[#0a0f1a] text-white p-6">

<div class="max-w-5xl mx-auto">

<h1 class="text-2xl font-bold mb-6">
Fleet <span class="text-blue-500">HQ</span>
</h1>

<h2 class="text-lg font-bold text-blue-400 mb-6">Add New Vehicle</h2>

<form action="{BASE}/admin1448/add" method="post" enctype="multipart/form-data"
class="bg-[#111827] p-8 rounded-2xl border border-gray-800 mb-12">

<input name="name" placeholder="Car Name" required class="mb-3 w-full p-3 bg-black text-white">

<input name="rate" type="number" placeholder="Rate ₹/KM" required class="mb-3 w-full p-3 bg-black text-white">

<textarea name="desc" required class="mb-3 w-full p-3 bg-black text-white"></textarea>

<input name="img1" type="file" required>
<input name="img2" type="file" required>
<input name="img3" type="file" required>

<button type="submit" class="w-full bg-blue-600 p-4 mt-4 rounded-xl">
Add Vehicle
</button>

</form>

{rows}

</div>

</body>
</html>
"""

# ─── Admin CRUD ───────────────────────────────────────────────────────────────

@app.post("/admin1448/add")
async def admin_add_car(
    name: str = Form(...),
    rate: int = Form(...),
    desc: str = Form(...),
    img1: UploadFile = File(...),
    img2: UploadFile = File(...),
    img3: UploadFile = File(...),
    user: str = Depends(check_admin),
    db: Session = Depends(get_db),
):

    if not user:
        return RedirectResponse(url="/admin1448", status_code=303)

    car = Car(
        name=name,
        rate=rate,
        desc=desc,
        available=True,
        image1=save_upload(img1),
        image2=save_upload(img2),
        image3=save_upload(img3),
    )

    db.add(car)
    db.commit()

    return RedirectResponse(url="/admin1448/dashboard", status_code=303)

# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
