import jwt  # used for encoding and decoding jwt tokens
from fastapi import HTTPException  # used to handle error handling
from passlib.context import CryptContext  # used for hashing the password
from datetime import datetime, timedelta  # used to handle expiry time for tokens
from ..dependencies import get_db, JWTBearer
from fastapi import APIRouter, Depends, HTTPException, Security
from starlette.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from random import choice
from ..schemas import RegisterModel, LoginModel, EmailSchema
from ..crud import get_user, put_user
from .auth import auth_handler
import string
import fastapi_plugins
import aioredis

router = APIRouter()
security = HTTPBearer()

conf = ConnectionConfig(
    MAIL_USERNAME="shuning0316@163.com",
    MAIL_PASSWORD="BEDHMPMGDHQVGFVO",
    MAIL_FROM="shuning0316@163.com",
    MAIL_PORT=465,
    MAIL_SERVER="smtp.163.com",
    MAIL_TLS=False,
    MAIL_SSL=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


@router.post('/admin/user/register')
async def signup(user_details: RegisterModel,
                 cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis),
                 db: Session = Depends(get_db)):
    veriy_code = await cache.get('verify-code')
    chars = string.digits
    random_digits = ''.join(choice(chars) for _ in range(4))
    await cache.set('verify-code', random_digits)  #重新随机初始化验证码，保证一个验证码只能用一次

    if not veriy_code:
        raise HTTPException(status_code=401, detail="请发送验证码")

    if user_details.verify_code != veriy_code.decode('utf-8'):
        raise HTTPException(status_code=401, detail="验证码错误")

    verify_code_email = await cache.get('verify-code-email')
    if user_details.email != verify_code_email.decode('utf-8'):
        raise HTTPException(status_code=412, detail='注册邮箱与验证码邮箱不一致')

    if get_user(db, user_details.email) != None:
        raise HTTPException(status_code=401, detail='邮箱已存在')

    try:
        hashed_password = auth_handler.encode_password(user_details.password)
        user = {
            'username': user_details.username,
            'password': hashed_password,
            'email': user_details.email,
        }
        put_user(db, **user)
        return dict(code=20000, message="注册成功")
    except:
        raise HTTPException(status_code=401, detail="注册失败")

@router.get('/admin/user/info', dependencies=[Depends(JWTBearer())])
def user_info():
    #token = credentials.credentials
    #if auth_handler.decode_token(token):
    return {
        'code': 20000,
        'roles': ['admin'],
        'introduction': 'I am a super administrator',
        'avatar': 'https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif',
        'name': 'Super Admin'
    }

@router.post('/admin/user/login')
def login(user_details: LoginModel, db: Session = Depends(get_db)):
    user = get_user(db, user_details.email)

    if (user is None):
        raise HTTPException(status_code=401, detail="非法用户")

    if (not auth_handler.verify_password(user_details.password, user.password)):
        raise HTTPException(status_code=401, detail="密码错误")

    access_token = auth_handler.encode_token(user.username)
    refresh_token = auth_handler.encode_refresh_token(user.username)
    return dict(code=20000, access_token=access_token,
                refresh_token=refresh_token, message="登录成功")

@router.post('/admin/user/logout')
async def logout(credentials: HTTPAuthorizationCredentials = Security(security),
                 cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis)):
    token = credentials.credentials
    if auth_handler.decode_token(token):
        await cache.sadd('token-blacklist', token)
    return dict(code=20000, message="成功注销")


@router.get('/admin/user/refresh-token')
def refresh_user_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    refresh_token = credentials.credentials
    new_token = auth_handler.refresh_token(refresh_token)
    return dict(code=20000, access_token=new_token)


@router.post("/admin/user/verify-code")
async def send_verify_code(email: EmailSchema,
                           cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis),
                           ) -> JSONResponse:
    emails = email.dict().get("email")

    if not emails[0].endswith('@impcas.ac.cn'):
        raise HTTPException(status_code=401, detail="请使用所邮箱")

    chars = string.digits
    random_digits = ''.join(choice(chars) for _ in range(4))
    html = f'''
    <p>验证码: {random_digits}</p>
    '''

    message = MessageSchema(
        subject="验证码",
        recipients=emails,  # List of recipients, as many as you can pass
        body=html,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    await cache.set('verify-code', random_digits)
    await cache.set('verify-code-email', emails[0])
    return dict(code=20000, message="验证码已发送邮箱")
