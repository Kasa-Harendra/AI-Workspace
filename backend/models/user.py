from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(..., description="Name of the User")
    google_id: str = Field(..., description="Unique google_id provided after succesfull OAuth")
    