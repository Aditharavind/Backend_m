import os
import uuid
import shutil
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Form, Cookie, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import uvicorn

# ─── Config ───────────────────────────────────────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cars.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

ADMIN_EMAIL = "admin@moto.com"
ADMIN_PASSWORD = "vishnu@2003@moto"
COOKIE_NAME = "motorox_session"
COOKIE_SECRET = "moto_secret_2026_prod"
BASE = "http://localhost:8000"  # Direct backend URL for admin forms

# ─── Database ─────────────────────────────────────────────────────────────────
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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

# Serve uploaded images
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
    """Save an uploaded file and return its public URL path."""
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

# ─── Admin Auth ───────────────────────────────────────────────────────────────
@app.get("/admin1448", response_class=HTMLResponse)
def admin_login_page(error: Optional[str] = None):
    err = f'<p class="text-rose-400 text-center mb-6 text-sm font-bold">{error}</p>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motorox Admin</title><script src="https://cdn.tailwindcss.com"></script>
</head><body class="bg-[#0a0f1a] min-h-screen flex items-center justify-center p-4">
<div class="bg-[#111827] p-10 rounded-3xl border border-gray-800 w-full max-w-md shadow-2xl">
    <h1 class="text-3xl font-bold text-center mb-10 text-white">Motorox <span class="text-blue-500">Admin</span></h1>
    {err}
    <form action="{BASE}/admin1448/login" method="post" class="space-y-6">
        <div><label class="block text-gray-500 text-xs font-bold mb-2 uppercase tracking-widest">Email</label>
        <input name="email" type="email" required class="w-full bg-black border border-gray-700 rounded-xl p-3.5 text-white focus:ring-2 focus:ring-blue-500 outline-none"></div>
        <div><label class="block text-gray-500 text-xs font-bold mb-2 uppercase tracking-widest">Password</label>
        <input name="password" type="password" required class="w-full bg-black border border-gray-700 rounded-xl p-3.5 text-white focus:ring-2 focus:ring-blue-500 outline-none"></div>
        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl transition-all">Sign In</button>
    </form>
