'use client';

import React, { useEffect, useState } from 'react';
import { UserCheck, AlertTriangle, ShieldCheck } from 'lucide-react';
import { cn } from '@/lib/shadcn/utils';

interface Escalation {
  reference_id: string;
  reason: string;
  short_summary: string;
  urgency: string;
  status: string;
  created_at: string;
}

export function HumanSupportCard() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  const fetchEscalations = async () => {
    try {
      const res = await fetch('/api/escalations');
      if (res.ok) {
        const data = await res.json();
        setEscalations(data);
      }
    } catch (err) {
      console.error('Failed to fetch escalations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEscalations();
    // Poll for status updates every 5 seconds
    const interval = setInterval(fetchEscalations, 5000);
    return () => clearInterval(interval);
  }, []);

  const latest = escalations[0];

  return (
    <div className="flex flex-col items-start gap-2 text-xs select-none">
      {/* Collapsed Badge / Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-zinc-200 bg-background/90 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950/90 dark:hover:bg-zinc-900 backdrop-blur-md shadow-xs font-semibold cursor-pointer transition-all duration-200 text-[11px]"
      >
        <span
          className={cn(
            "size-2 rounded-full",
            latest ? "bg-amber-500 animate-pulse" : "bg-teal-500"
          )}
        />
        <span className="tracking-wide uppercase text-muted-foreground hover:text-foreground">
          {latest ? `Support: Active` : `Human Support`}
        </span>
        <span className="text-[9px] text-muted-foreground opacity-60">
          {isOpen ? '▲' : '▼'}
        </span>
      </button>

      {/* Expanded Details Card */}
      {isOpen && (
        <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-background/95 backdrop-blur-md shadow-md max-w-xs w-64 md:w-72 text-xs transition-all duration-300 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5 font-semibold text-foreground text-[13px]">
              <UserCheck className="size-4 text-teal-600 dark:text-teal-400" />
              <span>Human Support</span>
            </div>
            <span
              className={cn(
                "px-2 py-0.5 rounded-full text-[9px] font-bold tracking-wide uppercase",
                latest
                  ? "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200/50 dark:border-amber-900/30"
                  : "bg-teal-50 text-teal-700 dark:bg-teal-950/20 dark:text-teal-400 border border-teal-100/50 dark:border-teal-900/20"
              )}
            >
              {latest ? "Active Request" : "Idle"}
            </span>
          </div>

          {latest ? (
            <div className="space-y-2 mt-3 pt-2.5 border-t border-zinc-100 dark:border-zinc-900">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground font-medium">Ref ID:</span>
                <span className="font-mono font-bold text-foreground select-all bg-zinc-100 dark:bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-200 dark:border-zinc-800 text-[10px]">
                  {latest.reference_id}
                </span>
              </div>
              <div className="flex justify-between items-start gap-2">
                <span className="text-muted-foreground font-medium">Reason:</span>
                <span className="text-foreground font-semibold text-right line-clamp-1">
                  {latest.reason}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground font-medium">Urgency:</span>
                <span
                  className={cn(
                    "px-1.5 py-0.5 rounded text-[9px] font-bold uppercase border",
                    latest.urgency.toLowerCase() === 'high'
                      ? "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400 border-red-100/50 dark:border-red-900/20"
                      : "bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-400 border-amber-100/50 dark:border-amber-900/20"
                  )}
                >
                  {latest.urgency}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground font-medium">Status:</span>
                <span className="text-foreground font-semibold flex items-center gap-1">
                  <span className="size-1.5 rounded-full bg-amber-500 animate-ping" />
                  <span>{latest.status}</span>
                </span>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground text-xs mt-2 leading-relaxed">
              No pending escalation requests. Anisha is monitoring calls.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
