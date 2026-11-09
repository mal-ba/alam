import json, sys
L = []
def lang(key, name, run, intro, lessons):
    L.append({"key": key, "name": name, "run": run, "intro": intro, "lessons": lessons})
def ls(t, b, code, task="", hint="", ans="", expect="", stdin="", astdin=""):   # 단계(lv)는 아래 LEVELS·more() 에서 붙여요
    d = {"t": t, "b": b.strip(), "code": code.strip("\n") + "\n"}
    if task: d["task"] = task.strip()
    if hint: d["hint"] = hint.strip()
    if ans: d["ans"] = ans.strip("\n") + "\n"
    if expect: d["expect"] = expect
    if stdin: d["stdin"] = stdin
    if astdin: d["astdin"] = astdin
    return d

# ---------------- Python ----------------
lang("py", "🐍 파이썬", "python", "문법이 쉬워서 처음 배우기 좋은 언어예요. 데이터 분석·인공지능·자동화에 많이 써요.", [
ls("print로 출력하기", """
`print()` 는 괄호 안의 내용을 화면에 보여 줘요. 글자(문자열)는 따옴표 `"..."` 로 감싸요.

쉼표로 여러 개를 넣으면 띄어쓰기로 이어서 보여 줘요. 숫자는 따옴표 없이 쓰고, 계산도 돼요.
""", """
print("안녕하세요!")
print("저는", "파이썬을", "배워요")
print(3 + 4)
""", task="자기 이름과 나이를 `print` 로 한 줄에 출력해 보세요. 예) `지훈 17`", hint="`print(\"이름\", 나이)` 처럼 쉼표로 이어요.", ans='print("지훈", 17)'),
ls("변수와 자료형", """
변수는 값을 담아 두는 이름표예요. `이름 = 값` 으로 만들어요.

- `int` 정수: `17`
- `float` 실수: `3.14`
- `str` 문자열: `"코딩"`
- `bool` 참/거짓: `True`, `False`

`type(값)` 으로 자료형을 알 수 있어요. f-문자열 `f"...{변수}..."` 을 쓰면 문장 안에 변수를 넣기 편해요.
""", """
name = "민지"
age = 17
height = 162.5
print(type(age), type(height), type(name))
print(f"{name}은(는) {age}살, 키는 {height}cm")
""", task="`a = 7`, `b = 3` 을 만들고 `7 + 3 = 10` 처럼 덧셈 식과 결과를 f-문자열로 출력해 보세요.", hint="`print(f\"{a} + {b} = {a + b}\")`", ans='a = 7\nb = 3\nprint(f"{a} + {b} = {a + b}")', expect="7 + 3 = 10"),
ls("input으로 입력 받기", """
`input()` 은 사용자가 입력한 한 줄을 **문자열**로 돌려줘요. 숫자로 계산하려면 `int()` 나 `float()` 으로 바꿔야 해요.

아래 **입력값** 칸에 한 줄에 하나씩 입력을 적어 두면, 실행할 때 `input()` 이 차례로 읽어요.
""", """
name = input()
age = int(input())
print(f"{name}님, 내년에는 {age + 1}살이에요!")
""", stdin="서연\n16", task="입력값 두 줄(두 정수)을 받아 두 수의 곱을 출력해 보세요. (입력값 칸을 `6` 과 `7` 로 바꾸면 `42`)", hint="`a = int(input())`, `b = int(input())` 다음 `print(a * b)`", ans="a = int(input())\nb = int(input())\nprint(a * b)", astdin="6\n7", expect="42"),
ls("연산자", """
- 사칙연산: `+` `-` `*` `/` (나누기 결과는 항상 실수)
- `//` 몫, `%` 나머지, `**` 거듭제곱
- 비교: `==` `!=` `>` `<` `>=` `<=` → `True` / `False`
- 논리: `and` `or` `not`
""", """
print(17 / 5, 17 // 5, 17 % 5, 2 ** 10)
x = 15
print(x > 10 and x % 2 == 1)
""", task="초 `3725` 를 `1시간 2분 5초` 형태로 바꿔 출력해 보세요.", hint="시간은 `s // 3600`, 분은 `s % 3600 // 60`, 초는 `s % 60`", ans='s = 3725\nprint(f"{s // 3600}시간 {s % 3600 // 60}분 {s % 60}초")', expect="1시간 2분 5초"),
ls("if 조건문", """
조건이 참일 때만 실행해요. `if` → `elif`(아니면 만약) → `else`(그 밖에) 순서로 써요.

파이썬은 **들여쓰기(스페이스 4칸)** 로 블록을 구분해요. 콜론 `:` 을 잊지 마세요.
""", """
score = int(input())
if score >= 90:
    print("A")
elif score >= 80:
    print("B")
else:
    print("C 이하")
""", stdin="85", task="입력받은 정수가 짝수면 `짝수`, 홀수면 `홀수` 를 출력해 보세요. (입력값 `8` → `짝수`)", hint="`n % 2 == 0` 이면 짝수", ans='n = int(input())\nif n % 2 == 0:\n    print("짝수")\nelse:\n    print("홀수")', astdin="8", expect="짝수"),
ls("for 반복문", """
`for 변수 in 범위:` 로 여러 번 반복해요.

- `range(5)` → 0, 1, 2, 3, 4
- `range(1, 6)` → 1 ~ 5
- `range(0, 10, 2)` → 0, 2, 4, 6, 8

리스트나 문자열도 하나씩 꺼내며 반복할 수 있어요.
""", """
for i in range(1, 6):
    print(i, "번째")
for ch in "코딩":
    print(ch)
""", task="1부터 100까지의 합을 구해 출력해 보세요.", hint="`total = 0` 을 만들고 `for` 안에서 `total += i`", ans="total = 0\nfor i in range(1, 101):\n    total += i\nprint(total)", expect="5050"),
ls("while 반복문", """
`while 조건:` 은 조건이 참인 동안 계속 반복해요. 조건이 언젠가 거짓이 되게 해야 무한 반복을 피해요.

`break` 는 반복을 바로 끝내고, `continue` 는 이번 차례를 건너뛰어요.
""", """
n = 1
while n <= 1000:
    n *= 2
print("처음으로 1000을 넘는 2의 거듭제곱:", n)
""", task="구구단 7단을 `7 x 1 = 7` 부터 `7 x 9 = 63` 까지 출력해 보세요. (for 든 while 이든 좋아요)", hint="`for i in range(1, 10): print(f\"7 x {i} = {7 * i}\")`", ans='for i in range(1, 10):\n    print(f"7 x {i} = {7 * i}")', expect="7 x 9 = 63"),
ls("리스트", """
리스트 `[ ]` 는 여러 값을 순서대로 담아요. 번호(인덱스)는 **0부터** 시작해요.

- `a[0]` 첫 번째, `a[-1]` 마지막
- `a.append(x)` 추가, `len(a)` 길이
- `sum(a)`, `max(a)`, `min(a)`, `sorted(a)`
- 슬라이싱 `a[1:3]` → 1번부터 2번까지
""", """
scores = [88, 92, 75, 100]
scores.append(64)
print(scores[0], scores[-1], len(scores))
print(sorted(scores))
print("평균:", sum(scores) / len(scores))
""", task="`[3, 8, 1, 9, 4]` 에서 가장 큰 수와 가장 작은 수의 차이를 출력해 보세요.", hint="`max(a) - min(a)`", ans="a = [3, 8, 1, 9, 4]\nprint(max(a) - min(a))", expect="8"),
ls("딕셔너리", """
딕셔너리 `{ }` 는 **키: 값** 짝으로 저장해요. 이름으로 값을 찾을 때 좋아요.

- `d["키"]` 값 꺼내기, `d["키"] = 값` 넣기/바꾸기
- `for k, v in d.items():` 짝으로 반복
""", """
grade = {"국어": 90, "수학": 85}
grade["영어"] = 95
for subject, score in grade.items():
    print(subject, score)
""", task="문자열 `\"banana\"` 의 글자별 개수를 딕셔너리로 세어 출력해 보세요. 결과: `{'b': 1, 'a': 3, 'n': 2}`", hint="`cnt[ch] = cnt.get(ch, 0) + 1`", ans='cnt = {}\nfor ch in "banana":\n    cnt[ch] = cnt.get(ch, 0) + 1\nprint(cnt)', expect="{'b': 1, 'a': 3, 'n': 2}"),
ls("함수", """
함수는 자주 쓰는 코드를 이름 붙여 묶어 둔 거예요. `def 이름(매개변수):` 로 만들고 `return` 으로 결과를 돌려줘요.
""", """
def area(w, h):
    return w * h

print(area(3, 4))
print(area(10, 2.5))
""", task="정수 n 을 받아 n 이 소수(1과 자기 자신으로만 나누어지는 수)면 `True` 를 돌려주는 `is_prime(n)` 을 만들고, 1~30 사이 소수를 출력해 보세요.", hint="2부터 n-1 까지 나눠서 나머지가 0인 수가 있으면 소수가 아니에요.", ans="def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, n):\n        if n % i == 0:\n            return False\n    return True\n\nprint([n for n in range(1, 31) if is_prime(n)])", expect="23, 29]"),
ls("문자열 다루기", """
- `s.upper()`, `s.lower()` 대·소문자
- `s.split()` 띄어쓰기로 나누기 → 리스트
- `" ".join(리스트)` 리스트를 이어 붙이기
- `s.replace("a", "b")`, `s[::-1]` 뒤집기
- `"사과" in s` 포함되어 있는지
""", """
s = "I love Python"
print(s.upper())
print(s.split())
print(s[::-1])
print("love" in s)
""", task="입력받은 문장의 단어 개수를 출력해 보세요. (입력값 `오늘 날씨가 정말 좋다` → `4`)", hint="`len(input().split())`", ans="print(len(input().split()))", stdin="오늘 날씨가 정말 좋다"),
])

# ---------------- C ----------------
lang("c", "⚙️ C", "c", "컴퓨터가 실제로 어떻게 움직이는지 배우기 좋은 언어예요. 정보 과목·알고리즘 대회에서 많이 써요. (실행은 Compiler Explorer 서버의 gcc 로 해요)", [
ls("Hello, World!", """
C 프로그램은 `main` 함수에서 시작해요. `printf` 로 출력하고, 문장 끝에는 세미콜론 `;` 을 붙여요.

- `#include <stdio.h>` : 입출력 함수를 쓰겠다는 선언
- `\\n` : 줄 바꿈
- `return 0;` : 정상 종료
""", """
#include <stdio.h>

int main(void) {
    printf("Hello, World!\\n");
    printf("C 언어 시작!\\n");
    return 0;
}
""", task="세 줄에 걸쳐 `*`, `**`, `***` 을 출력해 보세요.", hint="`printf(\"*\\n**\\n***\\n\");`", ans='#include <stdio.h>\n\nint main(void) {\n    printf("*\\n**\\n***\\n");\n    return 0;\n}', expect="***"),
ls("변수와 printf 형식", """
C 는 변수를 만들 때 자료형을 꼭 적어요.

| 자료형 | 뜻 | printf |
|---|---|---|
| `int` | 정수 | `%d` |
| `double` | 실수 | `%f` (`%.2f` 는 소수 둘째 자리) |
| `char` | 글자 하나 | `%c` |
""", """
#include <stdio.h>

int main(void) {
    int age = 17;
    double pi = 3.14159;
    char grade = 'A';
    printf("나이 %d, 원주율 %.2f, 학점 %c\\n", age, pi, grade);
    return 0;
}
""", task="반지름이 `5` 인 원의 넓이를 소수 둘째 자리까지 출력해 보세요. (π = 3.14159)", hint="`double r = 5; printf(\"%.2f\\n\", 3.14159 * r * r);`", ans='#include <stdio.h>\n\nint main(void) {\n    double r = 5;\n    printf("%.2f\\n", 3.14159 * r * r);\n    return 0;\n}', expect="78.54"),
ls("scanf로 입력 받기", """
`scanf("%d", &변수);` 로 정수를 입력받아요. 변수 앞에 `&`(주소)를 꼭 붙여요.

아래 **입력값** 칸에 입력을 적어 두면 실행할 때 읽어요.
""", """
#include <stdio.h>

int main(void) {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("%d + %d = %d\\n", a, b, a + b);
    return 0;
}
""", stdin="12 30", task="정수 두 개를 입력받아 몫과 나머지를 `몫 3 나머지 2` 처럼 출력해 보세요. (입력값 `17 5`)", hint="몫은 `a / b`, 나머지는 `a % b` (정수끼리 나누면 몫만 남아요)", ans='#include <stdio.h>\n\nint main(void) {\n    int a, b;\n    scanf("%d %d", &a, &b);\n    printf("몫 %d 나머지 %d\\n", a / b, a % b);\n    return 0;\n}', astdin="17 5", expect="몫 3 나머지 2"),
ls("if 조건문", """
`if (조건) { ... } else if (조건) { ... } else { ... }`

비교 `==` `!=` `<` `>` , 논리 `&&`(그리고) `||`(또는) `!`(아님). C 에서는 0 이 거짓, 0 이 아닌 값이 참이에요.
""", """
#include <stdio.h>

int main(void) {
    int year;
    scanf("%d", &year);
    if ((year % 4 == 0 && year % 100 != 0) || year % 400 == 0)
        printf("%d년은 윤년\\n", year);
    else
        printf("%d년은 평년\\n", year);
    return 0;
}
""", stdin="2024", task="정수 세 개를 입력받아 가장 큰 수를 출력해 보세요. (입력값 `4 9 2` → `9`)", hint="`int max = a; if (b > max) max = b; if (c > max) max = c;`", ans='#include <stdio.h>\n\nint main(void) {\n    int a, b, c;\n    scanf("%d %d %d", &a, &b, &c);\n    int max = a;\n    if (b > max) max = b;\n    if (c > max) max = c;\n    printf("%d\\n", max);\n    return 0;\n}', astdin="4 9 2", expect="9"),
ls("for · while 반복문", """
`for (시작; 조건; 증가) { ... }` 가 가장 많이 써요. `i++` 는 `i = i + 1` 과 같아요.

`while (조건) { ... }` 은 조건이 참인 동안 반복해요.
""", """
#include <stdio.h>

int main(void) {
    for (int i = 1; i <= 5; i++) {
        for (int j = 0; j < i; j++) printf("*");
        printf("\\n");
    }
    return 0;
}
""", task="1부터 10까지 곱한 값(10!)을 출력해 보세요. 결과 `3628800`", hint="`long long f = 1; for (int i = 1; i <= 10; i++) f *= i;` 출력은 `%lld`", ans='#include <stdio.h>\n\nint main(void) {\n    long long f = 1;\n    for (int i = 1; i <= 10; i++) f *= i;\n    printf("%lld\\n", f);\n    return 0;\n}', expect="3628800"),
ls("배열", """
배열은 같은 자료형 여러 개를 한 줄로 담아요. `int a[5] = {1, 2, 3, 4, 5};` 처럼 만들고 `a[0]` 부터 `a[4]` 까지 써요.

범위를 넘어간 번호(`a[5]`)를 쓰면 엉뚱한 값이 나오거나 프로그램이 멈출 수 있어요!
""", """
#include <stdio.h>

int main(void) {
    int score[5] = {80, 95, 70, 88, 100};
    int sum = 0;
    for (int i = 0; i < 5; i++) sum += score[i];
    printf("합 %d, 평균 %.1f\\n", sum, sum / 5.0);
    return 0;
}
""", task="배열 `{5, 3, 8, 1, 9}` 를 거꾸로 `9 1 8 3 5` 로 출력해 보세요.", hint="`for (int i = 4; i >= 0; i--)`", ans='#include <stdio.h>\n\nint main(void) {\n    int a[5] = {5, 3, 8, 1, 9};\n    for (int i = 4; i >= 0; i--) printf("%d ", a[i]);\n    printf("\\n");\n    return 0;\n}', expect="9 1 8 3 5"),
ls("함수", """
`돌려줄자료형 이름(매개변수) { ... return 값; }` 으로 만들어요. 돌려줄 게 없으면 `void` 예요.

함수는 `main` 보다 위에 만들거나, 위에 선언만 해 두면 돼요.
""", """
#include <stdio.h>

int square(int x) {
    return x * x;
}

int main(void) {
    for (int i = 1; i <= 5; i++)
        printf("%d의 제곱 = %d\\n", i, square(i));
    return 0;
}
""", task="두 정수의 최대공약수를 구하는 `int gcd(int a, int b)` 를 만들고 `gcd(48, 18)` 을 출력해 보세요. 결과 `6`", hint="유클리드 호제법: `b` 가 0 이면 `a`, 아니면 `gcd(b, a % b)`", ans='#include <stdio.h>\n\nint gcd(int a, int b) {\n    return b == 0 ? a : gcd(b, a % b);\n}\n\nint main(void) {\n    printf("%d\\n", gcd(48, 18));\n    return 0;\n}', expect="6"),
ls("포인터 기초", """
포인터는 **변수의 주소**를 담는 변수예요.

- `int *p = &x;` : p 에 x 의 주소를 넣기
- `*p` : 그 주소에 있는 값 (x 와 같음)
- `*p = 10;` 하면 x 가 바뀌어요

함수에 주소를 넘기면 함수 안에서 원래 변수를 바꿀 수 있어요. 그래서 `scanf` 에 `&` 를 붙였던 거예요.
""", """
#include <stdio.h>

void swap(int *a, int *b) {
    int t = *a;
    *a = *b;
    *b = t;
}

int main(void) {
    int x = 1, y = 2;
    swap(&x, &y);
    printf("x=%d y=%d\\n", x, y);
    return 0;
}
""", task="정수의 주소를 받아 그 값을 2배로 만드는 `void twice(int *p)` 를 만들고, `n = 21` 에 써서 `42` 를 출력해 보세요.", hint="`*p = *p * 2;` 그리고 `twice(&n);`", ans='#include <stdio.h>\n\nvoid twice(int *p) {\n    *p = *p * 2;\n}\n\nint main(void) {\n    int n = 21;\n    twice(&n);\n    printf("%d\\n", n);\n    return 0;\n}', expect="42"),
])

