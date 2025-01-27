from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from social_django.utils import load_strategy
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

class GoogleLoginCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("Received POST request to GoogleLoginCallbackView.")  # 요청 로그

        # 프론트엔드에서 전달된 Access Token 확인
        access_token = request.data.get('access_token')
        print(f"Access Token received: {access_token}")

        if not access_token:
            print("Access Token is missing!")  # 에러 디버깅
            return Response({'error': 'Access token is missing'}, status=400)

        # Google OAuth 전략 및 Backend 로드
        try:
            strategy = load_strategy(request)
            backend = strategy.get_backend('google-oauth2')
        except Exception as e:
            print(f"Error loading strategy or backend: {e}")  # 에러 로그
            return Response({'error': 'Failed to load OAuth strategy'}, status=500)

        # Google 사용자 인증
        try:
            user = backend.do_auth(access_token)
            print(f"User authenticated: {user}")  # 인증 성공 여부 확인
        except Exception as e:
            print(f"Error during authentication: {e}")  # 인증 에러 로그
            return Response({'error': 'Authentication failed'}, status=401)

        if user:
            # 이미 존재하는 사용자: JWT 발급
            print(f"Existing user found: {user.username} ({user.email})")
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

        # Google 사용자 데이터 가져오기
        try:
            user_info = backend.user_data(access_token)
            print(f"User info retrieved: {user_info}")  # 사용자 데이터 로그
        except Exception as e:
            print(f"Error retrieving user data: {e}")  # 데이터 조회 에러 로그
            return Response({'error': 'Failed to retrieve user data'}, status=500)

        email = user_info.get('email')
        if not email:
            print("Email is missing in user data.")  # 이메일 누락 체크
            return Response({'error': 'Email is required for authentication'}, status=400)

        username = email.split('@')[0]  # 이메일 앞부분을 username으로 사용
        print(f"Username generated: {username}")

        # 사용자 생성 또는 가져오기
        try:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'username': username}
            )
            print(f"User {'created' if created else 'found'}: {user.username} ({user.email})")
        except Exception as e:
            print(f"Error creating or retrieving user: {e}")  # 사용자 생성 에러
            return Response({'error': 'Failed to create or retrieve user'}, status=500)

        if created:
            try:
                # 사용자 추가 설정 (예: 프로필 이미지)
                user.set_unusable_password()  # 소셜 로그인 사용자 비밀번호 비활성화
                user.save()
                print(f"New user created and saved: {user.username}")
            except Exception as e:
                print(f"Error saving user: {e}")  # 저장 에러
                return Response({'error': 'Failed to save user'}, status=500)

        # JWT 발급
        try:
            refresh = RefreshToken.for_user(user)
            print(f"JWT tokens issued for user: {user.username}")
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
            })
        except Exception as e:
            print(f"Error issuing JWT tokens: {e}")  # JWT 발급 에러
            return Response({'error': 'Failed to issue tokens'}, status=500)
