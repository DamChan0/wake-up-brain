# HTML 가이드 형식

로컬 Python 3.10 이상 표준 라이브러리 렌더러를 사용한다. `<skill-dir>`은 설치된 스킬의 실제 디렉터리이며, 대상 저장소의 디렉터리와 혼동하지 않는다.

```bash
python3 "<skill-dir>/scripts/render.py" INPUT.json OUTPUT.html --mode learn
python3 "<skill-dir>/scripts/render.py" INPUT.json OUTPUT.html --mode explain
```

`--mode` 기본값은 `learn`이다. 입력과 출력은 서로 달라야 하며, 입력 파일을 덮어쓰지 않는다. 잘못된 JSON 또는 타입은 명확한 오류와 0이 아닌 종료 상태로 처리한다.

## JSON 계약

루트 객체:

- `title`: 문자열
- `summary`: 문자열
- `provenance`: 선택 문자열
- `diagram`: 선택 문자열. 공백·인코딩·역슬래시 없는 상대 `.html` 경로만 허용하며 절대 경로, `..`, 외부 URL, fragment는 거부한다.
- `steps`: 비어 있지 않은 배열

각 step:

- `id`: 소문자 영숫자/하이픈 slug. 중복, 예약된 UI id, 자동 생성되는 `<id>-title`과의 충돌은 거부한다.
- `title`: 문자열
- `source`: 선택 객체. `path` 문자열, 양수 `line`, 선택 `end_line >= line`. 실제 파일의 정확한 범위를 확인한다.
- `before`: 선택 문자열. 없으면 검증된 이전 버전이 없다는 뜻이며 만들지 않는다.
- `code`: 문자열. 소스에서 확인한 리터럴 코드
- `language`: 선택 문자열
- `explanation`: 비어 있지 않은 문자열 배열
- `inputs`: 문자열 배열
- `outputs`: 문자열 배열
- `question`: `{prompt, hint, answer, transfer}` 문자열 객체. `learn`에서는 필수, `explain`에서는 선택.

`source`는 표시용 텍스트일 뿐 링크나 URI가 아니다.

## 출력 동작

- 모든 텍스트와 속성은 HTML 이스케이프한다. 사용자 텍스트에 `eval`이나 `innerHTML`을 사용하지 않는다. 템플릿 토큰이 코드에 들어 있어도 문자 그대로 표시한다.
- 네트워크, 외부 asset, telemetry, 저장소를 사용하지 않는 단일 HTML이다.
- `learn`은 문제를 먼저 보여 주고 해설·출력·정답은 native `<details>`에 숨기되 즉시 열 수 있다. 입력 textarea는 레이블을 가지며 브라우저 메모리에만 둔다. 자동 채점이나 진행 차단은 없다.
- `explain`은 모든 해설을 펼치고 학습 질문을 숨긴다. 자세한 설명을 읽는 데 퀴즈를 요구하지 않는다.
- 모드 전환은 현재 step을 유지한다. 질문이 없는 explain 입력은 학습 전환을 비활성화한다. 이전/다음, 목차, 안정적인 hash deep link, 키보드 접근성, JavaScript 없이 읽을 수 있는 내용을 제공한다. JavaScript가 없으면 작동하지 않는 모드/이전·다음 버튼은 표시하지 않는다.
- 390/768/1440px에서 페이지 가로 넘침이 없어야 한다. 코드는 자체 스크롤을 허용한다. UI 레이블은 한국어다.

## 예시

합성된 공개 안전 데이터만 예시에 사용한다. 실제 비공개 저장소 코드나 경로를 포함하지 않는다.
