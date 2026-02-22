import React, { useEffect, useRef, useCallback } from 'react';

const Tachometer = ({ rpm, maxRpm = 8000 }) => {
    const canvasRef = useRef(null);
    const animRef = useRef(null);
    const currentAngleRef = useRef(-210);
    const velocityRef = useRef(0);

    const startAngle = -210;
    const endAngle = 30;
    const angleRange = endAngle - startAngle;

    const rpmToAngle = useCallback((r) => {
        const clamped = Math.min(Math.max(r, 0), maxRpm);
        return startAngle + (clamped / maxRpm) * angleRange;
    }, [maxRpm, angleRange, startAngle]);

    const degToRad = (deg) => (deg * Math.PI) / 180;

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        // Get actual rendered size and enforce square
        const container = canvas.parentElement;
        const containerSize = Math.min(container.clientWidth, container.clientHeight);
        const size = Math.max(containerSize, 280);

        canvas.style.width = size + 'px';
        canvas.style.height = size + 'px';
        canvas.width = size * 2;
        canvas.height = size * 2;

        const ctx = canvas.getContext('2d');
        ctx.setTransform(2, 0, 0, 2, 0, 0); // HiDPI

        const cx = size / 2;
        const cy = size / 2;
        const radius = size * 0.38; // ~38% of canvas for the main arc
        const targetAngle = rpmToAngle(rpm);



        const draw = () => {
            // Spring physics
            const diff = targetAngle - currentAngleRef.current;
            velocityRef.current = velocityRef.current * 0.78 + diff * 0.08;
            currentAngleRef.current += velocityRef.current;

            const currentDeg = currentAngleRef.current;
            const normalizedValue = Math.max(0, (currentDeg - startAngle) / angleRange);

            ctx.clearRect(0, 0, size, size);

            // === Background Circle ===
            const bgGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius + 25);
            bgGrad.addColorStop(0, '#0c1a2e');
            bgGrad.addColorStop(0.6, '#081220');
            bgGrad.addColorStop(1, '#020810');
            ctx.beginPath();
            ctx.arc(cx, cy, radius + 22, 0, Math.PI * 2);
            ctx.fillStyle = bgGrad;
            ctx.fill();

            // Outer glowing ring
            ctx.beginPath();
            ctx.arc(cx, cy, radius + 22, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(0, 229, 255, 0.12)';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Inner shadow ring
            ctx.beginPath();
            ctx.arc(cx, cy, radius + 16, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(0, 229, 255, 0.06)';
            ctx.lineWidth = 1;
            ctx.stroke();

            // === Dim Background Arc (inactive portion) ===
            ctx.beginPath();
            ctx.arc(cx, cy, radius, degToRad(startAngle), degToRad(endAngle));
            ctx.strokeStyle = 'rgba(0, 229, 255, 0.06)';
            ctx.lineWidth = 16;
            ctx.lineCap = 'butt';
            ctx.stroke();

            // === Glowing Active Arc ===
            if (normalizedValue > 0.001) {
                const fillStart = degToRad(startAngle);
                const fillEnd = degToRad(currentDeg);

                // Layer 3: Outermost soft glow
                ctx.beginPath();
                ctx.arc(cx, cy, radius, fillStart, fillEnd);
                ctx.strokeStyle = `rgba(0, 229, 255, 0.06)`;
                ctx.lineWidth = 40;
                ctx.lineCap = 'butt';
                ctx.stroke();

                // Layer 2: Medium glow
                ctx.beginPath();
                ctx.arc(cx, cy, radius, fillStart, fillEnd);
                ctx.strokeStyle = `rgba(0, 229, 255, 0.12)`;
                ctx.lineWidth = 26;
                ctx.stroke();

                // Layer 1: Core bright arc with gradient
                ctx.beginPath();
                ctx.arc(cx, cy, radius, fillStart, fillEnd);
                const arcGrad = ctx.createLinearGradient(
                    cx + radius * Math.cos(fillStart), cy + radius * Math.sin(fillStart),
                    cx + radius * Math.cos(fillEnd), cy + radius * Math.sin(fillEnd)
                );
                if (normalizedValue < 0.8) {
                    arcGrad.addColorStop(0, 'rgba(0, 160, 230, 0.5)');
                    arcGrad.addColorStop(1, `rgba(0, 229, 255, ${0.7 + normalizedValue * 0.3})`);
                } else {
                    arcGrad.addColorStop(0, 'rgba(0, 160, 230, 0.5)');
                    arcGrad.addColorStop(0.65, 'rgba(0, 229, 255, 0.9)');
                    arcGrad.addColorStop(1, 'rgba(255, 0, 85, 0.95)');
                }
                ctx.strokeStyle = arcGrad;
                ctx.lineWidth = 16;
                ctx.stroke();

                // Leading edge bloom
                const lx = cx + radius * Math.cos(fillEnd);
                const ly = cy + radius * Math.sin(fillEnd);
                const bloomColor = normalizedValue > 0.85 ? '255, 0, 85' : '0, 229, 255';
                const bloomGrad = ctx.createRadialGradient(lx, ly, 0, lx, ly, 25);
                bloomGrad.addColorStop(0, `rgba(${bloomColor}, ${0.5 + normalizedValue * 0.4})`);
                bloomGrad.addColorStop(0.4, `rgba(${bloomColor}, 0.15)`);
                bloomGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
                ctx.beginPath();
                ctx.arc(lx, ly, 25, 0, Math.PI * 2);
                ctx.fillStyle = bloomGrad;
                ctx.fill();
            }

            // === Red Zone Indicator ===
            const redZoneStart = startAngle + (7000 / maxRpm) * angleRange;
            ctx.beginPath();
            ctx.arc(cx, cy, radius + 16, degToRad(redZoneStart), degToRad(endAngle));
            ctx.strokeStyle = normalizedValue > 0.85 ? 'rgba(255, 0, 85, 0.6)' : 'rgba(255, 0, 85, 0.12)';
            ctx.lineWidth = 3;
            ctx.stroke();

            // === Tick Marks ===
            for (let i = 0; i <= 80; i++) {
                const tickRpm = i * 100;
                const tickAngle = startAngle + (tickRpm / maxRpm) * angleRange;
                const rad = degToRad(tickAngle);
                const isMajor = i % 10 === 0;
                const isRedZone = tickRpm >= 7000;
                const isLit = tickAngle <= currentDeg;

                const len = isMajor ? 14 : 7;
                const outer = radius - 3;
                const x1 = cx + outer * Math.cos(rad);
                const y1 = cy + outer * Math.sin(rad);
                const x2 = cx + (outer - len) * Math.cos(rad);
                const y2 = cy + (outer - len) * Math.sin(rad);

                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);

                if (isLit) {
                    ctx.strokeStyle = isRedZone ? '#ff0055' : '#00e5ff';
                    ctx.lineWidth = isMajor ? 3 : 1.5;
                    if (isMajor) { ctx.shadowColor = isRedZone ? '#ff0055' : '#00e5ff'; ctx.shadowBlur = 8; }
                } else {
                    ctx.strokeStyle = isRedZone ? 'rgba(255, 0, 85, 0.18)' : 'rgba(0, 229, 255, 0.15)';
                    ctx.lineWidth = isMajor ? 2 : 1;
                    ctx.shadowBlur = 0;
                }
                ctx.stroke();
                ctx.shadowBlur = 0;

                // Major tick number labels
                if (isMajor) {
                    const textR = radius - 28;
                    const tx = cx + textR * Math.cos(rad);
                    const ty = cy + textR * Math.sin(rad);
                    ctx.font = `bold ${Math.round(size * 0.055)}px Inter, sans-serif`;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = isLit ? (isRedZone ? '#ff0055' : '#e2f1ff') : 'rgba(136, 146, 176, 0.4)';
                    ctx.fillText(String(i / 10), tx, ty);
                }
            }

            // === Unit Label ===
            ctx.font = `bold ${Math.round(size * 0.045)}px Inter, sans-serif`;
            ctx.textAlign = 'center';
            ctx.fillStyle = 'rgba(136, 146, 176, 0.75)';
            ctx.fillText('x1000 RPM', cx, cy + radius * 0.35);

            // === Needle ===
            const needleRad = degToRad(currentDeg);
            const needleLen = radius - 10;
            const nx = cx + needleLen * Math.cos(needleRad);
            const ny = cy + needleLen * Math.sin(needleRad);

            // Needle glow
            ctx.shadowColor = normalizedValue > 0.85 ? '#ff0055' : '#00e5ff';
            ctx.shadowBlur = 15;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(nx, ny);
            ctx.strokeStyle = '#f0f4ff';
            ctx.lineWidth = 3;
            ctx.lineCap = 'round';
            ctx.stroke();
            ctx.shadowBlur = 0;

            // Tail
            const tailX = cx - 18 * Math.cos(needleRad);
            const tailY = cy - 18 * Math.sin(needleRad);
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(tailX, tailY);
            ctx.strokeStyle = 'rgba(240, 244, 255, 0.4)';
            ctx.lineWidth = 3.5;
            ctx.stroke();

            // Center cap
            const capGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 10);
            capGrad.addColorStop(0, '#e2f1ff');
            capGrad.addColorStop(0.5, '#8892b0');
            capGrad.addColorStop(1, '#334155');
            ctx.beginPath();
            ctx.arc(cx, cy, 9, 0, Math.PI * 2);
            ctx.fillStyle = capGrad;
            ctx.fill();
            ctx.strokeStyle = 'rgba(0, 229, 255, 0.3)';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // === Large Digital RPM Display ===
            const displayW = size * 0.28;
            const displayH = size * 0.12;
            const displayX = cx - displayW / 2;
            const displayY = cy + radius * 0.48;
            ctx.fillStyle = 'rgba(8, 18, 32, 0.85)';
            ctx.strokeStyle = 'rgba(0, 229, 255, 0.35)';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.roundRect(displayX, displayY, displayW, displayH, 6);
            ctx.fill();
            ctx.stroke();

            const fontSize = Math.round(size * 0.09);
            ctx.font = `bold ${fontSize}px 'Courier New', monospace`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#00e5ff';
            ctx.shadowColor = '#00e5ff';
            ctx.shadowBlur = 12;
            ctx.fillText(String(rpm), cx, displayY + displayH / 2);
            ctx.shadowBlur = 0;



            if (Math.abs(velocityRef.current) > 0.01 || Math.abs(diff) > 0.1) {
                animRef.current = requestAnimationFrame(draw);
            }
        };

        if (animRef.current) cancelAnimationFrame(animRef.current);
        animRef.current = requestAnimationFrame(draw);
        return () => { if (animRef.current) cancelAnimationFrame(animRef.current); };
    }, [rpm, rpmToAngle, maxRpm, angleRange, startAngle, endAngle]);

    return (
        <div style={{
            position: 'relative', width: '100%', height: '100%',
            display: 'flex', justifyContent: 'center', alignItems: 'center',
            overflow: 'hidden',
        }}>
            <canvas ref={canvasRef} />
        </div>
    );
};

export default Tachometer;
