# GitHub에 올리는 방법

## 준비된 파일

실행 코드, 테스트, README, 학습 문서, 예제, `.gitignore`, `.gitattributes`, GitHub Actions 설정을 준비했습니다. 별도의 패키지 설치가 없으므로 `requirements.txt`는 필요하지 않습니다.

실제 GitHub 저장소 생성이나 업로드는 아직 수행하지 않았습니다. 아래에서 자신의 계정과 원하는 공개 범위를 선택해 올릴 수 있습니다.

## 방법 A. Git 명령으로 업로드하기

GitHub에서 새 저장소를 만들고 원하는 이름과 공개 범위를 정합니다. 이름은 예를 들어 `mini-redis`로 정할 수 있습니다. 로컬 README가 있으므로 서버 쪽에는 README·gitignore·라이선스를 미리 추가하지 않은 빈 저장소를 만들면 절차가 단순합니다.

프로젝트 폴더에서 터미널을 열고 테스트를 먼저 실행합니다.

```powershell
python -m unittest discover -s tests -v
```

처음 Git 저장소로 만드는 경우 아래를 실행합니다. 이미 Git을 쓰는 폴더라면 먼저 `git status`와 `git remote -v`로 기존 구성을 확인하고 중복 초기화나 원격 주소 추가를 건너뛰세요.

```powershell
git init
git branch -M main
git add .
git status
git commit -m "Implement Mini Redis with LRU, TTL, tests and learning guides"
```

`git status`에서 코드·문서·설정 파일이 포함되고 개인 파일이 없는지 확인합니다. 커밋은 현재 파일 상태를 하나의 기록으로 남기는 작업입니다.

GitHub가 안내하는 자신의 저장소 주소를 복사해 아래의 예시 주소를 바꿉니다. `YOUR_ACCOUNT`와 `YOUR_REPOSITORY`를 그대로 실행하지 마세요.

```powershell
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

로그인이나 권한 승인이 나타나면 자신의 계정으로 진행합니다. 토큰이나 비밀번호를 파일에 적어 업로드하지 마세요.

Git이 작성자 정보를 요구하면 실제 사용할 이름과 이메일을 정해 프로젝트에 설정합니다. 공개 노출을 원하지 않으면 GitHub 계정에서 제공하는 비공개용 이메일을 사용할 수 있습니다.

```powershell
git config user.name "YOUR_NAME"
git config user.email "YOUR_EMAIL"
```

그다음 실패했던 commit과 push를 다시 실행합니다. 이미 origin이 있는 프로젝트에서는 새로 추가하지 말고 기존 주소가 맞는지 확인합니다.

## 방법 B. 웹에서 파일 업로드하기

새 저장소의 파일 업로드 기능을 이용해 프로젝트 파일과 폴더를 올릴 수도 있습니다. 코드 폴더 `mini_redis`, `tests`, `docs`, `examples`와 최상위 README 및 과제 문서를 함께 올립니다.

숨김 항목인 `.github`, `.gitignore`, `.gitattributes`도 빠뜨리지 않아야 자동 테스트와 파일 관리 설정이 적용됩니다. `__pycache__`, `.venv`, 개인 설정 파일은 올리지 않습니다. 숨김 폴더를 포함해 구조를 그대로 올리기 어렵다면 방법 A를 사용하세요.

## 업로드 후 확인

1. 저장소 첫 화면에 README가 보이는지 확인합니다.
2. README에서 학습 자료 링크가 열리는지 확인합니다.
3. Actions에서 Python 테스트 작업의 성공 여부를 확인합니다.
4. 다른 폴더에 복제하거나 ZIP을 내려받아 `python -m mini_redis`가 실행되는지 확인합니다.

GitHub에 코드를 올리는 것 자체가 프로그램을 웹 서비스로 배포하는 것은 아닙니다. 이 프로그램은 내려받은 컴퓨터의 터미널에서 실행합니다.

## 라이선스와 원문

공개 저장소와 오픈소스 사용 허가는 별개입니다. 사용자 이름·저작권자·재배포 허용 조건을 임의로 정하지 않기 위해 LICENSE 파일은 추가하지 않았습니다. 코드의 재사용을 허용하려면 자신의 권한과 의도에 맞는 라이선스를 선택해 LICENSE를 추가하세요.

제공된 과제 원문 `b3-1-mission.md`는 그대로 보존했습니다. 공개 업로드 시 원문의 공개 허용 여부도 본인의 과제 제공 조건에 맞게 확인하세요. 비공개 저장소로 제출할 수도 있습니다.
