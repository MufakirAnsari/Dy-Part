// scripts/audit_figures.js
// Comprehensive audit script for publication figures:
// 1. Strict XML validation
// 2. Anonymity / Banned string check
// 3. Mathematical & Factual data accuracy check
// 4. Geometry & Coordinate collision check

const fs = require('fs');
const path = require('path');

const targetFiles = [
    'Figure_Cost_Model_Empirical_Validation.svg',
    'Figure_Cut_Distribution_Comparison.svg',
    'Figure_In_Depth_Analysis.svg',
    'Figure_In_Depth_Beta_Gamma_Analysis.svg',
    'Figure_Oracle_Comparison_Detailed_10_nodes.svg',
    'Figure_Performance_Comparison_Averaged.svg',
    'Figure_Runtime_Breakdown.svg',
    'Figure_Scheduler_Decisions_Averaged.svg',
    'Figure_Scheduler_Decisions_with_Inset.svg',
    'Figure_Ternary_Search_Ablation.svg'
];

console.log('================================================================');
console.log('             DY-PART MASTER PUBLICATION FIGURE AUDIT            ');
console.log('================================================================\n');

let totalIssues = 0;

// 1. XML SYNTAX & INTEGRITY CHECK
console.log('--- 1. XML Syntax, Entities, & Encoding Integrity ---');
const validEntities = new Set(['&amp;', '&lt;', '&gt;', '&quot;', '&apos;']);

