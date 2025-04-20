# user_coverletter/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from langchain_community.chat_models import ChatOpenAI
from .models import UserCoverLetter
from langchain_app.models import RecruitJob, CoverLetterPrompt, CoverLetterGuide
from user_experience.models import STARExperience
from django.contrib.auth.decorators import login_required
import json
import logging
import re

# 로깅 설정
logger = logging.getLogger('django')

# OpenAI API 설정
llm = ChatOpenAI(model="o4-mini-2025-04-16", temperature=0.8)


@login_required
def create_cover_letter(request, recruit_job_id):
    """
    1) GET (AJAX): prompts + 추천 STARExperience 목록을 JSON으로 반환
    2) POST: 선택된 STARExperience를 저장한 뒤, (필요 시) 템플릿 렌더링 혹은 JsonResponse
    """
    user = request.user
    recruit_job = get_object_or_404(RecruitJob, id=recruit_job_id)
    prompts = CoverLetterPrompt.objects.filter(recruit_job=recruit_job)

    # 이미 추천된 경험의 제목을 추적하는 집합 (중복 추천 방지)
    recommended_titles = set()

    cover_letters = []
    for prompt in prompts:
        cover_letter, created = UserCoverLetter.objects.get_or_create(
            user=user,
            recruit_job=recruit_job,
            prompt=prompt,
            defaults={'content': "", 'draft': True}
        )
        # 추천 STARExperience가 없으면 LLM 호출
        if not cover_letter.recommended_starexperience.exists():
            try:
                # 이미 추천된 경험 제목은 제외한 STARExperience 조회
                star_experiences = STARExperience.objects.filter(user=user).exclude(title__in=recommended_titles)
                # 후보 경험이 없다면 빈 문자열 전달
                star_texts = "\n".join([f"{star.title}: {star.situation}" for star in star_experiences]) if star_experiences.exists() else ""
                prompt_text = f"""
                너의 목표는 아래 자기소개서 아웃라인에 가장 적합한 경험(STAR 구조 기반)을,  
                논리적으로 판단하고, 가장 잘 어울리는 하나의 경험 ID만 선택하는 거야.

                다음 단계를 따라 reasoning을 수행한 후,  
                최종적으로 **가장 적합한 경험 하나의 ID**를 숫자 형태의 JSON 배열로만 반환해줘.

                예: [2]

                ---

                ### [입력 데이터]

                1. 자기소개서 아웃라인:
                {prompt.outline}

                2. STAR 형식의 경험 목록:
                {star_texts}

                ---

                ### [작업 단계]

                #### 1단계. 문항 핵심 주제 및 키워드 파악
                - 아웃라인을 바탕으로 자기소개서 문항의 의도를 분석해.
                - 이 문항에서 강조해야 할 **핵심 역량**, **핵심 가치**, **필수 기술/태도**를 추출해.

                #### 2단계. 경험과 키워드 매칭
                - STAR 경험 목록의 각 항목을 읽고, 각 경험이 어떤 역량과 가치를 보여주는지 판단해.
                - 각 경험이 1단계에서 도출한 핵심 키워드와 얼마나 일치하는지 비교해.

                #### 3단계. 평가 기준에 따라 적합도 판단
                - 다음 기준을 참고해서 경험 간 우선순위를 판단해:
                - Salesforce 플랫폼 관련 경험인가?
                - 기술적 문제 해결 경험이 있는가?
                - 사용자 요구 분석 및 협업이 포함되어 있는가?
                - 결과가 구체적이고 측정 가능한가?
                - 회사의 가치(고객 중심, 책임감, 지속적 학습)와 부합하는가?

                #### 4단계. 최종 선택
                - 위 기준에 가장 부합하는 **경험 하나의 ID**를 숫자만 포함한 JSON 배열 형식으로 반환해.
                - 반드시 순수 JSON만 출력하고, 설명이나 기호는 포함하지 마.

                ---

                ### ✅ 출력 예시 (형식)

                ```json
                [1]
                ```
                """
                response = llm.predict(prompt_text)
                logger.info(f"LLM response for prompt {prompt.id}: {response}")
                # 정규 표현식으로 코드 블록 내 JSON만 추출
                match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
                if match:
                    json_str = match.group(1)
                else:
                    json_str = response.strip()

                try:
                    recommended_raw = json.loads(json_str)
                except Exception as e:
                    logger.error(f"Error parsing JSON for prompt {prompt.id}: {e}")
                    recommended_raw = []

                new_recommended_ids = []
                for rec in recommended_raw:
                    if isinstance(rec, dict):
                        rec_id = rec.get("STARExperienceID")
                        try:
                            rec_id = int(rec_id)
                        except (ValueError, TypeError):
                            continue
                        new_recommended_ids.append(rec_id)
                    else:
                        try:
                            new_recommended_ids.append(int(rec))
                        except (ValueError, TypeError):
                            continue
                recommended_stars = STARExperience.objects.filter(user=user, id__in=new_recommended_ids)
                if not recommended_stars.exists():
                    # 사용자의 모든 STARExperience 중 첫 번째 항목을 fallback으로 사용
                    recommended_stars = STARExperience.objects.filter(user=user)[:1]
                cover_letter.recommended_starexperience.add(*recommended_stars)
                #디버깅
                logger.debug(f"Prompt {prompt.id} | recommended_ids={new_recommended_ids}")
                logger.debug(f"CoverLetter {cover_letter.id} now has recommended experiences: "
                             f"{list(cover_letter.recommended_starexperience.values('id','title'))}")

                # 새로 추천된 경험들의 제목을 추적 집합에 추가
                for star in recommended_stars:
                    recommended_titles.add(star.title)
            except Exception as e:
                logger.error(f"Error recommending STARExperience for prompt {prompt.id}: {e}")
        cover_letters.append(cover_letter)

    # ---- GET 요청 처리 ----
    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            data = []
            for cl in cover_letters:
                recommended_list = []
                for star in cl.recommended_starexperience.all():
                    recommended_list.append({
                        'id': star.id,
                        'title': star.title
                    })
                data.append({
                    'cover_letter_id': cl.id,
                    'prompt': {
                        'id': cl.prompt.id,
                        'question_text': cl.prompt.question_text,
                    },
                    'recommended': recommended_list
                })
            logger.debug(f"[create_cover_letter GET] returning data: {json.dumps(data, ensure_ascii=False)}")
            
            return JsonResponse({'prompts': data}, safe=False)
        return render(request, 'user_coverletter/create_cover_letter.html', {
            'recruit_job': recruit_job,
            'prompts': prompts,
            'star_experiences': STARExperience.objects.filter(user=user),
            'cover_letters': cover_letters,
        })

    # ---- POST 요청 처리 ----
    if request.method == 'POST':
        for prompt in prompts:
            cover_letter = next((cl for cl in cover_letters if cl.prompt == prompt), None)
            selected_star_id = request.POST.get(f'selected_star_{prompt.id}')
            if selected_star_id and cover_letter:
                try:
                    selected_star = STARExperience.objects.get(id=selected_star_id, user=user)
                    cover_letter.selected_starexperience = selected_star
                    cover_letter.save()
                except STARExperience.DoesNotExist:
                    logger.warning(f"Invalid STAR experience ID: {selected_star_id} for prompt {prompt.id}")
        return JsonResponse({'message': 'Selected STARExperience saved successfully.'})