# ---------------- JavaScript ----------------
lang("js", "🟨 JS", "js", "웹 페이지를 움직이게 하는 언어예요. 브라우저만 있으면 바로 실행돼요. (결과는 `console.log` 로 봐요)", [
ls("console.log로 출력", """
`console.log()` 로 값을 출력해요. 문장 끝 세미콜론 `;` 은 써도 되고 안 써도 되지만, 쓰는 습관이 좋아요.
""", """
console.log("안녕, 자바스크립트!");
console.log(10 + 5, "개");
""", task="`console.log` 로 `JS 재밌다` 를 3번 출력해 보세요.", hint="같은 줄을 세 번 쓰거나, 다음 강의의 반복문을 미리 써 봐도 돼요.", ans='console.log("JS 재밌다");\nconsole.log("JS 재밌다");\nconsole.log("JS 재밌다");'),
ls("변수 let · const", """
- `let` : 나중에 바꿀 수 있는 변수
- `const` : 바꾸지 않을 값 (상수)

템플릿 문자열은 따옴표 대신 **백틱**(키보드 1 왼쪽 키)으로 감싸고, 그 안에 `${변수}` 로 값을 넣어요.
""", """
const name = "하준";
let level = 1;
level = level + 1;
console.log(`${name}의 레벨: ${level}`);
console.log(typeof name, typeof level);
""", task="`const price = 1200`, `let count = 3` 을 만들고 `총 3600원` 을 출력해 보세요.", hint="`console.log(`총 ${price * count}원`)`", ans="const price = 1200;\nlet count = 3;\nconsole.log(`총 ${price * count}원`);", expect="총 3600원"),
ls("조건문 if", """
`if (조건) { } else if (조건) { } else { }`

비교는 `===`(같다), `!==`(다르다)를 써요. `==` 는 자료형을 멋대로 바꿔서 비교해서 헷갈리기 쉬워요. 논리는 `&&` `||` `!`.
""", """
const temp = 28;
if (temp >= 30) {
  console.log("너무 더워요");
} else if (temp >= 20) {
  console.log("따뜻해요");
} else {
  console.log("쌀쌀해요");
}
console.log(1 == "1", 1 === "1");
""", task="`const n = 15` 가 3과 5의 공배수면 `FizzBuzz`, 3의 배수면 `Fizz`, 5의 배수면 `Buzz`, 아니면 숫자를 출력해 보세요.", hint="15의 배수인지 먼저 검사해야 해요: `n % 15 === 0`", ans='const n = 15;\nif (n % 15 === 0) console.log("FizzBuzz");\nelse if (n % 3 === 0) console.log("Fizz");\nelse if (n % 5 === 0) console.log("Buzz");\nelse console.log(n);', expect="FizzBuzz"),
ls("반복문", """
- `for (let i = 0; i < 5; i++) { }` : 횟수만큼
- `for (const x of 배열) { }` : 배열 값 하나씩
- `while (조건) { }` : 조건이 참인 동안
""", """
for (let i = 1; i <= 3; i++) {
  console.log(`${i}번째 반복`);
}
for (const fruit of ["사과", "배", "포도"]) {
  console.log(fruit);
}
""", task="1부터 20까지 중 짝수만 한 줄에 하나씩 출력해 보세요.", hint="`for (let i = 2; i <= 20; i += 2)`", ans="for (let i = 2; i <= 20; i += 2) console.log(i);", expect="20"),
ls("배열", """
배열 `[ ]` 은 여러 값을 순서대로 담아요.

- `a.push(x)` 끝에 추가, `a.length` 길이
- `a.map(x => x * 2)` 모두 바꾸기
- `a.filter(x => x > 3)` 조건에 맞는 것만
- `a.reduce((합, x) => 합 + x, 0)` 하나로 합치기
""", """
const nums = [4, 8, 15, 16, 23, 42];
console.log(nums.map(x => x * 2));
console.log(nums.filter(x => x % 2 === 1));
console.log(nums.reduce((s, x) => s + x, 0));
""", task="`[\"kim\", \"lee\", \"park\"]` 를 모두 대문자로 바꾼 배열을 출력해 보세요. 결과 `[ 'KIM', 'LEE', 'PARK' ]`", hint="`.map(s => s.toUpperCase())`", ans='console.log(["kim", "lee", "park"].map(s => s.toUpperCase()));', expect="'KIM'"),
ls("함수", """
- `function 이름(a, b) { return a + b; }`
- 화살표 함수: `const 이름 = (a, b) => a + b;`

함수도 값이라서 변수에 넣거나 다른 함수에 넘길 수 있어요.
""", """
function greet(name) {
  return `안녕, ${name}!`;
}
const square = x => x * x;
console.log(greet("도윤"));
console.log(square(9));
""", task="섭씨를 화씨로 바꾸는 화살표 함수 `toF` 를 만들고 `toF(36.5)` 를 출력해 보세요. (화씨 = 섭씨 × 9 / 5 + 32)", hint="`const toF = c => c * 9 / 5 + 32;`", ans="const toF = c => c * 9 / 5 + 32;\nconsole.log(toF(36.5));", expect="97.7"),
ls("객체", """
객체 `{ }` 는 **이름: 값** 짝으로 정보를 묶어요. `obj.이름` 으로 꺼내요.

객체 배열은 실제 프로그램에서 아주 많이 써요 (예: 학생 목록).
""", """
const student = { name: "서윤", grade: 2, scores: [90, 85] };
console.log(student.name, student.grade);
student.club = "코딩부";
console.log(student);
""", task="학생 배열 `[{name:\"A\", score:70}, {name:\"B\", score:95}, {name:\"C\", score:88}]` 에서 점수가 80점 이상인 학생 이름만 출력해 보세요.", hint="`.filter(s => s.score >= 80).map(s => s.name)`", ans='const list = [{ name: "A", score: 70 }, { name: "B", score: 95 }, { name: "C", score: 88 }];\nconsole.log(list.filter(s => s.score >= 80).map(s => s.name));', expect="'B', 'C'"),
ls("웹 페이지 움직이기 (DOM)", """
자바스크립트의 진짜 힘은 **웹 페이지를 바꾸는 것**이에요. 이건 HTML 과 같이 써야 해서, 🌐 HTML 의 마지막 강의 "버튼에 자바스크립트 연결" 에서 직접 해 봐요.

- `document.querySelector("#id")` 요소 찾기
- `요소.textContent = "글자"` 글자 바꾸기
- `요소.addEventListener("click", 함수)` 눌렀을 때 실행
""", """
// 여기(자바스크립트 실행기)에는 웹 페이지가 없어서 document 를 못 써요.
// 🌐 HTML → '버튼에 자바스크립트 연결' 강의에서 해 봐요!
console.log("HTML 탭으로 가 보세요 →");
"""),
])

# ---------------- HTML ----------------
lang("html", "🌐 HTML", "html", "웹 페이지의 뼈대(내용과 구조)를 만드는 언어예요. ▶ 실행을 누르면 바로 아래에 페이지가 보여요.", [
ls("HTML 기본 구조", """
HTML 은 `<태그>내용</태그>` 로 이루어져요. 페이지 전체는 이런 모양이에요.

- `<head>` : 제목 등 보이지 않는 정보
- `<body>` : 화면에 보이는 내용
""", """
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>내 첫 페이지</title>
</head>
<body>
  <h1>안녕하세요!</h1>
  <p>제 첫 웹 페이지예요.</p>
</body>
</html>
""", task="`<body>` 안에 자기소개 문단 `<p>` 를 하나 더 넣어 보세요."),
ls("제목 · 문단 · 강조", """
- `<h1>` ~ `<h6>` : 제목 (숫자가 작을수록 큼)
- `<p>` : 문단, `<br>` : 줄 바꿈
- `<strong>` 굵게(중요), `<em>` 기울임(강조)
- `<hr>` : 가로줄
""", """
<h1>큰 제목</h1>
<h2>중간 제목</h2>
<p>이건 <strong>중요한</strong> 문단이고,<br>이건 <em>강조</em>한 단어예요.</p>
<hr>
<h3>작은 제목</h3>
""", task="좋아하는 과목을 `<h2>` 제목으로, 그 이유를 `<p>` 로 적고 핵심 단어를 `<strong>` 으로 굵게 해 보세요."),
ls("링크와 이미지", """
- 링크: `<a href="주소">글자</a>` (새 탭은 `target="_blank"`)
- 이미지: `<img src="주소" alt="설명" width="100">` (닫는 태그 없음)

`alt` 는 이미지가 안 보일 때나 화면 낭독기가 읽는 설명이라 꼭 써 주세요.
""", """
<p><a href="https://developer.mozilla.org/ko/" target="_blank">MDN 웹 문서 열기</a></p>
<img src="icon-192.png" alt="내 계획표 아이콘" width="96">
""", task="자주 가는 사이트 링크 두 개를 만들어 보세요."),
ls("목록", """
- `<ul>` 순서 없는 목록 (점)
- `<ol>` 순서 있는 목록 (번호)
- 항목은 `<li>`
""", """
<h3>오늘 할 일</h3>
<ul>
  <li>수학 숙제</li>
  <li>영어 단어</li>
</ul>
<h3>라면 끓이는 순서</h3>
<ol>
  <li>물 550ml 끓이기</li>
  <li>면과 스프 넣기</li>
  <li>4분 30초 기다리기</li>
</ol>
""", task="좋아하는 음식 TOP 3 를 `<ol>` 로 만들어 보세요."),
ls("표", """
- `<table>` 표, `<tr>` 한 줄, `<th>` 제목 칸, `<td>` 내용 칸
- `border="1"` 을 주면 칸 테두리가 보여요 (보통은 CSS 로 꾸며요)
""", """
<table border="1">
  <tr><th>교시</th><th>월</th><th>화</th></tr>
  <tr><td>1</td><td>국어</td><td>수학</td></tr>
  <tr><td>2</td><td>영어</td><td>과학</td></tr>
</table>
""", task="3교시 줄을 하나 더 추가하고, 수요일 칸(열)도 추가해 보세요."),
ls("입력 폼", """
사용자에게 입력을 받는 요소예요.

- `<input type="text">` 글자, `type="number"` 숫자, `type="checkbox"` 체크
- `<select><option>` 고르기
- `<button>` 버튼
- `<label>` 은 입력칸 이름표
""", """
<label>이름 <input type="text" placeholder="홍길동"></label><br><br>
<label>학년
  <select><option>1학년</option><option>2학년</option><option>3학년</option></select>
</label><br><br>
<label><input type="checkbox"> 코딩부 가입</label><br><br>
<button>제출</button>
""", task="`type=\"date\"` 로 생일 입력칸을 추가해 보세요."),
ls("버튼에 자바스크립트 연결", """
`<script>` 안에 자바스크립트를 쓰면 페이지를 움직일 수 있어요.

- `document.querySelector("#아이디")` 로 요소를 찾고
- `addEventListener("click", ...)` 로 눌렀을 때 할 일을 정해요
""", """
<h2 id="count">0</h2>
<button id="plus">+1</button>
<button id="reset">초기화</button>
<script>
  let n = 0;
  const out = document.querySelector("#count");
  document.querySelector("#plus").addEventListener("click", () => {
    n++;
    out.textContent = n;
  });
  document.querySelector("#reset").addEventListener("click", () => {
    n = 0;
    out.textContent = n;
  });
</script>
""", task="`-1` 버튼을 추가해서 숫자를 줄일 수 있게 해 보세요.", hint="버튼 `<button id=\"minus\">-1</button>` 을 만들고 `n--` 하는 클릭 이벤트를 추가해요."),
])

# ---------------- CSS ----------------
lang("css", "🎨 CSS", "html", "웹 페이지를 꾸미는 언어예요 (색, 크기, 배치). HTML 의 `<style>` 안에 써요.", [
ls("선택자와 색", """
`선택자 { 속성: 값; }` 모양이에요.

- `p { }` 태그 전체, `.이름 { }` class, `#이름 { }` id
- `color` 글자색, `background` 배경색
- 색은 `red`, `#ff6600`, `rgb(0, 128, 255)` 처럼 써요
""", """
<style>
  body { background: #f4f6fb; }
  h1 { color: #4f46e5; }
  .warn { color: white; background: crimson; }
  #me { color: green; }
</style>
<h1>CSS 시작</h1>
<p class="warn">경고 문구</p>
<p id="me">초록 글자</p>
""", task="`.note` 클래스를 만들어 노란 배경 문단을 하나 꾸며 보세요."),
ls("박스 모델", """
모든 요소는 상자예요. 안쪽부터

`내용` → `padding`(안쪽 여백) → `border`(테두리) → `margin`(바깥 여백)

`border-radius` 로 모서리를 둥글게 할 수 있어요.
""", """
<style>
  .box {
    width: 200px;
    padding: 16px;
    border: 3px solid #4f46e5;
    border-radius: 12px;
    margin: 20px;
    background: #eef;
  }
</style>
<div class="box">padding 16px, margin 20px</div>
<div class="box">두 번째 상자</div>
""", task="상자를 완전히 동그랗게 만들어 보세요. (가로·세로를 같게 하고 `border-radius: 50%`)"),
ls("글꼴과 텍스트", """
- `font-size` 크기, `font-weight` 굵기 (`700` 이 굵게)
- `text-align` 정렬 (`center`), `line-height` 줄 간격
- `text-decoration` 밑줄, `letter-spacing` 자간
""", """
<style>
  h2 { font-size: 32px; text-align: center; letter-spacing: 4px; }
  p { font-size: 18px; line-height: 1.8; }
  a { text-decoration: none; font-weight: 700; color: tomato; }
</style>
<h2>TITLE</h2>
<p>줄 간격이 넓은 문단이에요.<br>읽기 편하죠? <a href="#">밑줄 없는 링크</a></p>
""", task="문단을 가운데 정렬하고 글자를 이탤릭(`font-style: italic`)으로 바꿔 보세요."),
ls("flex로 배치하기", """
`display: flex` 를 주면 안의 요소들이 가로로 나란히 서요.

- `justify-content` : 가로 정렬 (`center`, `space-between`)
- `align-items` : 세로 정렬
- `gap` : 사이 간격
- `flex-wrap: wrap` : 넘치면 다음 줄로
""", """
<style>
  .row { display: flex; gap: 10px; justify-content: center; }
  .card { width: 80px; height: 80px; background: #4f46e5; color: white;
          display: flex; align-items: center; justify-content: center; border-radius: 10px; }
</style>
<div class="row">
  <div class="card">1</div><div class="card">2</div><div class="card">3</div>
</div>
""", task="`justify-content` 를 `space-between` 으로 바꾸고, 카드를 2개 더 늘려 보세요."),
ls("hover와 transition", """
- `:hover` : 마우스를 올렸을 때(휴대폰은 눌렀을 때) 모양
- `transition` : 바뀔 때 부드럽게
- `transform: scale(1.1)` 크게, `rotate(10deg)` 돌리기
""", """
<style>
  .btn { padding: 12px 20px; border: 0; border-radius: 10px; background: #10b981;
         color: white; font-size: 16px; transition: transform .2s, background .2s; }
  .btn:hover { transform: scale(1.1); background: #059669; }
</style>
<button class="btn">눌러 보세요</button>
""", task="마우스를 올리면 버튼이 살짝 돌아가게(`rotate(-5deg)`) 바꿔 보세요."),
ls("반응형 (미디어 쿼리)", """
화면 크기에 따라 다른 모양을 보여 줄 수 있어요.

`@media (max-width: 500px) { ... }` 안의 CSS 는 화면 폭이 500px 이하일 때만 적용돼요.
""", """
<style>
  .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .grid div { background: #fbbf24; padding: 20px; text-align: center; border-radius: 8px; }
  @media (max-width: 500px) {
    .grid { grid-template-columns: 1fr; }
  }
</style>
<div class="grid"><div>A</div><div>B</div><div>C</div></div>
<p>휴대폰(폭 500px 이하)에서는 한 줄에 하나씩 보여요.</p>
""", task="폭이 500px 이하일 때 글자색도 빨간색이 되게 해 보세요."),
])


# ================= 단계(레벨) =================
# 1 기초 · 2 초급 · 3 중급 · 4 상급 · 5 고급 · 6 심화 · 7 최상위 · 8 전문가 · 9 마스터 · 10 전설
LEVELS = [
  ("기초", "🌱", "맨 처음 — 출력·변수"),
  ("초급", "🌿", "기본 문법 익히기"),
  ("중급", "🍀", "기본기 응용"),
  ("상급", "🌳", "구조 만들기 (클래스·재귀)"),
  ("고급", "🔥", "효율적으로 (정렬·탐색·메모리)"),
  ("심화", "💎", "자료구조·DP 입문"),
  ("최상위", "👑", "그래프·백트래킹·애니메이션"),
  ("전문가", "🧠", "고급 기법·함수형·컴포넌트"),
  ("마스터", "🏆", "고급 자료구조·설계 패턴"),
  ("전설", "🐉", "대회·컴파일러 수준"),
]
BASIC = {"py": 4, "c": 3, "js": 3, "html": 4, "css": 3}   # 처음 n개 강의는 기초, 나머지 기존 강의는 초급
for l in L:
    for i, x in enumerate(l["lessons"]):
        x.setdefault("lv", 1 if i < BASIC[l["key"]] else 2)
def more(key, lv, *lessons):
    lg = next(l for l in L if l["key"] == key)
    for x in lessons:
        x["lv"] = lv
        lg["lessons"].append(x)   # 뒤에만 붙여요 (진도 번호 py-1, py-2 … 가 바뀌지 않게)

