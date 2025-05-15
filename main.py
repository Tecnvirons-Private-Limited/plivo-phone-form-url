from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from supabase import create_client
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/", response_class=HTMLResponse)
def read_form(request: Request, phonenumber: str = ""):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "phonenumber": phonenumber,
        "message": ""
    })

def save_role(phone_number: str, role: str):
    # Check if phone_number exists
    existing = supabase.table("registration_form").select("phone_number").eq("phone_number", phone_number).execute()
    if existing.data:
        # Update role if phone number exists
        supabase.table("registration_form").update({"role": role}).eq("phone_number", phone_number).execute()
    else:
        # Insert new row
        supabase.table("registration_form").insert({
            "phone_number": phone_number,
            "role": role
        }).execute()

@app.post("/", response_class=HTMLResponse)
def submit_form(
    request: Request,
    name: str = Form(...),
    phone_number: str = Form(...),
    email: str = Form(...),
    location: str = Form(...),
    role: str = Form(...)
):
    try:
        data = {
            "name": name,
            "email": email,
            "location": location
        }
        # Try to update
        result = (
            supabase.table("registration_form")
            .update(data)
            .eq("phone_number", phone_number)
            .eq("role", role)
            .execute()
        )
        print("Supabase update result:", result)
        # If no row was updated, insert a new row
        if not result.data:
            insert_data = {
                "name": name,
                "phone_number": phone_number,
                "email": email,
                "location": location,
                "role": role
            }
            insert_result = supabase.table("registration_form").insert(insert_data).execute()
            print("Supabase insert result:", insert_result)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "phonenumber": phone_number,
            "message": "Data submitted successfully!"
        })
    except Exception as e:
        import traceback
        print("Error:", e)
        traceback.print_exc()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "phonenumber": phone_number,
            "message": "Submission failed. Check logs."
        })

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