@login_required
def generate_cover_letter_draft(request, recruit_job_id):
    if request.method == "POST":
        try:
            user = request.user
            recruit_job = get_object_or_404(RecruitJob, id=recruit_job_id)
            prompts = CoverLetterPrompt.objects.filter(recruit_job=recruit_job)

            # 1) CoverLetterGuide 가져오기 (예: 1개만 있다고 가정)
            try:
                cover_letter_guide_obj = CoverLetterGuide.objects.first()
                cover_letter_donts = cover_letter_guide_obj.cover_letter_donts
                cover_letter_guide = cover_letter_guide_obj.cover_letter_guide
            except:
                # 가이드가 없다면 공백 문자열로 처리
                cover_letter_donts = ""
                cover_letter_guide = ""

            for prompt in prompts:
                cover_letter = UserCoverLetter.objects.get(
                    user=user, 
                    recruit_job=recruit_job, 
                    prompt=prompt
                )
                star_experience = cover_letter.selected_starexperience
                # 2) selected_starexperience가 없으면 recommended_starexperience 중 첫 번째 자동선택
                if not star_experience:
                    recommended = cover_letter.recommended_starexperience.first()
                    if recommended:
                        cover_letter.selected_starexperience = recommended
                        cover_letter.save()
                        star_experience = recommended
                    else:
                        return JsonResponse(
                            {'error': f"No STAR experience selected for prompt {prompt.id}"},
                            status=400
                        )

                # 3) 문항 글자수 제한 가져오기 (없으면 1000으로 가정)
                char_limit = prompt.limit if prompt.limit else 1000

                # 4) LLM 프롬프트 구성
                prompt_text = f"""
                다음은 자기소개서를 작성하기 위한 자료들이야.  
                너의 목표는 이 정보를 바탕으로, **단순한 조합이 아닌 논리적인 사고 흐름을 따라 자기소개서를 작성**하는 거야.

                최종 출력은 자기소개서 초안 한 편으로, 반드시 글자수 {char_limit}자 이내(최소 90%)로 작성할 것.  
                출력에는 자기소개서 본문 외 아무 설명도 포함하지 마.

                ---

                ## 📘 입력 데이터

                1. 자기소개서 문항
                "{prompt.question_text}"

                2. 아웃라인 (문항 분석, 키워드, 경험 연결)
                {prompt.outline}

                3. 선택된 STAR 경험  
                - 제목: {star_experience.title}  
                - 상황: {star_experience.situation}  
                - 과제: {star_experience.task}  
                - 행동: {star_experience.action}  
                - 결과: {star_experience.result}

                4. 채용 직무 정보  
                - 직무 설명: {recruit_job.description}  
                - 핵심 역할: {recruit_job.key_roles}  
                - 요구 역량: {recruit_job.required_skills}  
                - 관련 기술: {recruit_job.related_technologies}  
                - 소프트 스킬: {recruit_job.soft_skills}  
                - 필요 강점: {recruit_job.key_strengths}

                5. 작성 가이드  
                {cover_letter_guide}

                6. 작성 시 피해야 할 내용  
                {cover_letter_donts}

                ---

                ## 🧠 작업 순서 및 reasoning 지시

                ### 1단계. 문항 분석
                - 문항의 질문 의도를 분석해.
                - 어떤 역량, 가치, 태도를 평가하려는지 파악하고, 아웃라인과 직무 정보에서 그에 맞는 키워드를 정리해.

                ### 2단계. 경험 분석
                - 선택된 STAR 경험을 통해 아웃라인에서 중요한 키워드들 중 지원자의 강조할 방향성을 정해.

                ### 3단계. 핵심 메시지 설계
                - STAR 경험과 문항/직무 요구사항을 연결해, 자기소개서에서 전하고자 하는 핵심 메시지를 한 문장으로 정의해.
                - 이 메시지를 자기소개서의 중심 주제로 삼아.

                ### 4단계. 자기소개서 전략 방향 설정
                - 아웃라인과 선택된 STAR 경험을 따라서 자기소개서의 방향성을 정립해.
                
                ### 5단계. 자기소개서 문단 구성 계획
                - 네가 정한 방향성에 따라서 자기소개서를 설계해.
                - 그리고 적절한 부분에 선택된 STAR경험을 자연스럽게 녹여낼 부분을 정해.
                +) 단, 문항이 자기 경험 중심이 아닐 경우에는 STAR 경험을 억지로 넣지 말고,
                +) 해당 문항에 더 적합한 방향성(지원 동기, 가치관 등)으로 풀어가.
                +) 아웃라인에서 '5단계: 경험 사례 매칭'은 참고하면 안돼.

                ### 6단계. 자기소개서 작성
                - 작성가이드에 따라서 설계한 방향성과 구성에 따라 자기소개서를 {char_limit}의 90%이상 글자수로 작성해

                ### 7단계. 스타일 가이드 확인
                - 글자 수: {char_limit}자 이내, 최소 90% 이상
                - 어조: 간결하고 명확한 표현 사용, 말줄임표나 형식적인 표현 금지
                - 강조: 수치 기반 결과 강조, 회사/직무와의 연결성 부각
                - 자기소개서 작성 가이드에 맞춰서 작성해줘.
                - 금지사항: {cover_letter_donts}를 읽고, 주해서 작성할 것

                ---

                ## 📝 출력 형식

                - 자기소개서 본문 한 편만 출력할 것
                - 제목, 설명, 마크업 등은 포함하지 말고 본문만 출력
                """

                # 5) LLM 호출
                response = llm.predict(prompt_text)
                logger.info(f"LLM draft response for prompt {prompt.id}: {response}")

                # 6) 혹시 LLM 응답이 제한 초과할 경우, 잘라내기 (필요 시)
                #    -> 프로젝트 성격에 따라 2차 LLM 호출로 "축약" 시킬 수도 있음
                if len(response) > char_limit:
                    response = response[:char_limit]
                    logger.warning(
                        f"Truncated LLM response for prompt {prompt.id} to {char_limit} chars."
                    )

                # 7) DB 저장
                cover_letter.content = response
                cover_letter.draft = False
                cover_letter.save()

            # 8) 생성된 초안 중 첫 번째 커버레터 편집화면으로 이동
            first_cover_letter = UserCoverLetter.objects.filter(
                user=user, 
                recruit_job=recruit_job
            ).first()
            if first_cover_letter:
                return redirect('user_coverletter:edit_cover_letter', pk=first_cover_letter.pk)

        except Exception as e:
            logger.error(f"Error generating drafts for recruit_job_id {recruit_job_id}: {e}")
            return JsonResponse({'error': 'Error generating drafts.'}, status=500)

    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def edit_cover_letter(request, pk):
    user = request.user
    cover_letter = get_object_or_404(UserCoverLetter, pk=pk, user=user)
    prompts = list(CoverLetterPrompt.objects.filter(recruit_job=cover_letter.recruit_job).values('id', 'question_text'))
    star_experiences = STARExperience.objects.filter(user=user)
    cover_letters = UserCoverLetter.objects.filter(recruit_job=cover_letter.recruit_job, user=user)
    contents = {cl.prompt_id: cl.content for cl in cover_letters}

    return render(request, 'user_coverletter/edit_cover_letter.html', {
        'prompts': prompts,
        'contents': contents,
        'star_experiences': star_experiences,
        'selected_starexperience_id': cover_letter.selected_starexperience_id,
    })