# ---------------- 🐍 파이썬 중급 ~ 전설 ----------------
more("py", 3,
ls("리스트 컴프리헨션", r"""
`[식 for 변수 in 범위 if 조건]` 한 줄로 리스트를 만들어요. 반복문 + `append` 를 짧게 쓴 거예요.

- `[x * x for x in nums]` 모두 제곱
- `[x for x in nums if x % 2 == 0]` 짝수만
- `{x: x * x for x in range(1, 4)}` 딕셔너리도 돼요
""", r"""
nums = [3, 8, 1, 6, 5]
print([x * x for x in nums])
print([x for x in nums if x % 2 == 0])
print({x: x * x for x in range(1, 4)})
print([[r * c for c in range(1, 4)] for r in range(1, 4)])
""", task="1부터 20까지 중 3의 배수의 합을 컴프리헨션과 `sum` 으로 한 줄에 구해 보세요. 결과 `63`", hint="`sum([x for x in range(1, 21) if x % 3 == 0])`", ans=r"""
print(sum([x for x in range(1, 21) if x % 3 == 0]))
""", expect="63"),
ls("예외 처리 try · except", r"""
프로그램이 오류로 멈추지 않게 **예외(Exception)** 를 잡을 수 있어요.

- `try:` 오류가 날 수 있는 코드
- `except 오류종류:` 그 오류가 나면 실행
- `finally:` 오류가 나든 안 나든 마지막에 실행
- `raise ValueError("메시지")` 로 직접 오류를 일으킬 수도 있어요
""", r"""
for s in ["12", "abc", "0"]:
    try:
        n = int(s)
        print(100 // n)
    except ValueError:
        print(s, "는 숫자가 아니에요")
    except ZeroDivisionError:
        print("0으로 나눌 수 없어요")
    finally:
        print("--")
""", task="입력값 두 줄(정수 a, b)을 받아 `a // b` 를 출력하되, b 가 0 이면 `나눌 수 없음` 을 출력해 보세요. `if` 말고 `try` 로! (입력값 `7`, `0`)", hint="`try: print(a // b)` / `except ZeroDivisionError: print(\"나눌 수 없음\")`", ans=r"""
a = int(input())
b = int(input())
try:
    print(a // b)
except ZeroDivisionError:
    print("나눌 수 없음")
""", stdin="17\n5", astdin="7\n0", expect="나눌 수 없음"),
)
more("py", 4,
ls("클래스와 객체", r"""
**클래스**는 데이터(속성)와 기능(메서드)을 묶은 설계도, **객체**는 그 설계도로 만든 물건이에요.

- `__init__(self, ...)` : 객체를 만들 때 실행 (생성자)
- `self.이름` : 그 객체의 속성
- `__str__` : `print(객체)` 했을 때 보여 줄 글자
- `class 자식(부모):` 로 **상속**하면 부모의 기능을 물려받아요
""", r"""
class Student:
    def __init__(self, name, score):
        self.name = name
        self.score = score

    def grade(self):
        return "A" if self.score >= 90 else "B" if self.score >= 80 else "C"

    def __str__(self):
        return f"{self.name}({self.score}점, {self.grade()})"

class Leader(Student):
    def __str__(self):
        return "⭐반장 " + super().__str__()

print(Student("하윤", 92))
print(Leader("도윤", 81))
""", task="가로 `w`, 세로 `h` 를 받는 `Rect` 클래스에 `area()`(넓이)와 `perimeter()`(둘레) 메서드를 만들고, `Rect(3, 5)` 로 `넓이 15 둘레 16` 을 출력해 보세요.", hint="둘레는 `2 * (self.w + self.h)`", ans=r"""
class Rect:
    def __init__(self, w, h):
        self.w = w
        self.h = h
    def area(self):
        return self.w * self.h
    def perimeter(self):
        return 2 * (self.w + self.h)

r = Rect(3, 5)
print(f"넓이 {r.area()} 둘레 {r.perimeter()}")
""", expect="넓이 15 둘레 16"),
ls("재귀 함수", r"""
함수가 **자기 자신을 다시 부르는 것**을 재귀라고 해요. 꼭 두 가지가 있어야 해요.

- **멈추는 조건** (기저 사례): 더 이상 부르지 않고 바로 답을 돌려줌
- **더 작은 문제로 부르기**: `n` → `n - 1` 처럼 점점 작아져야 함

멈추는 조건이 없으면 끝없이 불러서 `RecursionError` 가 나요. 하노이의 탑은 재귀로 풀면 아주 짧아져요.
""", r"""
def fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)

def hanoi(n, a, b, c):   # n개 원판을 a → c 로 (b 를 거쳐서)
    if n == 0:
        return
    hanoi(n - 1, a, c, b)
    print(f"{n}번 원판: {a} → {c}")
    hanoi(n - 1, b, a, c)

print(fact(5))
hanoi(3, "A", "B", "C")
""", task="피보나치 수 `fib(n)` (fib(1) = fib(2) = 1) 을 재귀로 만들고 `fib(20)` 을 출력해 보세요. 결과 `6765`", hint="`if n <= 2: return 1` 그리고 `return fib(n - 1) + fib(n - 2)`", ans=r"""
def fib(n):
    if n <= 2:
        return 1
    return fib(n - 1) + fib(n - 2)

print(fib(20))
""", expect="6765"),
)
more("py", 5,
ls("정렬 key 와 lambda", r"""
`sorted(목록, key=함수)` 는 각 원소에 함수를 적용한 값을 기준으로 정렬해요. `lambda 인자: 식` 은 이름 없는 짧은 함수예요.

- `key=lambda s: s[1]` 두 번째 값 기준
- `reverse=True` 큰 것부터
- `key=lambda s: (-s[1], s[0])` 점수 높은 순, 같으면 이름 순 (**튜플은 앞에서부터 비교**)
""", r"""
students = [("민준", 85), ("서연", 92), ("지호", 85), ("하은", 78)]
print(sorted(students, key=lambda s: s[1], reverse=True))
print(sorted(students, key=lambda s: (-s[1], s[0])))
words = ["banana", "kiwi", "apple", "fig"]
print(sorted(words, key=len))
print(max(students, key=lambda s: s[1]))
""", task="`[\"pear\", \"fig\", \"apple\", \"kiwi\", \"date\"]` 를 **길이 짧은 순**, 길이가 같으면 **사전 순**으로 정렬해 띄어쓰기로 이어 출력해 보세요. 결과 `fig date kiwi pear apple`", hint="`key=lambda w: (len(w), w)` 그리고 `\" \".join(...)`", ans=r"""
words = ["pear", "fig", "apple", "kiwi", "date"]
print(" ".join(sorted(words, key=lambda w: (len(w), w))))
""", expect="fig date kiwi pear apple"),
ls("이진 탐색", r"""
**정렬된** 목록에서 가운데 값과 비교해 절반씩 버리며 찾는 방법이에요. 100만 개도 20번이면 찾아요. (시간 복잡도 `O(log n)`)

- 찾는 값이 가운데보다 크면 오른쪽 절반, 작으면 왼쪽 절반
- 파이썬에는 `bisect` 모듈이 있어요: `bisect_left(목록, x)` 는 x 를 넣을 자리

이진 탐색은 "조건을 만족하는 가장 큰 x" 같은 **답 자체를 찾는 문제**(매개 변수 탐색)에도 써요.
""", r"""
def bsearch(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        if arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

arr = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]
print(bsearch(arr, 23), bsearch(arr, 7))

import bisect
print(bisect.bisect_left(arr, 20))
""", task="입력받은 정수 n 에 대해 `x * x <= n` 인 가장 큰 정수 x 를 **이진 탐색**으로 구해 보세요. (`**0.5` 금지!) 입력값 `99999999` → `9999`", hint="`lo, hi = 0, n` 으로 시작해 `mid * mid <= n` 이면 답 후보로 두고 `lo = mid + 1`", ans=r"""
n = int(input())
lo, hi, ans = 0, n, 0
while lo <= hi:
    mid = (lo + hi) // 2
    if mid * mid <= n:
        ans = mid
        lo = mid + 1
    else:
        hi = mid - 1
print(ans)
""", stdin="50", astdin="99999999", expect="9999"),
)
more("py", 6,
ls("큐와 너비 우선 탐색 (BFS)", r"""
**BFS** 는 가까운 곳부터 차례로 퍼져 나가며 탐색해요. 그래서 **최단 거리(가장 적은 횟수)** 를 구할 때 써요.

- 큐(`collections.deque`)에 시작점을 넣고
- 하나 꺼내서(`popleft`) 갈 수 있는 곳 중 **아직 안 간 곳**을 큐에 넣기
- 큐가 빌 때까지 반복

리스트의 `pop(0)` 은 느리니까 꼭 `deque` 를 써요.
""", r"""
from collections import deque

maze = ["S.#...",
        ".##.#.",
        "....#E"]
R, C = len(maze), len(maze[0])
dist = [[-1] * C for _ in range(R)]
q = deque([(0, 0)])
dist[0][0] = 0
while q:
    r, c = q.popleft()
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < R and 0 <= nc < C and maze[nr][nc] != "#" and dist[nr][nc] == -1:
            dist[nr][nc] = dist[r][c] + 1
            q.append((nr, nc))
print("E 까지 최단 거리:", dist[2][5])
for row in dist:
    print(" ".join(f"{d:2}" for d in row))
""", task="숫자 `1` 에서 시작해 한 번에 **+1** 또는 **×2** 만 할 수 있을 때, `100` 을 만드는 가장 적은 횟수를 BFS 로 구해 보세요. 결과 `8`", hint="큐에 `(숫자, 횟수)` 를 넣고, 꺼낸 숫자가 100 이면 횟수를 출력. 100 을 넘는 숫자는 버려요.", ans=r"""
from collections import deque

q = deque([(1, 0)])
seen = {1}
while q:
    x, d = q.popleft()
    if x == 100:
        print(d)
        break
    for y in (x + 1, x * 2):
        if y <= 100 and y not in seen:
            seen.add(y)
            q.append((y, d + 1))
""", expect="8"),
ls("동적 계획법 (DP) 기초", r"""
**동적 계획법**은 큰 문제를 작은 문제로 나누고, 작은 문제의 답을 **표에 저장해 두고 다시 쓰는** 방법이에요. 같은 계산을 두 번 하지 않아서 빨라요.

1. `dp[i]` 가 무슨 뜻인지 정하기 (예: i 칸까지 오르는 방법 수)
2. 점화식 세우기 (예: `dp[i] = dp[i-1] + dp[i-2]`)
3. 처음 값 채우고 작은 것부터 계산

동전 문제처럼 **욕심(그리디)으로 큰 동전부터 쓰면 틀리는** 문제도 DP 로는 정확히 풀려요.
""", r"""
# 계단: 한 번에 1칸 또는 2칸 → 10칸 오르는 방법 수
n = 10
dp = [0] * (n + 1)
dp[0] = dp[1] = 1
for i in range(2, n + 1):
    dp[i] = dp[i - 1] + dp[i - 2]
print("계단:", dp[n])

# 동전 1, 5, 7원으로 24원 만들기 (가장 적은 개수)
coins, m = [1, 5, 7], 24
INF = float("inf")
best = [0] + [INF] * m
for x in range(1, m + 1):
    for c in coins:
        if c <= x:
            best[x] = min(best[x], best[x - c] + 1)
print("동전:", best[m], "개  (욕심내면 7+7+7+1+1+1 = 6개)")
""", task="수열 `[10, 20, 10, 30, 20, 50]` 의 **가장 긴 증가하는 부분 수열(LIS)** 길이를 DP 로 구해 보세요. (10, 20, 30, 50) 결과 `4`", hint="`dp[i]` = i 번째로 끝나는 LIS 길이. 앞의 `j < i` 중 `a[j] < a[i]` 이면 `dp[i] = max(dp[i], dp[j] + 1)`", ans=r"""
a = [10, 20, 10, 30, 20, 50]
dp = [1] * len(a)
for i in range(len(a)):
    for j in range(i):
        if a[j] < a[i]:
            dp[i] = max(dp[i], dp[j] + 1)
print(max(dp))
""", expect="4"),
)
more("py", 7,
ls("다익스트라 최단 경로", r"""
간선마다 **비용(거리)** 이 다를 때 한 점에서 모든 점까지의 최단 거리를 구하는 알고리즘이에요. (비용이 음수면 안 돼요)

- 지금까지 가장 가까운 점부터 확정 → **우선순위 큐(`heapq`)** 로 꺼내요
- 그 점을 거쳐 가는 게 더 짧으면 거리를 줄이고(**완화**) 큐에 넣기
- 이미 더 짧은 거리가 확정된 점이 나오면 건너뛰기

시간 복잡도는 `O(E log V)`. 내비게이션 길찾기의 기본이에요.
""", r"""
import heapq

graph = {
    "집": [("학교", 7), ("도서관", 2)],
    "도서관": [("학교", 3), ("학원", 8)],
    "학교": [("학원", 2)],
    "학원": [],
}

def dijkstra(start):
    dist = {v: float("inf") for v in graph}
    dist[start] = 0
    pq = [(0, start)]
    while pq:
        d, v = heapq.heappop(pq)
        if d > dist[v]:
            continue
        for w, cost in graph[v]:
            if d + cost < dist[w]:
                dist[w] = d + cost
                heapq.heappush(pq, (dist[w], w))
    return dist

print(dijkstra("집"))
""", task="""입력 첫 줄에 정점 수 N, 간선 수 M, 다음 M 줄에 `출발 도착 비용` 이 있어요. 1번에서 N번까지의 최단 거리를 출력해 보세요. (한쪽 방향 간선) 입력값:
`4 5` / `1 2 4` / `1 3 1` / `3 2 2` / `2 4 1` / `3 4 5` → `4`""", hint="`graph = [[] for _ in range(N + 1)]` 에 `graph[a].append((b, c))` 로 넣고 위 코드처럼", ans=r"""
import heapq

N, M = map(int, input().split())
graph = [[] for _ in range(N + 1)]
for _ in range(M):
    a, b, c = map(int, input().split())
    graph[a].append((b, c))
dist = [float("inf")] * (N + 1)
dist[1] = 0
pq = [(0, 1)]
while pq:
    d, v = heapq.heappop(pq)
    if d > dist[v]:
        continue
    for w, c in graph[v]:
        if d + c < dist[w]:
            dist[w] = d + c
            heapq.heappush(pq, (dist[w], w))
print(dist[N])
""", astdin="4 5\n1 2 4\n1 3 1\n3 2 2\n2 4 1\n3 4 5", expect="4"),
ls("백트래킹 (N-Queen)", r"""
**백트래킹**은 가능한 선택을 하나씩 해 보다가, **조건에 어긋나면 바로 되돌아가서**(가지치기) 다른 선택을 해 보는 방법이에요.

N-Queen: N×N 체스판에 퀸 N개를 서로 공격하지 못하게 놓는 방법의 수.

- 한 줄(행)에 퀸 하나씩, 위에서부터 놓기
- 같은 열 `col`, 같은 대각선 `r + c`, `r - c` 에 이미 퀸이 있으면 건너뛰기
- 놓았다가 → 다음 줄로 → 돌아오면 **치우기** (`remove`)
""", r"""
def solve(n):
    cols, d1, d2 = set(), set(), set()
    board, out = [], []
    def place(r):
        if r == n:
            out.append(board[:])
            return
        for c in range(n):
            if c in cols or r + c in d1 or r - c in d2:
                continue
            cols.add(c); d1.add(r + c); d2.add(r - c); board.append(c)
            place(r + 1)
            cols.remove(c); d1.remove(r + c); d2.remove(r - c); board.pop()
    place(0)
    return out

sols = solve(4)
print("4-Queen 방법 수:", len(sols))
for c in sols[0]:
    print(" ".join("Q" if i == c else "." for i in range(4)))
""", task="8×8 체스판에서 퀸 8개를 놓는 방법의 수를 구해 보세요. 결과 `92`", hint="위 코드의 `solve(8)` 길이를 출력하면 돼요. 방법만 세려면 `board` 를 저장하지 않고 개수만 더해도 돼요.", ans=r"""
def count(n):
    cols, d1, d2 = set(), set(), set()
    def place(r):
        if r == n:
            return 1
        total = 0
        for c in range(n):
            if c in cols or r + c in d1 or r - c in d2:
                continue
            cols.add(c); d1.add(r + c); d2.add(r - c)
            total += place(r + 1)
            cols.remove(c); d1.remove(r + c); d2.remove(r - c)
        return total
    return place(0)

print(count(8))
""", expect="92"),
)
more("py", 8,
ls("제너레이터와 데코레이터", r"""
**제너레이터**: `return` 대신 `yield` 를 쓰면 값을 **하나씩, 필요할 때만** 만들어요. 끝없는 수열도 메모리 걱정 없이 다룰 수 있어요.

**데코레이터**: 함수를 받아서 기능을 덧붙인 새 함수를 돌려주는 함수. `@이름` 을 함수 위에 붙여요.

- `functools.lru_cache` 는 결과를 기억해 주는 내장 데코레이터예요 (재귀 DP 가 순식간에!)
- `itertools.islice(제너레이터, n)` 처음 n 개만 꺼내기
""", r"""
from functools import lru_cache
from itertools import islice

def logged(func):
    def wrapper(*args):
        result = func(*args)
        print(f"{func.__name__}{args} → {result}")
        return result
    return wrapper

@logged
def add(a, b):
    return a + b

def countdown(n):
    while n > 0:
        yield n
        n -= 1

@lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

add(2, 3)
print(list(countdown(5)))
squares = (x * x for x in range(10**12))   # 1조 개도 괜찮아요
print(list(islice(squares, 5)))
print(fib(200))
""", task="끝없이 피보나치 수(1, 1, 2, 3, 5, …)를 `yield` 하는 제너레이터 `fibs()` 를 만들고, 처음 10개의 합을 출력해 보세요. 결과 `143`", hint="`a, b = 1, 1` / `while True: yield a; a, b = b, a + b` 그리고 `sum(islice(fibs(), 10))`", ans=r"""
from itertools import islice

def fibs():
    a, b = 1, 1
    while True:
        yield a
        a, b = b, a + b

print(sum(islice(fibs(), 10)))
""", expect="143"),
ls("비트마스크와 외판원 문제", r"""
정수의 **비트(0/1)** 하나하나를 "골랐다/안 골랐다" 로 쓰면, 집합을 숫자 하나로 표현할 수 있어요.

- `1 << i` : i 번째만 켜진 수
- `mask & (1 << i)` : i 번째가 들어 있나?
- `mask | (1 << i)` : i 번째 넣기
- `range(1 << n)` : n 개로 만드는 **모든 부분 집합**

**외판원 문제(TSP)**: 모든 도시를 한 번씩 들르고 돌아오는 최소 비용. `dp[mask][i]` = mask 도시들을 들르고 지금 i 에 있을 때 최소 비용. `O(2ⁿ · n²)`
""", r"""
W = [[0, 10, 15, 20],
     [5, 0, 9, 10],
     [6, 13, 0, 12],
     [8, 8, 9, 0]]
n = len(W)
INF = float("inf")
dp = [[INF] * n for _ in range(1 << n)]
dp[1][0] = 0                      # 0번 도시에서 출발
for mask in range(1 << n):
    for i in range(n):
        if dp[mask][i] == INF:
            continue
        for j in range(n):
            if mask & (1 << j):
                continue
            nm = mask | (1 << j)
            dp[nm][j] = min(dp[nm][j], dp[mask][i] + W[i][j])
full = (1 << n) - 1
print("최소 비용:", min(dp[full][i] + W[i][0] for i in range(1, n)))
""", task="`[3, 5, 6, 7, 9]` 의 부분 집합 중 **합이 정확히 15** 인 것이 몇 개인지 비트마스크로 세어 보세요. (6+9, 3+5+7) 결과 `2`", hint="`for mask in range(1 << 5):` 안에서 `mask & (1 << i)` 인 원소만 더해서 15 인지 확인", ans=r"""
a = [3, 5, 6, 7, 9]
cnt = 0
for mask in range(1 << len(a)):
    s = sum(a[i] for i in range(len(a)) if mask & (1 << i))
    if s == 15:
        cnt += 1
print(cnt)
""", expect="2"),
)
more("py", 9,
ls("세그먼트 트리", r"""
배열의 값이 자꾸 바뀌는데 **구간 합**을 계속 물어본다면? 매번 더하면 `O(n)`, 세그먼트 트리는 바꾸기·묻기 모두 `O(log n)` 이에요.

- 트리의 잎(맨 아래)에 원래 값, 위로 갈수록 **두 자식의 합**
- 길이 `2n` 배열 하나로: 잎은 `t[n] ~ t[2n-1]`, 노드 `i` 의 자식은 `2i`, `2i+1`
- 값 바꾸기: 잎을 바꾸고 부모로 올라가며 다시 계산
- 구간 `[l, r)` 묻기: 양 끝에서 올라오며 필요한 노드만 더하기
""", r"""
class SegTree:
    def __init__(self, a):
        self.n = len(a)
        self.t = [0] * (2 * self.n)
        self.t[self.n:] = a
        for i in range(self.n - 1, 0, -1):
            self.t[i] = self.t[2 * i] + self.t[2 * i + 1]
    def update(self, i, v):          # a[i] = v
        i += self.n
        self.t[i] = v
        while i > 1:
            i //= 2
            self.t[i] = self.t[2 * i] + self.t[2 * i + 1]
    def query(self, l, r):           # a[l] + … + a[r-1]
        s = 0
        l += self.n; r += self.n
        while l < r:
            if l & 1: s += self.t[l]; l += 1
            if r & 1: r -= 1; s += self.t[r]
            l //= 2; r //= 2
        return s

st = SegTree([5, 8, 6, 3, 2, 7, 2, 6])
print(st.query(1, 5))   # 8+6+3+2
st.update(3, 10)
print(st.query(1, 5))   # 8+6+10+2
""", task="위 코드를 **구간 최솟값** 트리로 바꿔 보세요. `[5, 8, 6, 3, 2, 7, 2, 6]` 에서 `a[2] ~ a[5]` 의 최솟값 → `a[4] = 9` 로 바꾼 뒤 다시 `a[2] ~ a[5]` 의 최솟값. 두 값을 띄어 출력 → `2 3`", hint="`+` 를 `min` 으로, `s = 0` 을 `s = float(\"inf\")` 로. 구간은 `query(2, 6)`", ans=r"""
class MinTree:
    def __init__(self, a):
        self.n = len(a)
        self.t = [float("inf")] * (2 * self.n)
        self.t[self.n:] = a
        for i in range(self.n - 1, 0, -1):
            self.t[i] = min(self.t[2 * i], self.t[2 * i + 1])
    def update(self, i, v):
        i += self.n
        self.t[i] = v
        while i > 1:
            i //= 2
            self.t[i] = min(self.t[2 * i], self.t[2 * i + 1])
    def query(self, l, r):
        s = float("inf")
        l += self.n; r += self.n
        while l < r:
            if l & 1: s = min(s, self.t[l]); l += 1
            if r & 1: r -= 1; s = min(s, self.t[r])
            l //= 2; r //= 2
        return s

mt = MinTree([5, 8, 6, 3, 2, 7, 2, 6])
x = mt.query(2, 6)
mt.update(4, 9)
print(x, mt.query(2, 6))
""", expect="2 3"),
ls("KMP 문자열 검색", r"""
긴 글(길이 N)에서 단어(길이 M)를 찾을 때, 한 칸씩 밀며 비교하면 `O(N·M)`. **KMP** 는 `O(N + M)` 이에요.

핵심은 **실패 함수 `pi[i]`**: 단어의 `0..i` 부분에서 **앞부분 = 뒷부분** 이 되는 가장 긴 길이. 비교가 틀리면 처음으로 돌아가지 않고 `pi` 만큼만 되돌아가요.

예) `ABABC` → `pi = [0, 0, 1, 2, 0]`
""", r"""
def make_pi(p):
    pi = [0] * len(p)
    j = 0
    for i in range(1, len(p)):
        while j > 0 and p[i] != p[j]:
            j = pi[j - 1]
        if p[i] == p[j]:
            j += 1
            pi[i] = j
    return pi

def kmp(text, p):
    pi, j, found = make_pi(p), 0, []
    for i, ch in enumerate(text):
        while j > 0 and ch != p[j]:
            j = pi[j - 1]
        if ch == p[j]:
            if j == len(p) - 1:
                found.append(i - j)
                j = pi[j]
            else:
                j += 1
    return found

print(make_pi("ABABC"))
print(kmp("ABABDABABCABABC", "ABABC"))
""", task="실패 함수로 문자열의 **가장 짧은 반복 단위 길이**를 구해 보세요. 길이 n 인 문자열이 반복으로 이루어졌다면 `n - pi[-1]` 이에요. `\"abcabcabcabc\"` → `3`, 그리고 `\"abababab\"` → `2`. 두 값을 띄어 `3 2` 로 출력", hint="`n % (n - pi[-1]) == 0` 이면 반복 단위 길이는 `n - pi[-1]`, 아니면 `n`", ans=r"""
def make_pi(p):
    pi = [0] * len(p)
    j = 0
    for i in range(1, len(p)):
        while j > 0 and p[i] != p[j]:
            j = pi[j - 1]
        if p[i] == p[j]:
            j += 1
            pi[i] = j
    return pi

def period(s):
    n = len(s)
    k = n - make_pi(s)[-1]
    return k if n % k == 0 else n

print(period("abcabcabcabc"), period("abababab"))
""", expect="3 2"),
)
more("py", 10,
ls("유니온 파인드와 최소 신장 트리", r"""
**유니온 파인드**: 원소들이 어느 그룹에 속하는지 빠르게 합치고(`union`) 찾는(`find`) 자료구조예요.

- `parent[x]` 를 따라 올라가면 그룹 대표
- **경로 압축**: 찾는 김에 대표에 바로 연결 → 거의 `O(1)`

**크루스칼 알고리즘**: 모든 정점을 가장 싸게 잇는 **최소 신장 트리(MST)**.
간선을 비용 순으로 정렬 → 두 끝이 **다른 그룹**이면 연결(사이클이 안 생기게).
""", r"""
def find(x):
    if parent[x] != x:
        parent[x] = find(parent[x])   # 경로 압축
    return parent[x]

def union(a, b):
    a, b = find(a), find(b)
    if a == b:
        return False
    parent[b] = a
    return True

n = 6
edges = [(1, 2, 3), (1, 3, 1), (2, 3, 7), (2, 4, 5), (3, 4, 2),
         (4, 5, 7), (3, 5, 8), (5, 6, 4), (4, 6, 6)]
parent = list(range(n + 1))
total, used = 0, []
for a, b, w in sorted(edges, key=lambda e: e[2]):
    if union(a, b):
        total += w
        used.append((a, b, w))
print("MST 비용:", total)
print(used)
""", task="정점 1~10 이 있고 친구 관계 `(1,2) (2,3) (4,5) (6,7) (7,8) (8,6) (9,9)` 가 있어요. 친구의 친구도 같은 무리일 때 **무리가 몇 개**인지 유니온 파인드로 세어 보세요. (아무와도 친구가 아니면 혼자 한 무리) 결과 `5`", hint="모두 `union` 한 다음 `len({find(i) for i in range(1, 11)})`", ans=r"""
parent = list(range(11))

def find(x):
    if parent[x] != x:
        parent[x] = find(parent[x])
    return parent[x]

for a, b in [(1, 2), (2, 3), (4, 5), (6, 7), (7, 8), (8, 6), (9, 9)]:
    parent[find(b)] = find(a)
print(len({find(i) for i in range(1, 11)}))
""", expect="5"),
ls("볼록 껍질 (기하 알고리즘)", r"""
평면 위 점들을 고무줄로 감쌌을 때 생기는 다각형이 **볼록 껍질(Convex Hull)** 이에요.

**CCW (외적)**: 세 점 A→B→C 가 왼쪽으로 꺾이면 양수, 오른쪽이면 음수, 일직선이면 0.
`(B-A) × (C-A) = (bx-ax)(cy-ay) - (by-ay)(cx-ax)`

**모노톤 체인**: 점을 x 순으로 정렬 → 아래 껍질, 위 껍질을 스택으로 만들며 **오른쪽으로 꺾이면 빼기**. `O(n log n)`
""", r"""
def ccw(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

def hull(pts):
    pts = sorted(set(pts))
    def half(seq):
        st = []
        for p in seq:
            while len(st) >= 2 and ccw(st[-2], st[-1], p) <= 0:
                st.pop()
            st.append(p)
        return st[:-1]
    return half(pts) + half(pts[::-1])

pts = [(0, 0), (2, 1), (4, 0), (3, 2), (4, 4), (1, 3), (0, 4), (2, 2)]
print(hull(pts))
""", task="위 점들의 볼록 껍질 **넓이**를 신발끈 공식으로 구해 출력해 보세요. 넓이 = |Σ (xᵢ·yᵢ₊₁ − xᵢ₊₁·yᵢ)| / 2. 결과 `16.0`", hint="`h = hull(pts)` 에서 `for i in range(len(h)): j = (i + 1) % len(h)` 로 더하고 `abs(s) / 2`", ans=r"""
def ccw(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

def hull(pts):
    pts = sorted(set(pts))
    def half(seq):
        st = []
        for p in seq:
            while len(st) >= 2 and ccw(st[-2], st[-1], p) <= 0:
                st.pop()
            st.append(p)
        return st[:-1]
    return half(pts) + half(pts[::-1])

pts = [(0, 0), (2, 1), (4, 0), (3, 2), (4, 4), (1, 3), (0, 4), (2, 2)]
h = hull(pts)
s = 0
for i in range(len(h)):
    j = (i + 1) % len(h)
    s += h[i][0] * h[j][1] - h[j][0] * h[i][1]
print(abs(s) / 2)
""", expect="16.0"),
)

