export function un(r) {
  return r && typeof r === 'object' && 'page' in r && 'value' in r ? r.value : r;
}

export async function waitFor(p, predicate, arg, { timeout = 8000, interval = 500 } = {}) {
  if (!Number.isFinite(timeout) || timeout < 0 || !Number.isFinite(interval) || interval <= 0) throw new Error('Invalid polling timeout or interval');
  const fn = typeof predicate === 'string' ? new Function(`return (${predicate})`)() : predicate;
  const start = Date.now();
  let waited = 0;
  while (true) {
    const result = un(await p.evaluate(fn, arg));
    if (result) return result;
    const remaining = timeout - Math.max(Date.now() - start, waited);
    if (remaining <= 0) throw new Error(`Timed out after ${timeout} ms`);
    const delay = Math.min(interval, remaining);
    await p.waitForTime(delay);
    waited += delay;
  }
}

export function refOf(snapshotText, pattern) {
  for (const line of snapshotText.split('\n')) {
    if (pattern instanceof RegExp) pattern.lastIndex = 0;
    if (pattern instanceof RegExp ? pattern.test(line) : line.includes(pattern)) {
      const ref = line.match(/\[ref=([^\]]+)\]/)?.[1];
      if (ref) return ref;
    }
  }
  throw new Error(`Snapshot reference not found: ${pattern}`);
}

export async function clickText(p, text, { frame } = {}) {
  const point = un(await p.evaluate(({ text, frame }) => {
    const f = frame ? document.querySelector(frame) : null;
    const d = frame ? f?.contentDocument : document;
    if (!d) throw new Error(`Frame unavailable: ${frame}`);
    const el = [...d.querySelectorAll('body *')].reverse().find(el =>
      (el.innerText ?? el.textContent).trim() === text.trim() && el.getBoundingClientRect().width > 0);
    if (!el) throw new Error(`Text not found: ${text}`);
    el.scrollIntoView({ block: 'center', inline: 'center' });
    const r = el.getBoundingClientRect();
    const o = f?.getBoundingClientRect();
    return { x: r.x + r.width / 2 + (o?.x ?? 0) + (f?.clientLeft ?? 0), y: r.y + r.height / 2 + (o?.y ?? 0) + (f?.clientTop ?? 0) };
  }, { text, frame }));
  await p.clickAt(point.x, point.y);
  return text;
}

export async function setFiles(p, selector, files, { frame } = {}) {
  const { root } = un(await p.cdp('DOM.getDocument', JSON.stringify({ depth: -1, pierce: true })));
  let nodeId = root.nodeId;
  if (frame) {
    const target = un(await p.cdp('DOM.querySelector', JSON.stringify({ nodeId, selector: frame })));
    const find = node => node.nodeId === target.nodeId ? node :
      [...(node.children ?? []), ...(node.shadowRoots ?? []), ...(node.contentDocument ? [node.contentDocument] : [])].map(find).find(Boolean);
    const doc = find(root)?.contentDocument;
    if (!doc) throw new Error(`Frame document unavailable: ${frame}`);
    nodeId = doc.nodeId;
  }
  const input = un(await p.cdp('DOM.querySelector', JSON.stringify({ nodeId, selector })));
  if (!input.nodeId) throw new Error(`File input not found: ${selector}`);
  await p.cdp('DOM.setFileInputFiles', JSON.stringify({ nodeId: input.nodeId, files: Array.isArray(files) ? files : [files] }));
  return { selector, files: Array.isArray(files) ? files : [files] };
}

export async function frameCall(p, ref, fnSource) {
  const { backendNodeId, sessionId } = un(await p.resolveRef(ref));
  const { object } = un(await browser.cdp('DOM.resolveNode', { backendNodeId }, sessionId));
  if (!object?.objectId) throw new Error(`Node could not be resolved: ${ref}`);
  const result = un(await browser.cdp('Runtime.callFunctionOn', {
    objectId: object.objectId, functionDeclaration: fnSource, returnByValue: true
  }, sessionId));
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text);
  return result.result?.value;
}

export async function acceptCookies(p) {
  const target = un(await p.evaluate(() => {
    const visible = el => el && el.getBoundingClientRect().width > 0 && el.getBoundingClientRect().height > 0;
    const text = el => (el.innerText ?? el.textContent ?? el.value ?? '').trim() || el.value || '';
    const safe = el => visible(el) && !/reject|decline|necessary only|settings|preferences/i.test(text(el));
    const buttons = [...document.querySelectorAll('button, [role=button], input[type=button]')].filter(safe);
    const el = [buttons.find(el => /^(accept all|allow all)$/i.test(text(el))),
      document.querySelector('#onetrust-accept-btn-handler'),
      buttons.find(el => /accept all|allow all/i.test(text(el))),
      buttons.find(el => /accept|agree|okay/i.test(text(el)))].find(safe);
    if (!el) return null;
    el.scrollIntoView({ block: 'center' });
    const r = el.getBoundingClientRect();
    return { text: text(el), x: r.x + r.width / 2, y: r.y + r.height / 2 };
  }));
  if (!target) return null;
  await p.clickAt(target.x, target.y);
  return target.text;
}
