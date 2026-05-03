# AWS CLI 설정 가이드

## 1. AWS CLI 설치

### macOS (Homebrew)
```bash
brew install awscli
```

### macOS (공식 패키지)
```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

### 설치 확인
```bash
aws --version
# 예상 출력: aws-cli/2.x.x Python/3.x.x Darwin/xx.x.x source/x86_64
```

---

## 2. AWS Access Key 생성

### AWS 콘솔에서 Access Key 생성하기

1. **AWS 콘솔 로그인**
   - https://console.aws.amazon.com 접속
   - 계정 로그인

2. **IAM 서비스로 이동**
   - 상단 검색창에 "IAM" 입력
   - IAM 서비스 클릭

3. **사용자 메뉴**
   - 왼쪽 메뉴에서 "사용자" 클릭
   - 본인 사용자 이름 클릭 (또는 새 사용자 생성)

4. **보안 자격 증명 탭**
   - "보안 자격 증명" 탭 클릭
   - "액세스 키" 섹션으로 스크롤

5. **액세스 키 만들기**
   - "액세스 키 만들기" 버튼 클릭
   - 사용 사례 선택: "로컬 코드" 또는 "명령줄 인터페이스(CLI)"
   - "다음" 클릭
   - 설명 태그 추가 (선택사항)
   - "액세스 키 만들기" 클릭

6. **액세스 키 저장**
   - ⚠️ **중요**: 이 화면에서만 Access Key ID와 Secret Access Key를 볼 수 있습니다!
   - Access Key ID 복사
   - Secret Access Key 복사 (또는 "CSV 다운로드" 클릭)
   - 안전한 곳에 저장 (나중에 다시 볼 수 없음)

---

## 3. `aws configure` 실행

### 기본 설정

터미널에서 다음 명령어 실행:

```bash
aws configure
```

### 입력 항목 (4가지)

#### 1. AWS Access Key ID
```
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
```
- 위에서 복사한 **Access Key ID** 입력
- Enter 키 누름

#### 2. AWS Secret Access Key
```
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```
- 위에서 복사한 **Secret Access Key** 입력
- Enter 키 누름

#### 3. Default region name
```
Default region name [None]: ap-northeast-2
```
- **ap-northeast-2** 입력 (서울 리전)
- 다른 리전 사용 시:
  - `us-east-1` (버지니아 북부)
  - `us-west-2` (오레곤)
  - `ap-southeast-1` (싱가포르)
  - 등등...

#### 4. Default output format
```
Default output format [None]: json
```
- **json** 입력 (권장)
- 다른 옵션:
  - `json` - JSON 형식 (가장 일반적)
  - `yaml` - YAML 형식
  - `text` - 텍스트 형식
  - `table` - 표 형식

---

## 4. 설정 확인

### 현재 설정 확인
```bash
aws configure list
```

출력 예시:
```
      Name                    Value             Type    Location
      ----                    -----             ----    --------
   profile                <not set>             None    None
access_key     ****************ABCD shared-credentials-file    ~/.aws/credentials
secret_key     ****************WXYZ shared-credentials-file    ~/.aws/credentials
    region                ap-northeast-2      config-file    ~/.aws/config
```

### 계정 정보 확인
```bash
aws sts get-caller-identity
```

출력 예시:
```json
{
    "UserId": "AIDAIOSFODNN7EXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

---

## 5. 설정 파일 위치

설정은 다음 파일에 저장됩니다:

### 자격 증명 (Credentials)
```bash
~/.aws/credentials
```

내용 예시:
```ini
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### 설정 (Config)
```bash
~/.aws/config
```

내용 예시:
```ini
[default]
region = ap-northeast-2
output = json
```

---

## 6. 여러 프로필 사용하기

여러 AWS 계정을 사용하는 경우:

### 프로필 생성
```bash
aws configure --profile myprofile
```

### 프로필 사용
```bash
aws s3 ls --profile myprofile
```

### 환경 변수로 프로필 지정
```bash
export AWS_PROFILE=myprofile
aws s3 ls
```

---

## 7. 환경 변수로 설정하기

`aws configure` 대신 환경 변수 사용:

```bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_DEFAULT_REGION=ap-northeast-2
```

### 영구적으로 설정 (`.zshrc` 또는 `.bashrc`에 추가)
```bash
echo 'export AWS_ACCESS_KEY_ID=your-key' >> ~/.zshrc
echo 'export AWS_SECRET_ACCESS_KEY=your-secret' >> ~/.zshrc
echo 'export AWS_DEFAULT_REGION=ap-northeast-2' >> ~/.zshrc
source ~/.zshrc
```

---

## 8. 설정 변경하기

### 전체 재설정
```bash
aws configure
```

### 특정 항목만 변경
```bash
# 리전만 변경
aws configure set region us-east-1

# 출력 형식만 변경
aws configure set output yaml

# Access Key 변경
aws configure set aws_access_key_id NEW_ACCESS_KEY
aws configure set aws_secret_access_key NEW_SECRET_KEY
```

---

## 9. 문제 해결

### "Unable to locate credentials" 에러
- `aws configure`를 다시 실행하여 자격 증명 확인
- 환경 변수 확인: `echo $AWS_ACCESS_KEY_ID`

### "Access Denied" 에러
- IAM 사용자에게 필요한 권한이 있는지 확인
- 다음 권한이 필요:
  - ECS (클러스터, 태스크 실행)
  - ECR (이미지 푸시/풀)
  - IAM (역할 생성/관리)
  - Secrets Manager (시크릿 읽기)
  - CloudWatch Logs (로그 그룹 생성)
  - EC2 (VPC, 서브넷, 보안 그룹 조회)

### 권한 확인
```bash
# 현재 사용자 정보
aws sts get-caller-identity

# 연결된 정책 확인 (IAM 콘솔에서 확인)
```

---

## 10. 보안 주의사항

⚠️ **중요한 보안 규칙:**

1. **Access Key는 절대 공유하지 마세요**
   - GitHub에 커밋하지 마세요
   - `.env` 파일을 `.gitignore`에 추가하세요

2. **최소 권한 원칙**
   - 필요한 권한만 부여하세요
   - 관리자 권한은 피하세요

3. **정기적으로 키 교체**
   - 3-6개월마다 새 키 생성
   - 오래된 키는 삭제

4. **MFA 활성화**
   - 가능하면 Multi-Factor Authentication 활성화

---

## 11. 빠른 시작 체크리스트

- [ ] AWS CLI 설치 (`brew install awscli`)
- [ ] AWS 콘솔에서 Access Key 생성
- [ ] `aws configure` 실행
- [ ] `aws sts get-caller-identity`로 확인
- [ ] `./create-iam-roles.sh` 실행
- [ ] `./setup-and-deploy-aws.sh` 실행

---

## 참고 자료

- [AWS CLI 공식 문서](https://docs.aws.amazon.com/cli/latest/userguide/)
- [AWS CLI 설치 가이드](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [AWS 리전 목록](https://docs.aws.amazon.com/general/latest/gr/rande.html)





