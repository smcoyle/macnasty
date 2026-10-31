import base64
import json
import os

rsrc_path = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\extracted\MacNasty_.rsrc"
chars_json_path = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\reference\macnasty\chars_db.json"
out_html_path = r"C:\Users\scoyl\Dropbox\HOBBY_CODE\wrms\macnasty.html"

with open(rsrc_path, "rb") as f:
    rsrc_b64 = base64.b64encode(f.read()).decode("ascii")

with open(chars_json_path, "r", encoding="utf-8") as f:
    chars_json_str = f.read()

html_template = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MacNasty (1987, System 6 Macintosh) — Native Resource Fork Port</title>
<style>
  :root {
    --bg: #1a1b1e;
    --panel: #25262b;
    --accent: #f59f00;
    --text: #e9ecef;
    --muted: #adb5bd;
  }
  * { box-sizing: border-box; user-select: none; -webkit-user-select: none; }
  body {
    margin: 0;
    padding: 16px;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100vh;
  }
  .header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 1024px;
    max-width: 100%;
    margin-bottom: 10px;
    padding: 8px 14px;
    background: var(--panel);
    border-radius: 8px;
    border: 1px solid #373a40;
  }
  .header-bar h1 {
    font-size: 16px;
    margin: 0;
    font-weight: 600;
    letter-spacing: 0.3px;
  }
  .header-controls {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  button.ui-btn {
    background: #373a40;
    color: #fff;
    border: 1px solid #5c5f66;
    border-radius: 5px;
    padding: 5px 10px;
    font-size: 12px;
    cursor: pointer;
  }
  button.ui-btn:hover { background: #495057; }
  .mac-bezel {
    background: #d8d4c8;
    padding: 18px 22px 24px 22px;
    border-radius: 16px;
    box-shadow: 0 18px 50px rgba(0,0,0,0.65), inset 0 2px 3px rgba(255,255,255,0.7);
    border: 2px solid #aba698;
  }
  .crt-frame {
    background: #000;
    padding: 4px;
    border-radius: 8px;
    box-shadow: inset 0 0 8px rgba(0,0,0,0.9);
  }
  canvas#macScreen {
    display: block;
    width: 1024px;
    height: 684px;
    image-rendering: pixelated;
    image-rendering: crisp-edges;
    cursor: default;
    background: #fff;
  }
  .status-strip {
    width: 1024px;
    max-width: 100%;
    margin-top: 10px;
    padding: 8px 14px;
    background: var(--panel);
    border-radius: 8px;
    border: 1px solid #373a40;
    font-size: 13px;
    display: flex;
    justify-content: space-between;
    color: var(--muted);
  }
  .status-strip b { color: var(--text); }
  #dossierDrawer {
    display: none;
    width: 1024px;
    max-width: 100%;
    margin-top: 12px;
    padding: 14px;
    background: var(--panel);
    border-radius: 8px;
    border: 1px solid #373a40;
    max-height: 360px;
    overflow-y: auto;
    font-size: 12px;
  }
  table.dossier-table {
    width: 100%;
    border-collapse: collapse;
  }
  table.dossier-table th, table.dossier-table td {
    border-bottom: 1px solid #373a40;
    padding: 5px 6px;
    text-align: left;
  }
  table.dossier-table th { color: var(--accent); position: sticky; top: 0; background: var(--panel); }
  .lover-tag { color: #ff6b6b; font-weight: bold; }
</style>
</head>
<body>

<div class="header-bar">
  <h1> MacNasty (1987, Version 1.00 by George Lott) — Classic Macintosh System 6</h1>
  <div class="header-controls">
    <button class="ui-btn" onclick="resetGame()">New Game</button>
    <button class="ui-btn" onclick="toggleDossier()">Toggle Detective Cheat Sheet</button>
    <button class="ui-btn" onclick="toggleScale()">1x / 2x Size</button>
  </div>
</div>

<div class="mac-bezel">
  <div class="crt-frame">
    <canvas id="macScreen" width="512" height="342"></canvas>
  </div>
</div>

<div class="status-strip">
  <span id="statusLeft">Location: <b>Tumbleweed, Texas</b> | Selected: <b>Max MacNasty</b></span>
  <span id="statusRight">Cash: <b>$150,000</b> | Worth: <b>$150,000</b> | Debt: <b>$0</b> | Prestige: <b>0</b> | Age: <b>30</b></span>
</div>

<div id="dossierDrawer">
  <h3 style="margin-top:0;">Complete Tumbleweed Detective Dossier (All 44 Characters & Secret Lovers)</h3>
  <table class="dossier-table" id="dossierTable">
    <thead>
      <tr>
        <th>ID</th><th>Name</th><th>Spouse</th><th>Building</th><th>Reputation</th><th>Rumor</th><th>Detective Secret / Lover</th><th>Weaknesses</th><th>Your Clout</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>
</div>

<script>
const RSRC_B64 = "__RSRC_B64__";
const CHARS_DB = __CHARS_JSON__;

// Decode binary resource fork
function b64ToBytes(b64) {
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return arr;
}

const RSRC_BYTES = b64ToBytes(RSRC_B64);
const RSRC = { ICON: {}, DLOG: {}, DITL: {}, MENU: {}, WIND: {}, CNTL: {}, ICN_LIST: {} };

function readU16(buf, off) { return (buf[off] << 8) | buf[off+1]; }
function readI16(buf, off) { const v = readU16(buf, off); return v >= 0x8000 ? v - 0x10000 : v; }
function readU32(buf, off) { return ((buf[off] << 24) | (buf[off+1] << 16) | (buf[off+2] << 8) | buf[off+3]) >>> 0; }
function readMacStr(buf, off, len) {
  let s = "";
  for (let i = 0; i < len; i++) {
    const c = buf[off + i];
    s += String.fromCharCode(c === 0xD5 ? 0x27 : c);
  }
  return s;
}

function parseResourceFork(bytes) {
  const dataOff = readU32(bytes, 0);
  const mapOff = readU32(bytes, 4);
  const typeListOff = mapOff + readU16(bytes, mapOff + 24);
  const nameListOff = mapOff + readU16(bytes, mapOff + 26);
  const numTypes = (readU16(bytes, mapOff + 28) + 1) & 0xFFFF;

  for (let i = 0; i < numTypes; i++) {
    const toff = typeListOff + 2 + i * 8;
    const rtype = readMacStr(bytes, toff, 4);
    const rcount = readU16(bytes, toff + 4) + 1;
    const refListOff = typeListOff + readU16(bytes, toff + 6);
    for (let j = 0; j < rcount; j++) {
      const roff = refListOff + j * 12;
      const rid = readI16(bytes, roff);
      const rdoff = ((bytes[roff+5] << 16) | (bytes[roff+6] << 8) | bytes[roff+7]) >>> 0;
      const absOff = dataOff + rdoff;
      const rlen = readU32(bytes, absOff);
      const rdata = bytes.subarray(absOff + 4, absOff + 4 + rlen);
      if (rtype === "ICON") RSRC.ICON[rid] = rdata;
      else if (rtype === "ICN#") RSRC.ICN_LIST[rid] = rdata;
      else if (rtype === "DLOG") RSRC.DLOG[rid] = parseDLOG(rid, rdata);
      else if (rtype === "DITL") RSRC.DITL[rid] = parseDITL(rid, rdata);
      else if (rtype === "MENU") RSRC.MENU[rid] = rdata;
      else if (rtype === "WIND") RSRC.WIND[rid] = rdata;
      else if (rtype === "CNTL") RSRC.CNTL[rid] = rdata;
    }
  }
}

function parseDLOG(id, data) {
  const t = readI16(data, 0), l = readI16(data, 2), b = readI16(data, 4), r = readI16(data, 6);
  const procId = readI16(data, 8);
  const itemsId = readI16(data, 18);
  const titleLen = data[20];
  const title = readMacStr(data, 21, titleLen);
  return { id, rect: { l, t, r, b, w: r - l, h: b - t }, procId, itemsId, title };
}

function parseDITL(id, data) {
  const count = readU16(data, 0) + 1;
  let pos = 2;
  const items = [];
  for (let i = 1; i <= count; i++) {
    const t = readI16(data, pos + 4), l = readI16(data, pos + 6), b = readI16(data, pos + 8), r = readI16(data, pos + 10);
    const itype = data[pos + 12], ilen = data[pos + 13];
    pos += 14;
    const idata = data.subarray(pos, pos + ilen);
    pos += ilen;
    if (pos % 2 === 1) pos++;
    const kind = itype & 0x7F;
    const enabled = (itype & 0x80) === 0;
    let val = null;
    if (kind === 4 || kind === 5 || kind === 6 || kind === 8 || kind === 16) {
      val = readMacStr(idata, 0, idata.length);
    } else if ((kind === 32 || kind === 7) && idata.length >= 2) {
      val = readI16(idata, 0);
    }
    items.push({ index: i, rect: { l, t, r, b, w: r - l, h: b - t }, kind, enabled, val });
  }
  return items;
}

parseResourceFork(RSRC_BYTES);

// Building character radio mappings from CODE_14
const BUILDING_RADIOS = {
  7000: { name: "Widget Mfg.", map: { 1: 742, 2: 741, 3: 734, 4: 708, 5: 724 } },
  7001: { name: "Allen Building", map: { 1: 700, 2: 701, 3: 709, 4: 712, 5: 714, 6: 703, 7: 704, 8: 735, 9: 724 } },
  7002: { name: "Tumbleweed Bank", map: { 1: 724, 2: 702, 3: 705, 4: 706, 5: 733, 6: 736, 7: 721, 8: 723, 9: 729 } },
  7003: { name: "Court House", map: { 1: 724, 2: 711, 3: 740, 4: 715, 5: 722, 6: 718, 7: 732, 8: 730, 9: 737 } },
  7004: { name: "Butler Building", map: { 1: 724, 2: 710, 3: 728, 4: 731, 5: 726, 6: 738, 7: 720 } },
  7005: { name: "Country Club", map: { 1: 724, 2: 713, 3: 716, 4: 717, 5: 725, 6: 727, 7: 707, 8: 719, 9: 739, 10: 743 } }
};

// Menu bar definition from MENU 1..5
const MENUS = [
  { id: 1, title: "\uF8FF", x: 10, w: 24, items: [
    { name: "About MacNasty...", enabled: true, action: "about" },
    { name: "-", enabled: false },
    { name: "Shareware Notice...", enabled: true, action: "shareware" }
  ]},
  { id: 2, title: "Action", x: 42, w: 52, items: [
    { name: "Score", enabled: true, action: "score" },
    { name: "Next Person", enabled: false, action: "next_person" },
    { name: "Leave Building", enabled: false, action: "leave_building" },
    { name: "Pass", enabled: true, action: "pass" },
    { name: "Quit", enabled: true, action: "quit" }
  ]},
  { id: 3, title: "Property", x: 102, w: 64, items: [
    { name: "Buy", enabled: true, action: "buy" },
    { name: "Sell", enabled: true, action: "sell" },
    { name: "Borrow", enabled: true, action: "borrow" }
  ]},
  { id: 4, title: "Info", x: 174, w: 38, items: [
    { name: "Public Facts", enabled: false, action: "info_public" },
    { name: "Rumors", enabled: false, action: "info_rumors" },
    { name: "Private Detective", enabled: false, action: "info_detective" }
  ]},
  { id: 5, title: "Bribe", x: 220, w: 46, items: [
    { name: "Money", enabled: false, action: "bribe_money" },
    { name: "Favors", enabled: false, action: "bribe_favors" },
    { name: "Charm", enabled: false, action: "bribe_charm" },
    { name: "Seduce", enabled: false, action: "bribe_seduce" }
  ]},
  { id: 6, title: "Blackmail", x: 274, w: 72, items: [
    { name: "Threaten disclosure", enabled: false, action: "bm_threaten" },
    { name: "Start Rumors", enabled: false, action: "bm_rumors" },
    { name: "Spouse's Secrets", enabled: false, action: "bm_spouse" }
  ]}
];

const STOCK_NAMES = ["Widget Company", "Bank", "Allen Office Building", "Butler Office Building", "Newspaper", "Country Club"];
const STOCK_BASE_VAL = [12000, 12000, 1200, 1200, 1200, 1200];

let G = null;

function createInitialState() {
  const rel = {};
  const detectiveKnown = {};
  for (let cid = 700; cid <= 743; cid++) {
    rel[cid] = 0;
    detectiveKnown[cid] = false;
  }
  return {
    mode: "MESSAGE", // "MESSAGE", "STREET", "BUILDING", "MODAL", "ENDGAME"
    currentBuilding: null, // 7000..7005
    selectedRadio: 1,
    selectedChar: 724,
    age: 30,
    turnInYear: 0,
    player: {
      shares: [0, 0, 0, 0, 0, 0],
      cash: 150000,
      worth: 150000,
      debt: 0,
      prestige: 0
    },
    rival: {
      shares: [50, 50, 50, 0, 50, 50],
      cash: 400000,
      worth: 1780000,
      debt: 0,
      prestige: 500
    },
    marketShares: [950, 950, 950, 1000, 950, 950],
    buyOfferLots: [1, 10, 1, 10, 5, 10],
    rel,
    detectiveKnown,
    mistresses: [
      { active: false, cid: 0, arc: 300, stage: 0 },
      { active: false, cid: 0, arc: 301, stage: 0 },
      { active: false, cid: 0, arc: 302, stage: 0 }
    ],
    trustsOwned: [false, false, false, false],
    isMayor: false,
    boardsOwned: [false, false], // Bank, Widget
    messageLines: [
      { x: 145, y: 30, text: "Welcome to Tumbleweed, Texas." },
      { x: 40, y: 50, text: "You have just inherited $150,000 and an old oil property from" },
      { x: 40, y: 70, text: "your uncle Sawdust MacNasty who lived in Tumbleweed.  You have" },
      { x: 40, y: 90, text: "decided to move to Tumbleweed with your wife, the perpetually" },
      { x: 40, y: 110, text: "bored ex-debutante Mona and become one of the town's most" },
      { x: 40, y: 130, text: "powerful citizens.  You soon find that there has been a running" },
      { x: 40, y: 150, text: "feud between the MacNastys and the MacRascals for several gen-" },
      { x: 40, y: 170, text: "erations now and that Mac MacRascal, the town boss, wants to" },
      { x: 40, y: 190, text: "carry it on against you." },
      { x: 165, y: 245, text: "(Click anywhere to continue)" }
    ],
    afterMessageCallback: () => openModal(7008),
    modal: null, // { dlogId, selectedRadio, scrollVal, customText, onItem }
    openMenuIdx: -1,
    hoverMenuItem: -1,
    endgameAnimTick: 0,
    endgameWon: false
  };
}

function recalcWorth(who) {
  let stockVal = 0;
  for (let i = 0; i < 6; i++) stockVal += who.shares[i] * STOCK_BASE_VAL[i];
  who.worth = who.cash + stockVal - who.debt;
}

function getCatInfluence(catId) {
  let sum = 0;
  for (let cid = 700; cid <= 743; cid++) {
    const ch = CHARS_DB[cid];
    if (ch.cat === catId) {
      sum += G.rel[cid] * 2 + G.rel[ch.spouse_id];
    }
  }
  return sum;
}

function clampRel(cid, delta) {
  G.rel[cid] = Math.max(-20, Math.min(25, (G.rel[cid] || 0) + delta));
}

function updateMenus() {
  const inBldg = G.mode === "BUILDING";
  const inMapOrBldg = G.mode === "STREET" || G.mode === "BUILDING";
  MENUS[1].items[0].enabled = inMapOrBldg;
  MENUS[1].items[1].enabled = inBldg;
  MENUS[1].items[2].enabled = inBldg;
  MENUS[1].items[3].enabled = inMapOrBldg;
  MENUS[2].items.forEach(it => it.enabled = inMapOrBldg);
  MENUS[3].items.forEach(it => it.enabled = inBldg);
  MENUS[4].items.forEach(it => it.enabled = inBldg);
  MENUS[5].items.forEach(it => it.enabled = inBldg);
}

function showMessageLines(lines, nextCb = null) {
  const formatted = lines.map((txt, idx) => (typeof txt === "string" ? { x: 40, y: 45 + idx * 20, text: txt } : txt));
  formatted.push({ x: 165, y: 268, text: "(Click anywhere to continue)" });
  G.mode = "MESSAGE";
  G.messageLines = formatted;
  G.afterMessageCallback = nextCb || (() => {
    if (G.currentBuilding) {
      G.mode = "BUILDING";
    } else {
      G.mode = "STREET";
    }
    updateMenus();
  });
  updateMenus();
}

function openModal(dlogId, opts = {}) {
  G.prevMode = G.mode === "MODAL" ? G.prevMode : G.mode;
  G.mode = "MODAL";
  G.modal = {
    dlogId,
    selectedRadio: opts.selectedRadio || 3,
    selectedRadio2: opts.selectedRadio2 || 10,
    scrollVal: opts.scrollVal !== undefined ? opts.scrollVal : 1000,
    promptLines: opts.promptLines || [],
    onDone: opts.onDone || null
  };
  updateMenus();
}

function closeModal() {
  G.modal = null;
  G.mode = G.currentBuilding ? "BUILDING" : "STREET";
  updateMenus();
}

function rollBuyOffers() {
  const choices = [0, 1, 5, 10];
  for (let i = 0; i < 6; i++) {
    let pick = choices[Math.floor(Math.random() * choices.length)];
    if (pick > G.marketShares[i]) pick = G.marketShares[i] >= 10 ? 10 : (G.marketShares[i] >= 5 ? 5 : (G.marketShares[i] >= 1 ? 1 : 0));
    G.buyOfferLots[i] = pick;
  }
}

// Persuade dialog (DLOG 6003) after successful Bribe or Blackmail
function openPersuadeDialog(targetCid, bonusWeight = 1) {
  const ch = CHARS_DB[targetCid];
  openModal(6003, {
    selectedRadio: 2,
    onDone: (itemIdx) => {
      closeModal();
      // itemIdx: 2=Yourself, 3=Spouse, 4=Lover, 5=Boss, 6=Other
      if (itemIdx === 2) {
        clampRel(targetCid, 4 * bonusWeight);
        G.player.prestige += 5;
        showMessageLines([
          `${ch.name} agrees to support you personally!`,
          `Your influence with ${ch.name} has increased.`
        ], () => advanceTurn());
      } else if (itemIdx === 3) {
        const sp = CHARS_DB[ch.spouse_id];
        if (ch.has_affair && Math.random() < 0.55) {
          showMessageLines([
            `${ch.name} tried to talk to ${sp.name},`,
            `but since their marriage is rocky, it didn't help much.`
          ], () => advanceTurn());
        } else {
          clampRel(ch.spouse_id, 4 * bonusWeight);
          clampRel(targetCid, 2);
          G.player.prestige += 5;
          showMessageLines([
            `${ch.name} persuades spouse ${sp.name}`,
            `that you are a wonderful person to do business with!`
          ], () => advanceTurn());
        }
      } else if (itemIdx === 4) {
        if (ch.lover_id && CHARS_DB[ch.lover_id]) {
          const lv = CHARS_DB[ch.lover_id];
          clampRel(ch.lover_id, 5 * bonusWeight);
          clampRel(targetCid, 2);
          G.player.prestige += 8;
          showMessageLines([
            `${ch.name} whispers sweet words about you`,
            `to secret lover ${lv.name}!`,
            `Your influence with ${lv.name} increased substantially.`
          ], () => advanceTurn());
        } else if (ch.secret_id === 852) {
          // Irwin Idle or Inger Idle (numerous lovers)
          [729, 731, 738, 739].forEach(id => clampRel(id, 3));
          G.player.prestige += 8;
          showMessageLines([
            `${ch.name} puts in a good word for you`,
            `with numerous secret admirers around Tumbleweed!`
          ], () => advanceTurn());
        } else {
          showMessageLines([
            `${ch.name} says: "What lover?! I don't have a lover!"`,
            `Your attempt accomplished nothing.`
          ], () => advanceTurn());
        }
      } else if (itemIdx === 5) {
        // Boss of their building
        const bossMap = { 7000: 742, 7001: 704, 7002: 706, 7003: 718, 7004: 738, 7005: 713 };
        const bossId = bossMap[G.currentBuilding] || 706;
        const boss = CHARS_DB[bossId];
        clampRel(bossId, 4 * bonusWeight);
        clampRel(targetCid, 1);
        G.player.prestige += 5;
        showMessageLines([
          `${ch.name} puts in a glowing recommendation for you`,
          `with ${boss.name}!`
        ], () => advanceTurn());
      } else {
        G.player.prestige += 12 * bonusWeight;
        clampRel(targetCid, 2);
        showMessageLines([
          `${ch.name} spreads word of your generosity and clout`,
          `throughout Tumbleweed. You gain ${12 * bonusWeight} prestige points!`
        ], () => advanceTurn());
      }
    }
  });
}

// Menu Action Handler
function handleMenuAction(action) {
  const cid = G.selectedChar;
  const ch = CHARS_DB[cid];
  if (action === "about") {
    showMessageLines([
      "MacNasty — Version 1.00 (1987)",
      "Original 68000 Classic Macintosh Game by George Lott",
      "P.O. Box 13834, Arlington, TX 76013",
      "",
      "Reverse-engineered directly from SoftShoppe #5691",
      "StuffIt ('Arsenic') archive & HFS Resource Fork (MNTY)."
    ]);
  } else if (action === "shareware") {
    openModal(7008);
  } else if (action === "score") {
    recalcWorth(G.player);
    recalcWorth(G.rival);
    openModal(6002);
  } else if (action === "next_person") {
    if (!G.currentBuilding) return;
    const bmap = BUILDING_RADIOS[G.currentBuilding].map;
    const count = Object.keys(bmap).length;
    G.selectedRadio = (G.selectedRadio % count) + 1;
    G.selectedChar = bmap[G.selectedRadio];
  } else if (action === "leave_building") {
    G.currentBuilding = null;
    G.mode = "STREET";
    G.selectedChar = 724;
    updateMenus();
  } else if (action === "pass") {
    advanceTurn();
  } else if (action === "quit") {
    triggerEndgame();
  } else if (action === "buy") {
    rollBuyOffers();
    openModal(6000, { selectedRadio: 3 });
  } else if (action === "sell") {
    openModal(6001, { selectedRadio: 4, selectedRadio2: 10 });
  } else if (action === "borrow") {
    openModal(6010, { selectedRadio: 3 });
  } else if (action === "info_public") {
    showMessageLines(ch.public_lines.length ? ch.public_lines : [`${ch.name} is a citizen of Tumbleweed.`]);
  } else if (action === "info_rumors") {
    const rep = ch.rep_str ? `${ch.name}'s reputation is: ${ch.rep_str}.` : `${ch.name} has no special reputation.`;
    const rum = ch.rumor_str ? `The rumor around town is: ${ch.rumor_str}.` : `There are no rumors about ${ch.name}.`;
    showMessageLines([rep, rum]);
  } else if (action === "info_detective") {
    if (G.player.cash < 500) {
      showMessageLines(["The Private Detective requires $500 in cash up front."]);
      return;
    }
    G.player.cash -= 500;
    recalcWorth(G.player);
    G.detectiveKnown[cid] = true;
    const lines = [
      "The private detective takes your $500 and investigates",
      `${ch.name}...`
    ];
    if (ch.secret_id === 850 && ch.lover_name) {
      lines.push(`SECRET REPORT: ${ch.name}'s secret lover is ${ch.lover_name}!`);
    } else if (ch.secret_str) {
      lines.push(`SECRET REPORT: ${ch.name} ${ch.secret_str}`);
    } else {
      lines.push(`SECRET REPORT: ${ch.name} is squeaky clean. Nothing found.`);
    }
    showMessageLines(lines, () => advanceTurn());
  } else if (action === "bribe_money") {
    if (cid === 724) {
      showMessageLines(["Bribing yourself doesn't accomplish much, Max."]);
      return;
    }
    openModal("BRIBE_MONEY", { scrollVal: 2000 });
  } else if (action === "bribe_favors") {
    if (cid === 724) {
      showMessageLines(["You already owe yourself plenty of favors."]);
      return;
    }
    if (ch.vuln_favors) {
      showMessageLines([
        `${ch.name} gladly accepts your offer of a political favor!`,
        `"One hand washes the other, Max."`
      ], () => openPersuadeDialog(cid, 1));
    } else {
      clampRel(cid, -2);
      showMessageLines([
        `${ch.name} turns down your offer of favors coldly.`,
        `"I don't need anything from you, MacNasty."`
      ], () => advanceTurn());
    }
  } else if (action === "bribe_charm") {
    if (cid === 724) {
      showMessageLines(["You admire yourself in the mirror. Very charming!"]);
      return;
    }
    if (ch.vuln_charm) {
      showMessageLines([
        `You turn on the famous MacNasty Texas charm.`,
        `${ch.name} is completely flattered!`
      ], () => openPersuadeDialog(cid, 1));
    } else {
      clampRel(cid, -1);
      showMessageLines([
        `${ch.name} sees right through your flattery.`,
        `"Save the sweet talk for someone else, Max."`
      ], () => advanceTurn());
    }
  } else if (action === "bribe_seduce") {
    if (cid % 2 === 0) {
      showMessageLines(["No, no. We don't do that kind of thing around here."]);
      return;
    }
    if (cid === 725) {
      showMessageLines(["Forget it Max, you turn me off."]);
      return;
    }
    G.player.cash -= 300;
    recalcWorth(G.player);
    const seduceSuccess = ch.vuln_charm || ch.has_affair || cid === 719 || cid === 727 || cid === 733 || cid === 737 || Math.random() < 0.35;
    if (seduceSuccess) {
      let extraMsg = `You wine and dine ${ch.name} ($300) and seduce her!`;
      if (cid === 727) {
        G.player.prestige += 10;
        extraMsg = "You seduced MacRascal's wife Marta! (+10 Prestige bonus!)";
      }
      assignMistress(cid);
      showMessageLines([
        extraMsg,
        `${ch.name} is now one of your secret mistresses.`
      ], () => openPersuadeDialog(cid, 2));
    } else {
      clampRel(cid, -4);
      clampRel(ch.spouse_id, -4);
      G.player.prestige -= 5;
      showMessageLines([
        `${ch.name} slaps your face and rejects your advances!`,
        `You spent $300 and lost 5 prestige points.`
      ], () => advanceTurn());
    }
  } else if (action === "bm_threaten") {
    if (cid === 724) {
      showMessageLines(["Blackmailing yourself is a bold strategy, Max."]);
      return;
    }
    if (ch.vuln_blackmail && (G.detectiveKnown[cid] || ch.rumor_id === 801)) {
      showMessageLines([
        `You threaten to expose ${ch.name}'s secret (${ch.lover_name ? "affair with " + ch.lover_name : ch.secret_str})!`,
        `${ch.name} turns pale: "All right, Max! What do you want?"`
      ], () => openPersuadeDialog(cid, 2));
    } else if (ch.vuln_blackmail && !G.detectiveKnown[cid]) {
      showMessageLines([
        `You bluff ${ch.name}, but without concrete proof from`,
        `the Private Detective, ${ch.name} calls your bluff!`
      ], () => advanceTurn());
    } else {
      clampRel(cid, -5);
      G.player.prestige -= 5;
      showMessageLines([
        `${ch.name} laughs at your threats!`,
        `"Publish whatever you want, MacNasty!" (Lose 5 prestige)`
      ], () => advanceTurn());
    }
  } else if (action === "bm_rumors") {
    if (cid === 724) return;
    G.player.cash -= 200;
    recalcWorth(G.player);
    const repInf = getCatInfluence(453); // Reporters (Betty Baker 703, Kirk King 720)
    if (repInf >= 0 || Math.random() < 0.55) {
      clampRel(cid, 3);
      G.player.prestige += 5;
      showMessageLines([
        `You pay $200 to plant nasty rumors about ${ch.name}`,
        `in the Tumbleweed Newspaper!`,
        `${ch.name} begs you to call off the reporters.`
      ], () => openPersuadeDialog(cid, 1));
    } else {
      clampRel(cid, -4);
      showMessageLines([
        `You spend $200 trying to start rumors about ${ch.name},`,
        `but the reporters trace the story back to you!`
      ], () => advanceTurn());
    }
  } else if (action === "bm_spouse") {
    const sp = CHARS_DB[ch.spouse_id];
    if (ch.vuln_spouse_sec && (G.detectiveKnown[ch.spouse_id] || sp.secret_id !== 0)) {
      showMessageLines([
        `You threaten to reveal ${sp.name}'s dark secret`,
        `(${sp.secret_str})!`,
        `${ch.name} pleads with you to keep quiet and agrees to help!`
      ], () => openPersuadeDialog(cid, 2));
    } else {
      clampRel(cid, -3);
      showMessageLines([
        `${ch.name} doesn't care about your threats against ${sp.name}!`
      ], () => advanceTurn());
    }
  }
  updateDossierTable();
}

function assignMistress(cid) {
  for (let i = 0; i < 3; i++) {
    if (G.mistresses[i].active && G.mistresses[i].cid === cid) return;
  }
  for (let i = 0; i < 3; i++) {
    if (!G.mistresses[i].active) {
      G.mistresses[i] = { active: true, cid, arc: 300 + i, stage: 1 };
      return;
    }
  }
  // All 3 slots full: oldest mistress gets dumped and angry (CODE_12 / CODE_20)
  const dumped = G.mistresses[0];
  clampRel(dumped.cid, -10);
  G.mistresses[0] = G.mistresses[1];
  G.mistresses[1] = G.mistresses[2];
  G.mistresses[2] = { active: true, cid, arc: 302, stage: 1 };
}

// Annual settlement + Random Events from CODE_15..CODE_22
function advanceTurn() {
  G.turnInYear++;
  let eventLines = [];

  // Every 4 actions = 1 year (CODE_19)
  if (G.turnInYear >= 4) {
    G.turnInYear = 0;
    G.age += 1;
    // Dividends & Interest
    let div = 0;
    div += G.player.shares[0] * 1200; // Widget Co
    div += G.player.shares[1] * 1200; // Bank
    div += G.player.shares[2] * 150;  // Allen Bldg
    div += G.player.shares[3] * 150;  // Butler Bldg
    div += G.player.shares[4] * 150;  // Newspaper
    div += G.player.shares[5] * 150;  // Country Club
    for (let t = 0; t < 4; t++) if (G.trustsOwned[t]) div += 12000;
    if (G.boardsOwned[0]) div += 10000;
    if (G.boardsOwned[1]) div += 10000;
    if (G.isMayor) { div += 15000; G.player.prestige += 15; }

    const interest = Math.floor(G.player.debt * 0.10);
    G.player.cash += div - interest;
    G.player.prestige += Math.floor((G.player.shares[0] + G.player.shares[1]) * 0.5);

    // Rival AI (CODE_22)
    G.rival.cash += 65000;
    G.rival.prestige += 12;
    for (let si = 0; si < 6; si++) {
      if (G.marketShares[si] >= 5 && G.rival.cash >= STOCK_BASE_VAL[si] * 5 && Math.random() < 0.35) {
        G.rival.shares[si] += 5;
        G.marketShares[si] -= 5;
        G.rival.cash -= STOCK_BASE_VAL[si] * 5;
      }
    }
    recalcWorth(G.player);
    recalcWorth(G.rival);

    if (G.player.cash < -50000 || G.player.worth < -100000) {
      showMessageLines([
        "BANKRUPTCY!",
        "The Tumbleweed Bank has foreclosed on all your loans.",
        "You are broke and run out of town on a rail!",
        "Mac MacRascal laughs all the way to the bank."
      ], () => resetGame());
      return;
    }

    if (G.age >= 70) {
      triggerEndgame();
      return;
    }
  }

  // Check active mistress arc events (CODE_20)
  for (let i = 0; i < 3; i++) {
    const m = G.mistresses[i];
    if (m.active && Math.random() < 0.28) {
      const mch = CHARS_DB[m.cid];
      if (m.stage === 1) {
        m.stage = 2;
        G.player.cash -= 500;
        recalcWorth(G.player);
        showMessageLines([
          `Your mistress ${mch.name} demands a fancy fur coat`,
          `and jewelry to keep her happy. It costs you $500.`
        ]);
        return;
      } else if (m.stage === 2) {
        m.stage = 3;
        openModal(7007, {
          promptLines: [
            `Your mistress ${mch.name} threatens to tell your wife`,
            `Mona about your affair unless you give her $2,000!`,
            `Do you pay her the $2,000?`
          ],
          onDone: (yes) => {
            closeModal();
            if (yes) {
              G.player.cash -= 2000;
              recalcWorth(G.player);
              showMessageLines([`You pay ${mch.name} $2,000 to keep quiet.`]);
            } else {
              m.active = false;
              clampRel(m.cid, -8);
              G.player.prestige -= 15;
              showMessageLines([
                `${mch.name} tells your wife Mona everything!`,
                `Mona throws a tantrum at the Country Club.`,
                `You lose 15 prestige points!`
              ]);
            }
          }
        });
        return;
      } else {
        m.active = false;
        showMessageLines([
          `Your affair with ${mch.name} has quietly run its course.`,
          `You part ways on friendly terms.`
        ]);
        return;
      }
    }
  }

  // Roll a random town event from CODE_15, CODE_16, CODE_17, CODE_21
  if (Math.random() < 0.48) {
    triggerRandomTownEvent();
  }
  recalcWorth(G.player);
  recalcWorth(G.rival);
  updateDossierTable();
}

function triggerRandomTownEvent() {
  const roll = Math.floor(Math.random() * 14);
  if (roll === 0) {
    // CODE_15: Trust appointment
    const trustNames = ["Emil J. Aardvark", "Joseph P. Baloney", "Jacob Z. Coldfish", "Carl V. Dipstik"];
    const tidx = Math.floor(Math.random() * 4);
    const trustInf = getCatInfluence(455) + getCatInfluence(462);
    if (trustInf > 2) {
      G.trustsOwned[tidx] = true;
      G.player.cash += 15000;
      G.player.prestige += 25;
      showMessageLines([
        `The Bank Trust Officers and Judges have appointed you`,
        `Trustee of the ${trustNames[tidx]} Trust!`,
        `You receive a $15,000 trustee fee and 25 prestige points.`
      ]);
    } else {
      G.rival.cash += 15000;
      G.rival.prestige += 20;
      showMessageLines([
        `You and MacRascal competed to be Trustee of the`,
        `${trustNames[tidx]} Trust.`,
        `Because you lacked clout with the Trust Officers (Cathy Cook,`,
        `Lily Long, Sam Smith), MacRascal got the appointment!`
      ]);
    }
  } else if (roll === 1) {
    // CODE_15: Run for Mayor
    openModal(7007, {
      promptLines: [
        "The Tumbleweed Mayoral Election is coming up!",
        "Campaigning against MacRascal's candidate costs $5,000.",
        "Do you want to run for Mayor of Tumbleweed?"
      ],
      onDone: (yes) => {
        closeModal();
        if (!yes) return;
        G.player.cash -= 5000;
        const polInf = getCatInfluence(465) + getCatInfluence(453) + (G.player.shares[4] * 0.2);
        if (polInf > 4 || Math.random() < 0.4) {
          G.isMayor = true;
          G.player.prestige += 60;
          showMessageLines([
            "LANDSLIDE VICTORY!",
            "With the backing of Political Chairman Ted Taft and the",
            "Newspaper reporters, you are elected Mayor of Tumbleweed!",
            "You gain 60 prestige points!"
          ]);
        } else {
          G.player.prestige -= 10;
          showMessageLines([
            "You lost the Mayoral election to MacRascal's candidate!",
            "Try building more influence with Ted Taft (Butler Bldg)",
            "and the Newspaper reporters (Betty Baker & Kirk King)."
          ]);
        }
      }
    });
  } else if (roll === 2) {
    // CODE_16: Consulting Fee competition
    const bankInf = getCatInfluence(464) + (G.player.shares[1] * 0.3);
    if (bankInf > 3) {
      G.player.cash += 20000;
      G.player.prestige += 15;
      showMessageLines([
        "Tumbleweed Bank awarded you a $20,000 consulting contract",
        "over Mac MacRascal! (+15 prestige)"
      ]);
    } else {
      G.rival.cash += 20000;
      showMessageLines([
        "You and MacRascal competed for a $20,000 Bank consulting fee.",
        "Bank President Dan Davis awarded the contract to MacRascal!"
      ]);
    }
  } else if (roll === 3) {
    // CODE_16: Lawsuit ($50,000)
    const lawInf = getCatInfluence(461) + getCatInfluence(462);
    if (lawInf >= 3) {
      G.player.prestige += 10;
      showMessageLines([
        "MacRascal's cronies sued you for $50,000 in Tumbleweed Court,",
        "but your friendly Judges and Lawyers threw the case out!",
        "You gain 10 prestige points."
      ]);
    } else {
      G.player.cash -= 20000;
      G.player.prestige -= 10;
      showMessageLines([
        "You were sued for damages in Tumbleweed Court!",
        "Because you lacked influence with the Judges (John Jones,",
        "Perry Parks) and Lawyers, you lost $20,000 and 10 prestige!"
      ]);
    }
  } else if (roll === 4) {
    // CODE_16: Tax Audit
    const taxInf = getCatInfluence(451); // Nate Ness (728)
    if (taxInf > 0) {
      G.player.cash += 10000;
      showMessageLines([
        "Tax Appraiser Nate Ness lowered the tax assessment",
        "on your properties! You save $10,000."
      ]);
    } else {
      G.player.cash -= 8000;
      showMessageLines([
        "Tax Appraiser Nate Ness hit your properties with a",
        "surprise tax reassessment! You owe $8,000."
      ]);
    }
  } else if (roll === 5) {
    // CODE_17: Oil Well Discovery
    const oilInf = getCatInfluence(460) + getCatInfluence(458); // Olga Oaks (731), Rita Ryan (735)
    if (oilInf >= 0) {
      G.player.cash += 35000;
      G.player.prestige += 20;
      showMessageLines([
        "GUSHER! Following a tip from Geologist Olga Oaks and",
        "Landman Rita Ryan, your Uncle Sawdust's old oil lease",
        "struck a new pocket of crude! You make $35,000!"
      ]);
    } else {
      G.player.cash -= 10000;
      showMessageLines([
        "Your oil well ran into saltwater seepage.",
        "Environmental cleanup and repairs cost you $10,000."
      ]);
    }
  } else if (roll === 6) {
    // CODE_17: Mona MacNasty Scandal
    const scandals = [
      {
        lines: [
          "You had a fight with your wife Mona.",
          "She went to a bar, got drunk, and danced on the table",
          "in her underwear. You lose 5 prestige points."
        ],
        cash: 0, prestige: -5
      },
      {
        lines: [
          "Your wife Mona was arrested after shooting at a traffic cop",
          "with her pearl-handled revolver!",
          "Legal fees and fines cost you $5,000."
        ],
        cash: -5000, prestige: -5
      },
      {
        lines: [
          "Your wife Mona got mad when you stayed out all night.",
          "She threw a lamp through the picture window.",
          "Repairs cost you $500."
        ],
        cash: -500, prestige: 0
      }
    ];
    const sc = scandals[Math.floor(Math.random() * scandals.length)];
    G.player.cash += sc.cash;
    G.player.prestige += sc.prestige;
    showMessageLines(sc.lines);
  } else if (roll === 7) {
    // CODE_21: Horse Race Bet ($1,000 on Faster Than Light)
    openModal(7007, {
      promptLines: [
        "Mac MacRascal walks up to you at the Country Club:",
        "\"Say Max, Care to bet $1,000 on my horse Faster Than Light",
        "in the Tumbleweed Derby today?\""
      ],
      onDone: (yes) => {
        closeModal();
        if (!yes) return;
        if (Math.random() < 0.5) {
          G.player.cash += 1000;
          G.player.prestige += 5;
          showMessageLines([
            "Your horse beat MacRascal's Faster Than Light by a nose!",
            "You win $1,000 and 5 prestige points!"
          ]);
        } else {
          G.player.cash -= 1000;
          showMessageLines([
            "Faster Than Light won the race!",
            "You hand $1,000 over to a grinning Mac MacRascal."
          ]);
        }
      }
    });
  } else if (roll === 8) {
    // CODE_21: Horse Race Bet ($20,000 on Old Gray — poisoned by MacRascal!)
    openModal(7007, {
      promptLines: [
        "MacRascal offers to bet you $20,000 that his nag can beat",
        "the undefeated champion racehorse 'Old Gray'!",
        "Do you take the $20,000 bet?"
      ],
      onDone: (yes) => {
        closeModal();
        if (!yes) return;
        const copInf = getCatInfluence(452); // Holly Hall (715), Leon Long (722)
        if (copInf >= 4) {
          G.player.cash += 20000;
          G.player.prestige += 25;
          showMessageLines([
            "MacRascal tried to poison Old Gray before the race,",
            "but your friends on the Police force caught his henchman!",
            "Old Gray wins easily — you collect $20,000 and 25 prestige!"
          ]);
        } else {
          G.player.cash -= 20000;
          G.player.prestige -= 10;
          showMessageLines([
            "DIRTY POOL! MacRascal poisoned Old Gray's oats before the race!",
            "Old Gray stumbled out of the gate and lost.",
            "You lose $20,000 and 10 prestige points!"
          ]);
        }
      }
    });
  } else if (roll === 9) {
    // CODE_21: J. Marmaduke Dirty — Stealing Oil ($5,000)
    openModal(7007, {
      promptLines: [
        "Your old college fraternity brother J. Marmaduke Dirty",
        "slips into your office: \"Max! For $5,000 we can tap into",
        "the main pipeline and siphon $25,000 worth of oil! In?\""
      ],
      onDone: (yes) => {
        closeModal();
        if (!yes) return;
        G.player.cash -= 5000;
        const lawCop = getCatInfluence(452) + getCatInfluence(463);
        if (lawCop >= 2 || Math.random() < 0.55) {
          G.player.cash += 30000;
          showMessageLines([
            "J. Marmaduke Dirty's midnight pipeline tap worked like a charm!",
            "Your $5,000 investment nets you $25,000 in clear profit!"
          ]);
        } else {
          G.player.cash -= 15000;
          G.player.prestige -= 15;
          showMessageLines([
            "BUSTED! Police Detective Leon Long and DA Oscar Oaks",
            "caught J. Marmaduke Dirty red-handed!",
            "Paying off fines and lawyers costs you $15,000 and 15 prestige!"
          ]);
        }
      }
    });
  } else if (roll === 10) {
    // CODE_21: J. Marmaduke Dirty — Salted Oil Well Scam ($10,000)
    openModal(7007, {
      promptLines: [
        "J. Marmaduke Dirty grins: \"Max, put up $10,000 and we'll",
        "salt a dry oil well and sell shares to eastern suckers",
        "for a $50,000 profit! Are you in?\""
      ],
      onDone: (yes) => {
        closeModal();
        if (!yes) return;
        G.player.cash -= 10000;
        const geoInf = getCatInfluence(460) + getCatInfluence(458);
        if (geoInf >= 2 || Math.random() < 0.5) {
          G.player.cash += 60000;
          showMessageLines([
            "Geologist Olga Oaks certified the salted core samples!",
            "You and J. Marmaduke Dirty clear a $50,000 profit!"
          ]);
        } else {
          G.player.cash -= 20000;
          G.player.prestige -= 20;
          showMessageLines([
            "Geologist Olga Oaks exposed the salted oil well as a fraud!",
            "Angry investors sue you for $20,000 and you lose 20 prestige!"
          ]);
        }
      }
    });
  } else if (roll === 11) {
    // CODE_17: Board of Directors Election
    const which = Math.random() < 0.5 ? 0 : 1;
    const bName = which === 0 ? "Tumbleweed Bank" : "Widget Company";
    const sIdx = which === 0 ? 1 : 0;
    const inf = getCatInfluence(which === 0 ? 464 : 467) + G.player.shares[sIdx];
    if (inf >= 15) {
      G.boardsOwned[which] = true;
      G.player.prestige += 30;
      showMessageLines([
        `You have been elected to the Board of Directors`,
        `of the ${bName}!`,
        `You gain 30 prestige points and $10,000/yr in director fees!`
      ]);
    } else {
      showMessageLines([
        `A seat opened up on the ${bName} Board of Directors,`,
        `but you didn't have enough shares and executive influence`,
        `to win the seat.`
      ]);
    }
  } else if (roll === 12) {
    // CODE_17: Country Club Membership
    const ccInf = getCatInfluence(456) + G.player.shares[5];
    if (ccInf >= 5) {
      G.player.prestige += 25;
      showMessageLines([
        "With the support of Club Manager Gail Giles and pros",
        "Irwin & Inger Idle, you win the Country Club",
        "Citizen of the Year trophy! (+25 prestige)"
      ]);
    } else {
      G.player.prestige -= 5;
      showMessageLines([
        "Mac MacRascal convinced the Country Club committee",
        "to snub you at the annual Charity Ball! (-5 prestige)"
      ]);
    }
  } else {
    // CODE_16: MacRascal smears you
    const victimCid = 700 + Math.floor(Math.random() * 44);
    if (victimCid !== 724 && victimCid !== 726) {
      clampRel(victimCid, -3);
      showMessageLines([
        `Mac MacRascal has been spreading vicious stories about you`,
        `to ${CHARS_DB[victimCid].name}!`,
        `Your standing with ${CHARS_DB[victimCid].name} dropped.`
      ]);
    }
  }
}

function triggerEndgame() {
  recalcWorth(G.player);
  recalcWorth(G.rival);
  const pScore = G.player.worth + G.player.prestige * 1000;
  const rScore = G.rival.worth + G.rival.prestige * 1000;
  G.endgameWon = pScore >= rScore;
  G.mode = "ENDGAME";
  G.endgameAnimTick = 0;
  updateMenus();
}

// ============================================================================
// CLASSIC MACINTOSH SYSTEM 6 RENDERER (512x342 1-bit + crisp Chicago/Geneva UI)
// ============================================================================
const canvas = document.getElementById("macScreen");
const ctx = canvas.getContext("2d");

function drawIcon(iconId, dx, dy, transparentWhite = false) {
  const data = RSRC.ICON[iconId];
  if (!data) return;
  const imgData = ctx.getImageData(dx, dy, 32, 32);
  const pix = imgData.data;
  for (let y = 0; y < 32; y++) {
    const rowOff = y * 4;
    const b0 = data[rowOff], b1 = data[rowOff+1], b2 = data[rowOff+2], b3 = data[rowOff+3];
    const rowBits = ((b0 << 24) | (b1 << 16) | (b2 << 8) | b3) >>> 0;
    for (let x = 0; x < 32; x++) {
      const bit = (rowBits >>> (31 - x)) & 1;
      const pIdx = (y * 32 + x) * 4;
      if (bit) {
        pix[pIdx] = 0; pix[pIdx+1] = 0; pix[pIdx+2] = 0; pix[pIdx+3] = 255;
      } else if (!transparentWhite) {
        pix[pIdx] = 255; pix[pIdx+1] = 255; pix[pIdx+2] = 255; pix[pIdx+3] = 255;
      }
    }
  }
  ctx.putImageData(imgData, dx, dy);
}

function drawDesktopPattern() {
  const imgData = ctx.createImageData(512, 342);
  const pix = imgData.data;
  for (let y = 0; y < 342; y++) {
    for (let x = 0; x < 512; x++) {
      const isBlack = ((x + y) & 1) === 0;
      const c = y < 20 ? 255 : (isBlack ? 85 : 220);
      const idx = (y * 512 + x) * 4;
      pix[idx] = c; pix[idx+1] = c; pix[idx+2] = c; pix[idx+3] = 255;
    }
  }
  ctx.putImageData(imgData, 0, 0);
}

function drawMacWindowFrame(x, y, w, h, title, hasTitleBar = true) {
  // Drop shadow
  ctx.fillStyle = "#000";
  ctx.fillRect(x + 2, y + 2, w, h);
  // White window body
  ctx.fillStyle = "#fff";
  ctx.fillRect(x, y, w, h);
  ctx.strokeStyle = "#000";
  ctx.lineWidth = 1;
  ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);

  if (hasTitleBar) {
    const th = 18;
    ctx.fillStyle = "#fff";
    ctx.fillRect(x + 1, y + 1, w - 2, th);
    ctx.strokeRect(x + 0.5, y + 0.5, w - 1, th);
    // Classic Mac pinstripes
    ctx.fillStyle = "#000";
    for (let py = y + 3; py < y + th - 2; py += 2) {
      ctx.fillRect(x + 4, py, w - 8, 1);
    }
    if (title) {
      ctx.font = "bold 11px 'Chicago', 'Geneva', 'Monaco', monospace";
      const tw = ctx.measureText(title).width + 12;
      const tx = x + Math.floor((w - tw) / 2);
      ctx.fillStyle = "#fff";
      ctx.fillRect(tx, y + 2, tw, th - 3);
      ctx.fillStyle = "#000";
      ctx.fillText(title, tx + 6, y + 13);
    }
  }
}

