
function flagImg(url) {
  return url ? '<img class="flag" src="' + url + '" />' : '';
}

function formatDate(s) {
  if (!s) return "";
  const d = new Date(s);
  return d.toLocaleString("zh-TW", { hour12: false });
}

function renderMiniTags(tags) {
  if (!tags || tags.length === 0) return "";
  return '<div class="quick-meta">' + tags.slice(0, 3).join("　") + '</div>';
}

function renderList(title, desc, list) {
  if (!list || list.length === 0) return "";

  const content = list.map(function(m, index) {
    const dateText = m.date ? formatDate(m.date) : "日期待定";
    const meta = [m.round || "世界盃小組賽", m.venue || "場地待定"].filter(Boolean).join("｜");
    return '<div class="quick" data-home="' + m.home + '" data-away="' + m.away + '" data-fixture="' + (m.fixtureId || "") + '">' +
      '<div class="quick-date">' + dateText + '</div>' +
      '<div class="quick-top">' +
        '<div class="quick-title">' + (index + 1) + '. ' + flagImg(m.homeFlag) + m.home + ' vs ' + flagImg(m.awayFlag) + m.away + '</div>' +
        '<div class="score-pill">AI ' + (m.qualityScore || m.stars || "觀察") + '</div>' +
      '</div>' +
      '<div class="quick-meta">' + meta + '</div>' +
      '<div class="quick-meta">' + (m.recommendation || "焦點觀察") + (m.homeRate ? "｜" + m.homeRate + "% : " + m.awayRate + "%" : "") + '</div>' +
      '<div class="quick-meta">' + (m.predictedScore ? "AI比分 " + m.predictedScore + "｜" : "") + (m.goalModel ? "高進球" + m.goalModel.over25 + "%｜BTTS " + m.goalModel.btts + "%｜" : "") + (m.upsetModel ? "變數" + m.upsetModel.upsetIndex + "%" : "") + '</div>' +
      renderMiniTags(m.tags) +
    '</div>';
  }).join("");

  return '<div class="reco-group">' +
    '<div class="reco-tab" onclick="toggleReco(this)">' +
      '<div>' + title + '</div>' +
      '<span>' + desc + ' ▼</span>' +
    '</div>' +
    '<div class="reco-content">' + content + '</div>' +
  '</div>';
}

function toggleReco(el) {
  const group = el.parentElement;
  group.classList.toggle("open");

  const span = el.querySelector("span");
  if (group.classList.contains("open")) {
    span.innerText = span.innerText.replace("▼", "▲");
  } else {
    span.innerText = span.innerText.replace("▲", "▼");
  }
}


function renderScheduleGame(g) {
  return '<div class="schedule-game" data-home="' + g.home + '" data-away="' + g.away + '">' +
    '<div class="schedule-top">' +
      '<div class="schedule-title">' + flagImg(g.homeFlag) + g.home + ' vs ' + flagImg(g.awayFlag) + g.away + '</div>' +
      '<div class="schedule-pill">' + (g.round || "小組賽") + '</div>' +
    '</div>' +
    '<div class="schedule-meta">' + (g.time || formatDate(g.date)) + (g.venue ? "｜" + g.venue : "") + '</div>' +
    '<div class="schedule-meta">' + (g.status || "未開賽") + '</div>' +
  '</div>';
}

let standingsGroups = [];
let standingsIndex = 0;
let standingsTimer = null;

function renderStandingsDots(total, active) {
  const dots = document.getElementById("standingsDots");
  if (!dots) return;

  dots.innerHTML = Array.from({ length: total }).map(function(_, index) {
    return '<button class="standings-dot' + (index === active ? ' active' : '') + '" aria-label="切換到第 ' + (index + 1) + ' 組" onclick="showStandingsGroup(' + index + ')"></button>';
  }).join("");
}

