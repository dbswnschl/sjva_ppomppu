# sjva_ppomppu
[SJVA](https://sjva.me/)용 [뽐뿌](http://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu) 게시판 키워드 기반의 알리미 플러그인 입니다.

# 설명
원하는 키워드로 즉시 알림을 받을 수 있는 플러그인 입니다.  
뽐뿌에서 제공하는 [rss 데이터](http://www.ppomppu.co.kr/rss.php?id=ppomppu) 를 이용합니다.

# 업데이트
### 0.3.0
#### 여러 게시판 등록 기능 추가
> rss url에 `,` 구분자를 이용하여 여러 게시판 등록 가능  
> ex : 뽐뿌게시판, 해외뽐뿌게시판 : http://www.ppomppu.co.kr/rss.php?id=ppomppu,http://www.ppomppu.co.kr/rss.php?id=ppomppu4

### 0.2.0
#### 직접 크롤링 기능 추가
> RSS 피드가 업데이트 되는 속도가 느려 속도가 중요하신 분들을 위하여,  
> 직접 페이지에 접근하여 크롤링 할 수 있도록 기능을 추가하였습니다.  
> 속도가 빠른 대신, 게시글의 내용은 수집되지 않습니다.

# 가이드
### 설정 페이지  
#### 포함 키워드  
> 키워드 또는 정규식으로 게시글 제목을 검사하여 알람을 발생시킵니다.  
#### 제외 키워드  
> 키워드 또는 정규식으로 게시글 제목을 검사하여 알람을 예외시킵니다.  
#### 알람 봇 ID
> SJVA 설정 > 알림 > Advanced > 정책 에서 사용할 알림 ID를 입력해 주시면, 해당 webhook으로 알람을 전송합니다.  
#### 메시지 포맷
> 알림 받으실 메시지의 포맷을 `{변수명}` 형식에 맞게 작성해 주세요.    
> 사용 가능한 변수의 종류는 다음과 같습니다.  
> title : 게시글 제목  
> link : 게시글 주소  
> author : 작성자 이름  
> description : 게시글 내용  
> pub_date : 게시글 생성 시각  