function drawRadioButton(x, y, w, h, label, checked) {
  ctx.fillStyle = "#fff";
  ctx.fillRect(x, y + 1, w, h - 2);
  const cx = x + 7;
  const cy = y + Math.floor(h / 2);
  ctx.strokeStyle = "#000";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(cx, cy, 5, 0, Math.PI * 2);
  ctx.fillStyle = "#fff";
  ctx.fill();
  ctx.stroke();
  if (checked) {
    ctx.beginPath();
    ctx.arc(cx, cy, 2.5, 0, Math.PI * 2);
    ctx.fillStyle = "#000";
    ctx.fill();
  }
  ctx.fillStyle = "#000";
  ctx.font = "11px 'Geneva', 'Tahoma', sans-serif";
  ctx.fillText(label || "", x + 16, cy + 4);
}

function drawPushButton(x, y, w, h, label, isDefault = false) {
  ctx.fillStyle = "#fff";
  ctx.fillRect(x, y, w, h);
  ctx.strokeStyle = "#000";
  ctx.lineWidth = isDefault ? 2 : 1;
  ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
  ctx.fillStyle = "#000";
  ctx.font = "bold 11px 'Chicago', 'Geneva', sans-serif";
  const tw = ctx.measureText(label || "").width;
  ctx.fillText(label || "", x + Math.floor((w - tw) / 2), y + Math.floor(h / 2) + 4);
}

