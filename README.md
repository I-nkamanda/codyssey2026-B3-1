# Mini Redis — 자료구조를 직접 만드는 작은 저장소

Python으로 구현한 CLI 기반 문자열 저장소입니다. 해시맵, 이중 연결 리스트, 최소 힙을 직접 구현해 LRU 메모리 관리와 TTL 만료를 처리합니다. 과제 원문은 [b3-1-mission.md](b3-1-mission.md)입니다.

## 처음 시작하기

Python 3.8 이상이 필요합니다. 외부 패키지는 필요하지 않습니다.

1. 이 폴더를 다운로드하거나 Git으로 복제합니다.
2. 폴더 안에서 터미널을 엽니다. Windows에서는 폴더의 주소창에 `powershell`을 입력할 수 있습니다.
3. 다음 명령을 실행합니다.

```powershell
python --version
python -m mini_redis
```

Windows에서 `python`을 찾지 못하지만 Python이 설치되어 있다면 `py -m mini_redis`를 사용합니다. macOS/Linux에서는 환경에 따라 `python3`를 사용합니다. 이후 문서의 `python`도 같은 방식으로 바꿉니다.

`mini-redis>`가 나타나면 아래 명령을 한 줄씩 입력합니다. 프롬프트 글자 자체는 입력하지 않습니다.

```text
SET name "Alice Kim"
GET name
EXISTS name
DBSIZE
KEYS
EXPIRE name 10
TTL name
INFO memory
DEL name
quit
```

종료하면 저장한 데이터는 사라집니다. 파일 저장 및 네트워크 기능은 구현 범위에 포함되지 않습니다.

## 명령어

- `SET key value`: 저장 또는 덮어쓰기. `OK`를 반환하고 TTL을 초기화하며 최근 사용 순서를 갱신합니다.
- `GET key`: 값이 있으면 `"value"`, 없으면 `(nil)`. 조회 성공 시 최근 사용 순서를 갱신합니다.
- `DEL key`: 삭제했다면 `(integer) 1`, 없으면 `(integer) 0`.
- `EXISTS key`: 존재하면 `(integer) 1`, 없으면 `(integer) 0`.
- `DBSIZE`: 만료되지 않은 전체 키 개수.
- `KEYS`: 전체 키 목록. 순서는 보장하지 않으며 패턴 인자는 받지 않습니다.
- `CONFIG SET maxmemory bytes`: 메모리 한도. 0은 무제한입니다.
- `INFO memory`: `used_memory`, `maxmemory`, `evicted_keys` 출력.
- `EXPIRE key seconds`: 만료 시간 설정. 키가 있으면 1, 없으면 0. 0 이하인 시간은 즉시 삭제합니다.
- `TTL key`: 남은 초를 내림한 정수. 키가 없으면 -2, 시간 제한이 없으면 -1.
- `exit` 또는 `quit`: 종료. Ctrl+C 및 입력 끝(EOF)도 지원합니다.

명령어와 CONFIG/INFO의 옵션은 대소문자를 구분하지 않습니다. 키와 값은 구분합니다. 큰따옴표로 공백을 포함할 수 있으며 빈 문자열도 지원합니다. 파싱은 Python 표준 `shlex` 규칙을 사용하므로 따옴표 밖의 역슬래시는 이스케이프 문자입니다. `#`는 주석 시작이 아니라 일반 문자입니다. 실행 예시의 설명 문장을 명령어로 입력하지 마세요.

## LRU 실행 예시

```text
mini-redis> CONFIG SET maxmemory 30
OK
mini-redis> SET user:1 "Alice"
OK
mini-redis> SET user:2 "Bob"
OK
mini-redis> SET user:3 "Charlie"
OK
mini-redis> GET user:1
(nil)
mini-redis> INFO memory
used_memory:22
maxmemory:30
evicted_keys:1
```

전체 명령 예제는 [examples/demo.txt](examples/demo.txt)에 있습니다. Windows PowerShell에서는 다음과 같이 일괄 실행할 수 있습니다.

```powershell
Get-Content examples/demo.txt | python -m mini_redis
```

## 고등학생 대상 발표·시연

[현장 시연 매뉴얼](docs/LIVE_DEMO_MANUAL.md)은 약 25분 동안 그대로 따라 할 수 있는 발표 대본입니다. 준비 점검, 장면별 입력 명령과 예상 출력, 쉬운 설명 멘트, 학생 참여 질문, 오류 대처법과 10분 축약 순서를 포함합니다.

