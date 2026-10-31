use font8x8::{BASIC_FONTS, UnicodeFonts};
use minifb::{Key, MouseButton, MouseMode, Window, WindowOptions};
use std::collections::HashMap;
use std::time::{Duration, Instant};

const MAC_W: usize = 512;
const MAC_H: usize = 342;
const SCALE: usize = 2;
const WIN_W: usize = MAC_W * SCALE;
const WIN_H: usize = MAC_H * SCALE;

const RSRC_BYTES: &[u8] = include_bytes!("../../reference/macnasty/extracted/MacNasty_.rsrc");

#[derive(Clone, Debug)]
pub struct CharRecord {
    pub id: u16,
    pub name: &'static str,
    pub spouse_id: u16,
    pub cat: u16,
    pub vuln_blackmail: bool,
    pub secret_id: u16,
    pub secret_str: &'static str,
    pub vuln_money: bool,
    pub vuln_favors: bool,
    pub has_affair: bool,
    pub lover_id: u16,
    pub lover_name: &'static str,
    pub rumor_id: u16,
    pub rumor_str: &'static str,
    pub rep_id: u16,
    pub rep_str: &'static str,
    pub vuln_charm: bool,
    pub vuln_spouse_sec: bool,
    pub pub_lines: [&'static str; 3],
}

include!("../../reference/macnasty/rust_chars_table.inc");

fn get_char(cid: u16) -> &'static CharRecord {
    let idx = cid.saturating_sub(700) as usize;
    &CHARS_DB[idx.min(43)]
}

#[derive(Clone, Copy, Debug)]
struct Rect {
    l: i32,
    t: i32,
    r: i32,
    b: i32,
}

impl Rect {
    fn w(&self) -> i32 {
        self.r - self.l
    }
    fn h(&self) -> i32 {
        self.b - self.t
    }
    fn contains(&self, x: i32, y: i32) -> bool {
        x >= self.l && x <= self.r && y >= self.t && y <= self.b
    }
}

#[derive(Clone, Debug)]
struct DlogRes {
    rect: Rect,
    proc_id: i16,
    items_id: i16,
    title: String,
}

#[derive(Clone, Debug)]
struct DitlItem {
    index: usize,
    rect: Rect,
    kind: u8,
    val_str: String,
    val_id: i16,
}

struct ResourceFork {
    icons: HashMap<i16, [u8; 128]>,
    dlogs: HashMap<i16, DlogRes>,
    ditls: HashMap<i16, Vec<DitlItem>>,
}

fn read_u16(b: &[u8], off: usize) -> u16 {
    ((b[off] as u16) << 8) | (b[off + 1] as u16)
}
fn read_i16(b: &[u8], off: usize) -> i16 {
    read_u16(b, off) as i16
}
fn read_u32(b: &[u8], off: usize) -> u32 {
    ((b[off] as u32) << 24)
        | ((b[off + 1] as u32) << 16)
        | ((b[off + 2] as u32) << 8)
        | (b[off + 3] as u32)
}
fn read_mac_str(b: &[u8]) -> String {
    b.iter()
        .map(|&c| match c {
            0xD5 | 0x60 => '\'',
            0x20..=0x7E => c as char,
            _ => ' ',
        })
        .collect()
}

impl ResourceFork {
    fn parse(bytes: &[u8]) -> Self {
        let mut icons = HashMap::new();
        let mut dlogs = HashMap::new();
        let mut ditls = HashMap::new();

        let data_off = read_u32(bytes, 0) as usize;
        let map_off = read_u32(bytes, 4) as usize;
        let type_list_off = map_off + read_u16(bytes, map_off + 24) as usize;
        let num_types = (read_u16(bytes, map_off + 28).wrapping_add(1)) as usize;

        for i in 0..num_types {
            let toff = type_list_off + 2 + i * 8;
            let rtype = &bytes[toff..toff + 4];
            let rcount = (read_u16(bytes, toff + 4) + 1) as usize;
            let ref_list_off = type_list_off + read_u16(bytes, toff + 6) as usize;

            for j in 0..rcount {
                let roff = ref_list_off + j * 12;
                let rid = read_i16(bytes, roff);
                let rdoff = (((bytes[roff + 5] as usize) << 16)
                    | ((bytes[roff + 6] as usize) << 8)
                    | (bytes[roff + 7] as usize))
                    + data_off;
                let rlen = read_u32(bytes, rdoff) as usize;
                let rdata = &bytes[rdoff + 4..rdoff + 4 + rlen];

                if rtype == b"ICON" && rdata.len() >= 128 {
                    let mut arr = [0u8; 128];
                    arr.copy_from_slice(&rdata[..128]);
                    icons.insert(rid, arr);
                } else if rtype == b"DLOG" && rdata.len() >= 21 {
                    let t = read_i16(rdata, 0) as i32;
                    let l = read_i16(rdata, 2) as i32;
                    let b = read_i16(rdata, 4) as i32;
                    let r = read_i16(rdata, 6) as i32;
                    let proc_id = read_i16(rdata, 8);
                    let items_id = read_i16(rdata, 18);
                    let tlen = rdata[20] as usize;
                    let title = read_mac_str(&rdata[21..(21 + tlen).min(rdata.len())]);
                    dlogs.insert(
                        rid,
                        DlogRes {
                            rect: Rect { l, t, r, b },
                            proc_id,
                            items_id,
                            title,
                        },
                    );
                } else if rtype == b"DITL" && rdata.len() >= 2 {
                    let count = (read_u16(rdata, 0) + 1) as usize;
                    let mut pos = 2;
                    let mut items = Vec::new();
                    for idx in 1..=count {
                        if pos + 14 > rdata.len() {
                            break;
                        }
                        let t = read_i16(rdata, pos + 4) as i32;
                        let l = read_i16(rdata, pos + 6) as i32;
                        let b = read_i16(rdata, pos + 8) as i32;
                        let r = read_i16(rdata, pos + 10) as i32;
                        let itype = rdata[pos + 12];
                        let ilen = rdata[pos + 13] as usize;
                        pos += 14;
                        let idata = &rdata[pos..(pos + ilen).min(rdata.len())];
                        pos += ilen;
                        if pos % 2 == 1 {
                            pos += 1;
                        }
                        let kind = itype & 0x7F;
                        let mut val_str = String::new();
                        let mut val_id = 0i16;
                        if matches!(kind, 4 | 5 | 6 | 8 | 16) {
                            val_str = read_mac_str(idata);
                        } else if matches!(kind, 7 | 32) && idata.len() >= 2 {
                            val_id = read_i16(idata, 0);
                        }
                        items.push(DitlItem {
                            index: idx,
                            rect: Rect { l, t, r, b },
                            kind,
                            val_str,
                            val_id,
                        });
                    }
                    ditls.insert(rid, items);
                }
            }
        }
        Self {
            icons,
            dlogs,
            ditls,
        }
    }
}