function renderDITLWindow(dlogId, selectedRad1, selectedRad2 = -1, customHook = null) {
  const dlog = RSRC.DLOG[dlogId];
  const ditl = RSRC.DITL[dlog.itemsId];
  if (!dlog || !ditl) return;

  const wx = dlog.rect.l;
  const wy = dlog.rect.t;
  const ww = dlog.rect.w;
  const wh = dlog.rect.h;
  const hasTitle = dlog.procId === 0 || dlog.procId === 4 || dlog.title.length > 0;
  drawMacWindowFrame(wx, wy, ww, wh, dlog.title, hasTitle);
  if (!hasTitle) {
    // Double-border modal dialog frame
    ctx.strokeStyle = "#000";
    ctx.strokeRect(wx + 3.5, wy + 3.5, ww - 7, wh - 7);
  }

  // First pass: ICON items (kind === 32)
  for (const it of ditl) {
    if (it.kind === 32 && it.val !== null) {
      drawIcon(it.val, wx + it.rect.l, wy + it.rect.t);
    }
  }
  // Second pass: controls & static text
  for (const it of ditl) {
    const ix = wx + it.rect.l, iy = wy + it.rect.t, iw = it.rect.w, ih = it.rect.h;
    if (it.kind === 5 || it.kind === 6) {
      const isChecked = (it.index === selectedRad1) || (it.index === selectedRad2);
      drawRadioButton(ix, iy, iw, ih, it.val, isChecked);
    } else if (it.kind === 4) {
      drawPushButton(ix, iy, iw, ih, it.val, it.index === 1);
    } else if (it.kind === 8) {
      let text = it.val || "";
      if (customHook) {
        const rep = customHook(it);
        if (rep !== null && rep !== undefined) text = rep;
      }
      ctx.fillStyle = "#000";
      ctx.font = "11px 'Geneva', 'Monaco', sans-serif";
      ctx.fillText(text, ix, iy + 12);
    }
  }
}

