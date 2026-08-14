'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import {
  useAgent,
  useParticipants,
  useSessionContext,
  useSessionMessages,
} from '@livekit/components-react';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import { Shimmer } from '@/components/ai-elements/shimmer';
import { cn } from '@/lib/shadcn/utils';
import { TileLayout } from './tile-view';

const MotionMessage = motion.create(Shimmer);

const BOTTOM_VIEW_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      translateY: '0%',
    },
    hidden: {
      opacity: 0,
      translateY: '100%',
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.3,
    delay: 0.5,
    ease: 'easeOut',
  },
};

const CHAT_MOTION_PROPS: MotionProps = {
  variants: {
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeOut',
        duration: 0.3,
      },
    },
    visible: {
      opacity: 1,
      transition: {
        delay: 0.2,
        ease: 'easeOut',
        duration: 0.3,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

const SHIMMER_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0.8,
      },
    },
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

interface FadeProps {
  top?: boolean;
  bottom?: boolean;
  className?: string;
}

export function Fade({
  top = false,
  bottom = false,
  className,
}: FadeProps) {
  return (
    <div
      className={cn(
        'from-background pointer-events-none h-4 bg-linear-to-b to-transparent',
        top && 'bg-linear-to-b',
        bottom && 'bg-linear-to-t',
        className,
      )}
    />
  );
}

export interface AgentSessionView_01Props {
  preConnectMessage?: string;
  supportsChatInput?: boolean;
  supportsVideoInput?: boolean;
  supportsScreenShare?: boolean;
  isPreConnectBufferEnabled?: boolean;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';

  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  className?: string;
}

export function AgentSessionView_01({
  preConnectMessage = 'Agent is listening, ask it a question',
  supportsChatInput = true,
  supportsVideoInput = true,
  supportsScreenShare = true,
  isPreConnectBufferEnabled = true,

  audioVisualizerType,
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerWaveLineWidth,

  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & AgentSessionView_01Props) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);

  const [chatOpen, setChatOpen] = useState(false);

  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const agent = useAgent();
  const agentState = agent.state;

  // =====================================================
  // ACTIVE AGENT
  // =====================================================
  //
  // useAgent() gives us the agent state, but it is not
  // the Participant object. Therefore we use useParticipants()
  // to inspect the actual LiveKit agent participant.
  //
  // Backend attributes:
  // agent_role = main / specialist
  // agent_name = Anisa / Samar
  // =====================================================

  const participants = useParticipants();

  const activeAgentParticipant = participants.find(
    (participant) => participant.isAgent,
  );

  const backendAgentName =
    activeAgentParticipant?.attributes?.agent_name ?? '';

  const backendAgentRole =
    activeAgentParticipant?.attributes?.agent_role ?? '';

  const normalizedAgentName =
    backendAgentName.trim().toLowerCase();

  const normalizedAgentRole =
    backendAgentRole.trim().toLowerCase();

  const isSpecialist =
    normalizedAgentRole === 'specialist' ||
    normalizedAgentName === 'samar';

  // =====================================================
  // DISPLAY NAME
  // =====================================================

  const displayAgentName = isSpecialist
    ? 'Specialist Samar'
    : 'Anisa';

  // =====================================================
  // CONTROLS
  // =====================================================

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  // =====================================================
  // AUTO SCROLL
  // =====================================================

  useEffect(() => {
    const lastMessage = messages.at(-1);

    const lastMessageIsLocal =
      lastMessage?.from?.isLocal === true;

    if (
      scrollAreaRef.current &&
      lastMessageIsLocal
    ) {
      scrollAreaRef.current.scrollTop =
        scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  // =====================================================
  // UI
  // =====================================================

  return (
    <section
      ref={ref}
      className={cn(
        'bg-background relative z-10 h-full w-full overflow-hidden',
        className,
      )}
      {...props}
    >
      {/* =================================================
          FLOATING STATUS INDICATOR
          ================================================= */}

      <div className="absolute top-6 left-0 z-50 flex w-full justify-center pointer-events-none">
        <div className="flex items-center gap-2 rounded-full border border-teal-100 bg-teal-50/80 px-4 py-2 text-xs font-semibold tracking-wider text-teal-800 uppercase shadow-sm backdrop-blur-sm transition-all duration-300 dark:border-teal-900/30 dark:bg-teal-950/40 dark:text-teal-300 md:text-sm">

          {agentState === 'speaking' ? (
            <>
              <span className="animate-pulse">
                🔊
              </span>

              <span>
                {displayAgentName} is speaking
              </span>
            </>
          ) : (
            <>
              <span>🎤</span>

              <span>
                Listening to you
              </span>
            </>
          )}
        </div>
      </div>

      {/* =================================================
          TOP FADE
          ================================================= */}

      <Fade
        top
        className="absolute inset-x-4 top-0 z-10 h-40"
      />

      {/* =================================================
          TRANSCRIPT
          ================================================= */}

      <div className="absolute top-0 bottom-[135px] flex w-full flex-col md:bottom-[170px]">
        <AnimatePresence>
          {chatOpen && (
            <motion.div
              {...CHAT_MOTION_PROPS}
              className="flex h-full w-full flex-col gap-4 space-y-3 transition-opacity duration-300 ease-out"
            >
              <AgentChatTranscript
                agentState={agentState}
                messages={messages}
                className="mx-auto w-full max-w-2xl [&_.is-user>div]:rounded-[22px] [&>div>div]:px-4 [&>div>div]:pt-40 md:[&>div>div]:px-6"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* =================================================
          TILE LAYOUT
          ================================================= */}

      <TileLayout
        chatOpen={chatOpen}
        audioVisualizerType={audioVisualizerType}
        audioVisualizerColor={audioVisualizerColor}
        audioVisualizerColorShift={
          audioVisualizerColorShift
        }
        audioVisualizerBarCount={
          audioVisualizerBarCount
        }
        audioVisualizerRadialBarCount={
          audioVisualizerRadialBarCount
        }
        audioVisualizerRadialRadius={
          audioVisualizerRadialRadius
        }
        audioVisualizerGridRowCount={
          audioVisualizerGridRowCount
        }
        audioVisualizerGridColumnCount={
          audioVisualizerGridColumnCount
        }
        audioVisualizerWaveLineWidth={
          audioVisualizerWaveLineWidth
        }
      />

      {/* =================================================
          BOTTOM CONTROLS
          ================================================= */}

      <motion.div
        {...BOTTOM_VIEW_MOTION_PROPS}
        className="absolute inset-x-3 bottom-0 z-50 md:inset-x-12"
      >
        {/* PRE-CONNECT MESSAGE */}

        {isPreConnectBufferEnabled && (
          <AnimatePresence>
            {messages.length === 0 && (
              <MotionMessage
                key="pre-connect-message"
                duration={2}
                aria-hidden={messages.length > 0}
                {...SHIMMER_MOTION_PROPS}
                className="pointer-events-none mx-auto block w-full max-w-2xl pb-4 text-center text-sm font-semibold"
              >
                {preConnectMessage}
              </MotionMessage>
            )}
          </AnimatePresence>
        )}

        {/* CONTROL BAR */}

        <div className="bg-background relative mx-auto max-w-2xl pb-3 md:pb-12">
          <Fade
            bottom
            className="absolute inset-x-0 top-0 h-4 -translate-y-full"
          />

          <AgentControlBar
            variant="livekit"
            controls={controls}
            isChatOpen={chatOpen}
            isConnected={session.isConnected}
            onDisconnect={session.end}
            onIsChatOpenChange={setChatOpen}
          />
        </div>
      </motion.div>
    </section>
  );
}
