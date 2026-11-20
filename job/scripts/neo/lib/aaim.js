import { un, setFiles, waitFor } from './core.js';

export async function aaimFill(p, labelToValue) {
  const { text } = await p.snapshot({ mode: 'interactive' });
  const fields = text.split('\n').map(line => line.match(/\btextbox "((?:\\.|[^"\\])*)"[^\n]*\[ref=([^\]]+)\]/)).filter(Boolean);
  const filled = [];
  for (const [label, value] of Object.entries(labelToValue)) {
    const matches = fields.filter(m => JSON.parse(`"${m[1]}"`) === label);
    if (matches.length !== 1) throw new Error(`Expected one textbox for ${label}, found ${matches.length}`);
    await p.fill(matches[0][2], String(value));
    filled.push(label);
  }
  return filled;
}

export async function aaimUpload(p, file) {
  await setFiles(p, '#default_resume', [file]);
  const point = un(await p.evaluate(() => {
    const el = [...document.querySelectorAll('form#upload_resume button, form#upload_resume input[type=submit]')]
      .find(el => (el.innerText ?? el.textContent ?? '').trim() === 'Upload Files' || el.value?.trim() === 'Upload Files');
    if (!el) throw new Error('AAIM resume Upload Files button not found');
    el.scrollIntoView({ block: 'center' });
    const r = el.getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  }));
  await p.clickAt(point.x, point.y);
  const name = file.split(/[\\/]/).pop();
  try {
    return await waitFor(p, name => {
      const rows = [...document.querySelectorAll('button.delete[data-id]')].map(el => ({
        id: el.dataset.id, text: (el.closest('li, tr, .row, div') ?? el.parentElement).textContent.replace(/\s+/g, ' ').trim()
      }));
      return rows.some(row => row.text.replace(/\s+/g, '').includes(name.replace(/\s+/g, ''))) ? rows : null;
    }, name, { timeout: 12000, interval: 1000 });
  } catch (error) { throw new Error(`AAIM upload failed for ${name}: ${error.message}`); }
}

export async function aaimDeleteAttachment(p, matchText) {
  const target = un(await p.evaluate(matchText => {
    const matches = [...document.querySelectorAll('button.delete[data-id]')]
      .filter(el => (el.closest('li, tr, .row, div') ?? el.parentElement).textContent.replace(/\s+/g, '').includes(matchText.replace(/\s+/g, '')));
    if (matches.length !== 1) throw new Error(`Expected one attachment matching ${matchText}, found ${matches.length}`);
    const el = matches[0];
    el.scrollIntoView({ block: 'center' });
    const r = el.getBoundingClientRect();
    return { id: el.dataset.id, x: r.x + r.width / 2, y: r.y + r.height / 2 };
  }, matchText));
  let result;
  try { result = un(await p.clickAt(target.x, target.y)); }
  catch (error) {
    if (!/dialog|alert|confirm/i.test(error.message)) throw error;
    result = { dialogOpen: true };
  }
  if (result?.dialogOpen) await p.dialogAccept();
  try {
    const { remaining } = await waitFor(p, id => {
      const remaining = [...document.querySelectorAll('button.delete[data-id]')].map(el => ({
        id: el.dataset.id, text: (el.closest('li, tr, .row, div') ?? el.parentElement).textContent.replace(/\s+/g, ' ').trim()
      }));
      return remaining.some(row => row.id === id) ? null : { remaining };
    }, target.id, { timeout: 8000, interval: 1000 });
    return { id: target.id, remaining };
  } catch (error) { throw new Error(`AAIM attachment ${target.id} was not deleted: ${error.message}`); }
}
