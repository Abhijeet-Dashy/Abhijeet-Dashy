<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Abhijeet - Developer Profile</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: #000;
            color: #fff;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            overflow-x: hidden;
            padding: 60px 20px;
            line-height: 1.6;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        /* Subtle dot matrix background */
        .dot-matrix {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            opacity: 0.08;
            pointer-events: none;
            background-image: radial-gradient(circle, #fff 1px, transparent 1px);
            background-size: 40px 40px;
        }

        /* Header Section */
        .header {
            position: relative;
            z-index: 1;
            margin-bottom: 60px;
            opacity: 0;
            animation: fadeIn 1s ease forwards;
        }

        .header h1 {
            font-size: 3rem;
            font-weight: 600;
            letter-spacing: -1px;
            margin-bottom: 8px;
        }

        .header h2 {
            font-size: 1.1rem;
            font-weight: 400;
            color: #666;
        }

        /* Divider */
        .divider {
            width: 100%;
            height: 1px;
            background: #222;
            margin: 50px 0;
            position: relative;
            overflow: hidden;
        }

        .divider::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 40%;
            height: 100%;
            background: linear-gradient(90deg, transparent, #fff, transparent);
            animation: slide 3s ease-in-out infinite;
        }

        @keyframes slide {
            0%, 100% { left: -100%; }
            50% { left: 100%; }
        }

        /* Section Styling */
        .section {
            margin: 50px 0;
            opacity: 0;
            animation: fadeIn 1s ease forwards;
            position: relative;
            z-index: 1;
        }

        .section:nth-child(3) { animation-delay: 0.2s; }
        .section:nth-child(4) { animation-delay: 0.4s; }
        .section:nth-child(5) { animation-delay: 0.6s; }
        .section:nth-child(6) { animation-delay: 0.8s; }

        .section h3 {
            font-size: 1.5rem;
            margin-bottom: 20px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* What I Do */
        .cards {
            display: grid;
            gap: 15px;
        }

        .card {
            border: 1px solid #222;
            padding: 20px;
            transition: border-color 0.3s ease;
        }

        .card:hover {
            border-color: #444;
        }

        .card::before {
            content: '○';
            margin-right: 12px;
            color: #666;
        }

        /* Tech Stack */
        .tech-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 12px;
            margin-top: 20px;
        }

        .tech-item {
            border: 1px solid #222;
            padding: 18px 10px;
            text-align: center;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }

        .tech-item:hover {
            border-color: #fff;
            transform: translateY(-2px);
        }

        /* Current Focus */
        .focus-list {
            list-style: none;
        }

        .focus-item {
            padding: 15px 0;
            border-bottom: 1px solid #111;
            transition: padding-left 0.3s ease;
        }

        .focus-item:last-child {
            border-bottom: none;
        }

        .focus-item::before {
            content: '→';
            margin-right: 12px;
            color: #666;
            transition: margin-right 0.3s ease;
        }

        .focus-item:hover {
            padding-left: 10px;
        }

        .focus-item:hover::before {
            margin-right: 16px;
        }

        /* Footer */
        .footer {
            text-align: center;
            margin-top: 80px;
            padding: 30px;
            border: 1px solid #222;
            opacity: 0;
            animation: fadeIn 1s ease 1s forwards;
        }

        .footer-text {
            font-style: italic;
            color: #666;
        }

        @keyframes fadeIn {
            to {
                opacity: 1;
            }
        }

        /* Responsive */
        @media (max-width: 600px) {
            .header h1 {
                font-size: 2rem;
            }
            
            .tech-grid {
                grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            }
        }
    </style>
</head>
<body>
    <!-- Dot Matrix Background -->
    <div class="dot-matrix"></div>

    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>Hi, I'm Abhijeet 👋</h1>
            <h2>B.Tech (3rd Year) • Full-Stack Web Developer</h2>
        </div>

        <div class="divider"></div>

        <!-- What I Do -->
        <div class="section">
            <h3>🧠 What I Do</h3>
            <div class="cards">
                <div class="card">
                    Build <strong>scalable full-stack web applications</strong>
                </div>
                <div class="card">
                    Focus on <strong>clean UI + strong backend logic</strong>
                </div>
                <div class="card">
                    Prefer <strong>real projects over tutorials</strong>
                </div>
            </div>
        </div>

        <div class="divider"></div>

        <!-- Tech Stack -->
        <div class="section">
            <h3>🛠 Tech Stack</h3>
            <div class="tech-grid">
                <div class="tech-item">React</div>
                <div class="tech-item">Next.js</div>
                <div class="tech-item">Tailwind</div>
                <div class="tech-item">Node.js</div>
                <div class="tech-item">Express</div>
                <div class="tech-item">PostgreSQL</div>
                <div class="tech-item">MongoDB</div>
                <div class="tech-item">Git</div>
            </div>
        </div>

        <div class="divider"></div>

        <!-- Current Focus -->
        <div class="section">
            <h3>🚀 Current Focus</h3>
            <ul class="focus-list">
                <li class="focus-item">Full-stack project development</li>
                <li class="focus-item">Backend performance & system design</li>
                <li class="focus-item">Preparing for internships & SDE roles</li>
            </ul>
        </div>

        <div class="divider"></div>

        <!-- Footer -->
        <div class="footer">
            <p class="footer-text">Open to internships, collaborations, and impactful projects</p>
        </div>
    </div>
</body>
</html>
