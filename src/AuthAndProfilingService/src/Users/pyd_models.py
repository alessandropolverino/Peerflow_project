from pydantic import BaseModel, Field


class BatchUserDetailsRequest(BaseModel):
    """
    Represents the request body for batch user details retrieval.
    This model corresponds to BatchUserDetailsRequest from the User Service.
    """
    userIds: list[str] = Field(..., min_items=1, description="List of user IDs to retrieve details for")

    class Config:
        json_schema_extra = {
            "example": {
                "userIds": ["user_id_1", "user_id_2", "user_id_3"]
            }
        }