function renderStandingsGroup(group, index, total) {
  const teams = Array.isArray(group.teams) ? group.teams.slice(0, 4) : [];

  return '<div class="standings-group">' +
    '<div class="standings-group-name">' +
      '<span>' + (group.group || "小組") + '積分</span>' +
      '<span>' + (index + 1) + ' / ' + total + '</span>' +
    '</div>' +
    '<div class="standings-table">' +
      '<div class="standings-row header">' +
        '<span>排名</span><span>球隊</span><span>賽</span><span>勝</span><span>平</span><span>負</span><span>淨勝</span><span>積分</span>' +
      '</div>' +
      teams.map(function(team) {
        return '<div class="standings-row">' +
          '<span>' + team.rank + '</span>' +
          '<span class="standings-team">' + flagImg(team.flag) + team.team + '</span>' +
          '<span>' + team.played + '</span>' +
          '<span>' + team.wins + '</span>' +
          '<span>' + team.draws + '</span>' +
          '<span>' + team.losses + '</span>' +
          '<span>' + (team.gd > 0 ? "+" + team.gd : team.gd) + '</span>' +
          '<span class="standings-pts">' + team.pts + '</span>' +
        '</div>';
      }).join("") +
    '</div>' +
  '</div>';
}

function showStandingsGroup(nextIndex) {
  const panel = document.getElementById("standingsPanel");
  if (!panel || standingsGroups.length === 0) return;

  standingsIndex = (nextIndex + standingsGroups.length) % standingsGroups.length;
  panel.classList.remove("bounce");
  panel.innerHTML = renderStandingsGroup(standingsGroups[standingsIndex], standingsIndex, standingsGroups.length);
  void panel.offsetWidth;
  panel.classList.add("bounce");
  renderStandingsDots(standingsGroups.length, standingsIndex);
}

async function loadGroupStandings() {
  const panel = document.getElementById("standingsPanel");
  const source = document.getElementById("standingsSource");
  if (!panel) return;

  try {
    const res = await fetch("FOOTBALL_FULL_DATABASE_DUMP.json?v=" + Date.now(), { cache: "no-store" });
    const db = await res.json();
    const data = db.endpoints && db.endpoints.groupStandings ? db.endpoints.groupStandings : {};

    standingsGroups = Array.isArray(data.groups) ? data.groups.filter(function(group) {
      return Array.isArray(group.teams) && group.teams.length > 0;
    }) : [];

    if (source) {
      source.innerText = data.source === "ttyingqiu-standings-cache" ? "天天盈球資料" : "小組積分";
    }

    if (standingsGroups.length === 0) {
      panel.innerHTML = "目前尚未取得小組積分。";
      return;
    }

    showStandingsGroup(0);

    if (standingsTimer) clearInterval(standingsTimer);
    standingsTimer = setInterval(function() {
      showStandingsGroup(standingsIndex + 1);
    }, 4200);
  } catch (err) {
    console.error("loadGroupStandings error:", err);
    panel.innerHTML = "小組積分讀取失敗，請稍後再試。";
  }
}


function toggleScheduleCenter() {
  const card = document.getElementById("scheduleCard");
  const arrow = document.getElementById("scheduleArrow");
  if (!card || !arrow) return;

  const open = card.classList.toggle("open");
  arrow.innerText = open ? "近期賽程 ▲" : "近期賽程 ▼";
}

