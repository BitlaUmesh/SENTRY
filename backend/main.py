import json
import os
import uuid
from typing import Any, Dict

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from dotenv import load_dotenv
from groq import Groq

from database.database import init_db, insert_alert, update_human_action, get_alert_by_id, get_latest_alerts, check_duplicate_alert

# Load environment variables from .env
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

groq_client = None
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)

# Use lifespan to initialize our database during startup
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Local SOAR Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def send_to_telegram(severity: str, summary: str, mitre_tactic: str, predictive_hardening: str, source_ip: str, alert_id: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram configuration missing. Skipping Telegram notification.")
        return
        
    message = (
        f"🚨 <b>{severity} Security Alert</b> 🚨\n\n"
        f"<b>Summary:</b> {summary}\n"
        f"<b>MITRE Tactic:</b> {mitre_tactic}\n"
        f"<b>Predictive Hardening:</b> {predictive_hardening}\n\n"
        f"<b>Source IP:</b> {source_ip}"
    )
    
    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "[Isolate Host]", "callback_data": f"isolate_{alert_id}"},
                {"text": "[Ignore]", "callback_data": f"ignore_{alert_id}"}
            ]
        ]
    }
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(inline_keyboard)
    }
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, data=payload)
        except Exception as e:
            print(f"Error sending Telegram message: {e}")

async def process_alert(payload: dict):
    alert_id = str(uuid.uuid4())
    source_ip = payload.get("source_ip", "Unknown")
    raw_payload_str = json.dumps(payload)
    
    prompt = (
        f"You are a SOC AI. Output ONLY a valid JSON object with EXACTLY these keys: "
        "'severity' (Low/Medium/High/Critical), "
        "'mitre_tactic', "
        "'summary' (2 sentences max), "
        "'predictive_hardening' (1 sentence). "
        f"Analyze this payload: {raw_payload_str}"
    )
    
    severity = "Low"
    mitre_tactic = "Unknown"
    summary = "Analysis failed."
    predictive_hardening = "N/A"
    ai_analysis_str = "{}"
    
    if groq_client:
        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
            )
            text_resp = completion.choices[0].message.content.strip()
            
            analysis = json.loads(text_resp)
            severity = analysis.get("severity", "Low")
            mitre_tactic = analysis.get("mitre_tactic", "Unknown")
            summary = analysis.get("summary", summary)
            predictive_hardening = analysis.get("predictive_hardening", predictive_hardening)
            ai_analysis_str = json.dumps(analysis)
            
        except Exception as e:
            print(f"Error calling Groq: {e}")
            ai_analysis_str = json.dumps({"error": str(e)})

    # Insert into the database
    insert_alert(
        id=alert_id,
        source_ip=source_ip,
        raw_payload=raw_payload_str,
        ai_analysis=ai_analysis_str,
        mitre_mapping=mitre_tactic,
        severity=severity,
        human_action="PENDING"
    )
    
    # Send ALL alerts to Telegram for the Demo (Low/Medium/High/Critical)
    if severity in ["Low", "Medium", "High", "Critical"]:
        await send_to_telegram(
            severity=severity,
            summary=summary,
            mitre_tactic=mitre_tactic,
            predictive_hardening=predictive_hardening,
            source_ip=source_ip,
            alert_id=alert_id
        )

@app.post("/api/v1/alert")
async def receive_alert(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    # Backend De-Duplication: Set to 0s for demo to allow repeated notifications
    source_ip = payload.get("source_ip", "Unknown")
    raw_payload_str = json.dumps(payload)
    
    if check_duplicate_alert(source_ip, raw_payload_str, seconds=0):
        print(f"[DEDUPLICATION] Dropping redundant alert from {source_ip}")
        return {"status": "duplicate_ignored"}

    background_tasks.add_task(process_alert, payload)
    return {"status": "processing"}

@app.post("/api/v1/telegram-webhook")
async def telegram_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    if "callback_query" in payload:
        callback_query = payload["callback_query"]
        callback_id = callback_query.get("id")
        data = callback_query.get("data", "")
        
        if data.startswith("isolate_") or data.startswith("ignore_"):
            parts = data.split("_", 1)
            if len(parts) == 2:
                action, alert_id = parts
                
                # Ensure it ONLY updates status to ISOLATED or IGNORED based on valid callback
                new_status = "ISOLATED" if action == "isolate" else "IGNORED"
                
                # Apply human action to DB
                update_human_action(alert_id, new_status)
                
                # Mock isolation step
                if action == "isolate":
                    alert = get_alert_by_id(alert_id)
                    source_ip = alert.get("source_ip", "Unknown") if alert else "Unknown"
                    print(f"[EXECUTION] Host {source_ip} isolated.")
                
                # Acknowledge the callback query so the loading spinner stops
                if TELEGRAM_BOT_TOKEN:
                    async with httpx.AsyncClient() as client:
                        # 1. Answer Callback Query
                        try:
                            answer_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
                            await client.post(answer_url, data={
                                "callback_query_id": callback_id,
                                "text": f"Host {new_status.lower()} successfully.",
                            })
                        except Exception as e:
                            print(f"Failed to answer Telegram callback query: {e}")
                        
                        # 2. Edit Original Message (Remove buttons and update text)
                        message = callback_query.get("message", {})
                        chat_id = message.get("chat", {}).get("id")
                        message_id = message.get("message_id")
                        original_text = message.get("text", "")
                        
                        if chat_id and message_id:
                            status_suffix = "✅ STATUS: HOST ISOLATED" if action == "isolate" else "⚪ STATUS: ALERT IGNORED"
                            new_text = f"{original_text}\n\n{status_suffix}"
                            
                            try:
                                edit_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
                                await client.post(edit_url, data={
                                    "chat_id": chat_id,
                                    "message_id": message_id,
                                    "text": new_text,
                                    "parse_mode": "HTML",
                                    "reply_markup": json.dumps({"inline_keyboard": []})
                                })
                            except Exception as e:
                                print(f"Failed to edit Telegram message: {e}")
                            
    return JSONResponse(status_code=200, content={"status": "ok"})

@app.get("/api/v1/alerts")
async def get_alerts():
    try:
        # Fetch up to 50 latest rows to avoid heavy loads on frontend polling
        alerts = get_latest_alerts(limit=50)
        return {"alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch alerts from database")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)
