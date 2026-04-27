import re
import sys

def modify_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # 1. Update stats to include latencies
    content = content.replace(
        'baseline: { latSum: 0, cnt: 0, lost: 0 },',
        'baseline: { latSum: 0, cnt: 0, lost: 0, latencies: [] },'
    )
    content = content.replace(
        'rpl: { latSum: 0, cnt: 0, lost: 0, tSum: 0, tCnt: 0 },',
        'rpl: { latSum: 0, cnt: 0, lost: 0, tSum: 0, tCnt: 0, latencies: [] },'
    )
    content = content.replace(
        'pcertv3: { latSum: 0, cnt: 0, lost: 0, critLatSum: 0, critCnt: 0, lbEvents: 0 },',
        'pcertv3: { latSum: 0, cnt: 0, lost: 0, critLatSum: 0, critCnt: 0, lbEvents: 0, latencies: [] },'
    )
    content = content.replace(
        'pcertv4: { latSum: 0, cnt: 0, lost: 0, critLatSum: 0, critCnt: 0, lbEvents: 0, etxSaves: 0, hystBlocks: 0 },',
        'pcertv4: { latSum: 0, cnt: 0, lost: 0, critLatSum: 0, critCnt: 0, lbEvents: 0, etxSaves: 0, hystBlocks: 0, latencies: [] },'
    )

    # Reset stats
    content = content.replace(
        'stats.baseline = { latSum: 0, cnt: 0, lost: 0 };',
        'stats.baseline = { latSum: 0, cnt: 0, lost: 0, latencies: [] };'
    )
    content = content.replace(
        'stats.rpl = { latSum: 0, cnt: 0, lost: 0, tSum: 0, tCnt: 0 };',
        'stats.rpl = { latSum: 0, cnt: 0, lost: 0, tSum: 0, tCnt: 0, latencies: [] };'
    )
    content = content.replace(
        'stats.pcertv3 = { latSum: 0, cnt: 0, lost: 0, critLatSum: 0, critCnt: 0, lbEvents: 0 };',
        'stats.pcertv3 = { latSum: 0, cnt: 0, lost: 0, critLatSum: 0, critCnt: 0, lbEvents: 0, latencies: [] };'
    )
    content = content.replace(
        'stats.pcertv4 = { latSum: 0, cnt: 0, lost: 0, critLatSum: 0, critCnt: 0, lbEvents: 0, etxSaves: 0, hystBlocks: 0 };',
        'stats.pcertv4 = { latSum: 0, cnt: 0, lost: 0, critLatSum: 0, critCnt: 0, lbEvents: 0, etxSaves: 0, hystBlocks: 0, latencies: [] };'
    )

    # 2. Add Jitter HTML to Scorecards
    content = content.replace(
        '''                            <div class="met">
                                <div class="lbl">Lost</div>
                                <div class="v red" id="mBLost">0</div>
                            </div>''',
        '''                            <div class="met">
                                <div class="lbl">Lost</div>
                                <div class="v red" id="mBLost">0</div>
                            </div>
                        </div>
                        <div class="sub-mg mg">
                            <div class="met">
                                <div class="lbl">Jitter</div>
                                <div class="v cyan" id="mBJit">0ms</div>
                            </div>'''
    )
    content = content.replace(
        '''                            <div class="met">
                                <div class="lbl">Lost</div>
                                <div class="v red" id="mRLost">0</div>
                            </div>''',
        '''                            <div class="met">
                                <div class="lbl">Lost</div>
                                <div class="v red" id="mRLost">0</div>
                            </div>
                        </div>
                        <div class="sub-mg mg">
                            <div class="met">
                                <div class="lbl">Jitter</div>
                                <div class="v cyan" id="mRJit">0ms</div>
                            </div>'''
    )
    
    content = content.replace(
        '''                            <div class="met">
                                <div class="lbl">Lost</div>
                                <div class="v red" id="mV3Lost">0</div>
                            </div>''',
        '''                            <div class="met">
                                <div class="lbl">Lost</div>
                                <div class="v red" id="mV3Lost">0</div>
                            </div>
                        </div>
                        <div class="sub-mg mg">
                            <div class="met">
                                <div class="lbl">Jitter</div>
                                <div class="v cyan" id="mV3Jit">0ms</div>
                            </div>'''
    )

    content = content.replace(
        '''                            <div class="met">
                                <div class="lbl">Lost</div>
                                <div class="v red" id="mV4Lost">0</div>
                            </div>''',
        '''                            <div class="met">
                                <div class="lbl">Lost</div>
                                <div class="v red" id="mV4Lost">0</div>
                            </div>
                        </div>
                        <div class="sub-mg mg">
                            <div class="met">
                                <div class="lbl">Jitter</div>
                                <div class="v cyan" id="mV4Jit">0ms</div>
                            </div>
                            <div class="met">
                                <div class="lbl">Stab Score</div>
                                <div class="v green" id="mV4StabScore">0.00</div>
                            </div>'''
    )

    # Calculate Jitter Function
    jitter_func = """
        function getJitter(latencies) {
            if (latencies.length < 2) return 0;
            let sum = 0;
            for(let i=0; i<latencies.length; i++) sum += latencies[i];
            const avg = sum / latencies.length;
            let sqDiff = 0;
            for(let i=0; i<latencies.length; i++) sqDiff += Math.pow(latencies[i] - avg, 2);
            return Math.sqrt(sqDiff / latencies.length);
        }
    """
    content = content.replace('function computeRouteStability() {', jitter_func + '\n        function computeRouteStability() {')

    # Record Delivery Latencies
    content = content.replace(
        's.cnt++; s.latSum += p.cost;',
        's.cnt++; s.latSum += p.cost; s.latencies.push(p.cost);'
    )

    # Update Scorecards UI
    update_ui = """
            document.getElementById('mBJit').textContent = getJitter(b.latencies).toFixed(1) + 'ms';
            document.getElementById('mRJit').textContent = getJitter(r.latencies).toFixed(1) + 'ms';
            document.getElementById('mV3Jit').textContent = getJitter(v3.latencies).toFixed(1) + 'ms';
            const v4Jit = getJitter(v4.latencies);
            document.getElementById('mV4Jit').textContent = v4Jit.toFixed(1) + 'ms';
            document.getElementById('mV4StabScore').textContent = (1.0 / (1.0 + v4Jit)).toFixed(3);
    """
    content = content.replace("makeLBar('lb0', 'Baseline', '#f04040', b.cnt, b.lost);", update_ui + "\n            makeLBar('lb0', 'Baseline', '#f04040', b.cnt, b.lost);")

    # 3. Trust Exploration & Congestion Penalty in costV4
    trust_explore = """
            // ② Dual Trust Compound: ETX and trust amplify each other
            let trustBase = (1 - tr) * 20;
            if (tag === 2 && tr >= 0.45 && tr <= 0.55) {
                trustBase = trustBase * 0.1; // Trust Exploration for Bulk
            }
            const etxTrustCompound = etxPenalty * (1 - tr); // double-penalty for bad-link + low-trust
    """
    content = content.replace(
        "const trustBase = (1 - tr) * 20;\n            const etxTrustCompound = etxPenalty * (1 - tr); // double-penalty for bad-link + low-trust",
        trust_explore
    )

    queue_penalty = """
            // Queue Load Congestion Penalty
            const qLoad = Math.min(1.0, (loadCount[vn.id] || 0) / 10.0);
            let congestionPenalty = 0;
            if (qLoad > 0.8) {
                congestionPenalty = Math.pow((qLoad - 0.8) / 0.2, 2) * 200.0;
            } else if (qLoad > 0.5) {
                congestionPenalty = (qLoad - 0.5) * 20.0;
            }

            const lCost = lbCost * w.wl + congestionPenalty;
    """
    content = content.replace("const lCost = lbCost * w.wl;", queue_penalty)

    # 4. Global Vars for backpressure
    content = content.replace('let nextSpawn = 0, lastFrame = 0;', 'let nextSpawn = 0, lastFrame = 0;\n        let backpressureActive = false, injectionRateMultiplier = 1.0;')

    # 5. Spawn logic rate
    content = content.replace('nextSpawn = simTime + 0.26 + Math.random() * 0.5;', 'nextSpawn = simTime + (0.26 + Math.random() * 0.5) * injectionRateMultiplier;')

    # 6. TTL
    content = content.replace(
        'lbTag: false,\n            };',
        'lbTag: false, ttl: 15,\n            };'
    )
    content = content.replace(
        'if (p.path[p.currentIdx] === p.failedAt) { p.alive = false; recordDelivery(p, false); }',
        'p.ttl--; if(p.ttl <= 0) { p.alive = false; p.failReason = "ttl"; recordDelivery(p, false); log("Packet dropped (TTL expired during loops)", "fail"); } else if (p.path[p.currentIdx] === p.failedAt) { p.alive = false; recordDelivery(p, false); }'
    )

    # 7. Bi-directional Feedback Loop
    backpressure_logic = """
            if (proto === 'pcertv4') {
                let totalQ = 0;
                for(let i=0; i<18; i++) totalQ += Math.min(1.0, (loadCount[i] || 0) / 10.0);
                const avgQ = totalQ / 18;
                if (avgQ > 0.6 && !backpressureActive) {
                    backpressureActive = true;
                    log(`⚠️ Network Backpressure: PerBlocks reducing injection rate by 20%`, 'crit');
                    injectionRateMultiplier = 1.2;
                } else if (avgQ < 0.3 && backpressureActive) {
                    backpressureActive = false;
                    log(`✅ Backpressure resolved. Restoring normal rate.`, 'sys');
                    injectionRateMultiplier = 1.0;
                }
            }
            const spd = 2.2;
    """
    content = content.replace('const spd = 2.2;', backpressure_logic)

    # 8. Queue load visualization
    queue_vis = """
                // Battery bar
                if (n.type !== 'mains') {
                    const bw = 22, bh = 3, bx = n.x - bw / 2, by = n.y + 23;
                    ctx.fillStyle = '#0a0e18'; ctx.fillRect(bx, by, bw, bh);
                    let fc = n.battery < 0.05 ? '#f04040' : n.battery < 0.2 ? '#e8b820' : '#20c060';
                    if ((isV3 || isV4) && n.battery < BAT_SOFT && n.battery >= BAT_HARD) fc = '#f07830';
                    ctx.fillStyle = fc; ctx.fillRect(bx, by, bw * n.battery, bh);
                }
                
                if (isV4) {
                    const bw = 22, bh = 2, bx = n.x - bw / 2, by = n.y + (n.type !== 'mains' ? 27 : 23);
                    ctx.fillStyle = '#0a0e18'; ctx.fillRect(bx, by, bw, bh);
                    const qPct = Math.min(1.0, (loadCount[n.id] || 0) / 10.0);
                    let qc = qPct > 0.8 ? '#f04040' : qPct > 0.5 ? '#f07830' : '#08c8e8';
                    ctx.fillStyle = qc; ctx.fillRect(bx, by, bw * qPct, bh);
                }
    """
    old_battery_bar = """                // Battery bar
                if (n.type !== 'mains') {
                    const bw = 22, bh = 3, bx = n.x - bw / 2, by = n.y + 23;
                    ctx.fillStyle = '#0a0e18'; ctx.fillRect(bx, by, bw, bh);
                    let fc = n.battery < 0.05 ? '#f04040' : n.battery < 0.2 ? '#e8b820' : '#20c060';
                    if ((isV3 || isV4) && n.battery < BAT_SOFT && n.battery >= BAT_HARD) fc = '#f07830';
                    ctx.fillStyle = fc; ctx.fillRect(bx, by, bw * n.battery, bh);
                }"""
    content = content.replace(old_battery_bar, queue_vis)

    # 9. Buttons for Kill Node & Burst
    btns = """
            <button class="btn btn-crit" id="btnCrit">🚨 Inject Critical</button>
            <button class="btn btn-atk" id="btnKill">💀 Kill Node</button>
            <button class="btn btn-bulk" id="btnBurst">🌊 Burst Inject</button>
            <button class="btn btn-v4" id="btnDegrade">📡 Degrade Link ETX</button>
    """
    content = content.replace(
        '''            <button class="btn btn-crit" id="btnCrit">🚨 Inject Critical</button>
            <button class="btn btn-atk" id="btnAtk">⚠️ Degrade Node</button>
            <button class="btn btn-bulk" id="btnBulk">📦 Inject Bulk</button>
            <button class="btn btn-v4" id="btnDegrade">📡 Degrade Link ETX</button>''',
        btns
    )

    # 10. Button logic
    btn_logic = """
            document.getElementById('btnKill').onclick = () => {
                const candidates = [2, 3, 5, 7, 8, 10, 13, 15, 16].filter(i => !nodes[i].dead);
                if (!candidates.length) return;
                const pick = candidates[Math.floor(Math.random() * candidates.length)];
                nodes[pick].battery = 0; nodes[pick].dead = true;
                log(`💀 Node ${pick} manually KILLED! Triggering mid-flight reroutes...`, 'fail');
                // Reroute in-flight packets
                packets.forEach(p => {
                    if (p.alive && p.path.slice(p.currentIdx).includes(pick)) {
                        const cur = p.path[p.currentIdx];
                        const newR = buildPath(p.tag);
                        if (newR && !newR.failReason) {
                            p.path = p.path.slice(0, p.currentIdx).concat(newR.path);
                            log(`🔄 Mid-flight reroute: packet diverted around dead Node ${pick}`, 'sys');
                        } else {
                            p.alive = false; p.failReason = "dead"; recordDelivery(p, false);
                            log(`💀 Reroute failed: packet dropped, no alternate route`, 'fail');
                        }
                    }
                });
            };
            document.getElementById('btnBurst').onclick = () => {
                log(`🌊 BURST: 10 Critical packets injected simultaneously`, 'crit');
                for(let i=0; i<10; i++) spawnPacket(0);
            };
    """
    content = content.replace(
        "document.getElementById('btnAtk').onclick = randomDegradeNode;",
        btn_logic
    )
    content = content.replace("document.getElementById('btnBulk').onclick = () => spawnPacket(2);", "")

    with open(filepath, 'w') as f:
        f.write(content)

modify_file('index_v3.html')
