#!/bin/bash
# 클라우드 세션에서 커밋 작성자를 Claude 대신 저장소 주인으로 설정
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"
git config user.name "issue"
git config user.email "198208151+mal-ba@users.noreply.github.com"
