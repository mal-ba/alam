// 앱보다 먼저 실행돼요 (index.html <head>).
// 🔒 다른 사이트가 이 앱을 보이지 않는 틀(iframe)에 넣고 누르게 속이는 것(클릭재킹)을 막아요.
//    GitHub Pages 는 X-Frame-Options 헤더를 못 붙여서 여기서 직접 막아요.
if (window.top !== window.self) {
  document.documentElement.style.display = "none";
  try { window.top.location = window.self.location.href; } catch (e) { /* 막혀도 화면은 이미 숨겼어요 */ }
}
// 연결 정보는 캐시 없이 항상 새로 받기 (예전 빈 config.js 가 남아 있지 않게)
document.write('<script src="config.js?v=' + Date.now() + '"><\/script>');
