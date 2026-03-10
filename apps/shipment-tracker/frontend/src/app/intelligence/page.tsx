'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Brain,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  Sparkles,
  FileText,
  ThumbsUp,
  ThumbsDown,
  Loader2,
} from 'lucide-react';
import { api } from '@/lib/api';
import type { AiDealUpdateDetail, MemorySearchResult } from '@/lib/types';

export default function IntelligencePage() {
  const [activeTab, setActiveTab] = useState<'updates' | 'memory'>('updates');

  return (
    <div className="flex h-full flex-col overflow-hidden bg-zinc-950">
      {/* Header */}
      <div className="border-b border-zinc-800/60 px-6 py-4">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-zinc-100">
          <Brain size={20} className="text-purple-400" />
          AI Intelligence
        </h1>
        <p className="mt-0.5 text-sm text-zinc-500">
          Review AI-proposed deal updates and search meeting memory
        </p>

        <div className="mt-4 flex gap-1">
          {[
            { key: 'updates' as const, label: 'Deal Updates', icon: Sparkles },
            { key: 'memory' as const, label: 'Memory Search', icon: Search },
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                activeTab === key
                  ? 'bg-purple-600/20 text-purple-400'
                  : 'text-zinc-500 hover:bg-zinc-800/60 hover:text-zinc-300'
              }`}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'updates' && <DealUpdatesTab />}
        {activeTab === 'memory' && <MemorySearchTab />}
      </div>
    </div>
  );
}

function DealUpdatesTab() {
  const [updates, setUpdates] = useState<AiDealUpdateDetail[]>([]);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.getAiDealUpdates(statusFilter);
      setUpdates(res.items);
    } catch {
      setUpdates([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    setProcessing((prev) => new Set(prev).add(id));
    try {
      if (action === 'approve') {
        await api.approveAiDealUpdate(id);
      } else {
        await api.rejectAiDealUpdate(id);
      }
      setUpdates((prev) => prev.filter((u) => u.id !== id));
    } catch {
      // ignore
    } finally {
      setProcessing((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  return (
    <div className="space-y-4">
      {/* Filter */}
      <div className="flex gap-1.5">
        {['pending', 'approved', 'rejected', 'all'].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              statusFilter === s
                ? 'bg-purple-600 text-white'
                : 'bg-zinc-800/60 text-zinc-400 hover:bg-zinc-700/60'
            }`}
          >
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="animate-spin text-purple-500" />
        </div>
      ) : updates.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Sparkles size={32} className="mb-3 text-zinc-600" />
          <p className="text-sm text-zinc-400">No {statusFilter} deal updates</p>
          <p className="mt-1 text-xs text-zinc-600">
            AI will propose updates when it processes meeting transcripts
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {updates.map((u) => (
            <div
              key={u.id}
              className="rounded-xl border border-zinc-800/60 bg-zinc-900/30 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 text-xs text-zinc-500">
                    <span className="font-medium text-zinc-300">{u.contract_id}</span>
                    <span>·</span>
                    <span>{u.commodity}</span>
                    <span>·</span>
                    <span>{u.buyer} → {u.seller}</span>
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="rounded bg-zinc-800 px-2 py-0.5 text-xs font-mono text-zinc-400">
                      {u.field_name}
                    </span>
                    <span className="text-sm text-zinc-500">{u.old_value || '(empty)'}</span>
                    <ArrowRight size={14} className="text-zinc-600" />
                    <span className="text-sm font-medium text-purple-400">{u.proposed_value}</span>
                  </div>
                  <p className="mt-2 text-xs text-zinc-500">{u.reasoning}</p>
                  <div className="mt-2 flex items-center gap-3 text-xs text-zinc-600">
                    <span className="flex items-center gap-1">
                      <FileText size={12} />
                      {u.meeting_title}
                    </span>
                    <span>Confidence: {Math.round(u.confidence * 100)}%</span>
                    {u.meeting_date && <span>{new Date(u.meeting_date).toLocaleDateString()}</span>}
                  </div>
                </div>

                {u.status === 'pending' && (
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => handleAction(u.id, 'approve')}
                      disabled={processing.has(u.id)}
                      className="rounded-lg bg-emerald-600/20 p-2 text-emerald-400 hover:bg-emerald-600/30 disabled:opacity-40 transition-colors"
                      title="Approve"
                    >
                      {processing.has(u.id) ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <ThumbsUp size={16} />
                      )}
                    </button>
                    <button
                      onClick={() => handleAction(u.id, 'reject')}
                      disabled={processing.has(u.id)}
                      className="rounded-lg bg-red-600/20 p-2 text-red-400 hover:bg-red-600/30 disabled:opacity-40 transition-colors"
                      title="Reject"
                    >
                      <ThumbsDown size={16} />
                    </button>
                  </div>
                )}
                {u.status === 'approved' && (
                  <CheckCircle2 size={18} className="text-emerald-500" />
                )}
                {u.status === 'rejected' && (
                  <XCircle size={18} className="text-red-500" />
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MemorySearchTab() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<MemorySearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    setSearched(true);
    try {
      const res = await api.searchMemory(query.trim());
      setResults(res.results);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Search input */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search across all meeting transcripts and summaries..."
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800/60 py-2.5 pl-10 pr-4 text-sm text-zinc-200 placeholder-zinc-500 focus:border-purple-500 focus:outline-none"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={!query.trim() || searching}
          className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-500 disabled:opacity-40 transition-colors"
        >
          {searching ? <Loader2 size={16} className="animate-spin" /> : 'Search'}
        </button>
      </div>

      {/* Results */}
      {searching ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="animate-spin text-purple-500" />
        </div>
      ) : results.length > 0 ? (
        <div className="space-y-3">
          {results.map((r, i) => (
            <div
              key={i}
              className="rounded-xl border border-zinc-800/60 bg-zinc-900/30 p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs">
                  <span className="font-medium text-zinc-300">{r.meeting_title}</span>
                  <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-zinc-500">
                    {r.chunk_type}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-600">
                  <span>{Math.round(r.similarity * 100)}% match</span>
                  {r.scheduled_start && (
                    <span>{new Date(r.scheduled_start).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-zinc-400">
                {r.chunk_text}
              </p>
            </div>
          ))}
        </div>
      ) : searched ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Search size={32} className="mb-3 text-zinc-600" />
          <p className="text-sm text-zinc-400">No results found</p>
          <p className="mt-1 text-xs text-zinc-600">
            Try different search terms or wait for more meetings to be processed
          </p>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Brain size={32} className="mb-3 text-zinc-600" />
          <p className="text-sm text-zinc-400">Semantic Meeting Memory</p>
          <p className="mt-1 text-xs text-zinc-600">
            Search across all meeting transcripts and AI summaries using natural language
          </p>
        </div>
      )}
    </div>
  );
}
