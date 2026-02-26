from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.config.config import config
from src.infrastructure.database.repositories.cats import (
    CatRepository,
)
from src.presentation.dependencies import get_cat_repository
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class Auth:
    """
    Class handles authentication and authorization
    """

    SECRET_KEY = config.SECRET_KEY
    ALGORITHM = config.ALGORITHM
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    

    def _get_current_time(self):
        """Get current UTC time"""
        return datetime.now(timezone.utc)

    async def create_access_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        to_encode = data.copy()
        now_utc = self._get_current_time()
        if expires_delta:
            expire = now_utc + timedelta(seconds=expires_delta)
        else:
            expire = now_utc + timedelta(minutes=180)
        to_encode.update({"iat": now_utc, "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_access_token

    async def create_refresh_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        to_encode = data.copy()
        now_utc = self._get_current_time()
        if expires_delta:
            expire = now_utc + timedelta(seconds=expires_delta)
        else:
            expire = now_utc + timedelta(days=7)
        to_encode.update({"iat": now_utc, "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
        )
            if payload["scope"] == "refresh_token":
                username = payload["sub"]
                return username
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    async def get_current_cat(
        self,
        token: str = Depends(oauth2_scheme),
        cat_repository: CatRepository = Depends(get_cat_repository),
    ):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "access_token":
                username = payload["sub"]
                if username is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise e

        cat = await cat_repository.get_by_name(username)
        if cat is None:
            raise credentials_exception
        return cat

    async def get_current_admin(self, current_cat=Depends(get_current_cat)):
        if not current_cat.is_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return current_cat

    def create_reset_token(self, data: dict):
        to_encode = data.copy()
        now_utc = self._get_current_time()
        expire = now_utc + timedelta(days=1)
        to_encode.update({"iat": now_utc, "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_name_from_token(self, token: str, cat_repository: CatRepository):
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            name = payload["sub"]
            cat = await cat_repository.get_by_name(name)
            return cat.name
        except JWTError as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for verification",
            )


    async def get_current_cat_token(self, token: str = Depends(oauth2_scheme)):
        return token


auth_service = Auth()


async def get_current_cat(
    token: str = Depends(auth_service.oauth2_scheme),
    cat_repository: CatRepository = Depends(get_cat_repository),
):
    """Standalone function to get current authenticated cat"""
    return await auth_service.get_current_cat(token, cat_repository)


async def get_current_admin(current_cat=Depends(get_current_cat)):
    """Standalone function to get current admin cat"""
    if not current_cat.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_cat
    