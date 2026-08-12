# Cynovela settlement — one-command smoke recipes (non-stale)

## Standalone (host)
unset SSL_CERT_FILE
./launch.sh --demo --mode text --port 8770
curl -s http://127.0.0.1:8770/ -o /dev/null -w "%{http_code}\n"   # expect 200
# admin login: cynovela （初回ログイン時にパスワード変更を求められます。パスワードは配布物と同じ場所の admin-password.txt）
# API token: POST /api/auth/login (username + password) が返す access_token を Bearer に使う。
#   固定トークンは廃止済み（C-B5 2026-07-29）。起動形態によらず demo-token-* は 401 になる。
#   例: TOKEN=$(curl -s -X POST http://127.0.0.1:8770/api/auth/login \
#          -H 'Content-Type: application/json' \
#          -d "{\"username\":\"cynovela\",\"password\":\"$ADMIN_PW\"}" | python3 -c 'import json,sys;print(json.load(sys.stdin)["access_token"])')
#   初回パスワード変更を済ませるまで管理系 API は 403（変更 API のみ通る）。

## Container (podman)
./launch.sh     # builds every time + runs on :8801
# LLM (同梱の既定 = LM Studio): POST /api/settings/llm
#   provider=lmstudio base_url=http://host.containers.internal:1234/v1 model=<LM Studio でロード中のチャット用モデル名>
#   model は "auto" にしない（一覧の先頭が埋め込み専用モデルだと生成要求が 400 になる: B2 実測 2026-07-29）。
#   Ollama を使う場合のみ: provider=ollama base_url=http://host.containers.internal:11434/v1 model=<pull 済みモデル名> api_key=dummy

## K8s (Lima k3s-genk8s)
export KUBECONFIG=~/.lima/k3s-genk8s/copied-from-guest/kubeconfig.yaml
# image must be in VM containerd: podman save localhost/cynovela-all-in-one:latest | limactl shell k3s-genk8s sudo ctr -n k8s.io images import -
kubectl apply -f deploy/k8s/        # namespace, pvc, deployment, service
kubectl -n cynovela rollout status deploy/cynovela --timeout=300s
kubectl -n cynovela port-forward svc/cynovela-svc 8890:8765 &
curl -s http://127.0.0.1:8890/ -o /dev/null -w "%{http_code}\n"   # expect 200
# LLM gateway from pod: http://192.168.5.2:1234/v1 (LM Studio を "Serve on Local Network" で公開した場合)
#   Ollama を使う場合のみ: http://192.168.5.2:11434/v1 (OLLAMA_HOST=0.0.0.0) + api_key=dummy
#   どちらも model は実在するチャット用モデル名を指定する（"auto" は避ける）。
