"""모의고사 탭 데이터 → docs/mock.json

    python mock_gen.py docs/mock.json

- exams : 수능(1993~) · 평가원 6·9월 모의평가 · 교육청 전국연합학력평가(고1·고2·고3) 목록 (UNTIL 까지)
          시험지·정답 PDF 는 저작권이 출제 기관(한국교육과정평가원·시도교육청)에 있어서 앱에 넣지 않고,
          EBSi 기출문제·검색 링크로 열어요. 앱에서는 OMR 답안지로 풀고, 정답표를 한 번 넣으면 채점해요.
- subjects : 과목별 문항 수·시간 기본값 (시험지에서 다르면 앱에서 바꿀 수 있어요)
- words : 영어 단어 (mock_words.py)
- practice : 앱 안에서 바로 푸는 연습 문제 (직접 만든 문제)
"""
import json, sys
from mock_words import W1, W2, W3

UNTIL = (2026, 10)   # 이 달까지 (올해 10월)

# ---------------- 시험 목록 ----------------
# 해마다 대표 일정 규칙으로 만들어요. 해에 따라 날짜가 미뤄지거나(예: 2020년 3월 → 5월) 빠진 시험이 있을 수 있어요.
EX = []
def ex(y, m, g, org, name, csat=None):
    if (y, m) > UNTIL: return
    d = {"id": f"{y}-{m:02d}-{'s' if org == '수능' else org[0] if org == '평가원' else 'g'}{g}", "y": y, "m": m, "g": g, "org": org, "name": name}
    if csat: d["csat"] = csat
    EX.append(d)

ex(1993, 8, 3, "수능", "1994학년도 대학수학능력시험 1차", 1994)
ex(1993, 11, 3, "수능", "1994학년도 대학수학능력시험 2차", 1994)
for y in range(1994, UNTIL[0] + 1):
    ex(y, 11, 3, "수능", f"{y + 1}학년도 대학수학능력시험", y + 1)
for y in range(2002, UNTIL[0] + 1):
    for m in (6, 9):
        ex(y, m, 3, "평가원", f"{y + 1}학년도 {m}월 모의평가", y + 1)
    for m in (3, 4, 7, 10):
        ex(y, m, 3, "교육청", f"{y}년 {m}월 고3 전국연합학력평가")
    for g in (1, 2):
        for m in (3, 6, 9, 11):
            ex(y, m, g, "교육청", f"{y}년 {m}월 고{g} 전국연합학력평가")
EX.sort(key=lambda e: (-e["y"], -e["m"], -e["g"], e["org"]))
assert len({e["id"] for e in EX}) == len(EX)

# ---------------- 과목 (OMR 기본값) ----------------
# n: 문항 수, min: 시간(분), short: 단답형(숫자로 쓰는) 문항 번호 — 앱에서 시험 연도·학년 보고 고르고, 바꿀 수도 있어요
INQ_SOC = ["생활과 윤리", "윤리와 사상", "한국지리", "세계지리", "동아시아사", "세계사", "경제", "정치와 법", "사회·문화"]
INQ_SCI = ["물리학Ⅰ", "화학Ⅰ", "생명과학Ⅰ", "지구과학Ⅰ", "물리학Ⅱ", "화학Ⅱ", "생명과학Ⅱ", "지구과학Ⅱ"]
SUBJ = {
    "국어": {"n": 45, "min": 80, "icon": "📗"},
    "수학": {"n": 30, "min": 100, "icon": "📐"},
    "영어": {"n": 45, "min": 70, "icon": "🔤", "listen": 17},
    "한국사": {"n": 20, "min": 30, "icon": "🏯"},
    "통합사회": {"n": 20, "min": 30, "icon": "🌏"},
    "통합과학": {"n": 20, "min": 30, "icon": "🔬"},
    **{s: {"n": 20, "min": 30, "icon": "🌏", "inq": "사탐"} for s in INQ_SOC},
    **{s: {"n": 20, "min": 30, "icon": "🔬", "inq": "과탐"} for s in INQ_SCI},
}

# ---------------- 영어 단어 ----------------
LEVELS = [{"lv": 1, "name": "고1 기본", "icon": "🌱"}, {"lv": 2, "name": "고2 필수", "icon": "🌿"}, {"lv": 3, "name": "고3·수능", "icon": "🔥"}]
WORDS, seen = [], set()
for lv, src in ((1, W1), (2, W2), (3, W3)):
    for line in src.strip().splitlines():
        w, k = (s.strip() for s in line.split("|", 1))
        if w.lower() in seen: print("중복 단어:", w, file=sys.stderr); continue
        seen.add(w.lower()); WORDS.append([w, k, lv])

