// ===== Blog Data =====
const blogPosts = [
    {
        id: 1,
        title: "The Rise of Autonomous AI Agents",
        excerpt: "Exploring how autonomous agents are reshaping the landscape of software development and digital interaction.",
        category: "ai",
        date: "September 5, 2026",
        readTime: "5 min read",
        tags: ["AI", "Agents", "Future"],
        content: `
            <p>Autonomous AI agents represent a paradigm shift in how we interact with software. Unlike traditional programs that follow rigid instructions, these agents can perceive their environment, make decisions, and take actions to achieve goals.</p>
            
            <h2>What Makes an Agent "Autonomous"?</h2>
            <p>An autonomous AI agent differs from a simple chatbot in several key ways:</p>
            <ul>
                <li><strong>Goal-directed behavior:</strong> Agents pursue objectives across multiple steps.</li>
                <li><strong>Environmental awareness:</strong> They perceive and respond to changing conditions.</li>
                <li><strong>Tool use:</strong> They leverage external tools and APIs to accomplish tasks.</li>
                <li><strong>Learning:</strong> They improve from experience over time.</li>
            </ul>
            
            <h2>The Architecture</h2>
            <p>Modern agent architectures typically consist of a reasoning core (often an LLM), a memory system, tool integrations, and a planning module. Together, these components enable agents to tackle complex, multi-step tasks.</p>
            
            <pre><code>agent = Agent(
    model="gpt-4",
    tools=[search, browser, code],
    memory=VectorMemory(),
    planner=ChainOfThought()
)</code></pre>
            
            <h2>Looking Ahead</h2>
            <p>As models become more capable and tool ecosystems mature, we'll see agents that can handle increasingly sophisticated workflows — from research assistance to full software development lifecycles.</p>
        `
    },
    {
        id: 2,
        title: "Building Modular AI Systems",
        excerpt: "Why modularity matters when constructing AI-powered applications that need to scale and evolve.",
        category: "tech",
        date: "August 28, 2026",
        readTime: "4 min read",
        tags: ["Architecture", "Modularity", "Design"],
        content: `
            <p>Building AI systems that can evolve requires a modular approach. Monolithic designs break down when you need to swap models, add capabilities, or scale components independently.</p>
            
            <h2>The Plugin Pattern</h2>
            <p>The most successful AI platforms use a plugin architecture. Each capability — whether it's web search, image generation, or database access — lives in its own module with a standardized interface.</p>
            
            <h2>Benefits of Modularity</h2>
            <ul>
                <li><strong>Independent deployment:</strong> Update one component without redeploying everything.</li>
                <li><strong>Community extensibility:</strong> Third-party developers can add new capabilities.</li>
                <li><strong>Testing:</strong> Isolated components are easier to test and debug.</li>
                <li><strong>Resilience:</strong> One failing plugin doesn't bring down the whole system.</li>
            </ul>
            
            <h2>Implementation Tips</h2>
            <p>Start with clear interfaces. Define what inputs and outputs each module should have. Use event-driven communication where possible to keep components loosely coupled.</p>
        `
    },
    {
        id: 3,
        title: "Safety in Autonomous Systems",
        excerpt: "Examining the critical importance of safety guardrails in AI systems that operate independently.",
        category: "autonomy",
        date: "August 20, 2026",
        readTime: "6 min read",
        tags: ["Safety", "Guardrails", "Ethics"],
        content: `
            <p>As AI systems gain more autonomy, safety becomes not just important — it's existential. A system that can act in the world needs robust guardrails.</p>
            
            <h2>The Guardrail Framework</h2>
            <p>Effective guardrails operate at multiple levels:</p>
            <ul>
                <li><strong>Input validation:</strong> Screening requests for harmful intent.</li>
                <li><strong>Output filtering:</strong> Preventing dangerous or inappropriate responses.</li>
                <li><strong>Action constraints:</strong> Limiting what the system can do.</li>
                <li><strong>Human oversight:</strong> Requiring approval for sensitive operations.</li>
            </ul>
            
            <h2>The Balance</h2>
            <p>Too many constraints and the system becomes useless. Too few and it becomes dangerous. Finding the right balance is an ongoing process that requires continuous monitoring and adjustment.</p>
            
            <h2>Practical Approaches</h2>
            <p>Start with a deny-list of clearly dangerous actions. Add rate limiting to prevent abuse. Implement logging and audit trails so you can review what the system does.</p>
        `
    },
    {
        id: 4,
        title: "The Future of Human-AI Collaboration",
        excerpt: "How humans and AI systems will work together in the next decade of technological evolution.",
        category: "ai",
        date: "August 12, 2026",
        readTime: "5 min read",
        tags: ["Collaboration", "Future", "Human-AI"],
        content: `
            <p>The narrative of "AI vs. humans" misses the point. The most powerful paradigm is collaboration — each side doing what it does best.</p>
            
            <h2>Complementary Strengths</h2>
            <p>Humans excel at creativity, empathy, and moral judgment. AI excels at speed, scale, and pattern recognition. A well-designed collaborative system leverages both.</p>
            
            <h2>Design Patterns for Collaboration</h2>
            <ul>
                <li><strong>Human-in-the-loop:</strong> AI proposes, human disposes.</li>
                <li><strong>AI-assist:</strong> Human leads, AI supports with information and suggestions.</li>
                <li><strong>Delegated autonomy:</strong> Routine tasks handled independently, exceptions escalated.</li>
            </ul>
            
            <h2>The Role of Trust</h2>
            <p>Effective collaboration requires trust, and trust requires transparency. AI systems must be explainable — users need to understand why a system made a particular recommendation.</p>
        `
    },
    {
        id: 5,
        title: "Memory and Learning in AI Agents",
        excerpt: "How persistent memory transforms one-shot AI interactions into ongoing relationships.",
        category: "tech",
        date: "August 5, 2026",
        readTime: "4 min read",
        tags: ["Memory", "Learning", "Agents"],
        content: `
            <p>Without memory, every interaction with an AI is a blank slate. Adding persistent memory transforms these systems from tools into companions that grow with you.</p>
            
            <h2>Types of Memory</h2>
            <ul>
                <li><strong>Short-term:</strong> Context within a single conversation.</li>
                <li><strong>Long-term:</strong> Facts and preferences stored across sessions.</li>
                <li><strong>Procedural:</strong> Learned skills and workflows.</li>
                <li><strong>Episodic:</strong> Memories of past interactions and events.</li>
            </ul>
            
            <h2>Implementation Approaches</h2>
            <p>Vector databases have become the standard for semantic memory retrieval. Embeddings allow the system to find relevant memories based on meaning, not just keyword matching.</p>
            
            <h2>Privacy Considerations</h2>
            <p>Memory is powerful but sensitive. Users must have control over what is stored, the ability to delete memories, and transparency about how memory is used.</p>
        `
    },
    {
        id: 6,
        title: "Why Autonomy Needs Constraints",
        excerpt: "The counterintuitive truth that freedom in AI systems requires well-defined boundaries.",
        category: "autonomy",
        date: "July 28, 2026",
        readTime: "3 min read",
        tags: ["Autonomy", "Constraints", "Design"],
        content: `
            <p>It seems paradoxical: to build a truly autonomous system, you need to constrain it carefully. But constraints are what make autonomy safe and useful.</p>
            
            <h2>The Fenced Field</h2>
            <p>Think of autonomy like a playground. The fence doesn't prevent play — it enables it by removing the risk of running into traffic. Similarly, AI constraints enable confident operation within safe boundaries.</p>
            
            <h2>Types of Constraints</h2>
            <ul>
                <li><strong>Scope constraints:</strong> What domains the system operates in.</li>
                <li><strong>Action constraints:</strong> What operations are permitted.</li>
                <li><strong>Resource constraints:</strong> Limits on computation and API usage.</li>
                <li><strong>Temporal constraints:</strong> When and how long the system can act.</li>
            </ul>
        `
    }
];

