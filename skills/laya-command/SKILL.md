---
name: laya-command
description: Combine ko-en-command local Korean-to-English translation with the local Laya decision model for Korean task instructions. Use by default when the user gives a Korean command to Codex, or asks for Laya classification, routing or scoring. Review translation, run both models sequentially, then carry out the original request within its existing scope.
---

# 한국어 명령 + Laya

한국어 작업 지시에 `ko-en-command` 번역과 Laya 판단을 한 세트로 사용한다. 사용자는 두 스킬을 따로 호출하거나 질문 JSON을 작성할 필요가 없다. 명시 호출은 `$laya-command`이다. 일반 대화·인사·단순 사실 질문은 불필요하게 모델을 실행하지 않는다. 사용자가 번역/Laya 제외를 요청하면 그 범위를 우선한다.

## 실행

1. 먼저 [ko-en-command](../ko-en-command/SKILL.md)를 읽고 번역의 조건·부정·리터럴 검토 규칙을 적용한다. 원래 한국어 명령을 UTF-8 파일에 보존하고, 필요한 앞 대화만 `-Context`로 전달한다. 결과 폴더는 현재 작업의 `work/laya-command/<고유한 이름>`처럼 이번 요청 전용으로 정한다.
2. 아래 준비 명령으로 로컬 Qwen 번역을 실행한다. 번역 서버는 종료된 후 반환된다.

```powershell
& "$env:USERPROFILE/.codex/skills/laya-command/scripts/run.ps1" -InputFile 'SOURCE.txt' -OutputDir 'RUN_DIR'
```

짧은 입력은 `-Text '한국어 지시'`도 가능하다. `-Context` 및 `-Glossary`(UTF-8 JSON 경로)는 기존 번역기로 전달한다.

3. `RUN_DIR/translation.json`의 `source_ko`, `english`, `raw_model_english`, `warnings`, `constraint_repairs`를 읽는다. Codex가 원문과 직접 대조하여 행위자·대상·부정·조건·순서·숫자·경로·범위를 검토한다. 이 검토는 Codex가 수행하며 사용자에게 매번 확인을 요구하지 않는다. 경고가 없다는 사실만으로 의미가 같다고 판단하지 않는다. 오류는 원래 출력과 원래 경고를 별도 보존한 후 근거를 명시하여 수정한다. 해결된 경고만 제거하고 수정 내용을 기록한다. 필수 의미가 여전히 모호할 때만 해당 의미를 질문한다.
4. 검토한 번역을 Laya에 전달한다. `-Reviewed`는 위 대조를 실제로 수행했다는 뜻이다.

```powershell
& "$env:USERPROFILE/.codex/skills/laya-command/scripts/run.ps1" -OutputDir 'RUN_DIR' -Reviewed
```

기본 질문은 [요청 유형 분류](assets/command-questions.json)로, 조회/설명, 생성/변경, 혼합, 불명확을 구분하는 보조 판단이다. 단순 명령에도 두 모델을 함께 사용하기 위한 기본 작업이며 파일 삭제나 명령 실행을 결정하는 정책이 아니다. 사용자가 분류·평가할 실제 대상/기준을 주었으면 그 작업에 맞는 영어 질문 JSON을 작성하고 `-Questions 'QUESTIONS.json'`을 전달한다. 질문·선택지 설명도 필요하면 같은 번역기로 번역·검토하고, 키·ID·수치 경계는 유지한다. 본래 질문과 무관한 분류 문제를 새로 만들지 않는다.
5. `RUN_DIR/result.json`의 번역·질문·Laya 결과를 확인한다. 원래 한국어 요청을 기준으로 Codex가 후속 작업을 수행하고 사용자에게 한국어로 답한다. Laya는 판단을 보조하며, PC 명령 실행·권한 승인·진실성 검증을 대신하지 않는다. 결과가 원문과 충돌하면 원문과 확인 근거를 우선하고 충돌을 알린다. 모델 점수를 실제 정답률로 표현하지 않는다.

## 실행 조건과 실패

- 기존 `ko-en-command`의 스크립트와 설치된 모델을 재사용한다. 영어 Laya와 번역 Qwen을 동시에 메모리에 올리지 않는다. 실행 위치는 기존 스킬의 `KO_EN_RUNTIME` 설정을 따른다.
- 경고가 있는 번역, 실패한 번역, 잘린 Laya 입력은 후속 판단 완료로 처리하지 않는다. 원문을 축약하거나 조건을 삭제해 통과시키지 않는다. 긴 입력은 작업 의미를 유지해 나눈 뒤 범위를 기록한다.
- 실패 시 실패한 단계를 정확히 알린다. 온라인 번역이나 다른 모델로 조용히 대체하지 않는다. 사용자에게 모델이 실행되었다고 보고하려면 실제 결과가 있어야 한다.
- 설치된 영어 체크포인트는 일부 온도 보정값에 런타임 경고를 낼 수 있다. 경고를 숨기거나 점수를 보정 완료 값으로 소개하지 않는다. 기본 요청 유형 분류는 이 용도로 별도 학습·정확도 검증한 모델이 아니며, 모호한 입력에서 `unclear`를 반환할 수 있다. Codex는 대화 맥락으로 보완하며 점수나 `unclear`만을 이유로 불필요한 재질문을 하지 않는다.
- 자동 선택은 `agents/openai.yaml`에서 허용한다. 이는 Codex가 이 스킬을 선택했을 때 적용되는 작업 흐름이다. 모든 채팅을 가로채는 시스템 훅은 아니며, 확실한 호출에는 `$laya-command`를 사용한다.
