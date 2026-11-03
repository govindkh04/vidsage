import React from 'react';
import { Sparkles, Video, Search, MessageSquareCode, Database } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, health }) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('ask')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Sparkles className="w-5 h-5 text-slate-950 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight text-white">VidSage</span>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                AI Assistant
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Your videos. Your knowledge. Instantly.</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center space-x-1 bg-slate-800/60 p-1 rounded-xl border border-slate-700/50">
          <button
            onClick={() => setActiveTab('ask')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'ask'
                ? 'bg-emerald-500 text-slate-950 shadow-md font-semibold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <MessageSquareCode className="w-4 h-4" />
            <span>Revision Assistant</span>
          </button>

          <button
            onClick={() => setActiveTab('search')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'search'
                ? 'bg-emerald-500 text-slate-950 shadow-md font-semibold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Search className="w-4 h-4" />
            <span>Direct Search</span>
          </button>

          <button
            onClick={() => setActiveTab('library')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'library'
                ? 'bg-emerald-500 text-slate-950 shadow-md font-semibold'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Video className="w-4 h-4" />
            <span>Lectures</span>
          </button>
        </div>

        {/* Health status badge */}
        <div className="hidden md:flex items-center space-x-2 text-xs">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700/60 text-slate-300">
            <span
              className={`w-2 h-2 rounded-full ${
                health?.status === 'ok' ? 'bg-emerald-400 animate-pulse' : 'bg-yellow-400'
              }`}
            />
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span>{health?.total_indexed_chunks || 0} chunks</span>
          </div>
        </div>
      </div>
    </header>
  );
}
