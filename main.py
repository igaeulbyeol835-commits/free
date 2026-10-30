<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>치이카와 피하기 - 먼작귀 잠입 게임</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
            -webkit-user-select: none;
        }
        body {
            background-color: #121214;
            color: #ffffff;
            font-family: 'Pretendard', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            overflow: hidden;
        }
        #game-container {
            position: relative;
            width: 800px;
            height: 600px;
            max-width: 100vw;
            max-height: 100vh;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            border-radius: 12px;
            overflow: hidden;
            background-color: #1e1e24;
        }
        canvas {
            display: block;
            width: 100%;
            height: 100%;
        }
        /* 잡혔을 때 나타나는 오버레이 화면 */
        #caught-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(15, 15, 20, 0.92);
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 10;
            backdrop-filter: blur(5px);
            animation: fadeIn 0.3s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }
        #caught-title {
            font-size: 28px;
            font-weight: 800;
            color: #ff5252;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
        #caught-subtitle {
            font-size: 16px;
            color: #dddddd;
            margin-bottom: 25px;
        }
        #caught-avatar {
            width: 180px;
            height: 180px;
            border-radius: 50%;
            background: #ffffff;
            border: 6px solid #ff5252;
            box-shadow: 0 8px 25px rgba(255, 82, 82, 0.4);
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        #caught-avatar:hover {
            transform: scale(1.08);
            box-shadow: 0 12px 30px rgba(255, 82, 82, 0.6);
        }
        #caught-avatar:active {
            transform: scale(0.95);
        }
        #restart-hint {
            margin-top: 20px;
            font-size: 15px;
            color: #ffeb3b;
            font-weight: 600;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
        }
        /* UI 상단 보석 개수 */
        #ui-bar {
            position: absolute;
            top: 15px;
            left: 15px;
            right: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            pointer-events: none;
            z-index: 5;
        }
        .ui-badge {
            background: rgba(0, 0, 0, 0.65);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 16px;
            font-weight: bold;
            border: 1px solid rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(4px);
        }
    </style>
</head>
<body>

<div id="game-container">
    <div id="ui-bar">
        <div class="ui-badge" id="gem-status">💎 보석 획득: 0 / 1</div>
        <div class="ui-badge" style="color: #4fc3f7;">🏃‍♂️ 안전하게 탈출하세요!</div>
    </div>

    <canvas id="gameCanvas" width="800" height="600"></canvas>

    <!-- 게임 오버 오버레이 -->
    <div id="caught-overlay">
        <div id="caught-title">치이카와에게 잡혔습니다!</div>
        <div id="caught-subtitle"><span id="catcher-name" style="font-weight: bold; color: #ffeb3b;"></span>(이)가 당신을 발견했어요!</div>
        <div id="caught-avatar" onclick="restartGame()">
            <canvas id="avatarCanvas" width="160" height="160"></canvas>
        </div>
        <div id="restart-hint">👆 캐릭터 얼굴을 클릭하여 다시 시작하기</div>
    </div>
</div>

<script>
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const overlay = document.getElementById('caught-overlay');
const catcherNameEl = document.getElementById('catcher-name');
const avatarCanvas = document.getElementById('avatarCanvas');
const avatarCtx = avatarCanvas.getContext('2d');

let gameState = 'PLAYING'; // 'PLAYING', 'CAUGHT', 'WON'
let gemsCollected = 0;
const totalGems = 1;

// 키보드 입력 상태
const keys = {};
window.addEventListener('keydown', e => keys[e.key] = true);
window.addEventListener('keyup', e => keys[e.key] = false);

// 벽 설정
const walls = [
    {x: 150, y: 100, w: 20, h: 250},
    {x: 300, y: 250, w: 200, h: 20},
    {x: 600, y: 100, w: 20, h: 300},
    {x: 150, y: 450, w: 300, h: 20}
];

// 플레이어
const player = {
    x: 50,
    y: 50,
    radius: 14,
    speed: 3
};

// 탈출구 & 보석
const gem = { x: 720, y: 80, radius: 12, collected: false };
const exit = { x: 720, y: 500, w: 50, h: 50 };