function renderMenuBar() {
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, 512, 20);
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 19, 512, 1);

  ctx.font = "bold 12px 'Chicago', 'Geneva', sans-serif";
  for (let i = 0; i < MENUS.length; i++) {
    const m = MENUS[i];
    const active = G.openMenuIdx === i;
    if (active) {
      ctx.fillStyle = "#000";
      ctx.fillRect(m.x, 1, m.w, 18);
      ctx.fillStyle = "#fff";
    } else {
      ctx.fillStyle = "#000";
    }
    ctx.fillText(m.title === "\uF8FF" ? "" : m.title, m.x + 6, 14);
  }

  // Dropdown menu if open
  if (G.openMenuIdx >= 0) {
    const m = MENUS[G.openMenuIdx];
    const mw = 156;
    const mh = m.items.length * 18 + 4;
    const mx = m.x;
    const my = 20;
    ctx.fillStyle = "#000";
    ctx.fillRect(mx + 2, my + 2, mw, mh);
    ctx.fillStyle = "#fff";
    ctx.fillRect(mx, my, mw, mh);
    ctx.strokeStyle = "#000";
    ctx.strokeRect(mx + 0.5, my + 0.5, mw - 1, mh - 1);

    for (let j = 0; j < m.items.length; j++) {
      const it = m.items[j];
      const iy = my + 2 + j * 18;
      if (it.name === "-") {
        ctx.fillStyle = "#888";
        ctx.fillRect(mx + 2, iy + 8, mw - 4, 1);
        continue;
      }
      const hovered = G.hoverMenuItem === j && it.enabled;
      if (hovered) {
        ctx.fillStyle = "#000";
        ctx.fillRect(mx + 1, iy, mw - 2, 18);
        ctx.fillStyle = "#fff";
      } else {
        ctx.fillStyle = it.enabled ? "#000" : "#999";
      }
      ctx.font = "11px 'Chicago', 'Geneva', sans-serif";
      ctx.fillText(it.name, mx + 12, iy + 13);
    }
  }
}