# ---------------- ⚙️ C 중급 ~ 전설 ----------------
more("c", 3,
ls("문자열 (char 배열)", r"""
C 의 문자열은 **글자(char) 배열**이고, 끝에 보이지 않는 `'\0'`(널 문자)이 붙어 있어요.

- `char s[50];` 50칸짜리 (글자는 49개까지 + `'\0'`)
- `scanf("%49s", s);` 띄어쓰기 전까지 한 단어 입력 (배열 이름 앞엔 `&` 없음)
- `#include <string.h>` 의 `strlen`(길이), `strcmp`(비교), `strcpy`(복사)
- 글자는 사실 숫자(아스키 코드): `'a'` 는 97, `'A'` 는 65 → 32 를 빼면 대문자
""", r"""
#include <stdio.h>
#include <string.h>

int main(void) {
    char s[50];
    scanf("%49s", s);
    printf("길이 %d\n", (int)strlen(s));
    for (int i = 0; s[i] != '\0'; i++)
        if (s[i] >= 'a' && s[i] <= 'z') s[i] -= 32;
    printf("%s\n", s);
    printf("%d\n", strcmp("apple", "banana") < 0);
    return 0;
}
""", stdin="hello", task="입력받은 단어를 거꾸로 뒤집어 출력해 보세요. (입력값 `coding` → `gnidoc`)", hint="`int n = strlen(s);` 다음 `for (int i = n - 1; i >= 0; i--) printf(\"%c\", s[i]);`", ans=r"""
#include <stdio.h>
#include <string.h>

int main(void) {
    char s[50];
    scanf("%49s", s);
    int n = strlen(s);
    for (int i = n - 1; i >= 0; i--) printf("%c", s[i]);
    printf("\n");
    return 0;
}
""", astdin="coding", expect="gnidoc"),
ls("2차원 배열", r"""
`int a[3][4];` 는 3줄 × 4칸짜리 표예요. `a[줄][칸]` 으로 쓰고, 보통 **이중 for 문**으로 다뤄요.

- `int a[2][3] = {{1, 2, 3}, {4, 5, 6}};`
- 바깥 for: 줄(`i`), 안쪽 for: 칸(`j`)
- 게임 맵, 행렬, 바둑판, 엑셀 같은 표 데이터에 써요
""", r"""
#include <stdio.h>

int main(void) {
    int a[3][3];
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            a[i][j] = (i + 1) * (j + 1);
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) printf("%3d", a[i][j]);
        printf("\n");
    }
    return 0;
}
""", task="3×3 행렬 9개 숫자를 입력받아 **두 대각선의 합**을 `15 15` 처럼 출력해 보세요. (입력값 `1 2 3` / `4 5 6` / `7 8 9`)", hint="왼쪽 위→오른쪽 아래는 `a[i][i]`, 오른쪽 위→왼쪽 아래는 `a[i][2 - i]`", ans=r"""
#include <stdio.h>

int main(void) {
    int a[3][3], d1 = 0, d2 = 0;
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++) scanf("%d", &a[i][j]);
    for (int i = 0; i < 3; i++) {
        d1 += a[i][i];
        d2 += a[i][2 - i];
    }
    printf("%d %d\n", d1, d2);
    return 0;
}
""", astdin="1 2 3\n4 5 6\n7 8 9", expect="15 15"),
)
more("c", 4,
ls("구조체 struct", r"""
**구조체**는 서로 다른 자료형을 하나로 묶은 나만의 자료형이에요.

```
struct Student { char name[20]; int score; };
```

- `struct Student s = {"민서", 90};`
- `s.score` 처럼 **점(.)** 으로 꺼내요
- 포인터라면 `p->score` (화살표)
- `typedef` 를 쓰면 `struct` 를 매번 안 써도 돼요
""", r"""
#include <stdio.h>

typedef struct {
    char name[20];
    int score;
} Student;

int main(void) {
    Student cls[4] = {{"민서", 90}, {"준호", 75}, {"예린", 98}, {"태양", 84}};
    int best = 0;
    for (int i = 1; i < 4; i++)
        if (cls[i].score > cls[best].score) best = i;
    printf("1등: %s (%d점)\n", cls[best].name, cls[best].score);

    Student *p = &cls[1];
    p->score += 10;
    printf("%s 는 이제 %d점\n", p->name, cls[1].score);
    return 0;
}
""", task="`x`, `y` 를 담는 `Point` 구조체를 만들고, 두 점 `(1, 2)`, `(4, 6)` 사이의 **맨해튼 거리** |x1−x2| + |y1−y2| 를 출력해 보세요. 결과 `7`", hint="`int dist(Point a, Point b)` 함수 안에서 `abs` 대신 `a.x > b.x ? a.x - b.x : b.x - a.x` 처럼 계산해도 돼요.", ans=r"""
#include <stdio.h>

typedef struct { int x, y; } Point;

int absv(int v) { return v < 0 ? -v : v; }

int dist(Point a, Point b) {
    return absv(a.x - b.x) + absv(a.y - b.y);
}

int main(void) {
    Point a = {1, 2}, b = {4, 6};
    printf("%d\n", dist(a, b));
    return 0;
}
""", expect="7"),
ls("재귀 함수", r"""
C 에서도 함수가 자기 자신을 부를 수 있어요. **멈추는 조건**을 먼저 쓰는 습관을 들여요.

**분할 정복 거듭제곱**: `aⁿ = (a^(n/2))²` 를 쓰면 곱셈을 n 번이 아니라 log n 번만 해요.

- n 이 짝수: `half * half`
- n 이 홀수: `half * half * a`
""", r"""
#include <stdio.h>

int hanoi(int n) {           // 원판 n개를 옮기는 횟수
    if (n == 0) return 0;
    return 2 * hanoi(n - 1) + 1;
}

int sumDigits(int n) {       // 각 자리 숫자의 합
    if (n < 10) return n;
    return n % 10 + sumDigits(n / 10);
}

int main(void) {
    printf("하노이 10개: %d번\n", hanoi(10));
    printf("98765 의 자릿수 합: %d\n", sumDigits(98765));
    return 0;
}
""", task="분할 정복으로 `long long power(long long a, int n)` 을 만들고 `power(2, 40)` 을 출력해 보세요. 결과 `1099511627776`", hint="`if (n == 0) return 1; long long h = power(a, n / 2);` 그리고 n 이 홀수면 `h * h * a`", ans=r"""
#include <stdio.h>

long long power(long long a, int n) {
    if (n == 0) return 1;
    long long h = power(a, n / 2);
    return n % 2 ? h * h * a : h * h;
}

int main(void) {
    printf("%lld\n", power(2, 40));
    return 0;
}
""", expect="1099511627776"),
)
more("c", 5,
ls("동적 메모리 malloc", r"""
배열 크기를 **실행 중에** 정하고 싶을 때 `malloc` 으로 메모리를 빌려요. (`#include <stdlib.h>`)

- `int *a = malloc(n * sizeof(int));` int n 개 크기
- 다 쓰면 꼭 `free(a);` 로 돌려줘요 (안 하면 **메모리 누수**)
- 빌리지 못하면 `NULL` 을 돌려주니 확인하는 습관!
- `realloc` 으로 크기를 늘릴 수도 있어요
""", r"""
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n;
    scanf("%d", &n);
    int *a = malloc(n * sizeof(int));
    if (a == NULL) return 1;
    long long sum = 0;
    for (int i = 0; i < n; i++) {
        scanf("%d", &a[i]);
        sum += a[i];
    }
    printf("%d개, 합 %lld\n", n, sum);
    free(a);
    return 0;
}
""", stdin="5\n3 1 4 1 5", task="첫 줄에 개수 n, 다음 줄에 n 개 정수를 입력받아 `malloc` 한 배열에 저장하고 **거꾸로** 출력해 보세요. (입력값 `4` / `10 20 30 40` → `40 30 20 10`)", hint="입력은 위 코드처럼, 출력은 `for (int i = n - 1; i >= 0; i--)`. 마지막에 `free(a);`", ans=r"""
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n;
    scanf("%d", &n);
    int *a = malloc(n * sizeof(int));
    if (a == NULL) return 1;
    for (int i = 0; i < n; i++) scanf("%d", &a[i]);
    for (int i = n - 1; i >= 0; i--) printf("%d ", a[i]);
    printf("\n");
    free(a);
    return 0;
}
""", astdin="4\n10 20 30 40", expect="40 30 20 10"),
ls("qsort 로 정렬하기", r"""
`stdlib.h` 의 `qsort(배열, 개수, 원소크기, 비교함수)` 는 빠른 정렬(퀵 정렬)을 해 줘요.

**비교 함수**는 두 원소의 주소(`const void *`)를 받아서

- 앞이 먼저 와야 하면 **음수**
- 같으면 **0**
- 뒤가 먼저 와야 하면 **양수**

를 돌려줘요. 비교 함수만 바꾸면 내림차순, 구조체 정렬도 돼요.
""", r"""
#include <stdio.h>
#include <stdlib.h>

int asc(const void *a, const void *b) {
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);
}

int main(void) {
    int a[] = {42, 7, 19, 3, 88, 25};
    int n = sizeof(a) / sizeof(a[0]);
    qsort(a, n, sizeof(int), asc);
    for (int i = 0; i < n; i++) printf("%d ", a[i]);
    printf("\n");
    return 0;
}
""", task="비교 함수를 바꿔서 `{5, 2, 9, 1, 7}` 을 **내림차순**으로 정렬해 출력해 보세요. 결과 `9 7 5 2 1`", hint="`return (x < y) - (x > y);` 처럼 반대로", ans=r"""
#include <stdio.h>
#include <stdlib.h>

int desc(const void *a, const void *b) {
    int x = *(const int *)a, y = *(const int *)b;
    return (x < y) - (x > y);
}

int main(void) {
    int a[] = {5, 2, 9, 1, 7};
    qsort(a, 5, sizeof(int), desc);
    for (int i = 0; i < 5; i++) printf("%d ", a[i]);
    printf("\n");
    return 0;
}
""", expect="9 7 5 2 1"),
)
more("c", 6,
ls("연결 리스트", r"""
**연결 리스트**는 각 칸(노드)이 **값 + 다음 노드의 주소**를 가지고 줄줄이 이어진 자료구조예요.

- 배열과 달리 중간에 넣고 빼기가 빨라요 (주소만 바꾸면 됨)
- 대신 i 번째를 찾으려면 처음부터 따라가야 해요
- 노드는 `malloc` 으로 만들고, 다 쓰면 하나씩 `free`
""", r"""
#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int val;
    struct Node *next;
} Node;

Node *push(Node *head, int v) {     // 맨 앞에 넣기
    Node *n = malloc(sizeof(Node));
    n->val = v;
    n->next = head;
    return n;
}

int main(void) {
    Node *head = NULL;
    for (int i = 1; i <= 5; i++) head = push(head, i * 10);
    for (Node *p = head; p != NULL; p = p->next) printf("%d -> ", p->val);
    printf("NULL\n");
    while (head) { Node *t = head->next; free(head); head = t; }
    return 0;
}
""", task="1부터 10까지 `push` 한 리스트에서 **모든 노드 값의 합**을 구하는 `int sum(Node *head)` 를 만들어 출력해 보세요. 결과 `55`", hint="`int s = 0; for (Node *p = head; p; p = p->next) s += p->val; return s;`", ans=r"""
#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int val;
    struct Node *next;
} Node;

Node *push(Node *head, int v) {
    Node *n = malloc(sizeof(Node));
    n->val = v;
    n->next = head;
    return n;
}

int sum(Node *head) {
    int s = 0;
    for (Node *p = head; p; p = p->next) s += p->val;
    return s;
}

int main(void) {
    Node *head = NULL;
    for (int i = 1; i <= 10; i++) head = push(head, i);
    printf("%d\n", sum(head));
    while (head) { Node *t = head->next; free(head); head = t; }
    return 0;
}
""", expect="55"),
ls("스택 (괄호 검사)", r"""
**스택**은 마지막에 넣은 것을 가장 먼저 꺼내는(**LIFO**) 자료구조예요. 배열과 `top` 변수 하나로 만들 수 있어요.

- `push`: `st[top++] = x;`
- `pop`: `st[--top]`
- 괄호 짝 맞추기, 되돌리기(Ctrl+Z), 함수 호출, 계산기에 써요

**괄호 검사**: 여는 괄호는 넣고, 닫는 괄호가 나오면 꺼내서 짝이 맞는지 확인!
""", r"""
#include <stdio.h>

int check(const char *s) {
    char st[100];
    int top = 0;
    for (int i = 0; s[i]; i++) {
        char c = s[i];
        if (c == '(' || c == '[' || c == '{') st[top++] = c;
        else if (c == ')' || c == ']' || c == '}') {
            if (top == 0) return 0;
            char o = st[--top];
            if ((c == ')' && o != '(') || (c == ']' && o != '[') || (c == '}' && o != '{')) return 0;
        }
    }
    return top == 0;
}

int main(void) {
    const char *tests[] = {"(a[b]{c})", "([)]", "((()", "{[()()]}"};
    for (int i = 0; i < 4; i++)
        printf("%-10s %s\n", tests[i], check(tests[i]) ? "OK" : "틀림");
    return 0;
}
""", task="**후위 표기식** `\"34+2*\"` (= (3+4)×2) 을 스택으로 계산해 출력해 보세요. 숫자면 push, 연산자면 두 개 꺼내 계산 후 push. 결과 `14`", hint="`if (c >= '0' && c <= '9') st[top++] = c - '0';` 연산자면 `int b = st[--top], a = st[--top];`", ans=r"""
#include <stdio.h>

int main(void) {
    const char *s = "34+2*";
    int st[100], top = 0;
    for (int i = 0; s[i]; i++) {
        char c = s[i];
        if (c >= '0' && c <= '9') { st[top++] = c - '0'; continue; }
        int b = st[--top], a = st[--top];
        if (c == '+') st[top++] = a + b;
        else if (c == '-') st[top++] = a - b;
        else if (c == '*') st[top++] = a * b;
        else if (c == '/') st[top++] = a / b;
    }
    printf("%d\n", st[0]);
    return 0;
}
""", expect="14"),
)
more("c", 7,
ls("큐로 미로 최단 거리 (BFS)", r"""
**BFS(너비 우선 탐색)** 는 큐를 써서 가까운 칸부터 퍼져 나가요. 그래서 처음 도착했을 때가 곧 **최단 거리**예요.

C 에는 큐가 없으니 배열 + `head`, `tail` 두 변수로 만들어요.

- 넣기: `qr[tail] = r; qc[tail] = c; tail++;`
- 꺼내기: `r = qr[head]; c = qc[head]; head++;`
- `head == tail` 이면 큐가 빈 것
""", r"""
#include <stdio.h>

int main(void) {
    const char *maze[] = {"S.#...",
                          ".##.#.",
                          "....#E"};
    int R = 3, C = 6, dist[3][6];
    for (int i = 0; i < R; i++) for (int j = 0; j < C; j++) dist[i][j] = -1;
    int qr[18], qc[18], head = 0, tail = 0;
    int dr[] = {1, -1, 0, 0}, dc[] = {0, 0, 1, -1};
    qr[tail] = 0; qc[tail] = 0; tail++; dist[0][0] = 0;
    while (head < tail) {
        int r = qr[head], c = qc[head]; head++;
        for (int k = 0; k < 4; k++) {
            int nr = r + dr[k], nc = c + dc[k];
            if (nr < 0 || nr >= R || nc < 0 || nc >= C) continue;
            if (maze[nr][nc] == '#' || dist[nr][nc] != -1) continue;
            dist[nr][nc] = dist[r][c] + 1;
            qr[tail] = nr; qc[tail] = nc; tail++;
        }
    }
    printf("E 까지 %d칸\n", dist[2][5]);
    return 0;
}
""", task="""첫 줄에 N M, 다음 N 줄에 `1`(길)과 `0`(벽)으로 된 미로가 있어요. (1,1) 에서 (N,M) 까지 지나는 **칸 수**(시작·끝 포함)를 구해 보세요. 입력값:
`4 6` / `101111` / `101010` / `101011` / `111011` → `15`""", hint="`char g[101][102];` 에 `scanf(\"%s\", g[i]);` 로 한 줄씩. 시작 칸의 dist 를 1 로 두고 BFS", ans=r"""
#include <stdio.h>

char g[101][102];
int dist[101][101], qr[10001], qc[10001];

int main(void) {
    int N, M;
    scanf("%d %d", &N, &M);
    for (int i = 0; i < N; i++) scanf("%101s", g[i]);
    int dr[] = {1, -1, 0, 0}, dc[] = {0, 0, 1, -1}, head = 0, tail = 0;
    qr[tail] = 0; qc[tail] = 0; tail++; dist[0][0] = 1;
    while (head < tail) {
        int r = qr[head], c = qc[head]; head++;
        for (int k = 0; k < 4; k++) {
            int nr = r + dr[k], nc = c + dc[k];
            if (nr < 0 || nr >= N || nc < 0 || nc >= M) continue;
            if (g[nr][nc] != '1' || dist[nr][nc]) continue;
            dist[nr][nc] = dist[r][c] + 1;
            qr[tail] = nr; qc[tail] = nc; tail++;
        }
    }
    printf("%d\n", dist[N - 1][M - 1]);
    return 0;
}
""", astdin="4 6\n101111\n101010\n101011\n111011", expect="15"),
ls("동적 계획법 (LCS · 배낭)", r"""
**LCS(최장 공통 부분 수열)**: 두 문자열에서 순서를 지키며 공통으로 뽑을 수 있는 가장 긴 길이.

`dp[i][j]` = 앞 문자열 i 글자, 뒤 문자열 j 글자까지 봤을 때 LCS 길이

- 글자가 같으면 `dp[i-1][j-1] + 1`
- 다르면 `max(dp[i-1][j], dp[i][j-1])`

DP 표를 채우는 순서(작은 것 → 큰 것)가 중요해요.
""", r"""
#include <stdio.h>
#include <string.h>

int dp[101][101];

int main(void) {
    const char *a = "ACAYKP", *b = "CAPCAK";
    int n = strlen(a), m = strlen(b);
    for (int i = 1; i <= n; i++)
        for (int j = 1; j <= m; j++) {
            if (a[i - 1] == b[j - 1]) dp[i][j] = dp[i - 1][j - 1] + 1;
            else dp[i][j] = dp[i - 1][j] > dp[i][j - 1] ? dp[i - 1][j] : dp[i][j - 1];
        }
    printf("LCS 길이: %d\n", dp[n][m]);   // ACAK
    return 0;
}
""", task="""**0/1 배낭 문제**: 무게 한도 K 인 가방에 물건(무게, 가치)을 골라 넣어 가치 합을 최대로. 첫 줄 N K, 다음 N 줄 `무게 가치`. 입력값:
`4 7` / `6 13` / `4 8` / `3 6` / `5 12` → `14`""", hint="`dp[w]` = 무게 w 이하일 때 최대 가치. 물건마다 `for (w = K; w >= 무게; w--) dp[w] = max(dp[w], dp[w - 무게] + 가치);` (**거꾸로** 돌아야 한 번씩만 써요)", ans=r"""
#include <stdio.h>

int dp[100001];

int main(void) {
    int N, K;
    scanf("%d %d", &N, &K);
    for (int i = 0; i < N; i++) {
        int w, v;
        scanf("%d %d", &w, &v);
        for (int j = K; j >= w; j--)
            if (dp[j - w] + v > dp[j]) dp[j] = dp[j - w] + v;
    }
    printf("%d\n", dp[K]);
    return 0;
}
""", astdin="4 7\n6 13\n4 8\n3 6\n5 12", expect="14"),
)
more("c", 8,
ls("비트 연산", r"""
정수를 **2진수 비트** 단위로 다루는 연산이에요. 아주 빠르고, 하드웨어·암호·게임·알고리즘에서 많이 써요.

| 연산 | 뜻 | 예 (6=110, 3=011) |
|---|---|---|
| `&` | 둘 다 1 | `6 & 3` = 2 |
| `\|` | 하나라도 1 | `6 \| 3` = 7 |
| `^` | 서로 다르면 1 | `6 ^ 3` = 5 |
| `<<` `>>` | 왼쪽·오른쪽으로 밀기 | `1 << 4` = 16 |

- `n & (n - 1)` 은 가장 낮은 1 비트를 지워요 → 0 이면 **2의 거듭제곱**
""", r"""
#include <stdio.h>

int popcount(unsigned x) {          // 1 인 비트 개수
    int c = 0;
    while (x) { x &= x - 1; c++; }
    return c;
}

int main(void) {
    printf("%d %d %d\n", 6 & 3, 6 | 3, 6 ^ 3);
    printf("1 << 10 = %d, 1000 >> 3 = %d\n", 1 << 10, 1000 >> 3);
    printf("255 의 1 비트 수: %d\n", popcount(255));
    for (int n = 60; n <= 64; n++)
        printf("%d 는 2의 거듭제곱? %s\n", n, (n & (n - 1)) == 0 ? "예" : "아니오");
    return 0;
}
""", task="입력받은 정수를 **2진수**로 출력해 보세요. 비트 연산 `>>` 와 `&` 를 써서! (입력값 `13` → `1101`)", hint="가장 높은 비트부터: `for (int i = 30; i >= 0; i--)` 에서 `(n >> i) & 1` 을 보고, 처음 1 이 나오기 전의 0 은 건너뛰기", ans=r"""
#include <stdio.h>

int main(void) {
    int n, started = 0;
    scanf("%d", &n);
    for (int i = 30; i >= 0; i--) {
        int b = (n >> i) & 1;
        if (b) started = 1;
        if (started) printf("%d", b);
    }
    if (!started) printf("0");
    printf("\n");
    return 0;
}
""", stdin="42", astdin="13", expect="1101"),
ls("함수 포인터", r"""
함수도 메모리에 주소가 있어서, **함수를 가리키는 포인터**를 만들 수 있어요.

- `int (*op)(int, int) = add;` → `op(2, 3)` 은 `add(2, 3)`
- 함수를 다른 함수에 **인자로 넘길 수** 있어요 (`qsort` 의 비교 함수가 바로 이거!)
- 함수 포인터 배열로 메뉴·계산기·상태 기계를 깔끔하게 만들어요
""", r"""
#include <stdio.h>

int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }
int mul(int a, int b) { return a * b; }

int main(void) {
    int (*ops[])(int, int) = {add, sub, mul};
    const char *name = "+-*";
    for (int i = 0; i < 3; i++)
        printf("12 %c 4 = %d\n", name[i], ops[i](12, 4));
    return 0;
}
""", task="배열의 모든 원소에 함수를 적용하는 `void map(int *a, int n, int (*f)(int))` 를 만들고, `{1, 2, 3, 4, 5}` 에 제곱 함수를 적용해 출력해 보세요. 결과 `1 4 9 16 25`", hint="`for (int i = 0; i < n; i++) a[i] = f(a[i]);` 그리고 `int square(int x) { return x * x; }`", ans=r"""
#include <stdio.h>

int square(int x) { return x * x; }

void map(int *a, int n, int (*f)(int)) {
    for (int i = 0; i < n; i++) a[i] = f(a[i]);
}

int main(void) {
    int a[] = {1, 2, 3, 4, 5};
    map(a, 5, square);
    for (int i = 0; i < 5; i++) printf("%d ", a[i]);
    printf("\n");
    return 0;
}
""", expect="1 4 9 16 25"),
)
more("c", 9,
ls("해시 테이블 직접 만들기", r"""
**해시 테이블**은 키(예: 단어)를 **해시 함수**로 숫자로 바꿔 그 칸에 저장해요. 찾기·넣기가 평균 `O(1)`!

- 해시 함수: 글자들로 큰 수를 만들고 `% 칸수`
- 두 키가 같은 칸에 오면(**충돌**) 그 칸에 연결 리스트로 이어 붙이기 (**체이닝**)
- 파이썬의 `dict`, 자바스크립트의 `Map` 이 이렇게 동작해요
""", r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SIZE 101
typedef struct Entry { char key[32]; int count; struct Entry *next; } Entry;
Entry *table[SIZE];

unsigned hash(const char *s) {
    unsigned h = 5381;
    while (*s) h = h * 33 + (unsigned char)*s++;
    return h % SIZE;
}

void add(const char *key) {
    unsigned h = hash(key);
    for (Entry *e = table[h]; e; e = e->next)
        if (strcmp(e->key, key) == 0) { e->count++; return; }
    Entry *e = malloc(sizeof(Entry));
    strcpy(e->key, key); e->count = 1;
    e->next = table[h]; table[h] = e;
}

int get(const char *key) {
    for (Entry *e = table[hash(key)]; e; e = e->next)
        if (strcmp(e->key, key) == 0) return e->count;
    return 0;
}

int main(void) {
    const char *words[] = {"cat", "dog", "cat", "bird", "dog", "cat"};
    for (int i = 0; i < 6; i++) add(words[i]);
    printf("cat %d, dog %d, fish %d\n", get("cat"), get("dog"), get("fish"));
    return 0;
}
""", task="입력값의 단어들(띄어쓰기로 구분)을 해시 테이블로 세어, **가장 많이 나온 단어와 횟수**를 출력해 보세요. (입력값 `apple banana apple cherry banana apple` → `apple 3`)", hint="`char w[32]; while (scanf(\"%31s\", w) == 1) add(w);` 그다음 `table` 의 모든 칸과 리스트를 돌며 최댓값 찾기", ans=r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SIZE 101
typedef struct Entry { char key[32]; int count; struct Entry *next; } Entry;
Entry *table[SIZE];

unsigned hash(const char *s) {
    unsigned h = 5381;
    while (*s) h = h * 33 + (unsigned char)*s++;
    return h % SIZE;
}

void add(const char *key) {
    unsigned h = hash(key);
    for (Entry *e = table[h]; e; e = e->next)
        if (strcmp(e->key, key) == 0) { e->count++; return; }
    Entry *e = malloc(sizeof(Entry));
    strcpy(e->key, key); e->count = 1;
    e->next = table[h]; table[h] = e;
}

int main(void) {
    char w[32];
    while (scanf("%31s", w) == 1) add(w);
    Entry *best = NULL;
    for (int i = 0; i < SIZE; i++)
        for (Entry *e = table[i]; e; e = e->next)
            if (!best || e->count > best->count) best = e;
    if (best) printf("%s %d\n", best->key, best->count);
    return 0;
}
""", stdin="", astdin="apple banana apple cherry banana apple", expect="apple 3"),
ls("힙 (우선순위 큐)", r"""
**힙**은 가장 작은(또는 큰) 값을 `O(log n)` 에 넣고 꺼내는 **완전 이진 트리**예요. 배열 하나로 만들어요.

- 노드 `i` 의 부모 `(i - 1) / 2`, 자식 `2i + 1`, `2i + 2`
- **넣기**: 맨 끝에 넣고 부모보다 작으면 위로 바꾸기 (올리기)
- **꺼내기**: 맨 위를 꺼내고, 맨 끝을 맨 위로 옮긴 뒤 자식 중 작은 쪽과 바꾸며 내리기

다익스트라, 작업 스케줄링, 힙 정렬에 써요.
""", r"""
#include <stdio.h>

int heap[1000], sz = 0;

void swap(int *a, int *b) { int t = *a; *a = *b; *b = t; }

void push(int x) {
    int i = sz++;
    heap[i] = x;
    while (i > 0 && heap[(i - 1) / 2] > heap[i]) {
        swap(&heap[(i - 1) / 2], &heap[i]);
        i = (i - 1) / 2;
    }
}

int pop(void) {
    int top = heap[0];
    heap[0] = heap[--sz];
    int i = 0;
    while (1) {
        int l = 2 * i + 1, r = l + 1, m = i;
        if (l < sz && heap[l] < heap[m]) m = l;
        if (r < sz && heap[r] < heap[m]) m = r;
        if (m == i) break;
        swap(&heap[i], &heap[m]);
        i = m;
    }
    return top;
}

int main(void) {
    int a[] = {5, 3, 17, 10, 84, 19, 6, 22, 9};
    for (int i = 0; i < 9; i++) push(a[i]);
    while (sz) printf("%d ", pop());
    printf("\n");
    return 0;
}
""", task="부등호만 바꿔서 **최대 힙**으로 만들고, 입력받은 수들을 **큰 것부터** 출력해 보세요. (입력값 `8` / `5 3 17 10 84 19 6 22` → `84 22 19 17 10 6 5 3`)", hint="`push` 와 `pop` 의 `>` `<` 비교를 반대로 바꾸면 돼요.", ans=r"""
#include <stdio.h>

int heap[1000], sz = 0;

void swap(int *a, int *b) { int t = *a; *a = *b; *b = t; }

void push(int x) {
    int i = sz++;
    heap[i] = x;
    while (i > 0 && heap[(i - 1) / 2] < heap[i]) {
        swap(&heap[(i - 1) / 2], &heap[i]);
        i = (i - 1) / 2;
    }
}

int pop(void) {
    int top = heap[0];
    heap[0] = heap[--sz];
    int i = 0;
    while (1) {
        int l = 2 * i + 1, r = l + 1, m = i;
        if (l < sz && heap[l] > heap[m]) m = l;
        if (r < sz && heap[r] > heap[m]) m = r;
        if (m == i) break;
        swap(&heap[i], &heap[m]);
        i = m;
    }
    return top;
}

int main(void) {
    int n, x;
    scanf("%d", &n);
    for (int i = 0; i < n; i++) { scanf("%d", &x); push(x); }
    while (sz) printf("%d ", pop());
    printf("\n");
    return 0;
}
""", astdin="8\n5 3 17 10 84 19 6 22", expect="84 22 19 17 10 6 5 3"),
)
more("c", 10,
ls("다익스트라 최단 경로", r"""
간선마다 비용이 있는 그래프에서 **시작점 → 모든 정점**의 최단 거리를 구해요.

정점이 적을 때(수백 개)는 힙 없이 `O(V²)` 로도 충분해요.

1. 아직 확정 안 된 정점 중 **거리가 가장 짧은 정점** u 를 고르고 확정
2. u 와 이어진 정점 v 에 대해 `dist[u] + w < dist[v]` 면 줄이기
3. V 번 반복

정점이 많으면 앞에서 만든 **힙**을 써서 `O(E log V)` 로 바꿔요.
""", r"""
#include <stdio.h>

#define INF 1000000000
int w[6][6], dist[6], done[6];

int main(void) {
    int V = 5;
    for (int i = 1; i <= V; i++) for (int j = 1; j <= V; j++) w[i][j] = INF;
    w[1][2] = 4; w[1][3] = 1; w[3][2] = 2; w[2][4] = 1; w[3][4] = 5; w[4][5] = 3;
    for (int i = 1; i <= V; i++) dist[i] = INF;
    dist[1] = 0;
    for (int k = 0; k < V; k++) {
        int u = -1;
        for (int i = 1; i <= V; i++)
            if (!done[i] && (u == -1 || dist[i] < dist[u])) u = i;
        if (dist[u] == INF) break;
        done[u] = 1;
        for (int v = 1; v <= V; v++)
            if (w[u][v] < INF && dist[u] + w[u][v] < dist[v]) dist[v] = dist[u] + w[u][v];
    }
    for (int i = 1; i <= V; i++) printf("1 → %d : %d\n", i, dist[i]);
    return 0;
}
""", task="""입력 첫 줄 `V E`, 다음 E 줄 `u v w` (u → v 비용 w). 1번에서 각 정점까지 최단 거리를 한 줄에 띄어 출력하고, 갈 수 없으면 `INF`. 입력값:
`5 6` / `1 2 2` / `1 3 3` / `2 3 4` / `2 4 5` / `3 4 6` / `5 1 1` → `0 2 3 7 INF`""", hint="같은 u v 가 여러 번 나오면 작은 값만 `if (c < w[u][v]) w[u][v] = c;` 출력은 `dist[i] == INF ? printf(\"INF \") : printf(\"%d \", dist[i])`", ans=r"""
#include <stdio.h>

#define INF 1000000000
int w[101][101], dist[101], done[101];

int main(void) {
    int V, E;
    scanf("%d %d", &V, &E);
    for (int i = 1; i <= V; i++) for (int j = 1; j <= V; j++) w[i][j] = INF;
    for (int i = 0; i < E; i++) {
        int u, v, c;
        scanf("%d %d %d", &u, &v, &c);
        if (c < w[u][v]) w[u][v] = c;
    }
    for (int i = 1; i <= V; i++) dist[i] = INF;
    dist[1] = 0;
    for (int k = 0; k < V; k++) {
        int u = -1;
        for (int i = 1; i <= V; i++)
            if (!done[i] && (u == -1 || dist[i] < dist[u])) u = i;
        if (dist[u] == INF) break;
        done[u] = 1;
        for (int v = 1; v <= V; v++)
            if (w[u][v] < INF && dist[u] + w[u][v] < dist[v]) dist[v] = dist[u] + w[u][v];
    }
    for (int i = 1; i <= V; i++) {
        if (dist[i] == INF) printf("INF");
        else printf("%d", dist[i]);
        printf(i < V ? " " : "\n");
    }
    return 0;
}
""", astdin="5 6\n1 2 2\n1 3 3\n2 3 4\n2 4 5\n3 4 6\n5 1 1", expect="0 2 3 7 INF"),
ls("행렬 거듭제곱 · 빠른 거듭제곱", r"""
피보나치 수 F(n) 을 n = 10¹⁸ 처럼 엄청 큰 n 에 대해 구하려면? 반복문으로는 우주가 끝나도 못 해요.

```
| F(n+1)  F(n)  |   | 1 1 |ⁿ
| F(n)    F(n-1)| = | 1 0 |
```

행렬을 **제곱하며 거듭제곱**하면 곱셈 `log n` 번 (60번쯤) 이면 끝나요. 수가 커지니 `% 1000000007` 로 나머지만 남겨요.

- `(a * b) % m = ((a % m) * (b % m)) % m`
- 지수 `n` 을 2진수로 보고 1 인 비트에서만 결과에 곱하기
""", r"""
#include <stdio.h>

typedef long long ll;
const ll MOD = 1000000007;

void mul(ll a[2][2], ll b[2][2]) {
    ll c[2][2] = {{0, 0}, {0, 0}};
    for (int i = 0; i < 2; i++)
        for (int j = 0; j < 2; j++)
            for (int k = 0; k < 2; k++)
                c[i][j] = (c[i][j] + a[i][k] * b[k][j]) % MOD;
    for (int i = 0; i < 2; i++) for (int j = 0; j < 2; j++) a[i][j] = c[i][j];
}

ll fib(ll n) {
    ll r[2][2] = {{1, 0}, {0, 1}}, m[2][2] = {{1, 1}, {1, 0}};
    while (n > 0) {
        if (n & 1) mul(r, m);
        mul(m, m);
        n >>= 1;
    }
    return r[0][1];
}

int main(void) {
    printf("F(10) = %lld\n", fib(10));
    printf("F(10^18) mod 1e9+7 = %lld\n", fib(1000000000000000000LL));
    return 0;
}
""", task="같은 방법(지수를 2진수로)으로 **2¹⁰⁰⁰⁰⁰⁰⁰⁰⁰ mod 1000000007** 을 구하는 `ll power(ll a, ll n)` 을 만들어 출력해 보세요. 결과 `140625001`", hint="`ll r = 1; a %= MOD; while (n) { if (n & 1) r = r * a % MOD; a = a * a % MOD; n >>= 1; }`", ans=r"""
#include <stdio.h>

typedef long long ll;
const ll MOD = 1000000007;

ll power(ll a, ll n) {
    ll r = 1;
    a %= MOD;
    while (n > 0) {
        if (n & 1) r = r * a % MOD;
        a = a * a % MOD;
        n >>= 1;
    }
    return r;
}

int main(void) {
    printf("%lld\n", power(2, 1000000000));
    return 0;
}
""", expect="140625001"),
)

