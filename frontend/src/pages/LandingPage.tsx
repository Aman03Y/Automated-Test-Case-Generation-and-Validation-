import React, { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  motion,
  useMotionValue,
  useTransform,
  useSpring,
  AnimatePresence,
} from 'framer-motion';
import {
  ShieldCheck,
  Cpu,
  Sparkles,
  ArrowRight,
  Database,
  FileCheck2,
  AlertTriangle,
  GitMerge,
  Code2,
  ChevronRight,
  Menu,
  X,
  Target,
  Workflow,
  CheckCircle2,
} from 'lucide-react';

/* ==========================================================================
   1. 3D TILT FEATURE CARD (framer-motion)
   ========================================================================== */

interface FeatureCardProps {
  title: string;
  badge: string;
  description: string;
  icon: React.ReactNode;
  accent: 'indigo' | 'emerald';
}

function TiltCard({ title, badge, description, icon, accent }: FeatureCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const mouseXSpring = useSpring(x, { stiffness: 220, damping: 25 });
  const mouseYSpring = useSpring(y, { stiffness: 220, damping: 25 });

  const rotateX = useTransform(mouseYSpring, [-0.5, 0.5], ['12deg', '-12deg']);
  const rotateY = useTransform(mouseXSpring, [-0.5, 0.5], ['-12deg', '12deg']);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    x.set(mouseX / rect.width - 0.5);
    y.set(mouseY / rect.height - 0.5);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  const isEmerald = accent === 'emerald';

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        rotateX,
        rotateY,
        transformStyle: 'preserve-3d',
      }}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="group relative rounded-2xl bg-slate-900/70 p-8 border border-slate-800 transition-colors duration-300 hover:border-slate-700 hover:bg-slate-900/90 backdrop-blur-xl"
    >
      {/* Specular Radial Glow on Hover */}
      <div
        className="pointer-events-none absolute -inset-px rounded-2xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: isEmerald
            ? 'radial-gradient(400px circle at 50% 50%, rgba(16, 185, 129, 0.12), transparent 70%)'
            : 'radial-gradient(400px circle at 50% 50%, rgba(99, 102, 241, 0.12), transparent 70%)',
        }}
      />

      <div style={{ transform: 'translateZ(25px)' }} className="relative z-10 flex flex-col h-full">
        {/* Top Icon & Badge */}
        <div className="flex items-center justify-between mb-6">
          <div
            className={`p-3.5 rounded-xl border ${
              isEmerald
                ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400 group-hover:shadow-[0_0_20px_rgba(16,185,129,0.3)]'
                : 'bg-indigo-950/40 border-indigo-500/30 text-indigo-400 group-hover:shadow-[0_0_20px_rgba(99,102,241,0.3)]'
            } transition-all duration-300`}
          >
            {icon}
          </div>
          <span
            className={`text-xs font-mono font-medium px-2.5 py-1 rounded-full border ${
              isEmerald
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
            }`}
          >
            {badge}
          </span>
        </div>

        {/* Content */}
        <h3 className="text-xl font-bold text-white mb-3 group-hover:text-indigo-200 transition-colors">
          {title}
        </h3>
        <p className="text-slate-400 text-sm leading-relaxed flex-grow">
          {description}
        </p>

        {/* Card Footer Micro-Action */}
        <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500 group-hover:text-slate-300 transition-colors">
          <span>Engine Automated</span>
          <ChevronRight className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
        </div>
      </div>
    </motion.div>
  );
}

/* ==========================================================================
   2. MAIN LANDING PAGE COMPONENT
   ========================================================================== */