function renderScreen() {
  drawDesktopPattern();

  if (G.mode === "MESSAGE") {
    drawMacWindowFrame(7, 46, 498, 290, "Message", true);
    ctx.fillStyle = "#000";
    ctx.font = "12px 'Geneva', 'Helvetica', sans-serif";
    for (const ln of G.messageLines) {
      ctx.fillText(ln.text, 7 + ln.x, 46 + 18 + ln.y);
    }
  } else if (G.mode === "STREET") {
    renderDITLWindow(7006, -1);
  } else if (G.mode === "BUILDING") {
    renderDITLWindow(G.currentBuilding, G.selectedRadio);
  } else if (G.mode === "MODAL" && G.modal) {
    // Draw background window first
    if (G.currentBuilding) renderDITLWindow(G.currentBuilding, G.selectedRadio);
    else renderDITLWindow(7006, -1);

    const md = G.modal;
    if (md.dlogId === "BRIBE_MONEY") {
      // Custom Bribe -> Money scrollbar dialog (CODE_13 + CNTL 130)
      const wx = 85, wy = 80, ww = 340, wh = 160;
      drawMacWindowFrame(wx, wy, ww, wh, "Bribe with Money", true);
      ctx.fillStyle = "#000";
      ctx.font = "12px 'Geneva', sans-serif";
      const ch = CHARS_DB[G.selectedChar];
      ctx.fillText(`How much money do you offer ${ch.name}?`, wx + 22, wy + 44);
      ctx.font = "bold 14px 'Chicago', monospace";
      ctx.fillText(`Offer: $${md.scrollVal.toLocaleString()}`, wx + 115, wy + 70);
      // Scrollbar track (wx+30 .. wx+310, wy+85, h=16)
      ctx.strokeStyle = "#000";
      ctx.strokeRect(wx + 30.5, wy + 85.5, 280, 16);
      const pct = md.scrollVal / 10000;
      const thumbX = wx + 32 + Math.floor(pct * 260);
      ctx.fillStyle = "#000";
      ctx.fillRect(thumbX, wy + 87, 16, 13);
      ctx.font = "10px 'Geneva', sans-serif";
      ctx.fillText("$0", wx + 30, wy + 114);
      ctx.fillText("$5,000", wx + 155, wy + 114);
      ctx.fillText("$10,000", wx + 280, wy + 114);
      drawPushButton(wx + 75, wy + 125, 80, 22, "Offer Bribe", true);
      drawPushButton(wx + 185, wy + 125, 80, 22, "Cancel", false);
    } else if (md.dlogId === 6002) {
      // Score dialog (DLOG 6002)
      renderDITLWindow(6002, -1, -1, (it) => {
        if (it.index === 8) return "$" + G.player.cash.toLocaleString();
        if (it.index === 9) return "$" + G.rival.cash.toLocaleString();
        if (it.index === 10) return "$" + G.player.debt.toLocaleString();
        if (it.index === 11) return "$" + G.rival.debt.toLocaleString();
        if (it.index === 12) return "$" + G.player.worth.toLocaleString();
        if (it.index === 13) return "$" + G.rival.worth.toLocaleString();
        if (it.index === 14) return String(G.player.prestige);
        if (it.index === 15) return String(G.rival.prestige);
        if (it.index === 17) return String(G.age);
        return null;
      });
    } else if (md.dlogId === 6000) {
      // Buy Property (DLOG 6000)
      renderDITLWindow(6000, md.selectedRadio, -1, (it) => {
        if (it.index >= 9 && it.index <= 14) {
          const lot = G.buyOfferLots[it.index - 9];
          return lot < 10 ? "0" + lot : String(lot);
        }
        return null;
      });
    } else if (md.dlogId === 6001) {
      // Sell Property (DLOG 6001)
      renderDITLWindow(6001, md.selectedRadio, md.selectedRadio2, (it) => {
        if (it.index >= 16 && it.index <= 21) {
          return String(G.player.shares[it.index - 16]);
        }
        return null;
      });
    } else if (md.dlogId === 7007) {
      // Interactive Yes/No Event (DLOG 7007)
      renderDITLWindow(7007, -1);
      const dlog = RSRC.DLOG[7007];
      ctx.fillStyle = "#000";
      ctx.font = "12px 'Geneva', sans-serif";
      md.promptLines.forEach((ln, idx) => {
        ctx.fillText(ln, dlog.rect.l + 18, dlog.rect.t + 26 + idx * 18);
      });
    } else {
      renderDITLWindow(md.dlogId, md.selectedRadio);
    }
  } else if (G.mode === "ENDGAME") {
    // CODE_23 Endgame sequence with Mephistopheles & Devils (ICON 4000..4012)
    drawMacWindowFrame(7, 46, 498, 290, "End of the Road", true);
    ctx.fillStyle = "#000";
    ctx.font = "12px 'Geneva', sans-serif";
    if (!G.endgameWon) {
      ctx.fillText("Here you are at the end of your life. And what have you", 45, 95);
      ctx.fillText("accomplished? Not much. Even though you were given a fine", 45, 115);
      ctx.fillText("evil name to uphold, you let that upstart MacRascal beat you.", 45, 135);
      ctx.fillText(`Your Final Worth: $${G.player.worth.toLocaleString()} (Prestige: ${G.player.prestige})`, 45, 175);
      ctx.fillText(`MacRascal's Worth: $${G.rival.worth.toLocaleString()} (Prestige: ${G.rival.prestige})`, 45, 195);
      drawPushButton(200, 260, 110, 24, "Play Again", true);
    } else {
      ctx.fillText("Well Max, your life is over. Look around, someone is coming", 45, 85);
      ctx.fillText("to meet you. Why, it's Mephistopheles! And he's brought a", 45, 103);
      ctx.fillText("couple of his helpers:", 45, 121);
      ctx.font = "bold 12px 'Chicago', sans-serif";
      ctx.fillText("\"Welcome to Hell, Max. You're our kind of guy. Follow me,", 45, 148);
      ctx.fillText("we have a hot time in store for you!\"", 45, 166);

      // Draw Mephistopheles (ICON 4002 head + 4003 body) & dancing devils (4004..4012)
      const bounce = Math.floor(G.endgameAnimTick / 15) % 2;
      drawIcon(4002, 140, 185);
      drawIcon(4003, 140, 217);

      const dFrame = bounce === 0 ? 4005 : 4007;
      const dLegs = bounce === 0 ? 4006 : 4008;
      drawIcon(4004, 240, 185);
      drawIcon(dFrame, 240, 217);
      drawIcon(dLegs, 240, 249);

      drawIcon(4004, 330, 185);
      drawIcon(bounce === 0 ? 4009 : 4011, 330, 217);
      drawIcon(bounce === 0 ? 4010 : 4012, 330, 249);

      drawPushButton(200, 295, 110, 24, "Play Again", true);
    }
  }

  renderMenuBar();
  updateStatusStrip();
}