async function loadScheduleCenter() {
  const scheduleBox = document.getElementById("scheduleBox");
  const stageBox = document.getElementById("stageBox");
  const scheduleList = document.getElementById("scheduleList");

  if (!scheduleBox || !stageBox || !scheduleList) return;

  try {
    const res = await fetch("FOOTBALL_FULL_DATABASE_DUMP.json?v=" + Date.now(), { cache: "no-store" });
const db = await res.json();
const data = db.endpoints.schedule;

    const games = Array.isArray(data.scheduleGames) ? data.scheduleGames.slice(0, 3) : [];
    const next = data.nextGame || games[0] || {};
    const nextMatch = next.home && next.away ? next.home + " vs " + next.away : "尚未取得";
    const nextTime = next.home && next.away ? (next.time || formatDate(next.date)) : "";

    scheduleBox.innerText = "已讀取已鎖定賽程資料，近期顯示三場。";

    stageBox.innerHTML =
      '<div class="stageItem"><b>目前階段</b><span>' + (data.stageLabel || "小組賽準備中") + '</span></div>' +
      '<div class="stageItem"><b>下一場比賽</b><span class="next-match-name">' + nextMatch + '</span>' +
        (nextTime ? '<span class="next-match-time">' + nextTime + '</span>' : '') +
      '</div>';

    scheduleList.innerHTML = games.map(renderScheduleGame).join("");

    document.querySelectorAll(".schedule-game").forEach(function(el) {
      el.onclick = function() {
        quickMatch(el.dataset.home, el.dataset.away, "");
      };
    });
  } catch (err) {
    console.error("loadScheduleCenter error:", err);
    scheduleBox.innerText = "賽程資料讀取失敗，請稍後再試。";
  }
}


async function loadRecommended() {
  const box = document.getElementById("recommended");
  const info = document.getElementById("autoInfo");

  try {
    const res = await fetch("FOOTBALL_FULL_DATABASE_DUMP.json?v=" + Date.now(), { cache: "no-store" });
const db = await res.json();
const data = db.endpoints.recommended;

    if (data.source === "today") {
      info.innerText = "已自動抓取今日賽程：" + data.date;
    } else if (data.source === "upcoming") {
      info.innerText = "今日暫無賽事，已抓取最近一輪：" + data.date;
    } else if (data.source === "official-worldcup") {
      info.innerText = "已讀取已鎖定賽程，並由後端模型完成分析。";
    } else if (data.source === "site-local-worldcup-model" || data.source === "official-worldcup-schedule-fallback") {
      info.innerText = "已讀取世界盃開賽後賽程，並由站內模型完成分析。";
    } else {
      info.innerText = "已讀取站內模型觀察組合。";
    }

    box.innerHTML =
      renderList("🔥 焦點比賽分析", "綜合熱度", data.strongSignals) +
      renderList("⚽ 進攻節奏分析", "大小球模型", data.goalSignals) +
      renderList("⚠️ 比賽風格觀察", "變數風險", data.upsetSignals);

    document.querySelectorAll(".quick").forEach(function(el) {
      el.onclick = function() {
        quickMatch(el.dataset.home, el.dataset.away, el.dataset.fixture || "");
      };
    });
  } catch (err) {
    console.error("loadRecommended error:", err);
    box.innerHTML = "暫時無法載入推薦";
  }
}

function quickMatch(home, away, fixtureId) {
  document.getElementById("home").value = home;
  document.getElementById("away").value = away;
  analyze(fixtureId || "");
}

function renderTags(data) {
  if (!data.tags || data.tags.length === 0) return "";
  return '<div class="tags">' + (data.tags || []).map(function(t) {
    return '<span class="tag">' + t + '</span>';
  }).join("") + '</div>';
}