# ---------------- 연습 문제 (직접 만든 문제, 모의고사 유형) ----------------
# q: 문제, p: 지문(선택), c: 보기 5개, a: 정답 번호(1~5), e: 해설
P = {}
def qs(subj, *items): P.setdefault(subj, []).extend(items)
def q(q, c, a, e, p=""):
    assert len(c) == 5 and 1 <= a <= 5, q
    d = {"q": q, "c": c, "a": a, "e": e}
    if p: d["p"] = p
    return d

qs("국어",
   q("다음 중 표준 발음으로 옳은 것은?", ["맑다[막따]", "밟다[발따]", "넓다[넙따]", "읊고[을꼬]", "값을[갑슬]"], 1,
     "겹받침 'ㄺ'은 자음 앞에서 [ㄱ]으로 발음해 '맑다[막따]'. '밟다'는 예외로 [밥ː따], '넓다'는 [널따], '읊고'는 [읍꼬], '값을'은 [갑쓸]이에요."),
   q("'국물[궁물]'을 발음할 때 일어나는 음운 변동은?", ["비음화", "유음화", "구개음화", "된소리되기", "두음 법칙"], 1,
     "받침 'ㄱ'이 뒤의 비음 'ㅁ' 앞에서 비음 [ㅇ]으로 바뀌는 비음화예요."),
   q("다음 중 구개음화가 일어나는 단어는?", ["굳이", "신라", "국물", "먹다", "좋고"], 1,
     "받침 'ㄷ, ㅌ'이 모음 'ㅣ'로 시작하는 형식 형태소를 만나 [ㅈ, ㅊ]으로 바뀌는 것이 구개음화예요. 굳이 → [구지]. 신라[실라]는 유음화예요."),
   q("'그는 매우 빠르게 달렸다.'에서 '매우'의 품사는?", ["명사", "동사", "형용사", "부사", "관형사"], 4,
     "'매우'는 용언 '빠르게'를 꾸미는 부사예요. 관형사는 체언(명사 등)을 꾸며요."),
   q("'내 마음은 호수요'에 쓰인 표현 방법은?", ["직유법", "은유법", "의인법", "반어법", "설의법"], 2,
     "'~같이, ~처럼' 없이 'A는 B이다' 꼴로 빗대는 것이 은유법이에요."),
   q("밑줄 친 말이 바르게 쓰인 것은?", ["그의 침묵은 잘못을 인정한다는 방증이다.", "부장님께 결제를 받으러 갔다.", "몇일 뒤에 다시 만나자.", "왠만하면 같이 가자.", "소문이 금새 퍼졌다."], 1,
     "방증: 간접적으로 증명에 도움이 되는 것. ② 결재(승인) ③ 며칠 ④ 웬만하면 ⑤ 금세 가 맞아요."),
   q("'철수가 영희에게 책을 주었다.'에서 서술어 '주다'의 자릿수는?", ["한 자리", "두 자리", "세 자리", "네 자리", "다섯 자리"], 3,
     "'주다'는 주어(철수가)·부사어(영희에게)·목적어(책을)가 꼭 필요한 세 자리 서술어예요."),
   q("소설에서 '나'가 주인공이 되어 자기 이야기를 들려주는 시점은?", ["1인칭 주인공 시점", "1인칭 관찰자 시점", "3인칭 관찰자 시점", "전지적 작가 시점", "작가 관찰자 시점"], 1,
     "서술자 '나'가 곧 주인공이면 1인칭 주인공 시점, '나'가 다른 인물의 이야기를 하면 1인칭 관찰자 시점이에요."),
   q("다음 중 높임 표현이 바르지 않은 것은?", ["할머니께서 진지를 잡수신다.", "선생님께 여쭈어 보았다.", "아버지께서 댁에 계신다.", "주문하신 커피 나오셨습니다.", "어머니를 모시고 병원에 갔다."], 4,
     "'커피'는 높일 대상이 아니므로 '나왔습니다'가 맞아요(사물 존대 오류)."),
   q("'손이 크다'의 뜻으로 알맞은 것은?", ["씀씀이가 넉넉하다", "힘이 세다", "일을 잘한다", "도둑질을 한다", "솜씨가 좋다"], 1,
     "'손이 크다'는 관용구로, 씀씀이가 후하고 넉넉하다는 뜻이에요."),
)

