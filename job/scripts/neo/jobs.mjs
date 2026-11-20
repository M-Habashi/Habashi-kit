import { pathToFileURL } from 'node:url';
import { JSDOM } from 'jsdom';

export function parseWorkday(data, host, site) {
  if (!Array.isArray(data.jobPostings)) throw new Error('Workday response is missing jobPostings');
  return data.jobPostings.map(job => ({ title: job.title ?? '', location: job.locationsText ?? '',
    posted: job.postedOn ?? '', id: job.bulletFields?.[0] ?? '',
    url: new URL(`/${encodeURIComponent(site)}${job.externalPath}`, `https://${host}`).href }));
}

export function parseIcims(html, host) {
  const dom = new JSDOM(html, { url: `https://${host}` });
  try {
    const d = dom.window.document;
    const jobs = [...d.querySelectorAll('.iCIMS_JobListing, .iCIMS_JobListingRow, .iCIMS_JobCardItem')].map(row => {
      const a = row.querySelector('.iCIMS_JobTitle a, a[href*="/jobs/"]');
      if (!a) return null;
      const url = new URL(a.getAttribute('href'), `https://${host}`);
      if (!/^\/jobs\/\d+\//.test(url.pathname)) return null;
      const text = selector => row.querySelector(selector)?.textContent.replace(/\s+/g, ' ').trim() ?? '';
      const field = pattern => [...row.querySelectorAll('dt')].find(el => pattern.test(el.textContent))?.nextElementSibling?.textContent.replace(/\s+/g, ' ').trim() ?? '';
      const location = text('.iCIMS_JobLocation .iCIMS_JobHeaderData') || text('.iCIMS_JobLocation') || field(/location/i) || text('.header.left');
      url.search = '';
      url.hash = '';
      return { title: (a.querySelector('h2, h3') ?? a).textContent.replace(/\s+/g, ' ').trim(), location: location.replace(/^Job Locations?\s*/i, ''),
        posted: field(/posted|posting date/i), id: field(/^id$|job id|requisition/i) || url.pathname.match(/\/jobs\/(\d+)/)[1], url: url.href };
    }).filter(Boolean);
    const pages = [...d.querySelectorAll('a[href]')].map(a => new URL(a.getAttribute('href'), `https://${host}`).searchParams.get('pr'))
      .filter(value => value !== null && /^\d+$/.test(value)).map(Number);
    return { jobs, pages };
  } finally { dom.window.close(); }
}

function publicHost(host, suffix) {
  if (!/^[a-z0-9]+(?:[.-][a-z0-9]+)*$/i.test(host) || !host.toLowerCase().endsWith(`.${suffix}`)) throw new Error(`Expected a public ${suffix} hostname`);
  return host.toLowerCase();
}

export async function request(url, options = {}) {
  const response = await fetch(url, { ...options, redirect: 'error', signal: AbortSignal.timeout(20000) });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${url}`);
  return response;
}

export async function workday(host, tenant, site, query) {
  host = publicHost(host, 'myworkdayjobs.com');
  const jobs = [];
  for (let offset = 0; offset < 60; offset += 20) {
    const response = await request(`https://${host}/wday/cxs/${encodeURIComponent(tenant)}/${encodeURIComponent(site)}/jobs`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ appliedFacets: {}, limit: 20, offset, searchText: query })
    });
    const data = await response.json();
    const page = parseWorkday(data, host, site);
    jobs.push(...page);
    if (page.length < 20 || jobs.length >= data.total) break;
  }
  return jobs.slice(0, 60);
}

export async function icims(host, query) {
  host = publicHost(host, 'icims.com');
  const jobs = new Map();
  for (let page = 0; page < 60; page++) {
    const url = new URL(`https://${host}/jobs/search`);
    url.search = new URLSearchParams({ ss: '1', searchKeyword: query, in_iframe: '1', pr: String(page) });
    const data = parseIcims(await (await request(url)).text(), host);
    let added = 0;
    for (const job of data.jobs) {
      if (!jobs.has(job.url)) added++;
      jobs.set(job.url, job);
    }
    if (!added || !data.pages.some(n => n > page)) break;
  }
  return [...jobs.values()];
}

export async function main(argv) {
  const args = [], flags = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--json') flags.json = true;
    else if (argv[i] === '--filter') {
      if (argv[i + 1] === undefined) throw new Error('--filter requires a regular expression');
      flags.filter = new RegExp(argv[++i], 'i');
    } else if (argv[i].startsWith('--')) throw new Error(`Unknown flag: ${argv[i]}`);
    else args.push(argv[i]);
  }
  const [kind, ...params] = args;
  if (!(kind === 'workday' && params.length === 4 || kind === 'icims' && params.length === 2)) {
    throw new Error('Usage: jobs.mjs workday <host> <tenant> <site> <query> | icims <host> <query> [--json] [--filter <regex>]');
  }
  const jobs = (await (kind === 'workday' ? workday(...params) : icims(...params))).filter(job => !flags.filter || flags.filter.test(job.title));
  console.log(flags.json ? JSON.stringify(jobs, null, 2) : jobs.map(job => [job.title, job.location, job.posted || 'Not listed', job.url].join(' | ')).join('\n'));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try { await main(process.argv.slice(2)); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