</div></body></html>"""

@app.post("/admin1448/login")
def admin_login(email: str = Form(...), password: str = Form(...)):
    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        resp = RedirectResponse(url="/admin1448/dashboard", status_code=303)
        resp.set_cookie(key=COOKIE_NAME, value=COOKIE_SECRET, httponly=True, samesite="lax")
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
            <div class="md:col-span-2"><label class="text-gray-500 text-xs font-bold block mb-1">NAME</label>
            <input name="name" value="{c.name}" class="w-full bg-black border border-gray-700 rounded-lg p-2.5 text-white text-sm"></div>
            <div><label class="text-gray-500 text-xs font-bold block mb-1">RATE ₹/KM</label>
            <input name="rate" type="number" value="{c.rate}" class="w-full bg-black border border-gray-700 rounded-lg p-2.5 text-white text-sm"></div>
        </div>
        <div class="mb-4"><label class="text-gray-500 text-xs font-bold block mb-1">DESCRIPTION</label>
        <textarea name="desc" class="w-full bg-black border border-gray-700 rounded-lg p-2.5 text-white text-sm h-16">{c.desc}</textarea></div>
        <div class="grid grid-cols-3 gap-3 mb-4">
            <div><label class="text-gray-500 text-[10px] font-bold block mb-1">REPLACE IMG 1</label><input name="img1" type="file" accept="image/*" class="text-xs text-gray-400"></div>
            <div><label class="text-gray-500 text-[10px] font-bold block mb-1">REPLACE IMG 2</label><input name="img2" type="file" accept="image/*" class="text-xs text-gray-400"></div>
            <div><label class="text-gray-500 text-[10px] font-bold block mb-1">REPLACE IMG 3</label><input name="img3" type="file" accept="image/*" class="text-xs text-gray-400"></div>
        </div>
        <div class="flex items-center gap-3 mb-4">
            <input name="available" type="checkbox" {"checked" if c.available else ""} class="w-5 h-5 accent-blue-500">
            <span class="text-sm text-gray-300">Available for Rent</span>
        </div>
        <div class="flex gap-3">
            <button type="submit" class="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl transition-all text-sm">Save Changes</button>
            <a href="{BASE}/admin1448/delete/{c.id}" onclick="return confirm('Delete this car permanently?')" class="bg-rose-500/10 text-rose-400 hover:bg-rose-600 hover:text-white px-5 py-3 rounded-xl border border-rose-500/20 transition-all font-bold text-sm">Delete</a>
        </div>
    </form>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motorox Fleet HQ</title><script src="https://cdn.tailwindcss.com"></script>
</head><body class="bg-[#0a0f1a] text-white p-6 md:p-10">
<div class="max-w-5xl mx-auto">
    <div class="flex flex-col md:flex-row justify-between items-center mb-10 gap-4 bg-[#111827] p-6 rounded-2xl border border-gray-800">
        <div><h1 class="text-2xl font-bold">Fleet <span class="text-blue-500">HQ</span></h1>
        <p class="text-gray-500 text-xs mt-1 font-mono">{user}</p></div>
        <a href="{BASE}/admin1448/logout" class="text-rose-400 hover:text-rose-300 text-sm font-bold">Sign Out</a>
    </div>

    <h2 class="text-lg font-bold text-blue-400 mb-6">Add New Vehicle</h2>
    <form action="{BASE}/admin1448/add" method="post" enctype="multipart/form-data" class="bg-[#111827] p-8 rounded-2xl border border-gray-800 mb-12 shadow-xl">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div class="md:col-span-2"><label class="text-gray-500 text-xs font-bold block mb-2">CAR NAME</label>
            <input name="name" required class="w-full bg-black border border-gray-700 rounded-xl p-3.5 text-white"></div>
            <div><label class="text-gray-500 text-xs font-bold block mb-2">RATE ₹/KM</label>
            <input name="rate" type="number" required class="w-full bg-black border border-gray-700 rounded-xl p-3.5 text-white"></div>
        </div>
        <div class="mb-6"><label class="text-gray-500 text-xs font-bold block mb-2">DESCRIPTION</label>
        <textarea name="desc" required class="w-full bg-black border border-gray-700 rounded-xl p-3.5 text-white h-28 resize-none"></textarea></div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div><label class="text-gray-500 text-xs font-bold block mb-2">MAIN IMAGE</label>
            <input name="img1" type="file" accept="image/*" required class="text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700"></div>
            <div><label class="text-gray-500 text-xs font-bold block mb-2">INTERIOR IMAGE</label>
            <input name="img2" type="file" accept="image/*" required class="text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700"></div>
            <div><label class="text-gray-500 text-xs font-bold block mb-2">SIDE / EXTRA IMAGE</label>
            <input name="img3" type="file" accept="image/*" required class="text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700"></div>
        </div>
        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-600/20 transition-all text-lg">Add to Fleet</button>
    </form>

    <h2 class="text-lg font-bold text-gray-400 mb-6">Current Fleet ({len(cars)} vehicles)</h2>
    {rows if rows else '<div class="text-center py-16 bg-[#111827] border border-dashed border-gray-700 rounded-2xl text-gray-600 font-bold">No vehicles in fleet yet.</div>'}
</div></body></html>"""

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

@app.post("/admin1448/update/{car_id}")
async def admin_update_car(
    car_id: int,
    name: str = Form(...),
    rate: int = Form(...),
    desc: str = Form(...),
    available: str = Form("off"),
    img1: Optional[UploadFile] = File(None),
    img2: Optional[UploadFile] = File(None),
    img3: Optional[UploadFile] = File(None),
    user: str = Depends(check_admin),
    db: Session = Depends(get_db),
):
    if not user:
        return RedirectResponse(url="/admin1448", status_code=303)
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    car.name = name
    car.rate = rate
    car.desc = desc
    car.available = available == "on"

    # Only replace image if a new file was uploaded
    if img1 and img1.filename:
        car.image1 = save_upload(img1)
    if img2 and img2.filename:
        car.image2 = save_upload(img2)
    if img3 and img3.filename:
        car.image3 = save_upload(img3)

    db.commit()
    return RedirectResponse(url="/admin1448/dashboard", status_code=303)

@app.get("/admin1448/delete/{car_id}")
def admin_delete_car(car_id: int, user: str = Depends(check_admin), db: Session = Depends(get_db)):
    if not user:
        return RedirectResponse(url="/admin1448", status_code=303)
    car = db.query(Car).filter(Car.id == car_id).first()
    if car:
        db.delete(car)
        db.commit()
    return RedirectResponse(url="/admin1448/dashboard", status_code=303)

# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
