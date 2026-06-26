"use client";

import React, { useState } from "react";
import { 
  Users, 
  MapPin, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp, 
  Sparkles, 
  Bell, 
  Filter, 
  RefreshCw, 
  Moon, 
  Sun,
  Search,
  ChevronRight,
  UserCheck
} from "lucide-react";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  BarChart, 
  Bar,
  Cell
} from "recharts";

// Mock data representing database analytics outputs
const ATTENDANCE_TRENDS = [
  { day: "Mon", present: 41, expected: 48 },
  { day: "Tue", present: 44, expected: 48 },
  { day: "Wed", present: 42, expected: 48 },
  { day: "Thu", present: 39, expected: 48 },
  { day: "Fri", present: 45, expected: 48 },
  { day: "Sat", present: 46, expected: 48 },
  { day: "Sun", present: 43, expected: 48 },
];

const WORKER_EFFICIENCY = [
  { name: "Aarav S.", rate: 98 },
  { name: "Priya M.", rate: 94 },
  { name: "Kiran K.", rate: 72 }, // Flagged / Low efficiency
  { name: "Sunitha D.", rate: 91 },
  { name: "Chethan G.", rate: 96 },
];

const MOCK_INSIGHTS = [
  {
    id: 1,
    text: "Worker Kiran K. missed check-ins at Village Megalapura 3 times this week.",
    type: "critical",
    time: "2 hours ago"
  },
  {
    id: 2,
    text: "AI Scheduling suggested reassignment: Aarav S. covers absenteeism at Solur.",
    type: "info",
    time: "4 hours ago"
  },
  {
    id: 3,
    text: "GPS Anomaly detected: Worker Priya M. checked in 350m outside geofence boundary.",
    type: "warning",
    time: "1 day ago"
  }
];

const ACTIVE_NOTIFICATIONS = [
  { title: "Emergency Reassignment", desc: "Aarav S. accepted cover for Solur village", time: "10m ago" },
  { title: "Liveness Warning", desc: "Kiran K. face authentication match score low (0.42)", time: "1h ago" },
  { title: "Schedule Updated", desc: "AI optimization set 14 daily tasks for tomorrow", time: "3h ago" }
];