qs("수학",
   q("이차방정식 x² − 5x + 6 = 0 의 두 근의 합은?", ["−5", "1", "5", "6", "11"], 3, "근과 계수의 관계: 두 근의 합 = −(−5)/1 = 5. (실제로 근은 2, 3)"),
   q("(x + 2)³ 을 전개했을 때 x² 의 계수는?", ["2", "4", "6", "8", "12"], 3, "(x+2)³ = x³ + 3·x²·2 + 3·x·4 + 8 = x³ + 6x² + 12x + 8"),
   q("i²⁰²⁶ 의 값은? (단, i = √−1)", ["1", "i", "−1", "−i", "0"], 3, "i⁴ = 1 이므로 2026 = 4×506 + 2 → i² = −1"),
   q("이차함수 y = x² − 4x + 7 의 최솟값은?", ["1", "2", "3", "4", "7"], 3, "y = (x − 2)² + 3 → x = 2 일 때 최솟값 3"),
   q("다항식 x³ + 2x² − x + 3 을 x − 1 로 나눈 나머지는?", ["1", "3", "4", "5", "7"], 4, "나머지 정리: f(1) = 1 + 2 − 1 + 3 = 5"),
   q("원 x² + y² = 25 와 직선 y = x + 1 의 교점의 개수는?", ["2", "0", "1", "3", "4"], 1, "대입하면 x² + x − 12 = 0 → x = 3, −4. 서로 다른 두 점에서 만나요."),
   q("5명 중에서 회장 1명, 부회장 1명을 뽑는 경우의 수는?", ["10", "20", "25", "60", "120"], 2, "순서가 있는 선택: ₅P₂ = 5 × 4 = 20"),
   q("log₂8 + log₃9 의 값은?", ["4", "5", "6", "7", "8"], 2, "log₂8 = 3, log₃9 = 2 → 5"),
   q("첫째항이 3, 공차가 4인 등차수열의 제10항은?", ["35", "37", "39", "41", "43"], 3, "a₁₀ = 3 + 9 × 4 = 39"),
   q("f(x) = x³ − 3x 일 때, f′(2) 의 값은?", ["9", "3", "6", "12", "15"], 1, "f′(x) = 3x² − 3 → f′(2) = 12 − 3 = 9"),
   q("∫₀² (3x² + 1) dx 의 값은?", ["8", "9", "10", "11", "12"], 3, "[x³ + x]₀² = 8 + 2 = 10"),
   q("sin²θ + cos²θ = 1 일 때, sinθ = 3/5 이고 θ 가 제1사분면의 각이면 tanθ 는?", ["3/5", "4/5", "3/4", "4/3", "5/4"], 3, "cosθ = 4/5 → tanθ = (3/5)/(4/5) = 3/4"),
)

qs("영어",
   q("다음 글의 주제로 가장 적절한 것은?", ["the role of sleep in memory", "how to fall asleep faster", "the history of sleep research", "why dreams are meaningless", "the dangers of studying late"], 1,
     "잠자는 동안 뇌가 낮에 배운 것을 정리·저장한다는 내용 → 기억에서 잠의 역할.",
     "Many students stay up all night before a test, believing that more hours of study mean better results. However, research suggests that sleep is when the brain organizes what it has learned during the day. While we sleep, new information is moved into long-term memory and connected with what we already know. Without enough sleep, this process is cut short, and much of the night's studying may simply be lost."),
   q("다음 글의 밑줄 친 부분 중, 어법상 틀린 것은? (①~⑤ 중 고르기)", ["① which", "② to protect", "③ were", "④ themselves", "⑤ surprisingly"], 3,
     "주어가 'The number of volunteers'(단수, the number of)이므로 were → was 가 맞아요.",
     "The town built a new park, ① which quickly became popular. Residents formed a group ② to protect it, and the number of volunteers ③ were growing every month. They organized cleanups ④ themselves, and ⑤ surprisingly, the park stayed clean all year."),
   q("다음 빈칸에 들어갈 말로 가장 적절한 것은?", ["patience", "speed", "luck", "money", "silence"], 1,
     "작은 변화가 쌓여 오래 걸려서야 결과가 보인다 → 필요한 것은 인내(patience).",
     "When people start a new habit, they often expect quick results. But real change usually comes from small actions repeated over a long time. A single day of exercise will not make you fit, and one page of reading will not make you wise. What matters most is ________: the willingness to keep going even when progress seems invisible."),
   q("다음 글에서 필자가 주장하는 바로 가장 적절한 것은?", ["실수를 배움의 기회로 받아들여야 한다.", "실수를 하지 않도록 철저히 준비해야 한다.", "다른 사람의 실수를 지적해 주어야 한다.", "실수는 숨기는 것이 좋다.", "어려운 과제는 피해야 한다."], 1,
     "'We should treat mistakes not as failures but as chances to learn' 가 주장이에요.",
     "Many of us feel ashamed when we make mistakes, so we try to hide them. Yet every mistake contains useful information about what went wrong and how to do better next time. Students who review their wrong answers improve faster than those who only look at their scores. We should treat mistakes not as failures but as chances to learn."),
   q("다음 글의 요지로 가장 적절한 것은?", ["협력은 개인의 능력보다 더 큰 성과를 낼 수 있다.", "경쟁은 항상 나쁜 결과를 낳는다.", "혼자 일하는 것이 더 효율적이다.", "지도자는 모든 결정을 혼자 내려야 한다.", "능력 있는 사람만 팀에 넣어야 한다."], 1,
     "서로 다른 강점을 합치면 혼자서는 못 하는 일을 해낸다 → 협력의 힘.",
     "A team of average players who trust one another can often beat a team of stars who play alone. Each member brings different strengths, and when those strengths are combined, the group can solve problems no single person could handle. Cooperation, not individual talent alone, is what turns good efforts into great results."),
   q("다음 글의 제목으로 가장 적절한 것은?", ["Small Screens, Big Distractions", "How Phones Were Invented", "The Joy of Online Games", "Why Teachers Love Technology", "Phones Make Us Smarter"], 1,
     "휴대폰 알림이 집중을 깨뜨린다는 내용 → 작은 화면, 큰 방해.",
     "Even when we do not touch it, a phone on the desk can pull our attention away. Every notification sound makes us wonder who is calling, and it takes several minutes to return to deep focus. Students who leave their phones in another room tend to finish homework faster and remember more of what they studied."),
)