function renderModelCards(data) {
  const rows = [
    ["⚽ Over 2.5", data.goalModel.over25],
    ["🧊 Under 2.5", data.goalModel.under25],
    ["🥅 BTTS", data.goalModel.btts],
    ["⚠️ 變數風險", data.upsetModel.upsetIndex]
  ];

  const edge = Math.abs((Number(data.homeRate) || 0) - (Number(data.awayRate) || 0));
  const context = [
    "勝率差 " + edge + "%",
    "預期進球 " + data.goalModel.expectedGoals,
    data.goalModel.homeExpectedGoals && data.goalModel.awayExpectedGoals ? data.home + " xG " + data.goalModel.homeExpectedGoals + " / " + data.away + " xG " + data.goalModel.awayExpectedGoals : "",
    data.teamTierModel ? data.home + " " + data.teamTierModel.homeTier + " / " + data.away + " " + data.teamTierModel.awayTier : "",
    "BTTS " + data.goalModel.btts + "%",
    "變數 " + data.upsetModel.upsetIndex + "%"
  ].filter(Boolean);

  return '<div class="model-grid">' +
    '<div class="model-card"><b>高進球率</b><div>' + data.goalModel.over25 + '%</div></div>' +
    '<div class="model-card"><b>低進球率</b><div>' + data.goalModel.under25 + '%</div></div>' +
    '<div class="model-card"><b>雙方進球</b><div>' + data.goalModel.btts + '%</div></div>' +
    '<div class="model-card"><b>變數指數</b><div>' + data.upsetModel.upsetIndex + '%</div></div>' +
  '</div>' +
  '<div class="model-context">' +
    '<b>模型依據</b><span>' + context.join("｜") + '</span>' +
    '<em>資料：站內賽程模型、公開資訊補強、隊伍強弱分層、攻防係數與進球分布估算。</em>' +
  '</div>' +
  '<div class="goal-bars">' + rows.map(function(r) {
    return '<div class="goal-line"><div>' + r[0] + '</div><div class="goal-track"><div class="goal-fill" style="width:' + r[1] + '%"></div></div><b>' + r[1] + '%</b></div>';
  }).join("") + '</div>';
}

function renderRecommendationPanel(data) {
  const panel = Array.isArray(data.recommendationPanel) ? data.recommendationPanel : [
    { label: "比分", value: data.predictedScore, confidence: data.modelScore },
    { label: "大小球", value: data.goalModel.over25 >= 58 ? "大 2.5" : data.goalModel.over25 <= 48 ? "小 2.5" : "2/2.5 觀察", confidence: data.goalModel.over25 >= 58 ? data.goalModel.over25 : data.goalModel.under25 },
    { label: "勝率方向", value: data.predictedWinner + " " + Math.max(data.homeRate, data.awayRate) + "%", confidence: Math.max(data.homeRate, data.awayRate) },
    { label: "進球數", value: data.goalModel.expectedGoals >= 2.75 ? "2-4 球" : data.goalModel.expectedGoals <= 2.25 ? "1-2 球" : "2-3 球", confidence: Math.round(data.goalModel.expectedGoals * 22) },
    { label: "雙方進球", value: data.goalModel.btts >= 58 ? "是" : "觀察", confidence: data.goalModel.btts },
    { label: "特1/半場", value: data.goalModel.expectedGoals >= 2.75 ? "特1：上半場有球" : "特1：上半場小 1", confidence: data.goalModel.expectedGoals >= 2.75 ? 61 : 56 }
  ];

  return '<div class="model-grid recommendation-grid">' +
    panel.slice(0, 8).map(function(item) {
      const confidence = Math.max(0, Math.min(99, Math.round(item.confidence || 0)));
      return '<div class="model-card recommendation-card">' +
        '<b>' + item.label + '</b>' +
        '<div>' + item.value + '</div>' +
        '<span>信心 ' + confidence + '%</span>' +
      '</div>';
    }).join("") +
  '</div>';
}

