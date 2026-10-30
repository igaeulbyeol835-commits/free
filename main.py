import streamlit as st
import streamlit.components.v1 as components

# 페이지 기본 설정
st.set_page_config(
    page_title="치이카와 피하기 게임",
    page_icon="🐹",
    layout="centered"
)

st.title("🐹 치이카와(먼작귀) 보석 훔치기 게임")
st.caption("치이카와, 하치와레, 우사기, 모몬가를 피해 보석을 훔치고 탈출하세요!")

# HTML/JS/CSS 게임 코드
game_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
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
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }
        #game-container {
            position: relative;
            width: 800px;
            height: 600px;
            border-radius: 12px;
            overflow: hidden;
            background-color: #1e1e24;
            box-shadow: 0 8px 24px rgba(0,0,0,0.5);
        }
        canvas {
            display: block;
            width: 100%;
            height: 100%;
        }
        /* 잡혔을 때 오버레이 */
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
        }
        #caught-title {
            font-size: 26px;
            font-weight: 800;
            color: #ff5252;
            margin-bottom: 8px;
        }
        #caught-subtitle {
            font-size: 15px;
            color: #dddddd;
            margin-bottom: 20px;
        }
        #caught-avatar {
            width: 160px;
            height: 160px;
            border-radius: 50%;
            background: #ffffff;
            border: 5px solid #ff5252;
            box-shadow: 0 8px 20px rgba(255, 82, 82, 0.4);
            cursor: pointer;
            transition: transform 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        #caught-avatar:hover {
            transform: scale(1.08);
        }
        #caught-avatar:active {
            transform: scale(0.95);
        }
        #restart-hint {
            margin-top: 18px;
            font-size: 14px;
            color: #ffeb3b;
            font-weight: 600;
        }
        /* 상단 UI */
        #ui-bar {
            position: absolute;
            top: 12px;
            left: 12px;
            right: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            pointer-events: none;
            z-index: 5;
        }
        .ui-badge {
            background: rgba(0, 0, 0, 0.65);
            padding: 6px 14px;
            border-radius: 16px;
            font-size: 14px;
            font-weight: bold;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
    </style>
</head>
<body>

<div id="game-container">
    <div id="ui-bar">
        <div class="ui-badge" id="gem-status">💎 보석 획득: 0 / 1</div>
        <div class="ui-badge" style="color: #4fc3f7;">🕹️ 방향키 / WASD 로 이동</div>
    </div>

    <canvas id="gameCanvas" width="800" height="600"></canvas>

    <div id="caught-overlay">
        <div id="caught-title">치이카와에게 잡혔습니다!</div>
        <div id="caught-subtitle"><span id="catcher-name" style="font-weight: bold; color: #ffeb3b;"></span>(이)가 당신을 발견했어요!</div>
        <div id="caught-avatar" onclick="restartGame()">
            <canvas id="avatarCanvas" width="140" height="140"></canvas>
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

let gameState = 'PLAYING';
let gemCollected = false;

const keys = {};
window.addEventListener('keydown', e => {
    keys[e.key] = true;
    if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].includes(e.key)) {
        e.preventDefault();
    }
});
window.addEventListener('keyup', e => keys[e.key] = false);

const walls = [
    {x: 150, y: 100, w: 20, h: 250},
    {x: 300, y: 250, w: 200, h: 20},
    {x: 600, y: 100, w: 20, h: 300},
    {x: 150, y: 450, w: 300, h: 20}
];

const player = { x: 50, y: 50, radius: 14, speed: 3 };
const gem = { x: 720, y: 80, radius: 12 };
const exit = { x: 720, y: 500, w: 50, h: 50 };

const guards = [
    { id: 'chiikawa', name: '치이카와', x: 220, y: 180, angle: 0, speed: 1.2, waypoints: [{x:220, y:180}, {x:220, y:380}], currentWp: 0 },
    { id: 'hachiware', name: '하치와레', x: 400, y: 180, angle: Math.PI, speed: 1.5, waypoints: [{x:400, y:180}, {x:550, y:180}], currentWp: 0 },
    { id: 'usagi', name: '우사기', x: 520, y: 350, angle: 0, speed: 2.0, waypoints: [{x:520, y:350}, {x:520, y:520}, {x:350, y:520}], currentWp: 0 },
    { id: 'momonga', name: '모몬가', x: 100, y: 520, angle: 0, speed: 1.4, waypoints: [{x:100, y:520}, {x:280, y:520}], currentWp: 0 }
];

