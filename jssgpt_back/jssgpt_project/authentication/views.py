# authentication/views.py
import logging
import requests

from django.contrib.auth.models import User
from django.contrib.auth import login
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile

logger = logging.getLogger(__name__)

def validate_google_token(id_token):
    """
    Google의 id_token을 검증하여 토큰 정보를 리턴합니다.
    """
    google_api_url = "https://www.googleapis.com/oauth2/v3/tokeninfo"
    response = requests.get(google_api_url, params={'id_token': id_token})
    if response.status_code == 200:
        return response.json()
    raise Exception(f"Invalid Google ID Token: {response.text}")

def issue_tokens_and_respond(user):
    """
    Simple JWT를 사용하여 refresh 및 access 토큰을 발급합니다.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
    }

class GoogleLoginCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info("Received POST request to GoogleLoginCallbackView.")

        # React에서 전달한 토큰은 사실 id_token입니다.
        id_token = request.data.get('access_token')
        if not id_token:
            logger.warning("ID Token is missing!")
            return Response({'error': 'Access token is missing'}, status=400)

        # id_token 검증
        try:
            token_info = validate_google_token(id_token)
            logger.info(f"Token Info: {token_info}")
        except Exception as e:
            logger.error(f"Invalid ID Token: {e}")
            return Response({'error': 'Invalid Access Token'}, status=401)

        # token_info에서 필요한 정보 추출 (예: email, sub, picture 등)
        email = token_info.get('email')
        if not email:
            logger.warning("Email is missing in token info.")
            return Response({'error': 'Email is required for authentication'}, status=400)

        username = email.split('@')[0]
        user, created = User.objects.get_or_create(email=email, defaults={'username': username})
        if created:
            user.set_unusable_password()
            user.save()
            logger.info(f"New user created: {user.username}")

            # UserProfile 생성 (예: social_id는 token_info의 'sub' 필드를 사용)
            social_id = token_info.get('sub')
            if social_id:
                UserProfile.objects.create(
                    user=user,
                    provider='google',
                    social_id=social_id,
                    profile_image=token_info.get('picture')
                )
        login(request, user)

        return Response(issue_tokens_and_respond(user))
    