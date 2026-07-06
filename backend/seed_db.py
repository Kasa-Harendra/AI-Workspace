from db.database import SessionLocal, engine
from db import models
import bcrypt

# Ensure tables are created
models.Base.metadata.create_all(bind=engine)

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed():
    db = SessionLocal()
    try:
        # 1. Check or create admin user
        user = db.query(models.User).filter(models.User.username == "admin").first()
        if not user:
            user = models.User(
                username="admin",
                hashed_password=get_password_hash("password123")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created user: admin (id={user.id})")
        else:
            print(f"User admin already exists (id={user.id})")

        # 2. Check or create Google Account
        google_id = "demo_google_id_2026"
        g_acc = db.query(models.GoogleAccount).filter(models.GoogleAccount.google_id == google_id).first()
        if not g_acc:
            g_acc = models.GoogleAccount(
                google_id=google_id,
                user_id=user.id,
                name="Dr. LeelaSai (Executive Demo)",
                email="dr.leelasai@gmail.com",
                refresh_token="mock_refresh_token_demo"
            )
            db.add(g_acc)
            db.commit()
            db.refresh(g_acc)
            print("Created demo GoogleAccount linked to admin")
        elif g_acc.user_id != user.id:
            g_acc.user_id = user.id
            db.commit()
            print("Updated demo GoogleAccount link to admin")

        # 3. Seed real categorized emails into Harendra's Mail table
        demo_mails = [
            {
                "mail_id": "mail_vcvrao_001",
                "google_id": google_id,
                "snippet": "Professor VCV Rao confirming campus arrival for GPU cluster workshop. Requires immediate room allocation...",
                "subject": "URGENT: Campus Visit & GPU Cluster Workshop Schedule",
                "summary": "Professor VCV Rao confirming campus arrival for GPU cluster workshop. Requires immediate room allocation and schedule confirmation.",
                "category": "Highest-priority-work"
            },
            {
                "mail_id": "mail_github_001",
                "google_id": google_id,
                "snippet": "@baabjitvk has invited you to collaborate on the baabjitvk/gandharvam-frontend repository...",
                "subject": "baabjitvk invited you to baabjitvk/gandharvam-frontend",
                "summary": "Invitation to collaborate on gandharvam-frontend repository. Expires in 7 days. Action required to accept invitation.",
                "category": "Recommended-next-actions"
            },
            {
                "mail_id": "mail_github_002",
                "google_id": google_id,
                "snippet": "@baabjitvk has invited you to collaborate on the baabjitvk/gandharvam-backend repository...",
                "subject": "baabjitvk invited you to baabjitvk/gandharvam-backend",
                "summary": "Invitation to collaborate on gandharvam-backend repository. Expires in 7 days. Action required to accept invitation.",
                "category": "Recommended-next-actions"
            },
            {
                "mail_id": "mail_billing_001",
                "google_id": google_id,
                "snippet": "Google Cloud & Play billing method expiring soon. Requires immediate payment verification...",
                "subject": "Action Required: Google Cloud & Google Play Billing Account Update",
                "summary": "Google Cloud & Play billing method expiring soon. Requires immediate payment verification to avoid practice disruption and server outage.",
                "category": "Revenue-impacting-items"
            },
            {
                "mail_id": "mail_openai_001",
                "google_id": google_id,
                "snippet": "Enterprise tier rate limit upgrade confirmed. Decision required on custom deployment region...",
                "subject": "OpenAI API Enterprise Tier Upgrade Confirmation",
                "summary": "Enterprise tier rate limit upgrade confirmed. Decision required on custom deployment region and dedicated instance allocation.",
                "category": "Decisions-requiring-attention"
            },
            {
                "mail_id": "mail_risk_001",
                "google_id": google_id,
                "snippet": "Unidentified SSL login attempt detected from IP 100.116.59.48. Please verify if this was authorized...",
                "subject": "SECURITY ALERT: Unrecognized Tailscale VPN Login Attempt",
                "summary": "Unidentified SSL login attempt detected on Tailscale node. Requires security audit and firewall verification.",
                "category": "Risks"
            }
        ]

        for m_data in demo_mails:
            existing = db.query(models.Mail).filter(models.Mail.mail_id == m_data["mail_id"]).first()
            if not existing:
                mail_obj = models.Mail(**m_data)
                db.add(mail_obj)
                print(f"Inserted mail: {m_data['subject']}")
            else:
                existing.category = m_data["category"]
                existing.summary = m_data["summary"]
                existing.google_id = google_id
                print(f"Updated mail: {m_data['subject']}")
        
        db.commit()
        print("Database seeding completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
