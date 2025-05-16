from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from supabase import create_client
from dotenv import load_dotenv
import os
import traceback

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# GET: Show form
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request, phonenumber: str = ""):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "phonenumber": phonenumber,
        "message": ""
    })

# POST: Submit form
@app.post("/", response_class=HTMLResponse)
def submit_form(
    request: Request,
    name: str = Form(...),
    phone_number: str = Form(...),
    email: str = Form(...),
    location: str = Form(...)
):
    try:
        # Fetch existing role from DB using phone number
        existing = (
            supabase.table("registration_form")
            .select("role")
            .eq("phone_number", phone_number)
            .execute()
        )

        # Use existing role or default if missing
        role = existing.data[0]["role"] if existing.data else "unknown"

        update_data = {
            "name": name,
            "email": email,
            "location": location,
            "role": role
        }

        result = (
            supabase.table("registration_form")
            .update(update_data)
            .eq("phone_number", phone_number)
            .execute()
        )

        # If update fails (i.e., new phone number), insert instead
        if not result.data:
            insert_data = {
                "name": name,
                "phone_number": phone_number,
                "email": email,
                "location": location,
                "role": role
            }
            supabase.table("registration_form").insert(insert_data).execute()

        return templates.TemplateResponse("index.html", {
            "request": request,
            "phonenumber": phone_number,
            "message": "Your details were submitted successfully!"
        })

    except Exception as e:
        traceback.print_exc()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "phonenumber": phone_number,
            "message": f"Submission failed. Error: {e}"
        })

# Helper: Called by Plivo webhook to save phone_number + role during call
def save_role(phone_number: str, role: str):
    existing = supabase.table("registration_form").select("phone_number").eq("phone_number", phone_number).execute()
    if existing.data:
        supabase.table("registration_form").update({"role": role}).eq("phone_number", phone_number).execute()
    else:
        supabase.table("registration_form").insert({
            "phone_number": phone_number,
            "role": role
        }).execute()

# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
