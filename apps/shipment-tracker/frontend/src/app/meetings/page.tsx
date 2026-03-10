'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  Video,
  Clock,
  Users,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  FileText,
  ListChecks,
  Sparkles,
  Plus,
  X,
} from 'lucide-react';
import { api } from '@/lib/api';
import type {
  Meeting,
  MeetingStatus,
  TranscriptSegment,
  ActionItem,
} from '@/lib/types';

const STATUS_CONFIG: Record<MeetingStatus, { label: string; color: string; bg: string }> = {
  scheduled: { label: 'Scheduled', color: 'text-blue-400', bg: 'bg-blue-500/10' },
  in_progress: { label: 'In Progress', color: 'text-green-400', bg: 'bg-green-500/10' },
  processing: { label: 'Processing', color: 'text-amber-400', bg: 'bg-amber-500/10' },
  completed: { label: 'Completed', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  failed: { label: 'Failed', color: 'text-red-400', bg: 'bg-red-500/10' },
  cancelled: { label: 'Cancelled', color: 'text-zinc-500', bg: 'bg-zinc-500/10' },
};

const PRIORITY_COLORS: Record<string, string> = {
  urgent: 'border-red-500/40 bg-red-500/5',
  high: 'border-amber-500/40 bg-amber-500/5',
  medium: 'border-blue-500/40 bg-blue-500/5',
  low: 'border-zinc-700 bg-zinc-900/50',
};

function formatTime(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatTimestamp(ms: number): string {
  const mins = Math.floor(ms / 60000);
  const secs = Math.floor((ms % 60000) / 1000);
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [transcript, setTranscript] = useState<TranscriptSegment[]>([]);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [activeTab, setActiveTab] = useState<'summary' | 'transcript' | 'actions'>('summary');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');

  const loadMeetings = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.getMeetings(1, 50, statusFilter || undefined);
      setMeetings(res.items);
    } catch {
      // API may not be available yet
      setMeetings([]);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadMeetings();
  }, [loadMeetings]);

  const selectMeeting = async (meeting: Meeting) => {
    setSelectedMeeting(meeting);
    setActiveTab('summary');

    try {
      const [t, a] = await Promise.all([
        api.getTranscript(meeting.id),
        api.getActionItems(meeting.id),
      ]);
      setTranscript(t);
      setActionItems(a);
    } catch {
      setTranscript([]);
      setActionItems([]);
    }
  };

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    try {
      const m = await api.createMeeting({ title: newTitle.trim() });
      setMeetings((prev) => [m, ...prev]);
      setShowCreateModal(false);
      setNewTitle('');
    } catch {
      // ignore
    }
  };

  return (
    <div className="flex h-full overflow-hidden bg-zinc-950">
      {/* Left: Meeting List */}
      <div className="flex w-96 flex-shrink-0 flex-col border-r border-zinc-800/60">
        {/* Header */}
        <div className="border-b border-zinc-800/60 px-4 py-3">
          <div className="flex items-center justify-between">
            <h1 className="flex items-center gap-2 text-lg font-semibold text-zinc-100">
              <Calendar size={20} className="text-blue-400" />
              Meetings
            </h1>
            <button
              onClick={() => setShowCreateModal(true)}
              className="rounded-lg bg-blue-600 p-1.5 text-white hover:bg-blue-500 transition-colors"
            >
              <Plus size={16} />
            </button>
          </div>

          {/* Status filters */}
          <div className="mt-3 flex gap-1.5 overflow-x-auto">
            {['', 'scheduled', 'in_progress', 'completed'].map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`whitespace-nowrap rounded-full px-2.5 py-1 text-xs transition-colors ${
                  statusFilter === s
                    ? 'bg-blue-600 text-white'
                    : 'bg-zinc-800/60 text-zinc-400 hover:bg-zinc-700/60'
                }`}
              >
                {s ? STATUS_CONFIG[s as MeetingStatus]?.label : 'All'}
              </button>
            ))}
          </div>
        </div>

        {/* Meeting list */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
            </div>
          ) : meetings.length === 0 ? (
            <div className="px-4 py-12 text-center">
              <Video size={32} className="mx-auto mb-3 text-zinc-600" />
              <p className="text-sm text-zinc-500">No meetings found</p>
              <p className="mt-1 text-xs text-zinc-600">
                Meetings will appear when synced from Google Calendar
              </p>
            </div>
          ) : (
            meetings.map((m) => {
              const cfg = STATUS_CONFIG[m.status];
              const isSelected = selectedMeeting?.id === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => selectMeeting(m)}
                  className={`w-full border-b border-zinc-800/40 px-4 py-3 text-left transition-colors ${
                    isSelected
                      ? 'bg-blue-600/10 border-l-2 border-l-blue-500'
                      : 'hover:bg-zinc-900/50'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-sm font-medium text-zinc-200 line-clamp-1">
                      {m.title}
                    </h3>
                    <ChevronRight size={14} className="mt-0.5 flex-shrink-0 text-zinc-600" />
                  </div>
                  <div className="mt-1.5 flex items-center gap-3 text-xs">
                    <span className={`rounded-full px-2 py-0.5 ${cfg.bg} ${cfg.color}`}>
                      {cfg.label}
                    </span>
                    {m.scheduled_start && (
                      <span className="text-zinc-500">
                        {formatDate(m.scheduled_start)} {formatTime(m.scheduled_start)}
                      </span>
                    )}
                  </div>
                  {m.participants.length > 0 && (
                    <div className="mt-1.5 flex items-center gap-1 text-xs text-zinc-500">
                      <Users size={12} />
                      <span>{m.participants.length} participants</span>
                    </div>
                  )}
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Right: Detail panel */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {selectedMeeting ? (
          <>
            {/* Meeting header */}
            <div className="border-b border-zinc-800/60 px-6 py-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-zinc-100">
                    {selectedMeeting.title}
                  </h2>
                  <div className="mt-1 flex items-center gap-4 text-sm text-zinc-400">
                    {selectedMeeting.scheduled_start && (
                      <span className="flex items-center gap-1">
                        <Clock size={14} />
                        {formatDate(selectedMeeting.scheduled_start)}{' '}
                        {formatTime(selectedMeeting.scheduled_start)}
                        {selectedMeeting.scheduled_end &&
                          ` – ${formatTime(selectedMeeting.scheduled_end)}`}
                      </span>
                    )}
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${STATUS_CONFIG[selectedMeeting.status].bg} ${STATUS_CONFIG[selectedMeeting.status].color}`}
                    >
                      {STATUS_CONFIG[selectedMeeting.status].label}
                    </span>
                  </div>
                </div>
                {selectedMeeting.google_meet_url && (
                  <a
                    href={selectedMeeting.google_meet_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 rounded-lg bg-green-600/20 px-3 py-1.5 text-xs font-medium text-green-400 hover:bg-green-600/30 transition-colors"
                  >
                    <Video size={14} />
                    Join Meet
                  </a>
                )}
              </div>

              {/* Participants */}
              {selectedMeeting.participants.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {selectedMeeting.participants.map((p) => (
                    <span
                      key={p.id}
                      className="rounded-full bg-zinc-800/80 px-2.5 py-0.5 text-xs text-zinc-300"
                    >
                      {p.name}
                      {p.role === 'organizer' && (
                        <span className="ml-1 text-amber-400">★</span>
                      )}
                    </span>
                  ))}
                </div>
              )}

              {/* Tabs */}
              <div className="mt-4 flex gap-1">
                {[
                  { key: 'summary' as const, label: 'Summary', icon: Sparkles },
                  { key: 'transcript' as const, label: 'Transcript', icon: FileText },
                  { key: 'actions' as const, label: 'Action Items', icon: ListChecks },
                ].map(({ key, label, icon: Icon }) => (
                  <button
                    key={key}
                    onClick={() => setActiveTab(key)}
                    className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                      activeTab === key
                        ? 'bg-blue-600/20 text-blue-400'
                        : 'text-zinc-500 hover:bg-zinc-800/60 hover:text-zinc-300'
                    }`}
                  >
                    <Icon size={14} />
                    {label}
                    {key === 'actions' && actionItems.length > 0 && (
                      <span className="ml-1 rounded-full bg-blue-600/30 px-1.5 text-[10px]">
                        {actionItems.length}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-y-auto p-6">
              {activeTab === 'summary' && (
                <SummaryTab meeting={selectedMeeting} />
              )}
              {activeTab === 'transcript' && (
                <TranscriptTab segments={transcript} />
              )}
              {activeTab === 'actions' && (
                <ActionItemsTab items={actionItems} />
              )}
            </div>
          </>
        ) : (
          /* Empty state */
          <div className="flex flex-1 items-center justify-center">
            <div className="max-w-sm text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-zinc-800/80">
                <Calendar size={28} className="text-zinc-500" />
              </div>
              <h2 className="text-base font-medium text-zinc-300">
                Select a meeting
              </h2>
              <p className="mt-2 text-sm text-zinc-500">
                Choose a meeting from the list to view its summary, transcript, and action items.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Create modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-md rounded-xl bg-zinc-900 border border-zinc-800 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-zinc-100">Schedule Meeting</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-zinc-500 hover:text-zinc-300">
                <X size={18} />
              </button>
            </div>
            <input
              type="text"
              placeholder="Meeting title..."
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
              autoFocus
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setShowCreateModal(false)}
                className="rounded-lg px-3 py-1.5 text-sm text-zinc-400 hover:bg-zinc-800"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!newTitle.trim()}
                className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-500 disabled:opacity-40"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryTab({ meeting }: { meeting: Meeting }) {
  if (!meeting.summary) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <Sparkles size={32} className="mb-3 text-zinc-600" />
        <p className="text-sm text-zinc-400">No AI summary available yet</p>
        <p className="mt-1 text-xs text-zinc-600">
          {meeting.status === 'scheduled'
            ? 'Summary will be generated after the meeting is transcribed'
            : meeting.status === 'processing'
            ? 'AI is processing the transcript...'
            : 'This meeting does not have an AI summary'}
        </p>
      </div>
    );
  }

  const { summary } = meeting;

  return (
    <div className="space-y-6">
      {/* Summary text */}
      <div>
        <h3 className="mb-2 text-sm font-medium text-zinc-300">Summary</h3>
        <p className="text-sm leading-relaxed text-zinc-400">{summary.summary_text}</p>
      </div>

      {/* Key decisions */}
      {summary.key_decisions.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-medium text-zinc-300">Key Decisions</h3>
          <ul className="space-y-1.5">
            {summary.key_decisions.map((d, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-zinc-400">
                <CheckCircle2 size={14} className="mt-0.5 flex-shrink-0 text-emerald-500" />
                {d}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Market intel */}
      {summary.market_intel.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-medium text-zinc-300">Market Intelligence</h3>
          <ul className="space-y-1.5">
            {summary.market_intel.map((m, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-zinc-400">
                <AlertCircle size={14} className="mt-0.5 flex-shrink-0 text-blue-500" />
                {m}
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-zinc-600">
        Generated {timeAgo(summary.created_at)}
      </p>
    </div>
  );
}

function TranscriptTab({ segments }: { segments: TranscriptSegment[] }) {
  if (segments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <FileText size={32} className="mb-3 text-zinc-600" />
        <p className="text-sm text-zinc-400">No transcript available</p>
        <p className="mt-1 text-xs text-zinc-600">
          Transcript will appear after the meeting is recorded
        </p>
      </div>
    );
  }

  // Group by speaker for visual separation
  const speakers = [...new Set(segments.map((s) => s.speaker_name))];
  const speakerColors = ['text-blue-400', 'text-emerald-400', 'text-amber-400', 'text-purple-400', 'text-rose-400'];

  return (
    <div className="space-y-3">
      {/* Speaker legend */}
      <div className="flex flex-wrap gap-3 rounded-lg bg-zinc-900/50 p-3">
        {speakers.map((name, i) => (
          <span key={name} className="flex items-center gap-1.5 text-xs">
            <span className={`h-2 w-2 rounded-full ${speakerColors[i % speakerColors.length].replace('text-', 'bg-')}`} />
            <span className="text-zinc-400">{name}</span>
          </span>
        ))}
      </div>

      {/* Segments */}
      <div className="space-y-2">
        {segments.map((seg) => {
          const speakerIdx = speakers.indexOf(seg.speaker_name);
          const color = speakerColors[speakerIdx % speakerColors.length];
          return (
            <div key={seg.id} className="group flex gap-3 rounded-lg p-2 hover:bg-zinc-900/30">
              <span className="flex-shrink-0 pt-0.5 text-xs font-mono text-zinc-600">
                {formatTimestamp(seg.start_ms)}
              </span>
              <div>
                <span className={`text-xs font-medium ${color}`}>
                  {seg.speaker_name}
                </span>
                <p className="mt-0.5 text-sm text-zinc-300">{seg.text}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ActionItemsTab({ items }: { items: ActionItem[] }) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <ListChecks size={32} className="mb-3 text-zinc-600" />
        <p className="text-sm text-zinc-400">No action items</p>
        <p className="mt-1 text-xs text-zinc-600">
          AI will extract action items from the meeting transcript
        </p>
      </div>
    );
  }

  const open = items.filter((i) => i.status === 'open' || i.status === 'in_progress');
  const done = items.filter((i) => i.status === 'done' || i.status === 'cancelled');

  return (
    <div className="space-y-6">
      {open.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-zinc-300">
            Open ({open.length})
          </h3>
          <div className="space-y-2">
            {open.map((item) => (
              <ActionItemCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}

      {done.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-zinc-500">
            Completed ({done.length})
          </h3>
          <div className="space-y-2 opacity-60">
            {done.map((item) => (
              <ActionItemCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ActionItemCard({ item }: { item: ActionItem }) {
  const borderColor = PRIORITY_COLORS[item.priority] || PRIORITY_COLORS.low;
  const isDone = item.status === 'done' || item.status === 'cancelled';

  return (
    <div className={`rounded-lg border p-3 ${borderColor}`}>
      <div className="flex items-start justify-between gap-2">
        <h4 className={`text-sm font-medium ${isDone ? 'text-zinc-500 line-through' : 'text-zinc-200'}`}>
          {item.title}
        </h4>
        <span className={`flex-shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase ${
          item.priority === 'urgent'
            ? 'bg-red-500/20 text-red-400'
            : item.priority === 'high'
            ? 'bg-amber-500/20 text-amber-400'
            : item.priority === 'medium'
            ? 'bg-blue-500/20 text-blue-400'
            : 'bg-zinc-700 text-zinc-400'
        }`}>
          {item.priority}
        </span>
      </div>
      {item.description && (
        <p className="mt-1 text-xs text-zinc-500">{item.description}</p>
      )}
      <div className="mt-2 flex items-center gap-3 text-xs text-zinc-500">
        {item.assignee_name && (
          <span className="flex items-center gap-1">
            <Users size={12} />
            {item.assignee_name}
          </span>
        )}
        {item.due_date && (
          <span className="flex items-center gap-1">
            <Clock size={12} />
            Due {formatDate(item.due_date)}
          </span>
        )}
      </div>
    </div>
  );
}
