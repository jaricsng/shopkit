"""Profile CRUD — /users/me. Always scoped to the authenticated user, never an
arbitrary id, so there's no object-level authorization gap (review in Module 06).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..audit import audit
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_me(current: User = Depends(get_current_user)) -> User:
    return current


@router.put("/me", response_model=UserOut)
def update_me(
    body: UserUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if body.full_name is not None:
        current.full_name = body.full_name
    if body.display_name is not None:
        current.display_name = body.display_name
    db.add(current)
    db.commit()
    db.refresh(current)
    audit("user.profile_update", actor=current.email)
    return current


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    email = current.email
    db.delete(current)
    db.commit()
    # Privacy event (GDPR Art. 17) — keep this audit record per your retention policy.
    audit("user.delete", actor=email)
    return None
