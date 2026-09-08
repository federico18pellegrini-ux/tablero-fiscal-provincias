/* Export uses the dashboard's own rankings and simulation, including ties/missing data. */
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {METRICS, TRANSPARENCY_COMPONENTS, transparencyStatus, rankMunicipalities, peers, simulate} from './municipios/model.mjs';
export function reportModels(data) {
  const rankings = METRICS.map(meta => rankMunicipalities(data.municipalities, meta));
  return data.municipalities.map(m => ({...m,
    reportRankings: METRICS.map((meta, i) => {
      const all = rankings[i], similar = rankMunicipalities(peers(data.municipalities, m, true), meta);
      const selected = all.find(r => r.m.id === m.id), peer = similar.find(r => r.m.id === m.id);
      return {...meta, value: selected?.value ?? null, rank: selected?.rank ?? null, count: all.length,
        peerRank: peer?.rank ?? null, peerCount: similar.length};
    }),
    reportScenarios: Array.from({length: 41}, (_, i) => simulate(m, i / 2)),
    reportTransparency: TRANSPARENCY_COMPONENTS.map(c => ({...c,
      status: transparencyStatus(c, m.transparency?.components[c.id]),
      history: m.transparency?.history.map(h => h.components[c.id] ?? null) ?? []
    }))
  }));
}
if (process.argv[1] && fileURLToPath(import.meta.url) === fs.realpathSync(process.argv[1])) {
  const data = JSON.parse(fs.readFileSync(new URL('./municipios/data/dashboard.json', import.meta.url), 'utf8'));
  process.stdout.write(JSON.stringify({...data, municipalities: reportModels(data)}));
}
