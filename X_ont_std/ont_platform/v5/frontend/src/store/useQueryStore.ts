import { create } from 'zustand';

export type AnswerMode = 'document_only' | 'document_with_limits' | 'expert_mode';

export interface FollowUpSuggestion {
  rank: number;
  question: string;
  reason: string;
  confidence: number;
}

export interface QueryMessage {
  query_id: string;
  question: string;
  answer: string;
  coverage_level: number;
  coverage_level_name?: string;
  confidence_score: number;
  sources: any;
  limitations: any[];
  follow_up_suggestions: FollowUpSuggestion[];
  isStreaming: boolean;
}

interface QueryStore {
  // State
  currentProjectId: string | null;
  mode: AnswerMode;
  currentQuery: QueryMessage | null;
  previousQueries: QueryMessage[];
  isLoading: boolean;
  error: Error | null;

  // Actions
  setProjectId: (id: string) => void;
  setMode: (mode: AnswerMode) => void;
  
  // SSE Streaming Actions
  startQuery: (question: string) => void;
  updateStreamChunk: (textChunk: string) => void;
  updateSources: (sources: any) => void;
  updateLimitations: (limitations: any[]) => void;
  updateFollowUps: (followUps: FollowUpSuggestion[]) => void;
  finishQuery: (meta: any) => void;
  setError: (err: Error) => void;
  clearHistory: () => void;
}

export const useQueryStore = create<QueryStore>((set) => ({
  currentProjectId: null,
  mode: 'expert_mode',
  currentQuery: null,
  previousQueries: [],
  isLoading: false,
  error: null,

  setProjectId: (id) => set({ currentProjectId: id }),
  setMode: (mode) => set({ mode }),

  startQuery: (question) =>
    set((state) => ({
      isLoading: true,
      error: null,
      currentQuery: {
        query_id: `temp-${Date.now()}`,
        question,
        answer: '',
        coverage_level: 0,
        confidence_score: 0,
        sources: {},
        limitations: [],
        follow_up_suggestions: [],
        isStreaming: true,
      },
    })),

  updateStreamChunk: (textChunk) =>
    set((state) => ({
      currentQuery: state.currentQuery
        ? { ...state.currentQuery, answer: state.currentQuery.answer + textChunk }
        : null,
    })),

  updateSources: (sources) =>
    set((state) => ({
      currentQuery: state.currentQuery
        ? { ...state.currentQuery, sources }
        : null,
    })),

  updateLimitations: (limitations) =>
    set((state) => ({
      currentQuery: state.currentQuery
        ? { ...state.currentQuery, limitations }
        : null,
    })),

  updateFollowUps: (follow_up_suggestions) =>
    set((state) => ({
      currentQuery: state.currentQuery
        ? { ...state.currentQuery, follow_up_suggestions }
        : null,
    })),

  finishQuery: (meta) =>
    set((state) => {
      if (!state.currentQuery) return state;
      const completedQuery = {
        ...state.currentQuery,
        ...meta,
        isStreaming: false,
      };
      return {
        currentQuery: completedQuery,
        previousQueries: [...state.previousQueries, completedQuery],
        isLoading: false,
      };
    }),

  setError: (error) => set({ error, isLoading: false }),

  clearHistory: () => set({ previousQueries: [], currentQuery: null }),
}));
