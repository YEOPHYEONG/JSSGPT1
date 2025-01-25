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
llm = ChatOpenAI(model="gpt-4", temperature=0)

@login_required
def create_cover_letter(request, recruit_job_id):
    user = request.user
    recruit_job = get_object_or_404(RecruitJob, id=recruit_job_id)

    # 모든 문항 가져오기
    prompts = CoverLetterPrompt.objects.filter(recruit_job=recruit_job)

    # UserCoverLetter 생성 또는 가져오기
    cover_letters = []
    for prompt in prompts:
        cover_letter, created = UserCoverLetter.objects.get_or_create(
            user=user,
            recruit_job=recruit_job,
            prompt=prompt,
            defaults={'content': "", 'draft': True}
        )
        # 추천 STARExperience 설정
        if not cover_letter.recommended_starexperience.exists():
            try:
                star_experiences = STARExperience.objects.filter(user=user)
                star_texts = "\n".join([f"{star.title}: {star.situation}" for star in star_experiences])
                prompt_text = f"""
                {star_texts} 중에서 가장 {prompt.outline}에 가장 적용할만한 {star_experiences}를 추천해줘.
                Output the recommended STARExperience IDs as a JSON array.
                """
                response = llm.predict(prompt_text)
                recommended_ids = json.loads(response)
                recommended_stars = STARExperience.objects.filter(id__in=recommended_ids)
                cover_letter.recommended_starexperience.add(*recommended_stars)
            except Exception as e:
                logger.error(f"Error recommending STARExperience for prompt {prompt.id}: {e}")
        cover_letters.append(cover_letter)

    # POST 요청에서 선택된 STARExperience 저장
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

    # 템플릿 렌더링
    return render(request, 'user_coverletter/create_cover_letter.html', {
        'recruit_job': recruit_job,
        'prompts': prompts,
        'star_experiences': STARExperience.objects.filter(user=user),
        'cover_letters': cover_letters,
    })


@login_required
def generate_cover_letter_draft(request, recruit_job_id):
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

                # OpenAI에 요청
                prompt_text = f"""
                {prompt.outline}을 바탕으로 {star_experience}를 적절히 참고하여, {recruit_job.title}에 합격할 수 있는 자소서를 작성해줘.
                """
                response = llm.predict(prompt_text)
                cover_letter.content = response
                cover_letter.draft = False
                cover_letter.save()

            # 생성된 첫 번째 CoverLetter 편집 페이지로 이동
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

    # {prompt_id: content} 형태로 딕셔너리 생성
    cover_letters = UserCoverLetter.objects.filter(recruit_job=cover_letter.recruit_job, user=user)
    contents = {cl.prompt_id: cl.content for cl in cover_letters}

    return render(request, 'user_coverletter/edit_cover_letter.html', {
        'prompts': prompts,  # [{"id": 1, "question_text": "문항1"}, {"id": 2, "question_text": "문항2"}]
        'contents': contents,  # {1: "문항1 내용", 2: "문항2 내용"}
        'star_experiences': star_experiences,
        'selected_starexperience_id': cover_letter.selected_starexperience_id,
    })