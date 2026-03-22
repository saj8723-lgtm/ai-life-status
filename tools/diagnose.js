/**
 * diagnose.js — index.html の gen() をそのまま実行して診断値をJSONで返す
 * 使い方: node tools/diagnose.js "田中美久"
 *         node tools/diagnose.js "田中美久" "2026-03-18"  ← 日付指定
 */
const fs   = require('fs');
const path = require('path');

const name    = process.argv[2];
const dateArg = process.argv[3];  // オプション: "YYYY-MM-DD"

if (!name) {
  process.stderr.write('Usage: node diagnose.js <name> [YYYY-MM-DD]\n');
  process.exit(1);
}

// index.html を読み込んで必要な部分だけ抜き出す
const html = fs.readFileSync(path.join(__dirname, '../index.html'), 'utf-8');

// <script> ブロックを全部結合
const scripts = [];
const re = /<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi;
let m;
while ((m = re.exec(html)) !== null) {
  scripts.push(m[1]);
}
const jsSource = scripts.join('\n');

// ブラウザAPIのスタブ（gen()はDate以外使わない）
const dateOverride = dateArg ? new Date(dateArg) : null;

const sandbox = `
// --- ブラウザスタブ ---
const document  = { getElementById: () => null, body: { classList: { contains: () => false }, style: {} }, querySelectorAll: () => [] };
const window    = { open: () => {}, scrollTo: () => {} };
const location  = { href: '', search: '' };
const history   = { pushState: () => {} };
const navigator = { clipboard: { writeText: () => {} } };
const alert     = () => {};
const setTimeout = (fn) => {};  // gen()は使わないので無害

// Date.toDateString() を差し替えたい場合はここで上書き
${dateOverride ? `
const _origDate = Date;
Date = class extends _origDate {
  constructor(...a) { super(...(a.length ? a : [${dateOverride.getTime()}])); }
  static now() { return ${dateOverride.getTime()}; }
};
` : ''}

// --- index.html のスクリプト本体 ---
${jsSource}

// --- 出力 ---
const d = gen(${JSON.stringify(name)});
const sv = {};
[{n:'💪体力',k:'hp'},{n:'🧠知力',k:'int'},{n:'💰金運',k:'pay'},
 {n:'😎孤独耐性',k:'solo'},{n:'🔥やる気',k:'mot'},{n:'🍀運',k:'luk'}]
.forEach(s => {
  sv[s.k] = { icon: s.n, value: d.sv[s.k] };
});
process.stdout.write(JSON.stringify({
  name:     d.name,
  job:      d.job,
  level:    d.lv,
  title:    d.title,
  move:     d.move,
  weakness: d.wk,
  total:    d.total,
  sv:       sv,
}));
`;

try {
  eval(sandbox);
} catch (e) {
  process.stderr.write('Error: ' + e.message + '\n');
  process.exit(1);
}