export const LandingPage: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Smooth scroll handler with offset for permanently fixed navbar
  const scrollToSection = (
    e: React.MouseEvent<HTMLAnchorElement>,
    sectionId: string
  ) => {
    e.preventDefault();
    setMobileMenuOpen(false);

    const target = document.getElementById(sectionId);
    if (target) {
      const headerOffset = 80;
      const elementPosition = target.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth',
      });
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white font-sans antialiased">
      
      {/* ====================================================================
          1. PERMANENTLY FIXED GLASSMORPHISM NAVBAR (Always Visible)
          ==================================================================== */}
      <header className="fixed top-0 left-0 right-0 w-full z-50 backdrop-blur-md bg-slate-950/85 border-b border-slate-800/80 shadow-[0_4px_30px_rgba(0,0,0,0.5)]">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          
          {/* Logo */}
          <Link
            to="/"
            onClick={(e) => scrollToSection(e as any, 'hero')}
            className="flex items-center gap-3 group"
          >
            <div className="relative flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-500 to-emerald-500 p-[1px] shadow-[0_0_15px_rgba(99,102,241,0.35)] group-hover:shadow-[0_0_25px_rgba(99,102,241,0.55)] transition-shadow">
              <div className="w-full h-full bg-slate-950 rounded-[11px] flex items-center justify-center">
                <ShieldCheck className="w-6 h-6 text-indigo-400 group-hover:text-emerald-400 transition-colors" />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-indigo-200">
                AI Validator
              </span>
              <span className="text-[10px] font-mono uppercase tracking-widest text-emerald-400">
                Automated QA Engine
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
            <a
              href="#hero"
              onClick={(e) => scrollToSection(e, 'hero')}
              className="hover:text-white transition-colors cursor-pointer"
            >
              Home
            </a>
            <a
              href="#features"
              onClick={(e) => scrollToSection(e, 'features')}
              className="hover:text-white transition-colors cursor-pointer"
            >
              Features
            </a>
            <a
              href="#about"
              onClick={(e) => scrollToSection(e, 'about')}
              className="hover:text-white transition-colors cursor-pointer"
            >
              About Us
            </a>
            <a
              href="#education"
              onClick={(e) => scrollToSection(e, 'education')}
              className="hover:text-white transition-colors cursor-pointer"
            >
              What is a Test Case?
            </a>
          </nav>

          {/* Nav CTA */}
          <div className="hidden md:flex items-center gap-4">
            <Link
              to="/validate"
              className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-slate-900 hover:bg-slate-800 border border-slate-700/80 hover:border-indigo-500/60 shadow-[0_0_15px_rgba(99,102,241,0.2)] hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all flex items-center gap-2"
            >
              <Cpu className="w-4 h-4 text-emerald-400" />
              <span>Launch App</span>
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 border border-slate-800"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Dropdown */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-b border-slate-800 bg-slate-950/95 px-6 py-6 flex flex-col gap-4 text-sm font-medium"
            >
              <a
                href="#hero"
                onClick={(e) => scrollToSection(e, 'hero')}
                className="text-slate-300 hover:text-white py-2"
              >
                Home
              </a>
              <a
                href="#features"
                onClick={(e) => scrollToSection(e, 'features')}
                className="text-slate-300 hover:text-white py-2"
              >
                Features
              </a>
              <a
                href="#about"
                onClick={(e) => scrollToSection(e, 'about')}
                className="text-slate-300 hover:text-white py-2"
              >
                About Us
              </a>
              <a
                href="#education"
                onClick={(e) => scrollToSection(e, 'education')}
                className="text-slate-300 hover:text-white py-2"
              >
                What is a Test Case?
              </a>
              <Link
                to="/validate"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full text-center py-3 rounded-xl font-semibold text-white bg-indigo-600 hover:bg-indigo-500 mt-2"
              >
                Launch Dashboard
              </Link>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* ====================================================================
          2. CLEAN HERO SECTION (Ultra-Clean, High-Contrast, No Messy 3D)
          ==================================================================== */}
      <section
        id="hero"
        className="relative min-h-screen w-full flex items-center justify-center overflow-hidden px-6 pt-32 pb-24 scroll-mt-20"
      >
        {/* Clean Modern Tech Grid Overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_40%,#000_70%,transparent_100%)] opacity-30 pointer-events-none" />

        {/* Ambient Center Glow Blobs (Smooth, Pure, Modern) */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[450px] bg-gradient-to-tr from-indigo-600/20 via-indigo-500/15 to-emerald-500/15 rounded-full blur-[130px] pointer-events-none" />
        <div className="absolute top-1/4 left-1/3 w-[350px] h-[350px] bg-indigo-600/15 rounded-full blur-[100px] pointer-events-none" />

        {/* Center Illuminated Radial Halo Ring */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[580px] h-[340px] rounded-[100%] border border-indigo-500/20 pointer-events-none shadow-[0_0_50px_rgba(99,102,241,0.12)]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[720px] h-[440px] rounded-[100%] border border-emerald-500/10 pointer-events-none" />

        {/* Foreground Content - Centered & Razor Sharp */}
        <div className="relative z-10 w-full max-w-4xl mx-auto flex flex-col items-center justify-center text-center">
          
          {/* Eyebrow Pill */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-slate-900/90 border border-indigo-500/30 backdrop-blur-xl mb-8 shadow-[0_0_20px_rgba(99,102,241,0.2)]"
          >
            <Sparkles className="w-4 h-4 text-indigo-400 animate-pulse" />
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Next-Gen Autonomous Quality Engineering
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
          </motion.div>

          {/* Clean, Bold Headline */}
          <motion.h1
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tight leading-[1.08] text-white"
          >
            Automating QA <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-indigo-200 to-emerald-400 drop-shadow-[0_0_35px_rgba(99,102,241,0.4)]">
              with AI
            </span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="mt-6 max-w-2xl mx-auto text-base sm:text-lg md:text-xl text-slate-300 font-normal leading-relaxed"
          >
            Transform ambiguous, redundant, and orphaned test suites into hardened,
            verifiable execution plans. Detect hallucinations, merge semantic clones,
            and guarantee 100% specification traceability.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-5"
          >
            <Link
              to="/validate"
              className="group relative inline-flex items-center justify-center px-9 py-4 rounded-xl font-bold text-white text-base overflow-hidden bg-gradient-to-r from-indigo-600 via-indigo-500 to-indigo-600 shadow-[0_0_20px_rgba(99,102,241,0.6)] hover:shadow-[0_0_35px_rgba(99,102,241,0.9)] transition-all duration-300 transform hover:-translate-y-0.5 active:translate-y-0"
            >
              <span className="absolute inset-0 bg-white/20 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
              <span className="relative flex items-center gap-3">
                Launch Dashboard
                <ArrowRight className="w-5 h-5 text-indigo-200 group-hover:translate-x-1.5 transition-transform" />
              </span>
            </Link>

            <a
              href="#features"
              onClick={(e) => scrollToSection(e, 'features')}
              className="inline-flex items-center justify-center px-8 py-4 rounded-xl font-semibold text-slate-300 text-base bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800 hover:border-slate-700 hover:text-white transition-all backdrop-blur-md cursor-pointer"
            >
              Explore Architecture
            </a>
          </motion.div>

          {/* Stats Bar */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.45 }}
            className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6 pt-10 border-t border-slate-800/80 w-full max-w-3xl mx-auto text-center"
          >
            <div>
              <div className="text-2xl font-black text-white font-mono">99.4%</div>
              <div className="text-xs text-slate-400 mt-1">Schema Compliance</div>
            </div>
            <div>
              <div className="text-2xl font-black text-emerald-400 font-mono">0.88 Cosine</div>
              <div className="text-xs text-slate-400 mt-1">Deduplication Threshold</div>
            </div>
            <div>
              <div className="text-2xl font-black text-indigo-400 font-mono">&lt; 150ms</div>
              <div className="text-xs text-slate-400 mt-1">Validation Latency</div>
            </div>
            <div>
              <div className="text-2xl font-black text-white font-mono">0 Orphans</div>
              <div className="text-xs text-slate-400 mt-1">Traceability Guarantee</div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ====================================================================
          3. FEATURES GRID: "ERRORS WE AUTO-FIX"
          ==================================================================== */}
      <section id="features" className="relative py-28 px-6 max-w-7xl mx-auto scroll-mt-24">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full mb-4"
          >
            Autonomous Healing Engine
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-3xl sm:text-4xl md:text-5xl font-black tracking-tight text-white"
          >
            Errors We Auto-Fix
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="mt-4 text-slate-400 text-base sm:text-lg"
          >
            Legacy test suites deteriorate through human oversight and fragmented requirements.
            Our engine intercepts, sanitizes, and repairs flaws before they touch production.
          </motion.p>
        </div>

        {/* 4 Interactive 3D Tilt Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 perspective-[1000px]">
          
          <TiltCard
            title="Traceability & Hallucinations"
            badge="Orphan Sentinel"
            accent="indigo"
            icon={<AlertTriangle className="w-6 h-6" />}
            description="Isolates orphaned test cases referencing phantom specifications or non-existent endpoints. Validates bi-directional links between user stories and executable verification steps."
          />

          <TiltCard
            title="Semantic Deduplication"
            badge="SentenceTransformers NLP"
            accent="emerald"
            icon={<GitMerge className="w-6 h-6" />}
            description="Leverages high-dimensional embeddings to detect identical verification logic disguised under distinct wording. Clusters overlapping scenarios and merges redundant runs."
          />

          <TiltCard
            title="Structural Sanitization"
            badge="Schema Normalizer"
            accent="emerald"
            icon={<Code2 className="w-6 h-6" />}
            description="Auto-generates missing test IDs, converts free-form step strings into deterministic arrays, and cleans malformed JSON/YAML payloads into production-grade structures."
          />

          <TiltCard
            title="Data Consistency"
            badge="Matrix Alignment"
            accent="indigo"
            icon={<Database className="w-6 h-6" />}
            description="Resolves skewed priority hierarchies (P0/P1/P2) against real-world blast radius formulas. Normalizes flaky preconditions and eliminates divergent environment configs."
          />

        </div>
      </section>

      {/* ====================================================================
          4. ABOUT US
          ==================================================================== */}
      <section id="about" className="relative py-28 px-6 bg-slate-950/80 border-y border-slate-800/80 scroll-mt-24">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
          
          {/* Left Column: Holographic Abstract CSS Sphere */}
          <div className="lg:col-span-5 flex items-center justify-center">
            <div className="relative w-72 h-72 sm:w-88 sm:h-88 flex items-center justify-center">
              
              {/* Outer Orbit Ring */}
              <div className="absolute inset-0 rounded-full border border-indigo-500/20 animate-[spin_20s_linear_infinite]" />
              
              {/* Middle Tilted Orbit Ring */}
              <div
                className="absolute inset-4 rounded-full border border-dashed border-emerald-500/30 animate-[spin_14s_linear_infinite_reverse]"
                style={{ transform: 'rotateX(60deg) rotateY(20deg)' }}
              />

              {/* Glowing Core Sphere */}
              <div className="relative w-44 h-44 rounded-full bg-gradient-to-tr from-indigo-700 via-indigo-500 to-emerald-400 p-[2px] shadow-[0_0_60px_rgba(99,102,241,0.5)]">
                <div className="w-full h-full rounded-full bg-slate-950/90 backdrop-blur-md flex flex-col items-center justify-center p-6 text-center">
                  <Cpu className="w-10 h-10 text-emerald-400 mb-2 animate-bounce" />
                  <span className="text-xs font-mono font-bold text-white tracking-wider">
                    VALIDATOR CORE
                  </span>
                  <span className="text-[10px] text-indigo-400 font-mono mt-0.5">
                    v2.4 ACTIVE
                  </span>
                </div>
              </div>

              {/* Pulsing Glow Blobs */}
              <div className="absolute w-56 h-56 bg-indigo-600/20 rounded-full blur-2xl pointer-events-none" />
              <div className="absolute w-36 h-36 bg-emerald-500/15 rounded-full blur-xl pointer-events-none" />
            </div>
          </div>

          {/* Right Column: Mission Statement */}
          <div className="lg:col-span-7">
            <div className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full mb-4">
              Our Mission & Philosophy
            </div>
            
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight leading-tight">
              Eliminating Human Drag in Modern QA Pipelines
            </h2>
            
            <p className="mt-6 text-slate-400 text-base sm:text-lg leading-relaxed">
              Software releases are only as reliable as their test suites. Yet as teams scale,
              manual test design leads to subtle oversights: outdated steps, duplicate scenarios,
              and false senses of security.
            </p>

            <p className="mt-4 text-slate-400 text-base sm:text-lg leading-relaxed">
              <strong>AI Validator</strong> replaces subjective reviews with formal, automated
              scrutiny. By combining modern embedding models with deterministic syntax guards,
              we ensure every single test case is traceable, deduplicated, and ready for continuous
              integration execution.
            </p>

            {/* Feature Bullets */}
            <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <span className="text-sm text-slate-300 font-medium">
                  Zero hallucinated requirements in production pipelines
                </span>
              </div>
              <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <CheckCircle2 className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
                <span className="text-sm text-slate-300 font-medium">
                  Up to 40% reduction in bloated manual test suites
                </span>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* ====================================================================
          5. EDUCATIONAL SECTION: "WHAT IS A TEST CASE?"
          ==================================================================== */}
      <section id="education" className="relative py-28 px-6 max-w-7xl mx-auto scroll-mt-24">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <div className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full mb-4">
            Specification Anatomy
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black tracking-tight text-white">
            What is a Test Case?
          </h2>
          <p className="mt-4 text-slate-400 text-base sm:text-lg">
            A test case is not just a list of steps—it is a verifiable contract between business
            intent and software execution. Here is the anatomy of a hardened test case:
          </p>
        </div>

        {/* Step-by-Step Interactive Timeline Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          
          {/* Step 1: Requirement Mapping */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="relative rounded-2xl bg-slate-900/70 border border-slate-800 p-8 backdrop-blur-xl flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-6">
                <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950/80 border border-indigo-500/30 px-3 py-1 rounded-lg">
                  STEP 01
                </span>
                <Target className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Requirement Mapping</h3>
              <div className="text-xs font-mono text-emerald-400 mb-4 uppercase tracking-wider">
                The &ldquo;Why&rdquo;
              </div>
              <p className="text-slate-400 text-sm leading-relaxed">
                Anchors the test directly to a business story, ticket, or SRS spec. Ensures every
                action aligns with actual stakeholder value and prevents zombie requirements.
              </p>
            </div>
            <div className="mt-6 p-3 rounded-lg bg-slate-950 border border-slate-800/80 font-mono text-xs text-slate-400">
              <span className="text-indigo-400">REQ-ID:</span> AUTH-204_MFA_TOKEN
            </div>
          </motion.div>

          {/* Step 2: Action Steps */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.15 }}
            className="relative rounded-2xl bg-slate-900/70 border border-slate-800 p-8 backdrop-blur-xl flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-6">
                <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/80 border border-emerald-500/30 px-3 py-1 rounded-lg">
                  STEP 02
                </span>
                <Workflow className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Action Steps</h3>
              <div className="text-xs font-mono text-emerald-400 mb-4 uppercase tracking-wider">
                The &ldquo;How&rdquo;
              </div>
              <p className="text-slate-400 text-sm leading-relaxed">
                Deterministic, reproducible instructions detailing inputs, environment state,
                and precise navigation steps with no ambiguous instructions.
              </p>
            </div>
            <div className="mt-6 p-3 rounded-lg bg-slate-950 border border-slate-800/80 font-mono text-xs text-slate-400">
              <span className="text-emerald-400">EXEC:</span> POST /api/v2/auth/totp
            </div>
          </motion.div>

          {/* Step 3: Expected Result */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="relative rounded-2xl bg-slate-900/70 border border-slate-800 p-8 backdrop-blur-xl flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-6">
                <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950/80 border border-indigo-500/30 px-3 py-1 rounded-lg">
                  STEP 03
                </span>
                <FileCheck2 className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Expected Result</h3>
              <div className="text-xs font-mono text-emerald-400 mb-4 uppercase tracking-wider">
                The &ldquo;Proof&rdquo;
              </div>
              <p className="text-slate-400 text-sm leading-relaxed">
                Strict assertions that evaluate pass/fail criteria. Eliminates false confidence
                by establishing exact response codes, payload schemas, and UI states.
              </p>
            </div>
            <div className="mt-6 p-3 rounded-lg bg-slate-950 border border-slate-800/80 font-mono text-xs text-slate-400">
              <span className="text-indigo-400">ASSERT:</span> Status 200 & JWT returned
            </div>
          </motion.div>

        </div>

        {/* Live Sanitized Preview Box */}
        <div className="mt-16 rounded-2xl bg-gradient-to-r from-indigo-950/30 via-slate-900/60 to-emerald-950/30 p-8 border border-slate-800 text-center max-w-4xl mx-auto">
          <h4 className="text-xl font-bold text-white mb-2">Ready to audit your test cases?</h4>
          <p className="text-slate-400 text-sm max-w-xl mx-auto mb-6">
            Upload your test spreadsheets, JSON exports, or Jira specifications directly
            to our validation engine.
          </p>
          <Link
            to="/validate"
            className="inline-flex items-center gap-2 px-7 py-3 rounded-xl font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.5)] transition-all"
          >
            Upload Test Cases
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* ====================================================================
          6. FOOTER
          ==================================================================== */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-400 font-mono">Engine Status: All Validators Operational</span>
          </div>
          <div>
            &copy; {new Date().getFullYear()} AI Validator. Built for high-reliability software teams.
          </div>
          <div className="flex items-center gap-6">
            <a
              href="#hero"
              onClick={(e) => scrollToSection(e, 'hero')}
              className="hover:text-slate-300 transition-colors cursor-pointer"
            >
              Privacy
            </a>
            <a
              href="#hero"
              onClick={(e) => scrollToSection(e, 'hero')}
              className="hover:text-slate-300 transition-colors cursor-pointer"
            >
              Security
            </a>
            <a
              href="#hero"
              onClick={(e) => scrollToSection(e, 'hero')}
              className="hover:text-slate-300 transition-colors cursor-pointer"
            >
              Docs
            </a>
          </div>
        </div>
      </footer>

    </div>
  );
};

export default LandingPage;
