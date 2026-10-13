from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import database

app = FastAPI(title="Support Ticket Router")

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Request schemas
class TicketCreate(BaseModel):
    customer_email: str
    ticket_text: str
    is_enterprise: bool = False

class FeedbackCreate(BaseModel):
    is_correct: bool
    comments: str = None

# Priority Mappings
PRIORITY_MAP = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
REVERSE_PRIORITY = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}

def analyze_ticket_with_llm(ticket_text: str):
    """
    Mock LLM Engine:
    Rule: Never receives customer_email.
    Returns: category, initial_priority, sentiment, tags, suggested_reply
    """
    text = ticket_text.lower()

    # 1. Sentiment detection
    if any(word in text for word in ["fuck", "idiot", "stupid", "bastard", "abuse"]):
        sentiment = "Abusive"
    elif any(word in text for word in ["angry", "ruined", "terrible", "worst", "unacceptable", "furious"]):
        sentiment = "Angry"
    elif any(word in text for word in ["great", "thanks", "helpful", "awesome"]):
        sentiment = "Happy"
    else:
        sentiment = "Neutral"

    # 2. Category & Initial Priority detection
    if any(word in text for word in ["refund", "charged twice", "charge", "payment", "money"]):
        category = "Billing"
        initial_priority = "High"
    elif any(word in text for word in ["login", "password", "otp", "account", "cant log in", "can't log in"]):
        category = "Login"
        initial_priority = "Medium"
    elif any(word in text for word in ["never arrived", "cold", "late", "driver", "order"]):
        category = "Delivery"
        initial_priority = "Low"
    else:
        category = "General"
        initial_priority = "Low"

    return {
        "category": category,
        "initial_priority": initial_priority,
        "sentiment": sentiment,
        "tags": [category.lower(), "support"],
        "suggested_reply": f"Thank you for contacting support. We are reviewing your {category.lower()} issue and will assist you shortly."
    }

# --- API Endpoints ---

@app.post("/tickets")
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    # Rule: The same ticket should always get the same priority (Idempotency)
    existing = db.query(database.Ticket).filter(database.Ticket.ticket_text == ticket.ticket_text).first()
    if existing:
        return {
            "id": existing.id,
            "priority": REVERSE_PRIORITY[existing.priority],
            "status": "existing_ticket"
        }

    # Step 1: AI semantic analysis (Notice: ticket.customer_email is NEVER passed here)
    ai_result = analyze_ticket_with_llm(ticket.ticket_text)

    category = ai_result.get("category", "General")
    sentiment = ai_result.get("sentiment", "Neutral")
    tags = ",".join(ai_result.get("tags", []))
    suggested_reply = ai_result.get("suggested_reply")

    # Step 2: Deterministic Business Rules in Code
    priority_level = PRIORITY_MAP.get(ai_result.get("initial_priority", "Low"), 1)

    # Rule: If angry, increase priority by one level
    if sentiment.lower() == "angry" and priority_level < 4:
        priority_level += 1

    # Rule: If abusive, don't generate a suggested reply
    if sentiment.lower() == "abusive":
        suggested_reply = None

    # Rule: Enterprise customers with 3 or more previous tickets must be High (3) or above
    if ticket.is_enterprise:
        past_ticket_count = db.query(database.Ticket).filter(
            database.Ticket.customer_email == ticket.customer_email
        ).count()
        if past_ticket_count >= 3 and priority_level < 3:
            priority_level = 3

    # Step 3: Persist to SQLite
    new_ticket = database.Ticket(
        customer_email=ticket.customer_email,
        ticket_text=ticket.ticket_text,
        category=category,
        priority=priority_level,
        sentiment=sentiment,
        tags=tags,
        suggested_reply=suggested_reply
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return {
        "id": new_ticket.id,
        "priority": REVERSE_PRIORITY[priority_level],
        "category": new_ticket.category,
        "sentiment": new_ticket.sentiment,
        "suggested_reply": new_ticket.suggested_reply,
        "status": "processed"
    }

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(database.Ticket).filter(database.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {
        "id": ticket.id,
        "customer_email": ticket.customer_email,
        "ticket_text": ticket.ticket_text,
        "category": ticket.category,
        "priority": REVERSE_PRIORITY[ticket.priority],
        "sentiment": ticket.sentiment,
        "tags": ticket.tags.split(",") if ticket.tags else [],
        "suggested_reply": ticket.suggested_reply
    }

@app.get("/tickets")
def list_tickets(category: str = None, priority: str = None, db: Session = Depends(get_db)):
    query = db.query(database.Ticket)
    if category:
        query = query.filter(database.Ticket.category == category)
    if priority and priority in PRIORITY_MAP:
        query = query.filter(database.Ticket.priority == PRIORITY_MAP[priority])

    results = query.all()
    return [
        {
            "id": t.id,
            "customer_email": t.customer_email,
            "ticket_text": t.ticket_text,
            "category": t.category,
            "priority": REVERSE_PRIORITY[t.priority],
            "sentiment": t.sentiment,
            "suggested_reply": t.suggested_reply
        }
        for t in results
    ]

@app.post("/tickets/{ticket_id}/feedback")
def submit_feedback(ticket_id: int, feedback: FeedbackCreate, db: Session = Depends(get_db)):
    ticket = db.query(database.Ticket).filter(database.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    fb = database.Feedback(
        ticket_id=ticket_id,
        is_correct=feedback.is_correct,
        comments=feedback.comments
    )
    db.add(fb)
    db.commit()
    return {"message": "Feedback submitted successfully", "ticket_id": ticket_id}