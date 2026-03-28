from pydantic import BaseModel, constr


class RegistrationForm(BaseModel):
    name: constr(min_length=3)