export default function SupervisorDashboard() {
  const [darkMode, setDarkMode] = useState(true);
  const [timeframe, setTimeframe] = useState("weekly");
  const [region, setRegion] = useState("Bengaluru Rural");

  return (
    <div className={`min-h-screen transition-colors duration-300 ${darkMode ? "bg-[#0B0F19] text-gray-100" : "bg-[#F3F4F6] text-gray-900"}`}>
      
      {/* 1. Header Navigation Bar */}
      <header className={`sticky top-0 z-50 backdrop-blur-md border-b transition-colors ${darkMode ? "bg-[#0F172A]/80 border-gray-800/80" : "bg-white/80 border-gray-200"}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20">
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">SwasthAI</span>
              <span className={`block text-xs font-semibold ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Enterprise Dashboard</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Search Input */}
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
              <input 
                type="text" 
                placeholder="Search health workers..." 
                className={`w-64 pl-9 pr-4 py-2 text-sm rounded-lg border outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all ${
                  darkMode 
                    ? "bg-[#1E293B] border-gray-700/60 text-gray-100 placeholder-gray-500 focus:border-cyan-500" 
                    : "bg-gray-100 border-gray-300 text-gray-900 placeholder-gray-400 focus:bg-white focus:border-cyan-500"
                }`}
              />
            </div>

            {/* Notification Bell */}
            <button className={`relative p-2 rounded-lg transition-all border ${
              darkMode ? "bg-[#1E293B] border-gray-700 hover:bg-gray-800" : "bg-gray-100 border-gray-200 hover:bg-gray-200"
            }`}>
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full"></span>
            </button>

            {/* Dark Mode Toggle */}
            <button 
              onClick={() => setDarkMode(!darkMode)}
              className={`p-2 rounded-lg transition-all border ${
                darkMode ? "bg-[#1E293B] border-gray-700 hover:bg-gray-800" : "bg-gray-100 border-gray-200 hover:bg-gray-200"
              }`}
            >
              {darkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-slate-700" />}
            </button>

            {/* User Profile Info */}
            <div className="flex items-center gap-2 border-l pl-4 border-gray-700/60">
              <div className="w-9 h-9 rounded-full bg-cyan-600 flex items-center justify-center text-white font-bold text-sm shadow">
                CG
              </div>
              <div className="hidden lg:block text-left">
                <span className="block text-xs font-semibold">Chethan Gowda</span>
                <span className={`block text-[10px] ${darkMode ? "text-gray-400" : "text-gray-500"}`}>District Lead</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* 2. Filter & Controls Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">System Performance Metrics</h1>
            <p className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Showing data for region: <strong className="text-cyan-400">{region}</strong></p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex bg-[#1E293B] border border-gray-700/60 rounded-lg p-0.5">
              {["daily", "weekly", "monthly"].map((t) => (
                <button 
                  key={t}
                  onClick={() => setTimeframe(t)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-md capitalize transition-all ${
                    timeframe === t 
                      ? "bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-md" 
                      : "text-gray-400 hover:text-gray-100"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
            <button className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg border transition-all ${
              darkMode ? "bg-[#1E293B] border-gray-700 hover:bg-gray-800" : "bg-gray-100 border-gray-200 hover:bg-gray-200"
            }`}>
              <Filter className="w-4 h-4" /> Filters
            </button>
            <button className={`p-2 rounded-lg border transition-all ${
              darkMode ? "bg-[#1E293B] border-gray-700 hover:bg-gray-800" : "bg-gray-100 border-gray-200 hover:bg-gray-200"
            }`}>
              <RefreshCw className="w-4 h-4 animate-spin-hover" />
            </button>
          </div>
        </div>

        {/* 3. Core Stats Grid Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          
          {/* Card: Today's Attendance */}
          <div className={`p-6 rounded-2xl border transition-all shadow-sm ${darkMode ? "bg-[#131C2E] border-gray-800/80 hover:border-cyan-500/30" : "bg-white border-gray-200 hover:shadow-md"}`}>
            <div className="flex items-center justify-between mb-4">
              <span className={`text-sm font-semibold ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Today's Attendance</span>
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                <UserCheck className="w-5 h-5" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold">42</span>
              <span className={`text-sm font-semibold ${darkMode ? "text-gray-400" : "text-gray-500"}`}>/ 48 present</span>
            </div>
            <div className="mt-4 w-full bg-gray-700/30 rounded-full h-2">
              <div className="bg-gradient-to-r from-emerald-400 to-teal-500 h-2 rounded-full" style={{ width: "87.5%" }}></div>
            </div>
            <span className="block text-xs font-semibold text-emerald-400 mt-2">↑ 4.2% from last week</span>
          </div>

          {/* Card: Absent Workers */}
          <div className={`p-6 rounded-2xl border transition-all shadow-sm ${darkMode ? "bg-[#131C2E] border-gray-800/80 hover:border-rose-500/30" : "bg-white border-gray-200 hover:shadow-md"}`}>
            <div className="flex items-center justify-between mb-4">
              <span className={`text-sm font-semibold ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Absent Workers</span>
              <div className="w-10 h-10 rounded-lg bg-rose-500/10 flex items-center justify-center text-rose-500">
                <AlertTriangle className="w-5 h-5" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-rose-500">6</span>
              <span className={`text-sm font-semibold ${darkMode ? "text-gray-400" : "text-gray-500"}`}>unresolved</span>
            </div>
            <div className="mt-4 flex items-center gap-1.5">
              <span className="px-2 py-0.5 text-[10px] font-bold bg-rose-500/10 text-rose-400 rounded-md">Critical</span>
              <span className={`text-xs ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Requires reassignment</span>
            </div>
          </div>

          {/* Card: Late Arrivals */}
          <div className={`p-6 rounded-2xl border transition-all shadow-sm ${darkMode ? "bg-[#131C2E] border-gray-800/80 hover:border-amber-500/30" : "bg-white border-gray-200 hover:shadow-md"}`}>
            <div className="flex items-center justify-between mb-4">
              <span className={`text-sm font-semibold ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Late Workers</span>
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-500">
                <Users className="w-5 h-5" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-amber-500">4</span>
              <span className={`text-sm font-semibold ${darkMode ? "text-gray-400" : "text-gray-500"}`}>today</span>
            </div>
            <div className="mt-4 flex items-center gap-1.5">
              <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-500/10 text-amber-400 rounded-md">Warning</span>
              <span className={`text-xs ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Check-in delayed &gt; 30m</span>
            </div>
          </div>

          {/* Card: Village Coverage */}
          <div className={`p-6 rounded-2xl border transition-all shadow-sm ${darkMode ? "bg-[#131C2E] border-gray-800/80 hover:border-cyan-500/30" : "bg-white border-gray-200 hover:shadow-md"}`}>
            <div className="flex items-center justify-between mb-4">
              <span className={`text-sm font-semibold ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Village Coverage</span>
              <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-500">
                <MapPin className="w-5 h-5" />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold">91.6%</span>
              <span className={`text-sm font-semibold ${darkMode ? "text-gray-400" : "text-gray-500"}`}>total region</span>
            </div>
            <div className="mt-4 w-full bg-gray-700/30 rounded-full h-2">
              <div className="bg-gradient-to-r from-cyan-400 to-blue-500 h-2 rounded-full" style={{ width: "91.6%" }}></div>
            </div>
            <span className="block text-xs font-semibold text-cyan-400 mt-2">11 out of 12 villages covered</span>
          </div>

        </div>

        {/* 4. Secondary Data Visualization Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          
          {/* Chart Widget: Trends */}
          <div className={`lg:col-span-2 p-6 rounded-2xl border ${darkMode ? "bg-[#131C2E] border-gray-800/80" : "bg-white border-gray-200"}`}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="font-bold text-lg">Attendance Trends</h3>
                <p className={`text-xs ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Comparing expected check-ins vs actual logs</p>
              </div>
              <div className="flex items-center gap-4 text-xs font-semibold">
                <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-cyan-500"></span> Present</span>
                <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-gray-600"></span> Target</span>
              </div>
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={ATTENDANCE_TRENDS}>
                  <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? "#1F2937" : "#E5E7EB"} />
                  <XAxis dataKey="day" stroke={darkMode ? "#9CA3AF" : "#4B5563"} />
                  <YAxis stroke={darkMode ? "#9CA3AF" : "#4B5563"} />
                  <Tooltip contentStyle={{ backgroundColor: darkMode ? "#1E293B" : "#FFFFFF", borderColor: darkMode ? "#475569" : "#CBD5E1" }} />
                  <Line type="monotone" dataKey="present" stroke="#06B6D4" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 8 }} />
                  <Line type="monotone" dataKey="expected" stroke="#4B5563" strokeWidth={2} strokeDasharray="5 5" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Interactive Geographic Mock Map */}
          <div className={`p-6 rounded-2xl border ${darkMode ? "bg-[#131C2E] border-gray-800/80" : "bg-white border-gray-200"}`}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="font-bold text-lg">Active Coverage Map</h3>
                <p className={`text-xs ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Visualizing live checking patterns</p>
              </div>
            </div>
            
            {/* Custom SVG coordinate layout representing villages visually */}
            <div className={`h-72 rounded-xl relative overflow-hidden flex items-center justify-center border ${
              darkMode ? "bg-[#090D16] border-gray-800/80" : "bg-slate-50 border-gray-200"
            }`}>
              <div className="absolute inset-0 opacity-10 bg-[linear-gradient(to_right,#808080_1px,transparent_1px),linear-gradient(to_bottom,#808080_1px,transparent_1px)] bg-[size:24px_24px]"></div>
              
              {/* Village Nodes on Mock Grid */}
              <div className="absolute top-[20%] left-[30%] group">
                <div className="w-5 h-5 rounded-full bg-emerald-500/20 border-2 border-emerald-500 flex items-center justify-center animate-ping"></div>
                <div className="absolute top-0 left-0 w-5 h-5 rounded-full bg-emerald-500 border border-white flex items-center justify-center text-[8px] font-bold text-white shadow">V1</div>
                <span className="absolute bottom-6 left-[-20px] bg-[#1E293B]/90 text-[10px] text-white px-2 py-0.5 rounded shadow whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">Solur (Covered)</span>
              </div>

              <div className="absolute top-[60%] left-[70%] group">
                <div className="w-5 h-5 rounded-full bg-emerald-500/20 border-2 border-emerald-500 flex items-center justify-center animate-ping"></div>
                <div className="absolute top-0 left-0 w-5 h-5 rounded-full bg-emerald-500 border border-white flex items-center justify-center text-[8px] font-bold text-white shadow">V2</div>
                <span className="absolute bottom-6 left-[-20px] bg-[#1E293B]/90 text-[10px] text-white px-2 py-0.5 rounded shadow whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">Megalapura (Covered)</span>
              </div>

              <div className="absolute top-[40%] left-[45%] group">
                <div className="absolute w-5 h-5 rounded-full bg-rose-500 border border-white flex items-center justify-center text-[8px] font-bold text-white shadow animate-pulse">V3</div>
                <span className="absolute bottom-6 left-[-20px] bg-[#1E293B]/90 text-[10px] text-rose-400 px-2 py-0.5 rounded shadow whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity font-bold">Hosur (Alert: Uncovered)</span>
              </div>

              {/* Grid Legend */}
              <div className="absolute bottom-3 left-3 flex gap-4 text-[10px] font-semibold bg-[#1E293B]/80 px-3 py-1.5 rounded-lg border border-gray-700/50 backdrop-blur-sm">
                <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Covered</span>
                <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Uncovered</span>
              </div>
            </div>
          </div>

        </div>

        {/* 5. Lower Splitted Content: AI Insights vs Feeds */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* AI Insights Widget */}
          <div className={`p-6 rounded-2xl border ${darkMode ? "bg-[#131C2E] border-gray-800/80" : "bg-white border-gray-200"}`}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-cyan-500/15 text-cyan-400">
                  <Sparkles className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-lg">AI Supervisor Insights</h3>
              </div>
              <span className="px-2.5 py-1 text-[10px] font-bold bg-[#1E293B] text-cyan-400 border border-cyan-500/20 rounded-full">Gemini Active</span>
            </div>

            <div className="space-y-4">
              {MOCK_INSIGHTS.map((insight) => (
                <div 
                  key={insight.id}
                  className={`p-4 rounded-xl border flex gap-3 ${
                    insight.type === "critical" 
                      ? "bg-rose-500/5 border-rose-500/20 text-rose-400" 
                      : (insight.type === "warning" ? "bg-amber-500/5 border-amber-500/20 text-amber-400" : "bg-cyan-500/5 border-cyan-500/20 text-cyan-400")
                  }`}
                >
                  <AlertTriangle className="w-5 h-5 shrink-0" />
                  <div>
                    <p className={`text-xs font-medium leading-relaxed ${darkMode ? "text-gray-200" : "text-gray-700"}`}>
                      {insight.text}
                    </p>
                    <span className="block text-[10px] text-gray-500 mt-1">{insight.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Worker Performance Charts */}
          <div className={`p-6 rounded-2xl border ${darkMode ? "bg-[#131C2E] border-gray-800/80" : "bg-white border-gray-200"}`}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="font-bold text-lg">Worker Efficiency</h3>
                <p className={`text-xs ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Completion rate of scheduled village visits</p>
              </div>
            </div>

            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={WORKER_EFFICIENCY} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? "#1F2937" : "#E5E7EB"} />
                  <XAxis type="number" stroke={darkMode ? "#9CA3AF" : "#4B5563"} domain={[0, 100]} />
                  <YAxis dataKey="name" type="category" stroke={darkMode ? "#9CA3AF" : "#4B5563"} width={60} />
                  <Tooltip contentStyle={{ backgroundColor: darkMode ? "#1E293B" : "#FFFFFF" }} />
                  <Bar dataKey="rate" radius={[0, 4, 4, 0]} barSize={12}>
                    {WORKER_EFFICIENCY.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.rate < 80 ? "#F43F5E" : "#06B6D4"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Notifications Feed */}
          <div className={`p-6 rounded-2xl border ${darkMode ? "bg-[#131C2E] border-gray-800/80" : "bg-white border-gray-200"}`}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-gray-400" />
                <h3 className="font-bold text-lg">Active Reassignments</h3>
              </div>
              <button className="text-xs text-cyan-400 font-semibold flex items-center hover:underline">
                View all <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            <div className="divide-y divide-gray-800/50">
              {ACTIVE_NOTIFICATIONS.map((notif, index) => (
                <div key={index} className="py-3.5 first:pt-0 last:pb-0">
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="font-semibold text-xs">{notif.title}</span>
                    <span className="text-[10px] text-gray-500">{notif.time}</span>
                  </div>
                  <p className={`text-xs ${darkMode ? "text-gray-400" : "text-gray-500"}`}>{notif.desc}</p>
                </div>
              ))}
            </div>
          </div>

        </div>

      </main>
    </div>
  );
}
