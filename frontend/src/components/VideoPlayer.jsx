import React from 'react';
import { Youtube, Clock, ExternalLink } from 'lucide-react';

export default function VideoPlayer({ activeCitation, isPlayerReady }) {
  const containerId = "vidsage-youtube-iframe";

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl overflow-hidden shadow-2xl flex flex-col">
      {/* Header bar */}
      <div className="px-4 py-3 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between gap-3">
        <div className="flex items-center space-x-2 truncate">
          <Youtube className="w-5 h-5 text-red-500 shrink-0" />
          <span className="text-sm font-semibold text-slate-200 truncate">
            {activeCitation ? activeCitation.title : 'Embedded Lecture Player'}
          </span>
        </div>

        {activeCitation && (
          <div className="flex items-center space-x-2 shrink-0">
            <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-mono text-xs font-semibold border border-emerald-500/30">
              <Clock className="w-3 h-3" />
              <span>{activeCitation.timestamp}</span>
            </span>
          </div>
        )}
      </div>

      {/* Video Container (16:9 Aspect Ratio) */}
      <div className="relative w-full aspect-video bg-black flex items-center justify-center">
        {/* The YouTube iframe mounts inside this container */}
        <div id={containerId} className="w-full h-full" />

        {/* Placeholder before any citation is selected */}
        {!activeCitation && (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center bg-slate-950/80 space-y-3 pointer-events-none">
            <div className="w-16 h-16 rounded-2xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-slate-500">
              <Youtube className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-300">No Lecture Selected</p>
              <p className="text-xs text-slate-500 max-w-sm">
                Ask a question or click any citation card to automatically jump to that exact explanation.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      {activeCitation && (
        <div className="p-3 bg-slate-900/60 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <span>Jumping 5s before timestamp for immediate context</span>
          <a
            href={activeCitation.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1 text-emerald-400 hover:text-emerald-300 transition-colors"
          >
            <span>YouTube URL</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      )}
    </div>
  );
}
