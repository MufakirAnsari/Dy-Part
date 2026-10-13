// scripts/analyze_correlations.js
// ACT-022: Empirical Cost Model Validation analysis

const fs = require('fs');
const path = require('path');

function parseCSV(filePath) {
    const lines = fs.readFileSync(filePath, 'utf8').trim().split('\n');
    const header = lines[0].trim().split(',');
    const rows = [];
    for (let i = 1; i < lines.length; i++) {
        if (!lines[i].trim()) continue;
        const vals = lines[i].trim().split(',');
        const row = {};
        header.forEach((h, idx) => {
            row[h] = isNaN(vals[idx]) ? vals[idx] : parseFloat(vals[idx]);
        });
        rows.push(row);
    }
    return rows;
}

function pearson(x, y) {
    const n = x.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
    for (let i = 0; i < n; i++) {
        sumX += x[i];
        sumY += y[i];
        sumXY += x[i] * y[i];
        sumX2 += x[i] * x[i];
        sumY2 += y[i] * y[i];
    }
    const num = n * sumXY - sumX * sumY;
    const den = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
    return den === 0 ? 0 : num / den;
}

function rank(arr) {
    const sorted = arr.map((v, i) => ({ v, i })).sort((a, b) => a.v - b.v);
    const ranks = new Array(arr.length);
    let i = 0;
    while (i < sorted.length) {
        let j = i;
        while (j < sorted.length - 1 && sorted[j + 1].v === sorted[j].v) {
            j++;
        }
        const avgRank = (i + j + 2) / 2;
        for (let k = i; k <= j; k++) {
            ranks[sorted[k].i] = avgRank;
        }
        i = j + 1;
    }
    return ranks;
}

function spearman(x, y) {
    return pearson(rank(x), rank(y));
}

function pValueFromT(t, df) {
    // Two-tailed p-value approximation using normal approximation for large df or beta incomplete
    const x = df / (df + t * t);
    // for df > 30, t is very well approximated by standard normal
    const z = Math.abs(t);
    // Approximation of standard normal error function
    const b1 = 0.319381530;
    const b2 = -0.356563782;
    const b3 = 1.781477937;
    const b4 = -1.821255978;
    const b5 = 1.330274429;
    const p = 0.2316419;
    const c = 0.3989422804;
    const k = 1.0 / (1.0 + p * z);
    const poly = ((((b5 * k + b4) * k + b3) * k + b2) * k + b1) * k;
    const normCdf = 1.0 - c * Math.exp(-0.5 * z * z) * poly;
    return Math.max(1e-15, 2 * (1.0 - normCdf));
}

function calcStats(x, y) {
    const n = x.length;
    const r = pearson(x, y);
    const rho = spearman(x, y);
    const df = n - 2;
    const t_r = r * Math.sqrt(df) / Math.sqrt(Math.max(1e-12, 1 - r * r));
    const p_r = df > 2 ? pValueFromT(t_r, df) : 1.0;
    const t_rho = rho * Math.sqrt(df) / Math.sqrt(Math.max(1e-12, 1 - rho * rho));
    const p_rho = df > 2 ? pValueFromT(t_rho, df) : 1.0;
    return { n, r, rho, r2: r * r, p_r, p_rho };
}

const hyper = parseCSV('results/hyperparam_grid_search.csv');
const bench = parseCSV('results/corrected_benchmark.csv');

console.log('=== ACT-022 EMPIRICAL COST MODEL VALIDATION ===\n');

// 1. Grid search correlations
console.log('1. Hyperparameter Grid Search (N=2000 runs, 10 nodes, mid noise 5e-3):');
const h_pairs = [
    { name: 'Quantum Cost vs VQE Runtime', x: hyper.map(r => r.quantum_cost), y: hyper.map(r => r.runtime_seconds) },
    { name: 'Chosen Subgraph Size (n_sub) vs VQE Runtime', x: hyper.map(r => r.chosen_n_sub), y: hyper.map(r => r.runtime_seconds) },
    { name: 'Cut Penalty vs Number of Cuts', x: hyper.map(r => r.classical_cost), y: hyper.map(r => r.num_cuts) },
    { name: 'Quantum Cost vs Approximation Ratio (AR)', x: hyper.map(r => r.quantum_cost), y: hyper.map(r => r.approximation_ratio) },
    { name: 'Total Cost vs Approximation Ratio (AR)', x: hyper.map(r => r.total_cost), y: hyper.map(r => r.approximation_ratio) },
    { name: 'Number of Cuts vs Approximation Ratio (AR)', x: hyper.map(r => r.num_cuts), y: hyper.map(r => r.approximation_ratio) },
];