qs("한국사",
   q("훈민정음을 창제한 왕은?", ["태조", "태종", "세종", "세조", "성종"], 3, "세종은 1443년 훈민정음을 창제하고 1446년 반포했어요."),
   q("3·1 운동이 일어난 해는?", ["1910년", "1919년", "1926년", "1929년", "1945년"], 2, "1919년 3·1 운동 → 그해 대한민국 임시 정부 수립으로 이어졌어요."),
   q("427년 평양으로 도읍을 옮긴 고구려의 왕은?", ["광개토 대왕", "장수왕", "소수림왕", "고국천왕", "미천왕"], 2, "장수왕은 평양 천도 후 남진 정책을 펼쳐 한강 유역까지 차지했어요."),
   q("갑오개혁(1894)의 내용으로 옳은 것은?", ["과거제 폐지", "훈련도감 설치", "대동법 실시", "호패법 실시", "균역법 실시"], 1, "갑오개혁 때 과거제와 신분제가 폐지됐어요. 나머지는 조선 전기·후기의 정책이에요."),
   q("1919년 대한민국 임시 정부가 수립된 곳은?", ["베이징", "상하이", "블라디보스토크", "도쿄", "하와이"], 2, "여러 임시 정부가 통합되어 상하이에 대한민국 임시 정부가 세워졌어요."),
   q("918년 고려를 세운 인물은?", ["궁예", "견훤", "왕건", "김부", "최승로"], 3, "왕건은 궁예를 몰아내고 고려를 세웠고, 936년 후삼국을 통일했어요."),
   q("6·25 전쟁의 정전 협정이 맺어진 해는?", ["1950년", "1951년", "1953년", "1960년", "1961년"], 3, "1953년 7월 27일 정전 협정이 체결됐어요."),
   q("나당 전쟁에서 승리해 삼국 통일을 완성(676)한 신라의 왕은?", ["진흥왕", "태종 무열왕", "문무왕", "신문왕", "선덕 여왕"], 3, "문무왕은 매소성·기벌포 전투에서 당을 몰아내고 통일을 완성했어요."),
   q("조선 후기 실학자 정약용의 저서는?", ["목민심서", "열하일기", "북학의", "택리지", "동의보감"], 1, "목민심서(정약용), 열하일기(박지원), 북학의(박제가), 택리지(이중환), 동의보감(허준)."),
)