// 치이카와 4인방 정찰원
const guards = [
    { id: 'chiikawa', name: '치이카와', x: 220, y: 180, angle: 0, speed: 1.2, waypoints: [{x:220, y:180}, {x:220, y:380}], currentWp: 0 },
    { id: 'hachiware', name: '하치와레', x: 400, y: 180, angle: Math.PI, speed: 1.5, waypoints: [{x:400, y:180}, {x:550, y:180}], currentWp: 0 },
    { id: 'usagi', name: '우사기', x: 520, y: 350, angle: 0, speed: 2.0, waypoints: [{x:520, y:350}, {x:520, y:520}, {x:350, y:520}], currentWp: 0 },
    { id: 'momonga', name: '모몬가', x: 100, y: 520, angle: 0, speed: 1.4, waypoints: [{x:100, y:520}, {x:280, y:520}], currentWp: 0 }
];

// --- 캐릭터 정면 얼굴 그리기 함수 ---
function drawCharacterFace(context, id, x, y, radius) {
    context.save();
    context.translate(x, y);

    const scale = radius / 20;
    context.scale(scale, scale);

    // 공통 볼터치 및 눈/입 스타일
    if (id === 'chiikawa') {
        // [1] 치이카와 (하얀 곰)
        // 귀
        context.fillStyle = '#ffffff';
        context.strokeStyle = '#333333';
        context.lineWidth = 2;
        context.beginPath(); context.arc(-13, -15, 7, 0, Math.PI*2); context.fill(); context.stroke();
        context.beginPath(); context.arc(13, -15, 7, 0, Math.PI*2); context.fill(); context.stroke();
        // 귀 안쪽 분홍
        context.fillStyle = '#ffb7c5';
        context.beginPath(); context.arc(-13, -15, 4, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(13, -15, 4, 0, Math.PI*2); context.fill();

        // 얼굴
        context.fillStyle = '#ffffff';
        context.beginPath(); context.arc(0, 0, 20, 0, Math.PI*2); context.fill(); context.stroke();

        // 눈
        context.fillStyle = '#222222';
        context.beginPath(); context.arc(-7, -2, 2.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(7, -2, 2.5, 0, Math.PI*2); context.fill();

        // 볼터치
        context.fillStyle = '#ff8a9e';
        context.beginPath(); context.arc(-11, 4, 3.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(11, 4, 3.5, 0, Math.PI*2); context.fill();

        // 입 (걱정스러운/귀여운 입)
        context.strokeStyle = '#333333';
        context.lineWidth = 1.5;
        context.beginPath(); context.arc(-2, 5, 2, 0, Math.PI); context.stroke();
        context.beginPath(); context.arc(2, 5, 2, 0, Math.PI); context.stroke();

    } else if (id === 'hachiware') {
        // [2] 하치와레 (파란 고양이)
        // 귀
        context.fillStyle = '#5c9ce6';
        context.strokeStyle = '#333333';
        context.lineWidth = 2;
        context.beginPath(); context.arc(-13, -15, 7, 0, Math.PI*2); context.fill(); context.stroke();
        context.beginPath(); context.arc(13, -15, 7, 0, Math.PI*2); context.fill(); stroke();

        // 얼굴 베이스
        context.fillStyle = '#ffffff';
        context.beginPath(); context.arc(0, 0, 20, 0, Math.PI*2); context.fill(); context.stroke();

        // 파란색 V자 머리 무늬
        context.fillStyle = '#5c9ce6';
        context.beginPath();
        context.moveTo(-20, 0);
        context.arc(0, 0, 20, Math.PI, Math.PI * 2);
        context.lineTo(0, -6);
        context.closePath();
        context.fill();
        context.stroke();

        // 눈
        context.fillStyle = '#222222';
        context.beginPath(); context.arc(-7, -1, 2.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(7, -1, 2.5, 0, Math.PI*2); context.fill();

        // 볼터치
        context.fillStyle = '#ff8a9e';
        context.beginPath(); context.arc(-11, 5, 3.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(11, 5, 3.5, 0, Math.PI*2); context.fill();

        // 웃는 입
        context.strokeStyle = '#333333';
        context.lineWidth = 1.5;
        context.beginPath(); context.arc(-2, 4, 2, 0, Math.PI); context.stroke();
        context.beginPath(); context.arc(2, 4, 2, 0, Math.PI); context.stroke();

    } else if (id === 'usagi') {
        // [3] 우사기 (노란 토끼)
        // 긴 귀
        context.fillStyle = '#fce282';
        context.strokeStyle = '#333333';
        context.lineWidth = 2;
        context.beginPath(); context.ellipse(-8, -25, 5, 14, -0.1, 0, Math.PI*2); context.fill(); context.stroke();
        context.beginPath(); context.ellipse(8, -25, 5, 14, 0.1, 0, Math.PI*2); context.fill(); context.stroke();

        // 얼굴
        context.fillStyle = '#fce282';
        context.beginPath(); context.arc(0, 0, 20, 0, Math.PI*2); context.fill(); context.stroke();

        // 눈 (신난 표정)
        context.fillStyle = '#222222';
        context.beginPath(); context.arc(-7, -2, 2.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(7, -2, 2.5, 0, Math.PI*2); context.fill();

        // 볼터치
        context.fillStyle = '#ff8a9e';
        context.beginPath(); context.arc(-11, 4, 3.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(11, 4, 3.5, 0, Math.PI*2); context.fill();

        // 벌린 입
        context.fillStyle = '#ff5252';
        context.beginPath(); context.arc(0, 4, 4, 0, Math.PI); context.fill(); context.stroke();

    } else if (id === 'momonga') {
        // [4] 모몬가 (하늘색 하늘다람쥐)
        // 큰 귀
        context.fillStyle = '#a2d2ff';
        context.strokeStyle = '#333333';
        context.lineWidth = 2;
        context.beginPath(); context.arc(-14, -15, 8, 0, Math.PI*2); context.fill(); context.stroke();
        context.beginPath(); context.arc(14, -15, 8, 0, Math.PI*2); context.fill(); context.stroke();
        context.fillStyle = '#ffffff';
        context.beginPath(); context.arc(-14, -15, 4, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(14, -15, 4, 0, Math.PI*2); context.fill();

        // 얼굴
        context.fillStyle = '#ffffff';
        context.beginPath(); context.arc(0, 0, 20, 0, Math.PI*2); context.fill(); context.stroke();

        // 머리 상단 하늘색 무늬
        context.fillStyle = '#a2d2ff';
        context.beginPath();
        context.arc(0, -5, 15, Math.PI, Math.PI*2);
        context.fill();

        // 큰 눈
        context.fillStyle = '#222222';
        context.beginPath(); context.arc(-7, -1, 3.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(7, -1, 3.5, 0, Math.PI*2); context.fill();
        context.fillStyle = '#ffffff';
        context.beginPath(); context.arc(-8, -2, 1.2, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(6, -2, 1.2, 0, Math.PI*2); context.fill();

        // 볼터치
        context.fillStyle = '#ff8a9e';
        context.beginPath(); context.arc(-11, 6, 3, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(11, 6, 3, 0, Math.PI*2); context.fill();

        // 입
        context.strokeStyle = '#333333';
        context.lineWidth = 1.5;
        context.beginPath(); context.arc(0, 5, 2, 0, Math.PI); context.stroke();
    }

    context.restore();
}

// 충돌 처리 (원 vs 사각형)
function rectIntersectCircle(rect, circle) {
    const closestX = Math.max(rect.x, Math.min(circle.x, rect.x + rect.w));
    const closestY = Math.max(rect.y, Math.min(circle.y, rect.y + rect.h));
    const distanceX = circle.x - closestX;
    const distanceY = circle.y - closestY;
    return (distanceX * distanceX + distanceY * distanceY) < (circle.radius * circle.radius);
}

// 메인 게임 루프
function update() {
    if (gameState !== 'PLAYING') return;

    // 플레이어 이동
    let dx = 0, dy = 0;
    if (keys['ArrowUp'] || keys['w'] || keys['W']) dy -= 1;
    if (keys['ArrowDown'] || keys['s'] || keys['S']) dy += 1;
    if (keys['ArrowLeft'] || keys['a'] || keys['A']) dx -= 1;
    if (keys['ArrowRight'] || keys['d'] || keys['D']) dx += 1;

    if (dx !== 0 && dy !== 0) {
        dx *= 0.7071;
        dy *= 0.7071;
    }

    const nextX = player.x + dx * player.speed;
    const nextY = player.y + dy * player.speed;

    // 벽 충돌 검사
    let canMoveX = true, canMoveY = true;
    for (let wall of walls) {
        if (rectIntersectCircle(wall, {x: nextX, y: player.y, radius: player.radius})) canMoveX = false;
        if (rectIntersectCircle(wall, {x: player.x, y: nextY, radius: player.radius})) canMoveY = false;
    }

    if (canMoveX && nextX > player.radius && nextX < canvas.width - player.radius) player.x = nextX;
    if (canMoveY && nextY > player.radius && nextY < canvas.height - player.radius) player.y = nextY;

    // 보석 획득
    if (!gem.collected) {
        const distToGem = Math.hypot(player.x - gem.x, player.y - gem.y);
        if (distToGem < player.radius + gem.radius) {
            gem.collected = true;
            gemsCollected = 1;
            document.getElementById('gem-status').innerText = '💎 보석 획득: 1 / 1 (출구로 가세요!)';
            document.getElementById('gem-status').style.color = '#ffeb3b';
        }
    }

    // 탈출 검사
    if (gem.collected && rectIntersectCircle(exit, player)) {
        alert('🎉 축하합니다! 치이카와들을 피해 보석을 훔쳐 탈출했습니다!');
        restartGame();
        return;
    }

    // 경비원(치이카와들) 업데이트
    for (let g of guards) {
        const target = g.waypoints[g.currentWp];
        const angleToTarget = Math.atan2(target.y - g.y, target.x - g.x);
        
        g.angle = angleToTarget;
        g.x += Math.cos(g.angle) * g.speed;
        g.y += Math.sin(g.angle) * g.speed;

        if (Math.hypot(target.x - g.x, target.y - g.y) < 5) {
            g.currentWp = (g.currentWp + 1) % g.waypoints.length;
        }

        // 플레이어 감지 (거리 및 시야각)
        const distToPlayer = Math.hypot(player.x - g.x, player.y - g.y);
        if (distToPlayer < 120) {
            let angleDiff = Math.abs(Math.atan2(player.y - g.y, player.x - g.x) - g.angle);
            if (angleDiff > Math.PI) angleDiff = Math.PI * 2 - angleDiff;

            if (angleDiff < Math.PI / 4 || distToPlayer < 25) { // 시야각 90도 내 또는 근접
                triggerCaught(g);
                return;
            }
        }
    }
}

// 잡혔을 때 처리
function triggerCaught(catcher) {
    gameState = 'CAUGHT';
    catcherNameEl.innerText = catcher.name;

    // 잡은 캐릭터 얼굴 크게 그리기
    avatarCtx.clearRect(0, 0, avatarCanvas.width, avatarCanvas.height);
    drawCharacterFace(avatarCtx, catcher.id, 80, 80, 60);

    overlay.style.display = 'flex';
}

// 게임 재시작
function restartGame() {
    player.x = 50;
    player.y = 50;
    gem.collected = false;
    gemsCollected = 0;
    document.getElementById('gem-status').innerText = '💎 보석 획득: 0 / 1';
    document.getElementById('gem-status').style.color = '#ffffff';
    overlay.style.display = 'none';
    gameState = 'PLAYING';
}

// 렌더링
function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // [1] 탈출구 & 보석
    ctx.fillStyle = gem.collected ? '#4caf50' : '#333333';
    ctx.fillRect(exit.x, exit.y, exit.w, exit.h);
    ctx.fillStyle = '#ffffff';
    ctx.font = '12px sans-serif';
    ctx.fillText('EXIT', exit.x + 12, exit.y + 30);

    if (!gem.collected) {
        ctx.fillStyle = '#00e5ff';
        ctx.beginPath();
        ctx.arc(gem.x, gem.y, gem.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 10;
        ctx.shadowColor = '#00e5ff';
        ctx.fill();
        ctx.shadowBlur = 0;
    }

    // [2] 벽
    ctx.fillStyle = '#3a3a4c';
    for (let w of walls) {
        ctx.fillRect(w.x, w.y, w.w, w.h);
    }

    // [3] 치이카와 정찰원들 (시야 부채꼴 + 정면 얼굴)
    for (let g of guards) {
        // 시야 그리기
        ctx.fillStyle = 'rgba(255, 82, 82, 0.25)';
        ctx.beginPath();
        ctx.moveTo(g.x, g.y);
        ctx.arc(g.x, g.y, 120, g.angle - Math.PI / 4, g.angle + Math.PI / 4);
        ctx.closePath();
        ctx.fill();

        // 정면 얼굴 그리기 (언제나 정면 유지)
        drawCharacterFace(ctx, g.id, g.x, g.y, 18);
    }

    // [4] 플레이어
    ctx.fillStyle = '#ffeb3b';
    ctx.beginPath();
    ctx.arc(player.x, player.y, player.radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();
}

function gameLoop() {
    update();
    render();
    requestAnimationFrame(gameLoop);
}

gameLoop();
</script>
</body>
</html>