# ---------------- 🟨 JS 중급 ~ 전설 ----------------
more("js", 3,
ls("map · filter · reduce", r"""
배열을 반복문 없이 다루는 3대 메서드예요. 원래 배열은 바꾸지 않고 **새 배열(값)** 을 돌려줘요.

- `arr.map(x => 식)` : 모든 원소를 바꾼 새 배열
- `arr.filter(x => 조건)` : 조건이 참인 것만
- `arr.reduce((누적, x) => 새누적, 처음값)` : 하나의 값으로 모으기
- 이어 쓰기(체이닝)도 돼요: `arr.filter(...).map(...)`
""", r"""
const scores = [72, 95, 88, 60, 100];
console.log(scores.map(s => s + 5));
console.log(scores.filter(s => s >= 80));
const total = scores.reduce((sum, s) => sum + s, 0);
console.log("합계", total, "평균", total / scores.length);
console.log(scores.some(s => s === 100), scores.every(s => s >= 60));
""", task="`[\"hi\", \"code\", \"is\", \"great\", \"fun\"]` 에서 **길이 4 이상**인 단어만 골라 **대문자**로 바꾸고 `-` 로 이어 출력해 보세요. 결과 `CODE-GREAT`", hint="`.filter(w => w.length >= 4).map(w => w.toUpperCase()).join(\"-\")`", ans=r"""
const words = ["hi", "code", "is", "great", "fun"];
console.log(words.filter(w => w.length >= 4).map(w => w.toUpperCase()).join("-"));
""", expect="CODE-GREAT"),
ls("구조 분해 · 스프레드", r"""
- **구조 분해**: `const [a, b] = [1, 2];` / `const { name, age } = user;`
- 기본값: `const { lv = 1 } = obj;`
- **스프레드** `...` : 배열·객체를 펼쳐요. `[...a, ...b]` 합치기, `{ ...obj, age: 18 }` 복사하며 바꾸기
- **나머지** `...rest` : 남은 것을 모으기
- 값 바꾸기: `[x, y] = [y, x];`
""", r"""
const user = { name: "지우", age: 17, city: "부산" };
const { name, ...rest } = user;
console.log(name, rest);

const [first, , third = "없음"] = ["A", "B"];
console.log(first, third);

let x = 1, y = 2;
[x, y] = [y, x];
console.log(x, y);

const older = { ...user, age: user.age + 1 };
console.log(older.age, user.age);
console.log(Math.max(...[3, 9, 4]));
""", task="두 배열 `[3, 1, 2]` 와 `[2, 5, 3]` 을 스프레드로 합치고 **중복을 없앤 뒤** 오름차순 정렬해 `,` 로 이어 출력해 보세요. 결과 `1,2,3,5`", hint="`[...new Set([...a, ...b])]` 로 중복 제거, `.sort((p, q) => p - q)`", ans=r"""
const a = [3, 1, 2], b = [2, 5, 3];
console.log([...new Set([...a, ...b])].sort((p, q) => p - q).join(","));
""", expect="1,2,3,5"),
)
more("js", 4,
ls("클래스와 상속", r"""
`class` 로 객체의 설계도를 만들어요.

- `constructor(...)` : 만들 때 실행
- `this.이름` : 그 객체의 속성
- `#비밀` : 클래스 밖에서 못 보는 **private** 필드
- `get 이름()` : 속성처럼 읽는 함수
- `class 자식 extends 부모` + `super(...)` 로 상속
""", r"""
class Account {
  #balance = 0;
  constructor(owner) { this.owner = owner; }
  deposit(n) { this.#balance += n; return this; }
  withdraw(n) {
    if (n > this.#balance) throw new Error("잔액 부족");
    this.#balance -= n;
    return this;
  }
  get balance() { return this.#balance; }
}

class Savings extends Account {
  addInterest(rate) { return this.deposit(Math.floor(this.balance * rate)); }
}

const acc = new Savings("서윤");
acc.deposit(10000).withdraw(3000).addInterest(0.1);
console.log(acc.owner, acc.balance);
try { acc.withdraw(999999); } catch (e) { console.log("오류:", e.message); }
""", task="`name` 을 받는 `Animal` 클래스(메서드 `speak()` 는 `\"...\"` 반환)를 만들고, 이를 상속한 `Dog` 의 `speak()` 가 `이름: 멍멍` 을 돌려주게 해 보세요. `new Dog(\"바둑이\").speak()` 출력 → `바둑이: 멍멍`", hint="`class Dog extends Animal { speak() { return `${this.name}: 멍멍`; } }`", ans=r"""
class Animal {
  constructor(name) { this.name = name; }
  speak() { return "..."; }
}
class Dog extends Animal {
  speak() { return `${this.name}: 멍멍`; }
}
console.log(new Dog("바둑이").speak());
""", expect="바둑이: 멍멍"),
ls("클로저", r"""
**클로저**: 함수가 만들어질 때의 **바깥 변수를 기억**하는 것. 함수가 끝난 뒤에도 그 변수는 살아 있어요.

- 바깥에서 직접 못 건드리는 **비밀 변수**를 만들 수 있어요
- 설정값을 기억하는 함수 공장(`makeAdder(10)`)을 만들 수 있어요
- `let` 은 반복마다 새 변수라서 클로저와 잘 맞아요
""", r"""
function makeCounter() {
  let count = 0;               // 바깥에서 못 건드려요
  return {
    inc: () => ++count,
    reset: () => { count = 0; },
  };
}
const c1 = makeCounter(), c2 = makeCounter();
c1.inc(); c1.inc(); c2.inc();
console.log(c1.inc(), c2.inc());

const fns = [];
for (let i = 0; i < 3; i++) fns.push(() => i * 10);
console.log(fns.map(f => f()));
""", task="숫자 n 을 기억해서 받은 수에 n 을 더해 주는 함수를 만드는 `makeAdder(n)` 을 만들고, `makeAdder(10)(5)` 를 출력해 보세요. 결과 `15`", hint="`const makeAdder = n => x => x + n;`", ans=r"""
const makeAdder = n => x => x + n;
console.log(makeAdder(10)(5));
""", expect="15"),
)
more("js", 5,
ls("Map 과 Set", r"""
- **Set**: 중복 없는 값 모음. `add`, `has`, `delete`, `size`
- **Map**: 키 → 값. 객체와 달리 **아무 값이나 키**가 될 수 있고 넣은 순서를 지켜요. `set`, `get`, `has`, `size`
- `for (const [k, v] of map)` 로 돌기
- `[...map]`, `[...set]` 으로 배열로 바꾸기
""", r"""
const words = ["apple", "avocado", "banana", "blueberry", "cherry", "apple"];
const uniq = new Set(words);
console.log(uniq.size, uniq.has("cherry"));

const byLetter = new Map();
for (const w of uniq) {
  const k = w[0];
  if (!byLetter.has(k)) byLetter.set(k, []);
  byLetter.get(k).push(w);
}
for (const [k, list] of byLetter) console.log(k, list.join(", "));
""", task="`[\"사과\", \"배\", \"사과\", \"귤\", \"배\", \"사과\"]` 에서 **가장 많이 나온 과일과 개수**를 Map 으로 세어 `사과 3` 처럼 출력해 보세요.", hint="`cnt.set(f, (cnt.get(f) || 0) + 1)` 로 세고, `[...cnt].sort((a, b) => b[1] - a[1])[0]`", ans=r"""
const fruits = ["사과", "배", "사과", "귤", "배", "사과"];
const cnt = new Map();
for (const f of fruits) cnt.set(f, (cnt.get(f) || 0) + 1);
const [top, n] = [...cnt].sort((a, b) => b[1] - a[1])[0];
console.log(top, n);
""", expect="사과 3"),
ls("JSON 다루기", r"""
**JSON** 은 데이터를 글자로 주고받는 표준 형식이에요. 서버 API, 설정 파일, 이 앱의 저장 데이터도 JSON 이에요!

- `JSON.stringify(값)` : 객체 → 글자
- `JSON.stringify(값, null, 2)` : 보기 좋게 들여쓰기
- `JSON.parse(글자)` : 글자 → 객체 (형식이 틀리면 오류 → `try`)
- JSON 의 키는 **반드시 큰따옴표** `"..."`
""", r"""
const data = { name: "알람앱", ver: 2, tags: ["계획", "알림"], dark: true };
const text = JSON.stringify(data);
console.log(text);
const back = JSON.parse(text);
console.log(back.tags[1], typeof back.ver);
console.log(JSON.stringify({ a: 1, b: [1, 2] }, null, 2));
try { JSON.parse("{name: 1}"); } catch (e) { console.log("형식 오류!"); }
""", task="JSON 글자 `'[{\"name\":\"가온\",\"score\":80},{\"name\":\"나래\",\"score\":95},{\"name\":\"다온\",\"score\":71}]'` 를 parse 해서 **평균 점수**를 출력해 보세요. 결과 `82`", hint="`JSON.parse(text).reduce((s, x) => s + x.score, 0) / 3`", ans=r"""
const text = '[{"name":"가온","score":80},{"name":"나래","score":95},{"name":"다온","score":71}]';
const list = JSON.parse(text);
console.log(list.reduce((s, x) => s + x.score, 0) / list.length);
""", expect="82"),
)
more("js", 6,
ls("Promise 와 async · await", r"""
시간이 걸리는 일(서버 요청, 타이머)은 **기다리는 동안 다른 일을 하도록** 비동기로 처리해요.

- `Promise` : "나중에 값을 줄게" 라는 약속. 성공(`resolve`) 또는 실패(`reject`)
- `async function` 안에서 `await 약속` 을 쓰면 끝날 때까지 기다렸다가 값을 받아요
- `Promise.all([...])` : 여러 개를 **동시에** 기다리기
- 실패는 `try { await ... } catch (e) { }` 로 잡아요
""", r"""
const wait = (ms, v) => new Promise(ok => setTimeout(() => ok(v), ms));

async function main() {
  console.log("시작");
  const a = await wait(300, "첫 번째 (0.3초)");
  console.log(a);
  const t = Date.now();
  const [b, c] = await Promise.all([wait(300, "둘"), wait(300, "셋")]);
  console.log(b, c, "— 같이 기다려서", Math.round((Date.now() - t) / 100) / 10, "초쯤");
  try {
    await Promise.reject(new Error("실패!"));
  } catch (e) {
    console.log("잡았다:", e.message);
  }
}
main();
""", task="`wait(ms, v)` 를 써서 `[1, 2, 3, 4]` 의 각 수를 **0.1초씩 기다렸다가** 하나씩 더하는 `async` 함수를 만들고, 다 더한 뒤 `합 10` 을 출력해 보세요.", hint="`for (const n of nums) total += await wait(100, n);`", ans=r"""
const wait = (ms, v) => new Promise(ok => setTimeout(() => ok(v), ms));
async function sumLater(nums) {
  let total = 0;
  for (const n of nums) total += await wait(100, n);
  return total;
}
sumLater([1, 2, 3, 4]).then(s => console.log("합", s));
""", expect="합 10"),
ls("메모이제이션", r"""
**메모이제이션**: 함수가 계산한 결과를 **기억해 두고**, 같은 입력이 오면 다시 계산하지 않고 바로 돌려줘요.

그냥 재귀 피보나치 `fib(50)` 은 같은 계산을 수십억 번 반복해서 끝나지 않지만, 기억해 두면 50번이면 끝나요.

- `Map` 이나 객체에 `입력 → 결과` 를 저장
- 어떤 함수든 감싸서 기억하게 만드는 `memo(fn)` 도 만들 수 있어요 (클로저 활용!)
""", r"""
const memo = fn => {
  const cache = new Map();
  return function self(n) {
    if (cache.has(n)) return cache.get(n);
    const r = fn(self, n);
    cache.set(n, r);
    return r;
  };
};

let calls = 0;
const fib = memo((f, n) => { calls++; return n < 2 ? n : f(n - 1) + f(n - 2); });
console.log(fib(70), "계산 횟수:", calls);
""", task="m × n 격자의 왼쪽 위에서 오른쪽 아래까지 **오른쪽·아래로만** 가는 경로 수 `paths(m, n)` 을 메모이제이션으로 만들고 `paths(16, 16)` 을 출력해 보세요. (`paths(1, n) = paths(m, 1) = 1`) 결과 `155117520`", hint="키는 `m + \",\" + n` 처럼 글자로 (예: `\"3,4\"`). `paths(m, n) = paths(m - 1, n) + paths(m, n - 1)`", ans=r"""
const cache = new Map();
function paths(m, n) {
  if (m === 1 || n === 1) return 1;
  const k = `${m},${n}`;
  if (!cache.has(k)) cache.set(k, paths(m - 1, n) + paths(m, n - 1));
  return cache.get(k);
}
console.log(paths(16, 16));
""", expect="155117520"),
)
more("js", 7,
ls("이터레이터와 제너레이터", r"""
`for...of` 가 돌 수 있는 것을 **이터러블**이라고 해요. 배열, 문자열, Map, Set 이 그래요.

- `function*` + `yield` = **제너레이터**: 값을 하나씩, 필요할 때만 만들어요
- 객체에 `[Symbol.iterator]` 메서드를 만들면 내 객체도 `for...of` 와 `...` 가 돼요
- 끝없는 수열도 앞에서 필요한 만큼만 꺼낼 수 있어요
""", r"""
function* range(start, end, step = 1) {
  for (let i = start; i < end; i += step) yield i;
}
console.log([...range(0, 10, 3)]);

class Countdown {
  constructor(n) { this.n = n; }
  *[Symbol.iterator]() { for (let i = this.n; i > 0; i--) yield i; }
}
for (const x of new Countdown(3)) console.log(x);

function* naturals() { let n = 1; while (true) yield n++; }
const it = naturals();
console.log(it.next().value, it.next().value, it.next().value);
""", task="끝없이 피보나치 수(1, 1, 2, 3, …)를 `yield` 하는 `function* fib()` 를 만들고, **처음 10개**를 띄어쓰기로 이어 출력해 보세요. 결과 `1 1 2 3 5 8 13 21 34 55`", hint="`let [a, b] = [1, 1]; while (true) { yield a; [a, b] = [b, a + b]; }` 꺼낼 땐 `it.next().value` 를 10번", ans=r"""
function* fib() {
  let [a, b] = [1, 1];
  while (true) { yield a; [a, b] = [b, a + b]; }
}
const out = [], it = fib();
for (let i = 0; i < 10; i++) out.push(it.next().value);
console.log(out.join(" "));
""", expect="1 1 2 3 5 8 13 21 34 55"),
ls("이벤트 루프 (실행 순서)", r"""
자바스크립트는 **한 번에 한 가지 일**만 해요. 그래서 기다리는 일은 줄을 세워 두는데, 줄이 두 개예요.

1. 지금 실행 중인 코드(동기 코드)를 **끝까지**
2. **마이크로태스크** 줄: `Promise.then`, `await` 다음 부분 → 전부 비울 때까지
3. **매크로태스크** 줄: `setTimeout` 같은 타이머 → 하나 실행하고 다시 2번으로

그래서 `setTimeout(f, 0)` 은 "0초 뒤" 가 아니라 "**지금 일과 약속들이 다 끝난 뒤**" 예요.
""", r"""
console.log("1. 동기");
setTimeout(() => console.log("5. setTimeout"), 0);
Promise.resolve().then(() => console.log("3. then"));
(async () => {
  console.log("2. async 함수 안 (동기 부분)");
  await null;
  console.log("4. await 다음");
})();
console.log("2-2. 동기 끝");
""", task="아래 빈칸 ①②③ 에 `setTimeout(() => out.push(?), 0)` / `Promise.resolve().then(() => out.push(?))` / `out.push(?)` 중 알맞은 걸 넣어서, 마지막에 `1 2 3 4` 가 출력되게 해 보세요.\n\n`const out = [];` → ① 4 넣기 → ② 2 넣기 → `out.push(1);` → ③ 3 넣기 → `setTimeout(() => console.log(out.join(\" \")), 10);`", hint="4는 가장 늦게(setTimeout), 2와 3은 then 이에요. 먼저 등록한 then 이 먼저 실행돼요.", ans=r"""
const out = [];
setTimeout(() => out.push(4), 0);
Promise.resolve().then(() => out.push(2));
out.push(1);
Promise.resolve().then(() => out.push(3));
setTimeout(() => console.log(out.join(" ")), 10);
""", expect="1 2 3 4"),
)
more("js", 8,
ls("커링과 함수 합성", r"""
**함수형 프로그래밍**에서는 작은 함수를 레고처럼 조립해요.

- **고차 함수**: 함수를 받거나 돌려주는 함수
- **합성** `compose(f, g)(x) = f(g(x))`, **파이프** `pipe(f, g)(x) = g(f(x))` (왼쪽→오른쪽 순서)
- **커링**: `f(a, b, c)` 를 `f(a)(b)(c)` 로. 인자를 조금씩 채워 새 함수를 만들 수 있어요
""", r"""
const pipe = (...fns) => x => fns.reduce((v, f) => f(v), x);
const curry = fn => function c(...args) {
  return args.length >= fn.length ? fn(...args) : (...more) => c(...args, ...more);
};

const add = curry((a, b, c) => a + b + c);
console.log(add(1)(2)(3), add(1, 2)(3), add(1)(2, 3));

const slug = pipe(
  s => s.trim(),
  s => s.toLowerCase(),
  s => s.replace(/\s+/g, "-"),
);
console.log(slug("  Hello Coding World  "));
""", task="위의 `pipe` 를 써서 `x => x + 1`, `x => x * 2`, `x => x - 3` 을 차례로 적용하는 함수를 만들고 `5` 를 넣은 결과를 출력해 보세요. 결과 `9`", hint="`pipe(x => x + 1, x => x * 2, x => x - 3)(5)` → (5+1)×2−3", ans=r"""
const pipe = (...fns) => x => fns.reduce((v, f) => f(v), x);
console.log(pipe(x => x + 1, x => x * 2, x => x - 3)(5));
""", expect="9"),
ls("정규 표현식", r"""
**정규 표현식**은 글자의 **패턴**을 찾는 작은 언어예요. `/패턴/플래그`

| 기호 | 뜻 |
|---|---|
| `\d` | 숫자 한 개 |
| `\w` | 글자·숫자·_ |
| `+` `*` `?` | 1번 이상 · 0번 이상 · 있거나 없거나 |
| `{3}` | 정확히 3번 |
| `[가-힣]` | 한글 한 글자 |
| `( )` | 묶기 · 꺼내기 |

플래그 `g` 는 모두 찾기. `str.match`, `str.replace`, `regex.test` 와 함께 써요.
""", r"""
const text = "연락처: 010-1234-5678, 이메일 coder@alam.kr / 02-987-6543";
console.log(text.match(/\d{2,3}-\d{3,4}-\d{4}/g));
console.log(/^[\w.]+@[\w.]+\.\w+$/.test("coder@alam.kr"));
console.log(text.replace(/(\d{3})-(\d{4})-(\d{4})/, "$1-****-$3"));
const m = "2026-11-09".match(/(\d+)-(\d+)-(\d+)/);
console.log(`${m[1]}년 ${+m[2]}월 ${+m[3]}일`);
""", task="문장 `\"사과 3개, 배 12개, 귤 25개\"` 에서 **숫자만** 정규 표현식으로 모두 찾아 합을 출력해 보세요. 결과 `40`", hint="`s.match(/\\d+/g)` 는 `[\"3\", \"12\", \"25\"]` → `.map(Number).reduce(...)`", ans=r"""
const s = "사과 3개, 배 12개, 귤 25개";
console.log(s.match(/\d+/g).map(Number).reduce((a, b) => a + b, 0));
""", expect="40"),
)
more("js", 9,
ls("이벤트 이미터 (옵저버 패턴)", r"""
**옵저버 패턴**: "이 일이 생기면 알려 줘" 하고 함수를 등록해 두면, 일이 생길 때 등록한 함수들을 모두 불러 줘요. 버튼 클릭(`addEventListener`), 채팅 알림, Node.js 가 모두 이 방식이에요.

- `on(이름, 함수)` : 등록
- `off(이름, 함수)` : 해제
- `emit(이름, ...값)` : 그 이름에 등록된 함수를 모두 실행
""", r"""
class Emitter {
  #map = new Map();
  on(ev, fn) {
    if (!this.#map.has(ev)) this.#map.set(ev, new Set());
    this.#map.get(ev).add(fn);
    return () => this.off(ev, fn);       // 해제 함수를 돌려줘요
  }
  off(ev, fn) { this.#map.get(ev)?.delete(fn); }
  emit(ev, ...args) { for (const fn of [...(this.#map.get(ev) || [])]) fn(...args); }
}

const chat = new Emitter();
const stop = chat.on("msg", (who, text) => console.log(`[알림] ${who}: ${text}`));
chat.on("msg", who => console.log(`${who} 님이 메시지를 보냈어요`));
chat.emit("msg", "민지", "안녕!");
stop();
chat.emit("msg", "준서", "다들 뭐 해?");
""", task="위 `Emitter` 에 **한 번만 실행되고 자동으로 해제되는** `once(ev, fn)` 을 추가해 보세요. `once` 로 등록한 함수가 횟수를 세게 하고, `emit` 을 3번 한 뒤 `호출 1번` 을 출력", hint="`once(ev, fn) { const w = (...a) => { this.off(ev, w); fn(...a); }; this.on(ev, w); }`", ans=r"""
class Emitter {
  #map = new Map();
  on(ev, fn) {
    if (!this.#map.has(ev)) this.#map.set(ev, new Set());
    this.#map.get(ev).add(fn);
    return () => this.off(ev, fn);
  }
  off(ev, fn) { this.#map.get(ev)?.delete(fn); }
  emit(ev, ...args) { for (const fn of [...(this.#map.get(ev) || [])]) fn(...args); }
  once(ev, fn) {
    const w = (...a) => { this.off(ev, w); fn(...a); };
    this.on(ev, w);
  }
}
const e = new Emitter();
let n = 0;
e.once("hi", () => n++);
e.emit("hi"); e.emit("hi"); e.emit("hi");
console.log(`호출 ${n}번`);
""", expect="호출 1번"),
ls("LRU 캐시 만들기", r"""
**LRU(Least Recently Used) 캐시**: 정해진 개수만 기억하고, 꽉 차면 **가장 오래 안 쓴 것**부터 버려요. 브라우저 캐시, 데이터베이스, CPU 가 이렇게 해요.

`Map` 은 **넣은 순서**를 기억하니까 이걸로 쉽게 만들 수 있어요.

- `get` 할 때: 지우고 다시 넣어서 **맨 뒤(최근)** 로 보내기
- `put` 할 때 꽉 찼으면: `map.keys().next().value` (**맨 앞 = 가장 오래된 것**) 지우기
- 둘 다 `O(1)`
""", r"""
class LRU {
  constructor(cap) { this.cap = cap; this.m = new Map(); }
  get(k) {
    if (!this.m.has(k)) return -1;
    const v = this.m.get(k);
    this.m.delete(k); this.m.set(k, v);
    return v;
  }
  put(k, v) {
    this.m.delete(k);
    this.m.set(k, v);
    if (this.m.size > this.cap) this.m.delete(this.m.keys().next().value);
  }
}

const c = new LRU(3);
c.put("a", 1); c.put("b", 2); c.put("c", 3);
c.get("a");          // a 를 최근으로
c.put("d", 4);       // 가장 오래 안 쓴 b 가 빠져요
console.log([...c.m.keys()]);
""", task="용량 2 인 `LRU` 에 `put(1, 1)`, `put(2, 2)`, `get(1)`, `put(3, 3)` 을 한 뒤 `get(2)`, `get(1)`, `get(3)` 을 띄어 출력해 보세요. 결과 `-1 1 3`", hint="`put(3, 3)` 때 가장 오래 안 쓴 건 2 예요 (1 은 방금 get 했으니까).", ans=r"""
class LRU {
  constructor(cap) { this.cap = cap; this.m = new Map(); }
  get(k) {
    if (!this.m.has(k)) return -1;
    const v = this.m.get(k);
    this.m.delete(k); this.m.set(k, v);
    return v;
  }
  put(k, v) {
    this.m.delete(k);
    this.m.set(k, v);
    if (this.m.size > this.cap) this.m.delete(this.m.keys().next().value);
  }
}
const c = new LRU(2);
c.put(1, 1); c.put(2, 2); c.get(1); c.put(3, 3);
console.log(c.get(2), c.get(1), c.get(3));
""", expect="-1 1 3"),
)
more("js", 10,
ls("수식 계산기 만들기 (파서)", r"""
`"2 + 3 * (4 - 1)"` 같은 글자를 계산하려면 **컴파일러의 앞부분**을 직접 만들어야 해요.

1. **토크나이저**: 글자를 `2`, `+`, `3`, `*`, `(` … 같은 **토큰**으로 자르기
2. **재귀 하강 파서**: 문법 규칙마다 함수 하나
   - `expr` = term (`+`|`-` term)*  — 덧셈·뺄셈
   - `term` = factor (`*`|`/` factor)*  — 곱셈·나눗셈이 먼저 묶여요
   - `factor` = 숫자 | `-`factor | `(` expr `)`

규칙이 아래로 갈수록 **우선순위가 높아요**. `eval` 없이 계산!
""", r"""
function calc(src) {
  const toks = src.match(/\d+(\.\d+)?|[-+*/()]/g) || [];
  let i = 0;
  const peek = () => toks[i], next = () => toks[i++];
  function expr() {
    let v = term();
    while (peek() === "+" || peek() === "-") v = next() === "+" ? v + term() : v - term();
    return v;
  }
  function term() {
    let v = factor();
    while (peek() === "*" || peek() === "/") v = next() === "*" ? v * factor() : v / factor();
    return v;
  }
  function factor() {
    const t = next();
    if (t === "-") return -factor();
    if (t === "(") { const v = expr(); if (next() !== ")") throw new Error("괄호 짝이 안 맞아요"); return v; }
    if (t === undefined || isNaN(t)) throw new Error("예상 못한 " + t);
    return Number(t);
  }
  const v = expr();
  if (i < toks.length) throw new Error("남은 토큰: " + toks.slice(i).join(""));
  return v;
}

for (const s of ["2 + 3 * (4 - 1)", "-(5 - 8) * 2", "10 / 4", "(1 + 2"]) {
  try { console.log(s, "=", calc(s)); } catch (e) { console.log(s, "→ 오류:", e.message); }
}
""", task="계산기에 **거듭제곱 `^`** 을 추가해 보세요. 곱셈보다 먼저 계산하고, **오른쪽부터** 묶여요(`2 ^ 3 ^ 2` = 2⁹). `calc(\"2 ^ 3 ^ 2\")` 와 `calc(\"2 * 3 ^ 2\")` 를 띄어 출력 → `512 18`", hint="`factor` 와 숫자 사이에 `power` 단계를 만들어요: `power = unary (^ power)?` — 자기 자신을 부르면 오른쪽 결합이 돼요. 토큰 정규식에 `^` 도 추가!", ans=r"""
function calc(src) {
  const toks = src.match(/\d+(\.\d+)?|[-+*/()^]/g) || [];
  let i = 0;
  const peek = () => toks[i], next = () => toks[i++];
  function expr() {
    let v = term();
    while (peek() === "+" || peek() === "-") v = next() === "+" ? v + term() : v - term();
    return v;
  }
  function term() {
    let v = power();
    while (peek() === "*" || peek() === "/") v = next() === "*" ? v * power() : v / power();
    return v;
  }
  function power() {
    const b = factor();
    if (peek() === "^") { next(); return b ** power(); }
    return b;
  }
  function factor() {
    const t = next();
    if (t === "-") return -factor();
    if (t === "(") { const v = expr(); next(); return v; }
    return Number(t);
  }
  return expr();
}
console.log(calc("2 ^ 3 ^ 2"), calc("2 * 3 ^ 2"));
""", expect="512 18"),
ls("위상 정렬 (순서 정하기)", r"""
"수학Ⅰ 을 들어야 수학Ⅱ 를 들을 수 있다" 처럼 **먼저 해야 하는 관계**가 있을 때, 모든 관계를 지키는 순서를 찾는 게 **위상 정렬**이에요. (빌드 도구, 패키지 설치 순서, 엑셀 수식 계산)

**칸 알고리즘**:
1. 각 일의 **진입 차수**(먼저 해야 하는 일의 수)를 세기
2. 진입 차수가 0 인 일을 큐에 넣기
3. 하나 꺼내 결과에 넣고, 그 뒤의 일들의 진입 차수를 1씩 줄이기 → 0 이 되면 큐에
4. 결과 개수가 전체보다 적으면 **순환**(서로가 서로를 기다림)이 있는 거예요
""", r"""
function topo(nodes, edges) {
  const indeg = new Map(nodes.map(n => [n, 0])), next = new Map(nodes.map(n => [n, []]));
  for (const [a, b] of edges) { next.get(a).push(b); indeg.set(b, indeg.get(b) + 1); }
  const q = nodes.filter(n => indeg.get(n) === 0), order = [];
  while (q.length) {
    const n = q.shift();
    order.push(n);
    for (const m of next.get(n)) {
      indeg.set(m, indeg.get(m) - 1);
      if (indeg.get(m) === 0) q.push(m);
    }
  }
  return order.length === nodes.length ? order : null;
}

const subjects = ["수학Ⅰ", "수학Ⅱ", "미적분", "확률과 통계", "인공지능 수학"];
const needs = [["수학Ⅰ", "수학Ⅱ"], ["수학Ⅱ", "미적분"], ["수학Ⅰ", "확률과 통계"],
               ["확률과 통계", "인공지능 수학"], ["미적분", "인공지능 수학"]];
console.log(topo(subjects, needs).join(" → "));
""", task="`A → B`, `B → C`, `C → A`, `C → D` 관계에서 위상 정렬을 해 보고, 순환이 있으면 `순환 있음`, 없으면 순서를 출력해 보세요. 결과 `순환 있음`", hint="위 `topo` 를 그대로 쓰고 결과가 `null` 이면 `\"순환 있음\"`", ans=r"""
function topo(nodes, edges) {
  const indeg = new Map(nodes.map(n => [n, 0])), next = new Map(nodes.map(n => [n, []]));
  for (const [a, b] of edges) { next.get(a).push(b); indeg.set(b, indeg.get(b) + 1); }
  const q = nodes.filter(n => indeg.get(n) === 0), order = [];
  while (q.length) {
    const n = q.shift();
    order.push(n);
    for (const m of next.get(n)) {
      indeg.set(m, indeg.get(m) - 1);
      if (indeg.get(m) === 0) q.push(m);
    }
  }
  return order.length === nodes.length ? order : null;
}
const r = topo(["A", "B", "C", "D"], [["A", "B"], ["B", "C"], ["C", "A"], ["C", "D"]]);
console.log(r ? r.join(" → ") : "순환 있음");
""", expect="순환 있음"),
)

