from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmailAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    email_address: str
    created_at: datetime