function renderRadar(data) {
  if (!data.radar) return "";

  const rows = [
    ["攻擊力", data.radar.attack],
    ["防守力", data.radar.defense],
    ["近期狀態", data.radar.form],
    ["市場熱度", data.radar.market],
    ["進球熱度", data.radar.goals],
    ["變數風險", data.radar.upset],
    ["歷史交手", data.radar.history]
  ];

  const cx = 90;
  const cy = 90;
  const maxR = 72;
  const points = rows.map(function(r, i) {
    const angle = (-90 + i * 360 / rows.length) * Math.PI / 180;
    const rr = maxR * (r[1] / 100);
    return [Math.round(cx + Math.cos(angle) * rr), Math.round(cy + Math.sin(angle) * rr)].join(",");
  }).join(" ");

  const grid = [25, 50, 75, 100].map(function(v) {
    const pts = rows.map(function(r, i) {
      const angle = (-90 + i * 360 / rows.length) * Math.PI / 180;
      const rr = maxR * (v / 100);
      return [Math.round(cx + Math.cos(angle) * rr), Math.round(cy + Math.sin(angle) * rr)].join(",");
    }).join(" ");
    return '<polygon points="' + pts + '" fill="none" stroke="rgba(255,255,255,.10)" stroke-width="1" />';
  }).join("");

  const axis = rows.map(function(r, i) {
    const angle = (-90 + i * 360 / rows.length) * Math.PI / 180;
    const x = Math.round(cx + Math.cos(angle) * maxR);
    const y = Math.round(cy + Math.sin(angle) * maxR);
    return '<line x1="90" y1="90" x2="' + x + '" y2="' + y + '" stroke="rgba(255,255,255,.08)" />';
  }).join("");

  return '<div class="statbox"><div class="playbox-title">📊 AI 模型雷達</div>' +
    '<div class="radar-wrap">' +
      '<svg class="radar-svg" viewBox="0 0 180 180">' + grid + axis +
        '<polygon points="' + points + '" fill="rgba(0,255,156,.22)" stroke="#00ff9c" stroke-width="2" />' +
        '<circle cx="90" cy="90" r="3" fill="#4aa3ff" />' +
      '</svg>' +
      '<div>' + rows.map(function(r) {
        return '<div class="radar-row">' +
          '<div class="radar-label">' + r[0] + '</div>' +
          '<div class="radar-track"><div class="radar-fill" style="width:' + r[1] + '%"></div></div>' +
          '<div class="radar-num">' + r[1] + '</div>' +
        '</div>';
      }).join("") + '</div>' +
    '</div>' +
  '</div>';
}

function renderSignals(data) {
  if (!data.decisionSignals || data.decisionSignals.length === 0) return "";
  return '<div class="statbox"><div class="playbox-title">🧠 AI 信號</div>' +
    data.decisionSignals.map(function(s) {
      return '<div class="playitem">' + s.name + '｜' + s.level + '</div>';
    }).join("") +
  '</div>';
}

function renderExternalIntel(data) {
  const notes = data.externalIntel || [];
  if (!notes.length) return "";
  return '<div class="playbox">' +
    '<div class="playbox-title">🌐 外部公開資料補強</div>' +
    notes.slice(0, 4).map(function(x) {
      return '<div class="playitem">' + x + '</div>';
    }).join("") +
    '<div class="small">來源為公開列表頁摘要，只作模型補強，不直接複製完整文章。</div>' +
  '</div>';
}

function renderH2H(data) {
  if (!data.h2h || data.h2h.total === 0) {
    return '<div class="statbox"><div class="playbox-title">🤝 歷史交手</div><div class="playitem">API暫無完整歷史交手資料</div></div>';
  }

  const rows = data.h2h.recent.map(function(x) {
    const homeFlag = flagImg(data.home === x.home ? data.homeFlag : data.away === x.home ? data.awayFlag : "");
    const awayFlag = flagImg(data.home === x.away ? data.homeFlag : data.away === x.away ? data.awayFlag : "");
    return '<div class="h2h-row">' +
      '<div class="h2h-year">' + (x.year || "歷史") + '</div>' +
      '<div>' + homeFlag + x.home + '<span class="h2h-score">' + x.score + '</span>' + awayFlag + x.away +
        '<div class="small">勝方：' + x.winner + '｜' + (x.note || "API資料庫") + '</div>' +
      '</div>' +
    '</div>';
  }).join("");

  return '<div class="statbox">' +
    '<div class="playbox-title">🤝 ' + data.h2h.title + '</div>' +
    '<div class="small">資料來源：' + data.h2h.source + '</div>' +
    '<div class="playitem">' + data.home + '：' + data.h2h.homeWins + '勝｜' + data.away + '：' + data.h2h.awayWins + '勝｜平手：' + data.h2h.draws + '</div>' +
    '<div class="playitem">總進球：' + data.h2h.totalGoals + '｜場均：' + data.h2h.avgGoals + '</div>' +
    rows +
  '</div>';
}

