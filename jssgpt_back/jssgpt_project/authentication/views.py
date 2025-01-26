from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from social_django.utils import load_strategy
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

class GoogleLoginCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # 소셜 로그인 데이터 로드
        strategy = load_strategy(request)
        backend = strategy.get_backend('google-oauth2')
        user = backend.do_auth(request.data.get('access_token'))  # 프론트엔드에서 전달된 Access Token

        if user:
            # JWT 발급
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
            })
        else:
            return Response({'error': 'Authentication failed'}, status=401)
