// Vercel Edge Function — パーソナライズシェアページ（OGP用HTML返却）
export const config = { runtime: 'edge' };

export default function handler(req) {
  const { searchParams } = new URL(req.url);
  const n = searchParams.get('n') || '';

  const BASE = 'https://ai-life-status.vercel.app';
  const ogImageUrl = `${BASE}/api/og?v=3&n=${encodeURIComponent(n)}`;
  const destUrl = `${BASE}/?n=${encodeURIComponent(n)}`;
  const shareUrl = `${BASE}/api/share?n=${encodeURIComponent(n)}`;

  const ogTitle = n ? `${n} のギルド登録結果 ⚔️` : 'AI人生ステータス診断 ⚔️';
  const ogDesc  = n
    ? `${n} のジョブ・必殺技が判明！あなたのジョブは？`
    : '名前を入れるだけで人生がRPGになる無料診断';

  const html = `<!DOCTYPE html>
<html lang="ja"><head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0;url=${destUrl}">
<title>${ogTitle}</title>
<meta property="og:type" content="website">
<meta property="og:title" content="${ogTitle}">
<meta property="og:description" content="${ogDesc}">
<meta property="og:image" content="${ogImageUrl}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="${shareUrl}">
<meta property="og:site_name" content="AI人生ステータス診断">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@AILifeStatus">
<meta name="twitter:title" content="${ogTitle}">
<meta name="twitter:description" content="${ogDesc}">
<meta name="twitter:image" content="${ogImageUrl}">
</head><body><a href="${destUrl}">→ 結果を見る</a></body></html>`;

  return new Response(html, {
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'public, max-age=600, s-maxage=600',
    },
  });
}