# ---------------- 🌐 HTML 중급 ~ 전문가 ----------------
more("html", 3,
ls("시맨틱 태그", r"""
`<div>` 만 쓰지 말고 **뜻이 있는 태그**를 쓰면 검색 엔진·화면 낭독기(시각 장애인용)가 페이지 구조를 이해해요.

- `<header>` 머리말, `<nav>` 메뉴, `<main>` 본문 (한 번만)
- `<article>` 따로 떼어도 뜻이 통하는 글, `<section>` 주제별 묶음
- `<aside>` 곁들이는 내용, `<footer>` 꼬리말
- `<time datetime="2026-11-09">` 날짜, `<figure>` + `<figcaption>` 그림과 설명
""", r"""
<header>
  <h1>📒 나의 공부 블로그</h1>
  <nav><a href="#">홈</a> · <a href="#">코딩</a> · <a href="#">수학</a></nav>
</header>
<main>
  <article>
    <h2>재귀 함수 정복기</h2>
    <p><time datetime="2026-11-09">2026년 11월 9일</time></p>
    <p>오늘은 하노이의 탑을 재귀로 풀었다.</p>
  </article>
  <aside>💡 다음 목표: 동적 계획법</aside>
</main>
<footer>© 2026 나</footer>
""", task="`<article>` 를 하나 더 만들어 오늘 배운 다른 내용을 적고, `<figure>` 와 `<figcaption>` 으로 이모지 그림과 설명을 넣어 보세요."),
)
more("html", 4,
ls("폼 검증", r"""
자바스크립트 없이도 HTML 만으로 입력을 검사할 수 있어요.

- `required` 꼭 입력, `minlength="4"` 최소 글자 수
- `type="email"`, `type="number" min="1" max="100"`
- `pattern="[0-9]{3}-[0-9]{4}-[0-9]{4}"` 정규 표현식 패턴
- CSS `:invalid` / `:valid` 로 틀린 칸을 빨갛게
- 제출(`submit`)할 때 `event.preventDefault()` 로 페이지 이동을 막고 직접 처리
""", r"""
<style>
  input { display: block; margin: 6px 0 12px; padding: 8px; border: 2px solid #ccc; border-radius: 8px; }
  input:invalid:not(:placeholder-shown) { border-color: #ef4444; }
  input:valid:not(:placeholder-shown) { border-color: #10b981; }
</style>
<form id="f">
  아이디 (4글자 이상)<input name="id" required minlength="4" placeholder="coder">
  이메일<input name="mail" type="email" required placeholder="me@example.com">
  전화번호<input name="tel" pattern="010-[0-9]{4}-[0-9]{4}" placeholder="010-1234-5678">
  <button>가입하기</button>
</form>
<p id="msg"></p>
<script>
  document.getElementById("f").onsubmit = e => {
    e.preventDefault();
    const d = new FormData(e.target);
    document.getElementById("msg").textContent = `환영해요, ${d.get("id")} 님!`;
  };
</script>
""", task="나이 칸(`type=\"number\"`, 14 ~ 19 만 허용)을 추가하고, 환영 문구에 나이도 같이 보여 주세요."),
)
more("html", 5,
ls("canvas 에 그리기", r"""
`<canvas>` 는 자바스크립트로 그림을 그리는 도화지예요. 게임·차트·그림판을 만들 때 써요.

- `const ctx = canvas.getContext("2d");`
- `ctx.fillStyle = "색"; ctx.fillRect(x, y, 가로, 세로);` 채운 사각형
- `ctx.beginPath(); ctx.arc(x, y, 반지름, 0, Math.PI * 2); ctx.fill();` 원
- `ctx.moveTo` → `ctx.lineTo` → `ctx.stroke()` 선
- 좌표 (0, 0) 은 **왼쪽 위**, y 는 아래로 커져요
""", r"""
<canvas id="c" width="300" height="200" style="border:1px solid #ddd"></canvas>
<script>
  const ctx = document.getElementById("c").getContext("2d");
  ctx.fillStyle = "#bae6fd"; ctx.fillRect(0, 0, 300, 140);      // 하늘
  ctx.fillStyle = "#86efac"; ctx.fillRect(0, 140, 300, 60);     // 땅
  ctx.fillStyle = "#facc15";
  ctx.beginPath(); ctx.arc(250, 40, 22, 0, Math.PI * 2); ctx.fill();  // 해
  ctx.fillStyle = "#f87171"; ctx.fillRect(60, 90, 80, 50);      // 집
  ctx.fillStyle = "#7c2d12";
  ctx.beginPath(); ctx.moveTo(50, 90); ctx.lineTo(100, 50); ctx.lineTo(150, 90); ctx.fill();  // 지붕
  ctx.font = "16px sans-serif"; ctx.fillStyle = "#111";
  ctx.fillText("우리 집", 70, 175);
</script>
""", task="반복문으로 해 옆에 구름(흰 원 3개를 겹쳐서)을 그리고, 집 옆에 나무(갈색 사각형 + 초록 원)를 그려 보세요."),
)
more("html", 6,
ls("SVG 벡터 그래픽", r"""
**SVG** 는 도형을 **좌표와 수식**으로 그리는 그림이에요. 아무리 크게 키워도 깨지지 않아요. (이 앱 아이콘도 SVG!)

- `<svg viewBox="0 0 가로 세로">` 그림의 좌표계
- `<rect>` `<circle>` `<line>` `<polygon points="...">` `<path d="...">`
- `fill` 채우기 색, `stroke` 테두리 색, `stroke-width` 두께
- HTML 태그라서 CSS·자바스크립트로 꾸미고 움직일 수 있어요
""", r"""
<svg viewBox="0 0 220 160" width="320" style="background:#f8fafc;border-radius:12px">
  <polyline points="20,130 60,90 100,105 140,50 180,70 200,30"
            fill="none" stroke="#6366f1" stroke-width="4" stroke-linecap="round"/>
  <g fill="#6366f1">
    <circle cx="20" cy="130" r="5"/><circle cx="60" cy="90" r="5"/><circle cx="100" cy="105" r="5"/>
    <circle cx="140" cy="50" r="5"/><circle cx="180" cy="70" r="5"/><circle cx="200" cy="30" r="5"/>
  </g>
  <line x1="10" y1="145" x2="210" y2="145" stroke="#94a3b8"/>
  <text x="110" y="158" font-size="10" text-anchor="middle" fill="#64748b">내 코딩 공부 시간</text>
</svg>
<script>
  document.querySelectorAll("circle").forEach(c => c.onclick = () => alert(`높이 ${150 - c.getAttribute("cy")}`));
</script>
""", task="막대그래프로 바꿔 보세요: `<rect>` 6개로 요일별 공부 시간을 그리고, 막대 위에 `<text>` 로 숫자를 써 보세요."),
)
more("html", 7,
ls("canvas 애니메이션 (게임 루프)", r"""
게임은 1초에 60번 **지우기 → 움직이기 → 그리기**를 반복해요. 이걸 **게임 루프**라고 해요.

- `requestAnimationFrame(loop)` : 화면이 새로 그려질 때마다 `loop` 실행 (보통 초당 60번)
- 위치 `x += vx` 로 움직이고, 벽에 닿으면 `vx = -vx` 로 튕기기
- 키보드 `keydown` / 터치 `pointerdown` 으로 조작
""", r"""
<canvas id="c" width="320" height="220" style="background:#0f172a;border-radius:10px;touch-action:none"></canvas>
<p>화면을 누르면 공이 하나씩 늘어나요</p>
<script>
  const cv = document.getElementById("c"), ctx = cv.getContext("2d");
  const balls = [];
  const add = (x, y) => balls.push({ x, y, vx: Math.random() * 6 - 3, vy: -4, r: 8 + Math.random() * 10,
                                     color: `hsl(${Math.random() * 360} 80% 60%)` });
  add(160, 60);
  cv.onpointerdown = e => { const b = cv.getBoundingClientRect(); add(e.clientX - b.left, e.clientY - b.top); };
  function loop() {
    ctx.clearRect(0, 0, cv.width, cv.height);
    for (const b of balls) {
      b.vy += 0.25;                    // 중력
      b.x += b.vx; b.y += b.vy;
      if (b.x < b.r || b.x > cv.width - b.r) b.vx *= -1;
      if (b.y > cv.height - b.r) { b.y = cv.height - b.r; b.vy *= -0.85; }
      ctx.fillStyle = b.color;
      ctx.beginPath(); ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2); ctx.fill();
    }
    requestAnimationFrame(loop);
  }
  loop();
</script>
""", task="화면 아래쪽에 좌우 화살표 키(또는 화면 왼쪽·오른쪽 누르기)로 움직이는 막대(패들)를 만들고, 공이 패들에 닿으면 위로 튕기게 해 보세요. (벽돌 깨기의 시작!)"),
)
more("html", 8,
ls("웹 컴포넌트 (나만의 태그)", r"""
**웹 컴포넌트**로 `<my-counter>` 처럼 **나만의 HTML 태그**를 만들 수 있어요. React·Vue 같은 프레임워크의 아이디어를 브라우저가 직접 지원하는 거예요.

- `class MyTag extends HTMLElement { ... }`
- `customElements.define("my-tag", MyTag);` (이름에 `-` 가 꼭 있어야 해요)
- `this.attachShadow({ mode: "open" })` : **섀도 DOM** — 안의 CSS 가 바깥과 섞이지 않아요
- `connectedCallback()` : 페이지에 붙을 때 실행, `observedAttributes` + `attributeChangedCallback` : 속성이 바뀔 때
""", r"""
<my-counter label="물 마시기 🥛" step="1"></my-counter>
<my-counter label="팔굽혀펴기 💪" step="5"></my-counter>
<p style="color:red">바깥 CSS 는 컴포넌트 안에 영향을 못 줘요</p>
<script>
  class MyCounter extends HTMLElement {
    #n = 0;
    connectedCallback() {
      this.attachShadow({ mode: "open" }).innerHTML = `
        <style>
          .box { display:inline-flex; gap:8px; align-items:center; padding:8px 12px; margin:4px;
                 border-radius:12px; background:#eef2ff; font-family:sans-serif; }
          button { border:0; border-radius:8px; padding:4px 10px; background:#6366f1; color:#fff; font-size:16px; }
        </style>
        <div class="box"><span>${this.getAttribute("label")}</span><b>0</b><button>+</button></div>`;
      const step = +this.getAttribute("step") || 1;
      this.shadowRoot.querySelector("button").onclick = () => {
        this.#n += step;
        this.shadowRoot.querySelector("b").textContent = this.#n;
      };
    }
  }
  customElements.define("my-counter", MyCounter);
</script>
""", task="`max` 속성을 추가해서, 숫자가 max 에 닿으면 버튼이 꺼지고(`disabled`) 🎉 가 보이게 해 보세요. 그리고 `−` 버튼도 만들어 보세요."),
)