struct Rng(u64);
impl Rng {
    fn new() -> Self {
        Self(0x853C_49E6_748F_EA9B)
    }
    fn next_u32(&mut self) -> u32 {
        self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1);
        (self.0 >> 32) as u32
    }
    fn range(&mut self, max: usize) -> usize {
        if max == 0 {
            0
        } else {
            (self.next_u32() as usize) % max
        }
    }
    fn chance(&mut self, pct: u32) -> bool {
        (self.next_u32() % 100) < pct
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum GameMode {
    Message,
    Street,
    Building,
    Modal,
    Endgame,
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum ModalKind {
    Dlog(i16),
    BribeMoney,
    Persuade(u16, i32),
    Decision(u8),
}

#[derive(Clone, Copy)]
struct MistressSlot {
    active: bool,
    cid: u16,
    stage: u8,
}

struct MenuItem {
    name: &'static str,
    enabled: bool,
    action: &'static str,
}

struct MenuDef {
    title: &'static str,
    x: i32,
    w: i32,
    items: Vec<MenuItem>,
}

const STOCK_NAMES: [&str; 6] = [
    "Widget Company",
    "Bank",
    "Allen Office Building",
    "Butler Office Building",
    "Newspaper",
    "Country Club",
];
const STOCK_BASE_VAL: [i64; 6] = [12000, 12000, 1200, 1200, 1200, 1200];

fn building_chars(dlog_id: i16) -> &'static [(usize, u16)] {
    match dlog_id {
        7000 => &[(1, 742), (2, 741), (3, 734), (4, 708), (5, 724)],
        7001 => &[
            (1, 700),
            (2, 701),
            (3, 709),
            (4, 712),
            (5, 714),
            (6, 703),
            (7, 704),
            (8, 735),
            (9, 724),
        ],
        7002 => &[
            (1, 724),
            (2, 702),
            (3, 705),
            (4, 706),
            (5, 733),
            (6, 736),
            (7, 721),
            (8, 723),
            (9, 729),
        ],
        7003 => &[
            (1, 724),
            (2, 711),
            (3, 740),
            (4, 715),
            (5, 722),
            (6, 718),
            (7, 732),
            (8, 730),
            (9, 737),
        ],
        7004 => &[
            (1, 724),
            (2, 710),
            (3, 728),
            (4, 731),
            (5, 726),
            (6, 738),
            (7, 720),
        ],
        7005 => &[
            (1, 724),
            (2, 713),
            (3, 716),
            (4, 717),
            (5, 725),
            (6, 727),
            (7, 707),
            (8, 719),
            (9, 739),
            (10, 743),
        ],
        _ => &[],
    }
}

struct MacNastyApp {
    rsrc: ResourceFork,
    fb: Vec<u8>, // 512 * 342 (0 = white, 1 = black)
    rng: Rng,
    mode: GameMode,
    current_building: Option<i16>,
    selected_radio: usize,
    selected_char: u16,
    age: i32,
    turn_in_year: u32,
    p_shares: [i64; 6],
    p_cash: i64,
    p_worth: i64,
    p_debt: i64,
    p_prestige: i32,
    r_shares: [i64; 6],
    r_cash: i64,
    r_worth: i64,
    r_debt: i64,
    r_prestige: i32,
    market_shares: [i64; 6],
    buy_offer_lots: [i64; 6],
    rel: [i32; 44],
    detective_known: [bool; 44],
    mistresses: [MistressSlot; 3],
    trusts_owned: [bool; 4],
    boards_owned: [bool; 2],
    is_mayor: bool,
    message_lines: Vec<String>,
    after_msg_open_7008: bool,
    after_msg_advance_turn: bool,
    after_msg_persuade: Option<(u16, i32)>,
    modal: Option<ModalKind>,
    modal_rad1: usize,
    modal_rad2: usize,
    modal_scroll: i64,
    modal_prompt: Vec<String>,
    menus: Vec<MenuDef>,
    open_menu: Option<usize>,
    hover_item: Option<usize>,
    endgame_won: bool,
    anim_tick: u64,
}

fn fmt_money(val: i64) -> String {
    let neg = val < 0;
    let s = val.abs().to_string();
    let mut out = String::new();
    for (i, c) in s.chars().rev().enumerate() {
        if i > 0 && i % 3 == 0 {
            out.push(',');
        }
        out.push(c);
    }
    let formatted: String = out.chars().rev().collect();
    if neg {
        format!("-${}", formatted)
    } else {
        format!("${}", formatted)
    }
}

impl MacNastyApp {
    fn new() -> Self {
        let rsrc = ResourceFork::parse(RSRC_BYTES);
        let menus = vec![
            MenuDef {
                title: "@",
                x: 10,
                w: 24,
                items: vec![
                    MenuItem {
                        name: "About MacNasty...",
                        enabled: true,
                        action: "about",
                    },
                    MenuItem {
                        name: "-",
                        enabled: false,
                        action: "",
                    },
                    MenuItem {
                        name: "Shareware Notice...",
                        enabled: true,
                        action: "shareware",
                    },
                ],
            },
            MenuDef {
                title: "Action",
                x: 42,
                w: 52,
                items: vec![
                    MenuItem {
                        name: "Score",
                        enabled: true,
                        action: "score",
                    },
                    MenuItem {
                        name: "Next Person",
                        enabled: false,
                        action: "next_person",
                    },
                    MenuItem {
                        name: "Leave Building",
                        enabled: false,
                        action: "leave_building",
                    },
                    MenuItem {
                        name: "Pass",
                        enabled: true,
                        action: "pass",
                    },
                    MenuItem {
                        name: "Quit",
                        enabled: true,
                        action: "quit",
                    },
                ],
            },
            MenuDef {
                title: "Property",
                x: 102,
                w: 64,
                items: vec![
                    MenuItem {
                        name: "Buy",
                        enabled: true,
                        action: "buy",
                    },
                    MenuItem {
                        name: "Sell",
                        enabled: true,
                        action: "sell",
                    },
                    MenuItem {
                        name: "Borrow",
                        enabled: true,
                        action: "borrow",
                    },
                ],
            },
            MenuDef {
                title: "Info",
                x: 174,
                w: 38,
                items: vec![
                    MenuItem {
                        name: "Public Facts",
                        enabled: false,
                        action: "info_public",
                    },
                    MenuItem {
                        name: "Rumors",
                        enabled: false,
                        action: "info_rumors",
                    },
                    MenuItem {
                        name: "Private Detective",
                        enabled: false,
                        action: "info_detective",
                    },
                ],
            },
            MenuDef {
                title: "Bribe",
                x: 220,
                w: 46,
                items: vec![
                    MenuItem {
                        name: "Money",
                        enabled: false,
                        action: "bribe_money",
                    },
                    MenuItem {
                        name: "Favors",
                        enabled: false,
                        action: "bribe_favors",
                    },
                    MenuItem {
                        name: "Charm",
                        enabled: false,
                        action: "bribe_charm",
                    },
                    MenuItem {
                        name: "Seduce",
                        enabled: false,
                        action: "bribe_seduce",
                    },
                ],
            },
            MenuDef {
                title: "Blackmail",
                x: 274,
                w: 72,
                items: vec![
                    MenuItem {
                        name: "Threaten disclosure",
                        enabled: false,
                        action: "bm_threaten",
                    },
                    MenuItem {
                        name: "Start Rumors",
                        enabled: false,
                        action: "bm_rumors",
                    },
                    MenuItem {
                        name: "Spouse's Secrets",
                        enabled: false,
                        action: "bm_spouse",
                    },
                ],
            },
        ];

        let mut app = Self {
            rsrc,
            fb: vec![0; MAC_W * MAC_H],
            rng: Rng::new(),
            mode: GameMode::Message,
            current_building: None,
            selected_radio: 1,
            selected_char: 724,
            age: 30,
            turn_in_year: 0,
            p_shares: [0; 6],
            p_cash: 150_000,
            p_worth: 150_000,
            p_debt: 0,
            p_prestige: 0,
            r_shares: [50, 50, 50, 0, 50, 50],
            r_cash: 400_000,
            r_worth: 1_780_000,
            r_debt: 0,
            r_prestige: 500,
            market_shares: [950, 950, 950, 1000, 950, 950],
            buy_offer_lots: [1, 10, 1, 10, 5, 10],
            rel: [0; 44],
            detective_known: [false; 44],
            mistresses: [MistressSlot {
                active: false,
                cid: 0,
                stage: 0,
            }; 3],
            trusts_owned: [false; 4],
            boards_owned: [false; 2],
            is_mayor: false,
            message_lines: vec![
                "Welcome to Tumbleweed, Texas.".to_string(),
                "".to_string(),
                "You have just inherited $150,000 and an old oil property from".to_string(),
                "your uncle Sawdust MacNasty who lived in Tumbleweed. You have".to_string(),
                "decided to move to Tumbleweed with your wife, the perpetually".to_string(),
                "bored ex-debutante Mona and become one of the town's most".to_string(),
                "powerful citizens. You soon find that there has been a running".to_string(),
                "feud between the MacNastys and the MacRascals for several gen-".to_string(),
                "erations now and that Mac MacRascal, the town boss, wants to".to_string(),
                "carry it on against you.".to_string(),
            ],
            after_msg_open_7008: true,
            after_msg_advance_turn: false,
            after_msg_persuade: None,
            modal: None,
            modal_rad1: 3,
            modal_rad2: 10,
            modal_scroll: 2000,
            modal_prompt: Vec::new(),
            menus,
            open_menu: None,
            hover_item: None,
            endgame_won: false,
            anim_tick: 0,
        };
        app.update_menus();
        app
    }

    fn recalc_worth(&mut self) {
        let mut ps = 0i64;
        let mut rs = 0i64;
        for i in 0..6 {
            ps += self.p_shares[i] * STOCK_BASE_VAL[i];
            rs += self.r_shares[i] * STOCK_BASE_VAL[i];
        }
        self.p_worth = self.p_cash + ps - self.p_debt;
        self.r_worth = self.r_cash + rs - self.r_debt;
    }

    fn cat_influence(&self, cat: u16) -> i32 {
        let mut sum = 0;
        for ch in &CHARS_DB {
            if ch.cat == cat {
                let idx = (ch.id - 700) as usize;
                let sp_idx = (ch.spouse_id - 700) as usize;
                sum += self.rel[idx] * 2 + self.rel[sp_idx];
            }
        }
        sum
    }

    fn clamp_rel(&mut self, cid: u16, delta: i32) {
        let idx = cid.saturating_sub(700) as usize;
        if idx < 44 {
            self.rel[idx] = (self.rel[idx] + delta).clamp(-20, 25);
        }
    }

    fn update_menus(&mut self) {
        let in_bldg = self.mode == GameMode::Building;
        let in_map_or_bldg = matches!(self.mode, GameMode::Street | GameMode::Building);
        self.menus[1].items[0].enabled = in_map_or_bldg;
        self.menus[1].items[1].enabled = in_bldg;
        self.menus[1].items[2].enabled = in_bldg;
        self.menus[1].items[3].enabled = in_map_or_bldg;
        for it in &mut self.menus[2].items {
            it.enabled = in_map_or_bldg;
        }
        for it in &mut self.menus[3].items {
            it.enabled = in_bldg;
        }
        for it in &mut self.menus[4].items {
            it.enabled = in_bldg;
        }
        for it in &mut self.menus[5].items {
            it.enabled = in_bldg;
        }
    }

    fn show_msg(&mut self, lines: Vec<String>, adv_turn: bool, persuade: Option<(u16, i32)>) {
        self.message_lines = lines;
        self.after_msg_open_7008 = false;
        self.after_msg_advance_turn = adv_turn;
        self.after_msg_persuade = persuade;
        self.mode = GameMode::Message;
        self.update_menus();
    }

    fn assign_mistress(&mut self, cid: u16) {
        for slot in &self.mistresses {
            if slot.active && slot.cid == cid {
                return;
            }
        }
        for slot in &mut self.mistresses {
            if !slot.active {
                *slot = MistressSlot {
                    active: true,
                    cid,
                    stage: 1,
                };
                return;
            }
        }
        let dumped = self.mistresses[0].cid;
        self.clamp_rel(dumped, -10);
        self.mistresses[0] = self.mistresses[1];
        self.mistresses[1] = self.mistresses[2];
        self.mistresses[2] = MistressSlot {
            active: true,
            cid,
            stage: 1,
        };
    }

    fn roll_buy_offers(&mut self) {
        let choices = [0i64, 1, 5, 10];
        for i in 0..6 {
            let mut pick = choices[self.rng.range(4)];
            if pick > self.market_shares[i] {
                pick = if self.market_shares[i] >= 10 {
                    10
                } else if self.market_shares[i] >= 5 {
                    5
                } else if self.market_shares[i] >= 1 {
                    1
                } else {
                    0
                };
            }
            self.buy_offer_lots[i] = pick;
        }
    }

    fn handle_menu_action(&mut self, action: &str) {
        let cid = self.selected_char;
        let ch = get_char(cid);
        match action {
            "about" => {
                self.show_msg(
                    vec![
                        "MacNasty - Version 1.00 (1987)".into(),
                        "Original 68000 Macintosh Game by George Lott".into(),
                        "P.O. Box 13834, Arlington, TX 76013".into(),
                        "".into(),
                        "Native Windows Rust Port powered directly by".into(),
                        "the original MacNasty_.rsrc Resource Fork.".into(),
                    ],
                    false,
                    None,
                );
            }
            "shareware" => {
                self.modal = Some(ModalKind::Dlog(7008));
                self.mode = GameMode::Modal;
                self.update_menus();
            }
            "score" => {
                self.recalc_worth();
                self.modal = Some(ModalKind::Dlog(6002));
                self.mode = GameMode::Modal;
                self.update_menus();
            }
            "next_person" => {
                if let Some(bldg) = self.current_building {
                    let list = building_chars(bldg);
                    if !list.is_empty() {
                        self.selected_radio = (self.selected_radio % list.len()) + 1;
                        self.selected_char = list[self.selected_radio - 1].1;
                    }
                }
            }
            "leave_building" => {
                self.current_building = None;
                self.selected_char = 724;
                self.mode = GameMode::Street;
                self.update_menus();
            }
            "pass" => self.advance_turn(),
            "quit" => self.trigger_endgame(),
            "buy" => {
                self.roll_buy_offers();
                self.modal_rad1 = 3;
                self.modal = Some(ModalKind::Dlog(6000));
                self.mode = GameMode::Modal;
                self.update_menus();
            }
            "sell" => {
                self.modal_rad1 = 4;
                self.modal_rad2 = 10;
                self.modal = Some(ModalKind::Dlog(6001));
                self.mode = GameMode::Modal;
                self.update_menus();
            }
            "borrow" => {
                self.modal_rad1 = 3;
                self.modal = Some(ModalKind::Dlog(6010));
                self.mode = GameMode::Modal;
                self.update_menus();
            }
            "info_public" => {
                let mut lines = Vec::new();
                for l in &ch.pub_lines {
                    if !l.is_empty() {
                        lines.push((*l).to_string());
                    }
                }
                self.show_msg(lines, false, None);
            }
            "info_rumors" => {
                let rep = if !ch.rep_str.is_empty() {
                    format!("{}'s reputation is: {}.", ch.name, ch.rep_str)
                } else {
                    format!("{} has no special reputation.", ch.name)
                };
                let rum = if !ch.rumor_str.is_empty() {
                    format!("The rumor around town is: {}.", ch.rumor_str)
                } else {
                    format!("There are no rumors about {}.", ch.name)
                };
                self.show_msg(vec![rep, rum], false, None);
            }
            "info_detective" => {
                if self.p_cash < 500 {
                    self.show_msg(
                        vec!["The Private Detective requires $500 up front.".into()],
                        false,
                        None,
                    );
                    return;
                }
                self.p_cash -= 500;
                self.recalc_worth();
                self.detective_known[(cid - 700) as usize] = true;
                let secret_line = if ch.secret_id == 850 && !ch.lover_name.is_empty() {
                    format!("SECRET REPORT: {}'s secret lover is {}!", ch.name, ch.lover_name)
                } else if !ch.secret_str.is_empty() {
                    format!("SECRET REPORT: {} {}", ch.name, ch.secret_str)
                } else {
                    format!("SECRET REPORT: {} is squeaky clean. Nothing found.", ch.name)
                };
                self.show_msg(
                    vec![
                        format!("The Private Detective investigates {} ($500)...", ch.name),
                        secret_line,
                    ],
                    true,
                    None,
                );
            }
            "bribe_money" => {
                if cid == 724 {
                    self.show_msg(vec!["You cannot bribe yourself, Max.".into()], false, None);
                    return;
                }
                self.modal_scroll = 2000;
                self.modal = Some(ModalKind::BribeMoney);
                self.mode = GameMode::Modal;
                self.update_menus();
            }
            "bribe_favors" => {
                if cid == 724 {
                    return;
                }
                if ch.vuln_favors {
                    self.show_msg(
                        vec![
                            format!("{} gladly accepts your offer of a political favor!", ch.name),
                            "\"One hand washes the other, Max.\"".into(),
                        ],
                        false,
                        Some((cid, 1)),
                    );
                } else {
                    self.clamp_rel(cid, -2);
                    self.show_msg(
                        vec![
                            format!("{} turns down your offer of favors coldly.", ch.name),
                            "\"I don't need anything from you, MacNasty.\"".into(),
                        ],
                        true,
                        None,
                    );
                }
            }
            "bribe_charm" => {
                if cid == 724 {
                    return;
                }
                if ch.vuln_charm {
                    self.show_msg(
                        vec![
                            "You turn on the famous MacNasty Texas charm.".into(),
                            format!("{} is completely flattered!", ch.name),
                        ],
                        false,
                        Some((cid, 1)),
                    );
                } else {
                    self.clamp_rel(cid, -1);
                    self.show_msg(
                        vec![
                            format!("{} sees right through your flattery.", ch.name),
                            "\"Save the sweet talk for someone else, Max.\"".into(),
                        ],
                        true,
                        None,
                    );
                }
            }
            "bribe_seduce" => {
                if cid % 2 == 0 {
                    self.show_msg(
                        vec!["No, no. We don't do that kind of thing around here.".into()],
                        false,
                        None,
                    );
                    return;
                }
                if cid == 725 {
                    self.show_msg(vec!["Forget it Max, you turn me off.".into()], false, None);
                    return;
                }
                self.p_cash -= 300;
                self.recalc_worth();
                let ok = ch.vuln_charm
                    || ch.has_affair
                    || matches!(cid, 719 | 727 | 733 | 737)
                    || self.rng.chance(35);
                if ok {
                    let line1 = if cid == 727 {
                        self.p_prestige += 10;
                        "You seduced MacRascal's wife Marta! (+10 Prestige!)".to_string()
                    } else {
                        format!("You wine and dine {} ($300) and seduce her!", ch.name)
                    };
                    self.assign_mistress(cid);
                    self.show_msg(
                        vec![
                            line1,
                            format!("{} is now one of your secret mistresses.", ch.name),
                        ],
                        false,
                        Some((cid, 2)),
                    );
                } else {
                    self.clamp_rel(cid, -4);
                    self.clamp_rel(ch.spouse_id, -4);
                    self.p_prestige -= 5;
                    self.show_msg(
                        vec![
                            format!("{} slaps your face and rejects your advances!", ch.name),
                            "You spent $300 and lost 5 prestige points.".into(),
                        ],
                        true,
                        None,
                    );
                }
            }
            "bm_threaten" => {
                if cid == 724 {
                    return;
                }
                let known = self.detective_known[(cid - 700) as usize] || ch.rumor_id == 801;
                if ch.vuln_blackmail && known {
                    self.show_msg(
                        vec![
                            format!("You threaten to expose {}'s secret to the town!", ch.name),
                            format!("{} turns pale: \"All right, Max! What do you want?\"", ch.name),
                        ],
                        false,
                        Some((cid, 2)),
                    );
                } else if ch.vuln_blackmail && !known {
                    self.show_msg(
                        vec![
                            format!("You try to bluff {}, but without proof from", ch.name),
                            "the Private Detective, your bluff fails!".into(),
                        ],
                        true,
                        None,
                    );
                } else {
                    self.clamp_rel(cid, -5);
                    self.p_prestige -= 5;
                    self.show_msg(
                        vec![
                            format!("{} laughs at your threats!", ch.name),
                            "\"Publish whatever you want, MacNasty!\" (-5 prestige)".into(),
                        ],
                        true,
                        None,
                    );
                }
            }
            "bm_rumors" => {
                if cid == 724 {
                    return;
                }
                self.p_cash -= 200;
                self.recalc_worth();
                if self.cat_influence(453) >= 0 || self.rng.chance(55) {
                    self.clamp_rel(cid, 3);
                    self.p_prestige += 5;
                    self.show_msg(
                        vec![
                            format!("You pay $200 to plant nasty rumors about {}", ch.name),
                            "in the Tumbleweed Newspaper!".into(),
                            format!("{} begs you to call off the reporters.", ch.name),
                        ],
                        false,
                        Some((cid, 1)),
                    );
                } else {
                    self.clamp_rel(cid, -4);
                    self.show_msg(
                        vec![
                            format!("You spend $200 starting rumors about {},", ch.name),
                            "but the reporters trace the story back to you!".into(),
                        ],
                        true,
                        None,
                    );
                }
            }
            "bm_spouse" => {
                let sp = get_char(ch.spouse_id);
                if ch.vuln_spouse_sec && sp.secret_id != 0 {
                    self.show_msg(
                        vec![
                            format!("You threaten to expose {}'s dark secret", sp.name),
                            format!("({})!", sp.secret_str),
                            format!("{} pleads with you to keep quiet and agrees to help!", ch.name),
                        ],
                        false,
                        Some((cid, 2)),
                    );
                } else {
                    self.clamp_rel(cid, -3);
                    self.show_msg(
                        vec![format!(
                            "{} ignores your threats against {}!",
                            ch.name, sp.name
                        )],
                        true,
                        None,
                    );
                }
            }
            _ => {}
        }
    }

    fn advance_turn(&mut self) {
        self.turn_in_year += 1;
        if self.turn_in_year >= 4 {
            self.turn_in_year = 0;
            self.age += 1;
            let mut div = 0i64;
            div += self.p_shares[0] * 1200;
            div += self.p_shares[1] * 1200;
            div += self.p_shares[2] * 150;
            div += self.p_shares[3] * 150;
            div += self.p_shares[4] * 150;
            div += self.p_shares[5] * 150;
            for &t in &self.trusts_owned {
                if t {
                    div += 12000;
                }
            }
            for &b in &self.boards_owned {
                if b {
                    div += 10000;
                }
            }
            if self.is_mayor {
                div += 15000;
                self.p_prestige += 15;
            }
            let interest = self.p_debt / 10;
            self.p_cash += div - interest;
            self.r_cash += 65_000;
            self.r_prestige += 12;
            for si in 0..6 {
                if self.market_shares[si] >= 5
                    && self.r_cash >= STOCK_BASE_VAL[si] * 5
                    && self.rng.chance(35)
                {
                    self.r_shares[si] += 5;
                    self.market_shares[si] -= 5;
                    self.r_cash -= STOCK_BASE_VAL[si] * 5;
                }
            }
            self.recalc_worth();
            if self.p_cash < -50_000 || self.p_worth < -100_000 {
                self.trigger_endgame();
                return;
            }
            if self.age >= 70 {
                self.trigger_endgame();
                return;
            }
        }

        // Check mistress events (CODE_20)
        for i in 0..3 {
            if self.mistresses[i].active && self.rng.chance(25) {
                let cid = self.mistresses[i].cid;
                let mname = get_char(cid).name;
                if self.mistresses[i].stage == 1 {
                    self.mistresses[i].stage = 2;
                    self.p_cash -= 500;
                    self.recalc_worth();
                    self.show_msg(
                        vec![
                            format!("Your mistress {} demands a fancy gift", mname),
                            "to keep her happy. It costs you $500.".into(),
                        ],
                        false,
                        None,
                    );
                    return;
                } else {
                    self.mistresses[i].active = false;
                    self.show_msg(
                        vec![
                            format!("Your affair with {} has quietly run its course.", mname),
                            "You part ways on friendly terms.".into(),
                        ],
                        false,
                        None,
                    );
                    return;
                }
            }
        }

        if self.rng.chance(45) {
            self.trigger_random_event();
        }
        self.recalc_worth();
    }

    fn trigger_random_event(&mut self) {
        let roll = self.rng.range(8);
        match roll {
            0 => {
                // Trust appointment
                let trust_inf = self.cat_influence(455) + self.cat_influence(462);
                if trust_inf > 2 {
                    self.trusts_owned[0] = true;
                    self.p_cash += 15_000;
                    self.p_prestige += 25;
                    self.show_msg(
                        vec![
                            "The Bank Trust Officers and Judges appointed you".into(),
                            "Trustee of the Emil J. Aardvark Trust!".into(),
                            "You receive $15,000 and 25 prestige points.".into(),
                        ],
                        false,
                        None,
                    );
                } else {
                    self.r_cash += 15_000;
                    self.r_prestige += 20;
                    self.show_msg(
                        vec![
                            "You and MacRascal competed to be Trustee of the".into(),
                            "Emil J. Aardvark Trust, but MacRascal won!".into(),
                        ],
                        false,
                        None,
                    );
                }
            }
            1 => {
                // Consulting contract
                if self.cat_influence(464) > 2 {
                    self.p_cash += 20_000;
                    self.p_prestige += 15;
                    self.show_msg(
                        vec![
                            "Tumbleweed Bank awarded you a $20,000 consulting".into(),
                            "contract over Mac MacRascal! (+15 prestige)".into(),
                        ],
                        false,
                        None,
                    );
                } else {
                    self.r_cash += 20_000;
                    self.show_msg(
                        vec![
                            "You competed for a $20,000 Bank consulting fee,".into(),
                            "but Bank President Dan Davis gave it to MacRascal!".into(),
                        ],
                        false,
                        None,
                    );
                }
            }
            2 => {
                // Mona scandal
                self.p_prestige -= 5;
                self.show_msg(
                    vec![
                        "You had a fight with your wife Mona.".into(),
                        "She went to a bar, got drunk, and danced on the table".into(),
                        "in her underwear. You lose 5 prestige points.".into(),
                    ],
                    false,
                    None,
                );
            }
            3 => {
                // Oil gusher
                self.p_cash += 30_000;
                self.p_prestige += 15;
                self.show_msg(
                    vec![
                        "GUSHER! Uncle Sawdust's old oil lease struck a new".into(),
                        "pocket of crude! You make $30,000 and 15 prestige!".into(),
                    ],
                    false,
                    None,
                );
            }
            4 => {
                // Horse Race bet (DLOG 7007)
                self.modal_prompt = vec![
                    "Mac MacRascal walks up to you at the Country Club:".into(),
                    "\"Say Max, care to bet $5,000 on my horse Lightning".into(),
                    "in the Tumbleweed Derby today?\"".into(),
                ];
                self.modal = Some(ModalKind::Decision(1));
                self.mode = GameMode::Modal;
                self.update_menus();
            }
            5 => {
                // Old Gray poisoned racehorse bet (DLOG 7007)
                self.modal_prompt = vec![
                    "MacRascal offers to bet you $20,000 that his nag can".into(),
                    "beat the undefeated champion horse 'Old Gray'!".into(),
                    "Do you take the $20,000 bet?".into(),
                ];
                self.modal = Some(ModalKind::Decision(2));
                self.mode = GameMode::Modal;
                self.update_menus();
            }
            6 => {
                // J. Marmaduke Dirty pipeline scheme (DLOG 7007)
                self.modal_prompt = vec![
                    "Fraternity brother J. Marmaduke Dirty whispers:".into(),
                    "\"Max! For $5,000 we can tap the pipeline and siphon".into(),
                    "$25,000 worth of oil! Are you in?\"".into(),
                ];
                self.modal = Some(ModalKind::Decision(3));
                self.mode = GameMode::Modal;
                self.update_menus();
            }
            _ => {
                // Lawsuit
                if self.cat_influence(461) + self.cat_influence(462) >= 3 {
                    self.p_prestige += 10;
                    self.show_msg(
                        vec![
                            "MacRascal's cronies sued you for $50,000 in Court,".into(),
                            "but your friendly Judges threw the case out! (+10 prestige)".into(),
                        ],
                        false,
                        None,
                    );
                } else {
                    self.p_cash -= 15_000;
                    self.p_prestige -= 10;
                    self.show_msg(
                        vec![
                            "You were sued for damages in Tumbleweed Court!".into(),
                            "You lost $15,000 and 10 prestige points.".into(),
                        ],
                        false,
                        None,
                    );
                }
            }
        }
    }

    fn trigger_endgame(&mut self) {
        self.recalc_worth();
        let p_score = self.p_worth + (self.p_prestige as i64) * 1000;
        let r_score = self.r_worth + (self.r_prestige as i64) * 1000;
        self.endgame_won = p_score >= r_score;
        self.mode = GameMode::Endgame;
        self.anim_tick = 0;
        self.update_menus();
    }

    // ========================================================================
    // DRAWING PRIMITIVES (512x342 1-bit Classic Mac System 6)
    // ========================================================================
    fn set_px(&mut self, x: i32, y: i32, black: bool) {
        if x >= 0 && x < MAC_W as i32 && y >= 0 && y < MAC_H as i32 {
            self.fb[y as usize * MAC_W + x as usize] = u8::from(black);
        }
    }

    fn fill_rect(&mut self, l: i32, t: i32, w: i32, h: i32, black: bool) {
        for y in t..(t + h) {
            for x in l..(l + w) {
                self.set_px(x, y, black);
            }
        }
    }

    fn stroke_rect(&mut self, l: i32, t: i32, w: i32, h: i32, black: bool) {
        for x in l..(l + w) {
            self.set_px(x, t, black);
            self.set_px(x, t + h - 1, black);
        }
        for y in t..(t + h) {
            self.set_px(l, y, black);
            self.set_px(l + w - 1, y, black);
        }
    }

    fn draw_text(&mut self, x: i32, y: i32, text: &str, invert: bool) {
        let mut cx = x;
        for ch in text.chars() {
            if let Some(glyph) = BASIC_FONTS.get(ch) {
                for (row, &bits) in glyph.iter().enumerate() {
                    for col in 0..8 {
                        if (bits >> col) & 1 != 0 {
                            self.set_px(cx + col, y + row as i32, !invert);
                        }
                    }
                }
            }
            cx += match ch {
                'i' | 'l' | '!' | '.' | ',' | '\'' | ':' | ';' | '|' => 4,
                'I' | 'j' | 't' | 'f' | 'r' | ' ' | '(' | ')' => 5,
                _ => 6,
            };
        }
    }

    fn text_width(text: &str) -> i32 {
        text.chars()
            .map(|ch| match ch {
                'i' | 'l' | '!' | '.' | ',' | '\'' | ':' | ';' | '|' => 4,
                'I' | 'j' | 't' | 'f' | 'r' | ' ' | '(' | ')' => 5,
                _ => 6,
            })
            .sum()
    }

    fn draw_icon(&mut self, icon_id: i16, dx: i32, dy: i32) {
        if let Some(&data) = self.rsrc.icons.get(&icon_id) {
            for y in 0..32 {
                let b0 = data[y * 4] as u32;
                let b1 = data[y * 4 + 1] as u32;
                let b2 = data[y * 4 + 2] as u32;
                let b3 = data[y * 4 + 3] as u32;
                let row = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3;
                for x in 0..32 {
                    let bit = ((row >> (31 - x)) & 1) != 0;
                    self.set_px(dx + x, dy + y as i32, bit);
                }
            }
        }
    }

    fn draw_window_frame(&mut self, l: i32, t: i32, w: i32, h: i32, title: &str, has_title: bool) {
        self.fill_rect(l + 2, t + 2, w, h, true);
        self.fill_rect(l, t, w, h, false);
        self.stroke_rect(l, t, w, h, true);
        if has_title {
            let th = 18;
            self.stroke_rect(l, t, w, th, true);
            for py in (t + 3..t + th - 2).step_by(2) {
                self.fill_rect(l + 4, py, w - 8, 1, true);
            }
            if !title.is_empty() {
                let tw = Self::text_width(title) + 12;
                let tx = l + (w - tw) / 2;
                self.fill_rect(tx, t + 2, tw, th - 4, false);
                self.draw_text(tx + 6, t + 5, title, false);
            }
        } else {
            self.stroke_rect(l + 3, t + 3, w - 6, h - 6, true);
        }
    }

    fn draw_radio(&mut self, l: i32, t: i32, w: i32, h: i32, label: &str, checked: bool) {
        self.fill_rect(l, t + 1, w, h - 2, false);
        let cx = l + 6;
        let cy = t + h / 2;
        for dy in -4i32..=4 {
            for dx in -4i32..=4 {
                let d2 = dx * dx + dy * dy;
                if (11..=20).contains(&d2) {
                    self.set_px(cx + dx, cy + dy, true);
                } else if d2 < 11 {
                    self.set_px(cx + dx, cy + dy, checked && d2 <= 4);
                }
            }
        }
        self.draw_text(l + 14, cy - 4, label, false);
    }

    fn draw_button(&mut self, l: i32, t: i32, w: i32, h: i32, label: &str) {
        self.fill_rect(l, t, w, h, false);
        self.stroke_rect(l, t, w, h, true);
        let tw = Self::text_width(label);
        self.draw_text(l + (w - tw) / 2, t + (h - 8) / 2, label, false);
    }

    fn render_ditl_window(&mut self, dlog_id: i16, rad1: usize, rad2: usize) {
        let Some(dlog) = self.rsrc.dlogs.get(&dlog_id).cloned() else {
            return;
        };
        let Some(ditl) = self.rsrc.ditls.get(&dlog.items_id).cloned() else {
            return;
        };
        let wx = dlog.rect.l;
        let wy = dlog.rect.t;
        let has_title = dlog.proc_id == 0 || dlog.proc_id == 4 || !dlog.title.is_empty();
        self.draw_window_frame(wx, wy, dlog.rect.w(), dlog.rect.h(), &dlog.title, has_title);

        for it in &ditl {
            if it.kind == 32 && it.val_id != 0 {
                self.draw_icon(it.val_id, wx + it.rect.l, wy + it.rect.t);
            }
        }
        for it in &ditl {
            let ix = wx + it.rect.l;
            let iy = wy + it.rect.t;
            let iw = it.rect.w();
            let ih = it.rect.h();
            if it.kind == 5 || it.kind == 6 {
                let checked = it.index == rad1 || it.index == rad2;
                self.draw_radio(ix, iy, iw, ih, &it.val_str, checked);
            } else if it.kind == 4 {
                self.draw_button(ix, iy, iw, ih, &it.val_str);
            } else if it.kind == 8 {
                let txt = if dlog_id == 6002 {
                    match it.index {
                        8 => fmt_money(self.p_cash),
                        9 => fmt_money(self.r_cash),
                        10 => fmt_money(self.p_debt),
                        11 => fmt_money(self.r_debt),
                        12 => fmt_money(self.p_worth),
                        13 => fmt_money(self.r_worth),
                        14 => self.p_prestige.to_string(),
                        15 => self.r_prestige.to_string(),
                        17 => self.age.to_string(),
                        _ => it.val_str.clone(),
                    }
                } else if dlog_id == 6000 && (9..=14).contains(&it.index) {
                    format!("{:02}", self.buy_offer_lots[it.index - 9])
                } else if dlog_id == 6001 && (16..=21).contains(&it.index) {
                    self.p_shares[it.index - 16].to_string()
                } else {
                    it.val_str.clone()
                };
                self.draw_text(ix, iy + 4, &txt, false);
            }
        }
    }

    fn render(&mut self) {
        // Desktop 50% gray checkerboard
        for y in 0..MAC_H as i32 {
            for x in 0..MAC_W as i32 {
                let black = y >= 20 && ((x + y) & 1 == 0);
                self.set_px(x, y, black);
            }
        }

        match self.mode {
            GameMode::Message => {
                self.draw_window_frame(7, 46, 498, 290, "Message", true);
                let lines = self.message_lines.clone();
                for (i, ln) in lines.iter().enumerate() {
                    self.draw_text(35, 80 + (i as i32) * 18, ln, false);
                }
                self.draw_text(165, 305, "(Click anywhere to continue)", false);
            }
            GameMode::Street => {
                self.render_ditl_window(7006, 0, 0);
            }
            GameMode::Building => {
                if let Some(bldg) = self.current_building {
                    self.render_ditl_window(bldg, self.selected_radio, 0);
                }
            }
            GameMode::Modal => {
                if let Some(bldg) = self.current_building {
                    self.render_ditl_window(bldg, self.selected_radio, 0);
                } else {
                    self.render_ditl_window(7006, 0, 0);
                }
                if let Some(mk) = self.modal {
                    match mk {
                        ModalKind::Dlog(id) => {
                            self.render_ditl_window(id, self.modal_rad1, self.modal_rad2);
                        }
                        ModalKind::Persuade(_, _) => {
                            self.render_ditl_window(6003, self.modal_rad1, 0);
                        }
                        ModalKind::Decision(_) => {
                            self.render_ditl_window(7007, 0, 0);
                            if let Some(dlog) = self.rsrc.dlogs.get(&7007).cloned() {
                                let lines = self.modal_prompt.clone();
                                for (i, ln) in lines.iter().enumerate() {
                                    self.draw_text(
                                        dlog.rect.l + 18,
                                        dlog.rect.t + 20 + (i as i32) * 16,
                                        ln,
                                        false,
                                    );
                                }
                            }
                        }
                        ModalKind::BribeMoney => {
                            let wx = 85;
                            let wy = 80;
                            self.draw_window_frame(wx, wy, 340, 160, "Bribe with Money", true);
                            let ch = get_char(self.selected_char);
                            self.draw_text(
                                wx + 22,
                                wy + 34,
                                &format!("How much money do you offer {}?", ch.name),
                                false,
                            );
                            self.draw_text(
                                wx + 115,
                                wy + 58,
                                &format!("Offer: {}", fmt_money(self.modal_scroll)),
                                false,
                            );
                            self.stroke_rect(wx + 30, wy + 85, 280, 16, true);
                            let thumb_x =
                                wx + 32 + ((self.modal_scroll as f64 / 10000.0) * 260.0) as i32;
                            self.fill_rect(thumb_x, wy + 87, 16, 12, true);
                            self.draw_text(wx + 30, wy + 106, "$0", false);
                            self.draw_text(wx + 150, wy + 106, "$5,000", false);
                            self.draw_text(wx + 272, wy + 106, "$10,000", false);
                            self.draw_button(wx + 75, wy + 125, 80, 22, "Offer Bribe");
                            self.draw_button(wx + 185, wy + 125, 80, 22, "Cancel");
                        }
                    }
                }
            }
            GameMode::Endgame => {
                self.draw_window_frame(7, 46, 498, 290, "End of the Road", true);
                if !self.endgame_won {
                    self.draw_text(
                        40,
                        85,
                        "Here you are at the end of your life. And what have you",
                        false,
                    );
                    self.draw_text(
                        40,
                        105,
                        "accomplished? Not much. Even though you were given a fine",
                        false,
                    );
                    self.draw_text(
                        40,
                        125,
                        "evil name to uphold, you let that upstart MacRascal beat you.",
                        false,
                    );
                    self.draw_button(200, 260, 110, 24, "Play Again");
                } else {
                    self.draw_text(
                        40,
                        75,
                        "Well Max, your life is over. Look around, someone is coming",
                        false,
                    );
                    self.draw_text(
                        40,
                        93,
                        "to meet you. Why, it's Mephistopheles! And he's brought a",
                        false,
                    );
                    self.draw_text(40, 111, "couple of his helpers:", false);
                    self.draw_text(
                        40,
                        136,
                        "\"Welcome to Hell, Max. You're our kind of guy. Follow me,",
                        false,
                    );
                    self.draw_text(40, 154, "we have a hot time in store for you!\"", false);

                    let bounce = (self.anim_tick / 15) % 2 == 0;
                    self.draw_icon(4002, 140, 180);
                    self.draw_icon(4003, 140, 212);
                    self.draw_icon(4004, 240, 180);
                    self.draw_icon(if bounce { 4005 } else { 4007 }, 240, 212);
                    self.draw_icon(if bounce { 4006 } else { 4008 }, 240, 244);
                    self.draw_icon(4004, 330, 180);
                    self.draw_icon(if bounce { 4009 } else { 4011 }, 330, 212);
                    self.draw_icon(if bounce { 4010 } else { 4012 }, 330, 244);
                    self.draw_button(200, 292, 110, 24, "Play Again");
                }
            }
        }

        // Menu Bar
        self.fill_rect(0, 0, MAC_W as i32, 19, false);
        self.fill_rect(0, 19, MAC_W as i32, 1, true);
        for i in 0..self.menus.len() {
            let mx = self.menus[i].x;
            let mw = self.menus[i].w;
            let title = self.menus[i].title;
            let active = self.open_menu == Some(i);
            if active {
                self.fill_rect(mx, 1, mw, 18, true);
            }
            self.draw_text(mx + 6, 6, title, active);
        }

        if let Some(m_idx) = self.open_menu {
            let mx = self.menus[m_idx].x;
            let my = 20;
            let mw = 152;
            let count = self.menus[m_idx].items.len() as i32;
            let mh = count * 18 + 4;
            self.fill_rect(mx + 2, my + 2, mw, mh, true);
            self.fill_rect(mx, my, mw, mh, false);
            self.stroke_rect(mx, my, mw, mh, true);
            let items: Vec<(String, bool)> = self.menus[m_idx]
                .items
                .iter()
                .map(|it| (it.name.to_string(), it.enabled))
                .collect();
            for (j, (name, enabled)) in items.iter().enumerate() {
                let iy = my + 2 + (j as i32) * 18;
                if name == "-" {
                    self.fill_rect(mx + 2, iy + 8, mw - 4, 1, true);
                    continue;
                }
                let hov = self.hover_item == Some(j) && *enabled;
                if hov {
                    self.fill_rect(mx + 1, iy, mw - 2, 18, true);
                }
                self.draw_text(mx + 10, iy + 5, name, hov);
            }
        }
    }

    fn on_mouse_move(&mut self, x: i32, y: i32) {
        if let Some(m_idx) = self.open_menu {
            if y < 20 {
                for i in 0..self.menus.len() {
                    if x >= self.menus[i].x && x <= self.menus[i].x + self.menus[i].w {
                        self.open_menu = Some(i);
                        self.hover_item = None;
                        break;
                    }
                }
            } else {
                let mx = self.menus[m_idx].x;
                let my = 20;
                let mh = (self.menus[m_idx].items.len() as i32) * 18 + 4;
                if x >= mx && x <= mx + 152 && y >= my && y < my + mh {
                    self.hover_item = Some(((y - my - 2).max(0) / 18) as usize);
                } else {
                    self.hover_item = None;
                }
            }
        }
    }

    fn on_click(&mut self, x: i32, y: i32) {
        if let Some(m_idx) = self.open_menu {
            let mx = self.menus[m_idx].x;
            let my = 20;
            let mh = (self.menus[m_idx].items.len() as i32) * 18 + 4;
            if x >= mx && x <= mx + 152 && y >= my && y < my + mh {
                let idx = ((y - my - 2).max(0) / 18) as usize;
                self.open_menu = None;
                self.hover_item = None;
                if idx < self.menus[m_idx].items.len() && self.menus[m_idx].items[idx].enabled {
                    let act = self.menus[m_idx].items[idx].action;
                    self.handle_menu_action(act);
                }
                return;
            }
            self.open_menu = None;
            self.hover_item = None;
            if y < 20 {
                return;
            }
        }

        if y < 20 {
            for i in 0..self.menus.len() {
                if x >= self.menus[i].x && x <= self.menus[i].x + self.menus[i].w {
                    self.open_menu = Some(i);
                    self.hover_item = None;
                    return;
                }
            }
            return;
        }

        match self.mode {
            GameMode::Message => {
                if self.after_msg_open_7008 {
                    self.after_msg_open_7008 = false;
                    self.modal = Some(ModalKind::Dlog(7008));
                    self.mode = GameMode::Modal;
                } else if let Some((cid, weight)) = self.after_msg_persuade.take() {
                    self.modal_rad1 = 2;
                    self.modal = Some(ModalKind::Persuade(cid, weight));
                    self.mode = GameMode::Modal;
                } else {
                    let adv = self.after_msg_advance_turn;
                    self.after_msg_advance_turn = false;
                    self.mode = if self.current_building.is_some() {
                        GameMode::Building
                    } else {
                        GameMode::Street
                    };
                    if adv {
                        self.advance_turn();
                    }
                }
                self.update_menus();
            }
            GameMode::Endgame => {
                *self = Self::new();
            }
            GameMode::Street => {
                let Some(dlog) = self.rsrc.dlogs.get(&7006) else {
                    return;
                };
                let Some(ditl) = self.rsrc.ditls.get(&7006) else {
                    return;
                };
                let lx = x - dlog.rect.l;
                let ly = y - dlog.rect.t;
                let map = [
                    (1, 7002),
                    (2, 7001),
                    (3, 7004),
                    (4, 7000),
                    (5, 7003),
                    (6, 7005),
                ];
                for &(r_idx, bldg_id) in &map {
                    let r = ditl[r_idx - 1].rect;
                    if lx >= r.l - 30 && lx <= r.r + 30 && ly >= r.t - 90 && ly <= r.b + 20 {
                        self.current_building = Some(bldg_id);
                        self.selected_radio = 1;
                        self.selected_char = building_chars(bldg_id)[0].1;
                        self.mode = GameMode::Building;
                        self.update_menus();
                        return;
                    }
                }
            }
            GameMode::Building => {
                let Some(bldg) = self.current_building else {
                    return;
                };
                let Some(dlog) = self.rsrc.dlogs.get(&bldg) else {
                    return;
                };
                let Some(ditl) = self.rsrc.ditls.get(&bldg) else {
                    return;
                };
                let lx = x - dlog.rect.l;
                let ly = y - dlog.rect.t;
                for &(r_idx, cid) in building_chars(bldg) {
                    let r = ditl[r_idx - 1].rect;
                    if lx >= r.l - 8 && lx <= r.r + 8 && ly >= r.t - 68 && ly <= r.b + 4 {
                        self.selected_radio = r_idx;
                        self.selected_char = cid;
                        return;
                    }
                }
            }
            GameMode::Modal => self.on_modal_click(x, y),
        }
    }

    fn close_modal(&mut self) {
        self.modal = None;
        self.mode = if self.current_building.is_some() {
            GameMode::Building
        } else {
            GameMode::Street
        };
        self.update_menus();
    }

    fn on_modal_click(&mut self, x: i32, y: i32) {
        let Some(mk) = self.modal else {
            return;
        };
        if mk == ModalKind::BribeMoney {
            let wx = 85;
            let wy = 80;
            if x >= wx + 28 && x <= wx + 312 && y >= wy + 80 && y <= wy + 106 {
                let pct = ((x - (wx + 32)) as f64 / 260.0).clamp(0.0, 1.0);
                self.modal_scroll = ((pct * 10000.0) as i64 / 100) * 100;
                return;
            }
            if x >= wx + 75 && x <= wx + 155 && y >= wy + 125 && y <= wy + 147 {
                let amt = self.modal_scroll;
                self.close_modal();
                if amt > self.p_cash {
                    self.p_prestige -= 25;
                    self.show_msg(
                        vec![
                            "Your check bounced! You don't have enough cash.".into(),
                            "You lose 25 prestige points and forfeit a turn.".into(),
                        ],
                        true,
                        None,
                    );
                    return;
                }
                self.p_cash -= amt;
                self.recalc_worth();
                let cid = self.selected_char;
                let ch = get_char(cid);
                if ch.vuln_money && amt >= 1000 {
                    let w = if amt >= 5000 { 2 } else { 1 };
                    self.show_msg(
                        vec![
                            format!("{} pockets your {} with a smile!", ch.name, fmt_money(amt)),
                            "\"Pleasure doing business with you, Max.\"".into(),
                        ],
                        false,
                        Some((cid, w)),
                    );
                } else {
                    self.clamp_rel(cid, -2);
                    self.show_msg(
                        vec![format!(
                            "{} rejects your money bribe attempt!",
                            ch.name
                        )],
                        true,
                        None,
                    );
                }
                return;
            }
            if x >= wx + 185 && x <= wx + 265 && y >= wy + 125 && y <= wy + 147 {
                self.close_modal();
            }
            return;
        }

        let dlog_id = match mk {
            ModalKind::Dlog(id) => id,
            ModalKind::Persuade(_, _) => 6003,
            ModalKind::Decision(_) => 7007,
            ModalKind::BribeMoney => return,
        };
        let Some(dlog) = self.rsrc.dlogs.get(&dlog_id).cloned() else {
            return;
        };
        let Some(ditl) = self.rsrc.ditls.get(&dlog.items_id).cloned() else {
            return;
        };
        let lx = x - dlog.rect.l;
        let ly = y - dlog.rect.t;

        for it in &ditl {
            if it.rect.contains(lx, ly) {
                match mk {
                    ModalKind::Dlog(7008) => {
                        self.close_modal();
                        if it.index == 1 {
                            self.show_msg(
                                vec![
                                    "MacNasty is a shareware program.".into(),
                                    "If you enjoy playing MacNasty, send $15 to:".into(),
                                    "George Lott, P.O. Box 13834, Arlington, TX 76013".into(),
                                ],
                                false,
                                None,
                            );
                        }
                        return;
                    }
                    ModalKind::Dlog(6002) => {
                        if it.index == 1 {
                            self.close_modal();
                        }
                        return;
                    }
                    ModalKind::Persuade(cid, weight) => {
                        if (2..=6).contains(&it.index) {
                            self.modal_rad1 = it.index;
                        } else if it.index == 1 {
                            let choice = self.modal_rad1;
                            self.close_modal();
                            let ch = get_char(cid);
                            match choice {
                                2 => {
                                    self.clamp_rel(cid, 4 * weight);
                                    self.p_prestige += 5;
                                    self.show_msg(
                                        vec![format!(
                                            "{} agrees to support you personally!",
                                            ch.name
                                        )],
                                        true,
                                        None,
                                    );
                                }
                                3 => {
                                    let sp = get_char(ch.spouse_id);
                                    self.clamp_rel(ch.spouse_id, 4 * weight);
                                    self.show_msg(
                                        vec![format!(
                                            "{} puts in a good word with spouse {}!",
                                            ch.name, sp.name
                                        )],
                                        true,
                                        None,
                                    );
                                }
                                4 => {
                                    if ch.lover_id != 0 {
                                        self.clamp_rel(ch.lover_id, 5 * weight);
                                        self.p_prestige += 8;
                                        self.show_msg(
                                            vec![format!(
                                                "{} persuades secret lover {} to back you!",
                                                ch.name, ch.lover_name
                                            )],
                                            true,
                                            None,
                                        );
                                    } else {
                                        self.show_msg(
                                            vec![format!(
                                                "{} says: \"I don't have a secret lover!\"",
                                                ch.name
                                            )],
                                            true,
                                            None,
                                        );
                                    }
                                }
                                _ => {
                                    self.p_prestige += 10 * weight;
                                    self.clamp_rel(cid, 2);
                                    self.show_msg(
                                        vec![format!(
                                            "{} boosts your reputation around Tumbleweed!",
                                            ch.name
                                        )],
                                        true,
                                        None,
                                    );
                                }
                            }
                        }
                        return;
                    }
                    ModalKind::Decision(kind_id) => {
                        if it.index == 1 || it.index == 2 {
                            let yes = it.index == 1;
                            self.close_modal();
                            if !yes {
                                return;
                            }
                            match kind_id {
                                1 => {
                                    if self.rng.chance(50) {
                                        self.p_cash += 5_000;
                                        self.p_prestige += 5;
                                        self.show_msg(
                                            vec!["Your horse beat Lightning! You win $5,000!".into()],
                                            false,
                                            None,
                                        );
                                    } else {
                                        self.p_cash -= 5_000;
                                        self.show_msg(
                                            vec!["MacRascal's horse Lightning won! You lose $5,000.".into()],
                                            false,
                                            None,
                                        );
                                    }
                                }
                                2 => {
                                    if self.cat_influence(452) >= 4 {
                                        self.p_cash += 20_000;
                                        self.p_prestige += 25;
                                        self.show_msg(
                                            vec![
                                                "Police caught MacRascal trying to poison Old Gray!".into(),
                                                "Old Gray wins easily! You win $20,000 and 25 prestige!".into(),
                                            ],
                                            false,
                                            None,
                                        );
                                    } else {
                                        self.p_cash -= 20_000;
                                        self.p_prestige -= 10;
                                        self.show_msg(
                                            vec![
                                                "MacRascal poisoned Old Gray before the race!".into(),
                                                "You lose $20,000 and 10 prestige points!".into(),
                                            ],
                                            false,
                                            None,
                                        );
                                    }
                                }
                                _ => {
                                    if self.cat_influence(452) >= 2 || self.rng.chance(55) {
                                        self.p_cash += 25_000;
                                        self.show_msg(
                                            vec![
                                                "J. Marmaduke Dirty's oil pipeline tap succeeded!".into(),
                                                "You net $25,000 in clear profit!".into(),
                                            ],
                                            false,
                                            None,
                                        );
                                    } else {
                                        self.p_cash -= 20_000;
                                        self.p_prestige -= 15;
                                        self.show_msg(
                                            vec![
                                                "BUSTED! Police caught J. Marmaduke Dirty!".into(),
                                                "Fines and legal fees cost you $20,000 and 15 prestige!".into(),
                                            ],
                                            false,
                                            None,
                                        );
                                    }
                                }
                            }
                        }
                        return;
                    }
                    ModalKind::Dlog(6000) => {
                        if (3..=8).contains(&it.index) {
                            self.modal_rad1 = it.index;
                        } else if it.index == 2 {
                            self.close_modal();
                        } else if it.index == 1 {
                            let s_idx = self.modal_rad1 - 3;
                            let qty = self.buy_offer_lots[s_idx];
                            self.close_modal();
                            if qty <= 0 {
                                self.show_msg(
                                    vec!["No shares of that property are offered right now.".into()],
                                    false,
                                    None,
                                );
                                return;
                            }
                            let base = STOCK_BASE_VAL[s_idx];
                            let cost = base * qty;
                            if self.p_cash < cost {
                                self.p_prestige -= 50;
                                self.show_msg(
                                    vec![
                                        "Oops, you don't have enough money to buy this.".into(),
                                        "You lose 50 prestige points and forfeit a turn.".into(),
                                    ],
                                    true,
                                    None,
                                );
                                return;
                            }
                            self.p_cash -= cost;
                            self.p_shares[s_idx] += qty;
                            self.market_shares[s_idx] -= qty;
                            self.p_prestige += (qty as i32) * 2;
                            self.recalc_worth();
                            self.show_msg(
                                vec![
                                    format!(
                                        "Congratulations! You purchased {} share(s) of",
                                        qty
                                    ),
                                    format!(
                                        "the {} for {}.",
                                        STOCK_NAMES[s_idx],
                                        fmt_money(cost)
                                    ),
                                ],
                                true,
                                None,
                            );
                        }
                        return;
                    }
                    ModalKind::Dlog(6001) => {
                        if (4..=9).contains(&it.index) {
                            self.modal_rad1 = it.index;
                        } else if (10..=15).contains(&it.index) {
                            self.modal_rad2 = it.index;
                        } else if it.index == 2 {
                            self.close_modal();
                        } else if it.index == 1 {
                            let s_idx = self.modal_rad1 - 4;
                            let amounts = [1i64, 2, 5, 10, 25, 50];
                            let qty = amounts[self.modal_rad2 - 10];
                            self.close_modal();
                            if self.p_shares[s_idx] < qty {
                                self.show_msg(
                                    vec!["You don't own that many shares to sell!".into()],
                                    false,
                                    None,
                                );
                                return;
                            }
                            let sale = qty * STOCK_BASE_VAL[s_idx];
                            self.p_shares[s_idx] -= qty;
                            self.market_shares[s_idx] += qty;
                            self.p_cash += sale;
                            self.recalc_worth();
                            self.show_msg(
                                vec![format!(
                                    "You sold {} share(s) of {} for {}.",
                                    qty,
                                    STOCK_NAMES[s_idx],
                                    fmt_money(sale)
                                )],
                                true,
                                None,
                            );
                        }
                        return;
                    }
                    ModalKind::Dlog(6010) => {
                        if (3..=8).contains(&it.index) {
                            self.modal_rad1 = it.index;
                        } else if it.index == 2 {
                            self.close_modal();
                        } else if it.index == 1 {
                            let amounts = [10_000i64, 20_000, 50_000, 100_000, 200_000, 500_000];
                            let req = amounts[self.modal_rad1 - 3];
                            self.close_modal();
                            let bank_inf =
                                (self.cat_influence(464) + self.cat_influence(450)) as i64;
                            let max_loan = (self.p_worth + bank_inf * 25_000).max(50_000);
                            if self.p_debt + req <= max_loan {
                                self.p_cash += req;
                                self.p_debt += req;
                                self.recalc_worth();
                                self.show_msg(
                                    vec![format!(
                                        "Tumbleweed Bank approved your {} loan!",
                                        fmt_money(req)
                                    )],
                                    true,
                                    None,
                                );
                            } else {
                                self.show_msg(
                                    vec![
                                        "Tumbleweed Bank rejected your loan request!".into(),
                                        "Build more clout with Bank President Dan Davis.".into(),
                                    ],
                                    true,
                                    None,
                                );
                            }
                        }
                        return;
                    }
                    _ => {}
                }
            }
        }
    }
}

fn main() {
    let mut window = Window::new(
        "MacNasty (1987, George Lott) - Native Classic Mac System 6 Port",
        WIN_W,
        WIN_H,
        WindowOptions::default(),
    )
    .expect("Failed to open MacNasty window");
    window.set_target_fps(60);

    let mut app = MacNastyApp::new();
    let mut screen_buf = vec![0u32; WIN_W * WIN_H];
    let mut prev_mouse_down = false;
    let start_instant = Instant::now();

    while window.is_open() && !window.is_key_down(Key::Escape) {
        app.anim_tick = start_instant.elapsed().as_millis() as u64 / 16;

        if let Some((mx, my)) = window.get_mouse_pos(MouseMode::Clamp) {
            let x = (mx as usize / SCALE) as i32;
            let y = (my as usize / SCALE) as i32;
            app.on_mouse_move(x, y);
            let mouse_down = window.get_mouse_down(MouseButton::Left);
            if mouse_down && !prev_mouse_down {
                app.on_click(x, y);
            }
            prev_mouse_down = mouse_down;
        }

        app.render();

        for y in 0..MAC_H {
            for x in 0..MAC_W {
                let color = if app.fb[y * MAC_W + x] != 0 {
                    0x0018_181A
                } else {
                    0x00F6_F5F0
                };
                for sy in 0..SCALE {
                    let row_off = (y * SCALE + sy) * WIN_W + x * SCALE;
                    for sx in 0..SCALE {
                        screen_buf[row_off + sx] = color;
                    }
                }
            }
        }

        window
            .update_with_buffer(&screen_buf, WIN_W, WIN_H)
            .unwrap();
        std::thread::sleep(Duration::from_millis(16));
    }
}