function renderFormDots(form) {
  const recent = form?.recentResults || [];
  if (!recent.length) return '<div class="small">近期賽果資料不足</div>';
  return '<div class="form-dots">' + recent.map(function(x) {
    return '<span class="form-dot form-' + x.result + '" title="' + x.score + ' vs ' + x.opponent + '">' + x.result + '</span>';
  }).join("") + '</div>';
}

function renderMomentum(data) {
  return '<div class="playbox">' +
    '<div class="playbox-title">📈 球隊走勢</div>' +
    '<div class="squad-grid">' +
      '<div class="form-card"><div class="playitem">' + data.home + '｜' + (data.homeMomentum || '📊 狀態普通') + '</div>' + renderFormDots(data.homeForm) + '</div>' +
      '<div class="form-card"><div class="playitem">' + data.away + '｜' + (data.awayMomentum || '📊 狀態普通') + '</div>' + renderFormDots(data.awayForm) + '</div>' +
    '</div>' +
  '</div>';
}

function decimalOddFromRate(rate) {
  const safe = Math.max(8, Math.min(88, Number(rate) || 50));
  return (100 / safe * 0.92).toFixed(2);
}

function renderOdds(data) {
  if (!data.odds) {
    const draw = Math.max(9, Math.round(100 - Math.max(data.homeRate, data.awayRate) - 8));
    return '<div class="statbox"><div class="playbox-title">💰 AI 模擬賠率 / 推薦方向</div>' +
      '<div class="small">目前市場資料暫無，以下整合勝率、進球模型與公開資料補強，只作賽前觀察。</div>' +
      renderRecommendationPanel(data) +
      '<div class="odds-grid">' +
        '<div class="odd-card"><b>主勝</b><span>' + decimalOddFromRate(data.homeRate) + '</span></div>' +
        '<div class="odd-card"><b>和局</b><span>' + decimalOddFromRate(draw) + '</span></div>' +
        '<div class="odd-card"><b>客勝</b><span>' + decimalOddFromRate(data.awayRate) + '</span></div>' +
      '</div>' +
    '</div>';
  }

  return '<div class="statbox"><div class="playbox-title">💰 市場賠率 / 推薦方向</div>' +
    '<div class="playitem">莊家：' + (data.odds.bookmaker || '市場平均') + '</div>' +
    renderRecommendationPanel(data) +
    '<div class="odds-grid">' +
      '<div class="odd-card"><b>主勝</b><span>' + (data.odds.homeOdd || '-') + '</span></div>' +
      '<div class="odd-card"><b>和局</b><span>' + (data.odds.drawOdd || '-') + '</span></div>' +
      '<div class="odd-card"><b>客勝</b><span>' + (data.odds.awayOdd || '-') + '</span></div>' +
    '</div>' +
    '<div class="playitem">大小球2.5：大 ' + (data.odds.over25Odd || '-') + '｜小 ' + (data.odds.under25Odd || '-') + '</div>' +
    '<div class="playitem">BTTS：Yes ' + (data.odds.bttsYesOdd || '-') + '｜No ' + (data.odds.bttsNoOdd || '-') + '</div>' +
  '</div>';
}

