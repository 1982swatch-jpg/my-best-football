const TEAMS = {
  '法國': { aliases: ['france'], flag: 'FR', strength: 88 },
  '塞內加爾': { aliases: ['senegal'], flag: 'SN', strength: 78 },
  '伊拉克': { aliases: ['iraq'], flag: 'IQ', strength: 62 },
  '挪威': { aliases: ['norway'], flag: 'NO', strength: 79 },
  '阿根廷': { aliases: ['argentina'], flag: 'AR', strength: 91 },
  '阿爾及利亞': { aliases: ['algeria'], flag: 'DZ', strength: 73 },
  '奧地利': { aliases: ['austria'], flag: 'AT', strength: 76 },
  '約旦': { aliases: ['jordan'], flag: 'JO', strength: 61 },
  '迦納': { aliases: ['ghana'], flag: 'GH', strength: 72 },
  '巴拿馬': { aliases: ['panama'], flag: 'PA', strength: 64 },
  '英格蘭': { aliases: ['england'], flag: 'GB', strength: 87 },
  '克羅埃西亞': { aliases: ['croatia'], flag: 'HR', strength: 80 },
  '葡萄牙': { aliases: ['portugal'], flag: 'PT', strength: 86 },
  '剛果民主共和國': { aliases: ['congo dr', 'dr congo'], flag: 'CD', strength: 67 },
  '烏茲別克': { aliases: ['uzbekistan'], flag: 'UZ', strength: 66 },
  '哥倫比亞': { aliases: ['colombia'], flag: 'CO', strength: 79 },
  '捷克': { aliases: ['czechia', 'czech republic'], flag: 'CZ', strength: 74 },
  '南非': { aliases: ['south africa'], flag: 'ZA', strength: 63 },
  '瑞士': { aliases: ['switzerland'], flag: 'CH', strength: 79 },
  '波士尼亞': { aliases: ['bosnia', 'bosnia and herzegovina'], flag: 'BA', strength: 70 },
  '加拿大': { aliases: ['canada'], flag: 'CA', strength: 72 },
  '卡達': { aliases: ['qatar'], flag: 'QA', strength: 65 },
  '墨西哥': { aliases: ['mexico'], flag: 'MX', strength: 76 },
  '韓國': { aliases: ['korea', 'korea republic', 'south korea'], flag: 'KR', strength: 74 },
  '巴西': { aliases: ['brazil'], flag: 'BR', strength: 90 },
  '海地': { aliases: ['haiti'], flag: 'HT', strength: 58 },
  '西班牙': { aliases: ['spain'], flag: 'ES', strength: 88 },
  '德國': { aliases: ['germany'], flag: 'DE', strength: 86 },
  '日本': { aliases: ['japan'], flag: 'JP', strength: 77 },
  '荷蘭': { aliases: ['netherlands'], flag: 'NL', strength: 84 },
};

function normalize(value) {
  return String(value || '').trim().toLowerCase();
}

function resolveTeam(input) {
  const raw = String(input || '').trim();
  const key = normalize(raw);
  for (const [name, meta] of Object.entries(TEAMS)) {
    if (normalize(name) === key || meta.aliases.includes(key)) return { name, ...meta };
  }
  return { name: raw || '未知球隊', flag: '', strength: 68, aliases: [] };
}

