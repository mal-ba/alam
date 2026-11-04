import json, sys
L = []
def lang(key, name, run, intro, lessons):
    L.append({"key": key, "name": name, "run": run, "intro": intro, "lessons": lessons})
def ls(t, b, code, task="", hint="", ans="", expect="", stdin="", astdin=""):
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

LINKS = [
  ("🐍 파이썬 더 배우기", [("점프 투 파이썬 (무료 책)", "https://wikidocs.net/book/1"), ("파이썬 공식 튜토리얼 (한국어)", "https://docs.python.org/ko/3/tutorial/")]),
  ("⚙️ C · C++", [("코드업 — C 기초 100제", "https://codeup.kr/problemsetsol.php?psid=23"), ("모두의 코드 — 씹어먹는 C 언어", "https://modoocode.com/231"), ("모두의 코드 — 씹어먹는 C++", "https://modoocode.com/135")]),
  ("🌐 웹 (HTML · CSS · JS)", [("MDN 웹 문서 (한국어)", "https://developer.mozilla.org/ko/docs/Learn"), ("모던 자바스크립트 튜토리얼", "https://ko.javascript.info/"), ("생활코딩 WEB", "https://opentutorials.org/course/3084")]),
  ("☕ 자바", [("생활코딩 JAVA", "https://opentutorials.org/course/3930"), ("점프 투 자바", "https://wikidocs.net/book/31")]),
  ("🗄️ SQL · 데이터베이스", [("SQLBolt (연습하며 배우기)", "https://sqlbolt.com/"), ("생활코딩 DATABASE", "https://opentutorials.org/course/3161")]),
  ("🧩 알고리즘 문제 풀기", [("백준 온라인 저지 — 단계별로 풀어보기", "https://www.acmicpc.net/step"), ("프로그래머스 코딩테스트 연습", "https://school.programmers.co.kr/learn/challenges"), ("정보올림피아드 (KOI)", "https://koi.or.kr/")]),
  ("🛠️ 그 밖에", [("Git 배우기 (Learn Git Branching)", "https://learngitbranching.js.org/?locale=ko"), ("코틀린 공식 문서", "https://kotlinlang.org/docs/home.html"), ("스위프트 (Swift) 공식 문서", "https://www.swift.org/documentation/"), ("러스트 (Rust) 책 한국어", "https://rinthel.github.io/rust-lang-book-ko/")]),
]
data = {"langs": L, "links": [{"name": n, "items": [{"t": t, "u": u} for t, u in items]} for n, items in LINKS]}
json.dump(data, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(sum(len(l["lessons"]) for l in L), "lessons")
