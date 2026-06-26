import React from "react";
import Link from "next/link";
import { Sparkles, Activity, ShieldCheck, MapPin, BarChart3, MessageSquarePlus } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 font-sans flex flex-col justify-between selection:bg-cyan-500 selection:text-black">
      
      {/* Background Gradients */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-[128px] pointer-events-none"></div>
      <div className="absolute top-1/3 right-1/4 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[160px] pointer-events-none"></div>

      {/* Hero Section */}
      <main className="max-w-6xl mx-auto px-6 sm:px-8 pt-20 pb-16 flex-1 flex flex-col items-center text-center relative z-10">
        
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-cyan-500/20 bg-cyan-500/5 text-cyan-400 text-xs font-semibold mb-8 animate-pulse">
          <Sparkles className="w-4 h-4" /> AI Agent Builder Series 2026
        </div>

        <h1 className="text-5xl sm:text-7xl font-extrabold tracking-tight leading-none mb-6">
          Intelligence for Rural <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-500 bg-clip-text text-transparent">Health Workforces</span>
        </h1>

        <p className="max-w-2xl text-base sm:text-lg text-gray-400 leading-relaxed mb-10">
          SwasthAI orchestrates five specialized AI agents to automate biometric verify-in, 
          predict staffing shortages, optimize routes, and support rural health workers in local languages.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mb-16 w-full justify-center items-center">
          <Link
            href="/dashboard"
            className="w-full sm:w-auto h-12 px-8 flex items-center justify-center font-bold rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30 transition-all hover:scale-[1.02]"
          >
            Launch Supervisor Command Center
          </Link>
          <a
            href="https://github.com/chethangowda-web"
            target="_blank"
            className="w-full sm:w-auto h-12 px-8 flex items-center justify-center font-bold rounded-xl border border-gray-800 bg-[#131C2E]/60 text-gray-300 hover:text-white hover:bg-gray-800/80 transition-all"
          >
            Explore Core API Schema
          </a>
        </div>

        {/* Core Agent Feature Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left">
          
          <div className="p-6 rounded-2xl border border-gray-800/80 bg-[#131C2E]/40 backdrop-blur-sm">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400 mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-lg mb-2">Biometric Attendance Agent</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Leverages face verification via InsightFace and OpenCV to check worker identities and filter spoofing logs.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-gray-800/80 bg-[#131C2E]/40 backdrop-blur-sm">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 mb-4">
              <MapPin className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-lg mb-2">Smart Reassignment Route</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Integrates Google Distance Matrix and Directions to optimize schedules and balance local workloads.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-gray-800/80 bg-[#131C2E]/40 backdrop-blur-sm">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400 mb-4">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-lg mb-2">Supervisor Intelligence</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Generates regional statistics and risk profiles using LangGraph state-charts and Gemini predictions.
            </p>
          </div>

        </div>

      </main>

      {/* Footer Branding */}
      <footer className="border-t border-gray-900 bg-[#070B13] py-8 text-center text-xs text-gray-500 font-semibold">
        <p>© 2026 SwasthAI. Powered by Google Build with AI × AI House.</p>
      </footer>

    </div>
  );
}
