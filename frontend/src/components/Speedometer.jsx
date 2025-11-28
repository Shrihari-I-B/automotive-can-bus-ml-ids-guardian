import React from 'react';

const Speedometer = ({ speed, gear, maxSpeed = 120 }) => {
    // Calculate angle
    // 0 Speed = -210 degrees
    // Max Speed = 30 degrees
    // Range = 240 degrees
    const startAngle = -210;
    const endAngle = 30;
    const angleRange = endAngle - startAngle;

    const normalizedSpeed = Math.min(Math.max(speed, 0), maxSpeed);
    const angle = startAngle + (normalizedSpeed / maxSpeed) * angleRange;

    // Generate ticks
    const ticks = [];
    // Steps of 20 for main ticks: 0, 20, 40, 60, 80, 100, 120
    for (let i = 0; i <= 120; i += 20) {
        const tickAngle = startAngle + (i / maxSpeed) * angleRange;

        // Convert angle to radians for position calculation
        const rad = (tickAngle * Math.PI) / 180;
        const radius = 80;
        const textRadius = 60;

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
                    stroke="#3b82f6"
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

    // Generate sub-ticks (every 10 km/h)
    const subTicks = [];
    for (let i = 0; i <= 120; i += 10) {
        if (i % 20 === 0) continue; // Skip main ticks
        const tickAngle = startAngle + (i / maxSpeed) * angleRange;
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

    // Arc Path (Blue only, no red zone for speed usually, or maybe high speed warning?)
    // Let's keep it simple blue for now to match tachometer style
    const arcRadius = 88;
    // Start (-210 deg) to End (30 deg)
    // Start: x = 100 + 88*cos(-210) = 23.8, y = 144
    // End:   x = 100 + 88*cos(30) = 176.2, y = 144
    // Large arc flag 1 because 240 > 180
    const arcPath = `M 23.8 144 A ${arcRadius} ${arcRadius} 0 1 1 176.2 144`;

    return (
        <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <svg viewBox="0 0 200 200" style={{ width: '100%', height: '100%', maxWidth: '300px' }}>
                {/* Background Gradient Definition */}
                <defs>
                    <radialGradient id="speedoGradient" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
                        <stop offset="0%" stopColor="#1e293b" stopOpacity="1" />
                        <stop offset="80%" stopColor="#0f172a" stopOpacity="1" />
                        <stop offset="100%" stopColor="#000" stopOpacity="1" />
                    </radialGradient>
                    <filter id="glowSpeedo">
                        <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                    <filter id="needleGlowSpeedo">
                        <feGaussianBlur stdDeviation="1.5" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                {/* Gauge Background */}
                <circle cx="100" cy="100" r="95" fill="url(#speedoGradient)" stroke="#334155" strokeWidth="2" />

                {/* Arc */}
                <path
                    d={arcPath}
                    fill="none"
                    stroke="rgba(59, 130, 246, 0.3)"
                    strokeWidth="12"
                    strokeLinecap="butt"
                />

                {/* Ticks */}
                {subTicks}
                {ticks}

                {/* Speed Label */}
                <text x="100" y="135" textAnchor="middle" fill="#94a3b8" fontSize="10" fontWeight="bold">km/h</text>

                {/* Needle */}
                <g transform={`rotate(${angle}, 100, 100)`} style={{ transition: 'transform 0.1s cubic-bezier(0.4, 0.0, 0.2, 1)' }}>
                    <polygon
                        points="100,97 185,100 100,103"
                        fill="#f8fafc"
                        filter="url(#needleGlowSpeedo)"
                    />
                    <circle cx="100" cy="100" r="8" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="2" />
                    <circle cx="100" cy="100" r="3" fill="#334155" />
                </g>

                {/* Center Info (Gear & Speed) */}
                {/* We place this slightly below center or overlaying the needle pivot? 
            The user image shows gear in center. Let's put Gear in center big, and Speed below it.
            But wait, the needle pivot is in the center. 
            If we look at the user image 2, the gear is in the center, and the needle rotates AROUND it (or behind it).
            Actually, in image 2, the needle seems to be coming from the outer ring? No, it's a standard needle.
            Let's put the Gear Indicator in the center, covering the needle pivot.
        */}

                {/* Center Circle for Gear */}
                <circle cx="100" cy="100" r="25" fill="#0f172a" stroke="#334155" strokeWidth="2" />

                {/* Gear Value */}
                <text x="100" y="105" textAnchor="middle" fill="#3b82f6" fontSize="24" fontWeight="bold" style={{ fontFamily: 'Inter, sans-serif' }}>
                    {gear === 0 ? 'N' : gear}
                </text>
                <text x="100" y="118" textAnchor="middle" fill="#64748b" fontSize="8">GEAR</text>

                {/* Digital Speed Display (Bottom) */}
                <rect x="75" y="155" width="50" height="22" rx="4" fill="#0f172a" stroke="#334155" />
                <text x="100" y="171" textAnchor="middle" fill="#3b82f6" fontSize="14" fontWeight="bold" style={{ fontFamily: 'monospace' }}>
                    {speed}
                </text>
            </svg>
        </div>
    );
};

export default Speedometer;