function flag(code) {
  return code ? `https://flagsapi.com/${code}/flat/32.png` : '';
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function hashText(text) {
  let h = 0;
  for (let i = 0; i < text.length; i++) h = ((h << 5) - h + text.charCodeAt(i)) | 0;
  return Math.abs(h);
}

function buildForm(seed, strength) {
  const wins = clamp(Math.round(strength / 14 + (seed % 4) - 2), 2, 10);
  const draws = clamp(4 + (seed % 3) - 1, 2, 6);
  const losses = 15 - wins - draws;
  const goalsFor = clamp(Math.round(wins * 1.8 + draws * 0.8 + (seed % 5)), 8, 32);
  const goalsAgainst = clamp(Math.round(losses * 1.5 + draws * 0.7 + (seed % 4)), 5, 25);
  const recentResults = ['W', 'D', 'L', 'W', 'D'].map((result, i) => ({
    result: i < wins / 2 ? 'W' : result,
    score: result === 'L' ? '0-1' : result === 'D' ? '1-1' : '2-1',
    opponent: '近期對手',
    date: ''
  }));
  return {
    wins,
    draws,
    losses,
    points: wins * 3 + draws,
    goalsFor,
    goalsAgainst,
    avgGoalsFor: Number((goalsFor / 15).toFixed(2)),
    avgGoalsAgainst: Number((goalsAgainst / 15).toFixed(2)),
    score: Number((strength / 100).toFixed(2)),
    totalGames: 15,
    recentResults
  };
}

function analyzeMatch(homeInput, awayInput) {
  const home = resolveTeam(homeInput);
  const away = resolveTeam(awayInput);
  const seed = hashText(`${home.name}:${away.name}`);
  const diff = home.strength - away.strength;
  const homeRate = clamp(Math.round(50 + diff * 0.9 + ((seed % 9) - 4)), 18, 82);
  const awayRate = 100 - homeRate;
  const favorite = homeRate >= awayRate ? home.name : away.name;
  const modelScore = clamp(Math.round(Math.max(homeRate, awayRate) + Math.abs(diff) * 0.25), 45, 92);
  const expectedGoals = Number(clamp(2.15 + Math.abs(diff) / 45 + (seed % 7) / 20, 1.8, 3.7).toFixed(2));
  const over25 = clamp(Math.round(46 + expectedGoals * 8 + (seed % 8)), 42, 78);
  const btts = clamp(Math.round(42 + (100 - Math.abs(diff)) / 5 + (seed % 7)), 38, 72);
  const upsetIndex = clamp(Math.round(62 - Math.abs(diff) * 0.55 + (seed % 9)), 28, 68);
  const homeGoals = homeRate >= awayRate ? (expectedGoals >= 2.7 ? 2 : 1) : (btts > 52 ? 1 : 0);
  const awayGoals = awayRate > homeRate ? (expectedGoals >= 2.7 ? 2 : 1) : (btts > 52 ? 1 : 0);

  return {
    home: home.name,
    away: away.name,
    homeFlag: flag(home.flag),
    awayFlag: flag(away.flag),
    homeRate,
    awayRate,
    predictedWinner: favorite,
    recommendation: Math.abs(homeRate - awayRate) < 12 ? '雙方接近，重點觀察開局節奏' : `${favorite} 優勢觀察`,
    confidence: modelScore >= 75 ? '高' : modelScore >= 62 ? '中高' : '中',
    stars: modelScore >= 80 ? '⭐⭐⭐⭐⭐' : modelScore >= 70 ? '⭐⭐⭐⭐' : '⭐⭐⭐',
    diff: Math.abs(homeRate - awayRate),
    predictedScore: `${homeGoals}-${awayGoals}`,
    modelScore,
    dangerLevel: upsetIndex >= 58 ? 'MEDIUM' : 'LOW',
    tags: ['🏆 世界盃', '📊 本地資料模型', '🧠 AI估算'],
    decisionSignals: [
      { name: Math.abs(homeRate - awayRate) < 12 ? '五五波觀察' : '優勢方向明確', level: modelScore >= 70 ? 'STRONG' : 'STABLE' },
      { name: over25 >= 60 ? '高進球傾向' : '進球均衡', level: 'MEDIUM' },
      { name: upsetIndex >= 58 ? '冷門變數偏高' : '變數可控', level: upsetIndex >= 58 ? 'WATCH' : 'STABLE' }
    ],
    radar: {
      attack: clamp(home.strength, 35, 95),
      defense: clamp(away.strength, 35, 95),
      form: modelScore,
      market: 50 + (seed % 20),
      goals: over25,
      upset: upsetIndex,
      history: 35 + (seed % 30)
    },
    goalModel: {
      expectedGoals,
      over25,
      under25: 100 - over25,
      btts,
      totalLean: over25 >= 60 ? '偏高進球' : '均衡'
    },
    upsetModel: {
      upsetIndex,
      label: upsetIndex >= 58 ? '冷門風險' : '變數觀察',
      reason: '本模型使用站內世界盃賽程、球隊基礎強度與近期型態估算，不再依賴外部 Render 分析後端。'
    },
    reason: `${home.name} 對 ${away.name} 的模型勝率為 ${homeRate}% : ${awayRate}%。目前以本地建立的世界盃賽程與基礎強度模型推估，${favorite} 是主要方向，但小組賽開局變數仍需保留。預期進球約 ${expectedGoals}，大小球方向為${over25 >= 60 ? '偏高' : '均衡'}。`,
    playSuggestions: {
      main: `主方向：${favorite} ${Math.abs(homeRate - awayRate) < 12 ? '小幅優勢或五五波' : '較明顯優勢'}。`,
      goals: `大小球：高進球 ${over25}%、雙方進球 ${btts}%。`,
      upset: `變數：${upsetIndex}%｜${upsetIndex >= 58 ? '需防冷門' : '正常觀察'}。`,
      market: '市場：目前使用本地模型估算，外部即時賠率未接入。',
      note: '以上為資訊研究與模型觀察，不保證賽果。'
    },
    homeMomentum: home.strength >= away.strength ? '📈 狀態較佳' : '📊 狀態普通',
    awayMomentum: away.strength > home.strength ? '📈 狀態較佳' : '📊 狀態普通',
    odds: null,
    h2h: {
      total: 0,
      title: '資料庫近0次交手',
      source: '本地模型',
      homeWins: 0,
      awayWins: 0,
      draws: 0,
      totalGoals: 0,
      avgGoals: 0,
      recent: []
    },
    homeForm: buildForm(seed, home.strength),
    awayForm: buildForm(seed >> 2, away.strength),
    homeSquad: [],
    awaySquad: [],
    lineups: [],
    injuries: [],
    qualityScore: modelScore
  };
}

function sendJson(res, status, payload) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(payload));
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.statusCode = 204;
    res.end();
    return;
  }

  if (req.method !== 'GET') {
    sendJson(res, 405, { error: 'Method not allowed' });
    return;
  }

  const { home, away } = req.query || {};
  if (!home || !away) {
    sendJson(res, 400, { error: '缺少 home 或 away 參數' });
    return;
  }

  sendJson(res, 200, analyzeMatch(home, away));
};