qs("통합사회",
   q("다른 조건이 같을 때, 어떤 상품의 가격이 오르면 일반적으로 나타나는 현상은?", ["수요량 감소", "수요량 증가", "공급량 감소", "수요 곡선 오른쪽 이동", "변화 없음"], 1, "수요 법칙: 가격이 오르면 수요량이 줄어요(곡선 위의 이동)."),
   q("입법·행정·사법 권력을 나누어 서로 견제하게 하는 원리는?", ["권력 분립", "국민 주권", "법치주의", "입헌주의", "다수결"], 1, "권력 분립은 권력 집중과 남용을 막기 위한 원리예요."),
   q("교육받을 권리, 근로의 권리처럼 인간다운 생활을 국가에 요구할 수 있는 권리는?", ["사회권", "자유권", "참정권", "청구권", "평등권"], 1, "사회권은 현대 복지 국가에서 강조되는 권리예요."),
   q("일정 기간 한 나라 안에서 새로 생산된 최종 재화와 서비스의 시장 가치 합은?", ["국내 총생산(GDP)", "국민 총소득(GNI)", "물가 지수", "실업률", "환율"], 1, "GDP는 국적과 관계없이 '나라 안'에서 생산된 것을 계산해요."),
   q("일 년 내내 기온이 높고 강수량이 많아 밀림이 발달하는 기후는?", ["열대 우림 기후", "사막 기후", "온대 겨울 건조 기후", "툰드라 기후", "지중해성 기후"], 1, "적도 주변의 열대 우림 기후는 연중 고온 다습해요."),
   q("어떤 것을 선택해서 포기한 것 중 가장 큰 가치를 무엇이라 하는가?", ["기회비용", "매몰 비용", "편익", "희소성", "효용"], 1, "기회비용 = 선택으로 포기한 대안 중 가장 가치 있는 것."),
   q("시장 실패의 원인으로 볼 수 없는 것은?", ["완전 경쟁", "독과점", "외부 효과", "공공재", "정보의 비대칭"], 1, "완전 경쟁은 시장이 효율적으로 작동하는 조건이에요."),
)

qs("통합과학",
   q("질량 2 kg 인 물체에 4 N 의 알짜힘이 작용할 때 가속도의 크기는?", ["0.5 m/s²", "2 m/s²", "4 m/s²", "6 m/s²", "8 m/s²"], 2, "F = ma → a = 4 / 2 = 2 m/s²"),
   q("원자 번호와 같은 것은?", ["양성자 수", "중성자 수", "질량수", "전자껍질 수", "원자가 전자 수"], 1, "원자 번호 = 양성자 수 (중성 원자에서는 전자 수와도 같아요)"),
   q("식물 세포에서 광합성이 일어나는 곳은?", ["엽록체", "미토콘드리아", "핵", "리보솜", "세포벽"], 1, "엽록체에서 빛에너지로 포도당을 만들어요. 미토콘드리아는 세포 호흡."),
   q("물질이 산소를 얻는 반응은?", ["산화", "환원", "중화", "연소 억제", "용해"], 1, "산소를 얻거나 전자를 잃으면 산화, 산소를 잃거나 전자를 얻으면 환원이에요."),
   q("DNA 를 이루는 기본 단위는?", ["뉴클레오타이드", "아미노산", "포도당", "지방산", "글리세롤"], 1, "뉴클레오타이드 = 인산 + 당 + 염기. 아미노산은 단백질의 단위예요."),
   q("발전기에서 일어나는 주된 에너지 전환은?", ["운동 에너지 → 전기 에너지", "전기 에너지 → 운동 에너지", "화학 에너지 → 빛에너지", "빛에너지 → 화학 에너지", "열에너지 → 화학 에너지"], 1, "코일과 자석이 상대적으로 움직이면 전자기 유도로 전류가 생겨요."),
   q("지구계의 구성 요소가 아닌 것은?", ["핵권", "기권", "수권", "지권", "생물권"], 1, "지구계는 기권·수권·지권·생물권·외권으로 나눠요."),
   q("산과 염기가 반응해 물이 생기는 반응은?", ["중화 반응", "산화 반응", "핵분열", "광합성", "발효"], 1, "H⁺ + OH⁻ → H₂O, 중화 반응에서는 열이 나요(중화열)."),
)

def main(out):
    data = {"until": f"{UNTIL[0]}-{UNTIL[1]:02d}", "exams": EX, "subjects": SUBJ, "soc": INQ_SOC, "sci": INQ_SCI,
            "levels": LEVELS, "words": WORDS, "practice": P}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    print(f"{out}: 시험 {len(EX)}개, 단어 {len(WORDS)}개 ({', '.join(f'{l['name']} {sum(1 for w in WORDS if w[2] == l['lv'])}' for l in LEVELS)}), 연습 문제 {sum(map(len, P.values()))}개")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/mock.json")
