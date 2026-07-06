from db.database import engine
from db.models import Base

# Drop all tables and recreate them to apply the schema changes
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Database tables recreated successfully!")