@login_required
def get_user_coverletters(request):
    """
    현재 로그인한 사용자의, 주어진 recruit_job_id에 해당하는 UserCoverLetter들을
    prompt id와 content 매핑으로 반환합니다.
    """
    recruit_job_id = request.GET.get('recruit_job_id')
    if not recruit_job_id:
        return JsonResponse({"error": "recruit_job_id가 필요합니다."}, status=400)
    
    cover_letters = UserCoverLetter.objects.filter(user=request.user, recruit_job_id=recruit_job_id)
    contents = {str(cl.prompt.id): cl.content for cl in cover_letters}
    return JsonResponse(contents)


@login_required
def list_cover_letters(request):
    """
    현재 로그인한 사용자의 자기소개서를 채용 직무별로 그룹화하여 반환합니다.
    각 그룹은 하나의 카드로 표시되며, 포함 필드:
      - id: 대표 커버레터의 id (카드 클릭 시 EssayWrite 페이지 이동에 사용)
      - company_name: 채용 직무와 연결된 회사명
      - recruit_job_title: 채용 직무명
      - recruit_job_id: 해당 직무의 id
      - updated_at: 그룹 내 최신 수정일 (ISO 형식)
      - essay_questions: 해당 채용 직무에 속한 자기소개서 문항 목록 (각 항목은 {id, question_text, limit})
    """
    cover_letters = UserCoverLetter.objects.filter(user=request.user)
    grouped = {}
    for cl in cover_letters:
        job_id = cl.recruit_job.id
        if job_id not in grouped:
            grouped[job_id] = {
                'id': cl.id,
                'company_name': cl.recruit_job.recruitment.company.name,
                'recruit_job_title': cl.recruit_job.title,
                'recruit_job_id': cl.recruit_job.id,
                'updated_at': cl.updated_at,
                'essay_questions': [{
                    'id': cl.prompt.id,
                    'question_text': cl.prompt.question_text,
                    'limit': cl.prompt.limit,
                }],
            }
        else:
            if cl.updated_at > grouped[job_id]['updated_at']:
                grouped[job_id]['updated_at'] = cl.updated_at
            if not any(q['id'] == cl.prompt.id for q in grouped[job_id]['essay_questions']):
                grouped[job_id]['essay_questions'].append({
                    'id': cl.prompt.id,
                    'question_text': cl.prompt.question_text,
                    'limit': cl.prompt.limit,
                })
    
    result = sorted(grouped.values(), key=lambda x: x['updated_at'], reverse=True)
    for item in result:
        item['updated_at'] = item['updated_at'].isoformat()
    return JsonResponse(result, safe=False)


@login_required
def update_cover_letter_content(request):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            prompt_id = data.get("prompt_id")
            recruit_job_id = data.get("recruit_job_id")
            content = data.get("content", "")
            cover_letter = get_object_or_404(
                UserCoverLetter,
                user=request.user,
                recruit_job_id=recruit_job_id,
                prompt_id=prompt_id
            )
            cover_letter.content = content
            cover_letter.save()
            return JsonResponse({'message': 'Cover letter content updated successfully.'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