function updateStatusStrip() {
  const locName = G.currentBuilding ? BUILDING_RADIOS[G.currentBuilding].name : "On the Street (Tumbleweed)";
  const chName = CHARS_DB[G.selectedChar] ? CHARS_DB[G.selectedChar].name : "Max MacNasty";
  document.getElementById("statusLeft").innerHTML =
    `Location: <b>${locName}</b> | Selected: <b>${chName}</b> (Your Clout: <b>${G.rel[G.selectedChar] || 0}</b>)`;
  document.getElementById("statusRight").innerHTML =
    `Cash: <b>$${G.player.cash.toLocaleString()}</b> | Worth: <b>$${G.player.worth.toLocaleString()}</b> | Debt: <b>$${G.player.debt.toLocaleString()}</b> | Prestige: <b>${G.player.prestige}</b> | Age: <b>${G.age}</b>`;
}

// Mouse Interaction on the 512x342 Canvas
function getCanvasCoords(ev) {
  const r = canvas.getBoundingClientRect();
  return {
    x: Math.floor((ev.clientX - r.left) * (512 / r.width)),
    y: Math.floor((ev.clientY - r.top) * (342 / r.height))
  };
}

canvas.addEventListener("mousemove", (ev) => {
  const { x, y } = getCanvasCoords(ev);
  if (G.openMenuIdx >= 0) {
    // Check if hovering over another menu title
    if (y < 20) {
      for (let i = 0; i < MENUS.length; i++) {
        if (x >= MENUS[i].x && x <= MENUS[i].x + MENUS[i].w) {
          G.openMenuIdx = i;
          G.hoverMenuItem = -1;
          break;
        }
      }
    } else {
      const m = MENUS[G.openMenuIdx];
      const my = 20;
      const mh = m.items.length * 18 + 4;
      if (x >= m.x && x <= m.x + 156 && y >= my && y <= my + mh) {
        G.hoverMenuItem = Math.floor((y - my - 2) / 18);
      } else {
        G.hoverMenuItem = -1;
      }
    }
  }
});

