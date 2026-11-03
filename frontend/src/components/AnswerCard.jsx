import React from 'react';
import { CheckCircle2, AlertCircle, Quote } from 'lucide-react';

export default function AnswerCard({ question, answer, grounded, citationsCount = 0 }) {
  return (
    <div className="bg-slate-800/70 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-4">
      {/* Header with question and status badge */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-700/60">
        <div className="space-y-0.5">
          <span className="text-[11px] font-semibold tracking-wider uppercase text-slate-400">
            Student Question
          </span>
          <h3 className="text-base font-semibold text-white">"{question}"</h3>
        </div>

        {grounded ? (
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Grounded in Lectures ({citationsCount} cited)</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Not in Lectures / Refusal</span>
          </div>
        )}
      </div>

      {/* Answer Body */}
      <div className="relative pl-3 border-l-2 border-emerald-500/60">
        <p className="text-sm sm:text-base text-slate-200 leading-relaxed whitespace-pre-line font-normal">
          {answer}
        </p>
      </div>
    </div>
  );
}
