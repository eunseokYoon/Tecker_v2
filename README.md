<h2 align="center">2025 Summer Bootcamp Team G</h2>
<h3 align="center">
  🎟️ 티켓 리셀 방지 서비스
</h3>
</br>
<p align="center">
  <img width="1302" height="729" alt="스크린샷 2025-07-30 오후 2 56 22" src="https://github.com/user-attachments/assets/3fc7426c-a384-49a2-8ca2-39be7cc6cbc6" />
</p>

<br>

## 📌 Table of contents
* [Introduction](#-introduction)
* [Workflow](#-workflow)
* [Demo](#-demo)
* [System Architecture](#-system-architecture)
* [ERD](#-erd)
* [Monitoring](#-monitoring)
* [Tech Stack](#-tech-stack)
* [How to start](#-how-to-start)
* [Members](#-members)


## ✏️ Introduction
### Medium  
> 📄 [Ticketaka_Medium](https://medium.com/@juha.kim505/%ED%8B%B0%EC%BC%93-%EB%A6%AC%EC%85%80-%EB%B0%A9%EC%A7%80%EB%A5%BC-%EC%9C%84%ED%95%9C-%ED%8B%B0%EC%BC%93%ED%8C%85-%EC%95%B1-ticketaka-67235b14e675)

티켓 리셀을 방지하기 위해 얼굴 인식 기능을 도입한 서비스입니다.
## 📈 Workflow
저희 서비스를 쉽게 이해할 수 있도록 돕는 워크플로우입니다.
</br>
<img width="958" height="463" alt="스크린샷 2025-07-30 오후 2 57 29" src="https://github.com/user-attachments/assets/6fecd9f9-f215-43ed-9360-3b8a86f45f40" />


## 🎥 Demo
| 기능 | 기능 |
|------|------|
| <img src="https://github.com/user-attachments/assets/18cc0e86-f9a3-47fa-8d0d-ec1176e07f63" alt="홈화면+인기티켓스크롤" /><br/><b>홈 + 인기 티켓</b><br/>인기순으로 정렬된 티켓 확인 가능 | <img src="https://github.com/user-attachments/assets/6823fb48-35b8-42a8-8b63-1a32656653bc" alt="행사선택-좌석선택" /><br/><b>행사 및 좌석 선택</b><br/>시간대와 좌석을 선택 |
| <img src="https://github.com/user-attachments/assets/0ab188e3-62b1-4c86-a1eb-d698d834b124" alt="결제하는거" /><br/><b>티켓 결제</b><br/>결제 수단 및 정보 입력 | <img src="https://github.com/user-attachments/assets/5ad3c373-8195-4944-8965-988c125d6d4a" alt="생체인식+얼굴등록" /><br/><b>생체 인식 + 얼굴 등록</b><br/>본인 인증 후 얼굴 등록 |
| <img src="https://github.com/user-attachments/assets/7ebb8a8e-ce53-4189-bd18-38a5b96d33a5" alt="스푸핑감지" /><br/><b>스푸핑 감지</b><br/>위조 이미지 탐지 AI | <img src="https://github.com/user-attachments/assets/45c97ec2-c769-4b07-86d6-65a8bd986614" alt="동행자등록" /><br/><b>동행자 등록</b><br/>공유받은 사람도 얼굴 등록 필수 |
| <img src="https://github.com/user-attachments/assets/1f117009-9d31-45a4-8454-8e85633aa317" alt="상세정보" /><br/><b>내 티켓 상세정보</b><br/>보유한 티켓 조회 | <img src="https://github.com/user-attachments/assets/eaa3c074-c8e6-433d-a943-6d2889507813" alt="얼굴인증" /><br/><b>입장 전 얼굴 인증</b><br/>티켓 활성화 |
| <img src="https://github.com/user-attachments/assets/81fce9e3-36ee-49a3-9b1f-d17d8d1abdd3" alt="QR코드" /><br/><b>QR 입장 인증</b><br/>최종 입장 확인 |  |


## 📍 System Architecture

<img width="983" height="553" alt="아키텍처1" src="https://github.com/user-attachments/assets/423d7655-7a7d-4753-bcd3-2b51ea0c2ffe" />
</br>
</br>
<img width="1480" height="826" alt="아키텍처2" src="https://github.com/user-attachments/assets/95367dc2-7d78-43d2-8a83-20de7ab29b41" />



## 📊 ERD
<img width="2150" height="852" alt="ticket_erd (2)" src="https://github.com/user-attachments/assets/ef44dbdf-4fed-4cf8-b363-d5332f14d0d6" />

## 🖥️ Monitoring

### cAdvisor
<table>
  <tr>
    <td width="50%">
      <img src="https://github.com/user-attachments/assets/bdbce0e6-f247-4aa1-9c69-6851fd43647d" 
           alt="cAdvisor 1"
           style="width: 100%; height: auto;" />
    </td>
    <td width="50%">
      <img src="https://github.com/user-attachments/assets/2849fe91-5aad-41d3-8440-b5253693d802" 
           alt="cAdvisor 2"
           style="width: 100%; height: auto;" />
    </td>
  </tr>
</table>


### Django
<table>
  <tr>
    <td><img width="1909" height="768" alt="스크린샷 2025-07-31 오전 1 40 11" src="https://github.com/user-attachments/assets/e8601911-0006-43ca-a7a0-75d3d0b0b827" /></td>
  </tr>
</table>

### cAdvisor
<table>
  <tr>
    <td width="50%">
      <img 
        src="https://github.com/user-attachments/assets/694afdd0-c839-4cbb-9e4c-b0e3393ec3aa" 
        alt="node_exporter 1"
        style="width: 100%; height: auto;" />
    </td>
    <td width="50%">
      <img 
        src="https://github.com/user-attachments/assets/f8a840a4-f4c1-46b0-95a8-3b96e7bbb252" 
        alt="node_exporter 2"
        style="width: 100%; height: auto;" />
    </td>
  </tr>
</table>

### Sentry
<table>
  <tr>
    <td><img width="1422" height="769" alt="스크린샷 2025-07-31 오전 12 34 28" src="https://github.com/user-attachments/assets/4886631c-2214-4e29-b1b7-921ee893922f" /></td>
  </tr>
</table>

## 🛠 Tech Stack
<div align="center">
  <table>
    <tr>
      <th>Field</th>
      <th>Technology of use</th>
    </tr>
    <!-- Frontend -->
    <tr>
      <td><b>Frontend</b></td>
      <td>
        <img src="https://img.shields.io/badge/React Native-61DAFB?style=for-the-badge&logo=React&logoColor=black"/>
        <img src="https://img.shields.io/badge/Typescript-3178C6?style=for-the-badge&logo=typescript&logoColor=black">
        <img src="https://img.shields.io/badge/Expo-000000?style=for-the-badge&logo=Expo&logoColor=white"/>
        <img src="https://img.shields.io/badge/axios-5A29E4?style=for-the-badge&logo=axios&logoColor=white">
        <img src="https://img.shields.io/badge/eslint-4B32C3?style=for-the-badge&logo=eslint&logoColor=white">
        <img src="https://img.shields.io/badge/prettier-F7B93E?style=for-the-badge&logo=prettier&logoColor=white">
        <img src="https://img.shields.io/badge/React%20Navigation-CA4245?style=for-the-badge&logo=react&logoColor=white">
      </td>
    </tr>
    <!-- Backend -->
    <tr>
      <td><b>Backend</b></td>
      <td>
        <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">
        <img src="https://img.shields.io/badge/django-092E20?style=for-the-badge&logo=django&logoColor=white"/>
        <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=MySQL&logoColor=white"/>
        <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=Celery&logoColor=white">
        <img src="https://img.shields.io/badge/redis-DC382D?style=for-the-badge&logo=redis&logoColor=white">
        <img src="https://img.shields.io/badge/gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white">
        <img src="https://img.shields.io/badge/Flask-3BABC3?style=for-the-badge&logo=Flask&logoColor=white">
      </td>
    </tr>
    <!-- DevOps -->
    <tr>
      <td><b>DevOps</b></td>
      <td>
        <img src="https://img.shields.io/badge/NGINX-009639?style=for-the-badge&logo=nginx&logoColor=black">
        <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">
        <img src="https://img.shields.io/badge/github%20actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white">
        <img src="https://img.shields.io/badge/Amazon AWS-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white"/>
      </td>
    </tr>
    <td><b>DB</b></td>
      <td>
        <img src="https://img.shields.io/badge/Mysql-4479A1?&style=for-the-badge&logo=Mysql&logoColor=white" />
      </td>
    </tr>
    <tr>
      <td><b>Monitoring</b></td>
      <td>
        <img src="https://img.shields.io/badge/sentry-362D59?style=for-the-badge&logo=sentry&logoColor=white">
        <img src="https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=black">
        <img src="https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=Prometheus&logoColor=black">
        <img src="https://img.shields.io/badge/cAdvisor-1478FF?style=for-the-badge&logo=cAdvisor&Color=black">
        <img src="https://img.shields.io/badge/Node_EXPORTER-0?style=for-the-badge&logo=cAdvisor&Color=black">
      </td>
    </tr>
    <tr>
      <td><b>AI</b></td>
      <td>
        <img src="https://img.shields.io/badge/AWS%20Rekognition-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white">
      </td>
    </tr>
    <tr>
      <td><b>etc</b></td>
      <td>
        <img src="https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white">
        <img src="https://img.shields.io/badge/slack-4A154B?style=for-the-badge&logo=slack&logoColor=white">
        <img src="https://img.shields.io/badge/notion-000000?style=for-the-badge&logo=notion&logoColor=white">
        <img src="https://img.shields.io/badge/zoom-0B5CFF?style=for-the-badge&logo=zoom&logoColor=black">
        <img src="https://img.shields.io/badge/figma-F24E1E?style=for-the-badge&logo=figma&logoColor=white">
        <img src="https://img.shields.io/badge/Swagger-85EA2D?style=for-the-badge&logo=swagger&logoColor=black">
        <img src="https://img.shields.io/badge/postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white">
      </td>
    </tr>
  </table>
</div>


## 📖 How to start
<ol>
  <li>
    <h3>Clone the repository</h3>
    <pre><code>git clone https://github.com/your-org/your-repo.git](https://github.com/2025-summerbootcamp-TeamG/Frontend.git
git clone https://github.com/2025-summerbootcamp-TeamG/Backend.git
</code></pre>
  </li>

  <li>
    <h3>Install dependencies</h3>
    <pre><code>npm install
</code></pre>
  </li>

  <li>
    <h3>Set up environment variables</h3>
    <p>프로젝트 루트에 <code>.env</code> 파일을 생성하고 아래와 같이 설정합니다:</p>
    <pre><code>API_URL=https://api.example.com
SENTRY_DSN=your-sentry-dsn</code></pre>

  <li>
    <h3>iOS 설정 (Mac Only)</h3>
    <p><a href="https://developer.apple.com/xcode/">Xcode</a>와 Cocoapods가 필요합니다.</p>
    <p><b>(1) Cocoapods 설치</b></p>
    <pre><code>sudo gem install cocoapods</code></pre>
    <p><b>(2) Pods 설치</b></p>
    <pre><code>cd ios
pod install
cd ..</code></pre>
  </li>

  <li>
    <h3>Run the development server</h3>
    <pre><code>npx expo start</code></pre>
    <ul>
      <li>🔗 <b>실기기 실행:</b> Expo Go 앱으로 QR 코드 스캔</li>
    </ul>
  </li>

  <li>
    <h3>Build the app</h3>
    <p><b>iOS (Xcode 필요/ 생체인식 포함)</b></p>
    <pre><code>
npx expo prebuild //빌드해주기
cd ios
pod install
cd ..
npx expo start -c</code></pre>
    <p>Xcode에서 App.xcworkspace 파일을 열어 빌드해주세요</p>
    <p><b>Android</b></p>
    <pre>Expo go앱에서 실행 가능합니다.</pre>
  </li>

  <li>
    <h3>Login & Explore</h3>
    <p>앱 실행 후 회원가입/로그인을 진행하고 기능을 체험하세요.</p>
  </li>
</ol>
<hr />

## 🧑‍💻 Members

<table>
  <tr>
    <th>Name</th>
    <th>김주하</th>
    <th>김재영</th>
    <th>김혜연</th>
    <th>류상진</th>
    <th>윤은석</th>
  </tr>
  <tr>
    <th>Profile</th>
      <td style="text-align:center; vertical-align:middle;"><img src="https://github.com/user-attachments/assets/5a246be9-5ccf-4f5b-be65-0255b06a7481" style="width:100px;height:100px;"></td>
      <td style="text-align:center; vertical-align:middle;"><img src="https://github.com/user-attachments/assets/41a1a9c3-6185-4bde-b143-98fc9d09c8f4" style="width:100px;height:100px;"></td>
      <td style="text-align:center; vertical-align:middle;"><img src="https://github.com/user-attachments/assets/169d5462-d4c7-47d1-98d9-324e80b8eccb" style="width:100px;height:100px;"></td>
      <td style="text-align:center; vertical-align:middle;"><img src="https://github.com/user-attachments/assets/ae273739-df03-448f-a654-721a33a0eefb" style="width:100px;height:100px;"></td>
      <td style="text-align:center; vertical-align:middle;">
  <img src="https://github.com/user-attachments/assets/eddbbeab-4152-4ae9-9654-d28412cf0c04" style="width:100px; height:100px;"></td>
  </tr>
  <tr>
    <th>Role</th>
    <td>Leader, Fullstack</td>
    <td>Fullstack</td>
    <td>Fullstack</td>
    <td>Fullstack</td>
    <td>Fullstack</td>
  </tr>
 <tr>
  <th>GitHub</th>
  <td><a href="https://github.com/juha514" target="_blank">@juha514</a></td>
  <td><a href="https://github.com/KJY2523" target="_blank">@KJY2523</a></td>
  <td><a href="https://github.com/hyyeeon" target="_blank">@hyyeeon</a></td>
  <td><a href="https://github.com/Rael0515" target="_blank">@Rael0515</a></td>
  <td><a href="https://github.com/eunseokYoon" target="_blank">@eunseokYoon</a></td>
</tr>
  <tr>