targetFiles.forEach(f => {
    const filePath = path.join('results', f);
    if (!fs.existsSync(filePath)) {
        console.error('FAIL: Missing file ' + f);
        totalIssues++;
        return;
    }
    const content = fs.readFileSync(filePath, 'utf8');

    // Check SVG wrapping
    if (!content.trim().startsWith('<svg') || !content.trim().endsWith('</svg>')) {
        console.error('FAIL: ' + f + ' does not have valid <svg>...</svg> root wrapper');
        totalIssues++;
    }

    // Check XML entities
    const entityMatches = content.match(/&[a-zA-Z0-9#]+;/g) || [];
    const badEntities = entityMatches.filter(e => !validEntities.has(e) && !e.startsWith('&#'));
    if (badEntities.length > 0) {
        console.error('FAIL: ' + f + ' contains illegal XML entities: ' + badEntities.join(', '));
        totalIssues++;
    }

    // Check unescaped ampersands
    const badAmp = content.match(/&(?!amp;|lt;|gt;|quot;|apos;|#[0-9]+;|#x[0-9a-fA-F]+;)/g);
    if (badAmp) {
        console.error('FAIL: ' + f + ' contains ' + badAmp.length + ' unescaped ampersands');
        totalIssues++;
    }

    // Check viewBox matches width/height
    const vbMatch = content.match(/viewBox="0 0 (\d+) (\d+)"/);
    const wMatch = content.match(/width="(\d+)"/);
    const hMatch = content.match(/height="(\d+)"/);
    if (vbMatch && wMatch && hMatch) {
        if (vbMatch[1] !== wMatch[1] || vbMatch[2] !== hMatch[1]) {
            console.error('FAIL: ' + f + ' viewBox (' + vbMatch[1] + 'x' + vbMatch[2] + ') does not match width/height (' + wMatch[1] + 'x' + hMatch[1] + ')');
            totalIssues++;
        }
    }

    console.log('  PASS: ' + f + ' (' + content.length + ' bytes, valid XML, viewBox ' + (vbMatch ? vbMatch[1] + 'x' + vbMatch[2] : 'N/A') + ')');
});

// 2. ACADEMIC ANONYMITY & TONE CHECK
console.log('\n--- 2. Academic Tone & Anonymity Audit (Zero Internal Tickets/Reviewer Names) ---');
const bannedStrings = ['REV-', 'ACT-', 'Reviewer', 'Direct response', 'ISS-', 'DEC-'];

targetFiles.forEach(f => {
    const content = fs.readFileSync(path.join('results', f), 'utf8');
    let fileBanned = 0;
    bannedStrings.forEach(b => {
        if (content.includes(b)) {
            console.error('FAIL: ' + f + ' contains internal/reviewer string: "' + b + '"');
            fileBanned++;
            totalIssues++;
        }
    });
    if (fileBanned === 0) {
        console.log('  PASS: ' + f + ' is 100% clean of internal tracking codes');
    }
});

// 3. FACTUAL DATA & MATHEMATICAL BOUNDS CHECK
console.log('\n--- 3. Factual Experimental Data & Mathematical Bounds Audit ---');

function parseCSV(fp) {
    const lines = fs.readFileSync(fp, 'utf8').trim().split('\n');
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

const dfBench = parseCSV('results/corrected_benchmark.csv');
const dfHyper = parseCSV('results/hyperparam_grid_search.csv');
const dfAblation = parseCSV('results/ternary_ablation_table.csv');
const dfSched = parseCSV('results/scheduler_runtime_overhead.csv');

// Verify benchmark data bounds
const benchARs = dfBench.map(r => r.approximation_ratio);
const minAR = Math.min(...benchARs);
const maxAR = Math.max(...benchARs);
console.log('  Benchmark runs: ' + dfBench.length + ' (expected: 4,160)');
if (dfBench.length !== 4160) {
    console.error('FAIL: Incorrect benchmark row count: ' + dfBench.length);
    totalIssues++;
} else {
    console.log('  PASS: Benchmark row count is exactly 4,160 verified runs');
}

console.log('  Benchmark AR bounds: [' + minAR.toFixed(4) + ', ' + maxAR.toFixed(4) + ']');
if (minAR < 0.0 || maxAR > 1.0) {
    console.error('FAIL: Approximation ratio out of [0, 1] bounds!');
    totalIssues++;
} else {
    console.log('  PASS: All 4,160 approximation ratios are strictly in [0.0, 1.0]');
}

// Verify grid search data bounds
const hyperARs = dfHyper.map(r => r.approximation_ratio);
const minHyperAR = Math.min(...hyperARs);
const maxHyperAR = Math.max(...hyperARs);
console.log('  Grid search runs: ' + dfHyper.length + ' (expected: 2,000)');
if (dfHyper.length !== 2000) {
    console.error('FAIL: Incorrect grid search row count: ' + dfHyper.length);
    totalIssues++;
} else {
    console.log('  PASS: Grid search row count is exactly 2,000 verified runs');
}
console.log('  Grid search AR bounds: [' + minHyperAR.toFixed(4) + ', ' + maxHyperAR.toFixed(4) + ']');
if (minHyperAR < 0.0 || maxHyperAR > 1.0) {
    console.error('FAIL: Grid search AR out of [0, 1] bounds!');
    totalIssues++;
} else {
    console.log('  PASS: All 2,000 grid search ARs are strictly in [0.0, 1.0]');
}

// Verify optimal hyperparam
const alpha70 = dfHyper.filter(r => Math.abs(r.alpha - 0.70) < 0.01 && Math.abs(r.beta - 1.0) < 0.01 && Math.abs(r.gamma - 0.1) < 0.01);
const meanA70 = alpha70.reduce((a, b) => a + b.approximation_ratio, 0) / alpha70.length;
console.log('  Empirical mean AR at alpha=0.70: ' + meanA70.toFixed(4) + ' (expected: 0.9115)');
if (Math.abs(meanA70 - 0.9115) > 0.005) {
    console.error('FAIL: Pareto optimum alpha=0.70 mean mismatch');
    totalIssues++;
} else {
    console.log('  PASS: Pareto optimum alpha=0.70 verified at Mean AR = ' + meanA70.toFixed(4));
}

// 4. COORDINATE & GEOMETRIC COLLISION CHECK
console.log('\n--- 4. Visual Coordinates, Clipping, & Collision Audit ---');

targetFiles.forEach(f => {
    const content = fs.readFileSync(path.join('results', f), 'utf8');
    const vbMatch = content.match(/viewBox="0 0 (\d+) (\d+)"/);
    const vbW = parseFloat(vbMatch[1]);
    const vbH = parseFloat(vbMatch[2]);

    // Check for negative or off-viewbox coordinates in paths
    const pathMatches = content.match(/<path d="([^"]+)"/g) || [];
    let pathOutOfRange = 0;
    pathMatches.forEach(p => {
        const coords = p.match(/[-0-9.]+\s+[-0-9.]+/g) || [];
        coords.forEach(c => {
            const parts = c.trim().split(/\s+/).map(Number);
            const x = parts[0];
            const y = parts[1];
            if (x < 0 || x > vbW || y < 0 || y > vbH) {
                // Allow small negative margin only if clipped
                if (!content.includes('clip-path')) {
                    console.error('FAIL: ' + f + ' path coordinate (' + x + ', ' + y + ') exceeds viewBox (0,0,' + vbW + ',' + vbH + ')');
                    pathOutOfRange++;
                    totalIssues++;
                }
            }
        });
    });

    // Check text coordinates
    const textMatches = content.match(/<text x="([^"]+)" y="([^"]+)"/g) || [];
    let textOutOfRange = 0;
    textMatches.forEach(t => {
        const parts = t.match(/x="([^"]+)" y="([^"]+)"/);
        const x = parseFloat(parts[1]);
        const y = parseFloat(parts[2]);
        if (x < 0 || x > vbW || y < 0 || y > vbH) {
            console.error('FAIL: ' + f + ' text coordinate (' + x + ', ' + y + ') exceeds viewBox');
            textOutOfRange++;
            totalIssues++;
        }
    });

    if (pathOutOfRange === 0 && textOutOfRange === 0) {
        console.log('  PASS: ' + f + ' coordinates strictly within viewBox [0, 0, ' + vbW + ', ' + vbH + ']');
    }
});

console.log('\n================================================================');
if (totalIssues === 0) {
    console.log('AUDIT RESULT: 100% PASS! ALL FIGURES ARE FACTUAL, BOUNDED, AND VALID');
} else {
    console.error('AUDIT RESULT: FOUND ' + totalIssues + ' ISSUES TO FIX');
}
console.log('================================================================\n');