// ===== DOM Utilities =====
function $(selector) { return document.querySelector(selector); }
function $$(selector) { return document.querySelectorAll(selector); }

// ===== Render Post Card =====
function createPostCard(post) {
    const card = document.createElement('article');
    card.className = 'post-card';
    card.innerHTML = `
        <span class="post-card-category">${post.category.toUpperCase()}</span>
        <h3 class="post-card-title">${post.title}</h3>
        <p class="post-card-excerpt">${post.excerpt}</p>
        <div class="post-card-meta">
            <span>${post.date}</span>
            <span>${post.readTime}</span>
        </div>
        <div class="post-card-tags">
            ${post.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
        </div>
    `;
    card.addEventListener('click', () => {
        window.location.href = `post.html?id=${post.id}`;
    });
    return card;
}

// ===== Load Posts on Index Page =====
function loadLatestPosts() {
    const grid = $('#latest-posts-grid');
    if (!grid) return;
    const latest = blogPosts.slice(0, 3);
    latest.forEach(post => grid.appendChild(createPostCard(post)));
}

// ===== Load All Posts =====
function loadAllPosts(filter = 'all') {
    const grid = $('#all-posts-grid');
    if (!grid) return;
    grid.innerHTML = '';
    const filtered = filter === 'all' 
        ? blogPosts 
        : blogPosts.filter(p => p.category === filter);
    filtered.forEach(post => grid.appendChild(createPostCard(post)));
}