function renderSquad(data) {
  const homePlayers = data.homeSquad || [];
  const awayPlayers = data.awaySquad || [];

  function playerRows(players) {
    if (!players.length) return '<div class="playitem">暫無球員資料</div>';
    return players.map(function(p) {
      return '<div class="player-row">' +
        (p.photo ? '<img src="' + p.photo + '" />' : "") +
        '<span>' + (p.number ? '<b>' + p.number + '</b> ' : '') + p.name + (p.club ? '<small class="club-name">｜' + p.club + '</small>' : '') + '</span><em>' + (p.position || "") + '</em>' +
      '</div>';
    }).join("");
  }

  return '<div class="statbox"><div class="playbox-title">👥 球員資料</div>' +
    '<div class="squad-grid">' +
      '<div><div class="small">' + data.home + '</div>' + playerRows(homePlayers) + '</div>' +
      '<div><div class="small">' + data.away + '</div>' + playerRows(awayPlayers) + '</div>' +
    '</div>' +
  '</div>';
}

function renderInjuriesAndLineups(data) {
  const injuries = data.injuries || [];
  const lineups = data.lineups || [];
  const lineupText = lineups.length ? lineups.map(function(item) {
    return item.team + (item.formation ? " " + item.formation : "") + (item.avgAge ? "｜均齡 " + item.avgAge : "") + (item.starters ? "｜首發 " + item.starters + " 人" : "");
  }).join("<br>") : "賽前公布後自動更新";

  return '<div class="statbox">' +
    '<div class="playbox-title">🏥 傷病 / 先發資訊</div>' +
    '<div class="playitem">傷病資料：' + (injuries.length ? injuries.length + " 筆" : "暫無公開傷病") + '</div>' +
    '<div class="playitem">先發名單：' + lineupText + '</div>' +
  '</div>';
}

function renderDetailBlock(title, content, open) {
  return '<div class="detail-block ' + (open ? 'open' : '') + '">' +
    '<button class="detail-toggle" onclick="toggleDetail(this)">' + title + (open ? ' ▲' : ' ▼') + '</button>' +
    '<div class="detail-content">' + content + '</div>' +
  '</div>';
}

function toggleDetail(btn) {
  const block = btn.parentElement;
  block.classList.toggle('open');
  btn.innerText = btn.innerText.includes('▲') ? btn.innerText.replace('▲', '▼') : btn.innerText.replace('▼', '▲');
}

