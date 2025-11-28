import React from 'react';

const Tachometer = ({ rpm, maxRpm = 8000 }) => {
    // Calculate angle
    // 0 RPM = -210 degrees (8 o'clock)
    // Max RPM = 30 degrees (4 o'clock)
    // Range = 240 degrees
    const startAngle = -210;
    const endAngle = 30;
    const angleRange = endAngle - startAngle;

    const normalizedRpm = Math.min(Math.max(rpm, 0), maxRpm);
    const angle = startAngle + (normalizedRpm / maxRpm) * angleRange;

    // Generate ticks
    const ticks = [];
    for (let i = 0; i <= 8; i++) {
        const tickRpm = i * 1000;
        const tickAngle = startAngle + (tickRpm / maxRpm) * angleRange;
        const isRedZone = i >= 7;

        // Convert angle to radians for position calculation
        const rad = (tickAngle * Math.PI) / 180;
        const radius = 80;
        const textRadius = 60; // Moved text slightly inward

        const x1 = 100 + radius * Math.cos(rad);
        const y1 = 100 + radius * Math.sin(rad);
        const x2 = 100 + (radius - 10) * Math.cos(rad);
        const y2 = 100 + (radius - 10) * Math.sin(rad);

        const tx = 100 + textRadius * Math.cos(rad);
        const ty = 100 + textRadius * Math.sin(rad);

        ticks.push(
            <g key={i}>
                <line
                    x1={x1} y1={y1} x2={x2} y2={y2}
                    stroke={isRedZone ? "#ef4444" : "#3b82f6"}
                    strokeWidth="3"
                />
                <text
                    x={tx} y={ty}
                    fill="white"
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fontSize="14"
                    fontWeight="bold"
                    style={{ fontFamily: 'Inter, sans-serif' }}
                >
                    {i}
                </text>
            </g>
        );
    }

    // Generate sub-ticks
    const subTicks = [];
    for (let i = 0; i <= 80; i++) {
        if (i % 10 === 0) continue; // Skip main ticks
        const tickRpm = i * 100;
        const tickAngle = startAngle + (tickRpm / maxRpm) * angleRange;
        const rad = (tickAngle * Math.PI) / 180;
        const radius = 80;

        const x1 = 100 + radius * Math.cos(rad);
        const y1 = 100 + radius * Math.sin(rad);
        const x2 = 100 + (radius - 6) * Math.cos(rad);
        const y2 = 100 + (radius - 6) * Math.sin(rad);

        subTicks.push(
            <line
                key={`sub-${i}`}
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="rgba(59, 130, 246, 0.5)"
                strokeWidth="1.5"
            />
        );
    }

    // Arc Paths
    // Radius 88 (just outside ticks)
    const arcRadius = 88;

    // Blue Arc: -210 to 0 degrees (0 to 7000 RPM)
    // Start (-210 deg): x = 100 + 88*cos(-210*PI/180) = 100 + 88*(-0.866) = 23.8
    //                   y = 100 + 88*sin(-210*PI/180) = 100 + 88*(0.5) = 144
    // End (0 deg):      x = 188, y = 100
    const blueArcPath = `M 23.8 144 A ${arcRadius} ${arcRadius} 0 1 1 188 100`;

    // Red Arc: 0 to 30 degrees (7000 to 8000 RPM)
    // Start (0 deg):    x = 188, y = 100
    // End (30 deg):     x = 100 + 88*cos(30*PI/180) = 100 + 88*(0.866) = 176.2
    //                   y = 100 + 88*sin(30*PI/180) = 100 + 88*(0.5) = 144
    const redArcPath = `M 188 100 A ${arcRadius} ${arcRadius} 0 0 1 176.2 144`;

    return (
        <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <svg viewBox="0 0 200 200" style={{ width: '100%', height: '100%', maxWidth: '300px' }}>
                {/* Background Gradient Definition */}
                <defs>
                    <radialGradient id="gaugeGradient" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
                        <stop offset="0%" stopColor="#1e293b" stopOpacity="1" />
                        <stop offset="80%" stopColor="#0f172a" stopOpacity="1" />
                        <stop offset="100%" stopColor="#000" stopOpacity="1" />
                    </radialGradient>
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                    <filter id="needleGlow">
                        <feGaussianBlur stdDeviation="1.5" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                {/* Gauge Background */}
                <circle cx="100" cy="100" r="95" fill="url(#gaugeGradient)" stroke="#334155" strokeWidth="2" />

                {/* Arcs */}
                <path
                    d={blueArcPath}
                    fill="none"
                    stroke="rgba(59, 130, 246, 0.3)"
                    strokeWidth="12"
                    strokeLinecap="butt"
                />
                <path
                    d={redArcPath}
                    fill="none"
                    stroke="rgba(239, 68, 68, 0.6)"
                    strokeWidth="12"
                    strokeLinecap="butt"
                />

                {/* Ticks */}
                {subTicks}
                {ticks}

                {/* RPM Label */}
                <text x="100" y="135" textAnchor="middle" fill="#94a3b8" fontSize="10" fontWeight="bold">x1000r/min</text>

                {/* Needle */}
                {/* Rotated group for the needle */}
                <g transform={`rotate(${angle}, 100, 100)`} style={{ transition: 'transform 0.1s cubic-bezier(0.4, 0.0, 0.2, 1)' }}>
                    {/* Needle Shape: Tapered triangle from center to tip */}
                    {/* Center is 100,100. Tip is at 185,100 (radius 85) */}
                    {/* Base width 6px (100, 97 to 100, 103) */}
                    <polygon
                        points="100,97 185,100 100,103"
                        fill="#f8fafc"
                        filter="url(#needleGlow)"
                    />
                    {/* Center Pivot Cap */}
                    <circle cx="100" cy="100" r="8" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="2" />
                    <circle cx="100" cy="100" r="3" fill="#334155" />
                </g>

                {/* Digital Display */}
                <rect x="75" y="155" width="50" height="22" rx="4" fill="#0f172a" stroke="#334155" />
                <text x="100" y="171" textAnchor="middle" fill="#3b82f6" fontSize="14" fontWeight="bold" style={{ fontFamily: 'monospace' }}>
                    {rpm}
                </text>
            </svg>
        </div>
    );
};

export default Tachometer;