canvas.addEventListener("mousedown", (ev) => {
  const { x, y } = getCanvasCoords(ev);

  // 1. Check if clicking inside an open dropdown menu
  if (G.openMenuIdx >= 0) {
    const m = MENUS[G.openMenuIdx];
    const my = 20;
    const mh = m.items.length * 18 + 4;
    if (x >= m.x && x <= m.x + 156 && y >= my && y <= my + mh) {
      const idx = Math.floor((y - my - 2) / 18);
      const it = m.items[idx];
      G.openMenuIdx = -1;
      G.hoverMenuItem = -1;
      if (it && it.enabled && it.action) {
        handleMenuAction(it.action);
      }
      return;
    }
    G.openMenuIdx = -1;
    G.hoverMenuItem = -1;
    if (y < 20) return;
  }

  // 2. Check Menu Bar click
  if (y < 20) {
    for (let i = 0; i < MENUS.length; i++) {
      if (x >= MENUS[i].x && x <= MENUS[i].x + MENUS[i].w) {
        G.openMenuIdx = i;
        G.hoverMenuItem = -1;
        return;
      }
    }
    return;
  }

  // 3. Mode-specific clicks
  if (G.mode === "MESSAGE") {
    const cb = G.afterMessageCallback;
    G.afterMessageCallback = null;
    if (cb) cb();
    return;
  }

  if (G.mode === "ENDGAME") {
    resetGame();
    return;
  }

  if (G.mode === "MODAL" && G.modal) {
    handleModalClick(x, y);
    return;
  }

  if (G.mode === "STREET") {
    // Check DLOG 7006 radio buttons (1..6) or building icons
    const dlog = RSRC.DLOG[7006];
    const ditl = RSRC.DITL[7006];
    const lx = x - dlog.rect.l, ly = y - dlog.rect.t;
    // Radio buttons 1..6 map to: 1=Bank(7002), 2=Allen(7001), 3=Butler(7004), 4=Widget(7000), 5=Court(7003), 6=CountryClub(7005)
    const streetMap = { 1: 7002, 2: 7001, 3: 7004, 4: 7000, 5: 7003, 6: 7005 };
    for (let i = 1; i <= 6; i++) {
      const r = ditl[i - 1].rect;
      if (lx >= r.l - 30 && lx <= r.r + 30 && ly >= r.t - 90 && ly <= r.b + 20) {
        enterBuilding(streetMap[i]);
        return;
      }
    }
    return;
  }

  if (G.mode === "BUILDING") {
    const dlog = RSRC.DLOG[G.currentBuilding];
    const ditl = RSRC.DITL[G.currentBuilding];
    const lx = x - dlog.rect.l, ly = y - dlog.rect.t;
    const bmap = BUILDING_RADIOS[G.currentBuilding].map;
    for (const [rIdxStr, cid] of Object.entries(bmap)) {
      const rIdx = parseInt(rIdxStr, 10);
      const r = ditl[rIdx - 1].rect;
      // Allow clicking either the radio button OR the character's head/body portrait right above it!
      if (lx >= r.l - 8 && lx <= r.r + 8 && ly >= r.t - 68 && ly <= r.b + 4) {
        G.selectedRadio = rIdx;
        G.selectedChar = cid;
        return;
      }
    }
  }
});

function enterBuilding(dlogId) {
  G.currentBuilding = dlogId;
  G.mode = "BUILDING";
  G.selectedRadio = 1;
  G.selectedChar = BUILDING_RADIOS[dlogId].map[1];
  updateMenus();
}