async function analyze(fixtureId) {
  fixtureId = fixtureId || "";
  const home = document.getElementById("home").value.trim();
  const away = document.getElementById("away").value.trim();

  if (!home || !away) {
    alert("請輸入兩隊名稱");
    return;
  }

  const resultBox = document.getElementById("result");
  resultBox.innerHTML = '<div class="card">AI分析中...<br><span class="small">正在整理球隊資料、H2H、近15場與模型數據。</span></div>';

  try {
    let url = '/api/analyze?home=' + encodeURIComponent(home) + '&away=' + encodeURIComponent(away);
    if (fixtureId) url += '&fixture=' + encodeURIComponent(fixtureId);

    const res = await fetch(url, { cache: "no-store", mode: "cors" });
    const text = await res.text();

    let data;
    try {
    data = JSON.parse(text);
    } catch (jsonErr) {
    console.error("Raw response:", text);
    throw new Error("後端回傳不是JSON，請重新整理後再試。");
    }

    if (!res.ok || data.error) {
      throw new Error(data.error || ("HTTP " + res.status));
    }

    resultBox.innerHTML =
      '<div class="card">' +
        '<div class="match">' + flagImg(data.homeFlag) + data.home + ' VS ' + flagImg(data.awayFlag) + data.away + '</div>' +

        '<div class="rates">' +
          '<div><div class="rate green">' + data.homeRate + '%</div><div>' + data.home + '</div></div>' +
          '<div><div class="rate blue">' + data.awayRate + '%</div><div>' + data.away + '</div></div>' +
        '</div>' +

        '<div class="bar">' +
          '<div class="barHome" style="width:' + data.homeRate + '%"></div>' +
          '<div class="barAway" style="width:' + data.awayRate + '%"></div>' +
        '</div>' +

        '<div class="recommend">' + data.recommendation + '</div>' +
        renderTags(data) +

        '<div class="scorePredict">AI預測比分：' + data.predictedScore + '</div>' +
        '<div class="riskBox">🚨 ' + data.dangerLevel + ' RISK</div>' +

        renderModelCards(data) +

        '<div style="font-size:28px; margin-top:12px; color:gold; letter-spacing:4px;">' + data.stars + '</div>' +

        '<div class="playbox">' +
          '<div class="playbox-title">🧠 進階短評</div>' +
          '<div class="article">' + data.reason + '</div>' +
        '</div>' +

        renderExternalIntel(data) +

        '<p class="small">模型信心分數：' + data.modelScore + '%｜模型方向：' + data.predictedWinner + '</p>' +

        '<div class="playbox">' +
          '<div class="playbox-title">📌 AI 觀察方向</div>' +
          '<div class="playitem">' + data.playSuggestions.main + '</div>' +
          '<div class="playitem">' + data.playSuggestions.goals + '</div>' +
          '<div class="playitem">' + data.playSuggestions.upset + '</div>' +
          '<div class="playitem">' + data.playSuggestions.market + '</div>' +
          '<div class="small">' + data.playSuggestions.note + '</div>' +
        '</div>' +

        renderDetailBlock("📊 展開詳細分析", 
          renderSignals(data) +
          renderRadar(data) +
          renderH2H(data) +
          renderMomentum(data) +
          renderOdds(data) +
          '<p class="small">' + data.home + ' 近15場：' + data.homeForm.wins + '勝 ' + data.homeForm.draws + '平 ' + data.homeForm.losses + '敗，進 ' + data.homeForm.goalsFor + ' 球 / 失 ' + data.homeForm.goalsAgainst + ' 球</p>' +
          '<p class="small">' + data.away + ' 近15場：' + data.awayForm.wins + '勝 ' + data.awayForm.draws + '平 ' + data.awayForm.losses + '敗，進 ' + data.awayForm.goalsFor + ' 球 / 失 ' + data.awayForm.goalsAgainst + ' 球</p>',
          true
        ) +

        renderDetailBlock("👥 展開球員 / 傷病先發", renderSquad(data) + renderInjuriesAndLineups(data), false) +
      '</div>';

  } catch (err) {
    resultBox.innerHTML =
      '<div class="card">' +
        '<div class="playbox-title">⚠️ 分析失敗</div>' +
        '<div class="playitem">' + err.message + '</div>' +
        '<div class="small">請先確認 Render 環境變數 API_FOOTBALL_KEY 是否存在，或重新整理後再試。</div>' +
      '</div>';
    console.error("Analyze error:", err);
  }
}

window.addEventListener('error', function(e) {
  const box = document.getElementById("result");
  if (box && box.innerHTML.includes("AI分析中")) {
    box.innerHTML = '<div class="card"><div class="playbox-title">⚠️ 前端顯示錯誤</div><div class="playitem">' + e.message + '</div><div class="small">已捕捉到畫面渲染錯誤，通常是某個 API 欄位為空。請換用最新修正版。</div></div>';
  }
});

loadScheduleCenter();
loadGroupStandings();
loadRecommended();

const worldCupDate = new Date("2026-06-11T00:00:00");

function updateCountdown() {
  const now = new Date();
  const diff = worldCupDate - now;
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  document.getElementById("countdown").innerText =
    days >= 0 ? "距離 2026 世界盃開幕還有 " + days + " 天" : "2026 世界盃小組賽進行中";
}

updateCountdown();


document.addEventListener("contextmenu", function(e) {
  e.preventDefault();
});

document.addEventListener("keydown", function(e) {
  if (e.key === "F12") e.preventDefault();
  if (e.ctrlKey && e.shiftKey && e.key === "I") e.preventDefault();
  if (e.ctrlKey && e.shiftKey && e.key === "J") e.preventDefault();
  if (e.ctrlKey && e.key === "u") e.preventDefault();
});
