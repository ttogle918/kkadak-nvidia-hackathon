# 행사 카탈로그 주기 수집 (호스트)

수집기는 호스트에서 돈다(D7). 공공데이터 키는 호스트 셸 env 또는 레포 `.env` 에서만 읽고 샌드박스에는 넣지 않는다.

출처마다 주기가 다르다(`domains/kcontext/data/catalog_sources.json` 의 `cadence_hours`). 서울시 문화행사 정보는
"매일 1회" 갱신이라 24시간이다. 아래 어느 방식이든 **30분마다** 깨워서 `due` 가 주기가 된 출처만 수집하게 하면 된다
(실패한 출처는 5분·10분·20분… 최대 6시간 뒤에 다시 시도한다).

## 방법 1 — cron

```cron
*/30 * * * *  cd /path/to/nvidia-hackathon && uv run python -m domains.kcontext.catalog due >> var/catalog/due.log 2>&1
```

## 방법 2 — systemd 타이머 (사용자 단위)

`~/.config/systemd/user/kc-catalog.service`
```ini
[Unit]
Description=K-Context event catalog collection

[Service]
Type=oneshot
WorkingDirectory=/path/to/nvidia-hackathon
ExecStart=/usr/bin/env uv run python -m domains.kcontext.catalog due
```

`~/.config/systemd/user/kc-catalog.timer`
```ini
[Unit]
Description=Run the catalog collection every 30 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=30min
Persistent=true

[Install]
WantedBy=timers.target
```
```bash
systemctl --user daemon-reload && systemctl --user enable --now kc-catalog.timer
```

## 방법 3 — 한 프로세스로 계속 돌리기
```bash
uv run python -m domains.kcontext.catalog loop --interval-min 30
```

## 확인
```bash
uv run python -m domains.kcontext.catalog status    # 출처별 마지막 성공·오류·재시도 시각
```
관리자 화면(`/admin.html`)에서도 같은 정보를 보고 "지금 다시 수집"을 누를 수 있다.

수집이 실패하면 기존 데이터는 그대로 두고 오류만 기록한다. 목록에서 사라진 게시글을 취소로 처리하지 않는다.
