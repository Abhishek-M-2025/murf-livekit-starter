'use client';

import { useMemo, useState, useEffect } from 'react';
import { TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { ViewController } from '@/components/app/view-controller';
import { HumanSupportCard } from '@/components/app/human-support-card';
import { Toaster } from '@/components/ui/sonner';
import { useAgentErrors } from '@/hooks/useAgentErrors';
import { useDebugMode } from '@/hooks/useDebug';
import { getSandboxTokenSource } from '@/lib/utils';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();

  return null;
}

interface AppProps {
  appConfig: AppConfig;
}

// =============================================================
// Outbound Call View
// =============================================================

function OutboundCallView() {
  const [destination, setDestination] = useState(
    'sip:abhishek2026@sip.linphone.org'
  );

  const [userName, setUserName] = useState('Abhishek');

  const [status, setStatus] = useState<
    'idle' | 'loading' | 'success' | 'error'
  >('idle');

  const [message, setMessage] = useState('');

  const handleTriggerOutbound = async () => {
    setStatus('loading');
    setMessage('');

    try {
      const response = await fetch('/api/outbound', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          destination: destination || undefined,
          user_name: userName || undefined,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to trigger call');
      }

      setStatus('success');
      setMessage(
        `Call connected successfully in room ${data.room_name}`
      );
    } catch (err) {
      console.error(err);

      setStatus('error');

      setMessage(
        err instanceof Error
          ? err.message
          : 'An error occurred triggering the call.'
      );
    }
  };

  return (
    <div className="relative z-10 flex-1 flex flex-col items-center justify-center p-6 w-full">
      <div className="w-full max-w-md border border-blue-100/70 dark:border-zinc-800 bg-white/60 dark:bg-zinc-900/40 rounded-3xl p-8 shadow-sm backdrop-blur-md flex flex-col relative">

        <h2 className="text-xl font-bold text-foreground mb-1 text-center">
          Care Circle Outbound Dialer
        </h2>

        <p className="text-xs text-muted-foreground text-center mb-6">
          Initiate an automated medication reminder outbound SIP call.
        </p>

        <div className="space-y-4">

          {/* SIP Destination */}
          <div>
            <label
              htmlFor="sip-destination"
              className="block text-xs font-semibold text-muted-foreground mb-1.5"
            >
              SIP Destination / Phone Number
            </label>

            <input
              id="sip-destination"
              type="text"
              placeholder="sip:abhishek2026@sip.linphone.org"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-input bg-background/50 text-sm focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500/20"
            />
          </div>

          {/* Patient Name */}
          <div>
            <label
              htmlFor="user-name"
              className="block text-xs font-semibold text-muted-foreground mb-1.5"
            >
              Patient Name (Optional)
            </label>

            <input
              id="user-name"
              type="text"
              placeholder="Abhishek"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-input bg-background/50 text-sm focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500/20"
            />
          </div>

          {/* Call Button */}
          <button
            type="button"
            onClick={handleTriggerOutbound}
            disabled={status === 'loading'}
            className="w-full mt-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm py-2.5 rounded-xl shadow-xs flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 transition-colors"
          >
            {status === 'loading' && (
              <span className="animate-spin mr-1">
                🌀
              </span>
            )}

            Initiate Callback Reminder
          </button>

          {/* Success */}
          {status === 'success' && (
            <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-2 text-center font-semibold">
              {message}
            </p>
          )}

          {/* Error */}
          {status === 'error' && (
            <p className="text-xs text-red-600 dark:text-red-400 mt-2 text-center font-semibold">
              {message}
            </p>
          )}

        </div>
      </div>
    </div>
  );
}

// =============================================================
// Dashboard View
// =============================================================