# ---------------- 🎨 CSS 중급 ~ 전문가 ----------------
more("css", 3,
ls("grid 레이아웃", r"""
**grid** 는 가로·세로 **표처럼** 배치해요. flex 가 한 줄이라면 grid 는 두 방향이에요.

- `display: grid;`
- `grid-template-columns: 200px 1fr 1fr;` 칸 너비 (`fr` = 남은 공간 나누기)
- `repeat(auto-fill, minmax(100px, 1fr))` : 화면 크기에 맞춰 **칸 수가 저절로**
- `grid-template-areas` 로 이름을 붙여 배치하면 한눈에 보여요
- `gap` 칸 사이 간격
""", r"""
<style>
  .page { display: grid; gap: 8px; height: 260px;
          grid-template-columns: 90px 1fr;
          grid-template-rows: 50px 1fr 40px;
          grid-template-areas: "head head" "side main" "foot foot"; }
  .page > * { border-radius: 8px; padding: 8px; color: white; font-weight: bold; }
  header { grid-area: head; background: #6366f1; }
  aside  { grid-area: side; background: #f59e0b; }
  main   { grid-area: main; background: #10b981; }
  footer { grid-area: foot; background: #64748b; }
  .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(70px, 1fr)); gap: 6px; margin-top: 10px; }
  .cards div { background: #e0e7ff; padding: 14px 0; text-align: center; border-radius: 8px; }
</style>
<div class="page"><header>머리</header><aside>메뉴</aside><main>본문</main><footer>꼬리</footer></div>
<div class="cards"><div>1</div><div>2</div><div>3</div><div>4</div><div>5</div><div>6</div><div>7</div></div>
""", task="`grid-template-areas` 만 바꿔서 메뉴(aside)를 **오른쪽**으로 옮기고, 꼬리(footer)가 본문 아래에만 오게 해 보세요."),
)
more("css", 4,
ls("position 과 z-index", r"""
- `static` : 기본 (그냥 순서대로)
- `relative` : 원래 자리 기준으로 살짝 옮기기, 그리고 **absolute 의 기준**이 돼요
- `absolute` : 가장 가까운 `relative` 부모 기준으로 원하는 위치에 (`top` `right` `bottom` `left`)
- `fixed` : 화면 기준 고정 (스크롤해도 그 자리)
- `sticky` : 스크롤하다 그 위치에 닿으면 붙어 있기
- `z-index` : 겹칠 때 **큰 숫자가 위**
""", r"""
<style>
  .card { position: relative; width: 220px; height: 120px; background: #e0f2fe; border-radius: 14px; margin: 20px; }
  .badge { position: absolute; top: -10px; right: -10px; background: #ef4444; color: white;
           width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center; font-weight: bold; }
  .a, .b { position: absolute; width: 70px; height: 70px; border-radius: 10px; opacity: .9; }
  .a { left: 20px; top: 30px; background: #6366f1; z-index: 2; }
  .b { left: 60px; top: 45px; background: #f59e0b; z-index: 1; }
  .bar { position: sticky; top: 0; background: #111827; color: white; padding: 6px; }
</style>
<div class="bar">sticky 메뉴 (아래로 스크롤해 보세요)</div>
<div class="card"><span class="badge">3</span><div class="a"></div><div class="b"></div></div>
<p style="height:400px">스크롤용 빈 공간…</p>
""", task="`z-index` 를 바꿔 주황 상자가 위로 오게 하고, 카드 **가운데**에 absolute 로 `NEW` 글자를 놓아 보세요. (`top: 50%; left: 50%; transform: translate(-50%, -50%)`)"),
)
more("css", 5,
ls("CSS 변수와 다크 모드", r"""
**CSS 변수**(사용자 정의 속성)로 색·크기를 한곳에서 관리해요.

- 만들기: `:root { --main: #6366f1; }`
- 쓰기: `color: var(--main);` / 없을 때 기본값 `var(--gap, 8px)`
- 클래스 하나로 변수만 바꾸면 **테마 전체**가 바뀌어요
- `@media (prefers-color-scheme: dark)` : 휴대폰이 다크 모드일 때 (이 앱도 이렇게 해요!)
""", r"""
<style>
  :root { --bg: #ffffff; --text: #111827; --card: #f1f5f9; --main: #6366f1; }
  .dark { --bg: #0f172a; --text: #e5e7eb; --card: #1e293b; --main: #a5b4fc; }
  body { background: var(--bg); color: var(--text); font-family: sans-serif; transition: background .3s, color .3s; }
  .card { background: var(--card); border-left: 6px solid var(--main); padding: 12px; border-radius: 10px; margin: 10px 0; }
  button { background: var(--main); color: var(--bg); border: 0; padding: 8px 14px; border-radius: 8px; }
</style>
<button onclick="document.body.classList.toggle('dark')">🌙 테마 바꾸기</button>
<div class="card">변수만 바꿨는데 모든 색이 바뀌어요.</div>
<div class="card">테마 색: <b style="color:var(--main)">var(--main)</b></div>
""", task="`--radius` 변수를 만들어 카드와 버튼의 둥근 정도를 한 번에 바꿀 수 있게 하고, 🌸 '벚꽃 테마' 클래스도 하나 더 만들어 보세요."),
)
more("css", 6,
ls("@keyframes 애니메이션", r"""
`transition` 은 A → B 한 번이지만, **`@keyframes`** 는 여러 단계를 **반복**할 수 있어요.

```
@keyframes 이름 { 0% { ... } 50% { ... } 100% { ... } }
.box { animation: 이름 1s ease-in-out infinite alternate; }
```

- `infinite` 무한 반복, `alternate` 갔다가 되돌아오기
- `animation-delay` 시작 지연 → 여러 개를 엇갈리게
- `transform` 과 `opacity` 를 움직이면 부드럽고 빨라요
""", r"""
<style>
  .row { display: flex; gap: 10px; padding: 30px; }
  .dot { width: 18px; height: 18px; border-radius: 50%; background: #6366f1;
         animation: jump .6s ease-in-out infinite alternate; }
  .dot:nth-child(2) { animation-delay: .2s; background: #10b981; }
  .dot:nth-child(3) { animation-delay: .4s; background: #f59e0b; }
  @keyframes jump { from { transform: translateY(0); } to { transform: translateY(-24px); } }

  .heart { font-size: 48px; display: inline-block; animation: beat 1s infinite; }
  @keyframes beat { 0%, 100% { transform: scale(1); } 15% { transform: scale(1.3); } 30% { transform: scale(1); } 45% { transform: scale(1.15); } }
</style>
<div class="row"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
<span class="heart">❤️</span> 로딩 중…
""", task="⭐ 이 한 바퀴 빙글 도는(`rotate(360deg)`) 동시에 색이 무지개처럼 바뀌는(`filter: hue-rotate(...)`) 애니메이션을 만들어 보세요."),
)
more("css", 7,
ls("3D 변환 (카드 뒤집기)", r"""
CSS 만으로 3D 효과를 낼 수 있어요.

- 부모에 `perspective: 800px;` : 원근감 (작을수록 강하게)
- `transform: rotateY(180deg)` : 세로축으로 뒤집기
- `transform-style: preserve-3d;` : 자식도 3D 공간에
- `backface-visibility: hidden;` : 뒤집힌 뒷면은 안 보이게
→ 앞면·뒷면 두 장을 겹쳐 놓고 뒷면을 미리 180° 돌려 두면 **뒤집히는 카드**!
""", r"""
<style>
  .scene { perspective: 800px; width: 180px; height: 240px; margin: 20px; }
  .card { width: 100%; height: 100%; position: relative; transition: transform .7s; transform-style: preserve-3d; cursor: pointer; }
  .scene.on .card { transform: rotateY(180deg); }
  .face { position: absolute; inset: 0; border-radius: 16px; display: grid; place-items: center;
          font: bold 22px sans-serif; color: white; backface-visibility: hidden; }
  .front { background: linear-gradient(135deg, #6366f1, #a855f7); }
  .back  { background: linear-gradient(135deg, #10b981, #06b6d4); transform: rotateY(180deg); }
</style>
<div class="scene" onclick="this.classList.toggle('on')">
  <div class="card"><div class="face front">❓ 문제<br>2¹⁰ = ?</div><div class="face back">💡 1024</div></div>
</div>
<p>카드를 눌러 보세요</p>
""", task="암기 카드 3장을 만들고, 마우스를 올리면(`:hover`) 카드가 살짝 기울어지게(`rotateX(10deg)`) 해 보세요."),
)
more("css", 8,
ls("clamp() 와 컨테이너 쿼리", r"""
요즘 CSS 는 **화면 크기에 따라 저절로 맞춰지는** 기능이 많아요.

- `clamp(최소, 원하는값, 최대)` : `font-size: clamp(16px, 4vw, 32px);` 화면에 따라 자라지만 범위 안에서만
- `min()`, `max()` 도 있어요
- **컨테이너 쿼리**: 화면이 아니라 **부모 상자의 크기**에 따라 바뀌기
  - 부모: `container-type: inline-size;`
  - 자식: `@container (min-width: 300px) { ... }`

같은 카드 부품이 좁은 사이드바에서도, 넓은 본문에서도 알맞게 보여요.
""", r"""
<style>
  h1 { font-size: clamp(18px, 6vw, 40px); margin: 6px 0; }
  .wrap { container-type: inline-size; border: 2px dashed #94a3b8; padding: 8px; margin: 8px 0; resize: horizontal; overflow: auto; }
  .card { display: flex; flex-direction: column; gap: 6px; background: #f1f5f9; border-radius: 12px; padding: 10px; }
  .card .pic { background: #a5b4fc; border-radius: 8px; height: 60px; }
  @container (min-width: 320px) {
    .card { flex-direction: row; align-items: center; }
    .card .pic { width: 90px; flex: none; }
  }
</style>
<h1>화면에 맞춰 크는 제목</h1>
<div class="wrap" style="width:200px"><div class="card"><div class="pic"></div><div>좁은 상자: 세로로</div></div></div>
<div class="wrap"><div class="card"><div class="pic"></div><div>넓은 상자: 가로로 (오른쪽 아래 모서리를 끌어 크기를 바꿔 보세요)</div></div></div>
""", task="컨테이너가 500px 이상이면 그림 크기를 키우고 글자도 `clamp()` 로 커지게 해 보세요."),
)