function drawCharacterFace(context, id, x, y, radius) {
    context.save();
    context.translate(x, y);
    const scale = radius / 20;
    context.scale(scale, scale);

    if (id === 'chiikawa') {
        context.fillStyle = '#ffffff'; context.strokeStyle = '#333333'; context.lineWidth = 2;
        context.beginPath(); context.arc(-13, -15, 7, 0, Math.PI*2); context.fill(); context.stroke();
        context.beginPath(); context.arc(13, -15, 7, 0, Math.PI*2); context.fill(); context.stroke();
        context.fillStyle = '#ffb7c5';
        context.beginPath(); context.arc(-13, -15, 4, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(13, -15, 4, 0, Math.PI*2); context.fill();
        context.fillStyle = '#ffffff';
        context.beginPath(); context.arc(0, 0, 20, 0, Math.PI*2); context.fill(); context.stroke();
        context.fillStyle = '#222222';
        context.beginPath(); context.arc(-7, -2, 2.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(7, -2, 2.5, 0, Math.PI*2); context.fill();
        context.fillStyle = '#ff8a9e';
        context.beginPath(); context.arc(-11, 4, 3.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(11, 4, 3.5, 0, Math.PI*2); context.fill();
        context.strokeStyle = '#333333'; context.lineWidth = 1.5;
        context.beginPath(); context.arc(-2, 5, 2, 0, Math.PI); context.stroke();
        context.beginPath(); context.arc(2, 5, 2, 0, Math.PI); context.stroke();

    } else if (id === 'hachiware') {
        context.fillStyle = '#5c9ce6'; context.strokeStyle = '#333333'; context.lineWidth = 2;
        context.beginPath(); context.arc(-13, -15, 7, 0, Math.PI*2); context.fill(); context.stroke();
        context.beginPath(); context.arc(13, -15, 7, 0, Math.PI*2); context.fill(); context.stroke();
        context.fillStyle = '#ffffff';
        context.beginPath(); context.arc(0, 0, 20, 0, Math.PI*2); context.fill(); context.stroke();
        context.fillStyle = '#5c9ce6';
        context.beginPath(); context.moveTo(-20, 0); context.arc(0, 0, 20, Math.PI, Math.PI * 2); context.lineTo(0, -6); context.closePath(); context.fill(); context.stroke();
        context.fillStyle = '#222222';
        context.beginPath(); context.arc(-7, -1, 2.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(7, -1, 2.5, 0, Math.PI*2); context.fill();
        context.fillStyle = '#ff8a9e';
        context.beginPath(); context.arc(-11, 5, 3.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(11, 5, 3.5, 0, Math.PI*2); context.fill();
        context.strokeStyle = '#333333'; context.lineWidth = 1.5;
        context.beginPath(); context.arc(-2, 4, 2, 0, Math.PI); context.stroke();
        context.beginPath(); context.arc(2, 4, 2, 0, Math.PI); context.stroke();

    } else if (id === 'usagi') {
        context.fillStyle = '#fce282'; context.strokeStyle = '#333333'; context.lineWidth = 2;
        context.beginPath(); context.ellipse(-8, -25, 5, 14, -0.1, 0, Math.PI*2); context.fill(); context.stroke();
        context.beginPath(); context.ellipse(8, -25, 5, 14, 0.1, 0, Math.PI*2); context.fill(); context.stroke();
        context.beginPath(); context.arc(0, 0, 20, 0, Math.PI*2); context.fill(); context.stroke();
        context.fillStyle = '#222222';
        context.beginPath(); context.arc(-7, -2, 2.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(7, -2, 2.5, 0, Math.PI*2); context.fill();
        context.fillStyle = '#ff8a9e';
        context.beginPath(); context.arc(-11, 4, 3.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(11, 4, 3.5, 0, Math.PI*2); context.fill();
        context.fillStyle = '#ff5252';
        context.beginPath(); context.arc(0, 4, 4, 0, Math.PI); context.fill(); context.stroke();

    } else if (id === 'momonga') {
        context.fillStyle = '#a2d2ff'; context.strokeStyle = '#333333'; context.lineWidth = 2;
        context.beginPath(); context.arc(-14, -15, 8, 0, Math.PI*2); context.fill(); context.stroke();
        context.beginPath(); context.arc(14, -15, 8, 0, Math.PI*2); context.fill(); context.stroke();
        context.fillStyle = '#ffffff';
        context.beginPath(); context.arc(-14, -15, 4, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(14, -15, 4, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(0, 0, 20, 0, Math.PI*2); context.fill(); context.stroke();
        context.fillStyle = '#a2d2ff';
        context.beginPath(); context.arc(0, -5, 15, Math.PI, Math.PI*2); context.fill();
        context.fillStyle = '#222222';
        context.beginPath(); context.arc(-7, -1, 3.5, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(7, -1, 3.5, 0, Math.PI*2); context.fill();
        context.fillStyle = '#ff8a9e';
        context.beginPath(); context.arc(-11, 6, 3, 0, Math.PI*2); context.fill();
        context.beginPath(); context.arc(11, 6, 3, 0, Math.PI*2); context.fill();
        context.strokeStyle = '#333333'; context.lineWidth = 1.5;
        context.beginPath(); context.arc(0, 5, 2, 0, Math.PI); context.stroke();
    }
    context.restore();
}

function rectIntersectCircle(rect, circle) {
    const closestX = Math.max(rect.x, Math.min(circle.x, rect.x + rect.w));
    const closestY = Math.max(rect.y, Math.min(circle.y, rect.y + rect.h));
    const distanceX = circle.x - closestX;
    const distanceY = circle.y - closestY;
    return (distanceX * distanceX + distanceY * distanceY) < (circle.radius * circle.radius);
}

function update() {
    if (gameState !== 'PLAYING') return;

    let dx = 0, dy = 0;
    if (keys['ArrowUp'] || keys['w'] || keys['W']) dy -= 1;
    if (keys['ArrowDown'] || keys['s'] || keys['S']) dy += 1;
    if (keys['ArrowLeft'] || keys['a'] || keys['A']) dx -= 1;
    if (keys['ArrowRight'] || keys['d'] || keys['D']) dx += 1;

    if (dx !== 0 && dy !== 0) { dx *= 0.7071; dy *= 0.7071; }

    const nextX = player.x + dx * player.speed;
    const nextY = player.y + dy * player.speed;

    let canMoveX = true, canMoveY = true;
    for (let wall of walls) {
        if (rectIntersectCircle(wall, {x: nextX, y: player.y, radius: player.radius})) canMoveX = false;
        if (rectIntersectCircle(wall, {x: player.x, y: nextY, radius: player.radius})) canMoveY = false;
    }

    if (canMoveX && nextX > player.radius && nextX < canvas.width - player.radius) player.x = nextX;
    if (canMoveY && nextY > player.radius && nextY < canvas.height - player.radius) player.y = nextY;

    if (!gemCollected) {
        const distToGem = Math.hypot(player.x - gem.x, player.y - gem.y);
        if (distToGem < player.radius + gem.radius) {
            gemCollected = true;
            document.getElementById('gem-status').innerText = '💎 보석 획득: 1 / 1 (출구로 가세요!)';
            document.getElementById('gem-status').style.color = '#ffeb3b';
        }
    }

    if (gemCollected && rectIntersectCircle(exit, player)) {
        alert('🎉 축하합니다! 치이카와들을 피해 탈출 성공!');
        restartGame();
        return;
    }

    for (let g of guards) {
        const target = g.waypoints[g.currentWp];
        const angleToTarget = Math.atan2(target.y - g.y, target.x - g.x);
        g.angle = angleToTarget;
        g.x += Math.cos(g.angle) * g.speed;
        g.y += Math.sin(g.angle) * g.speed;

        if (Math.hypot(target.x - g.x, target.y - g.y) < 5) {
            g.currentWp = (g.currentWp + 1) % g.waypoints.length;
        }

        const distToPlayer = Math.hypot(player.x - g.x, player.y - g.y);
        if (distToPlayer < 120) {
            let angleDiff = Math.abs(Math.atan2(player.y - g.y, player.x - g.x) - g.angle);
            if (angleDiff > Math.PI) angleDiff = Math.PI * 2 - angleDiff;
            if (angleDiff < Math.PI / 4 || distToPlayer < 25) {
                triggerCaught(g);
                return;
            }
        }
    }
}

function triggerCaught(catcher) {
    gameState = 'CAUGHT';
    catcherNameEl.innerText = catcher.name;
    avatarCtx.clearRect(0, 0, avatarCanvas.width, avatarCanvas.height);
    drawCharacterFace(avatarCtx, catcher.id, 70, 70, 50);
    overlay.style.display = 'flex';
}

function restartGame() {
    player.x = 50;
    player.y = 50;
    gemCollected = false;
    document.getElementById('gem-status').innerText = '💎 보석 획득: 0 / 1';
    document.getElementById('gem-status').style.color = '#ffffff';
    overlay.style.display = 'none';
    gameState = 'PLAYING';
}

function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = gemCollected ? '#4caf50' : '#333333';
    ctx.fillRect(exit.x, exit.y, exit.w, exit.h);
    ctx.fillStyle = '#ffffff';
    ctx.font = '12px sans-serif';
    ctx.fillText('EXIT', exit.x + 12, exit.y + 30);

    if (!gemCollected) {
        ctx.fillStyle = '#00e5ff';
        ctx.beginPath();
        ctx.arc(gem.x, gem.y, gem.radius, 0, Math.PI * 2);
        ctx.fill();
    }

    ctx.fillStyle = '#3a3a4c';
    for (let w of walls) {
        ctx.fillRect(w.x, w.y, w.w, w.h);
    }

    for (let g of guards) {
        ctx.fillStyle = 'rgba(255, 82, 82, 0.25)';
        ctx.beginPath();
        ctx.moveTo(g.x, g.y);
        ctx.arc(g.x, g.y, 120, g.angle - Math.PI / 4, g.angle + Math.PI / 4);
        ctx.closePath();
        ctx.fill();

        drawCharacterFace(ctx, g.id, g.x, g.y, 18);
    }

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
"""

# Streamlit Component로 HTML 렌더링
components.html(game_html, height=620)