function DashboardView() {
  const [data, setData] = useState<{
    total_calls: number;
    successful_calls: number;
    failed_calls: number;
  } | null>(null);

  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      const res = await fetch('/api/analytics', {
        cache: 'no-store',
      });

      if (res.ok) {
        const payload = await res.json();
        setData(payload);
      }
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();

    const interval = setInterval(fetchAnalytics, 4000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative z-10 flex-1 flex flex-col items-center justify-center p-6 w-full">

      <div className="w-full max-w-2xl border border-blue-100/70 dark:border-zinc-800 bg-white/60 dark:bg-zinc-900/40 rounded-3xl p-8 shadow-sm backdrop-blur-md flex flex-col">

        <h2 className="text-xl font-bold text-foreground mb-1 text-center">
          Call Analytics Dashboard
        </h2>

        <p className="text-xs text-muted-foreground text-center mb-8">
          Real-time metrics for browser and outbound SIP calls.
        </p>

        {loading && !data ? (
          <div className="flex justify-center items-center py-12">
            <span className="animate-spin text-teal-600">
              🌀
            </span>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-4 mb-6">

            {/* Total */}
            <div className="bg-white/85 dark:bg-zinc-950/40 border border-blue-100/60 dark:border-zinc-800 p-6 rounded-2xl text-center shadow-2xs">

              <span className="text-3xl font-extrabold text-foreground block">
                {data?.total_calls ?? 0}
              </span>

              <span className="text-[11px] font-semibold tracking-wider text-muted-foreground uppercase mt-2 block">
                Total Calls
              </span>

            </div>

            {/* Successful */}
            <div className="bg-emerald-50/30 dark:bg-emerald-950/10 border border-emerald-100/50 dark:border-emerald-900/20 p-6 rounded-2xl text-center shadow-2xs">

              <span className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 block">
                {data?.successful_calls ?? 0}
              </span>

              <span className="text-[11px] font-semibold tracking-wider text-emerald-600 dark:text-emerald-400 uppercase mt-2 block">
                Successful
              </span>

            </div>

            {/* Failed */}
            <div className="bg-red-50/30 dark:bg-red-950/10 border border-red-100/50 dark:border-red-900/20 p-6 rounded-2xl text-center shadow-2xs">

              <span className="text-3xl font-extrabold text-red-500 block">
                {data?.failed_calls ?? 0}
              </span>

              <span className="text-[11px] font-semibold tracking-wider text-red-500 uppercase mt-2 block">
                Failed Calls
              </span>

            </div>

          </div>
        )}

        <div className="bg-blue-50/20 dark:bg-zinc-950/20 border border-blue-100/30 dark:border-zinc-800/40 p-4 rounded-xl text-center text-[10px] text-muted-foreground">
          ℹ️ Outcomes are evaluated dynamically. A call is successful if the
          caller receives safe health guidance or is escalated to human support.
        </div>

      </div>
    </div>
  );
}

// =============================================================
// Main App
// =============================================================

