"""
모든 DRF View에 인증 클래스가 명시적으로 설정돼 있는지 검사한다.

AllowAny 는 명시적으로 열어둔 엔드포인트이므로 허용.
authentication_classes / permission_classes 가 아예 없는 뷰(= 기본값에 의존)를 탐지.

사용:
    python scripts/check_auth_classes.py   → 문제 없으면 exit 0
"""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
VIEWS_DIRS = [ROOT / "apps"]

# 인증/권한 클래스를 명시하지 않아도 되는 예외 클래스명
_EXEMPT = {"HealthCheckView"}

issues: list[str] = []


def _check_file(path: Path) -> None:
    src = path.read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if node.name in _EXEMPT:
            continue

        # APIView / ViewSet 계열만 검사
        bases = [
            (b.id if isinstance(b, ast.Name) else getattr(b, "attr", ""))
            for b in node.bases
        ]
        is_view = any(
            "View" in b or "ViewSet" in b or "Mixin" in b
            for b in bases
        )
        if not is_view:
            continue

        attrs = {
            n.targets[0].id
            for n in node.body
            if isinstance(n, ast.Assign)
            and isinstance(n.targets[0], ast.Name)
        }
        if "permission_classes" not in attrs:
            issues.append(
                f"{path.relative_to(ROOT)}:{node.lineno}  {node.name}  — permission_classes 없음"
            )


for views_dir in VIEWS_DIRS:
    for f in views_dir.rglob("views*.py"):
        _check_file(f)

if issues:
    print("❌ permission_classes 미설정 뷰:")
    for i in issues:
        print(" ", i)
    sys.exit(1)

print(f"✅ permission_classes 검사 통과 ({sum(1 for _ in VIEWS_DIRS[0].rglob('views*.py'))} 파일)")
