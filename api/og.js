// 診断版：Edge runtime でエラーの正体を特定する
export const config = { runtime: 'edge' };
import { ImageResponse } from '@vercel/og';

function h(type, props, ...children) {
  return {
    type,
    props: {
      ...props,
      children: children.length === 0 ? undefined
               : children.length === 1 ? children[0]
               : children,
    },
  };
}

export default async function handler(req) {
  try {
    const element = h('div', {
      style: { width: '400px', height: '200px', display: 'flex', background: '#faf5ff', alignItems: 'center', justifyContent: 'center' }
    }, h('div', { style: { fontSize: '40px', color: '#2a2040', display: 'flex' } }, 'Hello'));

    const imgRes = new ImageResponse(element, { width: 400, height: 200 });

    // arrayBuffer() でストリームを完全に読む → レンダリングエラーがあればここでthrow
    const buf = await imgRes.arrayBuffer();

    if (buf.byteLength === 0) {
      return new Response('ERROR: arrayBuffer is empty (0 bytes)', { status: 500, headers: { 'Content-Type': 'text/plain' } });
    }

    return new Response(buf, {
      headers: {
        'Content-Type': 'image/png',
        'Cache-Control': 'no-cache',
        'X-Debug-Size': String(buf.byteLength),
      },
    });
  } catch (e) {
    return new Response('ERROR: ' + e.message + '\n\nSTACK:\n' + (e.stack || '(no stack)'), {
      status: 500,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }
}