export function App({ appConfig }: AppProps) {

  const [activeTab, setActiveTab] = useState<
    'home' | 'outbound' | 'dashboard'
  >('home');

  const tokenSource = useMemo(() => {
    return typeof process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT === 'string'
      ? getSandboxTokenSource(appConfig)
      : TokenSource.endpoint('/api/token');
  }, [appConfig]);

  const session = useSession(
    tokenSource,
    appConfig.agentName
      ? { agentName: appConfig.agentName }
      : undefined
  );

  return (
    <AgentSessionProvider session={session}>

      <AppSetup />

      <div className="relative flex flex-col min-h-screen bg-background text-foreground transition-colors duration-300">

        {/* =====================================================
            NAVBAR
        ====================================================== */}

        <header className="relative z-[100] w-full max-w-5xl mx-auto pt-6 px-4">

          <div className="relative z-[100] flex items-center justify-between border border-blue-100/70 bg-white/60 dark:bg-zinc-900/60 backdrop-blur-md px-6 py-3 rounded-2xl shadow-sm">

            {/* Logo */}
            <div className="flex items-center gap-2 shrink-0">

              <span className="text-teal-600 dark:text-teal-400 font-bold text-lg tracking-tight">
                Aarogya Sahayak
              </span>

            </div>

            {/* Navigation */}
            <nav className="relative z-[110] flex items-center gap-2">

              {/* HOME */}
              <button
                type="button"
                onClick={() => setActiveTab('home')}
                className={`relative z-[120] px-4 py-2 text-xs font-semibold rounded-xl border transition-all duration-200 cursor-pointer flex items-center gap-2 ${
                  activeTab === 'home'
                    ? 'bg-teal-50 border-teal-200 text-teal-700 dark:bg-teal-950/40 dark:border-teal-900/50 dark:text-teal-300 shadow-2xs'
                    : 'bg-white/40 border-blue-100 text-muted-foreground hover:bg-blue-50 hover:border-blue-200 hover:text-teal-700 dark:bg-zinc-900/40 dark:border-zinc-700 dark:hover:bg-zinc-800'
                }`}
              >
                <span>🏠</span>
                <span>Home</span>
              </button>

              {/* OUTBOUND */}
              <button
                type="button"
                onClick={() => setActiveTab('outbound')}
                className={`relative z-[120] px-4 py-2 text-xs font-semibold rounded-xl border transition-all duration-200 cursor-pointer flex items-center gap-2 ${
                  activeTab === 'outbound'
                    ? 'bg-teal-50 border-teal-200 text-teal-700 dark:bg-teal-950/40 dark:border-teal-900/50 dark:text-teal-300 shadow-2xs'
                    : 'bg-white/40 border-blue-100 text-muted-foreground hover:bg-blue-50 hover:border-blue-200 hover:text-teal-700 dark:bg-zinc-900/40 dark:border-zinc-700 dark:hover:bg-zinc-800'
                }`}
              >
                <span>📞</span>
                <span>Outbound Call</span>
              </button>

              {/* DASHBOARD */}
              <button
                type="button"
                onClick={() => setActiveTab('dashboard')}
                className={`relative z-[120] px-4 py-2 text-xs font-semibold rounded-xl border transition-all duration-200 cursor-pointer flex items-center gap-2 ${
                  activeTab === 'dashboard'
                    ? 'bg-teal-50 border-teal-200 text-teal-700 dark:bg-teal-950/40 dark:border-teal-900/50 dark:text-teal-300 shadow-2xs'
                    : 'bg-white/40 border-blue-100 text-muted-foreground hover:bg-blue-50 hover:border-blue-200 hover:text-teal-700 dark:bg-zinc-900/40 dark:border-zinc-700 dark:hover:bg-zinc-800'
                }`}
              >
                <span>📊</span>
                <span>Dashboard</span>
              </button>

            </nav>

            {/* Balance area */}
            <div className="w-[140px] shrink-0" />

          </div>
        </header>

        {/* =====================================================
            HUMAN SUPPORT
            Separate from navbar - LEFT SIDE
        ====================================================== */}

        <div className="relative z-[90] w-full max-w-5xl mx-auto px-4 pt-4">

          <div className="flex justify-start">

            <div className="w-fit">
              <HumanSupportCard />
            </div>

          </div>

        </div>

        {/* =====================================================
            MAIN CONTENT
        ====================================================== */}

        <main className="relative z-10 flex-1 flex flex-col w-full">

          {/* HOME */}
          {activeTab === 'home' && (
            <div className="relative z-10 flex-1 flex flex-col items-center justify-center p-6 max-w-5xl mx-auto w-full">

              <div className="relative z-10 w-full max-w-3xl border border-blue-100/60 dark:border-zinc-800 bg-white/50 dark:bg-zinc-900/40 rounded-3xl p-6 shadow-sm backdrop-blur-md flex flex-col min-h-[500px] overflow-hidden">

                <ViewController appConfig={appConfig} />

              </div>

            </div>
          )}

          {/* OUTBOUND */}
          {activeTab === 'outbound' && (
            <OutboundCallView />
          )}

          {/* DASHBOARD */}
          {activeTab === 'dashboard' && (
            <DashboardView />
          )}

        </main>

      </div>

      {/* Start Audio */}
      <StartAudioButton label="Start Audio" />

      {/* Toast */}
      <Toaster
        icons={{
          warning: <WarningIcon weight="bold" />,
        }}
        position="top-center"
        className="toaster group"
        style={
          {
            '--normal-bg': 'var(--popover)',
            '--normal-text': 'var(--popover-foreground)',
            '--normal-border': 'var(--border)',
          } as React.CSSProperties
        }
      />

    </AgentSessionProvider>
  );
}