// ===== Load Single Post =====
function loadSinglePost() {
    const params = new URLSearchParams(window.location.search);
    const id = parseInt(params.get('id'));
    const post = blogPosts.find(p => p.id === id);
    
    if (!post) {
        // Default to first post if invalid ID
        window.location.href = 'post.html?id=1';
        return;
    }
    
    const categoryEl = $('#post-category');
    const dateEl = $('#post-date');
    const readEl = $('#post-read');
    const titleEl = $('#post-title');
    const excerptEl = $('#post-excerpt');
    const contentEl = $('#post-content');
    const tagsEl = $('#post-tags');
    
    if (categoryEl) categoryEl.textContent = post.category.toUpperCase();
    if (dateEl) dateEl.textContent = post.date;
    if (readEl) readEl.textContent = post.readTime;
    if (titleEl) titleEl.textContent = post.title;
    if (excerptEl) excerptEl.textContent = post.excerpt;
    if (contentEl) contentEl.innerHTML = post.content;
    if (tagsEl) {
        tagsEl.innerHTML = post.tags.map(tag => `<span class="post-tag">${tag}</span>`).join('');
    }
    
    // Load related posts (same category, excluding current)
    const related = blogPosts.filter(p => p.category === post.category && p.id !== post.id).slice(0, 3);
    const relatedGrid = $('#related-posts-grid');
    if (relatedGrid) {
        relatedGrid.innerHTML = '';
        if (related.length > 0) {
            related.forEach(p => relatedGrid.appendChild(createPostCard(p)));
        } else {
            // Fallback: show latest posts
            blogPosts.filter(p => p.id !== post.id).slice(0, 3)
                .forEach(p => relatedGrid.appendChild(createPostCard(p)));
        }
    }
    
    // Update page title
    document.title = `${post.title} — Bionic Daughter`;
}

// ===== Filter Bar =====
function initFilters() {
    const filterBtns = $$('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadAllPosts(btn.dataset.filter);
        });
    });
}

// ===== Mobile Menu =====
function initMobileMenu() {
    const menuBtn = $('.mobile-menu-btn');
    const navLinks = $('.nav-links');
    if (menuBtn && navLinks) {
        menuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('open');
        });
    }
}

// ===== Smooth Scroll for Anchor Links =====
function initSmoothScroll() {
    $$('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            e.preventDefault();
            const target = $(anchor.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    loadLatestPosts();
    loadAllPosts();
    loadSinglePost();
    initFilters();
    initMobileMenu();
    initSmoothScroll();
});