h_pairs.forEach(p => {
    const s = calcStats(p.x, p.y);
    console.log(`  - ${p.name}:`);
    console.log(`      Pearson r = ${s.r.toFixed(4)} (p = ${s.p_r.toExponential(2)}, R^2 = ${(s.r2).toFixed(4)})`);
    console.log(`      Spearman rho = ${s.rho.toFixed(4)} (p = ${s.p_rho.toExponential(2)})`);
});

// 2. Full benchmark correlations
console.log('\n2. Multi-Scale Benchmark (N=4160 runs across 8, 10, 12, 16, 20 nodes):');
const dypart = bench.filter(r => r.method === 'dypart');
dypart.forEach(r => {
    const total_edges = 1.5 * r.num_nodes;
    const q_gates = 2 * (r.chosen_n_sub - 1);
    r.quantum_cost = 1.0 - Math.pow(1.0 - r.noise_level, q_gates);
    r.classical_cost = 0.1 * Math.pow(r.num_cuts / total_edges, 1.0 / 1.0);
    r.total_cost = 0.7 * r.quantum_cost + 0.3 * r.classical_cost;
});

const b_pairs = [
    { name: 'Dy-Part: Graph Size (N) vs Runtime', x: dypart.map(r => r.num_nodes), y: dypart.map(r => r.runtime_seconds) },
    { name: 'Dy-Part: Chosen Subgraph Size (n_sub) vs Runtime', x: dypart.map(r => r.chosen_n_sub), y: dypart.map(r => r.runtime_seconds) },
    { name: 'Dy-Part: Quantum Cost vs AR', x: dypart.map(r => r.quantum_cost), y: dypart.map(r => r.approximation_ratio) },
    { name: 'Dy-Part: Total Heuristic Cost vs AR', x: dypart.map(r => r.total_cost), y: dypart.map(r => r.approximation_ratio) },
    { name: 'Dy-Part: Number of Cuts vs AR', x: dypart.map(r => r.num_cuts), y: dypart.map(r => r.approximation_ratio) },
    { name: 'All Methods: Number of Cuts vs AR', x: bench.map(r => r.num_cuts), y: bench.map(r => r.approximation_ratio) },
    { name: 'All Methods: Graph Size (N) vs Runtime', x: bench.map(r => r.num_nodes), y: bench.map(r => r.runtime_seconds) },
];

b_pairs.forEach(p => {
    const s = calcStats(p.x, p.y);
    console.log(`  - ${p.name}:`);
    console.log(`      Pearson r = ${s.r.toFixed(4)} (p = ${s.p_r.toExponential(2)}, R^2 = ${(s.r2).toFixed(4)})`);
    console.log(`      Spearman rho = ${s.rho.toFixed(4)} (p = ${s.p_rho.toExponential(2)})`);
});

// 3. Per-scale breakdown for Dy-Part
console.log('\n3. Per-Scale Breakdown for Dy-Part (n_sub vs Runtime, Quantum Cost vs AR):');
[8, 10, 12, 16, 20].forEach(n => {
    const sub = dypart.filter(r => r.num_nodes === n);
    const s_run = calcStats(sub.map(r => r.chosen_n_sub), sub.map(r => r.runtime_seconds));
    const s_ar = calcStats(sub.map(r => r.quantum_cost), sub.map(r => r.approximation_ratio));
    const s_cost = calcStats(sub.map(r => r.total_cost), sub.map(r => r.approximation_ratio));
    console.log(`  Scale N = ${n} (${sub.length} runs):`);
    console.log(`    n_sub vs Runtime:        r = ${s_run.r.toFixed(4)}, rho = ${s_run.rho.toFixed(4)}`);
    console.log(`    Quantum Cost vs AR:      r = ${s_ar.r.toFixed(4)}, rho = ${s_ar.rho.toFixed(4)}`);
    console.log(`    Total Cost vs AR:        r = ${s_cost.r.toFixed(4)}, rho = ${s_cost.rho.toFixed(4)}`);
});