function handleModalClick(x, y) {
  const md = G.modal;
  if (md.dlogId === "BRIBE_MONEY") {
    const wx = 85, wy = 80;
    // Scrollbar click
    if (x >= wx + 28 && x <= wx + 312 && y >= wy + 80 && y <= wy + 106) {
      const pct = Math.max(0, Math.min(1, (x - (wx + 32)) / 260));
      md.scrollVal = Math.round((pct * 10000) / 100) * 100;
      return;
    }
    // Offer Bribe button
    if (x >= wx + 75 && x <= wx + 155 && y >= wy + 125 && y <= wy + 147) {
      const amt = md.scrollVal;
      closeModal();
      if (amt > G.player.cash) {
        G.player.prestige -= 25;
        showMessageLines([
          "Your check bounced! You don't have that much cash.",
          "You lose 25 prestige points and forfeit a turn."
        ], () => advanceTurn());
        return;
      }
      G.player.cash -= amt;
      recalcWorth(G.player);
      const cid = G.selectedChar;
      const ch = CHARS_DB[cid];
      if (ch.vuln_money && amt >= 1000) {
        const weight = amt >= 5000 ? 2 : 1;
        showMessageLines([
          `${ch.name} pockets your $${amt.toLocaleString()} with a warm smile!`,
          `"It's a pleasure doing business with you, Max."`
        ], () => openPersuadeDialog(cid, weight));
      } else if (ch.vuln_money && amt < 1000) {
        showMessageLines([
          `${ch.name} takes your $${amt.toLocaleString()}, but says:`,
          `"That's peanuts, Max! Don't expect any favors for that."`
        ], () => advanceTurn());
      } else {
        clampRel(cid, -3);
        showMessageLines([
          `${ch.name} is offended by your bribe attempt!`,
          `Your standing with ${ch.name} decreased.`
        ], () => advanceTurn());
      }
      return;
    }
    // Cancel button
    if (x >= wx + 185 && x <= wx + 265 && y >= wy + 125 && y <= wy + 147) {
      closeModal();
      return;
    }
    return;
  }

  const dlog = RSRC.DLOG[md.dlogId];
  const ditl = RSRC.DITL[dlog.itemsId];
  const lx = x - dlog.rect.l, ly = y - dlog.rect.t;

  for (const it of ditl) {
    const r = it.rect;
    if (lx >= r.l && lx <= r.r && ly >= r.t && ly <= r.b) {
      if (md.dlogId === 7008) {
        // Shareware intro dialog: 1=Yes (show address), 2=No (start game)
        closeModal();
        if (it.index === 1) {
          showMessageLines([
            "MacNasty is a shareware program.",
            "If you enjoy playing MacNasty, please send $15 to:",
            "George Lott",
            "P.O. Box 13834",
            "Arlington, TX 76013"
          ]);
        }
        return;
      } else if (md.dlogId === 6002) {
        if (it.index === 1) closeModal();
        return;
      } else if (md.dlogId === 6003) {
        // Persuade dialog: 1=OK, 2..6=Radio buttons
        if (it.index >= 2 && it.index <= 6) {
          md.selectedRadio = it.index;
        } else if (it.index === 1 && md.onDone) {
          md.onDone(md.selectedRadio);
        }
        return;
      } else if (md.dlogId === 7007) {
        // Yes (1) / No (2) decision dialog
        if ((it.index === 1 || it.index === 2) && md.onDone) {
          md.onDone(it.index === 1);
        }
        return;
      } else if (md.dlogId === 6000) {
        // Buy stock: 1=OK, 2=Cancel, 3..8=Stock radio
        if (it.index >= 3 && it.index <= 8) {
          md.selectedRadio = it.index;
        } else if (it.index === 2) {
          closeModal();
        } else if (it.index === 1) {
          const sIdx = md.selectedRadio - 3;
          const qty = G.buyOfferLots[sIdx];
          closeModal();
          if (qty <= 0) {
            showMessageLines([`There are no shares of the ${STOCK_NAMES[sIdx]}`, `offered for sale right now.`]);
            return;
          }
          // Price depends on Broker (459) & Appraiser (457/469) influence
          const brkInf = getCatInfluence(459) + getCatInfluence(457);
          const base = STOCK_BASE_VAL[sIdx];
          let pricePerShare = base;
          let luckMsg = `You got each share for $${base.toLocaleString()}.`;
          if (brkInf >= 4 || Math.random() < 0.25) {
            pricePerShare = base === 12000 ? 10000 : 1000;
            luckMsg = `You were lucky and got it for $${pricePerShare.toLocaleString()}.`;
          } else if (brkInf < 0 && Math.random() < 0.5) {
            pricePerShare = base === 12000 ? 14000 : 1400;
            luckMsg = `You had to pay $${pricePerShare.toLocaleString()}.`;
          }
          const totalCost = pricePerShare * qty;
          if (G.player.cash < totalCost) {
            G.player.prestige -= 50;
            showMessageLines([
              "Oops, you don't have enough money to buy this.",
              "You lose 50 prestige points and forfeit a turn."
            ], () => advanceTurn());
            return;
          }
          G.player.cash -= totalCost;
          G.player.shares[sIdx] += qty;
          G.marketShares[sIdx] -= qty;
          G.player.prestige += qty * (base === 12000 ? 3 : 1);
          recalcWorth(G.player);
          const qtyWord = qty === 1 ? "one" : (qty === 5 ? "five" : "ten");
          showMessageLines([
            `Congratulations, you have just purchased ${qtyWord}`,
            `share(s) of the ${STOCK_NAMES[sIdx]}.`,
            `And each share is valued at $${base.toLocaleString()}.`,
            luckMsg
          ], () => advanceTurn());
        }
        return;
      } else if (md.dlogId === 6001) {
        // Sell stock: 1=OK, 2=Cancel, 4..9=Stock radio, 10..15=Amount radio (1,2,5,10,25,50)
        if (it.index >= 4 && it.index <= 9) md.selectedRadio = it.index;
        else if (it.index >= 10 && it.index <= 15) md.selectedRadio2 = it.index;
        else if (it.index === 2) closeModal();
        else if (it.index === 1) {
          const sIdx = md.selectedRadio - 4;
          const amounts = [1, 2, 5, 10, 25, 50];
          const qty = amounts[md.selectedRadio2 - 10];
          closeModal();
          if (G.player.shares[sIdx] < qty) {
            showMessageLines([`You don't own ${qty} share(s) of the ${STOCK_NAMES[sIdx]}!`]);
            return;
          }
          const base = STOCK_BASE_VAL[sIdx];
          G.player.shares[sIdx] -= qty;
          G.marketShares[sIdx] += qty;
          G.player.cash += qty * base;
          recalcWorth(G.player);
          showMessageLines([
            `You sold ${qty} share(s) of the ${STOCK_NAMES[sIdx]}`,
            `for $${(qty * base).toLocaleString()}.`
          ], () => advanceTurn());
        }
        return;
      } else if (md.dlogId === 6010) {
        // Borrow money (DLOG 6010): 1=OK, 2=Cancel, 3..8=Amount ($10k, $20k, $50k, $100k, $200k, $500k)
        if (it.index >= 3 && it.index <= 8) md.selectedRadio = it.index;
        else if (it.index === 2) closeModal();
        else if (it.index === 1) {
          const amounts = [10000, 20000, 50000, 100000, 200000, 500000];
          const req = amounts[md.selectedRadio - 3];
          closeModal();
          const bankInf = getCatInfluence(464) + getCatInfluence(450); // Bankers + Credit Clerks
          const maxLoan = Math.max(50000, G.player.worth + bankInf * 25000);
          if (G.player.debt + req <= maxLoan) {
            G.player.cash += req;
            G.player.debt += req;
            recalcWorth(G.player);
            showMessageLines([
              `Tumbleweed Bank approved your loan of $${req.toLocaleString()}!`,
              `Your total bank debt is now $${G.player.debt.toLocaleString()}.`
            ], () => advanceTurn());
          } else {
            showMessageLines([
              `Tumbleweed Bank rejected your $${req.toLocaleString()} loan request!`,
              `Build more influence with Bank President Dan Davis, Loan Officers`,
              `Bob Baker & Patty Parks, and Credit Clerk Nina Ness.`
            ], () => advanceTurn());
          }
        }
        return;
      }
    }
  }
}

function updateDossierTable() {
  const tbody = document.querySelector("#dossierTable tbody");
  if (!tbody) return;
  let html = "";
  const bldgByChar = {};
  for (const [bid, binfo] of Object.entries(BUILDING_RADIOS)) {
    for (const cid of Object.values(binfo.map)) {
      if (cid !== 724) bldgByChar[cid] = binfo.name;
    }
  }
  bldgByChar[724] = "All Buildings";

  for (let cid = 700; cid <= 743; cid++) {
    const ch = CHARS_DB[cid];
    const sp = CHARS_DB[ch.spouse_id];
    let secHtml = "None";
    if (ch.secret_id === 850 && ch.lover_name) {
      secHtml = `<span class="lover-tag">Lover: ${ch.lover_name} [${ch.lover_id}]</span>`;
    } else if (ch.secret_str) {
      secHtml = ch.secret_id === 852 ? `<span class="lover-tag">${ch.secret_str}</span>` : ch.secret_str;
    }
    const weak = [];
    if (ch.vuln_money) weak.push("Money");
    if (ch.vuln_favors) weak.push("Favors");
    if (ch.vuln_charm) weak.push("Charm");
    if (ch.vuln_blackmail) weak.push("Blackmail");
    if (ch.vuln_spouse_sec) weak.push("Spouse's Secret");
    html += `<tr>
      <td><b>${cid}</b></td>
      <td><b>${ch.name}</b></td>
      <td>${sp ? sp.name : ""} [${ch.spouse_id}]</td>
      <td>${bldgByChar[cid] || ""}</td>
      <td>${ch.rep_str || "—"}</td>
      <td>${ch.rumor_str || "—"}</td>
      <td>${secHtml}</td>
      <td>${weak.join(", ") || "None"}</td>
      <td><b>${G ? (G.rel[cid] || 0) : 0}</b></td>
    </tr>`;
  }
  tbody.innerHTML = html;
}

function resetGame() {
  G = createInitialState();
  updateMenus();
  updateDossierTable();
}

function toggleDossier() {
  const el = document.getElementById("dossierDrawer");
  el.style.display = el.style.display === "block" ? "none" : "block";
}

let is2x = true;
function toggleScale() {
  is2x = !is2x;
  canvas.style.width = is2x ? "1024px" : "512px";
  canvas.style.height = is2x ? "684px" : "342px";
}

resetGame();
function loop() {
  if (G.mode === "ENDGAME") G.endgameAnimTick++;
  renderScreen();
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
</script>
</body>
</html>
"""

html_out = html_template.replace("__RSRC_B64__", rsrc_b64).replace("__CHARS_JSON__", chars_json_str)
with open(out_html_path, "w", encoding="utf-8") as f:
    f.write(html_out)

print(f"Wrote {out_html_path} ({len(html_out):,} bytes)")
