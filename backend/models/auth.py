from pydantic import BaseModel, Field

class AuthUserResponse(BaseModel):
    """
    Représente un utilisateur dans le système d'authentification Supabase
    """
    id: str = Field(
        description="ID unique de l'utilisateur (géré par Supabase Auth)"
    )
    email: str = Field(
        description="Email de l'utilisateur (géré par Supabase Auth)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com"
            }]
        }
    } 