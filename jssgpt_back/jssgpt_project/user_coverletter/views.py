# user_coverletter/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from langchain_community.chat_models import ChatOpenAI
from .models import UserCoverLetter
from langchain_app.models import RecruitJob, CoverLetterPrompt
from user_experience.models import STARExperience
from django.contrib.auth.decorators import login_required
import json
import logging

# 로깅 설정
logger = logging.getLogger('django')

# OpenAI API 설정
llm = ChatOpenAI(model="gpt-4o", temperature=0)

@login_required
def create_cover_letter(request, recruit_job_id):
    """
    1) GET (AJAX): prompts + 추천 STARExperience 목록을 JSON으로 반환
    2) POST: 선택된 STARExperience를 저장한 뒤, (필요 시) 템플릿 렌더링 혹은 JsonResponse
    """
    user = request.user
    recruit_job = get_object_or_404(RecruitJob, id=recruit_job_id)
    prompts = CoverLetterPrompt.objects.filter(recruit_job=recruit_job)

    # 1. UserCoverLetter 생성/가져오기 + 추천 STARExperience 처리
    cover_letters = []
    for prompt in prompts:
        cover_letter, created = UserCoverLetter.objects.get_or_create(
            user=user,
            recruit_job=recruit_job,
            prompt=prompt,
            defaults={'content': "", 'draft': True}
        )
        # 추천 STARExperience가 없으면 OpenAI 호출
        if not cover_letter.recommended_starexperience.exists():
            try:
                star_experiences = STARExperience.objects.filter(user=user)
                star_texts = "\n".join([f"{star.title}: {star.situation}" for star in star_experiences])
                prompt_text = f"""
                자기소개서 문항의 아웃라인: {prompt.outline}
                아래의 경험 목록 중, 위 아웃라인을 바탕으로 합격할만한 자기소개서를 쓸 수 있는 경험 ID를 한 개만 선택해줘.
                경험 목록:
                {star_texts}
                결과는 백틱 등을 모두 제거한 숫자 형태의 JSON 배열로 반환해줘.
                예: [1] 
                그리고 같은 {cover_letter}
                """
                response = llm.predict(prompt_text)
                # LLM 응답 로깅 추가
                logger.info(f"LLM response for prompt {prompt.id}: {response}")
                recommended_raw = json.loads(response)
                # recommended_raw가 객체 리스트인 경우, 각 항목에서 'STARExperienceID' 키의 값을 추출
                recommended_ids = []
                for rec in recommended_raw:
                    if isinstance(rec, dict):
                        rec_id = rec.get("STARExperienceID")
                        try:
                            rec_id = int(rec_id)
                        except (ValueError, TypeError):
                            continue
                        recommended_ids.append(rec_id)
                    else:
                        try:
                            recommended_ids.append(int(rec))
                        except (ValueError, TypeError):
                            continue
                recommended_stars = STARExperience.objects.filter(id__in=recommended_ids)
                cover_letter.recommended_starexperience.add(*recommended_stars)
            except Exception as e:
                logger.error(f"Error recommending STARExperience for prompt {prompt.id}: {e}")
        cover_letters.append(cover_letter)

    # ---- GET 요청 ----
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
            return JsonResponse({'prompts': data}, safe=False)
        return render(request, 'user_coverletter/create_cover_letter.html', {
            'recruit_job': recruit_job,
            'prompts': prompts,
            'star_experiences': STARExperience.objects.filter(user=user),
            'cover_letters': cover_letters,
        })

    # ---- POST 요청 ----
    if request.method == 'POST':
        for prompt in prompts:
            cover_letter = next(
                (cl for cl in cover_letters if cl.prompt == prompt), None
            )
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
def generate_cover_letter_draft(request, recruit_job_id,):
    if request.method == "POST":
        try:
            user = request.user
            recruit_job = get_object_or_404(RecruitJob, id=recruit_job_id)
            prompts = CoverLetterPrompt.objects.filter(recruit_job=recruit_job)

            for prompt in prompts:
                cover_letter = UserCoverLetter.objects.get(
                    user=user, recruit_job=recruit_job, prompt=prompt
                )
                star_experience = cover_letter.selected_starexperience
                if not star_experience:
                    return JsonResponse({'error': f"No STAR experience selected for prompt {prompt.id}"}, status=400)

                prompt_text = f"""
                이제 {prompt.outline}을 문항별로 작성해줘. 다음 요소들을 모두 반영해야 해:

                - 앞서 조사한 {recruit_job.description}, {recruit_job.key_roles}, {recruit_job.required_skills}, {recruit_job.related_technologies}, {recruit_job.soft_skills}, {recruit_job.key_strengths} 중 해당 문항에 relevant한 부분을 포함하기.
                - 해당 문항에 매칭된 {star_experience}을 구체적인 사례로 서술하기 (STAR 구조에서 도출한 내용 활용).
                - **자기소개서 가이드라인**에서 제시한 어조나 작성 원칙 지키기 (논리적 흐름, 적극적 표현, 간결한 문장 등).
                - 문항에서 요구하는 질문에 정확히 답하기.

                한두 개 단락으로 구성된 답변을 작성해줘. 답변은 **지원자가 직접 쓴 것처럼 자연스러운 1인칭**으로 서술하고, 회사와 직무에 대한 열의를 담아 긍정적으로 표현해줘.
                """
                response = llm.predict(prompt_text)
                # LLM 응답 로깅 추가
                logger.info(f"LLM draft response for prompt {prompt.id}: {response}")
                cover_letter.content = response
                cover_letter.draft = False
                cover_letter.save()

            first_cover_letter = UserCoverLetter.objects.filter(
                user=user, recruit_job=recruit_job
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
