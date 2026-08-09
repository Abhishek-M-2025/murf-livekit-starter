import { Button } from '@/components/ui/button';
import { HeartPulse, Loader2, MicOff } from 'lucide-react';

interface WelcomeViewProps {
  state: 'ready' | 'connecting' | 'ended' | 'denied';
  onStartCall: () => void;
  onRetry: () => void;
}

export const WelcomeView = ({
  state,
  onStartCall,
  onRetry,
  ref,
  ...props
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div
      ref={ref}
      className="w-full max-w-md mx-auto p-6 flex flex-col items-center justify-center min-h-[400px]"
      {...props}
    >
      <section className="bg-background flex flex-col items-center justify-center text-center">
        {state === 'ready' && (
          <>
            <div className="p-4 rounded-full bg-teal-50 dark:bg-teal-950/30 text-teal-600 dark:text-teal-400 mb-6 border border-teal-100 dark:border-teal-900/30 shadow-xs">
              <HeartPulse className="size-12" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground mb-1">
              Anisha
            </h1>
            <p className="text-teal-600 dark:text-teal-400 font-medium text-sm uppercase tracking-wider mb-6">
              Health Access Assistant
            </p>
            <p className="text-muted-foreground text-sm max-w-sm mb-8 leading-relaxed">
              Your voice-powered healthcare guide. Click below to start your conversation.
            </p>
            <Button
              size="lg"
              onClick={onStartCall}
              className="w-64 rounded-full bg-teal-600 hover:bg-teal-700 dark:bg-teal-500 dark:hover:bg-teal-600 text-white font-semibold text-sm tracking-wide shadow-md transition-all cursor-pointer"
            >
              Start Conversation
            </Button>
          </>
        )}

        {state === 'connecting' && (
          <>
            <div className="p-4 rounded-full bg-teal-50/50 dark:bg-teal-950/20 text-teal-600 dark:text-teal-400 mb-6 border border-teal-100/50 dark:border-teal-900/20">
              <Loader2 className="size-12 animate-spin" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground mb-2">
              Connecting to Anisha...
            </h1>
            <p className="text-muted-foreground text-sm font-medium">
              Please wait
            </p>
          </>
        )}

        {state === 'ended' && (
          <>
            <div className="p-4 rounded-full bg-zinc-100 dark:bg-zinc-800/50 text-zinc-500 dark:text-zinc-400 mb-6 border border-zinc-200 dark:border-zinc-700/50">
              <HeartPulse className="size-12 opacity-60" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground mb-1">
              Call Ended
            </h1>
            <p className="text-muted-foreground text-sm mb-8">
              Thank you for consulting Anisha.
            </p>
            <Button
              size="lg"
              onClick={onStartCall}
              className="w-64 rounded-full bg-teal-600 hover:bg-teal-700 dark:bg-teal-500 dark:hover:bg-teal-600 text-white font-semibold text-sm tracking-wide shadow-md transition-all cursor-pointer"
            >
              Start Conversation Again
            </Button>
          </>
        )}

        {state === 'denied' && (
          <>
            <div className="p-4 rounded-full bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400 mb-6 border border-red-100 dark:border-red-900/30 shadow-xs">
              <MicOff className="size-12" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-red-600 dark:text-red-400 mb-3">
              Microphone Access Blocked
            </h1>
            <p className="text-muted-foreground text-sm max-w-sm mb-8 leading-relaxed">
              Your microphone permission is currently blocked. Please allow microphone access in your browser settings to talk to Anisha.
            </p>
            <Button
              size="lg"
              onClick={onRetry}
              className="w-64 rounded-full bg-red-600 hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600 text-white font-semibold text-sm tracking-wide shadow-md transition-all cursor-pointer"
            >
              Retry
            </Button>
          </>
        )}
      </section>
    </div>
  );
};