저장·조회 → LRU 메모리 정리 → TTL 만료 → 오류 처리 순서로 진행합니다. 각 장면은 `quit`으로 종료한 뒤 `python -m mini_redis`로 새로 실행해 시작하세요. TTL 장면은 실제로 기다리는 구간이 있으므로 매뉴얼의 입력 순서를 따라 진행하는 것이 좋습니다. 발표 후에는 [학습 자료](docs/LEARNING_GUIDE.md)와 [실습·해설](docs/EXERCISES.md)로 복습할 수 있습니다.

## 구현 기준과 선택 사항

- 저장소와 보조 인덱스 모두 직접 만든 `HashMap`을 사용합니다. `dict`, `set`, `collections`, `heapq`, `OrderedDict`를 사용하지 않습니다.
- 해시 충돌은 연결 리스트 체이닝으로 해결합니다. 로드 팩터가 0.75를 초과하면 버킷을 두 배로 늘려 재배치합니다.
- LRU 리스트 앞이 최근 사용, 뒤가 가장 오래 사용하지 않은 키입니다. 각 엔트리가 자기 노드를 기억하므로 노드 이동은 O(1)입니다.
- 최소 힙은 `(expire_at, key)`를 저장합니다. 별도 직접 구현한 해시맵이 각 키의 힙 위치를 기억하므로 TTL 교체·취소 시 실제 힙 원소도 삭제합니다.
- 모든 유효한 저장소 연산 시작 시 힙에서 만료된 키를 정리합니다. 입력 대기 중에는 별도 작업을 하지 않습니다. 다음 조회에서는 만료된 데이터를 반환하지 않습니다.
- 메모리는 UTF-8 키 바이트 + 값 바이트의 합입니다. Python 프로세스 전체 메모리나 자료구조 공간을 나타내는 수치가 아닙니다.
- 과제에서 명시하지 않은 CONFIG 한도 축소 시점은 **설정 즉시 LRU 제거**로 정했습니다.
- 단일 엔트리가 한도를 초과하면 OOM을 반환합니다. 덮어쓰기 실패 시 기존의 유효한 값·TTL·LRU 순서를 보존합니다. 정상적인 만료 정리는 먼저 일어납니다.
- 만료와 직접 삭제는 `evicted_keys`에 포함하지 않습니다. 메모리 한도로 제거한 키만 누적합니다.
- CLI 정수는 부호 있는 64비트 범위의 ASCII 십진수로 제한합니다. TTL은 경과 시간을 측정하는 `time.monotonic()`을 기준으로 합니다.

## 파일 안내

```text
mini_redis/
  __main__.py          실행 진입점
  cli.py               파싱, 출력, 반복 입력
  store.py             저장소와 TTL/LRU/메모리 관리
  hash_map.py          해시맵
  linked_list.py       이중 연결 리스트
  min_heap.py          최소 힙과 위치 인덱스
  dynamic_array.py     직접 구현한 동적 배열
tests/                 자동 테스트
examples/demo.txt      실행 명령 모음
docs/
  LIVE_DEMO_MANUAL.md  고등학생 대상 현장 시연 대본
  LEARNING_GUIDE.md    비전공자를 위한 학습 자료
  EXERCISES.md         실습 문제와 해설
  IMPLEMENTATION.md   요구사항 연결 및 설계 설명
  TESTING.md          테스트 실행과 확인 범위
  GITHUB_GUIDE.md     GitHub 업로드 방법
  STACK_QUEUE_DEQUE.md 선택 과제: 스택·큐·덱
.github/workflows/tests.yml  GitHub 자동 테스트
```

## 테스트

프로젝트 최상위 폴더에서 실행합니다.

```powershell
python -m unittest discover -s tests -v
```

로컬 Python 3.14.7에서 기능·자료구조 테스트 24개를 통과했습니다. 무작위 테스트에는 고정된 난수를 사용해 같은 결과를 재현합니다. GitHub Actions는 Python 3.8, 3.12, 3.14 테스트를 실행하도록 구성했습니다. 해당 원격 실행 결과는 업로드 후 확인해야 합니다.

## 학습 및 업로드

처음 배우는 분은 [학습 자료](docs/LEARNING_GUIDE.md) → [실습과 해설](docs/EXERCISES.md) → [구현 설명](docs/IMPLEMENTATION.md) 순서로 읽으세요. [GitHub 업로드 가이드](docs/GITHUB_GUIDE.md)에 웹 업로드와 Git 명령 방식을 모두 설명했습니다.

필수 과제 전체와 선택 과제 중 동적 배열, 스택·큐·덱 문서를 포함합니다. 이진 트리, BST, Pub/Sub는 구현하지 않았습니다. 이 프로젝트는 과제 범위의 교육용 구현이며 실제 Redis 전체 구현과 동작·성능이 동일하다고 주장하지 않습니다.