LINKS = [
  ("🐍 파이썬 더 배우기", [("점프 투 파이썬 (무료 책)", "https://wikidocs.net/book/1"), ("파이썬 공식 튜토리얼 (한국어)", "https://docs.python.org/ko/3/tutorial/")]),
  ("⚙️ C · C++", [("코드업 — C 기초 100제", "https://codeup.kr/problemsetsol.php?psid=23"), ("모두의 코드 — 씹어먹는 C 언어", "https://modoocode.com/231"), ("모두의 코드 — 씹어먹는 C++", "https://modoocode.com/135")]),
  ("🌐 웹 (HTML · CSS · JS)", [("MDN 웹 문서 (한국어)", "https://developer.mozilla.org/ko/docs/Learn"), ("모던 자바스크립트 튜토리얼", "https://ko.javascript.info/"), ("생활코딩 WEB", "https://opentutorials.org/course/3084")]),
  ("☕ 자바", [("생활코딩 JAVA", "https://opentutorials.org/course/3930"), ("점프 투 자바", "https://wikidocs.net/book/31")]),
  ("🗄️ SQL · 데이터베이스", [("SQLBolt (연습하며 배우기)", "https://sqlbolt.com/"), ("생활코딩 DATABASE", "https://opentutorials.org/course/3161")]),
  ("🧩 알고리즘 문제 풀기", [("백준 온라인 저지 — 단계별로 풀어보기", "https://www.acmicpc.net/step"), ("프로그래머스 코딩테스트 연습", "https://school.programmers.co.kr/learn/challenges"), ("정보올림피아드 (KOI)", "https://koi.or.kr/")]),
  ("🛠️ 그 밖에", [("Git 배우기 (Learn Git Branching)", "https://learngitbranching.js.org/?locale=ko"), ("코틀린 공식 문서", "https://kotlinlang.org/docs/home.html"), ("스위프트 (Swift) 공식 문서", "https://www.swift.org/documentation/"), ("러스트 (Rust) 책 한국어", "https://rinthel.github.io/rust-lang-book-ko/")]),
]
data = {"levels": [{"lv": i + 1, "name": n, "icon": ic, "desc": d} for i, (n, ic, d) in enumerate(LEVELS)], "langs": L, "links": [{"name": n, "items": [{"t": t, "u": u} for t, u in items]} for n, items in LINKS]}
json.dump(data, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(sum(len(l["lessons"]) for l in L), "lessons")
