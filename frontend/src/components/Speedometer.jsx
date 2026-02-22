import React, { useEffect, useRef, useCallback } from 'react';

const Speedometer = ({ speed, gear, maxSpeed = 120 }) => {
    const canvasRef = useRef(null);
    const animRef = useRef(null);
    const currentAngleRef = useRef(-210);
    const velocityRef = useRef(0);

    const startAngle = -210;
    const endAngle = 30;
    const angleRange = endAngle - startAngle;

    const speedToAngle = useCallback((s) => {
        const clamped = Math.min(Math.max(s, 0), maxSpeed);
        return startAngle + (clamped / maxSpeed) * angleRange;
    }, [maxSpeed, angleRange, startAngle]);

    const degToRad = (deg) => (deg * Math.PI) / 180;

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const container = canvas.parentElement;
        const containerSize = Math.min(container.clientWidth, container.clientHeight);
        const size = Math.max(containerSize, 280);

        canvas.style.width = size + 'px';
        canvas.style.height = size + 'px';
        canvas.width = size * 2;
        canvas.height = size * 2;

        const ctx = canvas.getContext('2d');
        ctx.setTransform(2, 0, 0, 2, 0, 0);

        const cx = size / 2;
        const cy = size / 2;
        const radius = size * 0.38;
        const targetAngle = speedToAngle(speed);



        const draw = () => {
            const diff = targetAngle - currentAngleRef.current;
            velocityRef.current = velocityRef.current * 0.80 + diff * 0.07;
            currentAngleRef.current += velocityRef.current;

            const currentDeg = currentAngleRef.current;
            const normalizedValue = Math.max(0, (currentDeg - startAngle) / angleRange);

            ctx.clearRect(0, 0, size, size);

            // === Background ===
            const bgGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius + 25);
            bgGrad.addColorStop(0, '#0c1a2e');
            bgGrad.addColorStop(0.6, '#081220');
            bgGrad.addColorStop(1, '#020810');
            ctx.beginPath();
            ctx.arc(cx, cy, radius + 22, 0, Math.PI * 2);
            ctx.fillStyle = bgGrad;
            ctx.fill();

            // Outer ring
            ctx.beginPath();
            ctx.arc(cx, cy, radius + 22, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(0, 255, 170, 0.12)';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Inner shadow ring
            ctx.beginPath();
            ctx.arc(cx, cy, radius + 16, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(0, 255, 170, 0.06)';
            ctx.lineWidth = 1;
            ctx.stroke();

            // === Dim Background Arc ===
            ctx.beginPath();
            ctx.arc(cx, cy, radius, degToRad(startAngle), degToRad(endAngle));
            ctx.strokeStyle = 'rgba(0, 255, 170, 0.06)';
            ctx.lineWidth = 16;
            ctx.lineCap = 'butt';
            ctx.stroke();

            // === Glowing Active Arc ===
            if (normalizedValue > 0.001) {
                const fillStart = degToRad(startAngle);
                const fillEnd = degToRad(currentDeg);

                // Layer 3: Outer glow
                ctx.beginPath();
                ctx.arc(cx, cy, radius, fillStart, fillEnd);
                ctx.strokeStyle = 'rgba(0, 255, 170, 0.06)';
                ctx.lineWidth = 40;
                ctx.lineCap = 'butt';
                ctx.stroke();

                // Layer 2: Medium glow
                ctx.beginPath();
                ctx.arc(cx, cy, radius, fillStart, fillEnd);
                ctx.strokeStyle = 'rgba(0, 255, 170, 0.12)';
                ctx.lineWidth = 26;
                ctx.stroke();

                // Layer 1: Core arc
                ctx.beginPath();
                ctx.arc(cx, cy, radius, fillStart, fillEnd);
                const arcGrad = ctx.createLinearGradient(
                    cx + radius * Math.cos(fillStart), cy + radius * Math.sin(fillStart),
                    cx + radius * Math.cos(fillEnd), cy + radius * Math.sin(fillEnd)
                );
                arcGrad.addColorStop(0, 'rgba(0, 200, 130, 0.4)');
                arcGrad.addColorStop(1, `rgba(0, 255, 170, ${0.7 + normalizedValue * 0.3})`);
                ctx.strokeStyle = arcGrad;
                ctx.lineWidth = 16;
                ctx.stroke();

                // Leading edge bloom
                const lx = cx + radius * Math.cos(fillEnd);
                const ly = cy + radius * Math.sin(fillEnd);
                const bloomGrad = ctx.createRadialGradient(lx, ly, 0, lx, ly, 25);
                bloomGrad.addColorStop(0, `rgba(0, 255, 170, ${0.5 + normalizedValue * 0.4})`);
                bloomGrad.addColorStop(0.4, 'rgba(0, 255, 170, 0.15)');
                bloomGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
                ctx.beginPath();
                ctx.arc(lx, ly, 25, 0, Math.PI * 2);
                ctx.fillStyle = bloomGrad;
                ctx.fill();
            }

            // === Tick Marks ===
            for (let i = 0; i <= 120; i += 5) {
                const tickAngle = startAngle + (i / maxSpeed) * angleRange;
                const rad = degToRad(tickAngle);
                const isMajor = i % 20 === 0;
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
                    ctx.strokeStyle = '#00ffaa';
                    ctx.lineWidth = isMajor ? 3 : 1.5;
                    if (isMajor) { ctx.shadowColor = '#00ffaa'; ctx.shadowBlur = 8; }
                } else {
                    ctx.strokeStyle = 'rgba(0, 255, 170, 0.15)';
                    ctx.lineWidth = isMajor ? 2 : 1;
                    ctx.shadowBlur = 0;
                }
                ctx.stroke();
                ctx.shadowBlur = 0;

                if (isMajor) {
                    const textR = radius - 28;
                    const tx = cx + textR * Math.cos(rad);
                    const ty = cy + textR * Math.sin(rad);
                    ctx.font = `bold ${Math.round(size * 0.055)}px Inter, sans-serif`;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = isLit ? '#e2f1ff' : 'rgba(136, 146, 176, 0.4)';
                    ctx.fillText(String(i), tx, ty);
                }
            }

            // === Unit Label ===
            ctx.font = `bold ${Math.round(size * 0.045)}px Inter, sans-serif`;
            ctx.textAlign = 'center';
            ctx.fillStyle = 'rgba(136, 146, 176, 0.75)';
            ctx.fillText('KM/H', cx, cy + radius * 0.38);

            // === Needle ===
            const needleRad = degToRad(currentDeg);
            const needleLen = radius - 10;
            const nx = cx + needleLen * Math.cos(needleRad);
            const ny = cy + needleLen * Math.sin(needleRad);

            ctx.shadowColor = '#00ffaa';
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

            // === Center Gear Display ===
            const gearR = size * 0.085;
            const gearGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, gearR);
            gearGrad.addColorStop(0, '#0f1d32');
            gearGrad.addColorStop(1, '#0a1628');
            ctx.beginPath();
            ctx.arc(cx, cy, gearR, 0, Math.PI * 2);
            ctx.fillStyle = gearGrad;
            ctx.fill();
            ctx.strokeStyle = 'rgba(0, 255, 170, 0.35)';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // Gear number
            const gearFontSize = Math.round(size * 0.1);
            ctx.font = `bold ${gearFontSize}px Inter, sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#00ffaa';
            ctx.shadowColor = '#00ffaa';
            ctx.shadowBlur = 12;
            ctx.fillText(gear === 0 ? 'N' : String(gear), cx, cy - 2);
            ctx.shadowBlur = 0;

            // "GEAR" label
            ctx.font = `bold ${Math.round(size * 0.035)}px Inter, sans-serif`;
            ctx.fillStyle = 'rgba(136, 146, 176, 0.7)';
            ctx.fillText('GEAR', cx, cy + gearR * 0.7);

            // === Large Digital Speed Display ===
            const displayW = size * 0.28;
            const displayH = size * 0.12;
            const displayX = cx - displayW / 2;
            const displayY = cy + radius * 0.48;
            ctx.fillStyle = 'rgba(8, 18, 32, 0.85)';
            ctx.strokeStyle = 'rgba(0, 255, 170, 0.35)';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.roundRect(displayX, displayY, displayW, displayH, 6);
            ctx.fill();
            ctx.stroke();

            const fontSize = Math.round(size * 0.09);
            ctx.font = `bold ${fontSize}px 'Courier New', monospace`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#00ffaa';
            ctx.shadowColor = '#00ffaa';
            ctx.shadowBlur = 12;
            ctx.fillText(String(speed), cx, displayY + displayH / 2);
            ctx.shadowBlur = 0;



            if (Math.abs(velocityRef.current) > 0.01 || Math.abs(diff) > 0.1) {
                animRef.current = requestAnimationFrame(draw);
            }
        };

        if (animRef.current) cancelAnimationFrame(animRef.current);
        animRef.current = requestAnimationFrame(draw);
        return () => { if (animRef.current) cancelAnimationFrame(animRef.current); };
    }, [speed, gear, speedToAngle, maxSpeed, angleRange, startAngle, endAngle]);

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

export default Speedometer;
