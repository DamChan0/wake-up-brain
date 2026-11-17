# wake-up-brain

실제 코드의 흐름을 근거와 함께 배우거나 설명받는 Agent Skill입니다. 학습 효과나 의료적 효능을 약속하지 않습니다.

## 설치

```bash
npx skills add https://github.com/DamChan0/wake-up-brain --skill wake-up-brain
```

## 사용

```text
/wake-up-brain learn [대상]
/wake-up-brain 학습 [대상]
```

```text
/wake-up-brain explain [대상]
/wake-up-brain 설명 [대상]
```

`learn`은 한 번에 예측 질문 하나와 선택적 힌트를 제공하며, `skip` 또는 `answer`로 즉시 해설을 볼 수 있습니다. `explain`은 질문 없이 전체 흐름을 설명합니다. 모드를 생략하면 `learn`입니다.

## HTML 가이드

Python 3.10 이상, 표준 라이브러리만 있으면 됩니다. 아래 명령은 이 저장소 루트에서 실행합니다.

```bash
python3 scripts/render.py examples/session.json guide.html --mode learn
```

`--mode explain`은 질문 없이 상세 설명을 표시합니다. 입력 JSON 형식과 렌더링 규칙은 [references/guide-format.md](references/guide-format.md)에 있습니다.

생성한 HTML 안에서도 학습/설명을 전환할 수 있습니다. 학습 모드는 해설·출력을 접어 먼저 예상하도록 돕고, 설명 모드는 모두 펼쳐 바로 읽게 합니다. 목차와 이전/다음으로 블록을 이동합니다. [공개 예제 HTML](examples/guide.html)은 내려받아 브라우저에서 열 수 있습니다.

합성 예제의 실제 코드: `python3 examples/worker_demo.py`. 이 예제는 순차 실행이며 병렬 실행 예제가 아닙니다.

## 개인정보와 의존성

기본적으로 로컬 소스를 읽고 로컬 HTML을 생성합니다. 외부 업로드나 계정, API, 추적 기능은 사용하지 않습니다. 다이어그램은 선택 사항이며, 설치되어 있고 로컬에서 확인된 도구만 사용합니다.

## 디자인 출처

[Taste Skill](https://www.tasteskill.dev/)의 실제 화면·소스에서 종이색/잉크색, 제목 계층, 정렬과 제품 중심 구성을 추출했습니다. [Impeccable](https://github.com/pbakaus/impeccable)을 설치해 읽기 UI 원칙과 렌더링 검사를 적용했습니다. 원본 에셋·폰트·코드는 포함하지 않습니다. [출처와 적용 범위](references/design-sources.md).

## 확인

```bash
python3 -m unittest discover -s tests -v
python3 scripts/render.py examples/session.json guide.html --mode explain
```

입력/링크 검증, 코드의 비실행 이스케이프, 입력 덮어쓰기 방지를 검사합니다. 브라우저에서는 모드 전환, 해설 펼치기, 키보드·목차 이동, 390/768/1440px 레이아웃을 별도로 확인했습니다. 합성 소스로 두 모드·건너뛰기·주석 지시 무시의 네 프롬프트를 실행한 결과는 [evals/results.json](evals/results.json)에 있습니다. 학습 효과를 입증하는 비교 실험은 아닙니다.

MIT 라이선스. Archify는 선택 도구이며 필수 설치 대상이 아닙니다.
